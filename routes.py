from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
from app import app, db
from models import User, SearchResult, CrawlRule, CrawledContent, ContentDetails, AIEngine, TokenUsage, DataSource, IndustryTag, DataSourceTag, Spider, SpiderTest, ChatRoom, ChatMessage, UserChatRoom, Menu
from baidu_spider import BaiduSpider, BingSpider
from sqlalchemy import or_
import openai
import json
from urllib.parse import urlparse
import datetime
import time
import importlib

# 首页/登录页
@app.route('/')
def index():
    return render_template('login.html')

# 登录页面
@app.route('/login')
def login_page():
    return render_template('login.html')

# 登录处理
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # 验证用户
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error='用户名或密码错误')

# 登出处理
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 注册页面
@app.route('/register')
def register_page():
    return render_template('register.html')

# 注册处理
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # 验证密码是否一致
    if password != confirm_password:
        return render_template('register.html', error='两次输入的密码不一致')
    
    # 验证用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return render_template('register.html', error='用户名已存在')
    
    # 创建新用户
    new_user = User(username=username)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return render_template('register.html', success='注册成功，请登录')
    except Exception as e:
        db.session.rollback()
        return render_template('register.html', error=f'注册失败: {str(e)}')

# 后台主页
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    # 获取顶级功能菜单（排除菜单管理）
    top_menus = Menu.query.filter_by(parent_id=None).filter_by(is_active=True).filter(Menu.name != '菜单管理').order_by(Menu.order).all()
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    return render_template('dashboard.html', username=session['username'], top_menus=top_menus, left_menus=left_menus)

# 用户中心页面
@app.route('/user_center')
def user_center():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有用户
    users = User.query.all()
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('user_center.html', users=users, left_menus=left_menus, message=request.args.get('message'), success=request.args.get('success'))

# 新增用户处理
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # 验证密码是否一致
    if password != confirm_password:
        return redirect(url_for('user_center', message='两次输入的密码不一致', success='false'))
    
    # 验证用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return redirect(url_for('user_center', message='用户名已存在', success='false'))
    
    # 创建新用户
    new_user = User(username=username)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('user_center', message='用户添加成功', success='true'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('user_center', message=f'添加失败: {str(e)}', success='false'))

# 编辑用户处理
@app.route('/edit_user', methods=['POST'])
def edit_user():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = request.form['user_id']
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('user_center', message='用户不存在', success='false'))
    
    # 验证用户名是否已被其他用户使用
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user.id:
        return redirect(url_for('user_center', message='用户名已存在', success='false'))
    
    # 更新用户名
    user.username = username
    
    # 如果提供了新密码，则更新密码
    if password:
        if password != confirm_password:
            return redirect(url_for('user_center', message='两次输入的密码不一致', success='false'))
        user.set_password(password)
    
    try:
        db.session.commit()
        return redirect(url_for('user_center', message='用户信息更新成功', success='true'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('user_center', message=f'更新失败: {str(e)}', success='false'))

# 删除用户处理
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 不能删除当前登录用户
    if user_id == session['user_id']:
        return redirect(url_for('user_center', message='不能删除当前登录用户', success='false'))
    
    # 查找用户
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('user_center', message='用户不存在', success='false'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('user_center', message='用户删除成功', success='true'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('user_center', message=f'删除失败: {str(e)}', success='false'))

# 测试页面
@app.route('/test_chat')
def test_chat():
    return render_template('test_chat.html')

# 搜索处理
@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    keyword = request.form['keyword']
    selected_engines = request.form.getlist('search_engines[]')
    
    # 实现多元搜索，根据用户选择的搜索引擎获取结果
    results = []
    
    # 如果没有选择任何搜索引擎，默认使用百度
    if not selected_engines:
        selected_engines = ['baidu']
    
    # 百度搜索
    if 'baidu' in selected_engines:
        try:
            baidu_spider = BaiduSpider()
            baidu_results = baidu_spider.search(keyword)
            results.extend(baidu_results)
        except Exception as e:
            print(f"百度搜索失败: {e}")
    
    # Bing搜索
    if 'bing' in selected_engines:
        try:
            bing_spider = BingSpider()
            bing_results = bing_spider.search(keyword)
            results.extend(bing_results)
        except Exception as e:
            print(f"Bing搜索失败: {e}")
    
    return render_template('search_results.html', results=results, keyword=keyword)

# 保存搜索结果
@app.route('/save_results', methods=['POST'])
def save_results():
    if 'user_id' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '请先登录'})
        else:
            return redirect(url_for('index'))
    
    results = request.form.getlist('results[]')
    keyword = request.form['keyword']
    saved_result_ids = []
    
    for result_str in results:
        # 解析结果字符串，格式：title|summary|url|cover_url
        parts = result_str.split('|')
        if len(parts) >= 4:
            title, summary, url, cover_url = parts[:4]
            
            # 检查是否已存在相同URL的结果
            existing = SearchResult.query.filter_by(url=url).first()
            if not existing:
                # 根据结果的source字段设置正确的来源名称
                source_name = '百度搜索' if parts[4] == 'baidu' else 'Bing搜索'
                result = SearchResult(
                    title=title,
                    summary=summary,
                    url=url,
                    cover_url=cover_url,
                    search_keyword=keyword,
                    source=source_name
                )
                db.session.add(result)
                db.session.flush()  # 获取ID但不提交
                saved_result_ids.append(result.id)
            else:
                saved_result_ids.append(existing.id)
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': '结果保存成功', 'result_ids': saved_result_ids})
    else:
        return redirect(url_for('data_warehouse', message='结果保存成功', success='true'))

# 数据仓库
@app.route('/data_warehouse')
def data_warehouse():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    date = request.args.get('date', '')
    message = request.args.get('message', '')
    success = request.args.get('success', 'false')
    
    # 构建查询
    query = SearchResult.query
    
    if keyword:
        query = query.filter(or_(SearchResult.title.contains(keyword), SearchResult.summary.contains(keyword), SearchResult.search_keyword.contains(keyword)))
    
    if date:
        # 筛选指定日期的数据
        # 使用DATE()函数提取日期部分进行比较，确保格式匹配
        from sqlalchemy import func
        query = query.filter(func.date(SearchResult.created_at) == date)
    
    # 按创建时间倒序排序
    results = query.order_by(SearchResult.created_at.desc()).all()
    
    # 获取所有采集规则
    all_rules = CrawlRule.query.all()
    domain_rules = {}
    for rule in all_rules:
        if rule.domain not in domain_rules:
            domain_rules[rule.domain] = []
        domain_rules[rule.domain].append(rule)
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    # 为每个结果添加域名信息和对应的采集规则
    for result in results:
        try:
            parsed_url = urlparse(result.url)
            result.domain = parsed_url.netloc
            # 查找匹配的采集规则
            result.crawl_rules = domain_rules.get(result.domain, [])
            # 如果有规则，选择第一个作为默认显示规则
            result.default_crawl_rule = result.crawl_rules[0] if result.crawl_rules else None
        except:
            result.domain = '未知域名'
            result.crawl_rules = []
            result.default_crawl_rule = None
    
    return render_template('data_warehouse.html', results=results, keyword=keyword, date=date, message=message, success=success, left_menus=left_menus)

