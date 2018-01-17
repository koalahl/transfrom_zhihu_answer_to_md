#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by shimeng on 17-6-5
import os
import re
import sys
import json
import urllib
import urlparse
import requests
import html2text
from parse_content import parse

"""
just for study and fun
Talk is cheap
show me your code
"""


class ZhiHu(object):
    def __init__(self):
        pass

    def request(self, url, retry_times=10):
        host = urlparse.urlparse(url).netloc
        header = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
            'Host': host
        }
        content = None
        times = 0
        while retry_times > 0:
            times += 1
            print 'request %s, times: %d' % (url, times)
            try:

                content = requests.get(url, headers=header, timeout=10).content
            except Exception, e:
                print e
                retry_times -= 1
            else:
                return content

    def get_all_answer_content(self, question_id, flag=2):
        first_url_format = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data[*].content,voteup_count,created_time&offset=0&limit=20&sort_by=default'
        first_url = first_url_format.format(question_id)
        response = self.request(first_url)
        if response:
            contents = json.loads(response)
            print contents.get('paging').get('is_end')
            if contents.get('paging').get('is_end'):
                for content in contents.get('data'):
                    self.parse_content(content, flag)
            else:
                while not contents.get('paging').get('is_end'):
                    for content in contents.get('data'):
                        self.parse_content(content, flag)
                    next_page_url = contents.get('paging').get('next').replace('http', 'https')
                    contents = json.loads(self.request(next_page_url))

        else:
            raise ValueError('failed 10 times, quit......')

    def get_single_answer_content(self, answer_url, flag=1):
        all_content = {}
        question_id, answer_id = re.findall('https://www.zhihu.com/question/(\d+)/answer/(\d+)', answer_url)[0]

        html_content = self.request(answer_url)
        if html_content:
            all_content['main_content'] = html_content
        else:
            raise ValueError('failed 10 times, quit......')

        ajax_answer_url = 'https://www.zhihu.com/api/v4/answers/{}'.format(answer_id)
        ajax_content = self.request(ajax_answer_url)
        if ajax_content:
            all_content['ajax_content'] = json.loads(ajax_content)
        else:
            raise ValueError('failed 10 times, quit......')

        self.parse_content(all_content, flag, )

    def parse_content(self, content, flag=None):
        data = parse(content, flag)
        self.transform_to_markdown(data)

    def transform_to_markdown(self, data):
        content = data['content']
        author_name = data['author_name'].encode('utf-8')
        answer_id = data['answer_id']
        question_id = data['question_id']
        question_title = data['question_title'].encode('utf-8')

        vote_up_count = data['vote_up_count']
        create_time = data['create_time']

        file_name = unicode('%s--%s的回答[%d].md' % (question_title, author_name, answer_id), 'utf-8')

        folder_name = unicode('%s' % ('Questions/' + question_title), 'utf-8')

        if not os.path.exists(os.path.join(os.getcwd(), folder_name.encode('utf-8'))):
            os.mkdir(folder_name)

        f = open(os.path.join(os.getcwd(), folder_name.encode('utf-8'), file_name.encode('utf-8','ignore')),"wt")

        f.write("-" * 40 + "\n")
        origin_url = 'https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answer_id)
        f.write("## 本答案原始链接: " + origin_url + "\n")
        f.write("### question_title: " + question_title + "\n")
        f.write("### Author_Name: " + author_name + "\n")
        f.write("### Answer_ID: %d" % answer_id + "\n")
        f.write("### Question_ID %d: " % question_id + "\n")
        f.write("### VoteCount: %s" % vote_up_count + "\n")
        f.write("### Create_Time: " + create_time + "\n")
        f.write("-" * 40 + "\n")

        text = html2text.html2text(content.decode('utf-8')).encode("utf-8")
        # 标题
        r = re.findall(r'\*\*(.*?)\*\*', text, re.S)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'_(.*)_', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())
        text = text.replace('_ _', '')
        text = text.replace('_b.', '_r.')
        # 图片
        r = re.findall(r'!\[\]\((?:.*?)\)', text)
        for i in r:

            text = text.replace(i, i + "\n\n")

            cwd = os.getcwd()
            folder_name = '%s/images/%s' % (cwd,question_title)

            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            img_url = re.findall('\((.*)\)', i)[0]
            save_name =  author_name + '_' + img_url.split('/')[-1]
            pic_file_name = '%s/%s' % (folder_name, save_name)
            try:
                
                if not os.path.exists(pic_file_name):
                    print '正在下载图片：' + save_name
                    urllib.urlretrieve(img_url, pic_file_name)
                else:
                    pass#print '图片已存在！'
            except Exception, e:
                print e
            else:
                text = text.replace(img_url, pic_file_name)

        f.write(text)

        f.close()


if __name__ == '__main__':
    zhihu = ZhiHu()
    # url = 'https://www.zhihu.com/question/27621722/answer/105331078'
    # zhihu.get_single_answer_content(url)

    # 29470294
    # 24400664 长得好看是怎样一种体验？
    # '20215578' 国内有哪些工作环境很赞的互联网公司？
    inputCommand = sys.argv[1]#从命令行输入的id sys.argv[0]是自身脚本名zhihu.py

    #find函数返回的是查找到的子串的lowest index，所以这里刚好是0 ，要用not(⊙﹏⊙)
    if not inputCommand.find('https'):
        answerUrl = inputCommand
        print '爬取单个回答：' + answerUrl
        zhihu.get_single_answer_content(answerUrl)
    else:
        questionId = inputCommand
        print '爬取某个问题的所有回答：'+ questionId
        zhihu.get_all_answer_content(questionId)
