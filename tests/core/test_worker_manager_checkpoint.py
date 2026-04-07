
from core.worker_manager import WorkerManager, WorkerTask


class CheckpointingEngine:
    def submit(self, prompt):
        yield ("text", "working")
        yield ("text", "[checkpoint saved; run /resume-from-checkpoint]")


def test_worker_manager_marks_checkpoint_pause_as_completed():
    manager = WorkerManager(build_worker_engine=lambda: CheckpointingEngine())
    task = WorkerTask(task_id="agent-1", description="desc", engine=CheckpointingEngine())
    manager._run_task(task, "prompt")
    assert task.status == "completed"
    assert "checkpoint" in task.summary.lower()
