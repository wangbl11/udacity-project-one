#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import re
import json
import os

from openstreetmap.langcode import getLangcode

osm_file="/".join([os.getcwd(),"../../data/beijing_china.osm"])
print(osm_file)
baddata_file=".bad"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
TRANSLATION_SUPPORT=["name"]

languages=getLangcode()
def check2Level(node,key,subkey,value):
    if not key in node:
        node[key] = {}
    else:
        if type(node[key])==str:
            _def=node[key]
            node[key]={"_def":_def}
    node[key][subkey]=value

def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way":
        node['type'] = element.tag
        node['created'] = {}

        for key in element.attrib:
            if key in CREATED:
                if element.attrib[key]:
                    node['created'][key] = element.attrib[key]
                    continue
            if key not in ['lat', 'lon']:
                node[key] = element.attrib[key]
            if key in TRANSLATION_SUPPORT:
                check2Level(node, key, "_def", element.attrib[key])

        if element.tag == "node":
            node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]

        tags = element.findall('tag')
        for tag in tags:
            _key = tag.attrib['k']
            if re.search(problemchars, _key):
                continue
            segs = _key.split(":")
            length = len(segs)
            if length == 1:
                if _key in TRANSLATION_SUPPORT:
                    check2Level(node, _key, "_def", tag.attrib['v'])
                else:
                    node[_key] = tag.attrib['v']
            elif length == 2:
                if segs[0] == "addr":
                    if not 'address' in node:
                        node['address'] = {}
                    node['address'][segs[1]] = tag.attrib['v']
                else:
                    # translation, eg: for name
                    if segs[1] in languages:
                        check2Level(node, segs[0], segs[1], tag.attrib['v'])
                    else:
                        pass
            else:
                if segs[1] == 'street':
                    continue
                else:
                    pass
                    #_newkey=check2Level(node,segs[0])
                    #node[_newkey][_key[len(segs[0])+1:]] = tag.attrib['v']

        if element.tag == "way":
            nds = element.findall('nd')
            for nd in nds:
                if "node_refs" not in node:
                    node["node_refs"] = []
                node["node_refs"].append(nd.attrib['ref'])

        #print(node)
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2))
                else:
                    fo.write(json.dumps(el))
                fo.write("\n")
    return data

if __name__=='__main__':
    data = process_map(osm_file, True)