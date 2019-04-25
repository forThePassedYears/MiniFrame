import re
import pymysql
import urllib.parse as par
from settings import *


PATH_TO_FUNC = dict()


# 实现路由功能的装饰器
def route(path):  # 接收路由
    def wrapper(func):  # 接收对应处理函数
        PATH_TO_FUNC[path] = func  # 将映射添加到字典中
        def function(*args, **kwargs):
            return func(*args, **kwargs)
        return function
    return wrapper


def db_execute(sql, params=[]):
    show_msg = None
    try:
        conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
        cursor = conn.cursor()
        cursor.execute(sql, params)
        show_msg = cursor.fetchall()  # 查询数据
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
    return show_msg
    

@route(r'/index.html')
def index(matched):
    with open('./templates/index.html') as f:
        content = f.read()

    # show_msg = '这里是数据库中的数据'
    show_msg = db_execute('select * from info;')

    templates = """
    <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
            <input type="button" value="添加" id="toAdd" name="toAdd"
            systemIdValue="%s">
        </td>
    </tr>
    """
    html = ''
    for msg in show_msg:
        html += templates % (str(msg[0]), str(msg[1]), str(msg[2]),
        str(msg[3]), str(msg[4]), str(msg[5]), str(msg[6]), str(msg[7]),
        str(msg[1]))
    content = re.sub(r'\{%content%\}', html, content)
    return content


@route(r'/center.html')
def center(matched):
    with open('./templates/center.html') as f:
        content = f.read()

    sql = 'select code, short, chg, turnover, price, highs, note_info from info as i join focus as f on f.info_id=i.id;'

    show_msg = db_execute(sql)  # 查询数据

    templates = """
    <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
            <a type="button" class="btn btn-default btn-xs"
            href="/update/%s.html"> <span class="glyphicon glyphicon-star"
            aria-hidden="true"></span> 修改 </a>
        </td>
        <td>
            <input type="button" value="删除" id="toDel" name="toDel"
            systemIdValue="%s">
        </td>
    </tr>
    """
    html = ''
    for msg in show_msg:
        html += templates % (str(msg[0]),str(msg[1]),str(msg[2]),str(msg[3]),
        str(msg[4]),str(msg[5]),str(msg[6]),str(msg[0]),str(msg[0]))
    
    content = re.sub(r'\{%content%\}', html, content)
    return content


@route(r'/add/(\d+)\.html')
def add_focus(matched):
    try:
        code = matched[0]
        database_conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
        cursor = database_conn.cursor()
        sql_1 = 'select id from info where code=%s'
        params = [code]
        cursor.execute(sql_1, params)
        info_id = cursor.fetchone()
        # 判断关注的股票是否存在
        if not info_id:
            return '请求错误！'
        # 判断关注股票是否已经关注过
        sql_2 = 'select id from focus where info_id=%s'
        cursor.execute(sql_2, info_id[0])
        is_exist = cursor.fetchall()
        if is_exist:
            return '该股票已关注！请点击个人中心查看！'
        sql_3 = 'insert into focus(info_id) value(%s)'
        cursor.execute(sql_3, info_id[0])
        database_conn.commit()
        return '关注成功!'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        database_conn.close()


@route(r'/del/(\d+)\.html')
def del_focus(matched):
    try:
        code = matched[0]
        database_conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
        cursor = database_conn.cursor()
        sql_1 = 'select id from info where code=%s'
        params = [code]
        cursor.execute(sql_1, params)
        info_id = cursor.fetchone()
        # 判断关注的股票是否存在
        if not info_id:
            return '请求错误！'
        # 判断关注股票是否已经关注过
        sql_2 = 'select id from focus where info_id=%s'
        cursor.execute(sql_2, info_id[0])
        is_exist = cursor.fetchall()
        if not is_exist:
            return '未关注该股票！请确认股票代码！'
        sql_3 = 'delete from focus where info_id=%s'
        cursor.execute(sql_3, info_id[0])
        database_conn.commit()
        return '删除成功！'
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        database_conn.close()


@route('/update/(\d+)\.html')
def update_page(matched):
    with open('./templates/update.html', 'r') as f:
        content = f.read()
    sql_1 = 'select id from info where code=%s'
    code = db_execute(sql_1, [matched[0]])
    if not code:
        return '请求错误！'
    sql_2 = 'select note_info from focus where info_id=%s'
    results = db_execute(sql_2, [code[0]])
    if not results:
        return '股票代码错误！'
    content = re.sub('\{%note_info%\}', results[0][0], content)
    content = re.sub('\{%code%\}', matched[0], content)
    return content


@route(r'/update/(\d+)/(.*)\.html')
def update_note_info(matched):
    try:
        matched = matched[0]
        code = matched[0]
        note = par.unquote(matched[1])
        database_conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
        cursor = database_conn.cursor()
        sql_0 = 'select id from info where code=%s'
        cursor.execute(sql_0, [code])
        info_id = cursor.fetchone()
        # 判断关注的股票是否存在
        if not info_id:
            return '请求错误！'
        # 判断关注股票是否已经关注过
        sql_2 = 'update focus set note_info=%s where info_id=%s'
        cursor.execute(sql_2, [note, info_id])
        database_conn.commit()
        return '修改成功！'
    except Exception as e:
        print(e)
        return '修改失败！'
    finally:
        cursor.close()
        database_conn.close()


def application(environ, start_response):
    # 实现WSGI协议
    try:
        # 返回响应头
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])

        file_name = environ['PATH_INFO']
        for route, func in PATH_TO_FUNC.items():
            result = re.compile(route).findall(file_name)
            if len(result) > 0:
                return func(result)  # 返回响应体
        start_response('404 Failed', [('Content-Type', 'text/html;charset=utf-8')])
        return '<h1>404 Not Found</h1>'
    except Exception:
        start_response('404 Failed', [('Content-Type', 'text/html;charset=utf-8')])
        return '<h1>404 Not Found</h1>'

