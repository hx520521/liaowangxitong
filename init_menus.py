from app import app, db
from models import Menu

# 初始化菜单数据
def init_menus():
    with app.app_context():
        # 检查是否已有菜单数据
        if Menu.query.count() > 0:
            print('菜单数据已存在，跳过初始化')
            return
        
        # 创建一级菜单
        menus = [
            Menu(name='搜索采集', url='/dashboard', order=1, is_active=True),
            Menu(name='数据仓库', url='/data_warehouse', order=2, is_active=True),
            Menu(name='规则库管理', url='/rule_library', order=3, is_active=True),
            Menu(name='深度内容管理', url='/content_details', order=4, is_active=True),
            Menu(name='AI模型引擎', url='/ai_engines', order=5, is_active=True),
            Menu(name='爬虫管理', url='/spiders', order=6, is_active=True),
            Menu(name='聊天室', url='/chatrooms', order=7, is_active=True),
            Menu(name='用户中心', url='/user_center', order=8, is_active=True),
            Menu(name='菜单管理', url='/menus', order=9, is_active=True),
        ]
        
        # 创建聊天室的二级菜单
        chatrooms_menu = Menu.query.filter_by(name='聊天室').first()
        if chatrooms_menu:
            chatrooms_menu.children.append(Menu(name='创建聊天室', url='/create_chatroom', order=1, is_active=True))
        
        # 添加到数据库
        for menu in menus:
            db.session.add(menu)
        
        db.session.commit()
        print('菜单数据初始化完成')

if __name__ == '__main__':
    init_menus()