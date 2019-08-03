import os
import sys


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ...

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)

#app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')   #读取系统环境变量 SECRET_KEY 的值，如果没有获取到，则使用 dev。

# 注意更新这里的路径，把 app.root_path 添加到 os.path.dirname() 中
# 以便把文件定位到项目根目录
#app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), 'data.db')
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False      # 关闭对模型修改的监控

# 在扩展类实例化前加载配置
db = SQLAlchemy(app)    #初始化扩展，传入程序实例app
login_manager = LoginManager(app)    # 实例化扩展类

# 通过主键查询用户
@login_manager.user_loader
def load_user(user_id):    # 创建用户加载回调函数，接受用户 ID 作为参数
    from watchlist.models import User    #使用的模型类也在函数内进行导入,就是为了避免循环导入
    user = User.query.get(int(user_id))     # 用 ID 作为 User 模型的主键查询对应的用户
    return user

login_manager.login_view = 'login'

# 模板上下文函数，可将返回的变量在html中直接使用
@app.context_processor    #使用 app.context_processor 装饰器注册一个模板上下文处理函数
def inject_user():    #这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板(html)中使用。
    from watchlist.models import User
    user = User.query.first()
    return dict(user=user)    # 需要返回字典，等同于return {'user': user}

#在构造文件中，为了让视图函数、错误处理函数和命令函数注册到程序实例上，我们需要在这里导入这几个模块。
#但是因为这几个模块同时也要导入构造文件中的程序实例，为了避免循环依赖（A 导入 B，B 导入 A），我们把这一行导入语句放到构造文件的结尾。
from watchlist import views, errors, commands    