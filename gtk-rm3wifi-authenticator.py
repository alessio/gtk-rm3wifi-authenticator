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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
from gtk.gdk import pixbuf_new_from_file
import os, sys, shelve, time, signal
import gobject, dbus, dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib
import thread, threading

from rm3wificommon import VERSION, LICENSE, VERBOSE_MODE, ABOUT_LOGO_SVG, GLADE_XML

#### CONNECTION TO DAEMON

def none():
	pass

bus = dbus.SessionBus()
try:
	print 'attempting to connect daemon...'
	proxy_obj = bus.get_object('org.factotum.daemon', '/org/factotum/daemon')
	print 'success'
except dbus.DBusException, e:
	print "Daemon is not running!"
	sys.exit(1)

daemon = dbus.Interface(proxy_obj, 'org.factotum.daemon')

#### END

class Configuration:
	""" User configuration wrapper. """
	MIN_RELOGIN_TIMEOUT = 1800.0
	file = 'rm3wifi.conf' # configuration file
	def __init__(self):
		Verboser.print_verbose_msg('Initializing configuration...')
		self.params = dict() # class initialization
		self.params['username'] = ''
		self.params['password'] = ''
		self.params['saveconfig'] = False
		self.params['relogin'] = False
		self.params['timeout'] = 1800.0
		Verboser.print_verbose_msg('Configuration initialized')

	def save_to_file(self):
		Verboser.print_verbose_msg('Saving configuration...')
		db = shelve.open(os.path.expandvars('$HOME') + '/' + self.file)
		db['params'] = self.params
		db.close()
		Verboser.print_verbose_msg('Configuration saved')
	def load_from_file(self):
		Verboser.print_verbose_msg('Try to loading configuration from file...')
		db = shelve.open(os.path.expandvars('$HOME') + '/' + self.file)
		try:
			temp = db['params']
			self.params = temp
		except:
			Verboser.print_verbose_msg("Config file doesn't exist!")
		Verboser.print_verbose_msg('Configuration loaded')
		db.close()

class Verboser:
	""" Print verbose messages """
	@staticmethod
	def print_verbose_msg(msg):
		if VERBOSE_MODE == True:
			print msg

