# Memory Overcommitment Manager
# Copyright (c) 2014 Martin Pavlasek, Red Hat Corporation
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
import logging
from subprocess import *
from mom.HypervisorInterfaces.HypervisorInterface import *
from mom.Collectors.Collector import FatalError as CollectorFatalError

# This is special value that can be used in balloon_cur and means that VM is in
# shutdown state.
VM_SHUTDOWN = -1

def tis(num):
    return '{0:,}'.format(num)

class fakeInterface(HypervisorInterface):
    """
    fakeInterface provides interface to simulate MoM behaviour with various
    params. At this moment there is support for host and guest memory with
    mem balloon. Input is simple plain-text file in CSV values.
    You can find format description at begging of _parse_sample_file method.
    """
    def __init__(self, config):
        self.logger = logging.getLogger('mom.fakeInterface')
        self.mem_stats = ('mem_unused', '_mem_used')
        #self.domains = {
        #    'fake-vm-1': {
        #        'uuid': 'uuid-1',
        #    }
        #}
        #self.domains['fake-vm-1'].update(def_mem_stat)

        sample_file = config.get('simulator', 'source-file')
        self.logger.info('Using "%s" as source data for simulation.' % sample_file)

        self.domains = {}

        # This simulate constant memory utilization by host OS etc.
        self._parse_sample_file(sample_file)
        self.sample_index = -1

    def _parse_sample_file(self, filename):
        """
        Format description:
        It is like CSV (comma separated values).
        First line contains 'host' variables:
            - amount of whole host memory in kB,
            - amount used memory by host OS
        Each next upcomming line describe utilization memory inside VM:
            - maximum available memory that VM can allocate,
            - each next value is current memory usage by VM

        But there is one special value for VMs:
            - '-1' that means that VM in in shutted-off state.

        Example:
        8055976, 230000, 230000, 230000, 230000, 230000
        1048576, 320000, 325000, 340000, 340000, 330000
        524288,  200000, 210000, 220000, -1,     -1
        """


        with open(filename, 'r') as f:
            # each next line act as VM memory utilization
            vm_number = 0
            for line in f.readlines():
                line = line.strip()

                # skip blank and commented lines
                if line == '' or line[0] == '#':
                    self.logger.warn('Skipping source line %s' % line)
                    continue

                samples = self._parse_csv(line)
                # parse maximum available host memory
                max_mem = samples.pop(0)

                # store first valid line separaly as host samples
                if vm_number == 0:
                    self.host_available_mem = max_mem
                    self.host_samples = samples
                    self.logger.error('host.available: %s' % tis(self.host_available_mem))
                    self.logger.error('host.samples: %s' % self.host_samples)
                    vm_number += 1
                    continue

                curr_balloon = samples.pop(0)
                curr_mem_used = samples[0]

                domain = {'fake-vm-' + str(vm_number): {
                        'uuid': 'uuid-' + str(vm_number),
                        'balloon_cur': curr_balloon,
                        'balloon_min': 0,
                        'balloon_max': max_mem,
                        'mem_unused': max_mem - curr_mem_used,
                        'mem_usage_samples': samples,
                    }
                }
                #self.logger.error(domain)
                #self.logger.error(curr_mem_used)
                self.domains.update(domain)
                vm_number += 1

    @staticmethod
    def _parse_csv(line):
        """
        Method parse one line in CSV format to separated values and convert
        them into integers.
        """
        samples = re.split(',\s*', line)
        samples = map(lambda x: int(x), samples)
        return samples

    def _get_current_sample(self, source):
        """
        This method pick current sample from list. When someone ask for more
        samples that is currently available, it get last used value.
        """
        samples_len = len(source)
        self.logger.warn('Trying get %s. index from %s' % (self.sample_index, source))
        try:
            curr_sample = source[self.sample_index]
            self.logger.warn('Its... %s' % (curr_sample))
        except IndexError:
            curr_sample = source[samples_len - 1]
            self.logger.warn('Simulated resource is running out of samples '
                             '(%d > %d). Using latest value (%s)' %
                             (self.sample_index, samples_len, curr_sample))
            # This exception will cause shutdown whole MoM (as simulation)
            raise CollectorFatalError('Simulated resource is running out of samples.')
        return curr_sample

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

    def getHostMemoryStats(self):
        """
        Simulate host memory utilization by VMs. At this moment, we don't
        count with other factors such as memory-consuming processes
        running on host.
        """
        used = [vm['balloon_cur'] for vm in self.domains.itervalues()
                if self.sample_index >= 0 and self._get_current_sample(vm['mem_usage_samples']) != VM_SHUTDOWN]
        used_by_vm = sum(used)

        #used_by_vm = 0
        #for guest, vm in self.domains.iteritems():
        #    sample = self._get_current_sample(vm['mem_usage_samples'])
        #    self.logger.debug('getHostMemoryStats guest %s has current mem_usage %s' % (guest, sample))

        #    if sample != VM_SHUTDOWN:
        #        self.logger.debug('getHostMemoryStats guest %s is alive.' % (guest, ))
        #        used_by_vm += sample

        #for guest, vm in self.domains.iteritems():
        #    cur = vm['balloon_cur']
        #    self.logger.error('Guest %s, balloon_cur = %s' % (guest, cur))

        #used = [vm['balloon_cur'] for vm in self.domains]
        used_by_host = self._get_current_sample(self.host_samples)

        used = used_by_vm + used_by_host
        self.logger.error('getHostMemoryStats used: %s (by VMs: %s), by host itself: %s' % (tis(used), tis(used_by_vm), tis(used_by_host)))

        data = {'mem_available': self.host_available_mem,
                'mem_free': self.host_available_mem - used,
                '_mem_used': used,
        }
        self.logger.error('getHostMemoryStats = %s' % (data))
        return data

    def getVmList(self):
        ret = []
        self.sample_index += 1
        self.logger.info('\n\n\n\n\nNew iteration [%s]...' % self.sample_index)

        for k, v in self.domains.iteritems():
            try:
                #if v['mem_usage_samples'][self.sample_index] != VM_SHUTDOWN:
                if self._get_current_sample(v['mem_usage_samples']) != VM_SHUTDOWN:
                    ret.append(k)
            except IndexError, e:
                self.logger.debug('getVmList got %s' % s)
                pass
        self.logger.info('XX list = %s' % ret)
        return ret

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
        self.logger.info('getVmMemoryStats TICK!')
        domain = self._getDomainFromUUID(uuid)
        info = self.domains[domain]
        self.logger.info(info)
        ret = {}
        #info = self._domainGetMemoryStats(domain)
        curr_mem_used = self._get_current_sample(info['mem_usage_samples'])
        info['_mem_used']= curr_mem_used

        for key in self.mem_stats:
            ret[key] = info[key]
            if key == 'mem_unused':
                ret[key] = info['balloon_cur'] - curr_mem_used
        self.logger.debug('Domain %s USING ' % (domain) + '{0:,}'.format(curr_mem_used) + ' kB of memory')
        self.logger.debug('Domain %s returned getVmSstats: %s ' % (domain, ret))
        return ret

    def setVmBalloonTarget(self, uuid, target):
        dom = self._getDomainFromUUID(uuid)
        self.logger.info('New memballoon value %s for %s' % (tis(target), dom))
        self.domains[dom]['balloon_cur'] = target

    def getVmBalloonInfo(self, uuid):
        domain = self._getDomainFromUUID(uuid)

        # balloon_min originally came from <qos> element from domain XML
        d = self.domains[domain]
        ret =  {'balloon_max': d['balloon_max'], 'balloon_cur': d['balloon_cur'],
                'balloon_min': 0 }
        self.logger.info('memballoon info %s for %s' % (ret, domain))
        return ret

    def getStatsFields(self):
        return set(self.mem_stats)

    def getXMLQoSMetadata(self, uuid):
        return []

    def getXMLElementValue(self, xml, key):
        raise IndexError

    def getXMLQoSMetadata(self, uuid):
        return None

    def setVmCpuTune(self, uuid, quota, period):
        return

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
