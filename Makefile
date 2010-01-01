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

PREFIX ?= /usr
DESTDIR ?= /

JAMAENDOBIN = scripts/jamaendo
JAMAENDOVERSION = `grep -m 1 VERSION jamaui/ui.py | cut -d "'" -f 2`
#MESSAGESPOT = data/messages.pot


PYTHON ?= /usr/bin/python2.5

all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    distclean - remove build files + dist target"

install: python-install post-install install-schemas

python-install:
	$(PYTHON) setup.py install --optimize 2 --root=$(DESTDIR) --prefix=$(PREFIX)

post-install:
	gtk-update-icon-cache -f -i $(DESTDIR)$(PREFIX)/share/icons/hicolor/
	update-desktop-database $(DESTDIR)$(PREFIX)/share/applications/

clean:
	rm -rf build
	rm -f jamaendo/*.pyc jamaendo/*.pyo
	rm -f jamaui/*.pyc jamaui/*.pyo
#	make -C data/po clean

distclean: clean
	rm -rf dist

# See: http://wiki.maemo.org/Uploading_to_Extras#Debian_tooling
build-package:
	dpkg-buildpackage -rfakeroot -sa -i -I.git

#messagespot:
#	xgettext -k_ --from-code utf-8 --language Python \
#	  -o $(MESSAGESPOT) scripts/jamaendo jamaendo/*.py jamaui/*.py
#	sed -i \
#	  -e 's/SOME DESCRIPTIVE TITLE/Jamaendo translation template/g' \
#	  -e 's/THE PACKAGE'"'"'S COPYRIGHT HOLDER/Jamaendo Contributors/g' \
#	  -e 's/YEAR/2010/g' \
#	  -e 's/FIRST AUTHOR <EMAIL@ADDRESS>/Nick Nobody <me@nikosapi.org>/g' \
#	  -e 's/PACKAGE VERSION/Jamaendo '$(JAMAENDOVERSION)'/g' \
#	  -e 's/-Bugs-To: /-Bugs-To: kegie+jamaendo@ovi.com/g' \
#	  -e 's/PACKAGE/Jamaendo/g' $(MESSAGESPOT)

#gen_gettext: messagespot
#	make -C data/po generators
#	make -C data/po update
