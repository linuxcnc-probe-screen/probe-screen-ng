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

import linuxcnc  # to get our own error system

from .jog import ProbeScreenJog
from .psng import ProbeScreenClass
from .rotation import ProbeScreenRotation
from .settings import ProbeScreenSettings
from .zero import ProbeScreenZero


def get_handlers(halcomp, builder, useropts):
    return [
        ProbeScreenClass(halcomp, builder, useropts),
        ProbeScreenSettings(halcomp, builder, useropts),
        ProbeScreenJog(halcomp, builder, useropts),
        ProbeScreenZero(halcomp, builder, useropts),
        ProbeScreenRotation(halcomp, builder, useropts),
    ]
