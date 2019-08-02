import unittest    

from app import app, db, User, Movie
from app import forge, initdb    # 导入命令函数（都是自定义的命令）

class WatchlistTestCase(unittest.TestCase):    #测试用例
    
    #测试固件， setUp() 方法会在每个测试方法执行前被调用
    def setUp(self):    
        # 更新配置
        app.config.update(
            TESTING = True,    #将 TESTING 设为 True 来开启测试模式，这样在出错时不会输出多余信息
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'    #这会使用 SQLite 内存型数据库，不会干扰开发时使用的数据库文件。你也可以使用不同文件名的 SQLite 数据库文件，但内存型数据库速度更快
        )
        # 创建数据库和表
        db.create_all()

        # 创建测试用例，一个用户，一个电影条目
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2019')
        # 使用 add_all() 方法一次添加多个模型类实例，传入列表
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()    # 创建测试客户端（浏览器） —— 用来模拟客户端请求， 创建类属性 self.client 来保存它
                                           #对它调用 get() 方法就相当于浏览器向服务器发送 GET 请求，调用 post() 则相当于浏览器向服务器发送 POST 请求
        
        self.runner = app.test_cli_runner()    #创建测试命令运行器 —— 用来触发自定义命令
                                               # 通过对它调用 invoke() 方法可以执行命令，传入命令函数对象，或是使用 args 关键字直接给出命令参数列表。

     #测试固件， tearDown() 方法则会在每一个测试方法执行后被调用
    def tearDown(self):   
        db.session.remove()  # 清除数据库会话 需要调用 db.session.remove() 来确保数据库会话被清除。
        db.drop_all()  # 删除数据库表




    # 测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)

    # 测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])


# ---
# 测试客户端

    #测试固件---------------------------------------------------------

    # 测试 404 页面
    def test_404_page(self):
        response = self.client.get('/nothing')  # 传入目标 URL    调用这类方法返回包含响应数据的响应对象
        data = response.get_data(as_text=True)    #对这个响应对象调用 get_data() 方法并把 as_text 参数设为 True 可以获取 Unicode 格式的响应主体
        # 判断响应主体中是否包含预期的内容来测试程序是否正常工作
        self.assertIn('Page Not Found - 404', data)    
        self.assertIn('Go Back', data)            #404 页面响应是否包含 Go Back
        self.assertEqual(response.status_code, 404)  # 判断响应状态码

    # 测试主页
    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)    #主页响应是否包含标题 Test's Watchlist
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    # 测试辅助方法-----------------------------------------------------
    
    # 这些操作对应的请求都需要登录账户后才能发送，我们先编写一个用于登录账户的辅助方法
    # 辅助方法，用于登入用户
    def login(self):
        self.client.post('/login', data=dict(    #使用 post() 方法发送提交登录表单的 POST 请求。 使用 data 关键字以字典的形式传入请求数据
            username='test',
            password='123'
        ), follow_redirects=True)    #将 follow_redirects 参数设为 True 可以跟随重定向，最终返回的会是重定向后的响应。

    # 测试创建、删除更新条目---------------------------------------------
    # 接下来，我们要测试数据库操作相关的功能 比如创建、更新和删除电影条目。
    
    # 测试创建条目
    def test_create_item(self):
        self.login()    # 先登入用户

        # 测试创建条目操作
        response = self.client.post('/', data=dict(
            title='New Movie',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item Created.', data)
        self.assertIn('New Movie', data)

        # 测试创建条目操作，但电影标题为空
        response = self.client.post('/', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

        # 测试创建条目操作，但电影年份为空
        response = self.client.post('/', data=dict(
            title='New Movie',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

    # 测试更新条目
    def test_update_item(self):
        self.login()

        # 测试更新页面
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2019', data)

        # 测试更新条目操作
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated.', data)
        self.assertIn('New Movie Edited', data)

        # 测试更新条目操作，但电影标题为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        # 测试更新条目操作，但电影年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited Again',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('Invalid input.', data)
    
    # 测试删除条目
    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie Title', data)

    # 在这几个测试方法中，大部分的断言都是在判断响应主体是否包含正确的提示消息和电影条目信息。

    # 测试认证相关功能 ---------------------------------------------------
    
    # 测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
    
    # 测试登录
    def test_login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        # 测试使用错误的密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password='456'    #错误的密码
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)


        # 测试使用错误的用户名登录
        response = self.client.post('/login', data=dict(
            username='wrong',    #错误的用户名
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试使用空用户名登录
        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 测试使用空密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)


    # 测试登出
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)

    # 测试设置
    def test_settings(self):
        self.login()

        # 测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        #测试更新设置
        response = self.client.post('/settings', data=dict(
            name='Grey Li',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Grey Li', data)

        # 测试更新设置，名称为空
        response = self.client.post('/settings', data=dict(
            name='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)

# ---
# 测试命令

# 除了上面测的各个视图函数，我们还需要测试自定义命令

# app.test_cli_runner() 方法返回一个命令运行器对象，我们创建类属性 self.runner 来保存它。
# 对它调用 invoke() 方法可以执行命令，传入命令函数对象，或是使用 args 关键字直接给出命令参数列表。
# invoke() 方法返回的命令执行结果对象，它的 output 属性返回命令的输出信息。

    # 测试虚拟数据
    def test_forge_command(self):
        result = self.runner.invoke(forge)    # 执行自定义 forge命令——给数据库填满初始化虚拟数据。
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    # 测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)    # 执行自定义 initdb命令
        self.assertIn('Initialized database.', result.output)

    # 测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'grey', '--password', '123'])    # 执行自定义 admin命令
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'grey')
        self.assertTrue(User.query.first().validate_password('123'))

    # 测试更新管理员账户
    def test_admin_command_update(self):
        # 使用 args 参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'peter')
        self.assertTrue(User.query.first().validate_password('456'))

# 在这几个测试中，大部分的断言是在检查执行命令后的数据库数据是否发生了正确的变化，或是判断命令行输出（result.output）是否包含预期的字符。

if __name__ == '__main__':
    unittest.main()