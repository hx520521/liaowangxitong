from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 密码加密方法
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    # 密码验证方法
    def check_password(self, password):
        return check_password_hash(self.password, password)



# 爬取规则模型
class CrawlRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), nullable=False, index=True)
    rule_name = db.Column(db.String(100), nullable=False, index=True)  # 规则名称，用于区分不同的规则
    title_xpath = db.Column(db.String(200), nullable=True)
    content_xpath = db.Column(db.String(200), nullable=True)
    headers = db.Column(db.JSON, nullable=True)  # 存储request headers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CrawlRule {self.rule_name}>'

# 采集内容模型
class CrawledContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('search_result.id'), nullable=False, index=True)
    search_result = db.relationship('SearchResult', backref=db.backref('crawled_contents', lazy=True))
    rule_id = db.Column(db.Integer, db.ForeignKey('crawl_rule.id'), nullable=False, index=True)
    crawl_rule = db.relationship('CrawlRule', backref=db.backref('crawled_contents', lazy=True))
    title = db.Column(db.String(200), nullable=True)  # 采集到的标题
    content = db.Column(db.Text, nullable=True)  # 采集到的内容
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, success, failed
    error_message = db.Column(db.Text, nullable=True)  # 错误信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CrawledContent {self.id}>'

# 详细内容模型
class ContentDetails(db.Model):
    __tablename__ = 'content_details'
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('crawled_content.id'), nullable=False, index=True)
    crawled_content = db.relationship('CrawledContent', backref=db.backref('content_details', lazy=True))
    field_name = db.Column(db.String(100), nullable=False)  # 字段名称
    field_value = db.Column(db.Text, nullable=True)  # 字段值
    field_type = db.Column(db.String(50), nullable=False, default='text')  # 字段类型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ContentDetails {self.field_name}>'

# AI模型引擎模型
class AIEngine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 引擎名称
    api_base = db.Column(db.String(200), nullable=False)  # API地址
    api_key = db.Column(db.String(200), nullable=False)  # API密钥
    model_name = db.Column(db.String(100), nullable=False)  # 模型名称
    provider = db.Column(db.String(50), nullable=False)  # 提供商
    description = db.Column(db.Text, nullable=True)  # 描述
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AIEngine {self.name}>'

# 模型token消耗统计模型
class TokenUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engine_id = db.Column(db.Integer, db.ForeignKey('ai_engine.id'), nullable=False, index=True)
    engine = db.relationship('AIEngine', backref=db.backref('token_usages', lazy=True))
    prompt_tokens = db.Column(db.Integer, nullable=False)  # 提示token数
    completion_tokens = db.Column(db.Integer, nullable=False)  # 完成token数
    total_tokens = db.Column(db.Integer, nullable=False)  # 总token数
    usage_date = db.Column(db.Date, default=datetime.utcnow().date)  # 使用日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TokenUsage {self.id}>'

# 数据源模型
class DataSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 数据源名称
    type = db.Column(db.String(50), nullable=False)  # 数据源类型（如：搜索引擎、新闻网站、API等）
    base_url = db.Column(db.String(200), nullable=False)  # 基础URL
    description = db.Column(db.Text, nullable=True)  # 描述
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DataSource {self.name}>'

# 行业标签模型
class IndustryTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 标签名称
    description = db.Column(db.Text, nullable=True)  # 描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<IndustryTag {self.name}>'

# 数据源与行业标签关联模型
class DataSourceTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False, index=True)
    industry_tag_id = db.Column(db.Integer, db.ForeignKey('industry_tag.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 定义唯一约束，确保一个数据源不能重复添加同一个标签
    __table_args__ = (db.UniqueConstraint('data_source_id', 'industry_tag_id', name='_data_source_tag_uc'),)

# 爬虫模型
class Spider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 爬虫名称
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False, index=True)
    data_source = db.relationship('DataSource', backref=db.backref('spiders', lazy=True))
    spider_class = db.Column(db.String(100), nullable=False)  # 爬虫类名
    config = db.Column(db.JSON, nullable=True)  # 爬虫配置
    description = db.Column(db.Text, nullable=True)  # 描述
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Spider {self.name}>'

# 爬虫测试模型
class SpiderTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spider_id = db.Column(db.Integer, db.ForeignKey('spider.id'), nullable=False, index=True)
    spider = db.relationship('Spider', backref=db.backref('tests', lazy=True))
    test_query = db.Column(db.String(200), nullable=False)  # 测试查询词
    test_results = db.Column(db.JSON, nullable=True)  # 测试结果
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, success, failed
    error_message = db.Column(db.Text, nullable=True)  # 错误信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SpiderTest {self.id}>'

# 更新SearchResult模型，添加与数据源和爬虫的关联
class SearchResult(db.Model):
    __tablename__ = 'search_result'  # 显式指定表名，避免与旧表冲突
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)
    search_keyword = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(50), nullable=False, default='百度搜索')
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=True, index=True)
    data_source = db.relationship('DataSource', backref=db.backref('search_results', lazy=True))
    spider_id = db.Column(db.Integer, db.ForeignKey('spider.id'), nullable=True, index=True)
    spider = db.relationship('Spider', backref=db.backref('search_results', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchResult {self.title}>'

# 聊天室模型
class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 聊天室名称
    description = db.Column(db.Text, nullable=True)  # 聊天室描述
    is_public = db.Column(db.Boolean, default=True)  # 是否公开
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 创建者
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联用户
    creator = db.relationship('User', backref=db.backref('created_chatrooms', lazy=True))

    def __repr__(self):
        return f'<ChatRoom {self.name}>'

# 聊天消息模型
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False, index=True)  # 所属聊天室
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # 发送者
    content = db.Column(db.Text, nullable=False)  # 消息内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 发送时间

    # 关联关系
    room = db.relationship('ChatRoom', backref=db.backref('messages', lazy=True, order_by='ChatMessage.created_at'))
    user = db.relationship('User', backref=db.backref('chat_messages', lazy=True))

    def __repr__(self):
        return f'<ChatMessage {self.id} from {self.user.username} in {self.room.name}>'

# 用户与聊天室的关联模型（用于管理用户加入的聊天室）
class UserChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 定义唯一约束，确保一个用户只能加入一个聊天室一次
    __table_args__ = (db.UniqueConstraint('user_id', 'room_id', name='_user_room_uc'),)

    # 关联关系
    user = db.relationship('User', backref=db.backref('joined_rooms', lazy=True))
    room = db.relationship('ChatRoom', backref=db.backref('members', lazy=True))

# 菜单模型
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 菜单名称
    url = db.Column(db.String(100), nullable=False)  # 菜单URL
    icon = db.Column(db.String(50), nullable=True)  # 菜单图标（可选）
    parent_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=True, default=None)  # 父菜单ID
    order = db.Column(db.Integer, default=0)  # 菜单排序
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 自引用关系
    parent = db.relationship('Menu', remote_side=[id], backref=db.backref('children', lazy=True))

    def __repr__(self):
        return f'<Menu {self.name}>'