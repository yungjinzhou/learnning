#!/usr/bin/python3 -Es
# Copyright (C) 2014-2015 Red Hat
# AUTHOR: Dan Walsh <dwalsh@redhat.com>
# see file 'COPYING' for use and warranty information
#
# atomic is a tool for managing Atomic Systems and Containers
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation; either version 2 of
#    the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#    02110-1301 USA.
#
#
import argparse
import gettext
import os
import subprocess
import sys
import traceback

import docker

import Atomic
from Atomic import containers
from Atomic import diff
from Atomic import help as Help
from Atomic import host
from Atomic import info
from Atomic import install
from Atomic import mount
from Atomic import pull
from Atomic import push
from Atomic import run
from Atomic import scan
from Atomic import sign
from Atomic import stop
from Atomic import storage
from Atomic import top
from Atomic import trust
from Atomic import uninstall
from Atomic import update
from Atomic import verify
from Atomic.mount import MountError
from Atomic import images
from Atomic.util import write_err, ImageAlreadyExists
from Atomic.backends._docker_errors import NoDockerDaemon

try:
    import cProfile
    can_profile = True
except ImportError:
    can_profile = False

PROGNAME = "atomic"
gettext.bindtextdomain(PROGNAME, "/usr/share/locale")
gettext.textdomain(PROGNAME)
try:
    # pylint: disable=unexpected-keyword-arg
    gettext.install(PROGNAME, unicode=True, codeset='utf-8')
except TypeError:
    # Failover to python3 install
    gettext.install(PROGNAME, codeset='utf-8')
except IOError:
    import builtins # pylint: disable=import-error
    builtins.__dict__['_'] = str

class HelpByDefaultArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        write_err('%s: %s' % (self.prog, message))
        write_err("Try '%s --help' for more information." % self.prog)
        sys.exit(2)

    def print_usage(self, message="too few arguments"): # pylint: disable=arguments-differ
        self.prog = " ".join(sys.argv)
        self.error(message)

# Code for python2 copied from Adrian Sampson hack
# https://gist.github.com/sampsyo/471779
#
class AliasedSubParsersAction(argparse._SubParsersAction): # pylint: disable=protected-access
    class _AliasedPseudoAction(argparse.Action): # pylint: disable=abstract-method
        def __init__(self, name, aliases, help_text):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self) #pylint: disable=protected-access
            sup.__init__(option_strings=[], dest=dest, help=help_text)

    def add_parser(self, name, **kwargs):
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
            del kwargs['aliases']
        else:
            aliases = []

        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            help = kwargs.pop('help') # pylint: disable=redefined-builtin
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, help)
            self._choices_actions.append(pseudo_action)

        return parser

def need_root():
    sub_function = sys.argv[1] if sys.argv[1] not in ['--debug'] else sys.argv[2]
    exit("Some operations for '%s' require root access." % sub_function)
    sys.exit(1)

def create_parser(help_text):
    parser = HelpByDefaultArgumentParser(description=help_text)
    parser.register('action', 'parsers', AliasedSubParsersAction)
    parser.add_argument('-v', '--version', action='version', version=Atomic.__version__,
                        help=_("show atomic version and exit"))
    parser.add_argument('--debug', default=False, action='store_true',
                        help=_("show debug messages"))
    parser.add_argument('-i', '--ignore', default=False, action='store_true',
                        help=_("ignore install-first requirement"))
    parser.add_argument('-y', '--assumeyes', default=False, action='store_true',
                        help=_("automatically answer yes for all questions"))
    if can_profile:
        parser.add_argument('--profile', default=False, action='store_true',
                            help=argparse.SUPPRESS)
    subparser = parser.add_subparsers(help=_("commands"))

    containers.cli(subparser)
    diff.cli(subparser)
    Help.cli(subparser,hidden=True)
    images.cli(subparser)

    if os.path.exists("/usr/bin/rpm-ostree") and os.path.exists("/run/ostree-booted"):
        host.cli(subparser)
    info.cli(subparser, hidden=True)

    install.cli(subparser)
    mount.cli(subparser)
    pull.cli(subparser)
    push.cli(subparser)
    run.cli(subparser)
    scan.cli(subparser)
    sign.cli(subparser)
    stop.cli(subparser)
    storage.cli(subparser)
    top.cli(subparser)
    trust.cli(subparser)

    uninstall.cli(subparser)

    mount.cli_unmount(subparser)
    update.cli(subparser, hidden=True)
    verify.cli(subparser, hidden=True)
    info.cli_version(subparser, hidden=True)

    return parser

if __name__ == '__main__':
    aparser = None
    try:
        with Atomic.Atomic() as atomic:
            aparser = create_parser(atomic.help())
            args = aparser.parse_args()
            if 'profile' in args and args.profile:
                pr = cProfile.Profile()
                pr.enable()
            _class = atomic if '_class' not in args else args._class() # pylint: disable=protected-access
            _class.set_args(args)
            if "func" in args:
                _func = getattr(_class, args.func)
                sys.exit(_func())
            else:
                aparser.print_usage()
                sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except ImageAlreadyExists as e:
        write_err("%s" % str(e))
        sys.exit(0)
    except (ValueError, IOError, docker.errors.DockerException, NoDockerDaemon) as e:
        write_err("%s" % str(e))
        if os.geteuid() != 0:
            need_root()
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        write_err("")
        sys.exit(e.returncode)
    except MountError as e:
        if str(e).find("Permission denied") > 0:
            need_root()
        else:
            write_err("%s" % str(e))
        sys.exit(1)
    except AssertionError as e:
        traceback.print_exc(file=sys.stderr)
        sys.exit()
    except Exception as e: # pylint: disable=broad-except
        write_err("%s" % str(e))
        sys.exit(1)
    except SystemExit as e:
        # Overriding debug args to avoid a traceback from sys.exit()
        if 'args' in locals():
            args.debug = False
        sys.exit(e.code)
    finally:
        if 'args' in locals() and 'profile' in args and args.profile:
            pr.disable()
            pr.print_stats("cumulative")

        if 'args' in locals() and args.debug:
            traceback.print_exc(file=sys.stderr)
