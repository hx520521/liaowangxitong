from app import app, db
from models import User

# 创建应用上下文
with app.app_context():
    # 创建所有表
    db.create_all()
    
    # 检查是否已有默认管理员用户
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        # 创建默认管理员用户
        admin = User(username='admin', password='admin888')
        db.session.add(admin)
        db.session.commit()
        print("默认管理员用户创建成功: admin/admin888")
    else:
        print("默认管理员用户已存在")