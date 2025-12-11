from typing import Dict
from db.db_mysql import DBc
import pymysql


class ProjectDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `projects` (
         `id` BIGINT PRIMARY KEY  AUTO_INCREMENT  NOT NULL  UNIQUE ,
         `user_id` BIGINT NOT NULL, 
         `name` VARCHAR(50) NOT NULL, 
         `project_path` VARCHAR(500) NOT NULL,
         `codes_num` INT NOT NULL);
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

    def addProject(self, user_id, project_name, project_path, codes_num) -> int:
        """记录一个项目，并返回该项目的id"""
        sql = "INSERT INTO projects (user_id, name,project_path, codes_num) VALUES (%s, %s,%s, %s)"
        self.execute(sql, (user_id, project_name, project_path, codes_num))
        return self.cursor.lastrowid

    def modifyProjectCodesNum(self, project_id, codes_num):
        """修改一个项目的code数量"""
        sql = "UPDATE projects SET codes_num = %s WHERE id = %s"
        self.execute(sql, (codes_num, project_id))

    def selectProjectId(self, user_id, project_name) -> int | None:
        """根据用户id和项目名称查找一个项目，并返回该项目的id"""
        sql = "SELECT id FROM projects WHERE user_id = %s AND name = %s"
        self.cursor.execute(sql, (user_id, project_name))
        result = self.cursor.fetchone()
        return result["id"] if result else None

    # ---------------------------------------------------------------------------------

    def selectOneUserProjectName(self, user_id):
        """根据用户id查找该用户上传过的所有项目，返回所有项目名"""
        sql = "SELECT name FROM projects WHERE user_id = %s"
        self.cursor.execute(sql, user_id)
        return self.cursor.fetchall()
