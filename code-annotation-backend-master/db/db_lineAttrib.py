from db.db_mysql import DBc
class LineAttributeDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `line_attributes` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `line_number` INT NOT NULL,
            `is_highlighted` BOOLEAN DEFAULT FALSE,
            `highlight_color` VARCHAR(7) DEFAULT '#000000',
            `file_id` BIGINT NOT NULL,
            FOREIGN KEY (`file_id`) REFERENCES `files`(`id`) ON DELETE CASCADE,
            UNIQUE KEY `unique_line_per_file` (`file_id`, `line_number`)
        );
        """
        super().__init__(*args, **kwargs)

    def addLineAttribute(self, line_number, is_highlighted, highlight_color, file_id) -> int:
        """添加行属性"""
        sql = "INSERT INTO line_attributes (line_number, is_highlighted, highlight_color, file_id) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (line_number, is_highlighted, highlight_color, file_id))
        return self.cursor.lastrowid

    def getLineAttributesByFileId(self, file_id):
        """获取文件的所有行属性"""
        sql = "SELECT * FROM line_attributes WHERE file_id = %s ORDER BY line_number"
        self.cursor.execute(sql, (file_id,))
        return self.cursor.fetchall()

    def updateHighlight(self, line_id, is_highlighted, highlight_color=None):
        """更新高亮状态"""
        sql = "UPDATE line_attributes SET is_highlighted = %s, highlight_color = %s WHERE id = %s"
        self.execute(sql, (is_highlighted, highlight_color or '#000000', line_id))