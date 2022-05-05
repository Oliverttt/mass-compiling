# compile script
import os
from collections import defaultdict
import pandas as pd
import re
import subprocess
import time
from multiprocessing import Process
from db import database

class Compiler():
    def __init__(self):
        self.keil_path=list()
        self.iar_path=list()
        self.ccs_path=list()
        self.failed_list=list()
        self.work_project=list()
        self.work_path=list()
    
    # store SDK info
    def save_info(self,x,y):
        data=defaultdict(list)
        for k,v in x:
            data[k].append(v)
        text=pd.DataFrame(data)
        text.to_csv('{}.csv'.format(y),encoding='utf-8-sig')

    # read SDK info
    def read_info(self,compiler):
        f=open('{}.csv'.format(compiler),encoding='utf_8_sig')
        data=pd.read_csv(f,engine='python')
        return data
        
    # extract SDK info
    def get_all_samples(self,path):
        for root,dirs,files in os.walk(path,topdown=True):
            # Keil
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
            # IAR
            if 'iar' in dirs:
                files=os.listdir(root+'\\iar\\')
                project=[x for x in files if x.endswith('.ewp')]
                for i in project:
                    if i == 'copy.ewp' or 'Backup' in i:
                        pass
                    else:
                        self.iar_path.append(tuple(['path',root+'\\iar\\']))
                        self.iar_path.append(tuple(['project',i]))
            # CCS
            if 'ccs' in dirs:
                files=os.listdir(root+'\\ccs\\')
                project=[x for x in files if x.endswith('.projectspec')]
                if len(project) is not 0 and 'kernel' not in root and 'source' not in root:
                    self.ccs_path.append(tuple(['path',root+'\\ccs\\']))
                    self.ccs_path.append(tuple(['project',project[0]]))
        self.save_info(self.keil_path,'keil_p')
        self.save_info(self.iar_path,'iar_p')
        self.save_info(self.ccs_path,'ccs')

    # batch script
    def write_bat(self,path,project,optimization,ctype):
        if ctype=='keil':
            self.write_keil_bat(path,project,optimization)
        elif ctype=='iar':
            self.write_iar_bat(path,project,optimization)
        elif ctype=='ccs':
            self.write_makefile(path,project,optimization)
 
    #====================================================
    # Keil MDK compile script
    # params:project path,project name,optimization level
    #====================================================
    def write_keil_bat(self,path,project,optimization):
        os.chdir(path)
        with open(project,'r') as f:
            data=f.read()
        f.close()

        # change compile info
        outname=re.findall('<OutputName>[\S]+</OutputName>',data)
        newname=outname[0].split('>')[1].split('<')[0].replace('.out','')
        data=data.replace(outname[0],'<OutputName>'+newname+'</OutputName>')
        hexfile=re.findall('<CreateHexFile>[\d]*',data)
        data=data.replace(hexfile[0],'<CreateHexFile>1')
        hexformat=re.findall('<HexFormatSelection>[\d]*',data)
        data=data.replace(hexformat[0],'<HexFormatSelection>1')

        #------------------------------------------------------------------------------------------
        # optimization | -default | -O0 | -O1 | -O2 | -O3 | -Ofast | -Os balanced | -Oz image size
        #------------------------------------------------------------------------------------------
        #        value |    0     |  1  |  2  |  3  |  4  |    5   |       6      |        7
        #------------------------------------------------------------------------------------------
        if optimization=='O0':optimization=1
        elif optimization == 'O1':optimization=2
        elif optimization == 'O2':optimization=3
        elif optimization == 'O3':optimization=4
        elif optimization == 'Ofast':optimization=5
        elif optimization == 'Os':optimization=6
        elif optimization == 'Oz':optimization=7

        optimization=re.findall('<Optim>[\d]*',data)
        data=data.replace(optimization[0],'<Optim>{}'.format(optimization))

        # change compile version
        try:
            compiler=re.findall('<pArmCC>[\S]+</pArmCC>',data)
            data=data.replace(compiler[0],'<pArmCC>6150000::V6.15::ARMCLANG</pArmCC>')
            compiler=re.findall('<pCCUsed>[\S]+</pCCUsed>',data)
            data=data.replace(compiler[0],'<pCCUsed>6150000::V6.15::ARMCLANG</pCCUsed>')
        except Exception as e:
            print(e)
        
        # save new project
        with open(project,'w') as f:
            f.write(data)
        f.close()

        # use UV
        with open('project.bat','w',encoding='ansi') as f:
            f.write('@echo off \n')
            f.write('set UV={} \n'.format('your UV4.exe path'))
            f.write('set UV_PRO_PATH={}\n'.format(project))
            f.write('echo Init building ...\n')
            f.write('echo .>build_log.txt\n')
            f.write('%UV% -j0 -r %UV_PRO_PATH% -o build_log.txt\n')
            f.write('type build_log.txt\n')
            f.write('exit')
        f.close()
    
    # IAR optimization level and value
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
    #====================================================
    # IAR compile script
    # params:project path,project name,optimization level
    #====================================================
    def write_iar_bat(self,path,project,optimization):
        makefilepath=path+'makefile'
        os.chdir(path)

