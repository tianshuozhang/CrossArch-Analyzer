from db.db_mysql import DBc
from datetime import datetime


class VisualizationDataDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `visualization_data` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `natural_language_requirement` TEXT,
            `project_id` BIGINT NOT NULL,
            `title` VARCHAR(255) NOT NULL,
            `generated_at` DATETIME NOT NULL,
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
            table_name="visualization_data",
        )

    def add_visualization_data(
        self, natural_language_requirement: str, title: str, project_id: int
    ) -> int:
        """添加可视化数据"""
        now = datetime.now()
        sql = "INSERT INTO visualization_data (natural_language_requirement, title,project_id, generated_at) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (natural_language_requirement, title, project_id, now))
        return self.cursor.lastrowid

    def get_all_visualization_data_title_id_list(self, project_id: int) -> list[dict]:
        """获取所有可视化数据"""
        sql = "SELECT title FROM visualization_data WHERE project_id = %s ORDER BY generated_at DESC"
        self.execute(sql, (project_id,))
        results = self.cursor.fetchall()
        return [{"title": result["title"], "id": result["id"]} for result in results]
