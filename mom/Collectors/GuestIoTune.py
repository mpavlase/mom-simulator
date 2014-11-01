# Memory Overcommitment Manager
# Copyright (C) 2014 Martin Pavlasek, Red Hat inc.
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

import re
import sys
import logging

"""
<qos>
    <vcpuLimit>50</vcpuLimit>
    <ioTune>
    <!--<device path="test-device-by-path">-->
        <device name="test-device-by-name">
            <maximum>
                <total_bytes_sec>200</total_bytes_sec>
                <total_iops_sec>201</total_iops_sec>
                <read_bytes_sec>202</read_bytes_sec>
                <read_iops_sec>203</read_iops_sec>
                <write_bytes_sec>204</write_bytes_sec>
                <write_iops_sec>205</write_iops_sec>
            </maximum>
            <guaranteed>
                <total_bytes_sec>100</total_bytes_sec>
                <total_iops_sec>101</total_iops_sec>
                <read_bytes_sec>102</read_bytes_sec>
                <read_iops_sec>103</read_iops_sec>
                <write_bytes_sec>104</write_bytes_sec>
                <write_iops_sec>105</write_iops_sec>
            </guaranteed>
        </device>
    </ioTune>
</qos>

From libvirt iface
hda rd_bytes 103753216
hda wr_bytes 5977088
"""

class GuestIoTune:
    """
    Collectors are plugins that return a specific set of data items pertinent to
    a given Monitor object every time their collect() method is called.  Context
    is given by the Monitor properties that are used to init the Collector.
    """
    def getFields(self=None):
        """
        Used to query the names of mandatory statistics fields that this
        Collector will return.
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set(['rd_bytes', 'wr_bytes'])

    def getOptionalFields(self=None):
        """
        Used to query the names of optional statistics fields that this
        Collector will return.
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set()

    def __init__(self, properties):
        """
        The Collector constructor should use the passed-in properties to
        establish context from its owning Monitor.
        Override this method when creating new collectors.
        """
        self.hypervisor_iface = properties['hypervisor_iface']
        self.uuid = properties['uuid']
        self.logger = logging.getLogger('mom.Collectors.GuestIoTune')
        self.logger.info(self.hypervisor_iface.getIoTunables(self.uuid))

    def collect(self):
        """
        The principle interface for every Collector.  This method is called by a
        monitor to initiate data collection.
        Override this method when creating new collectors.
        Return: A dictionary of statistics.
        """
        return {}