#         # TI SDK, modify makefile
#         if os.path.exists(makefilepath):
#             print('[start] compile sample [{}] :'.format(path+project))
#             origin=''
#             with open(makefilepath,'r',encoding='utf-8') as f:
#                 origin=f.read().replace('$(NAME).out','$(NAME).elf')
#             f.close()
#             os.chdir(path)
#             with open(optimization,'w',encoding='utf-8') as f:
#                 try:
#                     name=re.findall(r'NAME.=.[\w]+',origin)[0]
#                     data=origin.replace(name,name.split('_')[0]+'_'+optimization)
#                     cf=re.findall(r'CFLAGS =.+',data)[0]
#                     o=cf.replace('\\','')+'-'+optimization+' \\'
#                     data=data.replace(cf,o)
#                     data=data.replace('@ $(RM) $(NAME).elf > $(DEVNULL) 2>&1','')
#                     f.write(data)
#                 except Exception as e:
#                     print(e)
#             f.close()

        with open(project,'r') as f:
            data=f.read()
        f.close()

        # get project name
        names=re.findall('configuration>[\s]+<name>[\w]+_*[\w]+',data)
        linkformat=re.findall('IlinkOutputFile</name>[\s]+<state>[.#\w]*<',data)
        for i in range(len(linkformat)):
            data=data.replace(linkformat[i],linkformat[i].split('<state>')[0]+'<state>'+project.split('.')[0]+'_'+str(optimization)+'.elf'+'<')

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
        
        # save new project 
        with open(project,'w') as f:
            f.write(data)
        f.close()

        # call IARBuild.exe
        with open('project.bat','w',encoding='ansi') as f:
            f.write('@echo off \n')
            # Nordic use IAR v9
            if 'pca10040e' in path or 'pca10056e' in path :
                f.write('set IAR={}\n'.format('your iarbuild.exe path'))
            # Nordic use IAR v7.80
            elif 'pca10040' in path or 'pca10056' in path or 'd52_starterkit' in path or 'pca10028' in path or 'pca10031' in path or 'n5_starterkit' in path:
                f.write('set IAR={}\n'.format('your IarBuild.exe path'))
            else:
                f.write('set IAR={}\n'.format('your iarbuild.exe path'))
            f.write('set IAR_PRO_PATH={}\n'.format(project))
            f.write('echo Init building ...\n')
            for i in range(len(names)):
                f.write('%IAR% %IAR_PRO_PATH% -build {} -log errors\n'.format(names[i].split('<name>')[1]))
            f.write('echo Done.\n')
            f.write('exit')
        f.close()

    #====================================================
    # CCS compile script
    # params:project path,project name,optimization level
    #====================================================
    def write_makefile(self,path,project,optimization):
        makefilepath=path+'makefile'
        os.chdir(path)
        # if exists makefile
        if os.path.exists(makefilepath):
            print('[start] compile sample [{}] :'.format(path+project))
            origin=''
            with open(makefilepath,'r',encoding='utf-8') as f:
                origin=f.read().replace('$(NAME).out','$(NAME).elf')
            f.close()
            os.chdir(path)
            with open(optimization,'w',encoding='utf-8') as f:
                try:
                    name=re.findall(r'NAME.=.[\w]+',origin)[0]
                    data=origin.replace(name,name.split('_')[0]+'_'+optimization)
                    # modify CFLAGS
                    cf=re.findall(r'CFLAGS =.+',data)[0]
                    o=cf.replace('\\','')+'-'+optimization+' \\'
                    data=data.replace(cf,o)
                    # modify make clean
                    data=data.replace('@ $(RM) $(NAME).elf > $(DEVNULL) 2>&1','')
                    f.write(data)
                except Exception as e:
                    print(e)
            f.close()

    #====================================================
    # CMD compilation
    # params:project path,project name,optimization level,compiler
    #====================================================
    def compile(self,path,project,optimization,compiler):
        os.chdir(path)
        flag = 0
        # if exists makefile
        if os.path.exists(path+optimization):
            try:
                e=subprocess.Popen('make -f %s clean'%(optimization),shell=True)
                e.wait()
                print('[clean][end]')
                
                print('[make][start][{}]--[{}]'.format(path+project,optimization))
                s=subprocess.Popen('make -f %s'%(optimization),shell=True,stdout=subprocess.PIPE)
                s.wait()
            except Exception as e:
                print(e)

        time.sleep(0.1)

        # if error, run project.bat
        for root,dirs,files in os.walk(path,topdown=True):
                for x in files:
                    if compiler == 'iar' or compiler == 'ccs':
                        if x == project.split('.')[0]+'_'+optimization+'.elf':
                            flag = 1
                    if compiler == 'keil':
                        if x == project.split('.')[0]+'_'+optimization+'.axf':
                            flag = 1
        if flag is 0:
            # run project.bat    
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

    #====================================================
    # compile
    #====================================================
    def run(self,start,end,optimization,compiler):
        data = self.read_info(compiler)
        for i in range(start,end):
            flag = 0
            project = data['project'][i]
            path = data['path'][i]

            print('project id{},name{},'.format(i,project))
            print('generating compile script...')
            self.write_bat(path,project,optimization,compiler)
            print('finish！')
            print('comopile id{},name{}...'.format(i,path+project))
            self.compile(path,project,optimization,compiler)

            # check compile status
            for root,dirs,files in os.walk(path,topdown=True):
                for x in files:
                    if compiler == 'iar' or compiler == 'ccs':
                        if x == project.split('.')[0]+'_'+optimization+'.elf':
                            flag = 1
                    if compiler == 'keil':
                        if x == project.split('.')[0]+'_'+optimization+'.axf':
                            flag=1

            # if error,record info
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
                text.to_csv('your failinfocsv',encoding='utf-8-sig')         
        
if __name__=='__main__':
    compiler=Compiler()
    db=database()
    compiler.get_all_samples('your SDK path')
    
    threads=list()
    try:
        for i in range(3):
            th_i=Process(target=compiler.run,args=(i*2,(i+1)*2,'O0','keil'))
            th_i.start()
            threads.append(th_i)
        for thread in threads:
            thread.join()
    except Exception as e:
        print(e)
