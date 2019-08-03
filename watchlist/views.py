from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user

from watchlist import app, db
from watchlist.models import User, Movie

# 主页视图
# 这个视图函数处理哪种方法类型的请求。默认只接受 GET 请求，上面的写法表示同时接受 GET 和 POST 请求。
@app.route('/', methods=['GET', 'POST'])    # index-索引，即主页
def index():

    if request.method == 'POST':    #判断是否是post请求
        if not current_user.is_authenticated:  # 如果当前用户未认证    因为创建新条目的功能比如登陆用户才可以
            return redirect(url_for('index'))  # 重定向到主页
        #获取表单数据（来自用户填写）
        title = request.form.get('title')    # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        #验证数据是否有效
        if not title or not year or len(title) > 60 or len(year) > 4:
            flash("Invalid input.")    # 显示错误提示
            return redirect(url_for('index'))    # 重定向回主页
        #保存表单数据到数据库
        movid = Movie(title=title, year=year)    # 创建记录
        db.session.add(movid)    # 添加到数据库会话
        db.session.commit()    # 提交数据库会话
        flash("Item Created.")    #显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页

    #user = User(name = 'Alex Goke')     #直接给user赋值，后面采用数据库的方式【弃用】
    user = User.query.first()
    movies = Movie.query.all()
    #return render_template('index.html', user=user, movies=movies)    #render_template() 函数在调用时会识别并执行 index.html 里所有的 Jinja2 语句，返回渲染好的模板内容。
    return render_template('index.html', movies=movies)    #有了模板上下文函数，user可省略


# 编辑电影条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])    #<int:movie_id> 部分表示 URL 变量，而 int 则是将变量转换成整型的 URL 变量转换器。
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)    #get_or_404() 方法，它会返回对应主键的记录，如果没有找到，则返回 404 错误响应。

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

# 删除电影条目
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required  # 登录保护 添加了这个装饰器后，如果未登录的用户访问对应的 URL，Flask-Login 会把用户重定向到登录页面，并显示一个错误提示。
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页   

# 支持设置用户名字
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)    # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))    # 重定向到主页
        
        flash('Invalid username or password.')    # 如果验证失败，显示错误消息
        return redirect(url_for('login'))     # 重定向回登录页面
    return render_template('login.html')

# 登出用户
@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页