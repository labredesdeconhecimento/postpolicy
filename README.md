 PostPolicy
=================
**Autor: Ronaldo Alves Marques Júnior**

Sinopse
-------

> Este projeto, trabalho final do curso *Python para Administradores de Redes Linux*,
busca implementar um servidor de políticas de acesso para o servidor Postfix. Através
de informações de reputação do endereço IP de um servidor SMTP remetente obtidas por meio 
de consultas a partir do serviço **SenderScore**, que variam com valores entre 0 e 100, 
são definidos o número de emails que poderão ser entregues em um período de 1 hora. A contagem
é definida pelo parâmetro de configuração **MULT**, que multiplica o valor da reputação definindo assim
a contagem máxima.
>Expirado este tempo a contagem é retomada em 0, criando-se assim um meio de evitar o 
desperdício de recursos caso sofra-se excessos a partir de um servidor SMTP comprometido.

Dependência
-----------
> A aplicação depende da linguagem Python com suporte a base de dados SQLite e do módulo de terceiros
dnspython.

Uso
----
> Assim como daemon, o arquivo main.py aceita comandos como start, stop, status e reports. O reports,
não comum como os demais, exibe um relatório com informações dos SMTP's contidos na base.
>
`python main.py start` 

>`python main.py stop` 

>`python main.py status` 

>`python main.py reports` 
