#!/usr/bin/python
#coding: utf-8
'''
.. moduleauthor:: Ronaldo A. Marques Jr. <ralvesmj@gmail.com>
:Plataforma: \*nix
:Sinopse: Módulo que possui praticamente todo o código desenvolvido para \
uso do Daemon. Existem três classes que gerenciam a alma da solução.

- A classe :class:`Worker`, que controla as threads utilizadas pela classe \
:class:`Policy`.
- A classe :class:`Policy`, reescreve o método :meth:`lib.daemon.Daemon.run` \
da classe :class:`lib.daemon.Daemon` e define o que deve ser feito quando o \
Daemon inicia.
- A classe :class:`SenderScore`, faz toda a avaliação do servidor que está \
enviando a mensagem (um servidor SMTP) e define uma ação para o mesmo. Esta \
ação quando passada a um servidor Postfix garante a entrega do email ou a \
emissão de um erro temporário.

Código
------
'''
from datetime import datetime, timedelta
from daemon import Daemon
from time import sleep, strftime
from os import getpid, getppid, fdopen
from dns.resolver import query, NXDOMAIN
import multiprocessing
import socket
import sys
import os
import types
import settings
import sqlite3


class Worker(multiprocessing.Process):
    '''
    Classe que extende a classe :class:`multiprocessing.Process` e que define\
    os passos que cada uma das threads do Daemon realizará ao receber uma\
    conexão. Ela instancia a classe :class:`SenderScore` que manipula os dados\
    obtidos através do Postfix e responde uma ação devida através do socket.

    :param socket: socket instanciado. Cada uma das instâncias das threads\
    recebe dados deste socket e os trata.
    :type socket: :meth:`socket.socket`
    :param pid: pid do processo pai. Cada thread possui como critério de saída\
    a inexistência do processo pai, que é identificado por este valor \
    informado.
    :type pid: int
    '''
    def __init__(self, socket, pid):
        multiprocessing.Process.__init__(self)
        self.socket = socket
        self.ppid = pid

    def run(self):
        '''
        Método reescrito para fazer com que a thread receba os dados passados\
        via socket pelo Postfix e responda através deste socket a ação a ser\
        tomada pelo SMTP. A ação é recuperada através do método \
        :meth:`SenderScore.action`.
        '''
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
        base.close()


