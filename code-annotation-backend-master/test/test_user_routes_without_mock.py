# tests/test_project_routes_integration.py
import pytest
import jwt
import os, shutil, json
from io import BytesIO
from datetime import datetime, timezone, timedelta
from werkzeug.datastructures import FileStorage
from test.test_helper import (
    make_a_post,
    make_a_zip,
    user_init,
    make_a_get,
    assert_zip,
    assert_dir,
)

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
    from app.Analysis import Analysis

    app.register_blueprint(User, url_prefix="/user")
    app.register_blueprint(Project, url_prefix="/project")
    app.register_blueprint(Analysis, url_prefix="/analysis")

    return app


@pytest.fixture
def test_client(app):
    """创建测试客户端"""
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestProjectIntegration:
    """集成测试项目功能，不使用mock"""

    def test_project_end_to_end_flow_basic(self, test_client):
        """测试完整的项目流程：添加 -> 列表 -> 打开 -> 获取树 -> 关闭 -> 删除"""

        headers = user_init(TEST_DIR, test_client)

        # 2. 添加项目
        test_file = make_a_zip()
        rst = make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/add",
            data={"file": test_file},
            print_content=[["project_id"], ["project_name"]],
            assert_content=[(1, "project_id"), ("test_project", "project_name")],
        )
        project_id = rst["project_id"]
        # 3. 获取项目列表
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/get_project_list",
            data={},
        )
        # 4. 打开项目
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/open",
            data={"project_id": str(project_id)},
        )
        # 5. 删除项目
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/delete",
            data={"project_id": str(project_id)},
        )

    def test_analysis_basic(self, test_client):
        headers = user_init(TEST_DIR, test_client)
        project_1 = make_a_zip(
            zip_base_name="project_1",
            zip_content=["src/hello.cpp", "graph/", "hello/"],
        )
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/add",
            data={"file": project_1},
        )
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/analysis/analysis",
            data={"project_id": str(1)},
        )
        import time

        while True:
            r = make_a_get(
                test_client=test_client,
                headers=headers,
                url="/analysis/progress",
                data={"task_id": str(1)},
            )
            print(f"query once==>{r['progress']}")
            if r["progress"] == 100:
                break
            time.sleep(1)

    def test_project_end_to_end_flow_project(self, test_client):
        """测试的完整项目流程：
        上传1 -> 添加另一个项目2 -> 打开项目2 ->
        删除项目1 -> 添加项目3 -> 删除项目2 ->
        打开项目3 -> 获取项目3的目录树 ->获取项目列表 -> 删除3"""
        headers = user_init(TEST_DIR, test_client)
        project_1 = make_a_zip(
            zip_base_name="project_1",
            zip_content=["src/hello.cpp", "graph/", "hello/"],
        )
        # 1. 添加项目1
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/add",
            data={"file": project_1},
            print_content=[["project_id"], ["project_name"]],
            assert_content=[(1, "project_id"), ("project_1", "project_name")],
        )
        assert_zip(
            os.path.join(TEST_DIR, "data", "1", "project", "1.zip"),
            {
                "content": {
                    "graph": {},
                    "hello": {},
                    "src": {"hello.cpp": None},
                },
                "graph": {},
                "tree.json": None,
            },
        )
        # 2. 添加项目2
        project_2 = make_a_zip(
            zip_base_name="project_2",
            zip_content=["src/eigen.cpp", "eigen/", "hello/world/"],
        )
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/add",
            data={"file": project_2},
            print_content=[["project_id"], ["project_name"]],
            assert_content=[(2, "project_id"), ("project_2", "project_name")],
        )
        assert_zip(
            os.path.join(TEST_DIR, "data", "1", "project", "2.zip"),
            {
                "content": {
                    "eigen": {},
                    "hello": {"world": {}},
                    "src": {"eigen.cpp": None},
                },
                "graph": {},
                "tree.json": None,
            },
        )
        # 3. 打开项目2

        # 4. 删除项目1
        make_a_post(
            test_client=test_client,
            headers=headers,
            url="/project/delete",
            data={"project_id": 1},
        )
        assert_dir(
            os.path.join(TEST_DIR, "data", "1", "project"),
            {"2.zip": None},
        )
        # assert_dir(
        #     os.path.join(TEST_DIR, "data", "1", "open"),
        #     {
        #         "content": {
        #             "eigen": {},
        #             "hello": {"world": {}},
        #             "src": {"eigen.cpp": None},
        #         },
        #         "graph": {},
        #         "tree.json": None,
        #     },
        # )
        # ---
        # make_a_get(
        #     test_client=test_client,
        #     headers=headers,
        #     url="/project/get-tree",
        #     data={"project_id": 1},
        #     print_content=[["file_tree"]],
        #     assert_content=[(1, "project_id")],
        # )
