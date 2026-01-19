from db.db_mysql import DBc
from datetime import datetime


class TaskDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `tasks` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `project_id` BIGINT NOT NULL,
            `progress` INT DEFAULT 0,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def add_task(self, project_id) -> int:
        """创建任务"""
        now = datetime.now()
        sql = "INSERT INTO tasks (project_id, progress, created_at, updated_at) VALUES (%s, 0, %s, %s)"
        self.execute(sql, (project_id, now, now))
        return self.cursor.lastrowid

    def update_progress(self, task_id, progress):
        """更新进度"""
        now = datetime.now()
        sql = "UPDATE tasks SET progress = %s, updated_at = %s WHERE id = %s"
        self.execute(sql, (progress, now, task_id))

    def get_task_progress(self, task_id):
        """获取任务进度"""
        sql = "SELECT progress FROM tasks WHERE id = %s"
        self.cursor.execute(sql, (task_id,))
        result = self.cursor.fetchone()
        return result["progress"] if result else None
