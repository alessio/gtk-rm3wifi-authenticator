#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of gtk-rm3wifi-authenticator
#
# gtk-rm3wifi-authenticator v0.4.1 - A small authenticator for wireless network of
# University of RomaTre.
# Copyright (C) 2008  Alessio Treglia <quadrispro@ubuntu-it.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

#change to the directory that the file lives in
import os, sys, time, signal, string, errno, thread, threading
if __name__ == '__main__':
	os.chdir(os.path.dirname(os.path.normpath(os.path.join(os.getcwd(),sys.argv[0]))))
#import the dbus stuff
import gobject
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib
import time, syslog

from rm3wifiservice import WiFiAuthenticator

from rm3wificommon import PID_PATH, LANG_PATH

import locale, gettext

############# TRANSLATIONS SECTION

LOCALE_PATH = os.path.realpath(os.path.dirname(sys.argv[0])) + '/po'
locale.setlocale(locale.LC_ALL, '')

# register the gettext function for the whole interpreter as "_"
import __builtin__
__builtin__._ = gettext.gettext

############# END TRANSLATIONS SECTION

class FactotumException(dbus.DBusException):
	_dbus_error_name = 'org.factotum.daemon.FactotumException'

class FactotumDaemon(dbus.service.Object):
	MIN_TIMEOUT_RELOGIN = 1800.0

	def __init__(self, bus_name, object_path='/org/factotum/daemon'):
		dbus.service.Object.__init__(self, bus_name, object_path)
		self.wifi_auth = WiFiAuthenticator()
	@dbus.service.method('org.factotum.daemon')
	def login(self):
		# Do auth
		return self.wifi_auth.authorize()
	@dbus.service.method('org.factotum.daemon')
	def set_username(self, username):
		self.wifi_auth.set_username(username)
	@dbus.service.method('org.factotum.daemon')
	def set_password(self, password):
		self.wifi_auth.set_password(password)
	@dbus.service.method('org.factotum.daemon')
	def start_autorelogin(self):
		self.wifi_auth.start_autorelogin()
	@dbus.service.method('org.factotum.daemon')
	def stop_autorelogin(self):
		self.wifi_auth.stop_autorelogin()
	@dbus.service.method('org.factotum.daemon')
	def set_relogin_timeout(self, relogin_timeout):
		self.wifi_auth.set_relogin_timeout(relogin_timeout)
	@dbus.service.method('org.factotum.daemon')
	def set_relogin(self, relogin):
		self.wifi_auth.set_relogin(relogin)
	@dbus.service.method('org.factotum.daemon')
	def hello(self):
		syslog.syslog(syslog.LOG_INFO, 'Hello world!')

############## SIGNAL HANDLERS ##############
def terminate(signal, param):
	try:
		# Do necessary cleanup handling
		#...
		#...
		#...

		# Remove the pid file
		os.remove(os.path.join(PID_PATH, 'run.pid'))
	except:
		pass                            # Ignore any errors
	sys.stdout.write("........terminating\n")
	sys.exit(0)
############## END SIGNAL HANDLERS ##############

def status():
	"""
	Return daemon's pid if it's running, -1 otherwise.
	"""
	if os.path.isfile(os.path.join(PID_PATH, 'run.pid')):
		f = open(os.path.join(PID_PATH, 'run.pid'), 'r')
		pid = string.atoi(string.strip(f.readline()))
		f.close()
		try:
			os.kill(pid, 0)
		except os.error, args:
			if args[0] != errno.ESRCH: # NO SUCH PROCESS
				raise os.error, args
		else:
			# daemon is running
			return pid
	# daemon is not running
	return -1

def start():
	"""
	Start daemon.
	"""
	try:
		pid = os.fork()
		if pid > 0:
			# exit first parent
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
		syslog.syslog(syslog.LOG_ERR, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)) # log
		sys.exit(1)

	# decouple from parent environment
	os.setsid()
	os.umask(0)

	# do second fork
	try:
		pid = os.fork()
		if pid > 0:
			print >>sys.stdout, "Starting %s... (pid %d)" % (call_name, pid),
			syslog.syslog(syslog.LOG_INFO, 'Starting with pid %d...' % pid) # log
			print >>sys.stdout, "\t\t\tOK"
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
		syslog.syslog(syslog.LOG_ERR, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)) # log
		sys.exit(1)

	# Check, if the log directory is already there. If not, create it
	if not os.path.isdir(PID_PATH):
		os.mkdir(PID_PATH, 0755)

	# Write our process id into the pid file
	f = open(os.path.join(PID_PATH, 'run.pid'), 'w')
	f.write("%d" % os.getpid())
	f.close()
	
	return 0

def stop():
	"""
	Return 0 if daemon is running, -1 otherwise.
	"""
	if os.path.isfile(os.path.join(PID_PATH, 'run.pid')):
		f = open(os.path.join(PID_PATH, 'run.pid'), 'r')
		pid = string.atoi(string.strip(f.readline()))
		f.close()
		try:
			os.kill(pid, 0)
		except os.error, args:
			if args[0] != errno.ESRCH: # NO SUCH PROCESS
				raise os.error, args
		else:
			os.kill(pid, signal.SIGTERM)
			syslog.syslog(syslog.LOG_INFO, 'stopped.') # log
			return 0

	return 1

# Store the name of the programm
call_name = os.path.split(sys.argv[0])[1]

#initialize logging
syslog.openlog(call_name)

# Get the call arguments (stop, status)
if len(sys.argv) != 2:
	sys.stderr.write("Usage: %s [start|stop|status]\n" % call_name)
	sys.exit(1)
if len(sys.argv) == 2:
	if sys.argv[1] == 'stop':
		# Stop the daemon
		s = stop()
		if s == 1:
			sys.stdout.write("%s is not running.\n" % call_name)
			sys.exit(1)
		sys.stdout.write("%s: stopped.\n" % call_name)
		sys.exit(0)
	elif sys.argv[1] == 'status':
		# Print daemon status
		s = status()
		if s == -1:
			sys.stdout.write("%s is not running\n" % call_name)
		else:
			sys.stdout.write("%s is running with pid %d\n" % (call_name, s))
		sys.exit(0)
	elif sys.argv[1] == 'start':
		# Start the daemon
		s = status()
		if s != -1:
			sys.stdout.write("%s is running with pid %d.\n" % (call_name, s))
			sys.exit(1)
		start()
	else:
		sys.stderr.write("Usage: %s [start|stop|status]\n" % call_name)
		sys.exit(1)

#open our dbus session
session_bus = dbus.SessionBus()
try:
	bus_name = dbus.service.BusName('org.factotum.daemon', bus=session_bus)
	object = FactotumDaemon(bus_name)
except Exception, e:
	# print >>sys.stderr, "Error %d: (%s)" % (e.errno, e.strerror)
	print >>sys.stderr, e
	syslog.syslog(syslog.LOG_ERR, str(e)) # log
	sys.exit(1)

#enter the main loop
mainloop = gobject.MainLoop()
mainloop.run()

