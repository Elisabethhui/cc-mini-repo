from __future__ import annotations
import time
from threading import Timer
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .ingester import WikiIngester

class WikiDebounceWatcher(FileSystemEventHandler):
    """
    带有防抖(Debounce)功能的监听器。
    防止用户一次保存触发多次事件，导致频繁重建 AST。
    """
    def __init__(self, ingester: WikiIngester, debounce_seconds: int = 3):
        self.ingester = ingester
        self.debounce_seconds = debounce_seconds
        self._timers = {}

    def _handle_change(self, file_path: str):
        # 过滤掉自身生成的 wiki 目录和 git 目录，防止无限递归
        if ".cc-mini" in file_path or ".git" in file_path or "__pycache__" in file_path:
            return

        path = Path(file_path)
        if path.is_file():
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

def start_wiki_watcher(workspace_root: str, ingester: WikiIngester) -> Observer:
    """在后台线程启动监听"""
    event_handler = WikiDebounceWatcher(ingester)
    observer = Observer()
    observer.schedule(event_handler, workspace_root, recursive=True)
    observer.daemon = True # 设置为守护线程，主进程退出时自动销毁
    observer.start()
    print("[Watcher] 后台静默监听已启动...")
    return observer