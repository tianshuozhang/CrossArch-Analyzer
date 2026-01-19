from db.db_mysql import DBc
from datetime import datetime


class ModifyDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `modify_records` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
            `operation_name` VARCHAR(100) NOT NULL,
            `file_id` BIGINT DEFAULT NULL,
            `property_name` VARCHAR(50) NOT NULL,
            `new_value` TEXT DEFAULT NULL,
            `project_id` BIGINT NOT NULL,
            `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
        )

    def add_modify_record(
        self,
        operation_name: str,
        file_id: int | None,
        property_name: str,
        new_value: str | None,
        project_id: int,
    ) -> int:
        """增加一条修改记录"""
        sql = """
        INSERT INTO modify_records 
        (operation_name, file_id, property_name, new_value, project_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.execute(
            sql,
            (operation_name, file_id, property_name, new_value, project_id),
        )
        return self.cursor.lastrowid

    def get_modify_records(self, project_id: int) -> list[dict]:
        """查询项目的所有修改记录"""
        sql = """
        SELECT id, operation_name, file_id, property_name, new_value, created_time
        FROM modify_records
        WHERE project_id = %s
        ORDER BY created_time DESC
        """
        records = self.cursor.fetchall(sql, (project_id,))
        return records

    def delete_all_modify_records(self, project_id: int) -> bool:
        """删除指定项目的全部修改记录"""
        sql = "DELETE FROM modify_records WHERE project_id = %s"
        self.execute(sql, (project_id,))
        return self.cursor.rowcount > 0

    def get_modify_records_by_file_id(self, file_id: int) -> list[dict]:
        """查询指定文件的所有修改记录"""
        sql = """
        SELECT id, operation_name, file_id, property_name, new_value, created_time
        FROM modify_records
        WHERE file_id = %s
        ORDER BY created_time DESC
        """
        records = self.cursor.fetchall(sql, (file_id,))
        return records

    def delete_modify_record_by_id(self, modify_record_id: int) -> bool:
        """删除指定修改记录"""
        sql = "DELETE FROM modify_records WHERE id = %s"
        self.execute(sql, (modify_record_id,))
        return self.cursor.rowcount > 0
