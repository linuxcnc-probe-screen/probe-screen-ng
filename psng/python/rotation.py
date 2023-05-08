#!/usr/bin/env python
#
# Copyright (c) 2015 Serguei Glavatski ( verser  from cnc-club.ru )
# Copyright (c) 2020 Probe Screen NG Developers
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

import math
import time

import hal

from .base import ProbeScreenBase


class ProbeScreenRotation(ProbeScreenBase):
    # --------------------------
    #
    #  INIT
    #
    # --------------------------
    def __init__(self, halcomp, builder, useropts):
        super(ProbeScreenRotation, self).__init__(halcomp, builder, useropts)

        self.hal_led_auto_rott = self.builder.get_object("hal_led_auto_rott")
        self.chk_auto_rott = self.builder.get_object("chk_auto_rott")
        self.spbtn_offs_angle = self.builder.get_object("spbtn_offs_angle")

        self.chk_auto_rott.set_active(self.prefs.getpref("chk_auto_rott", False, bool))
        self.spbtn_offs_angle.set_value(self.prefs.getpref("ps_offs_angle", 0.0, float))

        self.halcomp.newpin("ps_offs_angle", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("auto_rott", hal.HAL_BIT, hal.HAL_OUT)

        if self.chk_auto_rott.get_active():
            self.halcomp["auto_rott"] = True
            self.hal_led_auto_rott.hal_pin.set(1)
        self.halcomp["ps_offs_angle"] = self.spbtn_offs_angle.get_value()

    # --------------
    # Rotate Buttons
    # --------------
    def on_chk_auto_rott_toggled(self, gtkcheckbutton, data=None):
        self.halcomp["auto_rott"] = gtkcheckbutton.get_active()
        self.hal_led_auto_rott.hal_pin.set(gtkcheckbutton.get_active())
        self.prefs.putpref("chk_auto_rott", gtkcheckbutton.get_active(), bool)

    def on_btn_set_angle_released(self, gtkbutton, data=None):
        self.prefs.putpref("ps_offs_angle", self.spbtn_offs_angle.get_value(), float)

        self.display_result_a(self.spbtn_offs_angle.get_value())

        s = "G10 L2 P0"
        if self.halcomp["set_zero"]:
            s += " X%.4f" % self.halcomp["ps_offs_x"]
            s += " Y%.4f" % self.halcomp["ps_offs_y"]
        else:
            self.stat.poll()
            x = self.stat.position[0]
            y = self.stat.position[1]
            s += " X%.4f" % x
            s += " Y%.4f" % y
        s += " R%.4f" % self.spbtn_offs_angle.get_value()
        print("s=", s)
        self.gcode(s)
        self.vcp_reload()
        time.sleep(1)

    def on_spbtn_offs_angle_key_press_event(self, gtkspinbutton, data=None):
        self.on_common_spbtn_key_press_event("ps_offs_angle", gtkspinbutton, data)

    def on_spbtn_offs_angle_value_changed(self, gtkspinbutton, data=None):
        self.on_common_spbtn_value_changed("ps_offs_angle", gtkspinbutton, data)

    # Y+Y+
    @ProbeScreenBase.ensure_errors_dismissed
    def on_angle_yp_released(self, gtkbutton, data=None):
        self.stat.poll()
        xstart = (
            self.stat.position[0]
            - self.stat.g5x_offset[0]
            - self.stat.g92_offset[0]
            - self.stat.tool_offset[0]
        )
        # move Y - xy_clearance
        s = """%s
        G91
        G1 Y-%f
        G90""" % (
            self.setunits, self.halcomp["ps_xy_clearance"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_yplus.ngc
        if self.ocode("o<psng_yplus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ycres = float(a[1]) + 0.5 * self.halcomp["ps_probe_diam"]

        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move X + edge_length
        s = """%s
        G91
        G1 X%f
        G90""" % (
            self.setunits, self.halcomp["ps_edge_length"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_yplus.ngc
        if self.ocode("o<psng_yplus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ypres = float(a[1]) + 0.5 * self.halcomp["ps_probe_diam"]
        alfa = math.degrees(math.atan2(ypres - ycres, self.halcomp["ps_edge_length"]))

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "YcYpA",
            yc=ycres,
            yp=ypres,
            a=alfa,
        )

        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move XY to adj start point
        s = "G1 X%f Y%f" % (xstart, ycres)
        if self.gcode(s) == -1:
            return
        self.rotate_coord_system(alfa)

    # Y-Y-
    @ProbeScreenBase.ensure_errors_dismissed
    def on_angle_ym_released(self, gtkbutton, data=None):
        self.stat.poll()
        xstart = (
            self.stat.position[0]
            - self.stat.g5x_offset[0]
            - self.stat.g92_offset[0]
            - self.stat.tool_offset[0]
        )
        # move Y + xy_clearance
        s = """%s
        G91
        G1 Y%f
        G90""" % (
            self.setunits, self.halcomp["ps_xy_clearance"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_yminus.ngc
        if self.ocode("o<psng_yminus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ycres = float(a[1]) - 0.5 * self.halcomp["ps_probe_diam"]

        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move X - edge_length
        s = """%s
        G91
        G1 X-%f
        G90""" % (
            self.setunits, self.halcomp["ps_edge_length"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_yminus.ngc
        if self.ocode("o<psng_yminus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ymres = float(a[1]) - 0.5 * self.halcomp["ps_probe_diam"]
        alfa = math.degrees(math.atan2(ycres - ymres, self.halcomp["ps_edge_length"]))

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "YmYcA",
            ym=ymres,
            yc=ycres,
            a=alfa,
        )
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move XY to adj start point
        s = "G1 X%f Y%f" % (xstart, ycres)
        if self.gcode(s) == -1:
            return
        self.rotate_coord_system(alfa)

    # X+X+
    @ProbeScreenBase.ensure_errors_dismissed
    def on_angle_xp_released(self, gtkbutton, data=None):
        self.stat.poll()
        ystart = (
            self.stat.position[1]
            - self.stat.g5x_offset[1]
            - self.stat.g92_offset[1]
            - self.stat.tool_offset[1]
        )
        # move X - xy_clearance
        s = """%s
        G91
        G1 X-%f
        G90""" % (
            self.setunits, self.halcomp["ps_xy_clearance"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_xplus.ngc
        if self.ocode("o<psng_xplus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xcres = float(a[0]) + 0.5 * self.halcomp["ps_probe_diam"]

        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move Y - edge_length
        s = """%s
        G91
        G1 Y-%f
        G90""" % (
            self.setunits, self.halcomp["ps_edge_length"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_xplus.ngc
        if self.ocode("o<psng_xplus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xpres = float(a[0]) + 0.5 * self.halcomp["ps_probe_diam"]
        alfa = math.degrees(math.atan2(xcres - xpres, self.halcomp["ps_edge_length"]))

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "XcXpA",
            xc=xcres,
            xp=xpres,
            a=alfa,
        )
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move XY to adj start point
        s = "G1 X%f Y%f" % (xcres, ystart)
        if self.gcode(s) == -1:
            return
        self.rotate_coord_system(alfa)

    # X-X-
    @ProbeScreenBase.ensure_errors_dismissed
    def on_angle_xm_released(self, gtkbutton, data=None):
        self.stat.poll()
        ystart = (
            self.stat.position[1]
            - self.stat.g5x_offset[1]
            - self.stat.g92_offset[1]
            - self.stat.tool_offset[1]
        )
        # move X + xy_clearance
        s = """%s
        G91
        G1 X%f
        G90""" % (
            self.setunits, self.halcomp["ps_xy_clearance"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_xminus.ngc
        if self.ocode("o<psng_xminus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xcres = float(a[0]) - 0.5 * self.halcomp["ps_probe_diam"]

        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move Y + edge_length
        s = """%s
        G91
        G1 Y%f
        G90""" % (
            self.setunits, self.halcomp["ps_edge_length"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_xminus.ngc
        if self.ocode("o<psng_xminus> call") == -1:
            return
        # show X result
        a = self.probed_position_with_offsets()
        xmres = float(a[0]) - 0.5 * self.halcomp["ps_probe_diam"]
        alfa = math.degrees(math.atan2(xcres - xmres, self.halcomp["ps_edge_length"]))

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "XmXcA",
            xm=xmres,
            xc=xcres,
            a=alfa,
        )
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move XY to adj start point
        s = "G1 X%f Y%f" % (xcres, ystart)
        if self.gcode(s) == -1:
            return
        self.rotate_coord_system(alfa)

    # --------------
    # Helper Methods
    # --------------
    def rotate_coord_system(self, a=0.0):
        self.spbtn_offs_angle.set_value(a)
        self.display_result_a(a)

        if self.chk_auto_rott.get_active():
            s = "G10 L2 P0"
            if self.halcomp["set_zero"]:
                s += " X%s" % self.halcomp["ps_offs_x"]
                s += " Y%s" % self.halcomp["ps_offs_y"]
            else:
                self.stat.poll()
                x = self.stat.position[0]
                y = self.stat.position[1]
                s += " X%s" % x
                s += " Y%s" % y
            s += " R%s" % a
            self.gcode(s)
            self.vcp_reload()
            time.sleep(1)