class MainWindow:
	def showMessage(self, type, message_format):
		"""
		Create and show a message box.
		"""
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type, gtk.BUTTONS_CLOSE, message_format)
		md.show()
		Verboser.print_verbose_msg('A message dialog is appeared: %s' % message_format)
		response = md.run()
		if(response == gtk.RESPONSE_CLOSE):
			md.destroy()
		return response
	
	def __load_ui(self):
		"""
		Load user interface from a glade file.
		"""
		Verboser.print_verbose_msg("Loading GUI...")
		# load user interface glade file
		self.ui_XML = gtk.glade.XML(GLADE_XML)
		self.window = self.ui_XML.get_widget('MainWindow')
		# destroy and delete events
		self.window.connect("destroy", lambda wid: gtk.main_quit())
		self.window.connect("delete_event", lambda a1,a2:gtk.main_quit())

		# UI elements initialization		
		self.username_entry = self.ui_XML.get_widget('username_entry')
		self.password_entry = self.ui_XML.get_widget('password_entry')
		self.relogin_entry = self.ui_XML.get_widget('relogin_entry')
		self.saveconfig_checkbutton = self.ui_XML.get_widget('saveconfig_checkbutton')
		self.relogin_togglebutton = self.ui_XML.get_widget('relogin_togglebutton')

		# Messages handlers
		message_map = {
			'on_login_button_clicked' : self.on_login_button_clicked,
			'on_about_button_clicked' : self.on_about_button_clicked,
			'on_quit_button_clicked' : self.on_quit_button_clicked,
			'on_saveconfig_checkbutton_toggled' : self.on_saveconfig_checkbutton_toggled,
			'on_relogin_togglebutton_toggled' : self.on_relogin_togglebutton_toggled,
			'on_username_entry_changed' : self.on_username_entry_changed,
			'on_password_entry_changed' : self.on_password_entry_changed,
			'on_relogin_entry_changed' : self.on_relogin_entry_changed
		}
		self.ui_XML.signal_autoconnect(message_map)

		# SHOW THEM ALL!!
		self.window.show_all()
		Verboser.print_verbose_msg("GUI loaded")
	def __load_configuration(self):
		"""
		Load user configuration.
		"""
		# open the configuration file		
		self.config = Configuration()
		self.config.load_from_file()

		self.username_entry.set_text(self.config.params['username'])
		self.password_entry.set_text(self.config.params['password'])
		self.saveconfig_checkbutton.set_active(self.config.params['saveconfig'])
		self.relogin_togglebutton.set_active(self.config.params['relogin'])
		self.relogin_entry.set_text(str(self.config.params['timeout']))

	def __save_configuration(self):
		"""
		Save to file user configuration.
		"""
		self.config.save_to_file()

	def __init__(self):
		"""
		Constructor.
		"""
		# Attributes
		self.config = None
		self.ui_XML = None


		self.__load_ui()
		# os.chdir(os.path.expandvars('$HOME'))
		self.__load_configuration()

	def on_username_entry_changed(self, widget, data=None):
		self.config.params['username'] = self.username_entry.get_text()
	def on_password_entry_changed(self, widget, data=None):
		self.config.params['password'] = self.password_entry.get_text()
	def on_interface_entry_changed(self, widget, data=None):
		self.config.params['interface'] = self.interface_entry.get_text()
	def on_relogin_entry_changed(self, widget, data=None):
		self.config.params['timeout'] = float(self.relogin_entry.get_text())
	def on_relogin_togglebutton_toggled(self, widget, data=None):
		self.config.params['relogin'] = self.relogin_togglebutton.get_active()
	def on_saveconfig_checkbutton_toggled(self, widget, data=None):
		self.config.params['saveconfig'] = self.saveconfig_checkbutton.get_active()
	def on_login_button_clicked(self, widget):
		""" Do the login """
		daemon_method = daemon.login # daemon asynchronous method
		# set username and password
		daemon.set_username(self.config.params['username'])
		daemon.set_password(self.config.params['password'])
		# do the authentication
		daemon_method(reply_handler = self.handle_reply, error_handler = self.handle_error)
		# do autorelogin
		while self.config.params['relogin'] == True and self.config.params['relogin_timeout'] >= self.config.MIN_RELOGIN_TIMEOUT:
			t = threading.Timer(self.config.params['relogin_timeout'], daemon_method, kwargs = { 'reply_handler' : self.handle_reply, 'error_handler' : self.handle_error})
			t.start()
			
	def handle_reply(self, r):
		"""
		Daemon methods replies handler.
		"""
		self.showMessage(gtk.MESSAGE_INFO, "Success: Operation successfully terminated")
	def handle_error(self, e):
		"""
		Daemon methods exceptions handler.
		"""
		self.showMessage(gtk.MESSAGE_ERROR, str(e))

	def on_quit_button_clicked(self, widget):
		"""
		Exit.
		"""
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Are you sure?")
		md.show()
		response = md.run()
		if(response == gtk.RESPONSE_NO):
			md.destroy()
		else:
			if self.saveconfig_checkbutton.get_active() == True:
				self.__save_configuration()
				Verboser.print_verbose_msg("Quitting...")
			gtk.main_quit()
	def on_about_button_clicked(self,widget,data=None):
		"""
		Create and show an about dialog.
		"""		
		ad = gtk.AboutDialog()
		ad.set_name('GTK Rm3WiFi Authenticator')
		ad.set_version(VERSION)
		ad.set_copyright('Copyright © 2008 Alessio Treglia')
		ad.set_authors(['Alessio Treglia <quadrispro@ubuntu-it.org>'])
		ad.set_documenters = (['Not implemented yet'])
		ad.set_comments('gtk-rm3wifi-authenticator is a small authenticator for wireless network of University of RomaTre')
		ad.set_website = ('http://www.quadrispro.netsons.org/gtk-rm3wifi-factotum')
		ad.set_website_label = ('Website')
		# ad.set_logo = (pixbuf_new_from_file(ABOUT_LOGO_SVG))
		ad.set_license(LICENSE)
		response = ad.run()
		Verboser.print_verbose_msg('About dialog is appeared')
		ad.destroy()

if __name__ == "__main__":
	w = MainWindow()
	gtk.main()
