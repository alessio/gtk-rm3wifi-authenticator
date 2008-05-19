#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of gtk-rm3wifi-authenticator
#
# gtk-rm3wifi-authenticator v0.5.0 - A small authenticator for wireless network of
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

import os, sys
from sgmllib import SGMLParser
import urllib, urllib2, pycurl
import threading

import locale, gettext

############# TRANSLATIONS SECTION

LOCALE_PATH = os.path.realpath(os.path.dirname(sys.argv[0])) + '/po'
locale.setlocale(locale.LC_ALL, '')

# register the gettext function for the whole interpreter as "_"
import __builtin__
__builtin__._ = gettext.gettext

############# END TRANSLATIONS SECTION

class ServerNotFoundException(Exception):
	message = _("Server not found or offline.")
class AccessDeniedException(Exception):
	message = _("Access denied! Wrong user name or password!")
class LogoutException(Exception):
	message = _("Logout failed.")
class InvalidNameOrPasswordException(Exception):
	message = _("Invalid name or password")
class AlreadyLoggedInException(Exception):
	message = _("You are already logged in")
class LoginException(Exception):
	message = _("Unknown exception during login")
	
class MyParser(SGMLParser):
	"""
	A simple parser for HTML documents.
	It searches for 'ID' field within a form.
	"""
	def reset(self):
		"""
		__init__() calls this
		"""
		SGMLParser.reset(self)
		self.logout_params = []
	def __url_to_params_list(self, url):
		params_list = []
		for p in url.partition('/login.pl?')[2].split(';'):
			k, v = p.split('=')
			params_list.append( (k, v) )
		return params_list
	def start_a(self, attrs):
		"""
		Parse <a> tag.
		"""
		for k in attrs:
			if k[0] == 'href' and 'action=logout' in k[1]:
				self.logout_url = k[1]
				self.logout_params = self.__url_to_params_list(k[1])
				break
	def get_logout_url(self):
		"""
		Return URL for logout.
		"""
		return self.logout_url
	def get_logout_params(self):
		"""
		Return logout params by URL.
		"""
		return self.logout_params

class WiFiAuthenticator:
	# Server URL for authentication
	# server_url = 'https://193.204.167.81:1234/'
	server_url = 'https://authentication.uniroma3.it'
	# Server URL (for logout)
	# server_logout_url = 'http://logout.wifi-uniroma3.it/'
	# User agent
	user_agent = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3"
	# Timeout
	connection_timeout = 8
	# Authentication progress
	states = {'send_username' : '1', 'send_password' : '2', 'get_authorization' : '3'}
	# Method
	authentication_methods = {'standard_sign-on' : '1', 'special_sign-on' : '2', 'sign-off' : '3'}
	# Success string (for login)
	login_success_string = 'per continuare con la navigazione'
	# Success string (for logout)
	logout_success_string = 'You have successfully logged out'
	# Downloaded page
	page_file = '/tmp/pagefile.html'
	
	def __init__(self):
		"""
		Class constructor.
		"""
		self.username = ''
		self.password = ''
		self.logout_url = ''
		self.logout_params = []
		self.autorelogin_thread = None
		self.relogin_timeout = 600.0
		self.relogin = True
		## CURL INITIALIZATION
		self.curl_object = pycurl.Curl()
		self.curl_object.setopt(pycurl.URL, self.server_url)
		self.curl_object.setopt(pycurl.USERAGENT, self.user_agent)
		self.curl_object.setopt(pycurl.SSL_VERIFYHOST, 0)
		self.curl_object.setopt(pycurl.SSL_VERIFYPEER, 0)
		# self.curl_object.setopt(pycurl.POST, 1)
		self.curl_object.setopt(pycurl.WRITEFUNCTION, self.__write_page)
	def __write_page(self, body):
		"""
		Writes download page into a file.
		"""
		f = open(self.page_file, 'w')
		f.write(body)
		f.close()
	def __read_page(self):
		"""
		Reads previously downloaded page and returns its content.
		"""
		f = open(self.page_file, 'r')
		content = f.read()
		f.close()
		return content
	def login(self):
		# _FORM_SUBMIT=1;which_form=reg;destination=;source=;error=;
		self.curl_object.setopt(pycurl.URL, self.server_url + '/login.pl')
		params = urllib.urlencode([
			('_FORM_SUBMIT', '1'),
			('which_form', 'reg'),
			('destination', ''),
			('source', ''),
			('error', ''),
			# ('action', 'login'),
			('bs_name', self.username),
			('bs_password', self.password)
		])
		self.curl_object.setopt(pycurl.POSTFIELDS, params)
		try:
			self.curl_object.perform()
		except:
			raise ServerNotFoundException, ServerNotFoundException.message

		data = self.__read_page()
		print data
		if data.find(self.login_success_string) == -1:
			if 'Invalid name or password' in data:
				raise InvalidNameOrPasswordException, InvalidNameOrPasswordException.message
			elif 'You are already logged in' in data:
				raise AlreadyLoggedInException, AlreadyLoggedInException.message
			else:
				raise LoginException, LoginException.message
		parser = MyParser()
		parser.feed(data)
		# Params for logout
		self.logout_params = parser.get_logout_params()
		self.logout_url = parser.get_logout_url()
		return 0
	def logout(self):
		"""
		Logout from the network.
		"""
		try:
			# self.curl_object.perform()
			# data = urllib.urlopen(self.server_url + urllib.urlencode(self.logout_params)).read()
			data = urllib2.urlopen(self.server_url + self.logout_url).read()
		except:
			raise ServerNotFoundException, ServerNotFoundException.message
		
		# data = self.__read_page()
		print(data)
		if data.find(self.logout_success_string) == -1:
			raise LogoutException, LogoutException.message
		
		return 0
	def start_autorelogin(self):
		"""
		Starts automatic relogin procedure.
		"""
		while self.relogin is True:
			# init new thread
			self.autorelogin_thread = threading.Timer(self.relogin_timeout, self.login)
			self.autorelogin_thread.start() # start new thread
			self.autorelogin_thread.join() # and wait until it's finished
		self.stop_autorelogin()
	def stop_autorelogin(self):
		self.autorelogin_thread.cancel()
	def set_username(self, username):
		"""
		Set username.
		"""
		self.username = username
	def set_password(self, password):
		"""
		Set password.
		"""
		self.password = password
	def set_method(self, method):
		"""
		Set authentication method.
		"""
		self.method = method
	def set_relogin_timeout(self, relogin_timeout):
		"""
		Set relogin timeout.
		"""
		self.relogin_timeout = relogin_timeout
	def set_relogin(self, relogin):
		"""
		Enable/Disable automatic relogin.
		"""
		self.relogin = relogin
