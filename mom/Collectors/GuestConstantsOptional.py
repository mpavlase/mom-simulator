# Memory Overcommitment Manager Simulator
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

from mom.Collectors.Collector import *
from xml.dom.minidom import parseString as _domParseStr
import libvirt

_METADATA_CONSTANTS_URI = 'http://github.com/mpavlase/mom-simulator/1'


class GuestConstantsOptional(Collector):
    """
    This Collector uses libvirt's metadata element to get constants from VM to
    rules.

    # Let guest maintain at least this amout of memory
    min_guest_free_percent 0.20

    # Don't change a guest's memory by more than this percent of total memory
    max_balloon_change_percent 0.05

    # Only ballooning operations that change the balloon by this percentage
    # of current guest memory should be undertaken to avoid overhead
    min_balloon_change_percent 0.0025
    """

    def __init__(self, properties):
        self.hypervisor_iface = properties['hypervisor_iface']
        self.uuid = properties['uuid']
        self.logger = logging.getLogger('mom.Collectors.GuestConstantsOptional')

    def getOptionalFields(self=None):
        return set(['const_min_guest_free_percent',
                    'const_max_balloon_change_percent',
                    'const_min_balloon_change_percent'])

    def getFields(self=None):
        return set([])

    def _get_metadata(self, uuid, xmlns):
        metadata = self.hypervisor_iface.getXMLmetadata(uuid, xmlns)

        return metadata

    def collect(self):
        ret_fields = {}
        try:
            metadata_xml = self._get_metadata(self.uuid, _METADATA_CONSTANTS_URI)
        except Exception as e:
            #self.logger.error(dir(e))
            self.logger.error(e.message)
            return {}

        plan = self.hypervisor_iface.getXMLElementValue(metadata_xml, 'plan')
        self.logger.debug(plan)

        for key in self.getOptionalFields():
            try:
                self.logger.debug('Getting key %s... ' % key)
                ret_fields[key] = self.hypervisor_iface.getXMLElementValue( \
                    metadata_xml, key)
                self.logger.debug('... using VM\'s own value for key %s: %s ' %
                                  (key, ret_fields[key]))
            except IndexError as e:
                pass

        return ret_fields
