# tests/test_project_routes_integration.py
import pytest
import jwt
import os, shutil, json
from io import BytesIO
from datetime import datetime, timezone, timedelta
from werkzeug.datastructures import FileStorage
from test.test_helper import make_a_post, make_a_zip, user_init

# 获取测试文件所在目录
TEST_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def app():
    """创建Flask应用实例"""
    from flask import Flask

    # 创建Flask应用
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test_secret_key"
    app.config["ROOT"] = TEST_DIR

    # 注册蓝图
    from app.User import User
    from app.Project import Project

    app.register_blueprint(User, url_prefix="/user")
    app.register_blueprint(Project, url_prefix="/project")

    return app


@pytest.fixture
def test_client(app):
    """创建测试客户端"""
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestProjectIntegration:
    """集成测试项目功能，不使用mock"""

    def test_project_end_to_end_flow(self, test_client):
        """测试完整的项目流程：添加 -> 列表 -> 打开 -> 获取树 -> 关闭 -> 删除"""

        def _user():

            def _clean_up():
                """清理测试数据"""
                if os.path.exists(os.path.join(TEST_DIR, "data", "1")):
                    shutil.rmtree(os.path.join(TEST_DIR, "data", "1"))

                from db.db_project import ProjectDB
                from db.db_file import FileDB
                from db.db_user import UserDB
                from db.db_archTag import ArchTagDB
                from db.db_relation import RelationDB
                from db.db_task import TaskDB
                from db.db_visualData import VisualizationDataDB
                from db.db_mysql import DBc

                project_db = ProjectDB()
                file_db = FileDB()
                user_db = UserDB()
                arch_tag_db = ArchTagDB()
                relation_db = RelationDB()
                task_db = TaskDB()
                graph_db = VisualizationDataDB()

                graph_db.clear()
                task_db.clear()
                relation_db.clear()
                arch_tag_db.clear()
                file_db.clear()
                project_db.clear()
                user_db.clear()

                user_db = UserDB()
                project_db = ProjectDB()
                file_db = FileDB()
                arch_tag_db = ArchTagDB()
                relation_db = RelationDB()
                task_db = TaskDB()
                graph_db = VisualizationDataDB()

            _clean_up()
            # 1. 创建有效的JWT token
            SECRET_KEY = "test_secret_key"
            response = test_client.post(
                "/user/register",
                data={"username": "test_user", "password": "test_password"},
            )
            assert response.status_code == 201
            response = test_client.post(
                "/user/login",
                data={"username": "test_user", "password": "test_password"},
            )
            json_data = response.get_json()
            token = json_data["rst"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            return headers

        headers = _user()

        def _zip():
            import zipfile

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                zip_file.writestr("src/hello.cpp", "print('hello world')\n")
                zip_file.writestr("src/main.py", "print('hello world')\n")
                zip_file.writestr("include/hello.h", "#include <iostream>\n")
                zip_file.writestr(
                    "CMakeLists.txt", "cmake_minimum_required(VERSION 3.0)\n"
                )
            zip_buffer.seek(0)
            test_file = (zip_buffer, "test_project.zip")
            return test_file

        # 2. 添加项目
        test_file = _zip()
        response = test_client.post(
            "/project/add",
            data={"file": test_file},
            content_type="multipart/form-data",
            headers=headers,
        )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["state"] == "success"
        assert json_data["description"] == "成功添加项目"
        assert json_data["rst"]["project_id"] == 1
        assert json_data["rst"]["project_name"] == "test_project"

        project_id = json_data["rst"]["project_id"]

        # 3. 获取项目列表
        response = test_client.post(
            "/project/get_project_list", data={}, headers=headers
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["state"] == "success"
        assert json_data["description"] == "成功获取项目列表"

        assert len(json_data["rst"]["list"]) >= 1
        # 4. 打开项目
        response = test_client.post(
            "/project/open", data={"project_id": str(project_id)}, headers=headers
        )

        assert response.status_code == 200
        json_data = response.get_json()
        if "msg" in json_data["rst"]:
            print(json_data["rst"]["msg"])
        assert "file_tree" in json_data["rst"]
        # tree = json_data["rst"]["file_tree"]
        # print(json.dumps(tree, indent=2))
        # 5. 删除项目
        response = test_client.post(
            "/project/delete", data={"project_id": str(project_id)}, headers=headers
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["state"] == "success"
        assert json_data["description"] == "成功删除项目"

    def test_project_end_to_end_flow_2(self, test_client):
        """测试的完整项目流程：
        上传1 -> 添加另一个项目2 -> 打开项目2 ->
        删除项目1 -> 添加项目3 -> 删除项目2 ->
        打开项目3 -> 获取项目3的目录树 ->获取项目列表 -> 删除3"""
        headers = user_init(TEST_DIR, test_client)
        project_1 = make_a_zip()


class TestProjectRoutesWithoutAuth:
    """测试无认证情况下的项目路由"""

    def test_get_project_list_without_auth(self, test_client):
        """测试没有认证时获取项目列表"""
        response = test_client.post("/project/get_project_list", data={})
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["state"] == "fail"
        assert json_data["description"] == "请提供有效的 Token"

    def test_add_project_without_auth(self, test_client):
        """测试没有认证时添加项目"""
        test_file = (BytesIO(b"print('hello world')\n"), "test_project.py")
        response = test_client.post(
            "/project/add", data={"file": test_file}, content_type="multipart/form-data"
        )
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["state"] == "fail"
        assert json_data["description"] == "请提供有效的 Token"

    def test_upload_project_without_auth(self, test_client):
        """测试没有认证时上传项目"""
        test_file = (BytesIO(b"print('hello world')\n"), "test_project.py")
        response = test_client.post(
            "/project/upload",
            data={"file": test_file},
            content_type="multipart/form-data",
        )
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["state"] == "fail"
        assert json_data["description"] == "请提供有效的 Token"


class TestProjectWithInvalidAuth:
    """测试无效认证情况下的项目路由"""

    def test_get_project_list_with_invalid_token(self, test_client):
        """测试使用无效token获取项目列表"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.post(
            "/project/get_project_list", data={}, headers=headers
        )
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["state"] == "fail"
        assert json_data["description"] == "无效的 Token"

    def test_add_project_with_expired_token(self, test_client):
        """测试使用过期token添加项目"""
        SECRET_KEY = "test_secret_key"
        expired_token = jwt.encode(
            {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            SECRET_KEY,
            algorithm="HS256",
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        test_file = (BytesIO(b"print('hello world')\n"), "test_project.py")
        response = test_client.post(
            "/project/add",
            data={"file": test_file},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["state"] == "fail"
        assert json_data["description"] == "Token 已过期"
