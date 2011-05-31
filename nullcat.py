#!/usr/bin/env python
#nullcat is nulllllllllllllllllllllll

import os, stat, errno
import fuse

if not hasattr(fuse, '__version__'): raise RuntimeError
fuse.fuse_python_api = (0, 2)

class FS_Object:
	def __init__(self): return None

class FS_File(FS_Object):
	st_mode=stat.S_IFREG
	def __init__(self,name,parent=None):
		self.name=name
		self.parent=parent

class FS_Directory(FS_Object):
	st_mode=stat.S_IFDIR
	def __init__(self,name,parent=None):
		self.parent=parent
		self.name=name
		self.files={}
		self.directories={}

	def enter_directory(self,directory):
		if len(directory)==0: return self
		elif self.directories.has_key(directory[0]): return self.directories[directory[0]].enter_directory(directory[1:])
		elif self.files.has_key(directory[0]): return self.files[directory[0]]
		else: return -errno.ENOENT

class MyStat(fuse.Stat):
	def __init__(self):
		self.st_mode = 0
		self.st_ino = 0
		self.st_dev = 0
		self.st_nlink = 0
		self.st_uid = 0
		self.st_gid = 0
		self.st_size = 0
		self.st_atime = 0
		self.st_mtime = 0
		self.st_ctime = 0

class NullcatFS(fuse.Fuse):
	def __init__(self, *args, **kw):
		fuse.Fuse.__init__(self, *args, **kw)
		self.rootdir=FS_Directory('')
	
	def enter_directory(self,path,skip_elements=0):
		split_path=path.split('/'); return self.rootdir.enter_directory(split_path[1:len(split_path)-skip_elements])
	
	def readdir(self, path, offset):
		for r in  '.', '..': yield fuse.Direntry(r)
	
	def getattr(self, path):
		st = MyStat()
		d=self.enter_directory(path)
		if d!=-errno.ENOENT:
			st.st_mode = d.st_mode | 0666
			return st
		else: return -errno.ENOENT
	
	def mkent(self,path,entity_type=None,mode=None,dev=None):
		path_split=path.split('/')
		nest=self.rootdir.enter_directory(path_split[1:-1])
		if path!='/':
			if   entity_type=="directory": nest.directories[path_split[-1]]=FS_Directory(path_split[-1],nest)
			elif entity_type=="file": nest.directories[path_split[-1]]=FS_Directory(path_split[-1],nest)
		return 0

	def rename(self, oldPath, newPath): #Unfortunately, I had to implement this right :/
		d1=self.enter_directory(oldPath)
		d2=self.enter_directory(newPath,1)
		if d1.st_mode==stat.S_IFREG: del d1.parent.files[d1.name]; d2.files[d1.name]=d1
		else: del d1.parent.directories[d1.name]; d2.directories[d1.name]=d1
		return 0
	
	def rmdir (self, path):
		d=self.enter_directory(path)
		if d!=-errno.ENOENT:
			if len(d.files)+len(d.directories) == 0: del d.parent.directories[path.split('/')[-1]]; return 0
		else: return -errno.ENOENT
		return -errno.ENOTEMPTY
	
	def mknod (self, path, mode, dev): return self.mkent(path, "file")
	def mkdir(self, path, mode): return self.mkent(path, "directory")
	def truncate(self, path, size): return self.mknod(path, None, None) #Trunkating file, riiight...
	def ftruncate(self, path, size): return self.mknod(path, None, None) #(f)Trunkating file, riiight...
	def link(self, target, link): self.mknod(target, None, None) #Yeah, we'll link you up, especially if you want to link to a directory.
	def utime (self, path, times): return 0 #Ok, let me save this somewhere.
	def open(self, path, flags): return 0  #Yeah, open up whatever you want
	def read(self, path, size, offset): return "" #Ah, sure, here's your data
	def write (self, path, buf, offset): return len(buf) #Success! All data stored on your HDD!

if __name__ == '__main__':
	server = NullcatFS(version="%prog " + fuse.__version__, usage=fuse.Fuse.fusage, dash_s_do='setsingle')
	server.parse(errex=1)
	server.main()