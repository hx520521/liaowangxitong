from app import app, db
from models import User

# 检查AI用户是否存在
with app.app_context():
    # 查询ID为1的用户
    ai_user = User.query.filter_by(id=1).first()
    
    if ai_user:
        print(f"AI用户存在: ID={ai_user.id}, 用户名={ai_user.username}")
    else:
        print("AI用户不存在！需要创建一个ID为1的用户")
        
        # 列出所有用户
        users = User.query.all()
        if users:
            print("现有用户:")
            for user in users:
                print(f"ID={user.id}, 用户名={user.username}")
        else:
            print("数据库中没有用户")
