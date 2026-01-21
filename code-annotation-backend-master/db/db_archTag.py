from db.db_mysql import DBc


class ArchTagDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `arch_tags` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `text` VARCHAR(50) NOT NULL,
            `color` VARCHAR(7) DEFAULT '#000000',
            `user_id` BIGINT NOT NULL,
            FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
            UNIQUE KEY `unique_text_per_user` (`text`, `user_id`)
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
            table_name="arch_tags",
        )
        self.default_arch_tags = [
            {"text": "arm", "color": "#CCDA36"},
            {"text": "riscv", "color": "#1BCC59"},
            {"text": "loong", "color": "#E7199F"},
            {"text": "mips", "color": "#EA4C89"},
            {"text": "powerpc", "color": "#EA4C89"},
            {"text": "x86", "color": "#77BA67"},
        ]

    def set_default_arch_tags(self, user_id):
        """设置默认的架构标签"""
        for tag in self.default_arch_tags:
            if self.get_arch_tag_id(tag["text"], user_id):
                continue
            self.add_arch_tag(tag["text"], tag["color"], user_id)

    def add_arch_tag(self, text, color, user_id) -> int:
        """添加架构标签"""
        sql = "INSERT INTO arch_tags (text, color, user_id) VALUES (%s, %s, %s)"
        self.execute(sql, (text, color, user_id))
        return self.cursor.lastrowid

    def get_arch_tag_id(self, text, user_id) -> int | None:
        """根据文本和用户ID获取标签ID"""
        sql = "SELECT id FROM arch_tags WHERE text = %s AND user_id = %s"
        self.execute(sql, (text, user_id))
        result = self.cursor.fetchone()
        return result["id"] if result else None

    def update_arch_tag(self, text, color) -> bool:
        """更新架构标签"""
        sql = "UPDATE arch_tags SET color = %s WHERE text = %s"
        self.execute(sql, (color, text))
        return self.cursor.rowcount > 0