# 嗅探功能API
@app.route('/sniff_url', methods=['POST'])
def sniff_url():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    url = request.form.get('url')
    if not url:
        return jsonify({'success': False, 'message': 'URL不能为空'}), 400
    
    try:
        spider = BaiduSpider()
        result = spider.sniff(url)
        
        if result:
            return jsonify({'success': True, 'message': '嗅探成功', 'data': result})
        else:
            return jsonify({'success': False, 'message': '嗅探失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'嗅探失败: {str(e)}'}), 500

# 保存或更新嗅探规则
@app.route('/save_crawl_rule', methods=['POST'])
def save_crawl_rule():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 获取表单数据
    rule_name = request.form.get('rule_name')
    domain = request.form.get('domain')
    title_xpath = request.form.get('title_xpath')
    content_xpath = request.form.get('content_xpath')
    headers_str = request.form.get('headers')
    
    # 验证必填字段
    if not rule_name or not domain:
        return jsonify({'success': False, 'message': '规则名称和域名不能为空'}), 400
    
    try:
        # 解析headers JSON字符串
        headers = json.loads(headers_str) if headers_str else None
        
        with app.app_context():
            # 检查是否已有该规则名称的规则
            existing_rule = CrawlRule.query.filter_by(rule_name=rule_name).first()
            
            if existing_rule:
                # 更新现有规则
                existing_rule.domain = domain
                existing_rule.title_xpath = title_xpath
                existing_rule.content_xpath = content_xpath
                existing_rule.headers = headers
                existing_rule.updated_at = datetime.utcnow()
                db.session.commit()
                return jsonify({'success': True, 'message': '规则更新成功'})
            else:
                # 创建新规则
                new_rule = CrawlRule(
                    rule_name=rule_name,
                    domain=domain,
                    title_xpath=title_xpath,
                    content_xpath=content_xpath,
                    headers=headers
                )
                db.session.add(new_rule)
                db.session.commit()
                return jsonify({'success': True, 'message': '规则保存成功'})
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': '请求头格式不正确'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存规则失败: {str(e)}'}), 500

# 批量删除搜索结果
@app.route('/delete_results', methods=['POST'])
def delete_results():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    result_ids = request.form.getlist('result_ids[]')
    
    if result_ids:
        # 将字符串ID转换为整数
        result_ids = [int(id) for id in result_ids]
        # 删除选中的结果
        SearchResult.query.filter(SearchResult.id.in_(result_ids)).delete(synchronize_session=False)
        db.session.commit()
    
    return redirect(url_for('data_warehouse'))

# AI大模型分析功能
@app.route('/analyze_data', methods=['GET', 'POST'])
def analyze_data():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取请求数据
    if request.method == 'POST':
        analysis_text = request.form.get('analysis_text')
        result_ids = request.form.getlist('result_ids[]')
    else:  # GET请求，用于SSE
        analysis_text = request.args.get('prompt')
        result_ids_str = request.args.get('result_ids', '')
        result_ids = result_ids_str.split(',') if result_ids_str else []
    
    # 配置OpenAI客户端使用SiliconFlow API
    openai.api_key = "sk-qnefgnmlhjscyqapfjqklknpjiftbsuljfrjprckddthlzes"
    openai.api_base = "https://api.siliconflow.cn/v1/"
    
    # 准备分析数据
    if result_ids:
        # 过滤空字符串并转换为整数
        result_ids = [int(id) for id in result_ids if id.strip()]
        if result_ids:
            results = SearchResult.query.filter(SearchResult.id.in_(result_ids)).all()
            
            # 构建分析文本
            data_summary = "以下是搜索结果数据：\n\n"
            for idx, result in enumerate(results, 1):
                data_summary += f"{idx}. 标题：{result.title}\n"
                data_summary += f"   摘要：{result.summary[:100]}...\n"
                data_summary += f"   关键词：{result.search_keyword}\n\n"
            
            # 添加用户分析请求
            full_prompt = f"{data_summary}\n用户分析请求：{analysis_text}\n请对以上数据进行分析并提供详细结果。"
        else:
            full_prompt = analysis_text
    else:
        full_prompt = analysis_text
    
    # 定义生成器函数用于SSE响应
    def generate():
        try:
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[
                    {"role": "system", "content": "你是一个数据分析助手，需要对提供的数据进行深入分析并提供专业见解。"},
                    {"role": "user", "content": full_prompt}
                ],
                stream=True
            )
            
            # 处理流式响应
            for chunk in response:
                if "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        content = delta["content"]
                        # 使用SSE格式发送数据
                        yield f"data: {json.dumps({'content': content})}\n\n"
        except Exception as e:
            # 发送错误信息
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # 发送结束信号
            yield "data: [DONE]\n\n"
    
    # 设置响应头，使用SSE协议
    return Response(generate(), mimetype='text/event-stream')

# 规则库管理页面
@app.route('/rule_library')
def rule_library():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有规则
    rules = CrawlRule.query.order_by(CrawlRule.created_at.desc()).all()
    
    # 获取消息和状态（用于显示操作结果）
    message = request.args.get('message')
    success = request.args.get('success') == 'true'
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('rule_library.html', rules=rules, message=message, success=success, left_menus=left_menus)

# 保存规则（新增/编辑）
@app.route('/save_rule', methods=['POST'])
def save_rule():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        rule_id = request.form.get('id')
        action = request.form.get('action')
        rule_name = request.form.get('rule_name')
        domain = request.form.get('domain')
        title_xpath = request.form.get('title_xpath')
        content_xpath = request.form.get('content_xpath')
        headers_str = request.form.get('headers')
        
        # 解析headers JSON字符串
        headers = None
        if headers_str:
            try:
                headers = json.loads(headers_str)
            except json.JSONDecodeError:
                return redirect(url_for('rule_library', message='请求头格式不正确', success='false'))
        
        if action == 'add':
            # 新增规则
            new_rule = CrawlRule(
                rule_name=rule_name,
                domain=domain,
                title_xpath=title_xpath,
                content_xpath=content_xpath,
                headers=headers
            )
            db.session.add(new_rule)
            db.session.commit()
            return redirect(url_for('rule_library', message='规则新增成功', success='true'))
        else:
            # 编辑规则
            rule = CrawlRule.query.get(rule_id)
            if rule:
                rule.rule_name = rule_name
                rule.domain = domain
                rule.title_xpath = title_xpath
                rule.content_xpath = content_xpath
                rule.headers = headers
                rule.updated_at = datetime.utcnow()
                db.session.commit()
                return redirect(url_for('rule_library', message='规则更新成功', success='true'))
            else:
                return redirect(url_for('rule_library', message='规则不存在', success='false'))
    except Exception as e:
        return redirect(url_for('rule_library', message=f'操作失败: {str(e)}', success='false'))

