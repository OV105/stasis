#!/bin/sh -x 
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

#if [ ! -e ~/stasis ] ; then
#  mkdir ~/stasis
#fi

#if [ ! -e ~/stasis/conf ] ; then
#  mkdir ~/stasis/conf
#fi

if [ ! -e ${HOME}/stasis/conf ] ; then
   mkdir -p ${HOME}/stasis/conf
fi


if [ ! -e ${HOME}/stasis/examples ] ; then
   mkdir ${HOME}/stasis/examples
fi

cp * ${HOME}/stasis/examples
conf_file="${HOME}/stasis/conf/examples.conf"
echo "[examples]" > $conf_file
echo "search_paths=${HOME}/stasis/examples" >> $conf_file
echo "module_paths=${HOME}/stasis/examples" >> $conf_file
