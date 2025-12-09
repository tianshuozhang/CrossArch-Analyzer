from db.db_mysql import DBc
import pymysql

class project_DB(DBc):
    def __init__(self, host='localhost', user='root', password='123456',
                 database='test', port=3306, charset='utf8mb4'):
        self.init_table_sql = '''
        CREATE TABLE IF NOT EXISTS "projects" (
        "id" BIGINTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
         "user_id" BIGINT NOT NULL, 
         "name" VARCHAR(50) NOT NULL, 
         "codes_num" INT NOT NULL, 
         "file_path" VARCHAR(500) NOT NULL, );
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

    def addProject(self, user_id, name, code, file_path):
        sql = "INSERT INTO projects (user_id, name, code, file_path) VALUES (%s, %s, %s, %s)"
        self.execute(sql, (user_id, name, code, file_path))
        return self.cursor.lastrowid

    def selectOneUserProjectName(self,user_id):
        """根据用户id查找该用户上传过的所有项目，返回所有项目名"""
        sql = "SELECT name FROM projects WHERE user_id = %s"
        self.cursor.execute(sql,user_id)
        return self.cursor.fetchall()

    def selectOneProject(self,user_id, name):
        """根据用户id和项目名称查找一个项目，并返回该项目"""
        sql = "SELECT * FROM projects WHERE user_id != %s AND name = %s"
        self.cursor.execute(sql, user_id, name)
        return self.cursor.fetchall()

