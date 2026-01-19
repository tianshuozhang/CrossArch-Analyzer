from db.db_mysql import DBc


class SnippetDB(DBc):

    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `snippets` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `left` BIGINT NOT NULL,
            `right` BIGINT NOT NULL,
            `file_id` BIGINT NOT NULL,
            `project_id` BIGINT NOT NULL,
            FOREIGN KEY (`file_id`) REFERENCES `files`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def detele_all_snippets_by_project_id(self, project_id):
        sql = "DELETE FROM arch_tags WHERE project_id = %s"
        self.execute(sql, (project_id,))

    def add_snippet(self, left, right, file_id, project_id):
        sql = "INSERT INTO arch_tags (left, right, file_id, project_id) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (left, right, file_id, project_id))
        return self.cursor.lastrowid

    # def add_arch_tag(self, text, color, user_id) -> int:
    #     """添加架构标签"""
    #     sql = "INSERT INTO arch_tags (text, color, user_id) VALUES (%s, %s, %s)"
    #     self.execute(sql, (text, color, user_id))
    #     return self.cursor.lastrowid
