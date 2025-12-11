from db.db_mysql import DBc
import pymysql


class ReportDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `reports` (
         `id` BIGINT PRIMARY KEY  AUTO_INCREMENT  NOT NULL  UNIQUE ,
         `project_id` BIGINT NOT NULL,
         `file_path` VARCHAR(500) NOT NULL);
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

    def addReport(self, project_id, file_path) -> int:
        """添加一个项目的报告，并返回报告id"""
        sql = "INSERT INTO reports (project_id,file_path) VALUES(%s,%s)"
        self.execute(sql, (project_id, file_path))
        return self.cursor.lastrowid

    def selectReportPath(self, project_id) -> str | None:
        """根据项目id，查找该项目中的报告，返回报告所在路径"""
        sql = "SELECT file_path FROM reports WHERE project_id = %s"
        self.cursor.execute(sql, project_id)
        result = self.cursor.fetchone()
        return result["file_path"] if result else None
