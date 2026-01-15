from db.db_mysql import DBc
import db.helper_file as helper_file
import pymysql

from typing import List, Optional


class CodeDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `code_files` (
         `id` BIGINT PRIMARY KEY  AUTO_INCREMENT  NOT NULL  UNIQUE ,
         `project_id` BIGINT NOT NULL, 
         `file_rela_path` VARCHAR(500) NOT NULL,
         `file_abs_path` VARCHAR(500) NOT NULL,
         `parse_result_path` VARCHAR(500),
         `file_name` VARCHAR(255) NOT NULL, 
         `file_size` BIGINT NOT NULL,
         `file_type` VARCHAR(255));
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

    def addCode(
        self,
        project_id,
        file_rela_path,
        parse_result,
        file_name,
        file_size,
        file_type,
    ) -> int:
        """返回新增代码的id"""
        sql = "INSERT INTO code_files (project_id,file_rela_path,file_abs_path,parse_result_path,file_name,file_size,file_type) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        self.execute(
            sql,
            (
                project_id,
                file_rela_path,
                helper_file.abs_path(file_rela_path),
                parse_result,
                file_name,
                file_size,
                file_type,
            ),
        )
        return self.cursor.lastrowid

    def selectOneCodePath(self, project_id, file_rela_path) -> str | None:
        """根据项目id和代码路径查找该项目中的一个代码，返回该代码的绝对路径"""
        sql = "SELECT file_abs_path FROM code_files WHERE project_id = %s AND file_rela_path = %s"
        self.cursor.execute(sql, (project_id, file_rela_path))
        result = self.cursor.fetchone()
        return result["file_abs_path"] if result else None

    def removeCode(self, project_id, file_rela_path):
        """根据项目id和代码路径删除该项目中的一个代码"""
        sql = "DELETE FROM code_files WHERE project_id = %s AND file_rela_path = %s"
        self.execute(sql, (project_id, file_rela_path))

    def selectAllCodes(self, project_id) -> List[Optional[str]]:
        """根据项目id查找该项目里的所有代码，返回所有代码的绝对路径"""
        sql = "SELECT file_abs_path FROM code_files WHERE project_id = %s"
        self.cursor.execute(sql, project_id)
        result = self.cursor.fetchall()
        return [r.get("file_abs_path") for r in result] if result else []

    def modifyCodeParseResult(self, project_id, file_abs_path, parse_result_path):
        """根据项目id和代码路径修改该项目中的一个代码的解析结果"""
        sql = "UPDATE code_files SET parse_result_path = %s WHERE project_id = %s AND file_abs_path = %s"
        self.execute(sql, (parse_result_path, project_id, file_abs_path))

    # ---------------------------------------------------------------------------------

    # def selectAllCodeName(self, project_id):
    #     """根据项目id查找该项目里的所有代码，返回所有代码名"""
    #     sql = "SELECT file_name，file_type FROM projects WHERE project_id = %s"
    #     self.cursor.execute(sql, project_id)
    #     return self.cursor.fetchone()
