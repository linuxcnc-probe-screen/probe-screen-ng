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
from datetime import datetime
from subprocess import PIPE, Popen

import gtk
import linuxcnc

from .configparser import ProbeScreenConfigParser
from .util import restore_task_mode

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

        # Load Probe Screen Preferences
        self.prefs = ProbeScreenConfigParser(self.get_preference_file_path())

        # Which display is in use? AXIS / gmoccapy / unknown
        self.display = self.get_display() or "unknown"

        # LinuxCNC Command / Stat / Error Interfaces
        self.command = linuxcnc.command()
        self.stat = linuxcnc.stat()
        self.stat.poll()
        self.e = linuxcnc.error_channel()
        self.e.poll()

        # History Area
        textarea = builder.get_object("textview1")
        self.buffer = textarea.get_property("buffer")

        # Warning Dialog
        self.window = builder.get_object("window1")

        # VCP Reload Action
        self._vcp_action_reload = self.builder.get_object("vcp_action_reload")

        # Results Display
        self._lb_probe_xp = self.builder.get_object("lb_probe_xp")
        self._lb_probe_yp = self.builder.get_object("lb_probe_yp")
        self._lb_probe_xm = self.builder.get_object("lb_probe_xm")
        self._lb_probe_ym = self.builder.get_object("lb_probe_ym")
        self._lb_probe_lx = self.builder.get_object("lb_probe_lx")
        self._lb_probe_ly = self.builder.get_object("lb_probe_ly")
        self._lb_probe_z = self.builder.get_object("lb_probe_z")
        self._lb_probe_d = self.builder.get_object("lb_probe_d")
        self._lb_probe_xc = self.builder.get_object("lb_probe_xc")
        self._lb_probe_yc = self.builder.get_object("lb_probe_yc")
        self._lb_probe_a = self.builder.get_object("lb_probe_a")

    # --------------------------
    #
    #  MDI Command Methods
    #
    # --------------------------
    @restore_task_mode
    def gcode(self, s, data=None):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.wait_complete()

        for l in s.split("\n"):
            # Search for G1 followed by a space, otherwise we'll catch G10 too.
            if "G1 " in l:
                l += " F#<_ini[TOOLSENSOR]RAPID_SPEED>"
            self.command.mdi(l)
            self.command.wait_complete()
            if self.error_poll() == -1:
                return -1
        return 0

    @restore_task_mode
    def ocode(self, s, data=None):
        self.command.mode(linuxcnc.MODE_MDI)
        self.command.wait_complete()

        self.command.mdi(s)
        self.stat.poll()
        while self.stat.interp_state != linuxcnc.INTERP_IDLE:
            if self.error_poll() == -1:
                return -1
            self.command.wait_complete()
            self.stat.poll()
        self.command.wait_complete()
        if self.error_poll() == -1:
            return -1
        return 0

    def error_poll(self):
        # TODO: The method is essentially a giant race condition. AXIS UI
        # is also polling the error channel, and the first poller to
        # receive an error will be the only poller to get that specific
        # error. As a hacky workaround for this, we override the error
        # polling method in .axisrc to add an .error pin we can use for
        # times where the AXIS UI built in polling wins the race. However,
        # when this code wins the race - the AXIS UI build in method will
        # not receive the error - so no popup will be shown.
        # This code should probably be reworked - though I don't know we'll
        # be able to do much better without changes in AXIS UI.
        error = self.e.poll()
        if "axis" in self.display:
            error_pin = Popen(
                "halcmd getp probe.user.error ", shell=True, stdout=PIPE
            ).stdout.read()
        else:
            error_pin = Popen(
                "halcmd getp gmoccapy.error ", shell=True, stdout=PIPE
            ).stdout.read()
        if error:
            self.command.mode(linuxcnc.MODE_MANUAL)
            self.command.wait_complete()
            kind, text = error
            self.add_history("Error: %s" % text, "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                print("error", text)
                return -1
            else:
                # Info messages are not errors
                print("info", text)
                return 0
        else:
            if "TRUE" in error_pin:
                text = "User probe error"
                self.add_history(
                    "Error: %s" % text, "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                )
                print("error", text)
                self.command.mode(linuxcnc.MODE_MANUAL)
                self.command.wait_complete()
                return -1

        return 0

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

    def vcp_reload(self):
        """ Realods the VCP - e.g. after changing changing changing origin/zero points """
        self._vcp_action_reload.emit("activate")

    # --------------------------
    #
    #  History and Logging Methods
    #
    # --------------------------

    def add_history(
        self,
        tool_tip_text,
        s="",
        xm=0.0,
        xc=0.0,
        xp=0.0,
        lx=0.0,
        ym=0.0,
        yc=0.0,
        yp=0.0,
        ly=0.0,
        z=0.0,
        d=0.0,
        a=0.0,
    ):
        #        c = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = datetime.now().strftime("%H:%M:%S  ") + "{0: <10}".format(tool_tip_text)
        if "Xm" in s:
            c += "X-=%.4f " % xm
        if "Xc" in s:
            c += "Xc=%.4f " % xc
        if "Xp" in s:
            c += "X+=%.4f " % xp
        if "Lx" in s:
            c += "Lx=%.4f " % lx
        if "Ym" in s:
            c += "Y-=%.4f " % ym
        if "Yc" in s:
            c += "Yc=%.4f " % yc
        if "Yp" in s:
            c += "Y+=%.4f " % yp
        if "Ly" in s:
            c += "Ly=%.4f " % ly
        if "Z" in s:
            c += "Z=%.4f " % z
        if "D" in s:
            c += "D=%.4f" % d
        if "A" in s:
            c += "Angle=%.3f" % a
        i = self.buffer.get_end_iter()
        if i.get_line() > 1000:
            i.backward_line()
            self.buffer.delete(i, self.buffer.get_end_iter())
        i.set_line(0)
        self.buffer.insert(i, "%s \n" % c)

    def warning_dialog(self, message, secondary=None, title=_("Operator Message")):
        """ displays a warning dialog """
        dialog = gtk.MessageDialog(
            self.window,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK,
            message,
        )
        # if there is a secondary message then the first message text is bold
        if secondary:
            dialog.format_secondary_text(secondary)
        dialog.show_all()
        dialog.set_title(title)
        responce = dialog.run()
        dialog.destroy()
        return responce == gtk.RESPONSE_OK

    def display_result_xp(self, value):
        self._lb_probe_xp.set_text("%.4f" % value)

    def display_result_yp(self, value):
        self._lb_probe_yp.set_text("%.4f" % value)

    def display_result_xm(self, value):
        self._lb_probe_xm.set_text("%.4f" % value)

    def display_result_ym(self, value):
        self._lb_probe_ym.set_text("%.4f" % value)

    def display_result_lx(self, value):
        self._lb_probe_lx.set_text("%.4f" % value)

    def display_result_ly(self, value):
        self._lb_probe_ly.set_text("%.4f" % value)

    def display_result_z(self, value):
        self._lb_probe_z.set_text("%.4f" % value)

    def display_result_d(self, value):
        self._lb_probe_d.set_text("%.4f" % value)

    def display_result_xc(self, value):
        self._lb_probe_xc.set_text("%.4f" % value)

    def display_result_yc(self, value):
        self._lb_probe_yc.set_text("%.4f" % value)

    def display_result_a(self, value):
        self._lb_probe_a.set_text("%.3f" % value)

    # --------------------------
    #
    #  Generic Probe Movement Methods
    #
    # --------------------------
    def z_clearance_down(self, data=None):
        # move Z - z_clearance
        s = """G91
        G1 Z-%f
        G90""" % (
            self.halcomp["ps_z_clearance"]
        )
        if self.gcode(s) == -1:
            return -1
        return 0

    def z_clearance_up(self, data=None):
        # move Z + z_clearance
        s = """G91
        G1 Z%f
        G90""" % (
            self.halcomp["ps_z_clearance"]
        )
        if self.gcode(s) == -1:
            return -1
        return 0

    # --------------------------
    #
    #  Generic Position Calculations
    #
    # --------------------------
    def probed_position_with_offsets(self):
        self.stat.poll()
        probed_position = list(self.stat.probed_position)
        coord = list(self.stat.probed_position)
        g5x_offset = list(self.stat.g5x_offset)
        g92_offset = list(self.stat.g92_offset)
        tool_offset = list(self.stat.tool_offset)

        for i in range(0, len(probed_position) - 1):
            coord[i] = (
                probed_position[i] - g5x_offset[i] - g92_offset[i] - tool_offset[i]
            )
        angl = self.stat.rotation_xy
        res = self._rott00_point(coord[0], coord[1], -angl)
        coord[0] = res[0]
        coord[1] = res[1]
        return coord

    def _rott00_point(self, x1=0.0, y1=0.0, a1=0.0):
        """ rotate around 0,0 point coordinates """
        coord = [x1, y1]
        if a1 != 0:
            t = math.radians(a1)
            coord[0] = x1 * math.cos(t) - y1 * math.sin(t)
            coord[1] = x1 * math.sin(t) + y1 * math.cos(t)
        return coord
