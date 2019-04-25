import socket
import select
import re
# import dynamic.mini_frame
import sys
import logging
from settings import *


# 创建logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 创建handler，用于将日志写入文件
logfile = LOG_FILE
fh = logging.FileHandler(logfile, mode='a')  # 设置日志文件和写入模式
fh.setLevel(logging.DEBUG)  # 设置写入日志的信息等级

# 创建handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 设置日志输入格式
formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 将handler添加到logger对象中
logger.addHandler(fh)
logger.addHandler(ch)


class WSGIServer(object):

    def __init__(self, port, app, static_path):
        # 创建tcp套接字
        self.http_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 防止服务器先关闭套接字时,端口不能重用的问题
        self.http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定地址端口
        self.http_server.bind(('', port))
        logger.debug('开始监听%d端口'.format(port))
        logger.debug('访问: http://127.0.0.1:%d'.format(port))

        # 开始监听
        self.http_server.listen(128)

        # 设置为非阻塞
        self.http_server.setblocking(False)

        # 创建epoll对象
        self.epl = select.epoll()

        # 将监听套接字的文件描述符放入epoll列表内，并监听相应事件
        # EPOLLIN是输入事件
        self.epl.register(self.http_server.fileno(), select.EPOLLIN)

        # 创建客户端字典，为后面获取文件描述符相应的套接字做记录
        self.fd_event_dict = dict()

        # 接收app的name
        self.application = app

        # 接收static 路径
        self.static_path = static_path

    def handler(self, client, recv_data):
        '''处理客户端请求，返回数据'''
        # 接收数据
        data = recv_data.decode()
        # 按行分割
        data_lines = data.splitlines()
        print('>' * 50)
        print(data_lines)
        print('\r\n\r\n')
        file_name = ''
        try:
            ret = re.match(r"[^/]+(/[^ ]*)", data_lines[0])
        except:
            ret = None
        if ret:
            file_name = ret.group(1)
            if file_name == '/':
                file_name = '/index.html'

        # 如果请求的资源不是以.html结尾的,那么就认为是静态资源
        if not file_name.endswith('html'):
            try:
                f = open(self.static_path + file_name, 'r')
                header = 'HTTP/1.1 200 OK\r\n'
                header += '\r\n'
                response = header + f.read()
            except:
                response = 'HTTP/1.1 404 NOT FOUND\r\n'
                response += '\r\n 404 NOT FOUND'
        else:
            # 重点部分 ####################################
            # 如果是以html结尾的，那么就认为是请求动态资源
            env = dict()
            env['PATH_INFO'] = file_name
            # 将请求的信息 存入env字典中，传给web框架
            body = self.application(env, self.set_response_header)

            # 将服务器和web框架返回的响应头进行拼接
            header = 'HTTP/1.1 %s \r\n' % self.status
            for temp in self.headers:
                header += '%s:%s \r\n' % temp

            header += '\r\n'

            response = header + body

        # 返回数据
        client.send(response.encode('utf-8'))

        # 关闭套接字
        client.close()

    def set_response_header(self, status, headers):
        # 接收web框架返回的响应头
        self.status = status
        self.headers = [('Server', 'Ordinary-Web')]
        self.headers += headers

    def run_forever(self):
        # 等待链接
        while True:
            # 默认阻塞，解阻塞时返回产生事件的套接字的文件描述符和相应事件
            fd_event_list = self.epl.poll()  # [(fd, event),(文件描述符，事件)]
            # 遍历监听到相应事件的文件描述符和文件类型
            for fd, event in fd_event_list:
                if fd == self.http_server.fileno():
                    client_socket, client_addr = self.http_server.accept()
                    print('新的客户端连接：', client_addr)
                    self.epl.register(client_socket.fileno(), select.EPOLLIN)
                    self.fd_event_dict[client_socket.fileno()] = client_socket
                elif event == select.EPOLLIN:
                    recv_data = self.fd_event_dict[fd].recv(1024)
                    if recv_data:
                        self.handler(self.fd_event_dict[fd], recv_data)
                    else:
                        self.fd_event_dict[fd].close()
                        self.epl.unregister(fd)
                        del self.fd_event_dict[fd]


def main():
    '''控制整体，创建一个web服务器对象，然后调用这个对象的run_forever方法运行'''

    sys.path.append(WSGI_APPLICATION)  # 将导入路径添加到环境中

    frame = __import__(FRAME_NAME)  # 返回值标记着导入的模块
    app = getattr(frame, APPLICATION)  # 去frame模块寻找app_name的函数首地址

    wsgi_server = WSGIServer(PORT, app, STATIC_DIRS)
    wsgi_server.run_forever()


if __name__ == '__main__':
    main()
