"""
---

name: Pd-Socket

version: 0.4.0-wip

authors:
- Enrique Erne

license: MIT license

...
"""

import asyncore, os, socket, sys, threading

class Puredata(threading.Thread):

	def prepare(self, pd = None, dir = './', file = 'pd-socket.pd', args = '-stderr -nostdpath -rt -send \"pd dsp 1;pd dsp 0;\"'):
		self.pd = pd
		self.dir = dir
		self.file = file
		# args = -stderr -nostdpath -rt -nogui -path <path> -audiobuf <n> -nostdpath -nogui -send \"pd dsp 1;pd dsp 0;\"
		# note in -nogui you can't use -send
		self.args = args
		if pd != None:
			self.pd = pd
		elif sys.platform == 'linux2':
			self.pd = 'pd'
		elif sys.platform == 'darwin':
			self.pd = '//Applications/Pd-0.42-5.app/Contents/Resources/bin/pd'
		elif sys.platform == 'win32':
			self.pd = '%programfiles%\pd\bin\pd.exe'
		return self
		
	def run(self):
		try:
			os.system('%s %s %s/%s' %(self.pd, self.args, self.dir, self.file))
		except:
			print 'couldn\'t load Pd'
		finally:
			print 'Puredata quit'


class AsyncSocket(threading.Thread):
	
	@staticmethod
	def onReady(self): pass

	@staticmethod
	def onReceive(self, data): pass
		
	def addEvent(self, event, callback):
		setattr(self, 'on' + event.capitalize(), callback)
	
	def prepare(self, host = 'localhost', sendPort = 4025, receivePort = 4026):
		
		class Connect():
			def __init__(that):
				try:
					self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					self.socket.connect((host, sendPort))
					print 'connecting to port %s' % str(sendPort)
				except socket.error, (value, message):
					if self.socket:
						self.socket.close()
	
		class Listen(asyncore.dispatcher_with_send):
			def handle_read(that):
				data = that.recv(8192)
				self.onReceive(self, data)
			def handle_close(that):
				that.close()
				exit()
		
		class Open(asyncore.dispatcher):
			def __init__(that):
				asyncore.dispatcher.__init__(that)
				that.create_socket(socket.AF_INET, socket.SOCK_STREAM)
				that.set_reuse_addr()
				that.bind((host, receivePort))
				that.listen(1)
				print 'open socket on %s' % str(receivePort)
			def handle_accept(that):
				pair = that.accept()
				if pair is None:
					pass
				else:
					sock, addr = pair
					print 'incoming connection from %s' % repr(addr)
					Connect()
					Listen(sock)
					self.onReady(self)
		
		Open()
		
	def run(self):
		asyncore.loop()
	
	def send(self, data = ''):
		if isinstance(data, basestring):
			self.socket.send(data + ';\n')
		elif isinstance(data, (list, tuple)):
			self.socket.send(';\n'.join(data) + ';\n')
		elif isinstance(data, dict):
			self.socket.send(';\n'.join('%s %s' % (k, v) for k, v in data.items()) + ';\n')
		else:
			print 'data type not supported (yet)'


def init():
	
	r = AsyncSocket()
	r.prepare()
	r.start()
	
	def hello(self):
		self.send('symbol Hello\ Pd!')
		self.send('some more...;\n...messages at once')
		self.send(['list items', 'work', 'as well'])
		self.send(('tuple', 'too'))
		self.send({'key': 'value', 'more': 3})
	
	r.onReady = hello
	#r.addEvent('ready', hello)
	
	def log(self, data):
		print 'Receive: ' + data
	
	#r.onReceive = log
	r.addEvent('receive', log)
	
	pd = Puredata()
	pd.prepare(dir = os.getcwd())
	pd.start()
	

if __name__ == '__main__':
	init()
