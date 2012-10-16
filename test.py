#!/usr/bin/python
#coding: utf-8

from lib.postpolicy import SenderScore
import datetime
import time

if __name__ == '__main__':
    data = '''
request=smtpd_access_policy
protocol_state=RCPT
protocol_name=ESMTP
client_address=200.202.246.144
client_name=unknown
reverse_client_name=unknown
helo_name=localhost
sender=ronaldo@lalxxxa.com
recipient=ronaldoalves@pontocompontobr.net
recipient_count=0
queue_id=
instance=e4f.50614511.ebf1.0
size=0
etrn_domain=
stress=
sasl_method=
sasl_username=
sasl_sender=
ccert_subject=
ccert_issuer=
ccert_fingerprint=
encryption_protocol=TLSv1
encryption_cipher=DHE-RSA-AES256-SHA
encryption_keysize=256

    '''
    data2 = '''
request=smtpd_access_policy
protocol_state=RCPT
protocol_name=ESMTP
client_address=189.124.16.8
client_name=unknown
reverse_client_name=unknown
helo_name=localhost
sender=ronaldo@lalxxxa.com
recipient=ronaldoalves@pontocompontobr.net
recipient_count=0
queue_id=
instance=e4f.50614511.ebf1.0
size=0
etrn_domain=
stress=
sasl_method=
sasl_username=
sasl_sender=
ccert_subject=
ccert_issuer=
ccert_fingerprint=
encryption_protocol=TLSv1
encryption_cipher=DHE-RSA-AES256-SHA
encryption_keysize=256

    '''
    base = SenderScore('local.db')
    print base.get_reputation('200.202.246.144')  # unipac
    print base.get_reputation('200.243.63.174')  # funjob
    print base.get_reputation('189.124.16.8')  # net-rosas
    for x in xrange(300):
        print base.action(data)
        print base.action(data2)
