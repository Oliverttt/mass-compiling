# 通用编译脚本
import os
from collections import defaultdict
import pandas as pd
import re
import subprocess
import time
from multiprocessing import Process
from db import database

# 自动化编译类
class Compiler():
    def __init__(self):
        self.keil_path=list()
        self.iar_path=list()
        self.ccs_path=list()
        self.failed_list=list()
        self.work_project=list()
        self.work_path=list()
    
    #######################################
    # 临时存储例程信息
    #######################################
    def save_info(self,x,y):
        data=defaultdict(list)
        for k,v in x:
            data[k].append(v)
        text=pd.DataFrame(data)
        text.to_csv('{}.csv'.format(y),encoding='utf-8-sig')

    #######################################
    # 读取例程信息
    #######################################
    def read_info(self,compiler):
        f=open('{}.csv'.format(compiler),encoding='utf_8_sig')
        data=pd.read_csv(f,engine='python')
        return data
        
    #######################################
    # 例程信息提取
    #######################################
    def get_all_samples(self,path):
        # 遍历SDK目录
        for root,dirs,files in os.walk(path,topdown=True):
            # Keil 项目
            if 'Keil_5'  in dirs :
                files=os.listdir(root+'\\Keil_5\\')
                project=[x for x in files if x.endswith('.uvprojx')]
                if len(project) is not 0:
                    self.keil_path.append(tuple(['path',root+'\\Keil_5\\']))
                    self.keil_path.append(tuple(['project',project[0]]))
            if 'arm5_no_packs' in dirs :
                files=os.listdir(root+'\\arm5_no_packs\\')
                project=[x for x in files if x.endswith('.uvprojx')]
                if len(project) is not 0:
                    self.keil_path.append(tuple(['path',root+'\\arm5_no_packs\\']))
                    self.keil_path.append(tuple(['project',project[0]]))
            if 'mdk' in dirs :
                files=os.listdir(root+'\\mdk\\')
                project=[x for x in files if x.endswith('.uvprojx')]
                if len(project) is not 0:
                    self.keil_path.append(tuple(['path',root+'\\mdk\\']))
                    self.keil_path.append(tuple(['project',project[0]]))
            # IAR项目
            if 'iar' in dirs:
                files=os.listdir(root+'\\iar\\')
                project=[x for x in files if x.endswith('.ewp')]
                for i in project:
                    if i == 'copy.ewp' or 'Backup' in i:
                        pass
                    else:
                        self.iar_path.append(tuple(['path',root+'\\iar\\']))
                        self.iar_path.append(tuple(['project',i]))
            # CCS项目
            if 'ccs' in dirs:
                files=os.listdir(root+'\\ccs\\')
                project=[x for x in files if x.endswith('.projectspec')]
                if len(project) is not 0 and 'kernel' not in root and 'source' not in root:
                    self.ccs_path.append(tuple(['path',root+'\\ccs\\']))
                    self.ccs_path.append(tuple(['project',project[0]]))
        self.save_info(self.keil_path,'keil_p')
        self.save_info(self.iar_path,'iar_p')
        self.save_info(self.ccs_path,'ccs')

    #######################################
    # 批处理脚本编写
    #######################################
    def write_bat(self,path,project,optimization,ctype):
        if ctype=='keil':
            self.write_keil_bat(path,project,optimization)
        elif ctype=='iar':
            self.write_iar_bat(path,project,optimization)
        elif ctype=='ccs':
            self.write_makefile(path,project,optimization)
 
    #######################################
    # Keil MDK 编译脚本
    # 参数为项目路径、项目名称、优化级别
    #######################################
    def write_keil_bat(self,path,project,optimization):
        os.chdir(path)
        # 读取工程文件信息
        with open(project,'r') as f:
            data=f.read()
        f.close()

        # 更改编译信息，设置输出Hex文件，删除可能的.out后缀名
        outname=re.findall('<OutputName>[\S]+</OutputName>',data)
        newname=outname[0].split('>')[1].split('<')[0].replace('.out','')
        data=data.replace(outname[0],'<OutputName>'+newname+'</OutputName>')

        # 勾选生成 hex文件
        hexfile=re.findall('<CreateHexFile>[\d]*',data)
        data=data.replace(hexfile[0],'<CreateHexFile>1')
        hexformat=re.findall('<HexFormatSelection>[\d]*',data)
        data=data.replace(hexformat[0],'<HexFormatSelection>1')

        #------------------------------------------------------------------------------------------
        # 更改优化级别,优化级别对应的数字如下：
        # optimization | -default | -O0 | -O1 | -O2 | -O3 | -Ofast | -Os balanced | -Oz image size
        #------------------------------------------------------------------------------------------
        #        value |    0     |  1  |  2  |  3  |  4  |    5   |       6      |        7
        #------------------------------------------------------------------------------------------
        if optimization=='O0':
            optimization=1
        elif optimization == 'O1':
            optimization=2
        elif optimization == 'O2':
            optimization=3
        elif optimization == 'O3':
            optimization=4
        elif optimization == 'Ofast':
            optimization=5
        elif optimization == 'Os':
            optimization=6
        elif optimization == 'Oz':
            optimization=7

        optimization=re.findall('<Optim>[\d]*',data)
        data=data.replace(optimization[0],'<Optim>{}'.format(optimization))

        # 更换编译器版本
        try:
            compiler=re.findall('<pArmCC>[\S]+</pArmCC>',data)
            data=data.replace(compiler[0],'<pArmCC>6150000::V6.15::ARMCLANG</pArmCC>')
            compiler=re.findall('<pCCUsed>[\S]+</pCCUsed>',data)
            data=data.replace(compiler[0],'<pCCUsed>6150000::V6.15::ARMCLANG</pCCUsed>')
        except Exception as e:
            print(e)
        
        # 保存更新后的工程文件
        with open(project,'w') as f:
            f.write(data)
        f.close()

        # 编写批处理文件，调用 UV 命令
        # UV设置为本机的Keil目录
        with open('project.bat','w',encoding='ansi') as f:
            f.write('@echo off \n')
            f.write('set UV={} \n'.format('D:\\Keil5.33\\UV4\\UV4.exe'))
            f.write('set UV_PRO_PATH={}\n'.format(project))
            f.write('echo Init building ...\n')
            f.write('echo .>build_log.txt\n')
            f.write('%UV% -j0 -r %UV_PRO_PATH% -o build_log.txt\n')
            f.write('type build_log.txt\n')
            f.write('exit')
        f.close()
    
    # IAR 不同优化级别对应的数值
    def check_opt_num(self,opt):
        opts={
            'On':0,
            'Ol':1,
            'Om':2,
            'Oh':3,
            'Ohz':4,
            'Ohs':5
        }
        return opts.get(opt,None)

    #######################################
    # IAR 编译脚本
    # 参数为项目路径、项目名称、优化级别
    #######################################
    def write_iar_bat(self,path,project,optimization):
        makefilepath=path+'makefile'
        os.chdir(path)

        # 如果源码为TI SDK，且目录下存在 makefile文件，修改makefile文件
        if os.path.exists(makefilepath):
            print('[start] compile sample [{}] :'.format(path+project))
            origin=''
            # 将 makefile中编译结果由 out文件改为 elf文件
            with open(makefilepath,'r',encoding='utf-8') as f:
                origin=f.read().replace('$(NAME).out','$(NAME).elf')
            f.close()
            os.chdir(path)
            # 根据不同的优化选项编写不同的 makefile，以优化级别作为文件名
            with open(optimization,'w',encoding='utf-8') as f:
                try:
                    # 修改文件名
                    name=re.findall(r'NAME.=.[\w]+',origin)[0]
                    data=origin.replace(name,name.split('_')[0]+'_'+optimization)
                    # 增加优化级别选项
                    cf=re.findall(r'CFLAGS =.+',data)[0]
                    o=cf.replace('\\','')+'-'+optimization+' \\'
                    data=data.replace(cf,o)
                    # 删除 make clean命令中的删除 elf文件
                    data=data.replace('@ $(RM) $(NAME).elf > $(DEVNULL) 2>&1','')
                    f.write(data)
                except Exception as e:
                    print(e)
            f.close()

        # 通用的 IAR 编译方法
        with open(project,'r') as f:
            data=f.read()
        f.close()

        # 获取项目配置名
        names=re.findall('configuration>[\s]+<name>[\w]+_*[\w]+',data)

        # 更改输出文件格式
        linkformat=re.findall('IlinkOutputFile</name>[\s]+<state>[.#\w]*<',data)
        for i in range(len(linkformat)):
            data=data.replace(linkformat[i],linkformat[i].split('<state>')[0]+'<state>'+project.split('.')[0]+'_'+str(optimization)+'.elf'+'<')

        #--------------------------------------------------------------------------
        # 更改优化级别，优化级别对应的属性值如下：
        #--------------------------------------------------------------------------
        # optimization  CCOptLevel  CCOptLevelSlave  CCOptStrategy  CCAllowList
        #--------------------------------------------------------------------------
        #    -On           0               0              0           00000000
        #    -Ol           1               1              0           00000000
        #    -Om           2               2              0           10010100
        #    -Oh           3               3              0           11111110
        #    -Ohz          3               3              1           11111110
        #    -Ohs          3               3              2           11111110
        #--------------------------------------------------------------------------
        num=self.check_opt_num(optimization)
        if num < 3:
            opt=re.findall('CCOptLevel</name>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(num))
            opt=re.findall('CCOptLevelSlave</name>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(num))
            opt=re.findall('CCOptStrategy</name>[\s]+<version>0</version>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(0))
        else:
            opt=re.findall('CCOptLevel</name>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(3))
            opt=re.findall('CCOptLevelSlave</name>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(3))
            opt=re.findall('CCOptStrategy</name>[\s]+<version>0</version>[\s]+<state>[\d]+',data)
            for i in range(len(opt)):
                data=data.replace(opt[i],opt[i][0:-1]+str(num%3))
        if num == 1:
            optt=re.findall('CCAllowList</name>[\s]+<version>1</version>[\s]+<state>[\d]+',data)
            for i in range(len(optt)):
                data=data.replace(optt[i],optt[i][0:-8]+'00000000')
        elif num == 2:
            optt=re.findall('CCAllowList</name>[\s]+<version>1</version>[\s]+<state>[\d]+',data)
            for i in range(len(optt)):
                data=data.replace(optt[i],optt[i][0:-8]+'10010100')
                
        elif num >= 3:
            optt=re.findall('CCAllowList</name>[\s]+<version>1</version>[\s]+<state>[\d]+',data)
            for i in range(len(optt)):
                data=data.replace(optt[i],optt[i][0:-8]+'11111110')

        # 保存更新后的工程文件
        with open(project,'w') as f:
            f.write(data)
        f.close()

        # 编写批处理脚本，调用 IARBuild.exe根据 ewp文件重构项目
        with open('project.bat','w',encoding='ansi') as f:
            f.write('@echo off \n')
            # Nordic 芯片匹配 IAR 版本
            if 'pca10040e' in path or 'pca10056e' in path :
                # f.write('set IAR={}\n'.format('D:\\IARforARMfreetrial\\common\\bin\\iarbuild.exe'))
                f.write('set IAR={}\n'.format('D:\\IARforARMv8.40.2\\common\\bin\\iarbuild.exe'))
            # Nordic 低版本SDK使用 IAR v7.80
            elif 'pca10040' in path or 'pca10056' in path or 'd52_starterkit' in path or 'pca10028' in path or 'pca10031' in path or 'n5_starterkit' in path:
                f.write('set IAR={}\n'.format('D:\\IARforARMv7.80.4\\common\\bin\\IarBuild.exe'))
            else:
                # f.write('set IAR={}\n'.format('D:\\IARforARMfreetrial\\common\\bin\\iarbuild.exe'))
                f.write('set IAR={}\n'.format('D:\\IARforARMv8.40.2\\common\\bin\\iarbuild.exe'))
            f.write('set IAR_PRO_PATH={}\n'.format(project))
            f.write('echo Init building ...\n')
            # 根据不同的配置名编译项目
            for i in range(len(names)):
                f.write('%IAR% %IAR_PRO_PATH% -build {} -log errors\n'.format(names[i].split('<name>')[1]))
            f.write('echo Done.\n')
            f.write('exit')
        f.close()

    #######################################
    # CCS 编译脚本
    # 参数为项目路径、项目名称、优化级别
    #######################################
    def write_makefile(self,path,project,optimization):
        makefilepath=path+'makefile'
        os.chdir(path)
        #如果文件夹下存在makefile文件
        if os.path.exists(makefilepath):
            print('[start] compile sample [{}] :'.format(path+project))
            origin=''
            # 若makefile默认编译生成out文件，更改成elf文件
            with open(makefilepath,'r',encoding='utf-8') as f:
                origin=f.read().replace('$(NAME).out','$(NAME).elf')
            f.close()
            os.chdir(path)
            # 根据不同的优化选项编写不同的makefile
            with open(optimization,'w',encoding='utf-8') as f:
                try:
                    name=re.findall(r'NAME.=.[\w]+',origin)[0]
                    data=origin.replace(name,name.split('_')[0]+'_'+optimization)
                    # 在CFLAGS中添加编译选项
                    cf=re.findall(r'CFLAGS =.+',data)[0]
                    o=cf.replace('\\','')+'-'+optimization+' \\'
                    data=data.replace(cf,o)
                    # 更改 make clean命令的内容
                    data=data.replace('@ $(RM) $(NAME).elf > $(DEVNULL) 2>&1','')
                    f.write(data)
                except Exception as e:
                    print(e)
            f.close()

    #######################################
    # 命令行编译
    # 参数为项目路径、项目名称、优化级别
    #######################################
    def compile(self,path,project,optimization,compiler):
        os.chdir(path)
        flag = 0
        # 若目录下存在makefile脚本，执行make命令
        if os.path.exists(path+optimization):
            try:
                # 清除编译临时文件
                e=subprocess.Popen('make -f %s clean'%(optimization),shell=True)
                e.wait()
                print('[clean][end]')

                print('[make][start][{}]--[{}]'.format(path+project,optimization))
                s=subprocess.Popen('make -f %s'%(optimization),shell=True,stdout=subprocess.PIPE)
                s.wait()
            except Exception as e:
                print(e)

        time.sleep(0.1)

        # 判断 make 是否成功，若不成功执行 bat批处理脚本
        for root,dirs,files in os.walk(path,topdown=True):
                for x in files:
                    if compiler == 'iar' or compiler == 'ccs':
                        if x == project.split('.')[0]+'_'+optimization+'.elf':
                            flag = 1
                    if compiler == 'keil':
                        if x == project.split('.')[0]+'_'+optimization+'.axf':
                            flag = 1
        if flag is 0:
            # 执行 project.bat脚本     
            try:
                p=subprocess.Popen('project.bat',shell=True,stdout=subprocess.PIPE)
                while True:
                    if p.poll() == 0:
                        break
                
                    msg=p.stdout.readline().decode("gbk").strip()
                    print(msg)
                    if 'Error' in msg:
                        self.failed_list.append(tuple(['path',path]))
                        self.failed_list.append(tuple(['compiler',compiler]))
                        self.failed_list.append(tuple(['project',project]))
                        self.failed_list.append(tuple(['error',msg]))
                        p.kill()
                        p.wait()
                        break
            except Exception as e:
                print(e)

    #######################################
    # 编译入口
    #######################################
    def run(self,start,end,optimization,compiler):
        data = self.read_info(compiler)
        for i in range(start,end):
            flag = 0
            project = data['project'][i]
            path = data['path'][i]

            print('项目序号{}，名称{},'.format(i,project))
            print('生成编译脚本...')
            self.write_bat(path,project,optimization,compiler)
            print('脚本生成结束！')
            print('编译序号{}，名称{}...'.format(i,path+project))
            self.compile(path,project,optimization,compiler)

            # 判断编译是否成功
            for root,dirs,files in os.walk(path,topdown=True):
                for x in files:
                    if compiler == 'iar' or compiler == 'ccs':
                        if x == project.split('.')[0]+'_'+optimization+'.elf':
                            flag = 1
                    if compiler == 'keil':
                        if x == project.split('.')[0]+'_'+optimization+'.axf':
                            flag=1

            # 编译失败,记录失败信息
            if flag == 0:
                if compiler=='keil':
                    for root,dirs,files in os.walk(path,topdown=True):
                        for file in files:
                            k=data['project'][i].replace('.uvprojx','_{}.build_log.htm'.format(optimization))
                            fail_msg=''
                            if file==k:
                                with open(root+'\\'+k,'r',encoding='gbk') as f:
                                    for line in f:
                                        if 'Error:' in line:
                                            fail_msg=line
                                            self.failed_list.append(tuple(['path',path]))
                                            self.failed_list.append(tuple(['compiler','keil']))
                                            self.failed_list.append(tuple(['project',project]))
                                            self.failed_list.append(tuple(['error',line]))
                                            break

            if len(self.failed_list) > 0 :
                cn=defaultdict(list)
                for k,v in self.failed_list:
                    cn[k].append(v)
                text=pd.DataFrame(cn)
                text.to_csv('e:\\daimaku\\code\\failed_{}_{}.csv'.format(compiler,optimization),encoding='utf-8-sig')         
        
if __name__=='__main__':
    compiler=Compiler()
    db=database()
    compiler.get_all_samples('e:\\daimaku\\src\\NXP')

    # compiler.get_all_samples('e:\\daimaku\\src\\NXP\\ARM Cortex-M0\\SDK_2.2.0_FRDM-KL25Z\\')
    # compiler.run(0,4,'On','iar')
    # compiler.get_all_samples('e:\\daimaku\\src\\NXP\\ARM Cortex-A53\\SDK_2.9.0_MEK-MIMX8QM\\')
    # compiler.run(0,4,'On','iar')
    # compiler.get_all_samples('e:\\daimaku\\src\\NXP\\ARM Cortex-M0\\SDK_2.9.0_FRDM-KE04Z\\')
    # compiler.run(0,2,'O0','keil')



    # # 多进程编译 
    # threads=list()
    # try:
    #     for i in range(3):
    #         th_i=Process(target=compiler.run,args=(i*2,(i+1)*2,'O0','keil'))
    #         th_i.start()
    #         threads.append(th_i)
    #     for thread in threads:
    #         thread.join()
    # except Exception as e:
    #     print(e)