# 删除规则
@app.route('/delete_rule/<int:rule_id>')
def delete_rule(rule_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        rule = CrawlRule.query.get(rule_id)
        if rule:
            db.session.delete(rule)
            db.session.commit()
            return redirect(url_for('rule_library', message='规则删除成功', success='true'))
        else:
            return redirect(url_for('rule_library', message='规则不存在', success='false'))
    except Exception as e:
        return redirect(url_for('rule_library', message=f'删除失败: {str(e)}', success='false'))

# 批量删除规则
@app.route('/batch_delete_rules', methods=['POST'])
def batch_delete_rules():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        rule_ids = request.form.getlist('rule_ids')
        if not rule_ids:
            return redirect(url_for('rule_library', message='请选择要删除的规则', success='false'))
        
        # 将ID转换为整数
        rule_ids = [int(id) for id in rule_ids]
        
        # 删除选中的规则
        CrawlRule.query.filter(CrawlRule.id.in_(rule_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return redirect(url_for('rule_library', message=f'成功删除 {len(rule_ids)} 条规则', success='true'))
    except Exception as e:
        return redirect(url_for('rule_library', message=f'批量删除失败: {str(e)}', success='false'))

# 深度内容管理页面
@app.route('/content_details')
def content_details():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 分页处理
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取所有详细内容
    details_pagination = ContentDetails.query.order_by(ContentDetails.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取消息和状态
    message = request.args.get('message')
    success = request.args.get('success') == 'true'
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('content_details.html', details=details_pagination.items, pagination=details_pagination, message=message, success=success, left_menus=left_menus)

# 编辑详细内容页面
@app.route('/edit_content_detail/<int:detail_id>')
def edit_content_detail(detail_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取要编辑的详细内容
        detail = ContentDetails.query.get(detail_id)
        if not detail:
            return redirect(url_for('content_details', message='详细内容不存在', success='false'))
        
        return render_template('edit_content_detail.html', detail=detail)
    except Exception as e:
        return redirect(url_for('content_details', message=f'获取详细内容失败: {str(e)}', success='false'))

# 更新详细内容
@app.route('/update_content_detail', methods=['POST'])
def update_content_detail():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        detail_id = request.form.get('id')
        field_name = request.form.get('field_name')
        field_type = request.form.get('field_type')
        field_value = request.form.get('field_value')
        
        # 验证必填字段
        if not detail_id or not field_name or not field_type:
            return redirect(url_for('content_details', message='请填写必填字段', success='false'))
        
        # 更新详细内容
        detail = ContentDetails.query.get(detail_id)
        if not detail:
            return redirect(url_for('content_details', message='详细内容不存在', success='false'))
        
        detail.field_name = field_name
        detail.field_type = field_type
        detail.field_value = field_value
        db.session.commit()
        
        return redirect(url_for('content_details', message='详细内容更新成功', success='true'))
    except Exception as e:
        return redirect(url_for('content_details', message=f'更新详细内容失败: {str(e)}', success='false'))

# 删除详细内容
@app.route('/delete_content_detail/<int:detail_id>')
def delete_content_detail(detail_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 删除详细内容
        detail = ContentDetails.query.get(detail_id)
        if not detail:
            return redirect(url_for('content_details', message='详细内容不存在', success='false'))
        
        db.session.delete(detail)
        db.session.commit()
        
        return redirect(url_for('content_details', message='详细内容删除成功', success='true'))
    except Exception as e:
        return redirect(url_for('content_details', message=f'删除详细内容失败: {str(e)}', success='false'))

# 复制规则
@app.route('/copy_rule/<int:rule_id>')
def copy_rule(rule_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取原规则
        original_rule = CrawlRule.query.get(rule_id)
        if not original_rule:
            return redirect(url_for('rule_library', message='规则不存在', success='false'))
        
        # 创建新规则（复制原规则的所有属性）
        import datetime
        new_rule_name = f"{original_rule.rule_name}_副本_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_rule = CrawlRule(
            rule_name=new_rule_name,
            domain=original_rule.domain,
            title_xpath=original_rule.title_xpath,
            content_xpath=original_rule.content_xpath,
            headers=original_rule.headers
        )
        
        db.session.add(new_rule)
        db.session.commit()
        
        return redirect(url_for('rule_library', message='规则复制成功', success='true'))
    except Exception as e:
        return redirect(url_for('rule_library', message=f'复制失败: {str(e)}', success='false'))

# 单条采集路由
@app.route('/crawl_single_result', methods=['POST'])
def crawl_single_result():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    result_id = request.form.get('result_id')
    if not result_id:
        return jsonify({'success': False, 'message': '结果ID不能为空'})
    
    try:
        result_id = int(result_id)
        search_result = SearchResult.query.get(result_id)
        if not search_result:
            return jsonify({'success': False, 'message': '搜索结果不存在'})
        
        # 解析域名
        parsed_url = urlparse(search_result.url)
        domain = parsed_url.netloc
        
        # 查找匹配的规则
        crawl_rule = CrawlRule.query.filter_by(domain=domain).first()
        if not crawl_rule:
            return jsonify({'success': False, 'message': f'未找到域名 {domain} 对应的采集规则'})
        
        # 创建采集任务记录
        crawled_content = CrawledContent(
            result_id=search_result.id,
            rule_id=crawl_rule.id,
            status='pending'
        )
        db.session.add(crawled_content)
        db.session.commit()
        
        # 执行采集
        spider = BaiduSpider()
        try:
            crawl_result = spider.crawl_with_rule(search_result.url, crawl_rule)
            
            # 更新采集结果
            crawled_content.title = crawl_result.get('title')
            crawled_content.content = crawl_result.get('content')
            crawled_content.status = 'success'
            
            # 将内容分解为字段并保存到ContentDetails表
            if crawl_result.get('title'):
                # 先检查是否已存在该字段
                existing_title = ContentDetails.query.filter_by(
                    content_id=crawled_content.id, field_name='title'
                ).first()
                if not existing_title:
                    title_detail = ContentDetails(
                        content_id=crawled_content.id,
                        field_name='title',
                        field_value=crawl_result.get('title'),
                        field_type='text'
                    )
                    db.session.add(title_detail)
            
            if crawl_result.get('content'):
                # 先检查是否已存在该字段
                existing_content = ContentDetails.query.filter_by(
                    content_id=crawled_content.id, field_name='content'
                ).first()
                if not existing_content:
                    content_detail = ContentDetails(
                        content_id=crawled_content.id,
                        field_name='content',
                        field_value=crawl_result.get('content'),
                        field_type='text'
                    )
                    db.session.add(content_detail)
            
            db.session.commit()
        except Exception as e:
            # 更新采集失败信息
            crawled_content.status = 'failed'
            crawled_content.error_message = str(e)
            try:
                db.session.commit()
            except:
                db.session.rollback()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '采集完成',
            'result': {
                'id': crawled_content.id,
                'status': crawled_content.status,
                'title': crawled_content.title,
                'error_message': crawled_content.error_message
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'采集失败: {str(e)}'})

# 批量采集路由
@app.route('/crawl_batch_results', methods=['POST'])
def crawl_batch_results():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查两种可能的参数格式：单个字符串（前端用逗号分隔）或列表
    result_ids_str = request.form.get('result_ids')
    result_ids_list = request.form.getlist('result_ids[]')
    
    if result_ids_str:
        # 从逗号分隔的字符串转换为列表
        result_ids = [id.strip() for id in result_ids_str.split(',')]
    elif result_ids_list:
        # 使用列表格式
        result_ids = result_ids_list
    else:
        return jsonify({'success': False, 'message': '请至少选择一条数据'})
    
    try:
        result_ids = [int(id) for id in result_ids]
        search_results = SearchResult.query.filter(SearchResult.id.in_(result_ids)).all()
        
        # 初始化采集任务记录
        crawl_tasks = []
        no_rule_results = []
        for result in search_results:
            # 解析域名
            parsed_url = urlparse(result.url)
            domain = parsed_url.netloc
            
            # 查找匹配的规则
            crawl_rule = CrawlRule.query.filter_by(domain=domain).first()
            if crawl_rule:
                crawled_content = CrawledContent(
                    result_id=result.id,
                    rule_id=crawl_rule.id,
                    status='pending'
                )
                db.session.add(crawled_content)
                crawl_tasks.append(crawled_content)
            else:
                no_rule_results.append(result.id)
        
        db.session.commit()
        
        # 启动异步批量采集任务
        def async_batch_crawl():
            from app import db  # 在函数内导入避免循环导入问题
            from models import SearchResult, CrawlRule, CrawledContent, ContentDetails
            
            spider = BaiduSpider()
            for task in crawl_tasks:
                task_id = task.id
                try:
                    # 创建新的数据库会话以避免连接问题
                    db.session.expire_all()
                    task = CrawledContent.query.get(task_id)
                    search_result = SearchResult.query.get(task.result_id)
                    crawl_rule = CrawlRule.query.get(task.rule_id)
                    
                    crawl_result = spider.crawl_with_rule(search_result.url, crawl_rule)
                    
                    # 更新采集结果
                    task.title = crawl_result.get('title')
                    task.content = crawl_result.get('content')
                    task.status = 'success'
                    
                    # 将内容分解为字段并保存到ContentDetails表
                    if crawl_result.get('title'):
                        # 先检查是否已存在该字段
                        existing_title = ContentDetails.query.filter_by(
                            content_id=task.id, field_name='title'
                        ).first()
                        if not existing_title:
                            title_detail = ContentDetails(
                                content_id=task.id,
                                field_name='title',
                                field_value=crawl_result.get('title'),
                                field_type='text'
                            )
                            db.session.add(title_detail)
                    
                    if crawl_result.get('content'):
                        # 先检查是否已存在该字段
                        existing_content = ContentDetails.query.filter_by(
                            content_id=task.id, field_name='content'
                        ).first()
                        if not existing_content:
                            content_detail = ContentDetails(
                                content_id=task.id,
                                field_name='content',
                                field_value=crawl_result.get('content'),
                                field_type='text'
                            )
                            db.session.add(content_detail)
                    
                    db.session.commit()
                except Exception as e:
                    # 更新采集失败信息
                    try:
                        db.session.rollback()
                        task = CrawledContent.query.get(task_id)
                        task.status = 'failed'
                        task.error_message = str(e)
                        db.session.commit()
                    except Exception as commit_error:
                        print(f"更新任务状态失败: {commit_error}")
                
                # 避免请求过于频繁
                time.sleep(0.5)
        
        # 使用线程异步执行批量采集
        import threading
        thread = threading.Thread(target=async_batch_crawl)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '批量采集任务已启动',
            'total': len(search_results),
            'pending': len(crawl_tasks),
            'no_rule_count': len(no_rule_results),
            'no_rule_ids': no_rule_results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'批量采集请求失败: {str(e)}'})

# 获取采集进度路由
@app.route('/get_crawl_progress', methods=['GET'])
def get_crawl_progress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        # 获取最近5分钟内创建的采集任务
        from datetime import datetime, timedelta
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        recent_tasks = CrawledContent.query.filter(
            CrawledContent.created_at >= time_threshold,
            CrawledContent.status.in_(['pending', 'success', 'failed'])
        ).order_by(CrawledContent.created_at.desc()).all()
        
        total_tasks = len(recent_tasks)
        pending_tasks = sum(1 for task in recent_tasks if task.status == 'pending')
        success_tasks = sum(1 for task in recent_tasks if task.status == 'success')
        failed_tasks = sum(1 for task in recent_tasks if task.status == 'failed')
        
        progress = 0
        if total_tasks > 0:
            progress = int(((success_tasks + failed_tasks) / total_tasks) * 100)
        
        # 计算已完成任务数（成功 + 失败）
        completed_tasks = success_tasks + failed_tasks
        
        return jsonify({
            'success': True,
            'data': {
                'progress': progress,
                'pending': pending_tasks,
                'success': success_tasks,
                'failed': failed_tasks,
                'completed': completed_tasks,
                'total': total_tasks,
                'status': 'running' if pending_tasks > 0 else 'completed'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取进度失败: {str(e)}'})

# 获取采集结果路由
@app.route('/get_crawl_results', methods=['GET'])
def get_crawl_results():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    try:
        result_id = request.args.get('result_id')
        if result_id:
            # 获取单条采集结果
            crawled_content = CrawledContent.query.filter_by(result_id=result_id).first()
            if not crawled_content:
                return jsonify({'success': False, 'message': '未找到采集结果'})
            
            return jsonify({
                'success': True,
                'result': {
                    'id': crawled_content.id,
                    'status': crawled_content.status,
                    'title': crawled_content.title,
                    'content': crawled_content.content,
                    'error_message': crawled_content.error_message,
                    'created_at': crawled_content.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            # 获取最近的采集结果（最近100条）
            crawled_contents = CrawledContent.query.order_by(CrawledContent.created_at.desc()).limit(100).all()
            results = []
            for content in crawled_contents:
                # 获取对应的搜索结果标题
                search_result = SearchResult.query.get(content.result_id)
                title = search_result.title if search_result else content.title or '未知标题'
                
                results.append({
                    'id': content.id,
                    'status': content.status,
                    'title': title,
                    'content': content.content,
                    'error_message': content.error_message,
                    'created_at': content.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 同时返回两种格式以兼容前端
            return jsonify({
                'success': True,
                'data': results,  # 用于批量采集结果展示
                'results': results,  # 保持原有接口格式
                'count': len(results)
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取结果失败: {str(e)}'})

# 查看采集内容详情路由
@app.route('/view_crawled_content/<int:content_id>')
def view_crawled_content(content_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        crawled_content = CrawledContent.query.get(content_id)
        if not crawled_content:
            return render_template('error.html', message='未找到采集内容')
        
        return render_template('view_crawled_content.html', content=crawled_content)
    except Exception as e:
        return render_template('error.html', message=f'查看失败: {str(e)}')

# AI模型引擎管理路由
# AI模型引擎列表
@app.route('/ai_engines')
def ai_engines():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engines = AIEngine.query.order_by(AIEngine.created_at.desc()).all()
    
    # 获取token使用统计
    from sqlalchemy import func
    token_stats = db.session.query(
        TokenUsage.engine_id,
        func.sum(TokenUsage.total_tokens).label('total_tokens')
    ).group_by(TokenUsage.engine_id).all()
    
    # 将统计结果转换为字典，便于模板使用
    token_dict = {stat.engine_id: stat.total_tokens or 0 for stat in token_stats}
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('ai_engines.html', engines=engines, token_dict=token_dict, left_menus=left_menus)

# 添加AI模型引擎
@app.route('/add_ai_engine', methods=['GET', 'POST'])
def add_ai_engine():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        api_base = request.form['api_base']
        api_key = request.form['api_key']
        model_name = request.form['model_name']
        provider = request.form['provider']
        description = request.form['description']
        is_active = request.form.get('is_active', False) == 'on'
        
        # 检查是否已存在相同名称的引擎
        existing = AIEngine.query.filter_by(name=name).first()
        if existing:
            return render_template('add_ai_engine.html', error='引擎名称已存在')
        
        # 创建新引擎
        engine = AIEngine(
            name=name,
            api_base=api_base,
            api_key=api_key,
            model_name=model_name,
            provider=provider,
            description=description,
            is_active=is_active
        )
        
        db.session.add(engine)
        db.session.commit()
        
        return redirect(url_for('ai_engines', message='引擎添加成功'))
    
    return render_template('add_ai_engine.html')

# 编辑AI模型引擎
@app.route('/edit_ai_engine/<int:engine_id>', methods=['GET', 'POST'])
def edit_ai_engine(engine_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engine = AIEngine.query.get_or_404(engine_id)
    
    if request.method == 'POST':
        name = request.form['name']
        api_base = request.form['api_base']
        api_key = request.form['api_key']
        model_name = request.form['model_name']
        provider = request.form['provider']
        description = request.form['description']
        is_active = request.form.get('is_active', False) == 'on'
        
        # 检查是否已存在相同名称的引擎（排除当前引擎）
        existing = AIEngine.query.filter(AIEngine.name == name, AIEngine.id != engine_id).first()
        if existing:
            return render_template('edit_ai_engine.html', engine=engine, error='引擎名称已存在')
        
        # 更新引擎信息
        engine.name = name
        engine.api_base = api_base
        engine.api_key = api_key
        engine.model_name = model_name
        engine.provider = provider
        engine.description = description
        engine.is_active = is_active
        
        db.session.commit()
        
        return redirect(url_for('ai_engines', message='引擎更新成功'))
    
    return render_template('edit_ai_engine.html', engine=engine)

# 删除AI模型引擎
@app.route('/delete_ai_engine/<int:engine_id>', methods=['POST'])
def delete_ai_engine(engine_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engine = AIEngine.query.get_or_404(engine_id)
    
    try:
        db.session.delete(engine)
        db.session.commit()
        return jsonify({'success': True, 'message': '引擎删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 测试AI模型引擎（SSE响应）
@app.route('/test_ai_engine/<int:engine_id>')
def test_ai_engine(engine_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engine = AIEngine.query.get_or_404(engine_id)
    
    def generate():
        try:
            # 设置OpenAI兼容的API客户端（兼容旧版本0.28.0）
            import openai
            openai.api_key = engine.api_key
            openai.api_base = engine.api_base
            
            # 测试请求
            response = openai.ChatCompletion.create(
                model=engine.model_name,
                messages=[{"role": "user", "content": "你好，我在测试你的API连接"}],
                stream=True
            )
            
            # 逐块生成响应
            for chunk in response:
                if 'choices' in chunk and chunk['choices']:
                    if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                        content = chunk['choices'][0]['delta']['content']
                        if content:
                            yield f"data: {content}\n\n"
            
            # 记录token使用情况
            usage = TokenUsage(
                engine_id=engine.id,
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
            db.session.add(usage)
            db.session.commit()
            
        except Exception as e:
            yield f"data: 错误: {str(e)}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")

# 获取token消耗统计
@app.route('/token_usage_stats')
def token_usage_stats():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取按引擎分组的token使用统计
    from sqlalchemy import func
    stats = db.session.query(
        AIEngine.name,
        func.sum(TokenUsage.prompt_tokens).label('total_prompt_tokens'),
        func.sum(TokenUsage.completion_tokens).label('total_completion_tokens'),
        func.sum(TokenUsage.total_tokens).label('total_tokens')
    ).join(TokenUsage).group_by(AIEngine.id).all()
    
    return jsonify({
        'success': True,
        'stats': [{
            'engine_name': stat.name,
            'prompt_tokens': stat.total_prompt_tokens or 0,
            'completion_tokens': stat.total_completion_tokens or 0,
            'total_tokens': stat.total_tokens or 0
        } for stat in stats]
    })

# 获取token消耗趋势
@app.route('/token_usage_trend')
def token_usage_trend():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取最近30天的token使用趋势
    from sqlalchemy import func
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    
    trend = db.session.query(
        func.date(TokenUsage.usage_date).label('date'),
        func.sum(TokenUsage.total_tokens).label('total_tokens')
    ).filter(TokenUsage.usage_date >= thirty_days_ago).group_by(func.date(TokenUsage.usage_date)).order_by('date').all()
    
    return jsonify({
        'success': True,
        'trend': [{
            'date': str(stat.date),
            'total_tokens': stat.total_tokens or 0
        } for stat in trend]
    })

# 与AI模型对话页面
@app.route('/chat_with_engine/<int:engine_id>')
def chat_with_engine(engine_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engine = AIEngine.query.get_or_404(engine_id)
    return render_template('chat_with_engine.html', engine=engine)

# 与AI模型对话（SSE响应）
@app.route('/chat_with_engine/<int:engine_id>/stream')
def chat_with_engine_sse(engine_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    engine = AIEngine.query.get_or_404(engine_id)
    
    # 获取对话历史
    import json
    chat_history_param = request.args.get('chat_history', '[]')
    chat_history = json.loads(chat_history_param)
    
    def generate():
        try:
            # 设置OpenAI兼容的API客户端（兼容旧版本0.28.0）
            import openai
            openai.api_key = engine.api_key
            openai.api_base = engine.api_base
            
            # 调用AI模型
            response = openai.ChatCompletion.create(
                model=engine.model_name,
                messages=chat_history,
                stream=True
            )
            
            # 逐块生成响应并收集响应内容
            response_text = ''
            for chunk in response:
                if 'choices' in chunk and chunk['choices']:
                    if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                        content = chunk['choices'][0]['delta']['content']
                        if content:
                            response_text += content
                            yield f"data: {content}\n\n"
            
            # 记录token使用情况 - 对于流式响应，我们需要估算token数量
            try:
                # 由于是流式响应，无法直接获取usage信息，我们可以通过计算消息内容的长度来估算token数量
                # 一般来说，1个汉字约等于2个token，1个英文单词约等于1个token
                prompt_text = ''.join([msg['content'] for msg in chat_history if msg['content']])
                # 估算prompt tokens：汉字按2个token，其他按1个token
                prompt_tokens = sum(2 if ord(c) > 127 else 1 for c in prompt_text)
                
                # 估算completion tokens：假设平均每10个字符产生1个token
                # 注意：这里只是临时解决方案，实际应该根据具体模型的token计算方式来估算
                completion_tokens = len(response_text) // 10
                total_tokens = prompt_tokens + completion_tokens
                
                if total_tokens > 0:
                    usage = TokenUsage(
                        engine_id=engine.id,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens
                    )
                    db.session.add(usage)
                    db.session.commit()
            except Exception as e:
                # 记录token使用失败不影响对话功能
                pass
            
            # 发送完成信号
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: 错误: {str(e)}\n\n"
            yield "data: [DONE]\n\n"
    

# ========== 数据源管理 ==========

# 数据源列表页面
@app.route('/data_sources')
def data_sources():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有数据源
    data_sources = DataSource.query.order_by(DataSource.created_at.desc()).all()
    
    # 获取消息和状态
    message = request.args.get('message')
    success = request.args.get('success', 'false')
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('data_sources.html', data_sources=data_sources, message=message, success=success, left_menus=left_menus)

# 添加数据源页面
@app.route('/add_data_source')
def add_data_source():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有行业标签
    industry_tags = IndustryTag.query.all()
    
    return render_template('add_data_source.html', industry_tags=industry_tags)

# 编辑数据源页面
@app.route('/edit_data_source/<int:source_id>')
def edit_data_source(source_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取数据源
    data_source = DataSource.query.get_or_404(source_id)
    
    # 获取所有行业标签
    industry_tags = IndustryTag.query.all()
    
    # 获取当前数据源已添加的标签ID
    current_tag_ids = [tag.industry_tag_id for tag in DataSourceTag.query.filter_by(data_source_id=source_id).all()]
    
    return render_template('edit_data_source.html', data_source=data_source, industry_tags=industry_tags, current_tag_ids=current_tag_ids)

# 保存数据源（新增/编辑）
@app.route('/save_data_source', methods=['POST'])
def save_data_source():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        source_id = request.form.get('id')
        action = request.form.get('action')
        name = request.form.get('name')
        source_type = request.form.get('type')
        base_url = request.form.get('base_url')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'true'
        selected_tags = request.form.getlist('tags[]')
        
        # 验证必填字段
        if not name or not source_type or not base_url:
            return redirect(url_for('data_sources', message='数据源名称、类型和基础URL不能为空', success='false'))
        
        if action == 'add':
            # 新增数据源
            new_source = DataSource(
                name=name,
                type=source_type,
                base_url=base_url,
                description=description,
                is_active=is_active
            )
            db.session.add(new_source)
            db.session.flush()  # 获取ID但不提交
            
            # 添加关联的标签
            if selected_tags:
                for tag_id in selected_tags:
                    tag_relation = DataSourceTag(
                        data_source_id=new_source.id,
                        industry_tag_id=int(tag_id)
                    )
                    db.session.add(tag_relation)
            
            db.session.commit()
            return redirect(url_for('data_sources', message='数据源新增成功', success='true'))
        else:
            # 编辑数据源
            data_source = DataSource.query.get(source_id)
            if data_source:
                data_source.name = name
                data_source.type = source_type
                data_source.base_url = base_url
                data_source.description = description
                data_source.is_active = is_active
                data_source.updated_at = datetime.utcnow()
                
                # 更新标签关联
                # 先删除现有关联
                DataSourceTag.query.filter_by(data_source_id=source_id).delete()
                # 添加新关联
                if selected_tags:
                    for tag_id in selected_tags:
                        tag_relation = DataSourceTag(
                            data_source_id=source_id,
                            industry_tag_id=int(tag_id)
                        )
                        db.session.add(tag_relation)
                
                db.session.commit()
                return redirect(url_for('data_sources', message='数据源更新成功', success='true'))
            else:
                return redirect(url_for('data_sources', message='数据源不存在', success='false'))
    except Exception as e:
        return redirect(url_for('data_sources', message=f'保存失败: {str(e)}', success='false'))

# 删除数据源
@app.route('/delete_data_source/<int:source_id>')
def delete_data_source(source_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 先删除标签关联
        DataSourceTag.query.filter_by(data_source_id=source_id).delete()
        
        # 删除数据源
        data_source = DataSource.query.get(source_id)
        if data_source:
            db.session.delete(data_source)
            db.session.commit()
            return redirect(url_for('data_sources', message='数据源删除成功', success='true'))
        else:
            return redirect(url_for('data_sources', message='数据源不存在', success='false'))
    except Exception as e:
        return redirect(url_for('data_sources', message=f'删除失败: {str(e)}', success='false'))

# 数据源详情页面
@app.route('/data_source_details/<int:source_id>')
def data_source_details(source_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取数据源
    data_source = DataSource.query.get_or_404(source_id)
    
    # 获取关联的标签
    tag_relations = DataSourceTag.query.filter_by(data_source_id=source_id).all()
    tags = [IndustryTag.query.get(relation.industry_tag_id) for relation in tag_relations]
    
    # 获取关联的爬虫
    spiders = Spider.query.filter_by(data_source_id=source_id).all()
    
    return render_template('data_source_details.html', data_source=data_source, tags=tags, spiders=spiders)


# ========== 行业标签管理 ==========

# 行业标签列表页面
@app.route('/industry_tags')
def industry_tags():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有行业标签
    tags = IndustryTag.query.order_by(IndustryTag.created_at.desc()).all()
    
    # 获取消息和状态
    message = request.args.get('message')
    success = request.args.get('success', 'false')
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('industry_tags.html', tags=tags, message=message, success=success, left_menus=left_menus)

# 添加行业标签页面
@app.route('/add_industry_tag')
def add_industry_tag():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('add_industry_tag.html')

# 编辑行业标签页面
@app.route('/edit_industry_tag/<int:tag_id>')
def edit_industry_tag(tag_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取行业标签
    tag = IndustryTag.query.get_or_404(tag_id)
    
    return render_template('edit_industry_tag.html', tag=tag)

# 保存行业标签（新增/编辑）
@app.route('/save_industry_tag', methods=['POST'])
def save_industry_tag():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        tag_id = request.form.get('id')
        action = request.form.get('action')
        name = request.form.get('name')
        description = request.form.get('description')
        
        # 验证必填字段
        if not name:
            return redirect(url_for('industry_tags', message='标签名称不能为空', success='false'))
        
        if action == 'add':
            # 新增标签
            new_tag = IndustryTag(
                name=name,
                description=description
            )
            db.session.add(new_tag)
            db.session.commit()
            return redirect(url_for('industry_tags', message='标签新增成功', success='true'))
        else:
            # 编辑标签
            tag = IndustryTag.query.get(tag_id)
            if tag:
                tag.name = name
                tag.description = description
                tag.updated_at = datetime.utcnow()
                db.session.commit()
                return redirect(url_for('industry_tags', message='标签更新成功', success='true'))
            else:
                return redirect(url_for('industry_tags', message='标签不存在', success='false'))
    except Exception as e:
        return redirect(url_for('industry_tags', message=f'保存失败: {str(e)}', success='false'))

# 删除行业标签
@app.route('/delete_industry_tag/<int:tag_id>')
def delete_industry_tag(tag_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 先删除关联
        DataSourceTag.query.filter_by(industry_tag_id=tag_id).delete()
        
        # 删除标签
        tag = IndustryTag.query.get(tag_id)
        if tag:
            db.session.delete(tag)
            db.session.commit()
            return redirect(url_for('industry_tags', message='标签删除成功', success='true'))
        else:
            return redirect(url_for('industry_tags', message='标签不存在', success='false'))
    except Exception as e:
        return redirect(url_for('industry_tags', message=f'删除失败: {str(e)}', success='false'))


# ========== 爬虫管理 ==========

# 爬虫列表页面
@app.route('/spiders')
def spiders():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有爬虫
    spiders_list = Spider.query.order_by(Spider.created_at.desc()).all()
    
    # 获取消息和状态
    message = request.args.get('message')
    success = request.args.get('success', 'false')
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('spiders.html', spiders=spiders_list, message=message, success=success, left_menus=left_menus)

# 添加爬虫页面
@app.route('/add_spider')
def add_spider():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有数据源
    data_sources = DataSource.query.all()
    
    return render_template('add_spider.html', data_sources=data_sources)

# 编辑爬虫页面
@app.route('/edit_spider/<int:spider_id>')
def edit_spider(spider_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取爬虫
    spider = Spider.query.get_or_404(spider_id)
    
    # 获取所有数据源
    data_sources = DataSource.query.all()
    
    return render_template('edit_spider.html', spider=spider, data_sources=data_sources)

# 保存爬虫（新增/编辑）
@app.route('/save_spider', methods=['POST'])
def save_spider():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        spider_id = request.form.get('id')
        action = request.form.get('action')
        name = request.form.get('name')
        data_source_id = request.form.get('data_source_id')
        spider_class = request.form.get('spider_class')
        config_str = request.form.get('config')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'true'
        
        # 验证必填字段
        if not name or not data_source_id or not spider_class:
            return redirect(url_for('spiders', message='爬虫名称、数据源和爬虫类名不能为空', success='false'))
        
        try:
            # 解析配置JSON字符串
            config = json.loads(config_str) if config_str else None
        except json.JSONDecodeError:
            return redirect(url_for('spiders', message='配置格式不正确', success='false'))
        
        if action == 'add':
            # 新增爬虫
            new_spider = Spider(
                name=name,
                data_source_id=int(data_source_id),
                spider_class=spider_class,
                config=config,
                description=description,
                is_active=is_active
            )
            db.session.add(new_spider)
            db.session.commit()
            return redirect(url_for('spiders', message='爬虫新增成功', success='true'))
        else:
            # 编辑爬虫
            spider = Spider.query.get(spider_id)
            if spider:
                spider.name = name
                spider.data_source_id = int(data_source_id)
                spider.spider_class = spider_class
                spider.config = config
                spider.description = description
                spider.is_active = is_active
                spider.updated_at = datetime.utcnow()
                db.session.commit()
                return redirect(url_for('spiders', message='爬虫更新成功', success='true'))
            else:
                return redirect(url_for('spiders', message='爬虫不存在', success='false'))
    except Exception as e:
        return redirect(url_for('spiders', message=f'保存失败: {str(e)}', success='false'))

# 删除爬虫
@app.route('/delete_spider/<int:spider_id>')
def delete_spider(spider_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 删除爬虫
        spider = Spider.query.get(spider_id)
        if spider:
            db.session.delete(spider)
            db.session.commit()
            return redirect(url_for('spiders', message='爬虫删除成功', success='true'))
        else:
            return redirect(url_for('spiders', message='爬虫不存在', success='false'))
    except Exception as e:
        return redirect(url_for('spiders', message=f'删除失败: {str(e)}', success='false'))

# 爬虫测试页面
@app.route('/test_spider/<int:spider_id>')
def test_spider(spider_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取爬虫
    spider = Spider.query.get_or_404(spider_id)
    
    return render_template('test_spider.html', spider=spider)

# 执行爬虫测试
@app.route('/run_spider_test', methods=['POST'])
def run_spider_test():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        spider_id = request.form.get('spider_id')
        test_query = request.form.get('test_query')
        
        # 验证必填字段
        if not spider_id or not test_query:
            return redirect(url_for('spiders', message='爬虫ID和测试查询不能为空', success='false'))
        
        # 获取爬虫
        spider = Spider.query.get(spider_id)
        if not spider:
            return redirect(url_for('spiders', message='爬虫不存在', success='false'))
        
        # 动态加载爬虫类
        try:
            # 假设爬虫类在baidu_spider.py中
            if spider.spider_class == 'BaiduSpider':
                spider_instance = BaiduSpider()
            elif spider.spider_class == 'BingSpider':
                spider_instance = BingSpider()
            else:
                # 尝试从其他模块导入
                module = importlib.import_module('baidu_spider')
                spider_class = getattr(module, spider.spider_class)
                spider_instance = spider_class()
        except Exception as e:
            return redirect(url_for('spiders', message=f'加载爬虫类失败: {str(e)}', success='false'))
        
        # 执行搜索测试
        results = spider_instance.search(test_query)
        
        # 保存测试结果
        spider_test = SpiderTest(
            spider_id=int(spider_id),
            test_query=test_query,
            test_results=results,
            status='success'
        )
        db.session.add(spider_test)
        db.session.commit()
        
        # 返回测试结果页面
        return render_template('spider_test_results.html', spider=spider, test_query=test_query, results=results)
    except Exception as e:
        # 保存失败的测试结果
        spider_test = SpiderTest(
            spider_id=int(spider_id),
            test_query=test_query,
            status='failed',
            error_message=str(e)
        )
        db.session.add(spider_test)
        db.session.commit()
        
        return redirect(url_for('spiders', message=f'测试失败: {str(e)}', success='false'))


# ---------------------------- 聊天室功能 ----------------------------

# 聊天室列表页面
@app.route('/chatrooms')
def chatrooms():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取当前用户
    current_user = User.query.get(session['user_id'])
    
    # 获取所有公开聊天室
    public_rooms = ChatRoom.query.filter_by(is_public=True).all()
    
    # 获取用户加入的聊天室
    joined_rooms = current_user.joined_rooms
    joined_room_ids = [room.room_id for room in joined_rooms]
    
    # 获取所有菜单并构建左侧菜单树
    all_menus = Menu.query.order_by(Menu.order).all()
    left_menus = build_menu_tree(all_menus)
    
    return render_template('chatrooms.html', public_rooms=public_rooms, joined_room_ids=joined_room_ids, current_user=current_user, left_menus=left_menus)

# 创建聊天室页面
@app.route('/create_chatroom')
def create_chatroom_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    # 获取当前用户
    current_user = User.query.get(session['user_id'])
    return render_template('create_chatroom.html', current_user=current_user)

# 创建聊天室处理
@app.route('/create_chatroom', methods=['POST'])
def create_chatroom():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取表单数据
    name = request.form['name']
    description = request.form['description']
    is_public = request.form.get('is_public') == 'on'
    
    # 检查聊天室名称是否已存在
    existing_room = ChatRoom.query.filter_by(name=name).first()
    if existing_room:
        return render_template('create_chatroom.html', error='聊天室名称已存在')
    
    # 创建新聊天室
    new_room = ChatRoom(
        name=name,
        description=description,
        is_public=is_public,
        created_by=session['user_id']
    )
    db.session.add(new_room)
    db.session.commit()
    
    # 自动将创建者加入聊天室
    user_room = UserChatRoom(
        user_id=session['user_id'],
        room_id=new_room.id
    )
    db.session.add(user_room)
    db.session.commit()
    
    return redirect(url_for('chatrooms', message='聊天室创建成功', success='true'))

# 加入聊天室
@app.route('/join_chatroom/<int:room_id>')
def join_chatroom(room_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 检查聊天室是否存在
    room = ChatRoom.query.get(room_id)
    if not room:
        return redirect(url_for('chatrooms', message='聊天室不存在', success='false'))
    
    # 检查用户是否已加入该聊天室
    existing = UserChatRoom.query.filter_by(user_id=session['user_id'], room_id=room_id).first()
    if existing:
        return redirect(url_for('chatrooms', message='您已加入该聊天室', success='false'))
    
    # 将用户加入聊天室
    user_room = UserChatRoom(
        user_id=session['user_id'],
        room_id=room_id
    )
    db.session.add(user_room)
    db.session.commit()
    
    return redirect(url_for('chatrooms', message='加入聊天室成功', success='true'))

# 离开聊天室
@app.route('/leave_chatroom/<int:room_id>')
def leave_chatroom(room_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 查找用户与聊天室的关联
    user_room = UserChatRoom.query.filter_by(user_id=session['user_id'], room_id=room_id).first()
    if not user_room:
        return redirect(url_for('chatrooms', message='您未加入该聊天室', success='false'))
    
    # 删除关联记录
    db.session.delete(user_room)
    db.session.commit()
    
    return redirect(url_for('chatrooms', message='离开聊天室成功', success='true'))

# 聊天室详情页面
@app.route('/chatroom/<int:room_id>')
def chatroom_detail(room_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取当前用户
    current_user = User.query.get(session['user_id'])
    
    # 检查聊天室是否存在
    room = ChatRoom.query.get(room_id)
    if not room:
        return redirect(url_for('chatrooms', message='聊天室不存在', success='false'))
    
    # 检查用户是否已加入该聊天室
    user_room = UserChatRoom.query.filter_by(user_id=session['user_id'], room_id=room_id).first()
    if not user_room:
        return redirect(url_for('chatrooms', message='您需要先加入该聊天室', success='false'))
    
    # 获取聊天室的所有消息
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.created_at.desc()).limit(100).all()
    messages.reverse()  # 按时间顺序排列
    
    # 获取聊天室的所有成员
    members = User.query.join(UserChatRoom).filter(UserChatRoom.room_id == room_id).all()
    
    return render_template('chatroom_detail.html', room=room, messages=messages, members=members, current_user=current_user)

# 导入AI指令处理模块
from ai_commands import parse_ai_command, handle_ai_command

# 发送消息
@app.route('/send_message/<int:room_id>', methods=['POST'])
def send_message(room_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    # 获取消息内容
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'message': '消息内容不能为空'})
    
    # 创建新消息
    new_message = ChatMessage(
        room_id=room_id,
        user_id=session['user_id'],
        content=content
    )
    db.session.add(new_message)
    db.session.commit()
    
    # 检查是否为AI指令
    is_ai_cmd, command_type, command_params = parse_ai_command(content)
    if is_ai_cmd:
        # 处理AI指令
        ai_response = handle_ai_command(command_type, command_params, session['user_id'])
        
        # 创建AI回复消息
        ai_message = ChatMessage(
            room_id=room_id,
            user_id=1,  # 假设AI用户ID为1
            content=json.dumps(ai_response)
        )
        db.session.add(ai_message)
        db.session.commit()
    
    # 返回成功响应
    return jsonify({
        'success': True,
        'message': {
            'id': new_message.id,
            'content': new_message.content,
            'username': new_message.user.username,
            'created_at': new_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

# 获取消息列表
@app.route('/get_messages/<int:room_id>/<int:last_message_id>')
def get_messages(room_id, last_message_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    # 获取新消息
    messages = ChatMessage.query.filter(
        ChatMessage.room_id == room_id,
        ChatMessage.id > last_message_id
    ).order_by(ChatMessage.created_at).all()
    
    # 格式化消息
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            'id': msg.id,
            'content': msg.content,
            'username': msg.user.username,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'success': True, 'messages': formatted_messages})

# 删除聊天室
@app.route('/delete_chatroom/<int:room_id>')
def delete_chatroom(room_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 检查聊天室是否存在
    room = ChatRoom.query.get(room_id)
    if not room:
        return redirect(url_for('chatrooms', message='聊天室不存在', success='false'))
    
    # 检查是否是聊天室创建者
    if room.created_by != session['user_id']:
        return redirect(url_for('chatrooms', message='只有创建者可以删除聊天室', success='false'))
    
    # 删除所有与该聊天室相关的消息
    ChatMessage.query.filter_by(room_id=room_id).delete()
    
    # 删除所有用户与该聊天室的关联
    UserChatRoom.query.filter_by(room_id=room_id).delete()
    
    # 删除聊天室本身
    db.session.delete(room)
    db.session.commit()
    
    return redirect(url_for('chatrooms', message='聊天室删除成功', success='true'))


# ========== 菜单管理 ==========

# 构建菜单树的辅助函数
def build_menu_tree(menus, parent_id=None):
    menu_tree = []
    for menu in menus:
        if menu.parent_id == parent_id:
            children = build_menu_tree(menus, menu.id)
            menu.children = children  # 使用children属性
            menu_tree.append(menu)
    return menu_tree

# 菜单列表页面
@app.route('/menus')
def menus():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有菜单（按order排序）
    all_menus = Menu.query.order_by(Menu.order).all()
    
    menu_tree = build_menu_tree(all_menus)
    left_menus = build_menu_tree(all_menus)
    
    return render_template('menus.html', menu_tree=menu_tree, left_menus=left_menus)

# 添加菜单页面
@app.route('/add_menu')
def add_menu():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取所有一级菜单（作为父菜单选项）
    parent_menus = Menu.query.filter_by(parent_id=None).order_by(Menu.order).all()
    
    return render_template('add_menu.html', parent_menus=parent_menus)

# 保存菜单（新增/编辑）
@app.route('/save_menu', methods=['POST'])
def save_menu():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取表单数据
        menu_id = request.form.get('id')
        name = request.form.get('name')
        url = request.form.get('url')
        icon = request.form.get('icon')
        parent_id = request.form.get('parent_id') or None
        order = int(request.form.get('order', 0))
        is_active = request.form.get('is_active') == 'on'
        
        # 验证必填字段
        if not name or not url:
            return redirect(url_for('menus', message='菜单名称和URL不能为空', success='false'))
        
        if menu_id:
            # 编辑菜单
            menu = Menu.query.get(menu_id)
            if not menu:
                return redirect(url_for('menus', message='菜单不存在', success='false'))
            
            menu.name = name
            menu.url = url
            menu.icon = icon
            menu.parent_id = parent_id
            menu.order = order
            menu.is_active = is_active
            menu.updated_at = datetime.utcnow()
        else:
            # 新增菜单
            new_menu = Menu(
                name=name,
                url=url,
                icon=icon,
                parent_id=parent_id,
                order=order,
                is_active=is_active
            )
            db.session.add(new_menu)
        
        db.session.commit()
        return redirect(url_for('menus', message='菜单保存成功', success='true'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('menus', message=f'保存失败: {str(e)}', success='false'))

# 编辑菜单页面
@app.route('/edit_menu/<int:menu_id>')
def edit_menu(menu_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取菜单
    menu = Menu.query.get_or_404(menu_id)
    
    # 获取所有一级菜单（作为父菜单选项）
    parent_menus = Menu.query.filter_by(parent_id=None).filter(Menu.id != menu_id).order_by(Menu.order).all()
    
    return render_template('edit_menu.html', menu=menu, parent_menus=parent_menus)

# 删除菜单
@app.route('/delete_menu/<int:menu_id>')
def delete_menu(menu_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # 获取菜单
        menu = Menu.query.get(menu_id)
        if not menu:
            return redirect(url_for('menus', message='菜单不存在', success='false'))
        
        # 检查是否有子菜单
        if menu.children and len(menu.children) > 0:
            return redirect(url_for('menus', message='该菜单有子菜单，不能直接删除', success='false'))
        
        # 删除菜单
        db.session.delete(menu)
        db.session.commit()
        
        return redirect(url_for('menus', message='菜单删除成功', success='true'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('menus', message=f'删除失败: {str(e)}', success='false'))
