#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import request
from bs4 import BeautifulSoup
def getLangcode():
    codes=[]
    url="http://www.lingoes.net/en/translator/langcode.htm"
    data = request.urlopen(url).read()
    data=data.decode('utf-8')
    soup = BeautifulSoup(data, 'html5lib')
    idx=0
    for link in soup.find_all('td'):
       if idx>1 and idx%2==0:
           codes.append(link.string)
       idx=idx+1
    return codes

if __name__=='__main__':
    data=getLangcode()
    print(data)