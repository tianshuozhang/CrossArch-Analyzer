from db.db_mysql import DBc
import pymysql

class ReportDB(DBc):
    def __init__(self, host='localhost', user='root', password='123456',
                 database='test', port=3306, charset='utf8mb4'):
        self.init_table_sql = '''
        CREATE TABLE IF NOT EXISTS "code_files" (
        "id" BIGINTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
         "project_id" BIGINT NOT NULL, 
         "name" VARCHAR(255) NOT NULL, 
         "report_data" JSON NOT NULL,
         "file_path" VARCHAR(500) NOT NULL);
        '''
        super().__init__(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset=charset,
            init_table_sql=self.init_table_sql
        )

    def addCReport(self, project_id, name, report_data, file_path):
        sql = "INSERT INTO projects (project_id,name,report_data,file_path) VALUES(%s,%s,%s,%s)"
        self.execute(sql,(project_id, name, report_data, file_path))
        return self.cursor.lastrowid

    def selectReport(self,project_id):
        """根据项目id，查找该项目中的报告，报告所在路径"""
        sql = "SELECT file_path FROM projects WHERE project_id = %s"
        self.cursor.execute(sql,project_id)
        return self.cursor.fetchone()

