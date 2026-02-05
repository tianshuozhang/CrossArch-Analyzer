from db.db_task import TaskDB

task_db = TaskDB()


def update_progress(task_id: int, new_progress: int) -> dict:
    """更新任务进度"""
    task_db.update_progress(task_id, new_progress)


def check_task_killed(task_id: int) -> bool:
    """检查任务是否被要求取消
    如果返回true，那么需要完成llm的清理工作，
    清理工作完成后调用下面的`clear_task_killed`表示清理完成，然后立刻退出执行"""
    return task_db.get_task_killed(task_id)


def clear_task_killed():
    """表示llm的清理工作完成"""
    task_db.clear_task_killed()
