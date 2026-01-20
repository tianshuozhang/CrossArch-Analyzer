# coding=UTF-8
from flask import Flask
from app import app


@app.route("/")  # 装饰器，url，路由
def index():  # 试图函数
    return "hello world"


if __name__ == "__main__":
    # app.config["SECRET_KEY"] = "TPmi4aLWRbyVq8zu9v82dWYW1"
    app.config["JWT_SECRET_KEY"] = "CbE5qy48I-LsotmKrm9BgOVFiQVqc4lNJW6uqzcXJtI"
    app.config["ROOT"] = os.path.dirname(os.path.abspath(__file__))

    app.run(port=5000)
