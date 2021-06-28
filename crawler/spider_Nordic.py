########################################################################################################
# Nordic 官网爬虫类
# https://www.nordicsemi.com/Products是该网站的产品页
# 通过匹配关键词 class="see-all overlay azur skew-percent" 得到静态加载的产品链接，
# 点击“更多”按钮后，匹配关键词 "read_fullstory" 得到动态加载的产品链接
# 进入产品详情页面获取SDK和协议栈下载地址，需要动态点击
# 其中nRF5系列提供了SDK，nRF9只有固件hex文件
# 爬取方案如下：
# 1. 设定chrome的默认下载地址
# 2. 进入产品详情页面，获取芯片地址
# 3. 自动进入芯片详情页面
# 4. 自动点击“Download”按钮，获取匹配版本的SDK
########################################################################################################

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import requests,time,os,zipfile

class Nordic():
    headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36'
    }
    def __init__(self):
        self.chrome_opt=Options()
        self.chrome_opt.add_argument('--disable-gpu')
        prefs={'download.default_directory':"E:\\daimaku\\sdk压缩包\\Nordic2"}
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        self.chrome_opt.add_experimental_option('prefs',prefs)
        self.chromedriver=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'
        self.data=list()
        self.hrefs=list()

    # 爬取产品页面所有的产品链接
    def get_chip_url(self):
        url='https://www.nordicsemi.com/Products'
        driver=webdriver.Chrome(executable_path=self.chromedriver,options=self.chrome_opt)
        driver.get(url)
        WebDriverWait(driver,120).until(lambda driver:driver.find_element_by_xpath('//span[@class="icon-plus"]'))
        driver.find_element_by_xpath('//span[@class="icon-plus"]').click()
        urls=driver.find_elements_by_xpath('//div[@class="see-all overlay azur skew-percent"]/a')
        for i in range(2,len(urls)):
            href=urls[i].get_attribute('href')
            self.hrefs.append(href)
        extras=driver.find_elements_by_xpath('//a[@class="read_fullstory"]')
        for i in extras:
            href=i.get_attribute('href')
            self.hrefs.append(href)
        for i in self.hrefs:
            print(i)
        driver.quit()
    
    # 进入所有产品详情界面并下载源码
    def download(self):
        self.get_chip_url()
        if not os.path.exists("E:\\daimaku\\sdk压缩包\\Nordic2"):
            os.makedirs("E:\\daimaku\\sdk压缩包\\Nordic2")
        hou=['/Download#infotabs','/Downloads#infotabs','/Compatible-downloads#infotabs']
        driver=webdriver.Chrome(executable_path=self.chromedriver,options=self.chrome_opt)
        for i in self.hrefs:
            chip=i.split('/')[-1]
            for j in hou:
                url=i+j
                req=requests.get(url=url,headers=self.headers)
                if req.status_code==200:
                    break
            driver.get(url)
            driver.execute_script("window.scrollBy(0,1400);")
            try:
                WebDriverWait(driver,60).until(lambda driver: driver.find_element_by_id('sc_DownloadFiles_{}'.format(chip)))
                driver.find_element_by_id('sc_DownloadFiles_{}'.format(chip)).click()
                time.sleep(20)
            except Exception as e:
                print(e)
        driver.quit()
    
    def unzip(self):
        zips=os.listdir('E:\\daimaku\\sdk压缩包\\Nordic')
        print(zips)
        for zip in zips:
            print(zipfile.is_zipfile(zip))
            if zipfile.is_zipfile(zip):
                if not os.path.exists('E:\\物联网固件代码库\\src\\Nordic'):
                    os.makedirs('E:\\物联网固件代码库\\src\\Nordic')
                zipfile.extractall('E:\\物联网固件代码库\\src\\Nordic')

if __name__=='__main__':
    nordic=Nordic()
    nordic.download()
    # nordic.unzip()