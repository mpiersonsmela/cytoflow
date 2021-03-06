#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Utilities for opening files or URLs in the registered default application
and for sending e-mail using the user's preferred composer.

From http://code.activestate.com/recipes/511443-cross-platform-startfile-and-mailto-functions/
'''

__version__ = '1.1'
__all__ = ['mailto']

import os
import sys
import webbrowser
import subprocess
import stat

from email.utils import encode_rfc2231

_controllers = {}
_open = None

# the following three definitions were copied out of the python 2.7 webbrowser
# library.

if sys.platform[:3] == "win":
    def _isexecutable(cmd):
        cmd = cmd.lower()
        if os.path.isfile(cmd) and cmd.endswith((".exe", ".bat")):
            return True
        for ext in ".exe", ".bat":
            if os.path.isfile(cmd + ext):
                return True
        return False
else:
    def _isexecutable(cmd):
        if os.path.isfile(cmd):
            mode = os.stat(cmd)[stat.ST_MODE]
            if mode & stat.S_IXUSR or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
                return True
        return False


def _iscommand(cmd):
    """Return True if cmd is executable or can be found on the executable
    search path."""
    if _isexecutable(cmd):
        return True
    path = os.environ.get("PATH")
    if not path:
        return False
    for d in path.split(os.pathsep):
        exe = os.path.join(d, cmd)
        if _isexecutable(exe):
            return True
    return False




class BaseController(object):
    '''Base class for open program controllers.'''

    def __init__(self, name):
        self.name = name

    def _open(self, filename):
        raise NotImplementedError


class Controller(BaseController):
    '''Controller for a generic open program.'''

    def __init__(self, *args):
        super(Controller, self).__init__(os.path.basename(args[0]))
        self.args = list(args)

    def _invoke(self, cmdline):
        if sys.platform[:3] == 'win':
            closefds = False
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            closefds = True
            startupinfo = None

        if (os.environ.get('DISPLAY') or sys.platform[:3] == 'win' or
                                                    sys.platform == 'darwin'):
            inout = open(os.devnull, 'r+')
        else:
            # for TTY programs, we need stdin/out
            inout = None

        # if possible, put the child precess in separate process group,
        # so keyboard interrupts don't affect child precess as well as
        # Python
        setsid = getattr(os, 'setsid', None)
        if not setsid:
            setsid = getattr(os, 'setpgrp', None)

        pipe = subprocess.Popen(cmdline, stdin=inout, stdout=inout,
                                stderr=inout, close_fds=closefds,
                                preexec_fn=setsid, startupinfo=startupinfo)

        # It is assumed that this kind of tools (gnome-open, kfmclient,
        # exo-open, xdg-open and open for OSX) immediately exit after lauching
        # the specific application
        returncode = pipe.wait()
        if hasattr(self, 'fixreturncode'):
            returncode = self.fixreturncode(returncode)
        return not returncode

    def _open(self, filename):
        if isinstance(filename, str):
            cmdline = self.args + [filename]
        else:
            # assume it is a sequence
            cmdline = self.args + filename
        try:
            return self._invoke(cmdline)
        except OSError:
            return False


# Platform support for Windows
if sys.platform[:3] == 'win':

    class Start(BaseController):
        '''Controller for the win32 start progam through os.startfile.'''

        def _open(self, filename):
            try:
                os.startfile(filename)  # @UndefinedVariable
            except WindowsError:        # @UndefinedVariable
                # [Error 22] No application is associated with the specified
                # file for this operation: '<URL>'
                return False
            else:
                return True

    _controllers['windows-default'] = Start('start')
    _open = _controllers['windows-default']._open


# Platform support for MacOS
elif sys.platform == 'darwin':
    _controllers['open']= Controller('open')
    _open = _controllers['open']._open


# Platform support for Unix
else:

    class KfmClient(Controller):
        '''Controller for the KDE kfmclient program.'''

        def __init__(self, kfmclient='kfmclient'):
            super(KfmClient, self).__init__(kfmclient, 'exec')
            self.kde_version = self.detect_kde_version()

        def detect_kde_version(self):
            kde_version = None
            try:
                info = subprocess.getoutput('kde-config --version')

                for line in info.splitlines():
                    if line.startswith('KDE'):
                        kde_version = line.split(':')[-1].strip()
                        break
            except (OSError, RuntimeError):
                pass

            return kde_version

        def fixreturncode(self, returncode):
            if returncode is not None and self.kde_version > '3.5.4':
                return returncode
            else:
                return os.EX_OK

    def detect_desktop_environment():
        '''Checks for known desktop environments

        Return the desktop environments name, lowercase (kde, gnome, xfce)
        or "generic"

        '''

        desktop_environment = 'generic'

        if os.environ.get('KDE_FULL_SESSION') == 'true':
            desktop_environment = 'kde'
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            desktop_environment = 'gnome'
        else:
            try:
                info = subprocess.getoutput('xprop -root _DT_SAVE_MODE')
                if ' = "xfce4"' in info:
                    desktop_environment = 'xfce'
            except (OSError, RuntimeError):
                pass

        return desktop_environment


    def register_X_controllers():
        if _iscommand('kfmclient'):
            _controllers['kde-open'] = KfmClient()

        for command in ('gnome-open', 'exo-open', 'xdg-open'):
            if _iscommand(command):
                _controllers[command] = Controller(command)

    def get():
        controllers_map = {
            'gnome': 'gnome-open',
            'kde': 'kde-open',
            'xfce': 'exo-open',
        }

        desktop_environment = detect_desktop_environment()

        try:
            controller_name = controllers_map[desktop_environment]
            return _controllers[controller_name]._open

        except KeyError:
            if 'xdg-open' in _controllers:
                return _controllers['xdg-open']._open
            else:
                return webbrowser.open


    if os.environ.get("DISPLAY"):
        register_X_controllers()
    _open = get()


def _fix_addersses(**kwargs):
    for headername in ('address', 'to', 'cc', 'bcc'):
        try:
            headervalue = kwargs[headername]
            if not headervalue:
                del kwargs[headername]
                continue
            elif not isinstance(headervalue, str):
                # assume it is a sequence
                headervalue = ','.join(headervalue)

        except KeyError:
            pass
        except TypeError:
            raise TypeError('string or sequence expected for "%s", '
                            '%s found' % (headername,
                                          type(headervalue).__name__))
        else:
            translation_map = {'%': '%25', '&': '%26', '?': '%3F'}
            for char, replacement in list(translation_map.items()):
                headervalue = headervalue.replace(char, replacement)
            kwargs[headername] = headervalue

    return kwargs


def mailto_format(**kwargs):
    # @TODO: implement utf8 option

    kwargs = _fix_addersses(**kwargs)
    parts = []
    for headername in ('to', 'cc', 'bcc', 'subject', 'body', 'attach'):
        if headername in kwargs:
            headervalue = kwargs[headername]
            if not headervalue:
                continue
            if headername in ('address', 'to', 'cc', 'bcc'):
                parts.append('%s=%s' % (headername, headervalue))
            else:
                headervalue = encode_rfc2231(headervalue) # @TODO: check
                parts.append('%s=%s' % (headername, headervalue))

    mailto_string = 'mailto:%s' % kwargs.get('address', '')
    if parts:
        mailto_string = '%s?%s' % (mailto_string, '&'.join(parts))

    return mailto_string


def mailto(address, to=None, cc=None, bcc=None, subject=None, body=None,
           attach=None):
    '''
    Send an e-mail using the user's preferred composer.

    Open the user's preferred e-mail composer in order to send a mail to
    address(es) that must follow the syntax of RFC822. Multiple addresses
    may be provided (for address, cc and bcc parameters) as separate
    arguments.

    All parameters provided are used to prefill corresponding fields in
    the user's e-mail composer. The user will have the opportunity to
    change any of this information before actually sending the e-mail.


    Parameters
    ----------
    
    address : string
        specify the destination recipient
        
    cc : string
        specify a recipient to be copied on the e-mail
        
    bcc : string
        specify a recipient to be blindly copied on the e-mail
        
    subject : string
        specify a subject for the e-mail
        
    body : string
        specify a body for the e-mail. Since the user will be able
        to make changes before actually sending the e-mail, this
        can be used to provide the user with a template for the
        e-mail text may contain linebreaks
        
    attach : filename
        specify an attachment for the e-mail. file must point to an existing file

    '''

    mailto_string = mailto_format(**locals())
    return _open(mailto_string)


if __name__ == '__main__':
    from optparse import OptionParser

    version = '%%prog %s' % __version__
    usage = (
        '\n\n%prog FILENAME [FILENAME(s)] -- for opening files'
        '\n\n%prog -m [OPTIONS] ADDRESS [ADDRESS(es)] -- for sending e-mails'
    )

    parser = OptionParser(usage=usage, version=version, description=__doc__)
    parser.add_option('-m', '--mailto', dest='mailto_mode', default=False,
                      action='store_true', help='set mailto mode. '
                      'If not set any other option is ignored')
    parser.add_option('--cc', dest='cc', help='specify a recipient to be '
                      'copied on the e-mail')
    parser.add_option('--bcc', dest='bcc', help='specify a recipient to be '
                      'blindly copied on the e-mail')
    parser.add_option('--subject', dest='subject',
                      help='specify a subject for the e-mail')
    parser.add_option('--body', dest='body', help='specify a body for the '
                      'e-mail. Since the user will be able to make changes '
                      'before actually sending the e-mail, this can be used '
                      'to provide the user with a template for the e-mail '
                      'text may contain linebreaks')
    parser.add_option('--attach', dest='attach', help='specify an attachment '
                      'for the e-mail. file must point to an existing file')

    (options, args) = parser.parse_args()

    if not args:
        parser.print_usage()
        parser.exit(1)

    if options.mailto_mode:
        if not mailto(args, None, options.cc, options.bcc, options.subject,
                      options.body, options.attach):
            sys.exit('Unable to open the e-mail client')
    else:
        for name in ('cc', 'bcc', 'subject', 'body', 'attach'):
            if getattr(options, name):
                parser.error('The "cc", "bcc", "subject", "body" and "attach" '
                             'options are only accepten in mailto mode')
        success = False
        for arg in args:
            if not open(arg):
                print('Unable to open "%s"' % arg)
            else:
                success = True
        sys.exit(success)