class Policy(Daemon):
    '''
    Classe que extende :class:`lib.daemon.Daemon` e que define\
    as operações básicas para o Daemon. Ações como parar, iniciar, verificar\
    o estado e outros são realizados.

    :param pidfile: arquivo que guarda o pid do processo.
    :type pidfile: str
    :param stdin: valor que especifica o caminho do arquivo que guardará\
    informações a serem passadas como entrada para o Daemon.
    :type stdin: str
    :param stdout: valor que especifica o caminho do arquivo que guardará\
    informações de saída do Daemon.
    :type stdout: str
    :param stderr: valor que especifica o caminho do arquivo que guardará\
    informações de saída de erro do Daemon.
    :type stderr: str
    '''

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null',
                 stderr='/dev/null'):
        self.checkconfig()
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def run(self):
        '''
        Método que reescreve o método :meth:`lib.daemon.Daemon.run` para fazer\
        com que o Daemon realize as tarefas necessárias ao se passar o comando\
        **start**. O método abre o socket na porta 8888 e inicia os\
        trabalhadores que tratarão as conexões. Os trabalhadores são iniciados\
        instanciando objetos da classe :class:`Worker` e invocando o método\
        :meth:`Worker.start`.
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(2)
        self.socket.setblocking(0)
        self.socket.bind(('', 8888))
        self.socket.listen(5)
        for x in range(0, settings.PROCS):
            mp = Worker(self.socket, getpid())
            mp.start()
        base = SenderScore('{}/local.db'.format(settings.DBPATH))
        while True:
            base.clean()
            sleep(3600)
        base.close()

    def reports(self):
        '''
        Método que define uma ação de imprimir todos os endereços SMTP's
        contidos na base e suas informações de expiração e contagem. Utiliza o
        método :meth:`SenderScore.reports` para o resgate das informações.
        '''
        base = SenderScore('{}/local.db'.format(settings.DBPATH))
        base.reports()
        base.close()

    def checkconfig(self):
        '''
        Método para tratar os valores e a integridade das variáveis definidas
        no módulo :mod:`lib.settings`.
        '''
        try:
            assert type(settings.MULT) is types.IntType, 'MULT is not a integer'
            assert type(settings.PROCS) is types.IntType, 'PROCS is not a integer'
            assert type(settings.DBPATH) is types.StringType, 'DBPATH is not a string'
            if not os.access(settings.DBPATH, os.W_OK):
                raise(AssertionError('The path %s is not writable' % settings.DBPATH))
            assert type(settings.LOGS) is types.StringType, 'LOGS is not a string'
            if not os.access(settings.LOGS, os.W_OK):
                raise(AssertionError('The path %s is not writable' % settings.LOGS))
        except AssertionError as e:
            print str(e)
            sys.exit(1)


class SenderScore:
    '''
    Classe que desempenha todas as tarefas necessárias para o julgamento do
    SMTP remetente. Desde o resgate da reputação do SMTP via consulta DNS até
    o ingresso das informações na base utilizada para o armazenamento das
    informações.

    :param base: caminho e nome da base utilizada para tratamento do serviços.
    :type base: str
    '''

    def __init__(self, base):
        self.__con = sqlite3.connect(base)
        cursor = self.__con.cursor()
        cursor.execute(
        ''' CREATE  TABLE  IF NOT EXISTS score (
        ip text PRIMARY KEY  NOT NULL,
        count INTEGER NOT NULL  DEFAULT 0,
        expiration FLOAT NOT NULL)''')
        self.__con.commit()

    def get_reputation(self, sender):
        '''
        Método que recupera a reputação de um SMTP rementente através de uma\
        consulta DNS ao serviço SenderScore.

        :param sender: endereço ip do remetente.
        :type data: str
        :returns: reputação do SMTP ou None caso não exista um valor válido.
        '''
        sender = '.'.join(reversed(sender.split('.')))
        try:
            data = query('{}.score.senderscore.com'.format(sender),
                         'A')
            return data[0].address.split('.')[-1]
        except NXDOMAIN:
            return None

    def ch_sender(self, sender):
        '''
        Método que incrementa o valor de contagem de um servidor SMTP ou\
        reinicia sua contagem caso o tempo de expiração tenha sido completo.

        :param sender: endereço ip do remetente.
        :type data: str
        '''
        cursor = self.__con.cursor()
        cursor.execute('''SELECT * FROM score WHERE ip = ?''', (sender, ))
        resultado = cursor.fetchall()
        hora = datetime.now() + timedelta(hours=1)
        try:
            if len(resultado) == 0:
                cursor.execute('''INSERT INTO score (ip, count, expiration)
                                    VALUES (?,?,?)''',
                                    (sender, 1,
                                     strftime('%s', hora.timetuple())))
            elif resultado[0][2] < float(strftime('%s',
                                                  datetime.now().timetuple())):
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

    def get_sender(self, sender):
        '''
        Método que retorna uma tupla contendo o IP, a contagem e o tempo de\
        expiração da contagem para um servidor SMTP informado.

        :param sender: endereço ip do remetente.
        :type sender: tuple
        :returns: tupla com os valores para o SMTP remetente existentes na base
        '''
        cursor = self.__con.cursor()
        cursor.execute('''SELECT ip, count, expiration
                            FROM score where ip = ?''', (sender,))
        linhas = cursor.fetchone()
        cursor.close()
        return (linhas[0], linhas[1], linhas[2])

    def parser(self, data):
        '''
        Função que trata o conjunto de informações passadas pelo Postfix e\
        recupera informações necessárias para a classificação e resgate da\
        reputação do SMTP remetente.

        :param data: conjunto de informações passadas pelo Postfix para um\
        servidor de políticas
        :type data: str
        :returns: IP do SMTP remetente ou None caso a informação seja inválida.
        '''
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

    def clean(self):
        '''
        Método que deleta os registros de endereços de SMTP não vistos por
        mais de 6 horas.
        '''
        cursor = self.__con.cursor()
        hora = datetime.now() - timedelta(hours=6)
        cursor.execute('DELETE FROM score where expiration < ?',
                       (strftime('%s', hora.timetuple()),))
        self.__con.commit()
        cursor.close()

    def close(self):
        '''
        Método para fechar a conexão com o banco de dados.
        '''
        self.__con.close()

    def reports(self):
        '''
        Método que exibe no terminal um relatório da contagem e do tempo de
        expiração dos SMTPS relacionados.
        '''
        cursor = self.__con.cursor()
        cursor.execute('SELECT * FROM score')
        linhas = cursor.fetchall()
        if linhas:
            print '\n{}\t\t\t{}\t{}\n'.format('IP', 'Counting', 'Expire')
            for x in linhas:
                print '{}\t\t{}\t\t{}'.format(
                    x[0], x[1], datetime.fromtimestamp(x[2]))
        cursor.close()

    def action(self, data):
        '''
        Método que define uma ação baseada nas informações recebidas pelo \
        Postfix. Obtem-se em resumo os seguintes retornos:

        :param data: conjunto de informações passadas pelo Postfix para um\
        servidor de políticas
        :type data: str
        :returns:
            *action=dunno*
                aceite para as informações passadas, liberando a entrega da\
                mensagem ao seu destino.
            *action=421 sender score reputation = x, you are limited to xx \
            messages/hours in our policy, try again later*
                retorno do código de erro SMTP 421, que indica *Service not \
                available, closing transmission channel*
        '''
        sender = self.parser(data)
        if sender:
            rep = self.get_reputation(sender)
            if rep:
                self.ch_sender(sender)
                stats = self.get_sender(sender)
                if stats[1] > int(rep) * settings.MULT:
                    msg = 'action=421 sender score reputation = {0}, '\
                            'you are limited to {1} messages/hours '\
                            'in our policy, try again later\n\n'''.format(
                            rep, int(rep) * settings.MULT)
                    return msg
        return 'action=dunno\n\n'
