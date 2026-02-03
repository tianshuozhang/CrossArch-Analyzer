from db.db_mysql import DBc
from datetime import datetime
from typing import Optional, List, Dict


# TODO:这里可能有些函数待删除
class FileDB(DBc):
    def __init__(
        self,
        host="localhost",
        user="root",
        password="123456",
        database="classify_c",
        port=3306,
        charset="utf8mb4",
    ):
        # 新表结构初始化SQL（完全匹配你指定的字段）
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `files` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `name` VARCHAR(255) NOT NULL COMMENT '文件/目录名（不含路径）',
            `modify_time` DATETIME NOT NULL COMMENT '最后修改时间',
            `path` VARCHAR(512) NOT NULL COMMENT '完整路径（如src/utils/helper.cpp）',
            `project_id` BIGINT NOT NULL COMMENT '所属项目ID',
            `tmp_count` BIGINT NOT NULL DEFAULT 0 COMMENT '临时计数',
            FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
            UNIQUE KEY `uk_project_path` (`project_id`, `path`) COMMENT '保证项目内路径唯一'
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
            table_name="files",
        )

    def add_file(self, name: str, project_id: int, path: str) -> int:
        """
        添加文件/目录记录（核心适配新表结构）
        :param name: 文件名/目录名
        :param project_id: 所属项目ID
        :param path: 完整路径（如src/utils/helper.cpp）
        :return: 新增记录的ID
        """
        now = datetime.now()
        sql = """
        INSERT INTO files (name, modify_time, project_id, path)
        VALUES (%s, %s, %s, %s)
        """
        self.execute(sql, (name, now, project_id, path))
        return self.cursor.lastrowid

    def get_file_id_by_file_path(self, file_path: str, project_id: int) -> int | None:
        """根据文件路径和项目ID获取文件ID"""
        sql = "SELECT id FROM files WHERE project_id = %s AND path = %s"
        self.execute(sql, (project_id, file_path))
        result = self.cursor.fetchone()
        return result["id"] if result else None

    def get_file_path_by_id(self, file_id: int) -> Optional[str]:
        """根据文件ID获取文件路径"""
        sql = "SELECT path FROM files WHERE id = %s"
        self.execute(sql, (file_id,))
        result = self.cursor.fetchone()
        return result["path"] if result else None

    def get_file_by_id(self, file_id: int) -> Optional[Dict]:
        """根据文件ID获取单条文件记录"""
        sql = "SELECT * FROM files WHERE id = %s"
        self.execute(sql, (file_id,))
        result = self.cursor.fetchone()
        return result if result else None

    def get_files_by_project_id(self, project_id: int) -> List[Dict]:
        """获取指定项目下的所有文件/目录记录（按路径排序）"""
        sql = "SELECT * FROM files WHERE project_id = %s ORDER BY path"
        self.execute(sql, (project_id,))
        return self.cursor.fetchall()

    def delete_file(self, file_id: int):
        """物理删除文件记录（适配新表）"""
        sql = "DELETE FROM files WHERE id = %s"
        self.execute(sql, (file_id,))

    def get_file_tmp_count_by_id(self, file_id: int) -> int:
        """获取指定文件ID的临时计数"""
        sql = "SELECT tmp_count FROM files WHERE id = %s"
        self.execute(sql, (file_id,))
        result = self.cursor.fetchone()
        return result["tmp_count"] if result else 0

    def update_file_tmp_count_by_id(self, file_id: int, new_count: int) -> bool:
        """更新指定文件ID的临时计数"""
        sql = "UPDATE files SET tmp_count = %s WHERE id = %s"
        self.execute(sql, (new_count, file_id))
        return self.cursor.rowcount > 0

    def update_file_modify_time_by_id(self, file_id: int) -> bool:
        """更新指定文件ID的修改时间"""
        new_time = datetime.now()
        sql = "UPDATE files SET modify_time = %s WHERE id = %s"
        self.execute(sql, (new_time, file_id))
        return self.cursor.rowcount > 0
