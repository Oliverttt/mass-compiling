from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
from multiprocessing import Process

class NXP():
    def __init__(self):
        self.chrome_opt=Options()
        self.chrome_opt.add_argument('--disable-gpu')
        self.chrome_opt.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        prefs={'download.default_directory':"yourstoragepath"}
        self.chrome_opt.add_experimental_option('prefs',prefs)
        self.chromedriver=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'
        self.data=list()
        self.downloadlist=list()
        self.cookies=''

     # login
    def get_nodeid(self):
        url='https://mcuxpresso.nxp.com/en/select'
        driver=webdriver.Chrome(executable_path=self.chromedriver,options=self.chrome_opt)
        driver.get(url)
        WebDriverWait(driver,30).until(lambda driver: driver.find_element_by_id('username'))
        driver.find_element_by_id('username').clear()
        driver.find_element_by_id('username').send_keys('yourusername')
        driver.find_element_by_id('password').clear()
        driver.find_element_by_id('password').send_keys('yourpassword')
        driver.find_element_by_name('loginbutton').click()
        WebDriverWait(driver,100).until(lambda driver: driver.find_elements_by_xpath('//li[@data-nodeid="0"]'))
        driver.find_element_by_xpath('//li[@data-nodeid="0"]').click()
        i=1
        driver.find_element_by_xpath('//li[@data-nodeid="{}"]'.format(i)).click()
        driver.implicitly_wait(1)
        while i<119:
            next=driver.find_element_by_xpath('//li[@data-nodeid="{}"]/following-sibling::li'.format(i))
            if next.get_attribute('data-selectable')=='false':
                next.click()
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                driver.execute_script('document.getElementById("select-tree").scrollTop=1000')
            elif next.get_attribute('data-selectable')=='true':
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                tmp=next.get_attribute('data-nodeid')+'/'+next.get_attribute('innerText')
                self.data.append(tmp.split('/')[0])
            i+=1
        driver.quit()
        with open('NXP_board_id.txt','w') as f:
            for line in self.data:
                f.write(line+'\n')
        f.close()

    def check_id(self,board):
        with open('NXP_board_id.txt','r') as f:
            for line in f:
                if board in line:
                    id=int(line.split('/')[0])
        f.close()
        return id
        
    # make sdks
    def create(self,nodeid):
        url='https://mcuxpresso.nxp.com/en/select'
        driver=webdriver.Chrome(executable_path=self.chromedriver,options=self.chrome_opt)
        driver.get(url)
        WebDriverWait(driver,60).until(lambda driver: driver.find_element_by_id('username'))
        driver.find_element_by_id('username').clear()
        driver.find_element_by_id('username').send_keys('yourusername')
        driver.find_element_by_id('password').clear()
        driver.find_element_by_id('password').send_keys('yourpassword')
        driver.find_element_by_name('loginbutton').click()
        WebDriverWait(driver,180).until(lambda driver: driver.find_elements_by_xpath('//li[@data-nodeid="0"]'))
        driver.find_element_by_xpath('//li[@data-nodeid="0"]').click()
        i=1
        driver.find_element_by_xpath('//li[@data-nodeid="{}"]'.format(i)).click()
        driver.implicitly_wait(1)
        next=0
        while i<int(nodeid):
            next=driver.find_element_by_xpath('//li[@data-nodeid="{}"]/following-sibling::li'.format(i))
            if next.get_attribute('data-selectable')=='false':
                next.click()
                driver.execute_script("window.scrollTo(0, 90);")
                driver.execute_script('document.getElementById("select-tree").scrollBy(0,30)')
            elif next.get_attribute('data-selectable')=='true':
                driver.execute_script("window.scrollTo(0, 90);")
                driver.execute_script('document.getElementById("select-tree").scrollBy(0,30)')
            i+=1  
        print('start making SDK...id{}...name{}'.format(next.get_attribute('data-nodeid'),next.get_attribute('innerText')))
        next.click()
        WebDriverWait(driver,30).until(lambda driver: driver.find_element_by_id('select-button'))
        driver.find_element_by_id('select-button').click()

        WebDriverWait(driver,30).until(lambda driver: driver.find_element_by_id('select-all'))
        driver.find_element_by_id('select-all').click()
        # WebDriverWait(driver,30).until(lambda driver: driver.find_element_by_xpath('//span[@class="MuiButton-label"]'))
        # driver.find_element_by_xpath('//span[@class="MuiButton-label"]').click()
        driver.execute_script("window.scrollBy(0,600);")
        driver.find_element_by_id('btn_rebuild').click()
        time.sleep(10)
        driver.quit()
   
    def run(self,start,end):
        for i in range(start,end):
            self.create(self.data[i])
            time.sleep(1)

    # download sdk
    def download(self):
        url='https://mcuxpresso.nxp.com/en/dashboard'
        driver=webdriver.Chrome(executable_path=self.chromedriver,options=self.chrome_opt)
        driver.get(url)
        WebDriverWait(driver,180).until(lambda driver: driver.find_element_by_id('username'))
        driver.find_element_by_id('username').clear()
        driver.find_element_by_id('username').send_keys('yourusername')
        driver.find_element_by_id('password').clear()
        driver.find_element_by_id('password').send_keys('yourpassword')
        driver.find_element_by_name('loginbutton').click()
        # Show ALL
        WebDriverWait(driver,240).until(lambda driver: driver.find_element_by_id('dashboard-sdk-show'))
        driver.find_element_by_id('dashboard-sdk-show').click()
        time.sleep(90)
        hrefs=driver.find_elements_by_xpath('//a[@class="dash-download-action"]')
        for i in hrefs:
            try:
                driver.execute_script("arguments[0].scrollIntoView();",i)
                driver.execute_script("window.scrollBy(0,-80)")
                i.click()
                time.sleep(5)
                driver.find_element_by_xpath('//div[@id="dash-download-modal"]//a[@id="download-archive-link"]').click()
                time.sleep(5)
                driver.find_element_by_id('agree-license').click()
                time.sleep(5)
                driver.find_element_by_xpath('//button[@aria-label="Close"]').click()
                time.sleep(5)
            except Exception as e:
                print(e)
        time.sleep(20)


if __name__=='__main__':
    nxp=NXP()
    nxp.get_nodeid()
    threads=list()
    try:
        for i in range(1):
            th_i=Process(target=nxp.run,args=(i*1,(i+1)*1))
            th_i.start()
            threads.append(th_i)
        for thread in threads:
            thread.join()
    except Exception as e:
        print(e)

    nxp.download() 
