from threading import *
from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import numpy as np
import cv2
import sys
from queue import Queue 



class Signal(QObject):
    conn_signal = pyqtSignal()
    recv_signal = pyqtSignal(str)


class ServerSocket:

	
    def __init__(self):
        #self.parent = parent
        self.bListen = False
        self.clients = []
        self.ip = []
        self.threads = []

        self.conn = Signal()
        self.recv = Signal()
        self.queue = Queue()
        
        #self.conn.conn_signal.connect(self.parent.updateClient)
        #self.recv.recv_signal.connect(self.parent.updateMsg)
	

    def __del__(self):
        self.stop()

    def start(self, ip, port):
        self.server = socket(AF_INET, SOCK_STREAM)

        try:
            self.server.bind((ip, port))
        except Exception as e:
            print('Bind Error : ', e)
            return False
        else:
            self.bListen = True
            self.t = Thread(target=self.listen, args=(self.server,))
            self.t.start()
            print('Server Listening...')

        return True

    def stop(self):
        self.bListen = False
        if hasattr(self, 'server'):
            self.server.close()
            print('Server Stop')

    def listen(self, server):
        while self.bListen:
            server.listen(5)
            try:
                client, addr = server.accept()
            except Exception as e:
                print('Accept() Error : ', e)
                break
            else:
                self.clients.append(client)
                self.ip.append(addr)
                self.conn.conn_signal.emit()
                t = Thread(target=self.receive, args=(addr, client))
                self.threads.append(t)
                t.start()

        self.removeAllClients()
        self.server.close()

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def receive(self, addr, client):
        while True:
            try:
                length = self.recvall(client,16)
                recv = self.recvall(client, int(length))
                data = np.frombuffer(recv, dtype='uint8')
                decimg = cv2.imdecode(data, 1)
                #cv2.imshow('Image', decimg)
                self.queue.put(data)

                key = cv2.waitKey(1)
                if key == 27:
                    break

            except Exception as e:
                print('Recv() Error :', e)
                break
            #else:
            #    msg = str(recv, encoding='utf-8')
            #    if msg:
            #        self.send(msg)
            #        self.recv.recv_signal.emit(msg)
            #        print('[RECV]:', addr, msg)

        self.removeCleint(addr, client)

    def send(self, msg):
        try:
            for c in self.clients:
                c.send(msg.encode())
        except Exception as e:
            print('Send() Error : ', e)

    def removeCleint(self, addr, client):
        client.close()
        self.ip.remove(addr)
        self.clients.remove(client)

        self.conn.conn_signal.emit()

        i = 0
        for t in self.threads[:]:
            if not t.isAlive():
                del (self.threads[i])
            i += 1

        self.resourceInfo()

    def removeAllClients(self):
        for c in self.clients:
            c.close()

        self.ip.clear()
        self.clients.clear()
        self.threads.clear()

        self.conn.conn_signal.emit()

        self.resourceInfo()

    def resourceInfo(self):
        print('Number of Client ip\t: ', len(self.ip))
        print('Number of Client socket\t: ', len(self.clients))
        print('Number of Client thread\t: ', len(self.threads))
