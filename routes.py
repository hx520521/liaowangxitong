from flask import Flask, render_template, request, redirect, url_for, session, Response
from app import app, db
from models import User, SearchResult
from baidu_spider import BaiduSpider
from sqlalchemy import or_
import openai
import json

# 首页/登录页
@app.route('/')
def index():
    return render_template('login.html')

# 登录处理
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # 验证用户
    user = User.query.filter_by(username=username, password=password).first()
    if user:
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

# 后台主页
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

# 搜索处理
@app.route('/search', methods=['POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    keyword = request.form['keyword']
    spider = BaiduSpider()
    results = spider.search(keyword)
    
    return render_template('search_results.html', results=results, keyword=keyword)

# 保存搜索结果
@app.route('/save_results', methods=['POST'])
def save_results():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    results = request.form.getlist('results[]')
    keyword = request.form['keyword']
    
    for result_str in results:
        # 解析结果字符串，格式：title|summary|url|cover_url
        parts = result_str.split('|')
        if len(parts) >= 4:
            title, summary, url, cover_url = parts[:4]
            
            # 检查是否已存在相同URL的结果
            existing = SearchResult.query.filter_by(url=url).first()
            if not existing:
                result = SearchResult(
                    title=title,
                    summary=summary,
                    url=url,
                    cover_url=cover_url,
                    search_keyword=keyword
                )
                db.session.add(result)
    
    db.session.commit()
    return redirect(url_for('data_warehouse'))

# 数据仓库
@app.route('/data_warehouse')
def data_warehouse():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    date = request.args.get('date', '')
    
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
    
    return render_template('data_warehouse.html', results=results, keyword=keyword, date=date)

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
