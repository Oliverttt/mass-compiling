########################################################################################################
# TI 官网爬虫类
# 通过设计资源-->SDK-->下载各分类下的SDK-->记录存储的位置
########################################################################################################

import time,random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import os,requests
from lxml import etree
import ssl 
ssl._create_default_https_context = ssl._create_unverified_context

class TI():
    headers={
        'Host': 'www.ti.com.cn',
        'Cookie': 'user_pref_language="zh-CN"; CONSENTMGR=ts:1611890813596%7Cconsent:true; tiSessionID=01774c2deaaa0020beeaa898bb840307300cb06b00978; _ga=GA1.3.2080125770.1611890815; _gcl_au=1.1.376677685.1611890816; ti_p_api=0; __adroll_fpc=68cb18c00503aa3ddcd6a6953084d6ac-1611890820625; _evga_a55b=01774c2deaaa0020beeaa898bb840307300cb06b00978.02E; coveo_visitorId=bd1c8627-59d3-4de7-8217-c098a7a69226; _abck=45760C4DF769CE1095C013C005968A17~0~YAAQPg1x38JIMRt4AQAAny2pIQX1xgBWiL1/k6nD4iq08iNf4bcB8u5YxIxmyuGovPHk7jJk7OkwcCHeVSiev8FM7PJyw1cZgEtWzqBHST+7cTsCqzbH6CjFcNW6HYKxMg7Sdb7fRCHrqtA0vAV5R/hc9Rj6AJNrP8FKmJp51MaJdjbcOJRE2s/5xQGy7NlSnoAXHhgPp4d1a1LxNEGdk5XO+qfrjhmQ8yoY3U8eEUBkLyE8R6BSTZORPQ1WinHwunMKg24T6ID2zYYlIm7XtMyc+WR7eTWsYGFhtknh0YzXKlo4N2w9PE6/BIeBOvYB2BXS2fJcc07bGWf5/HJrvwdQ6oZjGTfLAqhGtyRbGHxVuUotkE8JA7bJe7jppRjSuKy6ww==~-1~-1~-1; _gcl_dc=GCL.1616394819.CKSzuJOiw-8CFRKjvAodbLQE4w; _fbp=fb.2.1616998772289.511136025; da_lid=BCDD00D89A72EA1B2D5EBB9901181FEF98|0|0|0; ti_geo=country=CN|city=SHANGHAI|continent=AS|tc_ip=36.152.115.56; ti_ua=Mozilla%2f5.0%20(Windows%20NT%2010.0%3b%20Win64%3b%20x64)%20AppleWebKit%2f537.36%20(KHTML,%20like%20Gecko)%20Chrome%2f89.0.4389.72%20Safari%2f537.36; ti_bm=; _gid=GA1.3.730442489.1619359274; last-domain=www.ti.com.cn; __ar_v4=S4HGNHQ7DNGNJDUXJ2XJA3%3A20210419%3A20%7C3GLIROW56VGDFM2KUHWC42%3A20210419%3A20%7CDMF3YWNTG5HTZP5WNBOFAA%3A20210419%3A20%7CG3YHLXUICZC3XKDXYVVLO4%3A20210425%3A1%7C2XNKMR6P4VGD5MD3ZP4SQR%3A20210425%3A1%7CQFXRHQEHOJDMLHSLFIWCLO%3A20210425%3A1; tipage=%2Fdesign%20resources%2Fembedded%20software%20(sdks)%20-%20en; tipageshort=embedded%20software%20(sdks)%20-%20en; ticontent=%2Fdesign%20resources; ABTasty=uid=1w1b8d9zyzyf5yb4&fst=1611890841947&pst=1619193042255&cst=1619359273814&ns=34&pvt=206&pvis=206&th=; ti_rid=5cc457a; ga_page_cookie=embedded%20software%20(sdks)%20-%20en; ga_content_cookie=%2Fdesign%20resources; utag_main=v_id:01774c2deaaa0020beeaa898bb840307300cb06b00978$_sn:33$_ss:0$_st:1619370754854$channel:organic%3Bexp-1620270297810$ctimestamp:Tue%20Apr%2006%202021%2011%3A04%3A57%20GMT%2B0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)%3Bexp-1620270297810$free_trial:false',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36'
    }
    def __init__(self):
        self.chrome_opt=Options()
        self.chrome_opt.add_argument('--disable-gpu')
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        prefs={'download.default_directory':"E:\\daimaku\\sdk压缩包\\TI2"}
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        self.chromedriver='C:\Program Files\Google\Chrome\Application\chromedriver.exe'
        self.dir=os.getcwd()+'/sdk压缩包/TI/'
        self.sdks=[]
    
    # 获取TI官网SDK下载地址
    def index_(self):
        url='https://www.ti.com.cn/zh-cn/design-resources/embedded-development/embedded-software.html'
        req=requests.get(url=url,headers=self.headers)
        if req.status_code==200:
            content=req.content
            html=etree.HTML(content)
            types=html.xpath('//ul[@class="lined"]/li/a/@href')
            for i in types:
                res=requests.get(url=i,headers=self.headers)
                if res.status_code==200:
                    content=res.content
                    html=etree.HTML(content)
                    try:
                        tmp=html.xpath('//div[@class="enhancedColumnControl parbase"]//h3[@class="ti_box-title"]/a/@href')
                        for href in tmp:
                            if 'sdk' in href.lower() and href.lower() not in self.sdks:
                                self.sdks.append(href)
                                print('find sdk at ',href)
                    except Exception as e:
                        print(e)
                time.sleep(random.randrange(5,8))

        url='https://www.ti.com.cn/zh-cn/microcontrollers-mcus-processors/processors/arm-based-processors/design-development.html'
        req=requests.get(url=url,headers=self.headers)
        if req.status_code==200:
            content=req.content
            html=etree.HTML(content)
            types=html.xpath('//tr[@class="ti_table-row  "]/td[0]/a/@href')
            for href in types:
                if 'SDK' in href and href not in self.sdks:
                    self.sdks.append(href)
        print(self.sdks)
    
    def get_download_url(self):
        # self.index_()
        self.sdks=['https://www.ti.com.cn/tool/cn/SIMPLELINK-CC13X2-26X2-SDK']
        for url in self.sdks:
            driver=webdriver.Chrome(self.chromedriver,options=self.chrome_opt)
            driver.get(url)
            handle=driver.current_window_handle
                
            WebDriverWait(driver,30).until(lambda driver: driver.find_elements(By.XPATH,'//ti-button[@data-navtitle="Software development kit (SDK) - Download options"]'))
            btn=driver.find_element(By.XPATH,'//ti-button[@data-navtitle="Software development kit (SDK) - Download options"]')
                
            # 出现悬浮框，点击有两种情况，一种需要跳转登录进行下载，另一种可以直接下载
            btn.click()
            WebDriverWait(driver,60).until(lambda driver: driver.find_element_by_xpath('//div[@class="u-flex"]'))
            a=driver.find_element_by_xpath('//div[@class="u-flex"]/div/a')
            download=a.get_attribute('href')

            # 直接下载，网址以software-dl.ti.com开头
            if download[8]=='s':
                print('下载地址:',download)
                a.click()
                time.sleep(60)
                self.downloadlist.append(download)

            # 需要账号登录下载，网址以www.ti.cn开头
            elif download[8]=='w':
                a.click()
                time.sleep(20)
                WebDriverWait(driver,20).until(lambda driver: driver.find_element_by_id('Civil'))
                driver.find_element_by_id('Civil').click()
                driver.find_element_by_name('Certify').click()
                driver.find_element_by_name('submitsubmit').click()
                WebDriverWait(driver,20).until(lambda driver: driver.find_element_by_name('Download'))
                driver.find_element_by_name('Download').click()

                # 切换到新的下载网页
                handles=driver.window_handles
                driver.switch_to_window(handles[1])
                print(driver.title)
                time.sleep(10)
            driver.quit()
                
    # 下载SDK
    def download(self,sdk,href):
        store_path='E:\\daimaku\\sdk压缩包\\TI2'
        if not os.path.exists(store_path):
            os.makedirs(store_path)
        req=requests.get(url=href,headers=self.headers)
        if req.status_code==200:
            with open('{}\\{}.zip'.format(store_path,sdk),'wb') as f:
                f.write(req.content)
            f.close()

if __name__=='__main__':
    ti=TI()
    ti.get_download_url()