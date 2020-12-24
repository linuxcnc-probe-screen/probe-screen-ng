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

import gtk  # base for pygtk widgets and constants
import hal  # base hal class to react to hal signals
import linuxcnc

from .base import ProbeScreenBase


class ProbeScreenJog(ProbeScreenBase):
    # --------------------------
    #
    #  INIT
    #
    # --------------------------
    def __init__(self, halcomp, builder, useropts):
        super(ProbeScreenJog, self).__init__(halcomp, builder, useropts)

        # For JOG
        self.steps = self.builder.get_object("steps")
        self.incr_rbt_list = []  # we use this list to add hal pin to the button later
        self.jog_increments = []  # This holds the increment values
        self.distance = 0  # This global will hold the jog distance
        self.halcomp.newpin("jog-increment", hal.HAL_FLOAT, hal.HAL_OUT)

        self._init_jog_increments()

    def _init_jog_increments(self):
        # Get the increments from INI File
        jog_increments = []
        increments = self.inifile.find("DISPLAY", "INCREMENTS")
        if increments:
            if "," in increments:
                for i in increments.split(","):
                    jog_increments.append(i.strip())
            else:
                jog_increments = increments.split()
            jog_increments.insert(0, 0)
        else:
            jog_increments = [0, "1,000", "0,100", "0,010", "0,001"]
            print(
                "**** PROBE SCREEN INFO **** \n No default jog increments entry found in [DISPLAY] of INI file"
            )

        self.jog_increments = jog_increments
        if len(self.jog_increments) > 5:
            print(_("**** PROBE SCREEN INFO ****"))
            print(_("**** To many increments given in INI File for this screen ****"))
            print(_("**** Only the first 5 will be reachable through this screen ****"))
            # we shorten the incrementlist to 5 (first is default = 0)
            self.jog_increments = self.jog_increments[0:5]

        # The first radio button is created to get a radio button group
        # The group is called according the name off  the first button
        # We use the pressed signal, not the toggled, otherwise two signals will be emitted
        # One from the released button and one from the pressed button
        # we make a list of the buttons to later add the hardware pins to them
        label = "Cont"
        rbt0 = gtk.RadioButton(None, label)
        rbt0.connect("pressed", self.on_increment_changed, 0)
        self.steps.pack_start(rbt0, True, True, 0)
        rbt0.set_property("draw_indicator", False)
        rbt0.show()
        rbt0.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("#FFFF00"))
        rbt0.__name__ = "rbt0"
        self.incr_rbt_list.append(rbt0)
        # the rest of the buttons are now added to the group
        # self.no_increments is set while setting the hal pins with self._check_len_increments
        for item in range(1, len(self.jog_increments)):
            rbt = "rbt%d" % (item)
            rbt = gtk.RadioButton(rbt0, self.jog_increments[item])
            rbt.connect("pressed", self.on_increment_changed, self.jog_increments[item])
            self.steps.pack_start(rbt, True, True, 0)
            rbt.set_property("draw_indicator", False)
            rbt.show()
            rbt.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("#FFFF00"))
            rbt.__name__ = "rbt%d" % (item)
            self.incr_rbt_list.append(rbt)
        self.active_increment = "rbt0"

    # -----------
    # JOG BUTTONS
    # -----------
    def on_increment_changed(self, widget=None, data=None):
        if data == 0:
            self.distance = 0
        else:
            self.distance = self._parse_increment(data)
        self.halcomp["jog-increment"] = self.distance
        self.active_increment = widget.__name__

    def _from_internal_linear_unit(self, v, unit=None):
        if unit is None:
            unit = self.stat.linear_units
        lu = (unit or 1) * 25.4
        return v * lu

    def _parse_increment(self, jogincr):
        if jogincr.endswith("mm"):
            scale = self._from_internal_linear_unit(1 / 25.4)
        elif jogincr.endswith("cm"):
            scale = self._from_internal_linear_unit(10 / 25.4)
        elif jogincr.endswith("um"):
            scale = self._from_internal_linear_unit(0.001 / 25.4)
        elif jogincr.endswith("in") or jogincr.endswith("inch"):
            scale = self._from_internal_linear_unit(1.0)
        elif jogincr.endswith("mil"):
            scale = self._from_internal_linear_unit(0.001)
        else:
            scale = 1
        jogincr = jogincr.rstrip(" inchmuil")
        if "/" in jogincr:
            p, q = jogincr.split("/")
            jogincr = float(p) / float(q)
        else:
            jogincr = float(jogincr)
        return jogincr * scale

    def on_btn_jog_pressed(self, widget, data=None):
        # only in manual mode we will allow jogging the axis at this development state
        self.command.mode(linuxcnc.MODE_MANUAL)
        self.command.wait_complete()
        self.stat.poll()
        if not self.stat.task_mode == linuxcnc.MODE_MANUAL:
            return

        axisletter = widget.get_label()[0]
        if not axisletter.lower() in "xyzabcuvw":
            print("unknown axis %s" % axisletter)
            return

        # get the axisnumber
        axisnumber = "xyzabcuvws".index(axisletter.lower())

        # if data = True, then the user pressed SHIFT for Jogging and
        # want's to jog at 0.2 speed
        if data:
            value = 0.2
        else:
            value = 1

        velocity = float(self.inifile.find("TRAJ", "DEFAULT_LINEAR_VELOCITY"))

        dir = widget.get_label()[1]
        if dir == "+":
            direction = 1
        else:
            direction = -1

        self.command.teleop_enable(1)
        if self.distance != 0:  # incremental jogging
            self.command.jog(
                linuxcnc.JOG_INCREMENT,
                False,
                axisnumber,
                direction * velocity,
                self.distance,
            )
        else:  # continuous jogging
            self.command.jog(
                linuxcnc.JOG_CONTINUOUS, False, axisnumber, direction * velocity
            )

    def on_btn_jog_released(self, widget, data=None):
        axisletter = widget.get_label()[0]
        if not axisletter.lower() in "xyzabcuvw":
            print("unknown axis %s" % axisletter)
            return

        axis = "xyzabcuvw".index(axisletter.lower())

        self.command.teleop_enable(1)
        if self.distance != 0:
            pass
        else:
            self.command.jog(linuxcnc.JOG_STOP, False, axis)
