import os
import sys
import click

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy    #导入扩展类
from flask import request, url_for, redirect, flash
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


@app.cli.command()    #创建自定义命令 initdb
@click.option('--drop', is_flag=True, help='Create after drop.')    #设置选项
def initdb(drop):
    """Initialize the database"""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo("Initialize database.")    #输出提示信息


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



class User(db.Model):  # 表名将会是 user（自动生成，小写处理）    
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字


class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份


# 这个视图函数处理哪种方法类型的请求。默认只接受 GET 请求，上面的写法表示同时接受 GET 和 POST 请求。
@app.route('/', methods=['GET', 'POST'])    # index-索引，即主页
def index():

    if request.method == 'POST':    #判断是否是post请求
        #获取表单数据
        title = request.form.get('title')    # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        #验证数据是否有效
        if not title or not year or len(title) > 60 or len(year) > 4:
            flash("Invalid inpur.")    # 显示错误提示
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
    

@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    #这个函数返回了状态码作为第二个参数，普通的视图函数之所以不用写出状态码，是因为默认会使用 200 状态码，表示成功。
    #return render_template('404.html', user=user), 404    #返回模板 和 状态码
    return render_template('404.html'), 404    ##有了模板上下文函数，user可省略
    

@app.context_processor    #使用 app.context_processor 装饰器注册一个模板上下文处理函数
def inject_user():    #这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板(html)中使用。
    user = User.query.first()
    return dict(user=user)    # 需要返回字典，等同于return {'user': user}


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])    #<int:movie_id> 部分表示 URL 变量，而 int 则是将变量转换成整型的 URL 变量转换器。
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

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页