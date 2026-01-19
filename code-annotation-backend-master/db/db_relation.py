from db.db_mysql import DBc


class RelationDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `snippet_arch_tag_relations` (
            `snippet_id` BIGINT NOT NULL,
            `arch_tag_id` BIGINT NOT NULL,
            `project_id` BIGINT NOT NULL,
            `file_id` BIGINT NOT NULL,
            PRIMARY KEY (`snipped_id`, `arch_tag_id`),
            FOREIGN KEY (`snippet_id`) REFERENCES `snippets`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`arch_tag_id`) REFERENCES `arch_tags`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def add_relation(self, snippet_id, arch_tag_id, project_id, file_id):
        """添加关系"""
        sql = "INSERT INTO snippet_arch_tag_relations (snippet_id, arch_tag_id, project_id, file_id) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (snippet_id, arch_tag_id, project_id, file_id))
        return self.cursor.lastrowid

    # -----------------------------------------------------------------------------------------------------------------------

    def addRelation(self, line_attr_id, arch_tag_id):
        """建立行与标签的关联"""
        sql = "INSERT INTO snippet_arch_tag_relations (line_attribute_id, arch_tag_id) VALUES (%s, %s)"
        self.execute(sql, (line_attr_id, arch_tag_id))

    def removeRelation(self, line_attr_id, arch_tag_id):
        """移除关联"""
        sql = "DELETE FROM snippet_arch_tag_relations WHERE line_attribute_id = %s AND arch_tag_id = %s"
        self.execute(sql, (line_attr_id, arch_tag_id))

    def getRelationsByLineId(self, line_attr_id):
        """获取某行的所有标签"""
        sql = "SELECT arch_tag_id FROM snippet_arch_tag_relations WHERE line_attribute_id = %s"
        self.cursor.execute(sql, (line_attr_id,))
        return [row["arch_tag_id"] for row in self.cursor.fetchall()]

    def getRelationsByTagId(self, arch_tag_id):
        """获取某标签关联的所有行"""
        sql = "SELECT line_attribute_id FROM snippet_arch_tag_relations WHERE arch_tag_id = %s"
        self.cursor.execute(sql, (arch_tag_id,))
        return [row["line_attribute_id"] for row in self.cursor.fetchall()]
