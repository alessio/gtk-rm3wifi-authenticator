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

from distutils.core import setup

from rm3wificommon import VERSION, SHORT_APPNAME

setup(name = SHORT_APPNAME,
      version = VERSION,
      description = 'Small authenticator for wireless network of University of RomaTre',
      author = 'Alessio Treglia',
      author_email = 'quadrispro@ubuntu-it.org',
      url = 'https://code.google.com/p/gtk-rm3wifi-authenticator',
      license = 'GNU GPL 3',
      requires = ["pygtk", "gtk", "pycurl"],
      platform = ["Platform independent"],
#      scripts = ['gtk-rm3wifi-authenticator'],
      packages = ['.'],
      package_data = {'' : ['glade/*', 'po/*/LC_MESSAGES/*.mo', 'images/*', 'misc/*']},
      data_files = [('share/pixmaps', ['images/gtk-rm3wifi-authenticator.png']),
                    ('share/icons/hicolor/scalable/apps', ['images/gtk-rm3wifi-authenticator.svg']),
                    ('share/applications',['misc/gtk-rm3wifi-authenticator.desktop']),
                    ('bin',['gtk-rm3wifi-authenticator']),
                    ('share/gtk-rm3wifi-authenticator/glade',['glade/gtk-rm3wifi-authenticator.glade'])])

