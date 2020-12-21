#!/usr/bin/env python
#
# Copyright (c) 2015 Serguei Glavatski ( verser  from cnc-club.ru )
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import linuxcnc

from .configparser import ProbeScreenConfigParser

CONFIGPATH1 = os.environ["CONFIG_DIR"]


class ProbeScreenBase(object):
    # --------------------------
    #
    #  INIT
    #
    # --------------------------
    def __init__(self, halcomp, builder, useropts):
        self.builder = builder
        self.halcomp = halcomp

        # Load the machines INI file
        self.inifile = linuxcnc.ini(os.environ["INI_FILE_NAME"])
        if not self.inifile:
            print("**** PROBE SCREEN GET INI INFO **** \n Error, no INI File given !!")
            sys.exit()

        self.display = self.get_display() or "unknown"
        self.command = linuxcnc.command()
        self.stat = linuxcnc.stat()
        self.prefs = ProbeScreenConfigParser(self.get_preference_file_path())

    # --------------------------
    #
    #  Utility Methods
    #
    # --------------------------
    def get_display(self):
        # gmoccapy or axis ?
        temp = self.inifile.find("DISPLAY", "DISPLAY")
        if not temp:
            print(
                "****  PROBE SCREEN GET INI INFO **** \n Error recognition of display type : %s"
                % temp
            )
        return temp

    def get_preference_file_path(self):
        # we get the preference file, if there is none given in the INI
        # we use toolchange2.pref in the config dir
        temp = self.inifile.find("DISPLAY", "PREFERENCE_FILE_PATH")
        if not temp:
            machinename = self.inifile.find("EMC", "MACHINE")
            if not machinename:
                temp = os.path.join(CONFIGPATH1, "probe_screen.pref")
            else:
                machinename = machinename.replace(" ", "_")
                temp = os.path.join(CONFIGPATH1, "%s.pref" % machinename)
        print("****  probe_screen GETINIINFO **** \n Preference file path: %s" % temp)
        return temp
