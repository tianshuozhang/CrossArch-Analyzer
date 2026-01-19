from db.db_task import TaskDB

task_db = TaskDB()


def update_progress(task_id: int, new_progress: int) -> dict:
    """
    获取任务进度
    :return:
    """
    task_db.update_progress(task_id, new_progress)
