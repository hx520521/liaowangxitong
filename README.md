# 智能瞭望数据分析处理系统

## 项目介绍

智能瞭望数据分析处理系统是一个基于Python Flask框架开发的Web应用，集成了百度搜索引擎爬虫功能，用于数据采集、存储和管理。系统提供了用户登录、搜索查询、数据展示、批量保存和数据仓库管理等功能。

## 技术栈

- **后端框架**: Flask
- **数据库**: SQLite
- **爬虫技术**: Python Requests + BeautifulSoup4
- **前端**: HTML5 + CSS3 + JavaScript
- **开发环境**: Python 3.8+

## 项目结构

```
.
├── app.py                 # Flask应用主文件
├── models.py              # 数据库模型定义
├── routes.py              # 路由定义
├── baidu_spider.py        # 百度爬虫类
├── init_db.py             # 数据库初始化脚本
├── venv/                  # Python虚拟环境
└── app/
    ├── data/              # 数据存储目录
    │   └── database.db    # SQLite数据库文件
    ├── static/            # 静态资源目录
    └── templates/         # 模板文件目录
        ├── login.html         # 登录页面
        ├── dashboard.html     # 后台主页
        ├── search_results.html # 搜索结果页面
        └── data_warehouse.html # 数据仓库页面
```

## 功能特性

### 1. 用户登录系统
- 默认管理员账号：admin/admin888
- 会话管理和权限控制

### 2. 百度搜索功能
- 支持动态参数搜索
- 配置了合理的请求头
- 解析搜索结果的标题、摘要、URL和封面图片

### 3. 数据展示与管理
- 搜索结果以列表形式展示
- 支持结果项的选择与批量保存
- 数据仓库支持按日期和关键词检索

### 4. 响应式设计
- 适配不同屏幕尺寸
- 现代化的UI设计
- 良好的用户交互体验

## 安装与配置

### 1. 创建虚拟环境
```bash
python3 -m venv venv
```

### 2. 激活虚拟环境

Windows系统:
```bash
venv\Scripts\activate
```

Linux/macOS系统:
```bash
source venv/bin/activate
```

### 3. 安装依赖包
```bash
pip install flask beautifulsoup4 requests flask_sqlalchemy
```

### 4. 初始化数据库
```bash
python init_db.py
```

## 运行应用

```bash
python app.py
```

应用将在 http://127.0.0.1:5000 启动

## 使用指南

### 1. 登录系统
- 访问 http://127.0.0.1:5000
- 使用默认账号密码登录：admin/admin888

### 2. 进行搜索
- 在后台主页输入搜索关键词
- 点击"搜索"按钮获取百度搜索结果

### 3. 保存搜索结果
- 在搜索结果页面选择需要保存的结果项
- 点击"保存选中结果"按钮保存到数据库

### 4. 管理数据仓库
- 点击"数据仓库"进入数据管理页面
- 可使用关键词搜索和日期筛选功能
- 点击结果标题可跳转到原始网页

## 开发日志

### 开发环境搭建
- 创建Python虚拟环境
- 安装Flask框架及相关依赖
- 配置项目目录结构

### 数据库设计
- 设计User和SearchResult两个数据模型
- 配置SQLAlchemy与SQLite连接
- 实现数据库初始化脚本

### 爬虫开发
- 实现百度搜索引擎爬虫
- 配置请求头模拟浏览器访问
- 解析HTML提取搜索结果数据

### Web应用开发
- 实现用户认证系统
- 开发搜索功能和结果展示
- 实现数据保存和仓库管理
- 创建响应式前端界面

## 注意事项

1. 爬虫功能仅用于学习和研究目的，请勿用于商业用途
2. 请遵守相关网站的robots协议
3. 频繁的请求可能会导致IP被封禁，建议合理使用
4. 系统使用SQLite数据库，适合小型应用部署

## 未来计划

1. 实现数据导出功能
2. 增加AI数据分析功能
3. 支持生成PDF报告
4. 优化爬虫性能和稳定性
5. 增加用户角色和权限管理

## 许可证

MIT License