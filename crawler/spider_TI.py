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
        'Cookie': 'yourcookie',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36'
    }
    def __init__(self):
        self.chrome_opt=Options()
        self.chrome_opt.add_argument('--disable-gpu')
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        prefs={'download.default_directory':"yourstoragepath"}
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        self.chromedriver='C:\Program Files\Google\Chrome\Application\chromedriver.exe'
        self.dir=os.getcwd()+'storagepath'
        self.sdks=[]
    
    # grab download url
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
        self.index_()
        for url in self.sdks:
            driver=webdriver.Chrome(self.chromedriver,options=self.chrome_opt)
            driver.get(url)
            handle=driver.current_window_handle  
            WebDriverWait(driver,30).until(lambda driver: driver.find_elements(By.XPATH,'//ti-button[@data-navtitle="Software development kit (SDK) - Download options"]'))
            btn=driver.find_element(By.XPATH,'//ti-button[@data-navtitle="Software development kit (SDK) - Download options"]')
            btn.click()
            WebDriverWait(driver,60).until(lambda driver: driver.find_element_by_xpath('//div[@class="u-flex"]'))
            a=driver.find_element_by_xpath('//div[@class="u-flex"]/div/a')
            download=a.get_attribute('href')

            if download[8]=='s':
                print('download from:',download)
                a.click()
                time.sleep(60)
                self.downloadlist.append(download)
            elif download[8]=='w':
                a.click()
                time.sleep(20)
                WebDriverWait(driver,20).until(lambda driver: driver.find_element_by_id('Civil'))
                driver.find_element_by_id('Civil').click()
                driver.find_element_by_name('Certify').click()
                driver.find_element_by_name('submitsubmit').click()
                WebDriverWait(driver,20).until(lambda driver: driver.find_element_by_name('Download'))
                driver.find_element_by_name('Download').click()
                handles=driver.window_handles
                driver.switch_to_window(handles[1])
                print(driver.title)
                time.sleep(10)
            driver.quit()
                
    # download SDK
    def download(self,sdk,href):
        store_path='yourstoragepath'
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
