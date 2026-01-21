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

    def add_project(self, name: str, user_id: int) -> int:
        """添加项目"""
        now = datetime.now()
        sql = "INSERT INTO projects (name, upload_time, modified_time, user_id) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (name, now, now, user_id))
        return self.cursor.lastrowid

    def get_project_name(self, project_id: int) -> str | None:
        """根据项目 ID 查询项目名称"""
        sql = "SELECT name FROM projects WHERE id = %s"
        self.execute(sql, (project_id,))
        result = self.cursor.fetchone()
        return result["name"] if result else None

    def get_project_view_list_by_user_id(self, user_id: int) -> list[dict]:
        """根据用户 ID 查询项目列表"""
        sql = "SELECT id,name,modified_time FROM projects WHERE user_id = %s"
        self.execute(sql, (user_id,))
        return self.cursor.fetchall()

    def delete_project_by_id(self, project_id: int) -> bool:
        """根据项目 ID 删除项目"""
        sql = "DELETE FROM projects WHERE id = %s"
        self.execute(sql, (project_id,))
        return self.cursor.rowcount > 0
