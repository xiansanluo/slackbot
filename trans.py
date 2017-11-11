#!/usr/bin/python
#coding:utf-8
import os
import requests
import base64
import hmac
import hashlib
import random
import time
import operator
from luis_sdk import LUISClient
from slackclient import SlackClient
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


NONCE = int(random.random()*1000)
SECRETID = "xxx"
secretKey = 'xxx'
REGION = "gz"
TIMESTAMP = int(time.time())
def get_trans(command):
    sig = {
        'Action': 'TextTranslate',
        'Nonce': NONCE,
        'Region': REGION,
        'SecretId': SECRETID,
        'Timestamp': TIMESTAMP,
        'sourceText': command,
        'source': "zh",
        'target': 'en'
    }
    sigl = sorted(sig.iteritems(), key=operator.itemgetter(0))
    for i, val in enumerate(sigl):
        if i == 0:
            sigstr = val[0] + '=' + str(val[1])
        else:
            sigstr = sigstr + '&' + val[0] + '=' + str(val[1])
    sigstr = "GETtmt.api.qcloud.com/v2/index.php?" + sigstr
    signature = (base64.b64encode(hmac.new(secretKey, sigstr, hashlib.sha1).digest()))
    payload = {
        'Action': 'TextTranslate',
        'Nonce': NONCE,
        'Region': REGION,
        'SecretId': SECRETID,
        'Timestamp': TIMESTAMP,
        'Signature': signature,
        'sourceText': command,
        'source': "zh",
        'target': 'en'
    }
    r = requests.get('https://tmt.api.qcloud.com/v2/index.php', params=payload)
    return r.json()['targetText']

if __name__ == '__main__':
    print get_trans('你好，我是joy,你来自哪里？')
