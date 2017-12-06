#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pymongo import MongoClient
from urllib.request import urlopen;
from urllib.parse import quote;
import json
from lxml import etree
from openstreetmap.bdTranslator import getTranslation

street_sym=[re.compile("$st\.?\s+",flags=re.I),re.compile("\s+st\.?\s+",flags=re.I)]
zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')

def cleanRoadTranslation():
   pass

conn = MongoClient('xingboedu.com', 27017)
db = conn.udacity
map=db.mapp

def addAdcode():
  url="http://restapi.amap.com/v3/geocode/regeo?output=json&location={0},{1}&key=5207eb75880ec13ec118ef705b0dfea6"

  cnt=0
  cur=map.find({"pos":{"$exists":True}},no_cursor_timeout = True)
  for one in cur:
     _url=url.format(one['pos'][1],one['pos'][0])
     print(cnt)
     cnt = cnt + 1
     rawtext = urlopen(_url, timeout=150).read()
     jsonStr = json.loads(rawtext.decode('utf8'))
     if jsonStr['status']=='0':
         print(jsonStr['info'])
         return
     if 'address' in jsonStr and 'adcode' in jsonStr['address'] and len(jsonStr['address']['adcode'])>0:
	     continue
     print(jsonStr)
     _adcode=''
     if 'adcode' in jsonStr:
         _adcode=jsonStr['adcode']
     if  'regeocode' in jsonStr and  'addressComponent' in jsonStr['regeocode']:
         _address=jsonStr['regeocode']['addressComponent']
         #print(_address)
         if 'adcode' in _address:
            _adcode=_address['adcode']
     if len(_adcode)>0:
       print(_adcode)
       _one = map.update({"_id": one['_id']}, {"$set": {"address.adcode":_adcode}}, upsert=True)
       cnt=cnt+1
  cur.close()

def fetchPostalCode():
   _dig=re.compile(r"10\d{4}")
   cur=db.map.find({"address.postcode":{"$exists":True,"$not":_dig}})
   url="http://www.webxml.com.cn/WebServices/ChinaZipSearchWebService.asmx/getZipCodeByAddress?theProvinceName="+quote("北京")+"&theCityName=&theAddress={0}&userID="
   for one in cur:
       if 'street' in one['address']:
           rawtext = urlopen(url.format(quote(one['address']['street'])), timeout=150).read()
           root=etree.fromstring(rawtext)
           found=root.xpath("//ZipInfo/ZIP")
           for f in found:
               db.mapp.update({"_id":one["_id"]},{"$set":{"address.postcode":f.text}})
               print(f)
               break

def containChinese(val):
    word = val.decode()
    global zh_pattern
    match = zh_pattern.search(word)
    return match

def containPinyin(val):
  if re.search("[āáǎàōóǒòêēéěèīíǐìūúǔùǖǘǚǜüńňǹɑɡ]+",val):
      return True
  return False

def translateEnglishName():
    _srckey={}
    _pattern=re.compile(r".*road|expressway|street.*",re.I)
    cur = db.map.find({"name._def": _pattern},no_cursor_timeout = True)
    for one in cur:
        _orig=one['name']["_def"]
        #whether contains pinyin
        if containPinyin(_orig):
            _one=_orig[0:_orig.find(" ")]
            db.mapp.update({"id": one["id"]}, {"$set": {"name._old": _orig, "name._def": _one}})
            continue
        if _orig in _srckey:
            db.mapp.update({"id": one["id"]}, {"$set": {"name._old": _orig, "name._def": _srckey[_orig]}})
        else:
          ret=getTranslation(_orig)
          if ret:
            print(ret)
            _srckey[_orig]=ret
            db.translation.insert({"k":_orig,"v":ret})
            print(one["id"])
            db.mapp.update({"id":one["id"]},{"$set":{"name._old":_orig,"name._def":ret}})
    cur.close()

def cleanReligion():
    _dict = {
        "庙": "buddhist",
        "清真": "muslim",
        "寺": "buddhist",
        "christian": "christian",
        "church": "christian",
        "缸瓦市堂":"christian"
    }
    _dict1={
        "政府":"",
        "图书馆":"library",
        "大学": "college"
    }
    cur = db.map.find(
        {"$and": [{"amenity": {"$exists": True}}, {"amenity": "place_of_worship"}, {"religion": {"$exists": False}}]},
        no_cursor_timeout=True)
    for one in cur:
        if 'name' not in one:
            continue
        n = one['name']
        print(n)
        _names = []
        for lang in ["_def", "en", "zh"]:
            if lang in n:
                _names.append(n[lang])
        found = False
        for key in _dict:
            for _name in _names:
                if re.search(key, _name, re.I):
                    print(_name)
                    db.mapp.update({"id": one["id"]}, {"$set": {"amenity": _dict[key]}})
                    found = False
                    break
            if found:
                break
        if found:
            continue

        #not wworship
        for key in _dict1:
          for _name in _names:
               if re.search(key, _name, re.I):
                    print(_name)
                    db.mapp.update({"id": one["id"]}, {"$set": {"religion": _dict1[key]}})
                    found = False
                    break
          if found:
              break

    cur.close()

def cleanCuisine():
    _dict={
         "india":"india",
         "印度":"india",
         "酒楼":"chinese",
         "食堂":"cihnese",
         "火锅":"chinese",
         "大饼":"chinese",
         "香锅":"chinese",
         "包子":"chinese",
         "饺子":"chinese",
         "烤鸭":"chinese",
         "拉面":"chinese",
         "牛肉面": "chinese",
         "小吃": "chinese",
         "爆肚":"chinese",
         "串吧":"chinese",
         "饭庄":"chinese",
         "japanese":"japanese",
         "寿司": "japanese",
    }
    cur = db.map.find({"$and":[{"amenity":{"$exists":True}},{"amenity":"restaurant"},{"cuisine":{"$exists":False}}]},no_cursor_timeout = True)
    for one in cur:
        if 'name' not in one:
            continue
        n=one['name']
        print(n)
        _names=[]
        for lang in ["_def","en","zh"]:
          if lang in n:
            _names.append(n[lang])

        for key in _dict:
            found=False
            for _name in _names:
              if re.search(key,_name,re.I):
                print(_name)
                db.mapp.update({"id": one["id"]}, {"$set": {"cuisine": _dict[key]}})
                found=False
                break
            if found:
                break
    cur.close()

#work on mapp (not map) collection
def cleanSource():
    db.mapp.update_many(
        {"source": {"$exists": True, "$in": [re.compile(r"^yahoo$", re.I), re.compile("^yahoo[\s;!]", re.I)]}},
        {"$set": {"source": 'Yahoo'}})
    db.mapp.update_many(
        {"source": {"$exists": True, "$in": [re.compile(r"^bing$", re.I), re.compile("^bing[\s,.\-;_]", re.I),re.compile("\sbing$",re.I)]}},
        {"$set": {"source": 'Bing'}})
    db.mapp.update_many(
        {"source": {"$exists": True, "$in": [re.compile(r"^gps", re.I)]}},
        {"$set": {"source": 'GPS'}})

def cleanDuplication():
    pass

if __name__=='__main__':
    cleanDuplication()

