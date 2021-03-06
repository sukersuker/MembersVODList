#!/usr/bin/env python3

import argparse
import arrow
import base64
import functools
import json
import logging
import multiprocessing
import os
import pathlib
import requests

def json_data():
    return json.loads(open('member_id.json','r').read())

def process(data,member):
    member_id=json_data()[member]
    file='%s-%s.json'%('%06d'%member_id,member)
    output_normal=pathlib.Path('normal')/file
    output_quiet=pathlib.Path('quiet')/file
    info=[dict for dict in data if dict['memberId']==member_id]
    f=open(output_normal,'w')
    f.write(json.dumps(info,indent=2,ensure_ascii=False))
    f.write('\n')
    f.close()
    logging.info('[normal] %d objects written in %s'%(len(info),output_normal))
    urls={}
    for dict in info:
        urls[dict['startTime']['datetime']]=dict['streamPath']
    f=open(output_quiet,'w')
    f.write(json.dumps(urls,indent=2,ensure_ascii=False))
    f.write('\n')
    f.close()
    logging.info('[quiet] %d objects written in %s'%(len(urls),output_quiet))

def main():
    parser=argparse.ArgumentParser()
    add=parser.add_argument
    add('-j','--jobs',type=int,default=os.cpu_count())
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(levelname)s: %(message)s')
    pathlib.Path('normal').mkdir(exist_ok=True)
    pathlib.Path('quiet').mkdir(exist_ok=True)
    resp=requests.post('https://plive.48.cn/livesystem/api/live/v1/memberLivePage',headers={'Content-Type':'application/json','version':'5.3.0','os':'android'},json={'lastTime':0,'groupId':0,'memberId':0,'limit':30000}).json()
    data=[]
    for dict in resp['content']['reviewList']:
        info={}
        info['title']=dict['title']
        sub_title={}
        sub_title['raw']=dict['subTitle']
        sub_title['base64']=bytes.decode(base64.b64encode(str.encode(dict['subTitle'])))
        info['subTitle']=sub_title
        info['picPath']=['https://source.48.cn%s'%obj for obj in dict['picPath'].split(',')]
        start_time={}
        start_time['timestamp']=dict['startTime']
        start_time['datetime']=arrow.get(dict['startTime']/1000).to('Asia/Shanghai').strftime('%Y-%m-%dT%H:%M:%SZ')
        info['startTime']=start_time
        info['memberId']=dict['memberId']
        info['liveType']=dict['liveType']
        info['streamPath']=dict['streamPath'].replace('http://','https://')
        data.append(info)
    work=functools.partial(process,data)
    pool=multiprocessing.Pool(args.jobs)
    pool.map(work,[key for key in json_data()])
    pool.close()
    pool.join()

if __name__=='__main__':
    main()
