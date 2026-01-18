from db.db_mysql import DBc
class RelationDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `line_arch_tag_relations` (
            `line_attribute_id` BIGINT NOT NULL,
            `arch_tag_id` BIGINT NOT NULL,
            PRIMARY KEY (`line_attribute_id`, `arch_tag_id`),
            FOREIGN KEY (`line_attribute_id`) REFERENCES `line_attributes`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`arch_tag_id`) REFERENCES `arch_tags`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def addRelation(self, line_attr_id, arch_tag_id):
        """建立行与标签的关联"""
        sql = "INSERT INTO line_arch_tag_relations (line_attribute_id, arch_tag_id) VALUES (%s, %s)"
        self.execute(sql, (line_attr_id, arch_tag_id))

    def removeRelation(self, line_attr_id, arch_tag_id):
        """移除关联"""
        sql = "DELETE FROM line_arch_tag_relations WHERE line_attribute_id = %s AND arch_tag_id = %s"
        self.execute(sql, (line_attr_id, arch_tag_id))

    def getRelationsByLineId(self, line_attr_id):
        """获取某行的所有标签"""
        sql = "SELECT arch_tag_id FROM line_arch_tag_relations WHERE line_attribute_id = %s"
        self.cursor.execute(sql, (line_attr_id,))
        return [row["arch_tag_id"] for row in self.cursor.fetchall()]

    def getRelationsByTagId(self, arch_tag_id):
        """获取某标签关联的所有行"""
        sql = "SELECT line_attribute_id FROM line_arch_tag_relations WHERE arch_tag_id = %s"
        self.cursor.execute(sql, (arch_tag_id,))
        return [row["line_attribute_id"] for row in self.cursor.fetchall()]