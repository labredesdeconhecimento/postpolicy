#!/usr/bin/python
#coding: utf-8

from lib.postpolicy import Policy
import sys

if __name__ == '__main__':
    daemon = Policy('/tmp/policy.pid',
                    stdout='/tmp/arqlog',
                    stderr='/tmp/errlog')

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
