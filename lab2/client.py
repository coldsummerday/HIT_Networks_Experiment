# -*- coding:utf-8 -*-
import socket
import thread
import server
import threading
from util import *


def new_client_socket(client_port, protocol):
    # 设置网络连接为ipv4， 传输层协议为tcp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 传输完成后立即回收该端口
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 任意ip均可以访问
    s.bind(('', client_port))

    p = protocol(s)
    p.pull_data()


if __name__ == '__main__':

    t = threading.Thread(target=server.new_server_socket,args=(CLIENT_PORT_EXTRA,SERVER_PORT_EXTRA,'testdata/client_push.txt',Gbn,))
    t.start()
    new_client_socket(CLIENT_PORT, Gbn)


