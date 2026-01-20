from db.db_mysql import DBc
from datetime import datetime


class VisualizationDataDB(DBc):
    def __init__(self, *args, **kwargs):
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
        super().__init__(*args, **kwargs)

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
        self.cursor.execute(sql, (project_id,))
        results = self.cursor.fetchall()
        return [{"title": result["title"], "id": result["id"]} for result in results]
