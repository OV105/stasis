# -*- coding: utf-8 -*-
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
# PLEASE DO NOT USE ANY OLD TEXT EDITOR TO EDIT THIS FILE.  The Unicode strings
# below may be screwed up as a result.  Editors known to work at this time are
# gedit (part of the standard GNOME distribution) and TextWrangler (for Mac).  Text
# editors known NOT to work are emacs, vi, and nano.  Sorry for the inconvenience!
#

import re

I18N_TEST_STRINGS = {'european': u'english-español-русский-română-Ελληνικά',
                     'asian': u'日本語-汉语-한국',
                     'rtl': u'עברית-عربية-𐠃𐠌𐠎',
                     'indic': u'ॐoॢ॰-ঔঙলoি-वेंकटाचलपत-ਰੋਕਰਹਿਤ-ઑખફૐ-ప్రజావాక్కు-ಮತ್ತು-ടെലിവിഷന്',
                     'asian_unsupported': u'རིན་ཆེན་སྡེ-ꁧꀏꂾꆏꑌꑿꎿꇁꃲ-ᠰᡳᠩᡤᡝᡵᡳ-ᠬᠤᠯᠤᠭᠠᠨᠠ-โดยพื้นฐานแล้ว-ການ​ຂ້າ​ຜີ​ຂອງ​ເຜົ່າ​ກະ​ຕູ-မဟာဓမ',
                     'nonlingual': u'𝄞𝄢𝅘𝅥𝅯𝄜-⟴⟳⟿⟽-⠋⠏⣗-⨌	⨊⨚⨦⨷⪻'
                     }

USE_I18N_TEST_STRINGS = ['european', 'asian']

def i18nize(instring):
    """Take a string and return a list of strings with selected i18n string substituted

    Any substring enclosed by {} will be substituted. 'a {b} c' becomes 'a b-עברית-عربية- c' """
    # if string is not ready for i18nization, just return it once
    if instring.find('{') == -1:
        return [instring]
    # otherwise, i18nize it
    outstrings = []
    outstrings.append(re.sub(r'{([^}]*)}', r'\1', instring))
    if USE_I18N_TEST_STRINGS:
        for teststr in USE_I18N_TEST_STRINGS:
            outstrings.append(re.sub(r'{([^}]*)}', r'\1-%s' % I18N_TEST_STRINGS[teststr], instring))
    return outstrings

def getI18nKeys():
	return I18N_TEST_STRINGS.keys()
