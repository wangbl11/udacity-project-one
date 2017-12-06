# /usr/bin/env python
# coding=utf8
import hashlib
from urllib.request import urlopen;
from urllib.parse import quote;
import random
import json

#the service can only be run on defined machine
appid = '20171128000100253'
secretKey = 'A96yqP5VGX_MBzAcg5BZ'

httpClient = None
myurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
q = 'apple'
fromLang = 'en'
toLang = 'zh'
salt = random.randint(32768, 65536)
m1 = hashlib.md5()
myurl = myurl + '?appid=' + appid + '&q={0}&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign={1}'

def getTranslation(q):
    sign = appid + q + str(salt) + secretKey
    m1 = hashlib.md5()
    m1.update(sign.encode("utf-8"))
    sign = m1.hexdigest()
    _url=myurl.format(quote(q),sign)
    rawtext = urlopen(_url, timeout=150).read()
    jsonStr = json.loads(rawtext.decode('utf8'))
    print(jsonStr)
    if 'error_code' in jsonStr:
        return None
    else:
        _one=jsonStr['trans_result'][0]
        return _one['dst']

if __name__=='__main__':
    print(getTranslation('Wangfujing Snack street'))
