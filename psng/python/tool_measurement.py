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

import os
import sys

import hal
import hal_glib

from .base import ProbeScreenBase


class ProbeScreenToolMeasurement(ProbeScreenBase):
    # --------------------------
    #
    #  INIT
    #
    # --------------------------
    def __init__(self, halcomp, builder, useropts):
        super(ProbeScreenToolMeasurement, self).__init__(halcomp, builder, useropts)

        self.hal_led_set_m6 = self.builder.get_object("hal_led_set_m6")
        self.frm_probe_pos = self.builder.get_object("frm_probe_pos")
        self.spbtn_setter_height = self.builder.get_object("spbtn_setter_height")
        self.spbtn_block_height = self.builder.get_object("spbtn_block_height")
        self.btn_probe_tool_setter = self.builder.get_object("btn_probe_tool_setter")
        self.btn_probe_workpiece = self.builder.get_object("btn_probe_workpiece")
        self.btn_tool_dia = self.builder.get_object("btn_tool_dia")
        self.tooledit1 = self.builder.get_object("tooledit1")
        self.chk_use_tool_measurement = self.builder.get_object(
            "chk_use_tool_measurement"
        )

        self.chk_use_tool_measurement.set_active(
            self.prefs.getpref("use_tool_measurement", False, bool)
        )

        # make the pins for tool measurement
        self.halcomp.newpin("use_tool_measurement", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("setterheight", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("blockheight", hal.HAL_FLOAT, hal.HAL_OUT)
        # for manual tool change dialog
        self.halcomp.newpin("toolchange-number", hal.HAL_S32, hal.HAL_IN)
        self.halcomp.newpin("toolchange-prep-number", hal.HAL_S32, hal.HAL_IN)
        self.halcomp.newpin("toolchange-changed", hal.HAL_BIT, hal.HAL_OUT)
        pin = self.halcomp.newpin("toolchange-change", hal.HAL_BIT, hal.HAL_IN)
        hal_glib.GPin(pin).connect("value_changed", self.on_tool_change)

        if self.chk_use_tool_measurement.get_active():
            self.halcomp["use_tool_measurement"] = True
            self.hal_led_set_m6.hal_pin.set(1)

        self._init_tool_sensor_data()

    # Read the ini file config [TOOLSENSOR] section
    def _init_tool_sensor_data(self):
        xpos = self.inifile.find("TOOLSENSOR", "X")
        ypos = self.inifile.find("TOOLSENSOR", "Y")
        zpos = self.inifile.find("TOOLSENSOR", "Z")
        maxprobe = self.inifile.find("TOOLSENSOR", "MAXPROBE")
        tsdiam = self.inifile.find("TOOLSENSOR", "TS_DIAMETER")

        if (
            xpos is None
            or ypos is None
            or zpos is None
            or maxprobe is None
            or tsdiam is None
        ):
            self.chk_use_tool_measurement.set_active(False)
            self.btn_tool_dia.set_sensitive(False)
            self.btn_probe_tool_setter.set_sensitive(False)

            self.error_dialog(
                "Invalid INI Configuration",
                secondary="Please check the TOOLSENSOR INI configurations",
            )
        else:
            self.xpos = float(xpos)
            self.ypos = float(ypos)
            self.zpos = float(zpos)
            self.maxprobe = float(maxprobe)
            self.tsdiam = float(tsdiam)

            self.spbtn_setter_height.set_value(
                self.prefs.getpref("setterheight", 0.0, float)
            )
            self.spbtn_block_height.set_value(
                self.prefs.getpref("blockheight", 0.0, float)
            )
            # to set the hal pin with correct values we emit a toogled
            if self.chk_use_tool_measurement.get_active():
                self.frm_probe_pos.set_sensitive(True)
                self.halcomp["use_tool_measurement"] = True
                self.halcomp["setterheight"] = self.spbtn_setter_height.get_value()
                self.halcomp["blockheight"] = self.spbtn_block_height.get_value()
            else:
                self.frm_probe_pos.set_sensitive(False)
                self.chk_use_tool_measurement.set_sensitive(True)

    # ----------------
    # Remap M6 Buttons
    # ----------------
    # Tickbox from gui for enable disable remap (with saving pref)
    def on_chk_use_tool_measurement_toggled(self, gtkcheckbutton, data=None):
        if gtkcheckbutton.get_active():
            self.frm_probe_pos.set_sensitive(True)
            self.halcomp["use_tool_measurement"] = True
            self.halcomp["setterheight"] = self.spbtn_setter_height.get_value()
            self.halcomp["blockheight"] = self.spbtn_block_height.get_value()
        else:
            self.frm_probe_pos.set_sensitive(False)
            self.halcomp["use_tool_measurement"] = False
            self.halcomp["setterheight"] = 0.0
            self.halcomp["blockheight"] = 0.0
        self.prefs.putpref("use_tool_measurement", gtkcheckbutton.get_active(), bool)
        self.hal_led_set_m6.hal_pin.set(gtkcheckbutton.get_active())

    # Spinbox for setter height with autosave value inside machine pref file
    def on_spbtn_setter_height_key_press_event(self, gtkspinbutton, data=None):
        self.on_common_spbtn_key_press_event("setterheight", gtkspinbutton, data)

    def on_spbtn_setter_height_value_changed(self, gtkspinbutton, data=None):
        self.on_common_spbtn_value_changed("setterheight", gtkspinbutton, data)

        # Record results to history panel
        c = "TS Height = " + "%.4f" % gtkspinbutton.get_value()
        self.add_history_text(c)

    # Spinbox for block height with autosave value inside machine pref file
    def on_spbtn_block_height_key_press_event(self, gtkspinbutton, data=None):
        self.on_common_spbtn_key_press_event("blockheight", gtkspinbutton, data)

    def on_spbtn_block_height_value_changed(self, gtkspinbutton, data=None):
        self.on_common_spbtn_value_changed("blockheight", gtkspinbutton, data)

        # set coordinate system to new origin
        self.gcode("G10 L2 P0 Z%s" % gtkspinbutton.get_value())
        self.vcp_reload()

        # Record results to history panel
        c = "Workpiece Height = " + "%.4f" % gtkspinbutton.get_value()
        self.add_history_text(c)

    # Down probe to table for measuring it and use for calculate tool setter height and can set G10 L20 Z0 if you tick auto zero
    @ProbeScreenBase.ensure_errors_dismissed
    def on_btn_probe_table_released(self, gtkbutton, data=None):
        # Start psng_probe_table.ngc
        if self.ocode("o<psng_probe_table> call") == -1:
            return
        a = self.probed_position_with_offsets()
        self.add_history(gtkbutton.get_tooltip_text(), "Z", z=a[2])
        self.set_zerro("Z", 0, 0, a[2])

    # Down probe to tool setter for measuring it vs table probing result
    @ProbeScreenBase.ensure_errors_dismissed
    def on_btn_probe_tool_setter_released(self, gtkbutton, data=None):
        # Start psng_probe_tool_setter.ngc
        if self.ocode("o<psng_probe_tool_setter> call") == -1:
            return
        self.vcp_reload()
        a = self.stat.probed_position
        self.spbtn_setter_height.set_value(float(a[2]))
        self.add_history(gtkbutton.get_tooltip_text(), "Z", z=a[2])

    # Down probe to workpiece for measuring it vs Know tool setter height
    @ProbeScreenBase.ensure_errors_dismissed
    def on_btn_probe_workpiece_released(self, gtkbutton, data=None):
        # Start psng_probe_workpiece.ngc
        if self.ocode("o<psng_probe_workpiece> call") == -1:
            return
        self.vcp_reload()
        a = self.stat.probed_position
        self.spbtn_block_height.set_value(float(a[2]))
        self.add_history(gtkbutton.get_tooltip_text(), "Z", z=a[2])

    # Probe tool Diameter
    @ProbeScreenBase.ensure_errors_dismissed
    def on_btn_tool_dia_released(self, gtkbutton, data=None):
        # move XY to Tool Setter point
        # Start psng_tool_diameter.ngc
        if self.ocode("o<psng_tool_diameter> call") == -1:
            return
        # move X - edge_length- xy_clearance
        s = """%s
        G91
        G1 X-%f
        G90""" % (
            self.setunits, 
            0.5 * self.tsdiam + self.halcomp["ps_xy_clearance"]
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
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

        # move X + tsdiam +  xy_clearance
        aa = self.tsdiam + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 X%f
        G90""" % (
            self.setunits, 
            aa
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc

        if self.ocode("o<psng_xminus> call") == -1:
            return
        # Calculate X result
        a = self.probed_position_with_offsets()
        xmres = float(a[0]) - 0.5 * self.halcomp["ps_probe_diam"]
        xcres = 0.5 * (xpres + xmres)
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # go to the new center of X
        s = "G1 X%f" % xcres
        if self.gcode(s) == -1:
            return

        # move Y - tsdiam/2 - xy_clearance
        a = 0.5 * self.tsdiam + self.halcomp["ps_xy_clearance"]
        s = """%s
            G91
        G1 Y-%f
        G90""" % (
            self.setunits,
            a
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yplus.ngc
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

        # move Y + tsdiam +  xy_clearance
        aa = self.tsdiam + self.halcomp["ps_xy_clearance"]
        s = """%s
        G91
        G1 Y%f
        G90""" % (
            self.setunits, 
            aa
        )
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode("o<psng_yminus> call") == -1:
            return
        # Calculate Y result
        a = self.probed_position_with_offsets()
        ymres = float(a[1]) - 0.5 * self.halcomp["ps_probe_diam"]

        # find, show and move to finded  point
        ycres = 0.5 * (ypres + ymres)
        diam = self.halcomp["ps_probe_diam"] + (ymres - ypres - self.tsdiam)

        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        self.stat.poll()
        tmpz = self.stat.position[2] - 4
        self.add_history(
            gtkbutton.get_tooltip_text(),
            "XcYcZD",
            xc=xcres,
            yc=ycres,
            z=tmpz,
            d=diam,
        )
        # move to finded  point
        s = "G1 Y%f" % ycres
        if self.gcode(s) == -1:
            return

    # Here we create a manual tool change dialog
    def on_tool_change(self, gtkbutton, data=None):
        change = self.halcomp["toolchange-change"]
        toolnumber = self.halcomp["toolchange-number"]
        toolprepnumber = self.halcomp["toolchange-prep-number"]
        print("tool-number =", toolnumber)
        print("tool_prep_number =", toolprepnumber, change)
        if change:
            # if toolprepnumber = 0 we will get an error because we will not be able to get
            # any tooldescription, so we avoid that case
            if toolprepnumber == 0:
                message = _("Please remove the mounted tool and press OK when done")
            else:
                tooltable = self.inifile.find("EMCIO", "TOOL_TABLE")
                if not tooltable:
                    self.error_dialog(
                        "Tool Measurement Error",
                        secondary="Did not find a toolfile file in [EMCIO] TOOL_TABLE",
                    )
                CONFIGPATH = os.environ["CONFIG_DIR"]
                toolfile = os.path.join(CONFIGPATH, tooltable)
                self.tooledit1.set_filename(toolfile)
                tooldescr = self.tooledit1.get_toolinfo(toolprepnumber)[16]
                message = _(
                    "Please change to tool\n\n# {0:d}     {1}\n\n then click OK."
                ).format(toolprepnumber, tooldescr)
            result = self.warning_dialog(message, title=_("Manual Toolchange"))
            if result:
                self.vcp_reload()
                self.halcomp["toolchange-changed"] = True
            else:
                print(
                    "toolchange abort",
                    toolnumber,
                    self.halcomp["toolchange-prep-number"],
                )
                self.command.abort()
                self.halcomp["toolchange-prep-number"] = toolnumber
                self.halcomp["toolchange-change"] = False
                self.halcomp["toolchange-changed"] = True
                message = _("**** TOOLCHANGE ABORTED ****")
                self.warning_dialog(message)
        else:
            self.halcomp["toolchange-changed"] = False
