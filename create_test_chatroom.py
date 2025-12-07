from app import app, db
from models import ChatRoom, User, UserChatRoom
from datetime import datetime

# 创建测试聊天室
with app.app_context():
    # 获取测试用户
    test_user = User.query.filter_by(username='testuser').first()
    
    if not test_user:
        print("测试用户不存在，请先运行create_test_user.py")
        exit()
    
    # 创建聊天室
    chat_room = ChatRoom(
        name='AI测试聊天室',
        description='用于测试AI指令功能的聊天室',
        is_public=True,
        created_by=test_user.id,
        created_at=datetime.now()
    )
    
    db.session.add(chat_room)
    db.session.commit()
    
    # 将测试用户添加到聊天室
    user_chat_room = UserChatRoom(
        user_id=test_user.id,
        room_id=chat_room.id,
        joined_at=datetime.now()
    )
    
    db.session.add(user_chat_room)
    db.session.commit()
    
    print("测试聊天室创建成功")
    print(f"聊天室ID: {chat_room.id}")
    print(f"聊天室名称: {chat_room.name}")
