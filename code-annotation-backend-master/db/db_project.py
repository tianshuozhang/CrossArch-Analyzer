from db.db_mysql import DBc
from datetime import datetime


class ProjectDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `projects` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `name` VARCHAR(100) NOT NULL,
            `upload_time` DATETIME NOT NULL,
            `modified_time` DATETIME NOT NULL,
            `place` VARCHAR(255) DEFAULT NULL,
            `processed` TINYINT NOT NULL DEFAULT 0,
            `modified` TINYINT NOT NULL DEFAULT 0,
            `user_id` BIGINT NOT NULL,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
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
            table_name="projects",
        )

    def add_project(
        self, name: str, place: str, processed: int, modified: int, user_id: int
    ) -> int:
        """添加项目"""
        now = datetime.now()
        sql = "INSERT INTO projects (name, upload_time, modified_time, place, processed, modified, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.execute(sql, (name, now, now, place, processed, modified, user_id))
        return self.cursor.lastrowid

    def get_project_status(self, project_id: int) -> dict | None:
        """根据项目 ID 查询项目状态"""
        sql = "SELECT place, processed, modified FROM projects WHERE id = %s"
        result = self.cursor.fetchone(sql, (project_id,))
        if result:
            return {
                "place": result["place"],
                "processed": result["processed"],
                "modified": result["modified"],
            }
        return None

    def update_project_status(
        self,
        project_id: int,
        place: str = None,
        processed: int = None,
        modified: int = None,
    ) -> bool:
        """
        更新项目状态（place, processed, modified）。
        未传入的字段将保持不变。
        """
        updates = []
        params = []

        if place is not None:
            updates.append("place = %s")
            params.append(place)
        if processed is not None:
            updates.append("processed = %s")
            params.append(processed)
        if modified is not None:
            updates.append("modified = %s")
            params.append(modified)

        if not updates:
            return False  # 没有需要更新的内容
        params.append(project_id)
        sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s"
        self.execute(sql, tuple(params))
        return self.cursor.rowcount > 0

    def get_project_name(self, project_id: int) -> str | None:
        """根据项目 ID 查询项目名称"""
        sql = "SELECT name FROM projects WHERE id = %s"
        result = self.cursor.fetchone(sql, (project_id,))
        return result["name"] if result else None
