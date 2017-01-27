
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
"""Library for exceptions for stasis
"""

import re
import commands


## exceptions
##
class StasisException(Exception):
    #base class for Stasis exceptions
    __name__ = "StasisException"
    pass

class AbstractMethod(StasisException):
    __name__ = "AbstractMethod"
    pass

class IncorrectArgument(StasisException):
    __name__ = "IncorrectArgument"
    pass

class EncodingError(StasisException):
    __name__ = "EncodingError"
    pass

class TestopiaError(StasisException):
    __name__ = "TestopiaError"
    pass

class FactoryError(StasisException):
    __name__ = "FactoryError"
    pass

class NoSourceHandlerFound(StasisException):
    __name__ = "NoSourceHandlerFound"
    pass

class SysInfoError(StasisException):
    __name__ = "SysInfoError"
    pass

class TestError(StasisException):
    __name__ = "TestError"
    pass

class TestNotImplemented(StasisException):
    __name__ = "TestNotImplemented"
    pass

#class TimeOutException(StasisException):
#    pass

class XMLValidationError(StasisException):
    __name__ = "XMLValidationError"
    pass

class FileNotFound(StasisException):
    __name__ = "FileNotFound"
    pass

class ParamTypeError(StasisException):
    __name__ = "ParamTypeError"
    pass

class MissingParameter(StasisException):
    __name__ = "MissingParameter"
    pass


""" Assertion functions - use these to make assertions in python type 
    source blocks"""

class AssertionFailure(Exception):
    pass

class AssertEqualsFailure(AssertionFailure):
    pass

class AssertNotEqualsFailure(AssertionFailure):
    pass

class AssertMatchFailure(AssertionFailure):
    pass

class AssertNotMatchFailure(AssertionFailure):
    pass

class AssertCommandFailure(AssertionFailure):
    pass


def assert_equals(x, y, error="", cmd=""):
    if x <> y:
        e = error
        e += " (%s != %s)" % (x, y)
        if cmd:
            e += " COMMAND: " + cmd
        raise AssertEqualsFailure, e


def assert_not_equals(x, y, error="", cmd=""):
    if x == y:
        e = error
        e += " (%s == %s)" % (x, y)
        if cmd:
            e += " COMMAND: " + cmd
        raise AssertEqualsFailure, e


def assert_match(expected, actual, error="", cmd=""):
    match = re.search(unicode(expected), unicode(actual), re.MULTILINE)
    if not match:
        e = error
        e += ' EXPECTED: "%s" ACTUAL: "%s"' % (expected, actual)
        if cmd:
            e += " COMMAND: " + cmd
            
        raise AssertMatchFailure, e


def assert_not_match(expected, actual, error="", cmd=""):
    match = re.search(unicode(expected), unicode(actual), re.MULTILINE)
    if match:
        e = error
        e += ' DID NOT EXPECT: "%s" ACTUAL: "%s"' % (expected, actual)
        if cmd:
            e += " COMMAND: " + cmd

        raise AssertNotMatchFailure, e


def assert_command(cmd, expected_status, output_match, error="",
                   inversed_match=0):
    """Run specified command, asserting status and output

    cmd - the command to run
    status - the expected retval when running the command
    output - a regular expression defining the matching output
    inversed_match - expect to NOT find output_match
    """
    status, output = commands.getstatusoutput(cmd)
    
    if status <> expected_status:
        msg = 'unexpected status! EXPECTED: "%s" | ACTUAL: "%s" | COMMAND: "%s" | OUTPUT: "%s"' %\
              (expected_status, status, cmd, output)
        raise AssertCommandFailure, msg

    match = re.search(unicode(output_match), unicode(output), re.MULTILINE)
    if not match:
        msg = 'unexpected output! EXPECTED: "%s" | ACTUAL: "%s" | COMMAND: "%s"' %\
              (output_match, output, cmd)
        raise AssertCommandFailure, msg

# vim: set et sw=4 ts=4 :
