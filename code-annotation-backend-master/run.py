# coding=UTF-8
import os
import sys

os.chdir("../")
print(os.getcwd())
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "LLM"))
sys.path.append(os.path.join(os.getcwd(), "LLM/core"))

from flask import Flask
from app import app


@app.route("/")  # 装饰器，url，路由
def index():  # 试图函数
    return "hello world"


if __name__ == "__main__":
    app.config["SECRET_KEY"] = "TPmi4aLWRbyVq8zu9v82dWYW1"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config["UPLOAD_ROOT"] = os.path.join(BASE_DIR, "uploads")
    app.run(port=5000)
