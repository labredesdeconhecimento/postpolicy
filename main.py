#!/usr/bin/python
#coding: utf-8
'''
###############
Módulo *main*
###############

    :Plataforma: \*nix
    :Sinopse: Módulo principal do projeto que instancia o objeto da classe \
Policy que gerencia toda a estrutura do Daemon.

.. moduleauthor:: Ronaldo A. Marques Jr. <ralvesmj@gmail.com>

Argumentos
----------

.. cmdoption:: comando

    Comando a ser passado para o daemon.

Código
------
'''

from lib.postpolicy import Policy
from lib.settings import LOGS
from argparse import ArgumentParser, ArgumentTypeError
from sys import exit


def commands(comando):
    '''
    Função que checa o comando informado a ser interpretado pelo Daemon.
    Através de um método da classe Policy, determinada tarefa do Daemon
    é executada.

    :param comando: comando a ser executado pelo daemon.
    :type p: str
    :returns: Executa uma tarefa específica para o Daemon.
    '''
    if comando not in ['start', 'stop', 'status', 'reports']:
        raise ArgumentTypeError('Comando desconhecido')
    return comando

if __name__ == '__main__':
    daemon = Policy('/tmp/policy.pid',
                    stdout='{}/postpolicy.log'.format(LOGS),
                    stderr='{}/postpolicy.err.log'.format(LOGS))
    parser = ArgumentParser()
    parser.add_argument('comando', help='Comando para o daemon', type=commands)
    args = parser.parse_args()

    if args.comando == 'start':
        daemon.start()
    elif args.comando == 'stop':
        daemon.stop()
    elif args.comando == 'status':
        daemon.status()
    elif args.comando == 'reports':
        daemon.reports()
    exit(0)
