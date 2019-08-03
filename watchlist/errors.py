from flask import render_template

from watchlist import app

# 错误处理函数
@app.errorhandler(404)
def page_not_found(e):
    #这个函数返回了状态码作为第二个参数，普通的视图函数之所以不用写出状态码，是因为默认会使用 200 状态码，表示成功。
    #return render_template('404.html', user=user), 404    #返回模板 和 状态码
    return render_template('errors/404.html'), 404    ##有了模板上下文函数，user可省略

@app.errorhandler(400)
def bad_request(e):
    return render_template('errors/400.html'), 400

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500
