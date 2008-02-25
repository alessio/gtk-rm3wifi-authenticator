#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of gtk-rm3wifi-authenticator
#
# gtk-rm3wifi-authenticator v0.4.0 - A small authenticator for wireless network of
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

from ConfigParser import ConfigParser

from rm3wificommon import VERSION, LICENSE, VERBOSE_MODE, ABOUT_LOGO_SVG, GLADE_XML, CONFIG_FILENAME

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
	CONFIG_SECTION_NAME = 'Config'
	file = CONFIG_FILENAME # configuration file
	def __init__(self):
		Verboser.print_verbose_msg('Initializing configuration...')
		self.cp = ConfigParser()
		self.params = dict() # class initialization
		Verboser.print_verbose_msg('Configuration initialized')
		
	def setdefaults(self):
		self.params['username'] = ''
		self.params['password'] = ''
		self.params['saveconfig'] = False
		self.params['relogin'] = False
		self.params['timeout'] = 1800.0
		Verboser.print_verbose_msg('Configuration set to default values')

	def save_to_file(self):
		config_file = file(os.path.expandvars('$HOME') + '/' + CONFIG_FILENAME, 'w')
		Verboser.print_verbose_msg('Saving configuration...')
		# if there's no section called [Config], create one
		if self.cp.has_section(self.CONFIG_SECTION_NAME) == False:
			self.cp.add_section(self.CONFIG_SECTION_NAME)
		# store each option
		for k, v in self.params.items():
			self.cp.set(self.CONFIG_SECTION_NAME, k, str(v))
		# write to file
		self.cp.write(config_file)
		
		# db = shelve.open(os.path.expandvars('$HOME') + '/' + self.file)
		# db['params'] = self.params
		# db.close()
		Verboser.print_verbose_msg('Configuration saved')
	def load_from_file(self):
		Verboser.print_verbose_msg('Try to loading configuration from file...')
		self.cp.read(os.path.expandvars('$HOME') + '/' + CONFIG_FILENAME)
		if self.cp.sections() == []:
		#db = shelve.open(os.path.expandvars('$HOME') + '/' + self.file)
		#try:
		#	temp = db['params']
		#	self.params = temp
		#except:
			Verboser.print_verbose_msg("Config file doesn't exist!")
			raise Exception, "Configuration file not found"
		# set config params
		self.params['username'] = self.cp.get(self.CONFIG_SECTION_NAME, 'username')
		self.params['password'] = self.cp.get(self.CONFIG_SECTION_NAME, 'password')
		self.params['saveconfig'] = self.cp.getboolean(self.CONFIG_SECTION_NAME, 'saveconfig')
		self.params['relogin'] = self.cp.getboolean(self.CONFIG_SECTION_NAME, 'relogin')
		self.params['timeout'] = self.cp.getfloat(self.CONFIG_SECTION_NAME, 'timeout')
		Verboser.print_verbose_msg('Configuration loaded')
		#db.close()
		

class Verboser:
	""" Print verbose messages """
	@staticmethod
	def print_verbose_msg(msg):
		if VERBOSE_MODE == True:
			print msg

