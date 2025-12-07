from app import app, db
from models import User, SearchResult, CrawlRule, CrawledContent, ContentDetails, DataSource, IndustryTag, DataSourceTag, Spider, SpiderTest
from sqlalchemy import text

# 创建应用上下文
with app.app_context():
    # 检查CrawlRule表是否需要添加rule_name字段
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = inspector.get_columns('crawl_rule')
    column_names = [col['name'] for col in columns]
    
    if 'rule_name' not in column_names:
        # 使用原始SQL添加rule_name字段
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE crawl_rule ADD COLUMN rule_name VARCHAR(100) NOT NULL DEFAULT ""'))
            conn.execute(text('CREATE INDEX ix_crawl_rule_rule_name ON crawl_rule(rule_name)'))
            conn.commit()
        print("已添加rule_name字段到crawl_rule表")
    
    # 创建所有表（如果不存在）
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