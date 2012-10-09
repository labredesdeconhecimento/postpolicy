#!/usr/bin/python
#coding: utf-8

from multiprocessing.reduction import reduce_handle, rebuild_handle
from datetime import *
from daemon import Daemon
from settings import *
from time import sleep
import multiprocessing
import socket
import sys
from os import getpid, getppid, fdopen

class Worker(multiprocessing.Process):
    def __init__(self, queue, pid):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.ppid = pid
    
    def run(self):
        sys.stdout = fdopen(sys.stdout.fileno(), 'w', 0)
        #fd = rebuild_handle(self.handle)
        #sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
        while getppid() == self.ppid:
            try:
                handle = self.queue.get_nowait()
                fd = rebuild_handle(handle)
                sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
                sock.send('bye')
                sock.shutdown()
                sock.close()
            except:
                sleep(0.5)
                continue
        print 'Fechando o Worker' 

class Policy(Daemon):
    __queue = multiprocessing.Queue()
    
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        
    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', 8888))
        self.socket.listen(5)
        for x in range(0, PROCS):
            mp = Worker(self.__queue, getpid())
            mp.start()
        while True:
            con, cli = self.socket.accept()
            handle = reduce_handle(con.fileno())
            self.__queue.put(handle)
        
class Mx:
    '''
    Classe para gerenciamento dos servidores de envio de email (Mx's)
    '''
    _mx = ''
    _cont = 0
    _expiration =  ''

    def __init__(self, mx):
        self._mx = mx
        self._cont = 1
        self._expiration = datetime.now()+timedelta(hours=1)

    def get_mx(self):
        return self._mx

    def get_cont(self):
        return self._cont

    def get_expiration(self):
        return self._expiration

    def inc_cont(self):
        self._cont += 1
        return self._cont

    def zero(self):
        self._expiration = datetime.now()+timedelta(hours=1)
        self._cont = 1

    def expired(self):
        if self._expiration >= datetime.now():
            return False
        return True

