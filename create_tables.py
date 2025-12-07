from app import app, db

# 在应用上下文中创建所有数据库表
with app.app_context():
    # 导入所有模型以确保它们被注册
    from models import *
    # 创建所有表
    db.create_all()
    print("数据库表创建成功！")