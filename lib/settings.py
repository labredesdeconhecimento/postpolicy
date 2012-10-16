#!/usr/bin/env python
#coding:utf-8
'''
.. moduleauthor:: Ronaldo A. Marques Jr. <ralvesmj@gmail.com>
:Plataforma: \*nix
:Sinopse: Módulo que possuí parâmetros de configuração para uso do servidor de\
políticas.

Parâmetros
----------

**PROCS**
    número de threads que será utilizadas para receber conexões \
TCP/IP no servidor de políticas.

**MULT**
    lembrando que as reputações obtidas no SenderScore variam entre\
1 e 100, o valor deste parâmetro faz com que o valor obtido seja multiplicado.\
Caso seja obtido um valor de reputação igual a 88 e o valor de MULT igual a 3,\
o limite de envios para o prazo de uma hora estaria restrito a no máximo 264.

**DBPATH**
    indica o caminho que será utilizado para armazenamento da base SQLite \
utilizada para guardar as informações obtidas.

**LOGS**
    indica o caminho que será utilizado para armazenar os arquivos de log.
'''
from os import getcwd

MULT = 3
PROCS = 4
DBPATH = getcwd()
LOGS = getcwd() + '/logs'
