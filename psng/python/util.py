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

from functools import wraps


def restore_task_mode(f):
    """ Ensures the task mode is restored when a function exits """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        # Store Current Task Mode
        prev_task_mode = self.stat.task_mode
        try:
            # Execute wrapped function
            return f(self, *args, **kwargs)
        finally:
            # Restore Previous Task Mode
            self.command.mode(prev_task_mode)
            self.command.wait_complete()

    return wrapper
