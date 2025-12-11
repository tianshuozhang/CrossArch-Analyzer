from app.User import User
from flask import request, session, jsonify, render_template

from db.db_user import UserDB
from db.db_code import CodeDB

user_DB = UserDB()
code_DB = CodeDB()


@User.route("/")
def hello_world():
    return "hello to Login!"


@User.route("/cur_user", methods=["GET"])
def cur_user():
    username = session.get("username")
    if username == None:
        return jsonify({"state": "fail", "description": "Not logged in"})
    else:
        return jsonify({"state": "success", "username": username})


@User.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user_id = user_DB.getUserId(username)
    if user_id == None:
        return jsonify(
            {"state": "fail", "description": "No user information, please sign up"}
        )
    ok = user_DB.checkUser(username, password)
    if not ok:
        return jsonify(
            {
                "state": "fail",
                "description": "Please enter the correct username and password",
            }
        )
    session["username"] = username
    return jsonify({"state": "success", "description": "Success"})


@User.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    existed = user_DB.checkSameUsername(username)
    if existed:
        return jsonify(
            {
                "state": "fail",
                "description": "The username has been used, please change the username and try again",
            }
        )
    user_DB.addUser(username, password)
    return jsonify({"state": "success", "description": "success"})


@User.route("/exit", methods=["GET"])
def exit():
    res = session.get("username")
    if res == None:
        return jsonify({"state": "fail", "description": "Not logged in"})
    else:
        session["username"] = None
        return jsonify({"state": "success", "description": "success"})


@User.route("/modifyPassword", methods=["POST"])
def modifyPassword():
    username = request.form.get("username")
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    user_id = user_DB.getUserId(username)
    if user_id == None:
        return jsonify(
            {"state": "fail", "description": "Please enter the correct username"}
        )
    ok = user_DB.checkUser(username, old_password)
    if not ok:
        return jsonify(
            {"state": "fail", "description": "Please enter the correct old password"}
        )
    if new_password == old_password:
        return jsonify(
            {
                "state": "fail",
                "description": "Please enter a new password different from the old one",
            }
        )
    else:
        user_DB.updatePassword(username, new_password)
        return jsonify({"state": "success", "description": "success"})


# # 两个函数，用于将flask_sql的输出转化为可以直接网络传输的json格式
# # 用法：直接调用classlist2dictlist，输入可以是单个object或者多个object的列表
# def class2dict(class_entry):
#     ret = {}
#     remove_keys = ["_sa_instance_state"]
#     for e in class_entry.__dict__:
#         if e in remove_keys:
#             continue
#         ret[e] = class_entry.__dict__[e]
#     return ret


# def classlist2dictlist(class_entries):
#     if type(class_entries) != type([]):
#         class_entries = [class_entries]
#     ret_list = [class2dict(e) for e in class_entries]
#     return ret_list

# @User.route("/removeUser", methods=["POST", "GET"])
# def removeUser():
#     if request.method == "GET":
#         username = request.args.get("username")
#         telphone = request.args.get("telphone")
#         password = request.args.get("password")
#     else:
#         username = request.form.get("username")
#         telphone = request.form.get("telphone")
#         password = request.form.get("password")
#     res = user.checkUser(username, password, telphone)
#     if res == None:
#         return jsonify(
#             {
#                 "state": "fail",
#                 "description": "The input information is wrong, delete failed",
#             }
#         )
#     else:
#         user.removeUser(username, password, telphone)
#         markDB.admin_removeUser(username)
#         labelDB.admin_removeUser(username)
#         codeDB.admin_removeUser(username)
#         return jsonify({"state": "success", "description": "success"})


# @User.route("/getUserlist", methods=["POST"])
# def getUserlist():
#     adminpassword = request.form.get("adminpassword")
#     res = user.GetAdminPassword()
#     temp = list(res.values())
#     res_p = temp[0]
#     if adminpassword != res_p:
#         return jsonify({"state": "fail", "description": "Wrong password"})
#     else:
#         rst = user.selectAllUser()
#         return jsonify({"state": "success", "rst": rst})


# @User.route("/admin_removeUser", methods=["POST"])
# def admin_removeUser():
#     adminpassword = request.form.get("adminpassword")
#     username = request.form.get("username")
#     res = user.GetAdminPassword()
#     temp = list(res.values())
#     res_p = temp[0]
#     if adminpassword != res_p:
#         return jsonify({"state": "fail", "description": "Wrong password"})
#     res_n = user.admin_checkUser(username)
#     if res_n == None:
#         return jsonify(
#             {
#                 "state": "fail",
#                 "description": "The input information is wrong, delete failed",
#             }
#         )
#     else:
#         user.admin_removeUser(username)
#         markDB.admin_removeUser(username)
#         labelDB.admin_removeUser(username)
#         codeDB.admin_removeUser(username)
#         return jsonify({"state": "success", "description": "success"})
