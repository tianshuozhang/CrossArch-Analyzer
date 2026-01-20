from db.db_mysql import DBc
import re


class RelationDB(DBc):
    def __init__(self, *args, **kwargs):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `snippet_arch_tag_relations` (
            `start` BIGINT NOT NULL,
            `end` BIGINT NOT NULL,
            `file_id` BIGINT NOT NULL,            
            `project_id` BIGINT NOT NULL,
            `arm` TINYINT NOT NULL default 0,
            `riscv` TINYINT NOT NULL default 0,
            `loong` TINYINT NOT NULL default 0,
            `mips` TINYINT NOT NULL default 0,
            `powerPC` TINYINT NOT NULL default 0,
            `x86` TINYINT NOT NULL  default 0,
            PRIMARY KEY (`file_id`, `project_id`),
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
            FOREIGN KEY (`file_id`) REFERENCES `files`(`id`) ON DELETE CASCADE
        );
        """
        super().__init__(*args, **kwargs)

    def add_relation(self, start, end, arch_names: list[str], project_id, file_id):
        """添加关系"""
        arch_names_str = ", ".join(arch_names)
        placeholders = ", ".join(["%s"] * len(arch_names))
        values = [1] * len(arch_names)
        sql = f"INSERT INTO snippet_arch_tag_relations (start, end, {arch_names_str}, file_id, project_id) VALUES (%s, %s, {placeholders}, %s, %s)"
        self.execute(sql, (start, end, *values, file_id, project_id))
        return self.cursor.lastrowid

    def add_arch_name(self, arch_name: str) -> bool:
        """添加架构名称"""
        # 校验列名合法性
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", arch_name):
            return False

        sql = f"ALTER TABLE snippet_arch_tag_relations ADD COLUMN `{arch_name}` TINYINT NOT NULL DEFAULT 0"
        try:
            self.execute(sql)
            return True
        except Exception:
            return False  # 或根据需要抛出异常

    def get_relations_by_file_id(self, file_id: int, project_id: int):
        """获取文件下的所有关系"""
        sql = f"SELECT * FROM snippet_arch_tag_relations WHERE file_id = %s AND project_id = %s"
        self.cursor.execute(sql, (file_id, project_id))
        results = self.cursor.fetchall()
        return [
            {
                "start": result["start"],
                "end": result["end"],
                "arch_names": [
                    key
                    for key, value in result.items()
                    if key != "start"
                    and key != "end"
                    and key != "file_id"
                    and key != "project_id"
                    and value == 1
                ],
            }
            for result in results
        ]

    def get_relations_by_project_id(self, project_id: int):
        """获取项目下的所有关系"""
        sql = f"SELECT * FROM snippet_arch_tag_relations WHERE project_id = %s"
        self.cursor.execute(sql, (project_id))
        results = self.cursor.fetchall()
        return [
            {
                "start": result["start"],
                "end": result["end"],
                "arch_names": [
                    key
                    for key, value in result.items()
                    if key != "start"
                    and key != "end"
                    and key != "file_id"
                    and key != "project_id"
                    and value == 1
                ],
            }
            for result in results
        ]

    def delete_relations_by_file_id(self, file_id: int, project_id: int) -> bool:
        """删除文件下的所有关系"""
        sql = f"DELETE FROM snippet_arch_tag_relations WHERE file_id = %s AND project_id = %s"
        self.execute(sql, (file_id, project_id))
        return self.cursor.rowcount > 0

    def update_relation_arch_value(
        self, file_id: int, project_id: int, line: int, arch_name: str, value: int
    ):
        """更新关系"""
        sql = f"UPDATE snippet_arch_tag_relations SET {arch_name} = %s WHERE file_id = %s AND project_id = %s AND start <= %s AND end >= %s"
        self.execute(sql, (value, file_id, project_id, line, line))
        return self.cursor.rowcount > 0

    def get_relation_include_line(self, file_id: int, project_id: int, line: int):
        """查询文件下包含某行的关系"""
        sql = f"SELECT start,end FROM snippet_arch_tag_relations WHERE file_id = %s AND project_id = %s AND start <= %s AND end >= %s"
        self.cursor.execute(sql, (file_id, project_id, line, line))
        return self.cursor.fetchone()
