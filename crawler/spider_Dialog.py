########################################################################################################
# Dialog 官网sdk爬虫类
# 爬取方案如下：
# 1. 搜索关键词sdk
# 2. 选择“Resources”类型的结果
# 3. 通过“sdk”和“.zip”匹配sdk下载链接
# 4. 构造携带cookies的请求访问sdk下载链接
# 5. 按照sdk名称保存响应报文
########################################################################################################

import requests
from lxml import etree
import time,random
import os

class Dialog():
    headers={
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
        'cookie': 'yourcookie'
    }

    def __init__(self):
        self.cookies=''
        self.sdk=[]
        self.name=[]

    def login(self):
        headers={
            'Host': 'www.dialog-semiconductor.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://www.dialog-semiconductor.com/user/login',
        }
        url='https://www.dialog-semiconductor.com/user/login'

        data={
            'name':'yourusername',
            'pass':'yourpassword',
            'form_id':'user_login_form',
            'form_build_id': 'form-ztJQd22kYJv2c30yCsXIKly4yJ4O9o4yhPnwWG28oPk',
            'op':'Log in',
        }
        res=requests.post(url=url,data=data,headers=headers)
        print(res.status_code)
        cookies=requests.utils.dict_from_cookiejar(res.cookies)
        self.cookies=cookies

    def get_sdk_url(self):
        for num in range(5,7):
            url='https://www.dialog-semiconductor.com/search?keywords=sdk&f%5B0%5D=search_category%3AResources&page='+str(num)
            try:
                req=requests.get(url=url,headers=self.headers,timeout=120)
                print('page:{},status_code:{}'.format(num,req.status_code))
                if req.status_code==200:
                    content=req.content
                    html=etree.HTML(content)
                    href=html.xpath('//div[@class="views-row"]/a/@href')
                    text=html.xpath('//div[@class="views-row"]/a/text()')
                    for i in range(len(href)):
                        if '.zip' in href[i] and 'sdk' in href[i].lower():
                            self.sdk.append(href[i])
                            self.name.append(text[i])
                            print('find sdk [{}] at [{}]'.format(text[i],href[i]))
                time.sleep(random.randrange(5,10))
            except Exception as e:
                print(e)
    
    def download_sdk(self):
         # 创建存储目录
        if not os.path.exists('yourstoragepath'):
            os.makedirs('yourstoragepath')
        for i in range(len(self.sdk)):
            url=self.sdk[i]
            name=self.name[i].replace('%20',' ').replace('.','_').replace('/','_')
            req=requests.get(url=url,headers=self.headers)
            if req.status_code==200:
                print('download [{}]...'.format(name))
                with open('yourstoragepath'+name+'.zip','wb') as f:
                    f.write(req.content)
                f.close()
                print('finish [{}] !'.format(name))
            else:
                print('error download [{}]'.format(name))
            time.sleep(random.randrange(1,5))

if __name__=='__main__':
    dialog=Dialog()
    dialog.get_sdk_url()
    dialog.download_sdk()
