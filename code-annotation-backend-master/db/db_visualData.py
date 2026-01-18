from db.db_mysql import DBc

class VisualizationDataDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `visualization_data` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `graph_data_path` VARCHAR(255) NOT NULL,
            `natural_language_requirement` TEXT,
            `project_id` BIGINT NOT NULL,
            `generated_at` DATETIME NOT NULL,
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def addVisualizationData(self, graph_data_path, natural_language_requirement, project_id) -> int:
        """添加可视化数据"""
        now = datetime.now()
        sql = "INSERT INTO visualization_data (graph_data_path, natural_language_requirement, project_id, generated_at) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (graph_data_path, natural_language_requirement, project_id, now))
        return self.cursor.lastrowid

    def getVisualizationDataByProjectId(self, project_id):
        """获取项目的可视化数据"""
        sql = "SELECT * FROM visualization_data WHERE project_id = %s ORDER BY generated_at DESC LIMIT 1"
        self.cursor.execute(sql, (project_id,))
        return self.cursor.fetchone()