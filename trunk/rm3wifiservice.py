#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of gtk-rm3wifi-authenticator
#
# gtk-rm3wifi-authenticator v0.3.8 - A small authenticator for wireless network of
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
import urllib, pycurl
import threading

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
		self.session_id = ''
	def start_input(self, attrs):
		"""
		Parse <input> tag.
		"""
		# print attrs
		for k in attrs:
			if k[0] == 'name' and k[1] == 'ID' and self.session_id == '':
				self.session_id = attrs[attrs.index(k)+1][1]
		# print self.session_id
	def get_session_id(self):
		"""
		Return session ID.
		"""
		return self.session_id

class WiFiAuthenticator:
	# Server URL for authentication
	server_url = 'https://193.204.167.81:1234/'
	# User agent
	user_agent = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.3) Gecko/20070309 Firefox/2.0.0.3"
	# Timeout
	connection_timeout = 8
	# Authentication progress
	states = {'send_username' : '1', 'send_password' : '2', 'get_authorization' : '3'}
	# Method
	authentication_methods = {'standard_sign-on' : '1', 'special_sign-on' : '2', 'sign-off' : '3'}
	# Success string
	success_string = "User authorized"
	# Downloaded page
	page_file = '/tmp/pagefile.html'
	
	def __init__(self):
		"""
		Class constructor.
		"""
		self.username = ''
		self.password = ''
		self.session_id = ''
		self.method = 'standard_sign-on'
		self.autorelogin_thread = None
		## CURL INITIALIZATION
		self.curl_object = pycurl.Curl()
		self.curl_object.setopt(pycurl.URL, self.server_url)
		self.curl_object.setopt(pycurl.USERAGENT, self.user_agent)
		self.curl_object.setopt(pycurl.SSL_VERIFYHOST, 0)
		self.curl_object.setopt(pycurl.SSL_VERIFYPEER, 0)
		self.curl_object.setopt(pycurl.WRITEFUNCTION, self.__write_page)
	def __encode_data(self, **data):
		"""
		Useful to convert dictionary to POST request string.
		"""
		return urllib.urlencode(data)
		
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
	def __send_username(self):
		"""
		First step of authentication procedure.
		"""
		params = urllib.urlencode([('ID', self.session_id),('STATE', self.states['send_username']),('DATA',self.username)])
		self.curl_object.setopt(pycurl.POSTFIELDS, params)
		self.curl_object.perform()
	def __send_password(self):
		"""
		Second step of authentication procedure.
		"""
		params = urllib.urlencode([('ID', self.session_id),('STATE', self.states['send_password']),('DATA',self.password)])
		self.curl_object.setopt(pycurl.POSTFIELDS, params)
		self.curl_object.perform()
	def __get_authorization(self):
		"""
		Third and last step of authentication procedure.
		Check if everything was done right.
		"""
		params = urllib.urlencode([('ID', self.session_id),('STATE', self.states['get_authorization']),('DATA',self.authentication_methods[self.method])])
		# params = self.__encode_data(ID=self.session_id, STATE=self.states['get_authorization'], DATA=self.authentication_methods[self.method])
		self.curl_object.setopt(pycurl.POSTFIELDS, params)
		self.curl_object.perform()
	def start_session(self):
		"""
		Start a new session and return current ID.
		"""
		try:
			self.curl_object.perform()
		except:
			raise Exception, "Server not found or offline."
		data = self.__read_page()
		p = MyParser()
		p.feed(data)
		p.close()
		self.session_id = p.get_session_id()
		
		return self.session_id
	def authorize(self):
		"""
		Send username and password and try to get authorization.
		"""
		self.start_session()
		self.__send_username()
		self.__send_password()
		self.__get_authorization()
		
		data = self.__read_page()
		
		if data.find('User authorized') == -1:
			raise Exception, "Access denied! Wrong user name or password!"
		return 0
	def start_autorelogin(self, interval):
		self.autorelogin_thread = threading.Timer(interval, self.authorize)
		# TODO LOOP
		t.start()
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