class AppStatusIcon(gtk.StatusIcon):
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
	def __init__(self):
		gtk.StatusIcon.__init__(self)
		menu = '''
			<ui>
			<menubar name="Menubar">
			<menu action="Menu">
			<menuitem action="Login"/>
			<separator/>
			<menuitem action="About"/>
			<menuitem action="Quit"/>
			</menu>
			</menubar>
			</ui>
		'''
		
		actions = [
			('Menu',  None, 'Menu'),
			('Login', gtk.STOCK_CONNECT, '_Login...', None, 'Login to network', self.on_login),
			('About', gtk.STOCK_ABOUT, '_About...', None, 'About gtk-rm3wifi-authenticator', self.on_about),
			('Quit',gtk.STOCK_QUIT,'_Quit', None, 'Quit gtk-rm3wifi-authenticator',
			self.on_quit),
		]
		
		ag = gtk.ActionGroup('Actions')
		ag.add_actions(actions)
		self.manager = gtk.UIManager()
		self.manager.insert_action_group(ag, 0)
		self.manager.add_ui_from_string(menu)
		self.menu = self.manager.get_widget("/Menubar/Menu/About").props.parent
		self.current_icon_path = ''
		self.set_from_file("images/gtk-rm3wifi-authenticator.png")
		self.set_visible(True)
		self.connect('popup-menu', self.on_popup_menu)
		self.connect('activate', self.on_activate)
		self.set_tooltip('Initializing gtk-rm3wifi-authenticator...')

		self.config = Configuration()
		self.__load_configuration()
		
		self.preferences_dialog = PreferencesDialog()
		self.preferences_dialog.set_configuration(self.config)

		# self.preferences_dialog_shown = False

	def __load_configuration(self):
		"""
		Load user configuration.
		"""
		# open the configuration file
		try:
			self.config.load_from_file()
		except Exception, e:
			self.config.setdefaults()
			self.config.save_to_file()
	def __save_configuration(self):
		"""
		Save to file user configuration.
		"""
		self.config.save_to_file()
		
	def on_activate(self, data):
		self.preferences_dialog.activate()
		# if self.preferences_dialog_shown is False:
			# self.preferences_dialog_shown = True
			# self.preferences_dialog.run()
			# if response == gtk.RESPONSE_CLOSE:
			# self.preferences_dialog.hide()
			# self.preferences_dialog_shown = False
		# else:
			# self.preferences_dialog_shown = False
			# TODO
			# self.preferences_dialog.hide()
	def on_popup_menu(self, status, button, time):
		self.menu.popup(None, None, None, button, time)
	def on_login(self, widget):
		""" Do the login """
		daemon_method = daemon.login # daemon's login method
		# set username and password
		daemon.set_username(self.config.params['username'])
		daemon.set_password(self.config.params['password'])
		daemon.set_relogin_timeout(self.config.params['timeout'])
		# do the authentication
		if self.config.params['relogin'] is True:
			daemon.start_autorelogin()
	def handle_reply(self, r):
		"""
		Daemon methods replies handler.
		"""
		self.showMessage(gtk.MESSAGE_INFO, "Success: Operation successfully terminated")
	def handle_error(self, e):
		"""
		Daemon method exceptions handler.
		"""
		self.showMessage(gtk.MESSAGE_ERROR, str(e))
	def on_about(self, data):
		pass
	def on_quit(self, data):
		"""
		Exit.
		"""
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Are you sure?")
		md.show()
		response = md.run()
		if(response == gtk.RESPONSE_NO):
			md.destroy()
		else:
			Verboser.print_verbose_msg("Quitting...")
			self.preferences_dialog.hide()
			self.__save_configuration()
			gtk.main_quit()

class PreferencesDialog:
	def __init__(self):
		self.ui_XML = gtk.glade.XML(GLADE_XML)
		self.dialog = self.ui_XML.get_widget('PreferencesDialog')
		
		# destroy and delete events
		self.dialog.connect("destroy", self.on_close)
		self.dialog.connect("delete_event", self.on_close)
		
		# UI elements initialization		
		self.username_entry = self.ui_XML.get_widget('dialog_username_entry')
		self.password_entry = self.ui_XML.get_widget('dialog_password_entry')
		self.relogin_entry = self.ui_XML.get_widget('dialog_relogin_entry')
		self.relogin_togglebutton = self.ui_XML.get_widget('dialog_relogin_togglebutton')

		self.config = Configuration()

		# Messages handlers
		message_map = {
			'on_dialog_relogin_togglebutton_toggled' : self.on_relogin_togglebutton_toggled,
			'on_dialog_username_entry_changed' : self.on_username_entry_changed,
			'on_dialog_password_entry_changed' : self.on_password_entry_changed,
			'on_dialog_relogin_entry_changed' : self.on_relogin_entry_changed,
			'on_dialog_close_button_clicked' : self.on_close
		}
		self.ui_XML.signal_autoconnect(message_map)
		self.is_shown = False
	def set_configuration(self, config):
		self.config = config
		self.username_entry.set_text(self.config.params['username'])
		self.password_entry.set_text(self.config.params['password'])
		self.relogin_togglebutton.set_active(self.config.params['relogin'])
		self.relogin_entry.set_text(str(self.config.params['timeout']))
	def on_username_entry_changed(self, widget, data=None):
		self.config.params['username'] = self.username_entry.get_text()
	def on_password_entry_changed(self, widget, data=None):
		self.config.params['password'] = self.password_entry.get_text()
	def on_relogin_entry_changed(self, widget, data=None):
		self.config.params['timeout'] = float(self.relogin_entry.get_text())
	def on_relogin_togglebutton_toggled(self, widget, data=None):
		self.config.params['relogin'] = bool(self.relogin_togglebutton.get_active())
		daemon.set_relogin(self.config.params['relogin'])
	def activate(self):
		if self.is_shown is False:
			self.run()
		else:
			self.hide()
	def on_close(self, widget, data=None):
		self.hide()
	def hide(self):
		self.dialog.hide()
		self.is_shown = False
	def run(self):
		self.is_shown = True
		self.dialog.run()
	def show(self):
		self.dialog.show()

if __name__ == "__main__":
	a = AppStatusIcon()
	gtk.main()
	sys.exit(0)
