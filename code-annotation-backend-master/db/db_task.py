from db.db_mysql import DBc

class TaskDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `tasks` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `project_id` BIGINT NOT NULL,
            `progress` INT DEFAULT 0,
            `status` ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def addTask(self, project_id) -> int:
        """创建任务"""
        now = datetime.now()
        sql = "INSERT INTO tasks (project_id, progress, status, created_at, updated_at) VALUES (%s, 0, 'pending', %s, %s)"
        self.execute(sql, (project_id, now, now))
        return self.cursor.lastrowid

    def updateProgress(self, task_id, progress):
        """更新进度"""
        now = datetime.now()
        sql = "UPDATE tasks SET progress = %s, updated_at = %s WHERE id = %s"
        self.execute(sql, (progress, now, task_id))

    def getTaskByProjectId(self, project_id):
        """获取项目对应的任务"""
        sql = "SELECT * FROM tasks WHERE project_id = %s ORDER BY created_at DESC LIMIT 1"
        self.cursor.execute(sql, (project_id,))
        return self.cursor.fetchone()