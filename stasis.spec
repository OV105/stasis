
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
#
# spec file for package stasis
#
# Copyright (c) 2006 Novell Inc., Waltham, MA
# This file and all modifications and additions to the pristine
# package are under the same license as the package itself.
#
# Please submit bug fixes or comments via http://www.novell.com
#

# norootforbuild

BuildRequires: python-devel 

Name:         stasis 
License:      GPL 
Group:        Development/Tools/Other
Autoreqprov:  on
Version:      1.0
Release:      0
Summary:      An automated test framework written in Python 
Url:          http://www.novell.com
Source:       %{name}-%{version}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-devel
Requires: python >= 2.4

%description
stasis is a frame work for automating the execution of test cases. 
 
%prep 
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%setup  

%build
python ./setup.py build

%install
#rm -rf $RPM_BUILD_ROOT
python ./setup.py install -O2 --prefix="/usr" --root=$RPM_BUILD_ROOT --record=%{name}.installed
sed -e 's/\.[0-9]$/&\*/' < %{name}.installed > %{name}.files


%clean
#rm -rf $RPM_BUILD_ROOT

%files -f %{name}.files
%defattr(-,root,root,-)
/etc/stasis
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}/xsd

%post
%{_bindir}/configure-stasis

%changelog


