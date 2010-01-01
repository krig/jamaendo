#!/usr/bin/env python
#
# This file is part of Jamaendo.
# Copyright (c) 2010 Kristoffer Gronlund
#
# Jamaendo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jamaendo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jamaendo.  If not, see <http://www.gnu.org/licenses/>.
#
# Player code heavily based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)
#
import os
import simplejson

def string_in_file( filepath, string ):
    try:
        f = open( filepath, 'r' )
        found = f.read().find( string ) != -1
        f.close()
    except:
        found = False

    return found

def get_platform():
    if ( os.path.exists('/etc/osso_software_version') or
         os.path.exists('/proc/component_version') or
         string_in_file('/etc/issue', 'maemo') ):
        return 'maemo'
    else:
        return 'linux'

platform = get_platform()

def jsonprint(x):
    print simplejson.dumps(x, sort_keys=True, indent=4)

def find_resource(name):
    if os.path.isfile(os.path.join('data', name)):
        return os.path.join('data', name)
    elif os.path.isfile(os.path.join('/opt/jaemendo', name)):
        return os.path.join('/opt/jaemendo', name)
    elif os.path.isfile(os.path.join('/usr/share/jaemendo', name)):
        return os.path.join('/usr/share/jaemendo', name)
    else:
        return None

