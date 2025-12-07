from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates'))
app.secret_key = 'your_secret_key_here'  # 用于会话管理

# 配置SQLite数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'app', 'data', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 导入路由
from routes import *

# 创建数据库表
with app.app_context():
    from models import *
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)