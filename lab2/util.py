# -*- coding:utf-8 -*-
import sys
import select
from random import random


HOST = '127.0.0.1'

SERVER_PORT = 8888
CLIENT_PORT = 8889


SERVER_PORT_EXTRA = 5003
CLIENT_PORT_EXTRA = 5004

BUFFER_SIZE = 2048

WINDOWS_LENGTH = 8
SEQ_LENGTH = 10


MAX_TIME = 3


class Data(object):
    def __init__(self,msg,seq = 0,state = 0):
        self.msg = msg
        ##数据状态 0：未发送
        self.state = state
        self.seq = str(seq % SEQ_LENGTH)

    def __str__(self):
        return self.seq + ' ' +self.msg


class Gbn(object):
    def __init__(self,sock):
        self.sock = sock
    
    def push_data(self,path,port):
        
        time = 0
        seq = 0
        data_windows = []

        with open(path,'r') as file_handle:
            while True:

                #超时后 ，将窗口打数据更改状态    
                if time > MAX_TIME:
                    for data in data_windows:
                        data.state = 0

                while len(data_windows) <WINDOWS_LENGTH:
                    line = file_handle.readline().rstrip()
                    if not line :
                        return
                    
                    data = Data(line,seq = seq)
                    data_windows.append(data)
                    seq += 1

                if not data_windows:
                    break
                
                ##发送窗口中未发送的数据
                for data in data_windows:
                    if not data.state:
                        self.sock.sendto(str(data),(HOST,port))
                        data.state = 1
                ##监控socket是否有数据可接收
                readable,writeable,errors = select.select([self.sock,],[],[],1)
                if len(readable):

                    time = 0

                    message,address = self.sock.recvfrom(BUFFER_SIZE)

                    sys.stdout.write("gbn ACK " + message +'\n')
                    
                    ##查看是ack的序号
                    for i in range(len(data_windows)):
                        if message == data_windows[i].seq:
                            data_windows = data_windows[i+1:]
                            break
                else:
                    time += 1

        self.sock.close()
    
    def pull_data(self):
        #记录上一个ACK
        last_ack = SEQ_LENGTH -1
        
        data_windows = []

        while True:
            readable,writeable,errors = select.select([self.sock,],[],[],1)

            if len(readable) > 0:
                message,address = self.sock.recvfrom(BUFFER_SIZE)
                
                ack = int(message.split()[0])
                ##假如有序收到.发回ack
                if last_ack ==(ack - 1) % SEQ_LENGTH:
                    ##假设 丢包率为 20% ，即有20%的包认为没收到ACK
                    if random()< 0.2:
                        continue
                    
                    self.sock.sendto(str(ack),address)
                    
                    last_ack = ack
                    
                    ##判断是否重复
                    if ack not in data_windows:
                        data_windows.append(ack)
                        sys.stdout.write('gbn recv:'+ message + '\n')
                    while len(data_windows) > WINDOWS_LENGTH:
                        data_windows.pop(0)
                else:
                    self.sock.sendto(str(last_ack),address)
        self.sock.close()


class SR(object):
    def __init__(self,sock):
        self.sock = sock
    
    def push_data(self,path,port):
        
        time = 0
        seq = 0
        
        data_windows = []
        with open(path,'r') as file_handle:
            while True:
                ##当超时后，将窗口内第一个发送成功但是未确认打数据状态更改未未发送
                if time >MAX_TIME:
                    for data in data_windows:
                        if data.state == 1:
                            data.state = 0
                            break
                # 窗口中数据少于最大容量时，尝试添加新数据
                while len(data_windows) < WINDOWS_LENGTH:
                    line = file_handle.readline().strip()
                    if not line:
                        return

                    data = Data(line,seq = seq)
                    data_windows.append(data)
                    seq += 1
                if not data_windows:
                    break
                # 遍历窗口内数据，如果存在未成功发送的则发送
                for data in data_windows:
                    if not data.state:
                        self.sock.sendto(str(data),(HOST,port))
                        data.state = 1

                readable,writeable,errors = select.select([self.sock,],[],[],1)
                if len(readable) > 0:
                    time = 0
                    message,address = self.sock.recvfrom(BUFFER_SIZE)
                    
                    sys.stdout.write('sr ack '+message + '\n')
                    
                    ##收到状态后更改数据包状态为已接收
                    
                    for data in data_windows:
                        if message == data.seq:
                            data.state = 2
                            break
                else:
                    time += 1
                
                # 当窗口中首个数据已接收时，窗口前移
                while data_windows[0].state == 2:
                    data_windows.pop(0)
                    
                    if not data_windows:
                        break

        self.sock.close()
                    
                    
    def pull_data(self):
        seq = 0
        data_windows = {}
        
        while True:
            readable,writeable,errors = select.select([self.sock,],[],[],1)
            
            if len(readable) > 0:
                message,address =self.sock.recvfrom(BUFFER_SIZE)
                
                ack = message.split()[0]
                
                if random() < 0.2:
                    continue
                
                self.sock.sendto(ack,address)
                data_windows[ack] = message.split()[1]

                #滑动窗口
                while str(seq) in data_windows:
                    sys.stdout.write('sr pull' + str(seq) + ' ' + data_windows[str(seq)] + '\n')
                    data_windows.pop(str(seq))
                    seq = (seq + 1) % SEQ_LENGTH

        self.s.close()

