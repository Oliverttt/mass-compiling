import time,os
import subprocess
from db import database

class elf2sig_Plugin():
	def __init__(self,ida,idcscript,flair):
		self.basedir='E:\\daimaku\\elfs\\Nordic'
		# idc script name
		self.idcscriptname=idcscript
		# idat.exe path
		self.idatpath=ida+'\\idat.exe'
		# flair sigmake path
		self.sigmake=flair+'\\sigmake.exe'
		# ida dir
		self.ida=ida
	
	# use idat.exe generate idb, call ida2pat plugin generate pat
	def make_pat(self,target):
		print('\\'.join(target.split('\\')[0:-1]))
		os.chdir('\\'.join(target.split('\\')[0:-1]))
		print('make pat...{}'.format(target))
		if os.path.exists(target):
			cmd=self.idatpath+' -A -S'+self.idcscriptname+' '+target.split('\\')[-1]
			subprocess.Popen(cmd)

	# make sig
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
		# function collision
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
		# remake sig
		print('remake sig...')
		p=subprocess.Popen('{} -n"{}" {} {}'.format(self.sigmake,sig_path.split('.')[0],pat_path,sig_path),shell=True)
		while p.poll() is None:
			time.sleep(0.5)
		time.sleep(1)
		self.move_sig(target)
	
	# move sig to sig dir under IDA path
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

# make sig from dir
def make_d(path):
	idc="toidb.idc"
	ida="your ida path"
	flair='your flair bin path'
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


# make dir from database
def make(chip):
	idc="toidb.idc"
	ida="your ida path"
	flair='your flair bin path'
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
			print('compile:')
			for i in range(len(data)):
				print(str(i)+'.'+data[i][0])
			compile=int(input('choose compile(input id)：'))
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
		print('no info！')
		
				
if __name__=='__main__':
	chip=str(input('input'))
	make(chip)
