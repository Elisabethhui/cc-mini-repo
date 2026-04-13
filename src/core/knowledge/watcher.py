from __future__ import annotations
import json
import time
from threading import Timer
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .ingester import WikiIngester


class ChangedFileTracker:
    """跟踪变更文件列表，用于 /digest --changed"""
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.changed_log = self.workspace_root / ".cc-mini" / "changed_files.json"
        self._changed: set[str] = set()
        self._load()

    def _load(self) -> None:
        """从磁盘加载变更列表"""
        if self.changed_log.exists():
            try:
                data = json.loads(self.changed_log.read_text())
                self._changed = set(data)
            except Exception:
                self._changed = set()
        else:
            self._changed = set()

    def _save(self) -> None:
        """保存变更列表到磁盘"""
        self.changed_log.parent.mkdir(parents=True, exist_ok=True)
        self.changed_log.write_text(json.dumps(sorted(self._changed)), encoding="utf-8")

    def add(self, file_path: str | Path) -> None:
        """添加文件到变更列表"""
        path = Path(file_path)
        if path.is_relative_to(self.workspace_root):
            rel_path = str(path.relative_to(self.workspace_root))
            self._changed.add(rel_path)
            self._save()

    def get_and_clear(self) -> list[str]:
        """获取所有变更文件并清空列表"""
        result = sorted(self._changed)
        self._changed.clear()
        self._save()
        return result

    def peek(self) -> list[str]:
        """查看变更列表但不清空"""
        return sorted(self._changed)


class WikiDebounceWatcher(FileSystemEventHandler):
    """
    带有防抖(Debounce)功能的监听器。
    防止用户一次保存触发多次事件，导致频繁重建 AST。
    同时跟踪变更文件用于 /digest --changed。
    """
    def __init__(self, ingester: WikiIngester, debounce_seconds: int = 3, tracker: ChangedFileTracker | None = None):
        self.ingester = ingester
        self.debounce_seconds = debounce_seconds
        self._timers = {}
        self.tracker = tracker

    def _handle_change(self, file_path: str):
        # 过滤掉自身生成的 wiki 目录和 git 目录，防止无限递归
        if ".cc-mini" in file_path or ".git" in file_path or "__pycache__" in file_path:
            return

        path = Path(file_path)
        if path.is_file():
            # 跟踪变更文件
            if self.tracker:
                self.tracker.add(path)
            print(f"👀 [Watcher] 检测到文件变更: {path.name}，正在更新 Wiki...")
            # 局部更新 entity
            self.ingester.ingest_file(path)
            # 因为文件可能增删类，这里可以简单地全量重建 L1 index，耗时极短
            # 真实场景下可以做增量更新
            self.ingester.ingest_all()

    def _debounce(self, event):
        path = event.src_path
        if path in self._timers:
            self._timers[path].cancel()

        timer = Timer(self.debounce_seconds, self._handle_change, args=[path])
        self._timers[path] = timer
        timer.start()

    def on_modified(self, event):
        if not event.is_directory:
            self._debounce(event)

    def on_created(self, event):
        if not event.is_directory:
            self._debounce(event)

def start_wiki_watcher(workspace_root: str, ingester: WikiIngester, tracker: ChangedFileTracker | None = None) -> Observer:
    """在后台线程启动监听"""
    event_handler = WikiDebounceWatcher(ingester, tracker=tracker)
    observer = Observer()
    observer.schedule(event_handler, workspace_root, recursive=True)
    observer.daemon = True  # 设置为守护线程，主进程退出时自动销毁
    observer.start()
    print("[Watcher] 后台静默监听已启动...")
    return observer


def get_changed_tracker(workspace_root: str | Path) -> ChangedFileTracker:
    """获取变更文件跟踪器实例"""
    return ChangedFileTracker(Path(workspace_root))