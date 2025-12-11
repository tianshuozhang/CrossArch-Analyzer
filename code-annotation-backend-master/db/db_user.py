from db.db_mysql import DBc
from datatime.get_time import get_now_time
import pymysql


class UserDB(DBc):
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
        CREATE TABLE IF NOT EXISTS `users` (
            `id` BIGINT PRIMARY KEY  AUTO_INCREMENT  NOT NULL  UNIQUE , 
            `username` VARCHAR(20), 
            `password` VARCHAR(20), 
            `created_at` DATETIME);
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

    def addUser(self, username, password) -> int:
        """不检验是否已有相同用户名，返回user_id"""
        time_now = get_now_time()
        sql = "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s)"
        self.execute(sql, (username, password, time_now))
        return self.cursor.lastrowid

    def getUserId(self, username) -> int | None:
        """根据用户名获取用户id，用于调取project"""
        sql = "SELECT id FROM users WHERE username = %s"
        self.cursor.execute(sql, (username,))
        result = self.cursor.fetchone()
        return result["id"] if result else None

    def updatePassword(self, username, password):
        """更新用户密码"""
        sql = "UPDATE users SET passwd = %s WHERE username = %s"
        self.execute(sql, (password, username))

    def checkUser(self, username, passwd) -> bool:
        """检查用户登录（用户名和密码验证）"""
        sql = "SELECT * FROM users WHERE username = %s AND passwd = %s"
        self.cursor.execute(sql, (username, passwd))
        result = self.cursor.fetchone()
        return True if result else False

    def checkSameUsername(self, username) -> bool:
        """检验是否是已有的相同的用户名，避免重复"""
        sql = "SELECT * FROM users WHERE username= %s"
        self.cursor.execute(sql, username)
        result = self.cursor.fetchone()
        return True if result else False

    # ---------------------------------------------------------------------------------

    def removeUser(self, username, passwd):
        """不检查是否用户存在，删除用户名和密码匹配的用户"""
        sql = "DELETE FROM users WHERE username = %s AND passwd = %s"
        self.execute(sql, (username, passwd))

    def getPassword(self, username):
        """获取用户密码"""
        sql = "SELECT password FROM users WHERE username = %s"
        self.cursor.execute(sql, (username,))
        result = self.cursor.fetchone()
        return result["password"] if result else None

    def GetAdminPassword(self):
        """获取管理员密码"""
        sql = "SELECT password FROM users WHERE username = 'admin'"
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        return result["password"] if result else None

    def admin_removeUser(self, username):
        """管理员删除用户（不需要密码验证）"""
        sql = "DELETE FROM users WHERE username = %s"
        self.execute(sql, username)

    def admin_checkUser(self, username):
        """管理员检查用户是否存在"""
        sql = "SELECT * FROM users WHERE username = %s"
        self.cursor.execute(sql, username)
        return self.cursor.fetchone()

    def create_admin_user(self, admin_password):
        """创建管理员用户（如果不存在）"""
        try:
            # 检查admin用户是否存在
            sql = "SELECT * FROM users WHERE username = 'admin'"
            self.cursor.execute(sql)
            admin_user = self.cursor.fetchone()

            if not admin_user:
                # 创建管理员用户
                sql = "INSERT INTO users (username, passwd, created_at) VALUES ('admin', %s, %s)"
                time_now = get_now_time()
                self.execute(sql, (admin_password, time_now))
                print("管理员用户创建成功")
                return True
            else:
                print("管理员用户已存在")
                return False
        except Exception as e:
            print(f"创建管理员用户时出错: {e}")
            return False

    def selectAllUser(self):
        sql = "SELECT * FROM users WHERE username != 'admin'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def selectAllUserlist(self):
        """查询除admin外的所有用户名"""
        sql = "SELECT username FROM users WHERE username != 'admin'"
        self.cursor.execute(sql)
        return self.cursor.fetchall()


if __name__ == "__main__":
    userdb = UserDB()
    print("first print...")
    print(userdb.selectAllUser())
    userdb.addUser("admin", "123456", "11111111111")
    print("second print...")
    print(userdb.selectAllUser())
