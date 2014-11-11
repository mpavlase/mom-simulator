# Memory Overcommitment Manager
# Copyright (C) 2010 Adam Litke, IBM Corporation
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

import libvirt
import re
import logging
from subprocess import *
from mom.HypervisorInterfaces.HypervisorInterface import *
from xml.etree import ElementTree
from xml.dom.minidom import parseString as _domParseStr

_METADATA_VM_TUNE_URI = 'http://ovirt.org/vm/tune/1.0'

class fakeInterface(HypervisorInterface):
    """
    libvirtInterface provides a wrapper for the libvirt API so that libvirt-
    related error handling can be consolidated in one place.  An instance of
    this class provides a single libvirt connection that can be shared by all
    threads.  If the connection is broken, an attempt will be made to reconnect.
    """
    def __init__(self, config):
        self.conn = None
        self.logger = logging.getLogger('mom.fakeInterface')
        self.mem_stats = {'available': 'mem_available',
                          'unused': 'mem_unused',
                          'major_fault': 'major_fault',
                          'minor_fault': 'minor_fault',
                          'swap_in': 'swap_in',
                          'swap_out': 'swap_out'
                          }
        def_mem_stat = {'available': 8000,
                'unused': 7000,
                'major_fault': 0,
                'minor_fault': 0,
                'swap_in': 0,
                'swap_out': 0,
                'balloon_cur': 100
                }
        self.domains = {
            'fake-vm-1': {
                'uuid': 'uuid-1',
            }
        }
        self.domains['fake-vm-1'].update(def_mem_stat)

    def __del__(self):
        pass
        #if self.conn is not None:
        #    self.conn.close()

    def _getDomainFromUUID(self, uuid):
        #self.logger.info('uuid = %s' % uuid)
        ret = filter(lambda x: self.domains[x]['uuid'] == uuid, self.domains)
        return ret[0]

    def getConstants():
        """
        These keys are necessary for balloning rules, values are used only if
        hypervisor isn't able to provide its own values.
        """
        return {'min_guest_free_percent': 0.201,
                'max_balloon_change_percent': 0.05,
                'min_balloon_change_percent': 0.0025}

    def getVmList(self):
        ret = [k for k, v in self.domains.iteritems()]
        #self.logger.info('list = %s' % ret)
        return [k for k, v in self.domains.iteritems()]

    def getVmInfo(self, idvm):
        data = {}
        data['uuid'] = self.domains[idvm]['uuid']
        data['name'] = idvm
        if None in data.values():
            return None
        return data

    def startVmMemoryStats(self, uuid):
        pass

    def getVmMemoryStats(self, uuid):
        domain = self._getDomainFromUUID(uuid)
        info = self.domains[domain]
        ret = {}
        ## Try to collect memory stats.  This function may not be available
        #info = self._domainGetMemoryStats(domain)
        #info = {'available': 8000,
        #        'unused': 7000,
        #        'major_fault': 0,
        #        'minor_fault': 0,
        #        'swap_in': 0,
        #        'swap_out': 0
        #        }
        for key in set(self.mem_stats.keys()):
            ret[self.mem_stats[key]] = info[key]
        return ret

    def getStatsFields(self):
        return set(self.mem_stats.values())

    def getXMLQoSMetadata(self, uuid):
        return []

    def getVmBalloonInfo(self, uuid):
        domain = self._getDomainFromUUID(uuid)
        #info = self._domainGetInfo(domain)
        #if info is None:
        #    self.logger.error('Failed to get domain info')
        #    return None
        #ret =  {'balloon_max': info[1], 'balloon_cur': info[2],
        #        'balloon_min': self._getGuaranteedMemory(domain) }
        d = self.domains[domain]
        ret =  {'balloon_max': 5000, 'balloon_cur': d['balloon_cur'],
                'balloon_min': 0 }
        return ret

    def getXMLElementValue(self, xml, key):
        raise IndexError

    def getXMLQoSMetadata(self, uuid):
        return None

    def setVmBalloonTarget(self, uuid, target):
        #self.logger.info('set to uuid = %s' % uuid)
        dom = self._getDomainFromUUID(uuid)
        self.domains[dom]['balloon_cur'] = target

    def setVmCpuTune(self, uuid, quota, period):
        return
        #dom = self._getDomainFromUUID(uuid)
        #try:
        #    dom.setSchedulerParameters({ 'vcpu_quota': quota, 'vcpu_period': period})
        #except libvirt.libvirtError, e:
        #    self.logger.error("libvirtInterface: Exception while " \
        #            "setSchedulerParameters: %s", e.message);

    def ksmTune(self, tuningParams):
        pass

    def qemuAgentCommand(self, uuid, command, timeout=10):
        return None
        #import libvirt_qemu
        #dom = self._getDomainFromUUID(uuid)
        #if dom is None:
        #    return None
        #return libvirt_qemu.qemuAgentCommand(dom, command, timeout, 0)

def instance(config):
    return fakeInterface(config)
