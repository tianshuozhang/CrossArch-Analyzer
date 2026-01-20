import os, shutil, zipfile, random, string

from io import BytesIO


def user_init(TEST_DIR, test_client):

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


def make_a_zip(
    zip_base_name="test_project",
    zip_content=[
        "src/hello.cpp",
        "src/main.py",
        "include/hello.h",
        "CMakeLists.txt",
    ],
):
    def gen_random_str(length=100):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_path in zip_content:
            zip_file.writestr(file_path, gen_random_str())
    zip_buffer.seek(0)
    test_file = (zip_buffer, zip_name + ".zip")
    return test_file


def make_a_post(test_client, headers, data: dict, print_content=[], assert_content=[]):
    """data是前端表格输入的键值对，print_content是列表，每一项是要打印的内容的各个键的名字列表，assert_content是列表，每一项是两个元素，第一个元素是预期结果，第二个元素是响应的键的列表"""
    response = test_client.post(
        "/project/add",
        data=data,
        content_type="multipart/form-data",
        headers=headers,
    )
    json_data = response.get_json()
    for print_item in print_content:
        start = json_data["rst"][print_item[0]]
        prefix = f"response[{print_item[0]}]"
        for name in print_item[1:]:
            prefix += f"[{name}]"
            start = start[name]
        print(f"{prefix}={start}")
    for assert_item in assert_content:
        left = assert_item[0]
        right = json_data["rst"][assert_item[1]]
        for name in assert_item[2:]:
            right = right[name]
        assert right == left


# TODO:现在还没验证get的情况


def make_a_get():
    pass
