########################################################################################################
# 函数签名自动生成模块，实现FLIRT签名库的生成和自动导入
# 实现以下功能：
#   1.查询数据库相关芯片信息，若存在该芯片，提供该芯片的编译器类型，否则提示该芯片未存储到数据库中
#   2.用户输入选择的编译器类型
#   3.利用ida命令行模式由elf文件生成idb文件
#   4.调用ida2pat插件实现pat文件的创建
#   5.调用sigmake命令生成sig文件
#   6.将sig文件移至IDA下的sig目录下
########################################################################################################

import time,os
import subprocess
from db import database

class elf2sig_Plugin():
	def __init__(self,ida,idcscript,flair):
		self.basedir='E:\\daimaku\\elfs\\Nordic'
		# 命令行启动idc脚本名称
		self.idcscriptname=idcscript
		# ida命令行启动程序路径
		self.idatpath=ida+'\\idat.exe'
		# flair sigmake路径
		self.sigmake=flair+'\\sigmake.exe'
		# ida安装目录
		self.ida=ida
	
	# 通过ida命令行程序生成idb数据库，调用ida2pat插件生成pat文件
	def make_pat(self,target):
		print('\\'.join(target.split('\\')[0:-1]))
		os.chdir('\\'.join(target.split('\\')[0:-1]))
		print('make pat...{}'.format(target))
		if os.path.exists(target):
			cmd=self.idatpath+' -A -S'+self.idcscriptname+' '+target.split('\\')[-1]
			subprocess.Popen(cmd)

	# 制作签名
	def make_sig(self,target):
		os.chdir('\\'.join(target.split('\\')[0:-1]))
		target=target.replace('/','\\')
		pat_path=target.split('\\')[-1][0:-3]+'pat'
		sig_path=target.split('\\')[-1][0:-3]+'sig'
		print('make sig...')
		while not os.path.exists(pat_path):
			time.sleep(0.5)
		p=subprocess.Popen('{} -n"{}" {} {}'.format(self.sigmake,sig_path.split('.')[0],pat_path,sig_path),shell=True)
		while p.poll() is None:
			time.sleep(0.5)
		# 处理函数碰撞
		print('modify err...')
		exc=target.split('\\')[-1][0:-3]+'exc'
		lines=list()
		if os.path.exists(exc):
			with open(exc,'r') as f:
				for line in f:
					if ';' not in line:
						lines.append(line)
			f.close()
			with open(exc,'w') as f:
				for i in range(len(lines)):
					if lines[i]=='\n' and i != (len(lines)-1):
						lines[i+1]='+'+lines[i+1]
					f.write(lines[i])
			f.close()
		# 重新制作签名
		print('remake sig...')
		p=subprocess.Popen('{} -n"{}" {} {}'.format(self.sigmake,sig_path.split('.')[0],pat_path,sig_path),shell=True)
		while p.poll() is None:
			time.sleep(0.5)
		time.sleep(1)
		self.move_sig(target)
	
	# 将生成的sig签名移至IDA下的sig目录下
	def move_sig(self,target):
		print('move sig...')
		target_dir=self.ida+'\\sig\\arm\\'
		sig=target[0:-3]+'sig'
		while not os.path.exists(sig):
			time.sleep(0.5)
		with open(sig,'rb') as f:
			data=f.read()
		f.close()
		new_sig=sig.split('\\')[-1]
		with open(target_dir+new_sig,'wb') as f:
			f.write(data)
		f.close()
		print('end!\n\n')

# 根据目录创建签名
def make_d(path):
	idc="toidb.idc"
	ida="D:\\IDA_Pro_v7.0_Portable"
	flair='D:\\IDA_Pro_v7.0_Portable\\ida_plugin\\7-Flair\\bin'
	flag=0
	axf_paths=[]
	elf_paths=[]

	plugin=elf2sig_Plugin(ida,idc,flair)
	pat_base=flair+'\\pat\\'
	sig_base=flair+'\\sig\\'
	if not os.path.exists(pat_base):os.makedirs(pat_base)
	if not os.path.exists(sig_base):os.makedirs(sig_base)

	for root,dirs,files in os.walk(path,topdown=True):
		for i in files:
			if i.endswith('.elf'):
				elf_paths.append(root+'\\'+i)
			if i.endswith('.axf'):
				axf_paths.append(root+'\\'+i)

	for i in elf_paths:
		if not os.path.exists(i.replace('.elf','.sig')):
			plugin.make_pat(i)
			# time.sleep(1)
			plugin.make_sig(i)

	# for i in axf_paths:
	# 	plugin.make_pat(i)
	# 	time.sleep(1)
	# 	plugin.make_sig(i)


# 数据库查询
def make(chip):
	idc="toidb.idc"
	ida="D:\\IDA_Pro_v7.0_Portable"
	flair='D:\\IDA_Pro_v7.0_Portable\\ida_plugin\\7-Flair\\bin'
	flag=0

	plugin=elf2sig_Plugin(ida,idc,flair)
	pat_base=flair+'\\pat\\'
	sig_base=flair+'\\sig\\'
	if not os.path.exists(pat_base):os.makedirs(pat_base)
	if not os.path.exists(sig_base):os.makedirs(sig_base)

	db=database()
	sql='select name from sqlite_master where type="table"'
	result=db.search(sql)
	for i in result:
		company=i[0]
		sql='select DISTINCT compiler from {} where chip_name LIKE "%{}%" '.format(company,chip)
		if len(db.search(sql)) is not 0:
			flag=1
			data=db.search(sql)
			print('该芯片的编译环境为:')
			for i in range(len(data)):
				print(str(i)+'.'+data[i][0])
			compile=int(input('选择编译环境为（请输入序号）：'))
			sql='select outputfile_name,outputfile_location from {} where chip_name like "%{}%" and compiler="{}"'.format(company,chip,data[compile][0])
			data=db.search(sql)
			for i in range(len(data)):
				sample=data[i][0]
				path=data[i][1].replace('/','\\')
		
				fi='E:\\daimaku\\'+path+'\\'+sample

				files=os.listdir('\\'.join(fi.split('\\')[0:-1]))
				sig=[x for x in files if x.endswith('.sig')]
				# if len(sig) is 0:
				# 	plugin.make_pat(fi)
				# 	time.sleep(1)
				# 	plugin.make_sig(fi)

				plugin.make_pat(fi)
				time.sleep(1)
				plugin.make_sig(fi)
	if not flag:
		print('数据库中暂无该芯片信息！')
		
				
if __name__=='__main__':
	chip=str(input('请输入待查询的芯片型号：'))
	make(chip)
	# make_d('E:\\daimaku\\elfs\\Nordic\\ARM Cortex-M0\\nRF51822\\')