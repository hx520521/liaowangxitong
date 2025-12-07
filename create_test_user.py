from app import app, db
from models import User
from datetime import datetime

# 创建测试用户
with app.app_context():
    # 检查是否已经存在测试用户
    existing_user = User.query.filter_by(username='testuser').first()
    
    if existing_user:
        print("测试用户已存在")
    else:
        # 创建新用户
        test_user = User(
            username='testuser',
            password='testpassword',
            created_at=datetime.now()
        )
        
        db.session.add(test_user)
        db.session.commit()
        print("测试用户创建成功")
        print(f"用户名: testuser")
        print(f"密码: testpassword")
