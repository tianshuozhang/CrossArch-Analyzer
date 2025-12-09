from db.db_mysql import DBc
import pymysql

class CodeDB(DBc):
    def __init__(self, host='localhost', user='root', password='123456',
                 database='test', port=3306, charset='utf8mb4'):
        self.init_table_sql = '''
        CREATE TABLE IF NOT EXISTS "code_files" (
        "id" BIGINTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
         "project_id" BIGINT NOT NULL, 
         "filename" VARCHAR(255) NOT NULL, 
         "file_path" VARCHAR(500) NOT NULL,
         "file_size" BIGINT NOT NULL,
         "file_type" VARCHAR(255),
         "parse_result" JSON);
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

    def addCode(self, project_id, file_name, file_path, file_size, file_type, parse_result):
        sql = "INSERT INTO projects (project_id,file_name, file_path, file_size, file_type, parse_result) VALUES (%s, %s, %s, %s, %s, %s)"
        self.execute(sql,(project_id, file_name, file_path, file_size, file_type, parse_result))
        return self.cursor.lastrowid

    def selectOneCode(self,project_id,file_name,file_type):
        """根据项目id，代码名称和后缀查找该项目中的一个代码，返回代码所在路径"""
        sql = "SELECT file_path FROM projects WHERE project_id = %s AND file_name = %s AND file_type = %s"
        self.cursor.execute(sql,(project_id,file_name,file_type))
        return self.cursor.fetchone()

    def selectAllCodeName(self,project_id):
        """根据项目id查找该项目里的所有代码，返回所有代码名"""
        sql = "SELECT file_name，file_type FROM projects WHERE project_id = %s"
        self.cursor.execute(sql,project_id)
        return self.cursor.fetchone()