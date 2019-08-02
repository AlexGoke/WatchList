import os
import sys
import click

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy    #导入扩展类
from flask import request, url_for, redirect, flash

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from flask_login import login_user
from flask_login import login_required, logout_user
from flask_login import login_required, current_user
#...

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False      # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'

# 在扩展类实例化前加载配置
db = SQLAlchemy(app)    #初始化扩展，传入程序实例app

login_manager = LoginManager(app)    # 实例化扩展类
login_manager.login_view = 'login'


#...

# 通过主键查询用户
@login_manager.user_loader
def load_user(user_id):    # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))     # 用 ID 作为 User 模型的主键查询对应的用户
    return user

# 自定义命令 —— 生成新的数据库
@app.cli.command()    #创建自定义命令 initdb
@click.option('--drop', is_flag=True, help='Create after drop.')    #设置选项
def initdb(drop):
    """Initialize the database"""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo("Initialized database.")    #输出提示信息

# 自定义命令 —— 数据库初始化数据
@app.cli.command()    #创建自定义命令 froge. 执行该命令即可将虚拟数据添加到数据库里。
def forge():
    """Generate fake data"""
    db.create_all()

    #全局的两个变量移动到这个函数内
    name = 'Alex Goke'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    
    db.session.commit()
    click.echo('Done.')


# 生成管理员账户
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=False, confirmation_prompt=True, help='The password used to login.')    # 这里只能先把hide_input关闭，不然我的命令行会卡住，源代码是打开的，只有我有这个问题。郁闷。。。
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')

# 用户模型 数据库表
class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）    # 继承 UserMixin类会让 User 类拥有几个用于判断认证状态的属性和方法
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    username = db.Column(db.String(20))    # 用户名
    password_hash = db.Column(db.String(128))    # 密码散列值
    
    def set_password(self, password):    # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):    # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值

# 电影记录 数据库表
class Movie(db.Model):   # 表名将会是movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份


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
    
# 错误处理函数
@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    #这个函数返回了状态码作为第二个参数，普通的视图函数之所以不用写出状态码，是因为默认会使用 200 状态码，表示成功。
    #return render_template('404.html', user=user), 404    #返回模板 和 状态码
    return render_template('404.html'), 404    ##有了模板上下文函数，user可省略
    

# 模板上下文函数，可将返回的变量在html中直接使用
@app.context_processor    #使用 app.context_processor 装饰器注册一个模板上下文处理函数
def inject_user():    #这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板(html)中使用。
    user = User.query.first()
    return dict(user=user)    # 需要返回字典，等同于return {'user': user}

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