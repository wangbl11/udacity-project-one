# -*-coding:utf-8-*-
from flask import Flask, url_for, request, abort, jsonify, send_from_directory
from flask import render_template
import sys, os, requests
import re
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import json_util
import pymysql

_host = '0.0.0.0'
UPLOAD_FOLDER = 'c:/opt/img'
ALLOWED_EXTS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
conn = MongoClient('xingboedu.com', 27017)
db = conn.udacity
map=db.map


@app.route('/invalidPostalCode',methods=['GET'])
def invalidPostcode():
    invalids=[]
    _dig = re.compile(r"10\d{4}")
    cur = map.find({"address.postcode": {"$exists": True, "$not": _dig}},{"_id":0})
    for one in cur:
        invalids.append(one)
    return jsonify({"success": True,"data":invalids}), 200

@app.route("/topusers/<int:cnt>",methods=['GET'])
def getTopContributors(cnt):
    ret=[]
    res=map.aggregate([{"$group": {"_id": "$created.user", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": cnt}])
    for one in res:
        ret.append(one)
    return jsonify({"data":ret,"success": True}), 200

@app.route("/dupElements/<int:page>/<int:size>",methods=['GET'])
def dupElements(page,size):
    ret=[]
    res=map.aggregate([{"$group":{"_id":{"name":"$name._def","type":"$type"},"count":{"$sum":1}}},{"$match":{"count":{"$gt":1}}},{"$sort":{"count":-1}},{"$skip":page*size},{"$limit":size}])
    for one in res:
        ret.append(one)
    return jsonify({"data":ret,"success": True}), 200

@app.route("/drb/one",methods=['GET','POST'])
def getChar():
    if not request.json or not 'char' in request.json:
        abort(400)
    _char=request.json['char']
    _char=map.find_one({"name":_char},{"_id":0})
    if _char:
      _char['success']=True
      return jsonify(_char),200
    else:
      return jsonify({"success":False})

@app.route('/')
def index():
    return render_template('analysis')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTS

def get_derunbang_char(char):
    print(char)
    _char=map.find_one({"name":char},{"_id":0})
    conn.close()
    if _char:
        return _char
    return None

@app.route('/uploaded')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/hanzi', methods=['POST'])
def check_hanzi():
    print(request.json)
    if not request.json or not 'char' in request.json:
        abort(400)
    _search=request.json['char']

    #search in our own server
    _char=get_derunbang_char(_search)
    result={}
    if _char:
        result['culture']=_char
        result['success_culture']=True
        result['words_culture_num']=1
    else:
        result['success_culture'] = False
        result['words_culture_num'] = 0
    #check word in jishapi
    ret = requests.get(u'https://api.jisuapi.com/zidian/word?appkey=b000c907bb308b5a&word='+_search)
    _json=ret.json()
    print(_json)
    result['words_zidian_num']=1
    result['words_result_num']=1
    result['success_zidian'] = True
    result['zidian']=_json['result']
    return jsonify(result), 200


def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()


@app.route('/hqkx/recruits', methods=['POST'])
def searchRecruit():
    print(request.json)
    conn = pymysql.connect(host="101.201.116.61", user="root", passwd="kyq2016rainbow", db='kyq', charset='utf8',cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    if not request.json or not 'search' in request.json:
        abort(400)
    page=int(request.json['page'])
    offset=page*10
    cursor.execute("select id,orgname,position_ky,position_nky,city,salary,img from recruit where orgname like '%{0}%' order by id desc limit {1},10".format(request.json['search'],offset))
    result={}
    rows=cursor.fetchall()
    print(rows)
    result['data']=rows
    result['success']=True
    cursor.close()
    conn.close()
    return jsonify(result),200

@app.route('/hqkx/recruitOne', methods=['POST'])
def oneRecruit():
    print(request.json)
    conn = pymysql.connect(host="101.201.116.61", user="root", passwd="kyq2016rainbow", db='kyq', charset='utf8',cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    if not request.json or not 'id' in request.json:
        abort(400)
    id=request.json['id']
    print(id)
    cursor.execute("select * from recruit_wechat where id={0}".format(id))
    result={}
    rows=cursor.fetchone()
    result['data']=rows
    result['success']=True
    cursor.close()
    conn.close()
    return jsonify(result),200

if __name__ == '__main__':
    app.run(port=6000, debug=True, host=_host)