#!/usr/bin/python
#coding: utf-8 
#DNS.dnslookup('144.246.202.221.score.senderscore.com','A')
#http://www.rmunn.com/sqlalchemy-tutorial/tutorial.html 
#http://jucacrispim.wordpress.com/2009/12/07/pequena-introducao-ao-sqlalchemy/
#http://www.rmunn.com/sqlalchemy-tutorial/tutorial.html

from lib.postpolicy import Policy
import sys
from multiprocessing import Queue

if __name__ == '__main__':
    daemon = Policy('/tmp/policy.pid', stdout='/tmp/arqlog', stderr='/tmp/errlog')

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'status' == sys.argv[1]:
            daemon.status()
        else:
            print 'Comando Desconhecido'
    else:
        print 'Uso indevido'
        sys.exit(2)
    sys.exit(0)
