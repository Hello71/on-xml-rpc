#!/usr/bin/env python

# Copyright 2014 Alex Xu (Hello71)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import six
from six.moves import configparser, xmlrpc_client
import readline
import code
import sys
import traceback

class ONProxy(xmlrpc_client.ServerProxy):
    """Like ServerProxy but injects a "session string"."""
    def __init__(self, uri, one_auth, *args):
        self.one_auth = one_auth
        return super().__init__(uri, *args)

    def __request(self, methodname, params):
        if methodname.startswith('one.'):
            params = (self.one_auth,) + params
        return super()._ServerProxy__request(methodname, params)

    def __getattr__(self, name):
        return xmlrpc_client._Method(self.__request, name)

class ONInterpreter(code.InteractiveInterpreter):
    """Like InteractiveInterpreter but injects 'proxy.' if there is a NameError
    on the first column. For obvious reasons one should ensure that proxy is
    defined in the local scope."""
    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False
        if code is None:
            return True
        self.runcode(code, source)
        return False

    def runcode(self, code, source):
        try:
            exec(code)
        except SystemExit:
            raise
        except NameError:
            # dark magic
            if not source.startswith('proxy.') and traceback.extract_tb(sys.exc_info()[2])[-1] == ('<console>', 1, '<module>', None):
                self.runsource("proxy." + source)
            else:
                self.showtraceback()
        except:
            self.showtraceback()

class ONConsole(code.InteractiveConsole, ONInterpreter):
    """Exactly the same as InteractiveConsole but uses ONInterpreter instead."""
    def __init__(self, locals=None, filename="<console>"):
        ONInterpreter.__init__(self, locals)
        self.filename = filename
        self.resetbuffer()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('xml_rpc.ini')
    sec = config['xml_rpc']
    user = sec['user']
    password = sec['password']
    server = sec['server']

    proxy = ONProxy(server, "%s:%s" % (user, password))
    banner = "Using server %s as user %s\n(OpenNebula console)" % (server, user)
    ONConsole().interact(banner=banner)
