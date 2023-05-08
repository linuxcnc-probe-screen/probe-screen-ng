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

from .base import ProbeScreenBase


class ProbeScreenLengthMeasurement(ProbeScreenBase):
    # --------------------------
    #
    #  INIT
    #
    # --------------------------
    def __init__(self, halcomp, builder, useropts):
        super(ProbeScreenLengthMeasurement, self).__init__(halcomp, builder, useropts)

        self.lx_out = self.builder.get_object("lx_out")
        self.lx_in = self.builder.get_object("lx_in")
        self.ly_out = self.builder.get_object("ly_out")
        self.ly_in = self.builder.get_object("ly_in")

    # --------------
    # Length Buttons
    # --------------

    # Lx OUT
    @ProbeScreenBase.ensure_errors_dismissed
    def on_lx_out_released(self, gtkbutton, data=None):
        # move X - edge_length- xy_clearance
        tmpx = self.halcomp["ps_edge_length"] + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 X-%f
        G90""" % (
            self.setunits, tmpx
        )
        print(s)
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_xplus.ngc
        if self.ocode("o<psng_xplus> call") == -1:
            return
        # show X result
        a = self.probed_position_with_offsets()
        xpres = float(a[0]) + 0.5 * self.halcomp["ps_probe_diam"]

        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point X
        s = "G1 X%f" % xpres
        if self.gcode(s) == -1:
            return

        # move X + 2 edge_length +  xy_clearance
        tmpx = 2 * self.halcomp["ps_edge_length"] + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 X%f
        G90""" % (
            self.setunits, tmpx
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
        xmres = float(a[0]) - 0.5 * self.halcomp["ps_probe_diam"]
        xcres = 0.5 * (xpres + xmres)

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "XmXcXpLx",
            xm=xmres,
            xc=xcres,
            xp=xpres,
            lx=self.length_x(xm=xmres, xp=xpres),
        )
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # go to the new center of X
        s = "G1 X%f" % (xcres)
        if self.gcode(s) == -1:
            return
        self.set_zerro("XY")

    # Ly OUT
    @ProbeScreenBase.ensure_errors_dismissed
    def on_ly_out_released(self, gtkbutton, data=None):
        # move Y - edge_length- xy_clearance
        tmpy = self.halcomp["ps_edge_length"] + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 Y-%f
        G90""" % (
            self.setunits, tmpy
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

        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point Y
        s = "G1 Y%f" % ypres
        if self.gcode(s) == -1:
            return

        # move Y + 2 edge_length +  xy_clearance
        tmpy = 2 * self.halcomp["ps_edge_length"] + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 Y%f
        G90""" % (
            self.setunits, tmpy
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start psng_yminus.ngc
        if self.ocode("o<psng_yminus> call") == -1:
            return
        # show Y result
        a = self.probed_position_with_offsets()
        ymres = float(a[1]) - 0.5 * self.halcomp["ps_probe_diam"]

        # find, show and move to finded  point
        ycres = 0.5 * (ypres + ymres)

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "YmYcYpLy",
            ym=ymres,
            yc=ycres,
            yp=ypres,
            ly=self.length_y(ym=ymres, yp=ypres),
        )
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        s = "G1 Y%f" % (ycres)
        if self.gcode(s) == -1:
            return
        self.set_zerro("XY")

    # Lx IN
    @ProbeScreenBase.ensure_errors_dismissed
    def on_lx_in_released(self, gtkbutton, data=None):
        if self.z_clearance_down() == -1:
            return
        # move X - edge_length Y + xy_clearance
        tmpx = self.halcomp["ps_edge_length"] - self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 X-%f
        G90""" % (
            self.setunits, tmpx
        )
        if self.gcode(s) == -1:
            return
        # Start psng_xminus.ngc
        if self.ocode("o<psng_xminus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xmres = float(a[0]) - 0.5 * self.halcomp["ps_probe_diam"]

        # move X +2 edge_length - 2 xy_clearance
        tmpx = 2 * (self.halcomp["ps_edge_length"] - self.halcomp["ps_xy_clearance"])
        s = """%s
        G91
        G1 X%f
        G90""" % (
            self.setunits, tmpx
        )
        if self.gcode(s) == -1:
            return
        # Start psng_xplus.ngc
        if self.ocode("o<psng_xplus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xpres = float(a[0]) + 0.5 * self.halcomp["ps_probe_diam"]
        xcres = 0.5 * (xmres + xpres)

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "XmXcXpLx",
            xm=xmres,
            xc=xcres,
            xp=xpres,
            lx=self.length_x(xm=xmres, xp=xpres),
        )
        # move X to new center
        s = """G1 X%f""" % (xcres)
        if self.gcode(s) == -1:
            return
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        self.set_zerro("XY")

    # Ly IN
    @ProbeScreenBase.ensure_errors_dismissed
    def on_ly_in_released(self, gtkbutton, data=None):
        if self.z_clearance_down() == -1:
            return
        # move Y - edge_length + xy_clearance
        tmpy = self.halcomp["ps_edge_length"] - self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 Y-%f
        G90""" % (
            self.setunits, tmpy
        )
        if self.gcode(s) == -1:
            return
        # Start psng_yminus.ngc
        if self.ocode("o<psng_yminus> call") == -1:
            return

        # Calculate Y result
        a = self.probed_position_with_offsets()
        ymres = float(a[1]) - 0.5 * self.halcomp["ps_probe_diam"]

        # move Y +2 edge_length - 2 xy_clearance
        tmpy = 2 * (self.halcomp["ps_edge_length"] - self.halcomp["ps_xy_clearance"])
        s = """%s
        G91
        G1 Y%f
        G90""" % (
            self.setunits, tmpy
        )
        if self.gcode(s) == -1:
            return
        # Start psng_yplus.ngc
        if self.ocode("o<psng_yplus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ypres = float(a[1]) + 0.5 * self.halcomp["ps_probe_diam"]

        # find, show and move to finded  point
        ycres = 0.5 * (ymres + ypres)

        self.add_history(
            gtkbutton.get_tooltip_text(),
            "YmYcYpLy",
            ym=ymres,
            yc=ycres,
            yp=ypres,
            ly=self.length_y(ym=ymres, yp=ypres),
        )

        # move to center
        s = "G1 Y%f" % (ycres)
        if self.gcode(s) == -1:
            return
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        self.set_zerro("XY")
