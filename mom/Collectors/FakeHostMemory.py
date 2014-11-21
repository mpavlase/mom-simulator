# Memory Overcommitment Manager
# Copyright (C) 2014 Martin Pavlasek, Red Hat corp.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

from mom.Collectors.Collector import *
from mom.HypervisorInterfaces.HypervisorInterface import *

class FakeHostMemory(Collector):
    """
    This Fake Collctor returns memory statistics about the host by examining
    /proc/meminfo and /proc/vmstat.  The fields provided are:
        mem_available - The total amount of available memory (kB)
        mem_free      - The amount of free memory including some caches (kB)
    """
    def __init__(self, properties):
        self.logger = logging.getLogger('mom.Collectors.FakeHostMemory')
        self.logger.info(properties)
        self.hypervisor_iface = properties['hypervisor_iface']

    def __del__(self):
        pass

    def collect(self):
        self.logger.info('collect...')
        mem = self.hypervisor_iface.getHostMemoryStats()
        self.logger.info(mem)
        data = {'mem_available': mem['mem_available'],
                'mem_free': mem['mem_free'],
        }
        return data

    def getFields(self=None):
        #return set(['mem_available', 'mem_unused', 'mem_free', 'swap_in', \
        #           'swap_out', 'anon_pages', 'swap_total', 'swap_usage'])
        return set(['mem_available', 'mem_free'])
