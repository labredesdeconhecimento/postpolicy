#!/usr/bin/python
#coding: utf-8

#from multiprocessing.reduction import reduce_handle, rebuild_handle
from datetime import datetime, timedelta
from daemon import Daemon
from time import sleep, strftime
from os import getpid, getppid, fdopen
from dns.resolver import query, NXDOMAIN
import multiprocessing
import socket
import sys
import settings
import sqlite3


class Worker(multiprocessing.Process):
    def __init__(self, socket, pid):
        multiprocessing.Process.__init__(self)
        self.socket = socket
        self.ppid = pid

    def run(self):
        sys.stdout = fdopen(sys.stdout.fileno(), 'w', 0)
        base = SenderScore('{}/local.db'.format(settings.DBPATH))
        while getppid() == self.ppid:
            try:
                con, ip = self.socket.accept()
                data = con.recv(2048)
                resp = base.action(data)
                con.send(resp)
                con.close()
            except socket.error:
                sleep(0.2)
                continue
        print 'Fechando o Worker'


class Policy(Daemon):
    __queue = multiprocessing.Queue()

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null',
                 stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(2)
        self.socket.setblocking(0)
        self.socket.bind(('', 8888))
        self.socket.listen(5)
        for x in range(0, settings.PROCS):
            mp = Worker(self.socket, getpid())
            mp.start()
        while True:
            sleep(0.5)


class SenderScore:

    def __init__(self, base):
        self.__con = sqlite3.connect(base)
        cursor = self.__con.cursor()
        cursor.execute(
        ''' CREATE  TABLE  IF NOT EXISTS score (
        ip text PRIMARY KEY  NOT NULL,
        count INTEGER NOT NULL  DEFAULT 0,
        expiration FLOAT NOT NULL)''')
        self.__con.commit()

    def __get_reputation(self, sender):
        sender = '.'.join(reversed(sender.split('.')))
        try:
            data = query('{}.score.senderscore.com'.format(sender),
                         'A')
            return data[0].address.split('.')[-1]
        except NXDOMAIN:
            return None

    def __ch_sender(self, sender):
        cursor = self.__con.cursor()
        cursor.execute('''SELECT * FROM score WHERE ip = ?''', (sender, ))
        resultado = cursor.fetchall()
        hora = datetime.now() + timedelta(hours=1)
        try:
            if len(resultado) == 0:
                cursor.execute('''INSERT INTO score (ip, count, expiration)
                                    VALUES (?,?,?)''',
                                    (sender, 1, strftime('%s', hora.timetuple())))
            elif resultado[0][2] < float(strftime('%s', datetime.now().timetuple())):
                print strftime('%s', hora.timetuple()), sender
                cursor.execute('''UPDATE score
                                    SET count = 1, expiration = ?
                                    WHERE ip = ?''',
                                    (strftime('%s', hora.timetuple()), sender))
            else:
                cursor.execute('''UPDATE score
                                    SET count = count+1
                                    WHERE ip =?''', (sender, ))
            self.__con.commit()
        except:
            self.__con.rollback()

    def __get_sender(self, sender):
        cursor = self.__con.cursor()
        cursor.execute('''SELECT ip, count, expiration
                            FROM score where ip = ?''', (sender,))
        linhas = cursor.fetchone()
        return (linhas[0], linhas[1], linhas[2])

    def __parser(self, data):
        try:
            sender = None
            for x in data.split():
                chave, valor = x.split('=')
                if chave == 'client_address':
                    sender = valor
                    break
            return sender
        except:
            return None

    def action(self, data):
        sender = self.__parser(data)
        for x in xrange(10000):
            print x
        if sender:
            rep = self.__get_reputation(sender)
            if rep:
                self.__ch_sender(sender)
                stats = self.__get_sender(sender)
                if stats[1] > int(rep) * settings.MULT:
                    msg = 'action=421 sender score reputation = {0}, '\
                            'you are limited to {1} messages/hours '\
                            'in our policy, try again later\n\n'''.format(
                            rep, int(rep) * settings.MULT)
                    return msg
        return 'action=dunno\n\n'
