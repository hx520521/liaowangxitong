from app import app, db
from models import Menu

# 添加用户中心菜单到数据库
def add_user_center_menu():
    with app.app_context():
        # 检查用户中心菜单是否已存在
        user_center_menu = Menu.query.filter_by(name='用户中心').first()
        if user_center_menu:
            print('用户中心菜单已存在')
            return
        
        # 获取菜单管理菜单，以便调整顺序
        menu_management = Menu.query.filter_by(name='菜单管理').first()
        if menu_management:
            # 调整菜单管理的顺序为9
            menu_management.order = 9
        
        # 创建用户中心菜单
        new_menu = Menu(
            name='用户中心',
            url='/user_center',
            order=8,
            is_active=True
        )
        
        # 添加到数据库
        db.session.add(new_menu)
        db.session.commit()
        print('用户中心菜单已添加')

if __name__ == '__main__':
    add_user_center_menu()