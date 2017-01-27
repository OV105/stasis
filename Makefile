
###############################################################################
#
# Copyright (c) 2009 Novell, Inc.
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public License 
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact Novell, Inc.
#
# To contact Novell about this file by physical or electronic mail,
# you may find current contact information at www.novell.com
#
###############################################################################
# stasis *development* Makefile
NAME="stasis"

all:
	python setup.py build_ext --inplace

install:
	python setup.py install

clean:
	python setup.py clean
	rm -f MANIFEST
	rm -f stasis_default.conf *~
	rm -rf build dist rpms 
	find . -name '*.pyc' -exec rm {} \;

# Dollar signs must be escaped with dollar signs in variables.
export camelCAPS='[a-z_][a-zA-Z0-9_]*$$'
export StudlyCaps='[a-zA-Z_][a-zA-Z0-9_]*$$'
export NAME=`python setup.py --name`
check:
	#pylint --indent-string="	" --class-rgx=${StudlyCaps} --function-rgx=${camelCAPS} --method-rgx=${camelCAPS} --variable-rgx=${camelCAPS} --argument-rgx=${camelCaps} dogtail sniff/sniff examples/*.py

tarball:
	python setup.py sdist

rpm_prep: tarball
	mkdir -p rpms/{BUILD,RPMS/noarch,SOURCES,SPECS,SRPMS}
	# Create an rpmrc that will include our custom rpmmacros file
	echo "%_topdir `pwd`/rpms/" > rpms/tmp.rpmmacros
	echo "macrofiles: /usr/lib/rpm/macros:/usr/lib/rpm/%{_target}/macros:/etc/rpm/macros.*:/etc/rpm/macros:/etc/rpm/%{_target}/macros:~/.rpmmacros:`pwd`/rpms/tmp.rpmmacros" > rpms/tmp.rpmrc

rpm: rpm_prep
	# Build using the custom rpmrc in the rpms/ sub-dir
	rpmbuild -vv --rcfile /usr/lib/rpm/rpmrc:`pwd`/rpms/tmp.rpmrc  -tb dist/${NAME}-*.tar.gz
	# Move the source and binary RPMs to dist/
	find rpms/RPMS -name "*.rpm" -exec mv '{}' dist \;
	#rm -rf rpms/

srpm: rpm_prep
	# Build using the custom rpmrc in the rpms/ sub-dir
	rpmbuild -vv --rcfile /usr/lib/rpm/rpmrc:`pwd`/rpms/tmp.rpmrc  -ts dist/${NAME}-*.tar.gz
	# Move the source and binary RPMs to dist/
	find rpms/SRPMS -name "*.rpm" -exec mv '{}' dist \;
	rm -rf rpms/

deb:
	fakeroot debian/rules clean
	dpkg-buildpackage -rfakeroot -us -uc

