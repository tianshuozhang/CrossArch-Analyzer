from db.db_mysql import DBc
from datetime import datetime


class TaskDB(DBc):
    def __init__(
        self,
        host="localhost",
        user="root",
        password="123456",
        database="classify_c",
        port=3306,
        charset="utf8mb4",
    ):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `tasks` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `project_id` BIGINT NOT NULL,
            `progress` INT DEFAULT 0,
            `killed` TINYINT(1) DEFAULT 0,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset=charset,
            init_table_sql=self.init_table_sql,
            table_name="tasks",
        )

    def add_task(self, project_id: int) -> int:
        """创建任务"""
        now = datetime.now()
        sql = "INSERT INTO tasks (project_id, progress, created_at, updated_at) VALUES (%s, 0, %s, %s)"
        self.execute(sql, (project_id, now, now))
        return self.cursor.lastrowid

    def update_progress(self, task_id: int, progress: int):
        """更新进度"""
        now = datetime.now()
        sql = "UPDATE tasks SET progress = %s, updated_at = %s WHERE id = %s"
        self.execute(sql, (progress, now, task_id))

    def get_task_progress(self, task_id: int) -> int | None:
        """获取任务进度"""
        sql = "SELECT progress FROM tasks WHERE id = %s"
        self.execute(sql, (task_id,))
        result = self.cursor.fetchone()
        return result["progress"] if result else None

    def delete_task(self, task_id: int):
        """删除任务"""
        sql = "DELETE FROM tasks WHERE id = %s"
        self.execute(sql, (task_id,))

    def set_task_killed(self, task_id: int):
        """设置任务取消"""
        sql = "UPDATE tasks SET killed = 1 WHERE id = %s"
        self.execute(sql, (task_id,))

    def get_task_killed(self, task_id: int) -> bool:
        """获取任务是否有设置取消"""
        sql = "SELECT killed FROM tasks WHERE id = %s"
        self.execute(sql, (task_id,))
        result = self.cursor.fetchone()
        return result["killed"] if result else False

    def clear_task_killed(self):
        """清除任务取消状态"""
        sql = "UPDATE tasks SET killed = 0"
        self.execute(sql)
