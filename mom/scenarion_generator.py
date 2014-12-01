#!/usr/bin/env python

# Generator sample data for MoM simulator

#def _setup_logger(self):
#    self.logger = logging.getLogger('mom.PlotLib')
#    self.logger.propagate = False
#    self.logger.setLevel(logging.DEBUG)
#
#    handler = logging.StreamHandler()
#    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#    handler.setFormatter(formatter)
#    handler.setLevel(logging.DEBUG)
#
#    self.logger.addHandler(handler)

import logging
import sys
import random
from textwrap import dedent

SHUTOFF = -1
NEWLINE = '\n'

class GuestBase(object):
    def __init__(self, name, max_mem, mem_start=None):
        """
        :param name identifier only for logging purpose
        :param max_mem maximum available memory that can guest got
        :param mem_start it means balloon_cur, must be <= than max_mem

        Guest is in stutoff state by default.
        """
        self.max_mem = max_mem
        self.name = name
        self.samples = []
        self.logger = logging.getLogger('mom.scenario_generator')

        # All samples would be multiplied by this value. This should avoid
        # mistakes from working with numbers that contains many digits (>4).
        self.scale = 1000

        if mem_start is None:
            mem_start = max_mem
        self.mem_start = mem_start
        self.memory = SHUTOFF

    def export_samples(self, width=8):
        """
        Return string with all data needed by mom simulator in correct format.
        :param width Produce aligned pretty-print output for better readability
        """
        ret = []
        # 1. maximum available memory
        ret.append(self.max_mem * self.scale)

        # 2. 'current' size of balloon, it means amount of RAM that guest
        # currently got from hypervisor.
        ret.append(self.mem_start * self.scale)

        # 3. fake value, because guest monitor thread starts after host monitor
        # and this loose first real sample. It's wouldn't be used for simulation.
        ret.append(SHUTOFF)

        # 4. all real samples
        def resample(val):
            if val == SHUTOFF:
                return val
            return val * self.scale

        ret.extend(map(resample, self.samples))

        #return ','.join([str(s) for s in ret])
        ret_str = ''
        fmt = '%'+str(width)+'s,'
        for s in ret:
            ret_str += fmt % s

        # cut off latest comma
        return ret_str[:-1]

    def add(self, amount):
        """
        Increase amount to current memory usage.
        """
        if self.momory + amount <= self.max_mem:
            self.memory += amount
            self.samples.append(self.memory)
        else:
            self.logger.error('.add exceedes max available memory (%s +%s > %s)'
                % (self.memory, amount, self.max_mem))

    def reduce(self, amount):
        """
        Substract amount from current memory usage.
        """
        new_mem = self.momory - amount
        if new_mem <= self.max_mem and new_mem > 0:
            self.memory -= amount
            self.samples.append(self.memory)
        else:
            self.logger.error('.reduce desired memory (%s) is out of interval: '
                              '0 < %s -%s <= %s' % (new_mem, self.memory,
                                                    amount, self.max_mem))

    def set(self, amount):
        """
        Set exact amount of memory to guest.
        """
        if amount <= self.max_mem:
            self.memory = amount
            self.samples.append(self.memory)
        else:
            self.logger.error('.set exceedes max available memory (%s +%s > %s)'
                % (self.memory, amount, self.max_mem))

    def no_change(self):
        """
        Just copy last used memory to list.
        """
        self.samples.append(self.memory)

    def stop(self):
        """
        At this moment is instance not running.
        """
        self.memory = SHUTOFF
        self.samples.append(self.memory)

    def start(self, amount):
        """
        Simulate transition from shutdown state to running.
        """
        self.set(amount)

    def rand_mean_as_curr(self):
        """
        Store current memory as mean parameter for Gaussian distribution
        """
        self.rand_const_mean = self.memory

    def random_norm(self, mean, deviation):
        """
        Set current memory as result of normal/Gaussian distributin.
        param: mean center of Gauss curve, if is None, local contstant value
               would be used. [MB]
        param: deviation scatter values, [MB]
        """
        if mean is None:
            mean = self.rand_const_mean

        new_usage = random.gauss(mean, deviation)
        new_usage = int(new_usage)
        self.set(new_usage)
        self.logger.debug('.random_norm set memory to %s (mean=%s, deviation=%s)'
                % (self.memory, mean, deviation))

class Guest(GuestBase):
    pass

class Host(GuestBase):
    def export_samples(self, width=8):
        """
        Return string with all data needed by mom simulator in correct format.
        :param width Produce aligned pretty-print output for better readability
        """
        ret = []
        # 1. maximum available memory
        ret.append(self.max_mem * self.scale)

        # 2. all real samples
        def resample(val):
            if val == SHUTOFF:
                return val
            return val * self.scale

        ret.extend(map(resample, self.samples))

        ret_str = ''
        fmt = '%'+str(width)+'s,'
        for s in ret:
            ret_str += fmt % s

        # cut off latest comma
        return ret_str[:-1]

class Simulator(object):
    def __init__(self, mem_max):
        self.host = Host('host', mem_max)
        self.guests = []
        random.seed(0)

    def add_guest(self, mem_max, balloon_curr):
        guest = Guest(len(self.guests), mem_max, balloon_curr)
        self.guests.append(guest)
        return guest

    def export(self, filename=None, comment=''):
        if filename:
            fd = open(filename, 'w+')
        else:
            fd = sys.stdout

        # Add comment to begining of output
        doc_lines = dedent(comment).splitlines()
        doc = map(lambda x: '# ' + x, doc_lines)
        fd.write(NEWLINE.join(doc) + NEWLINE)

        fd.write(self.host.export_samples() + NEWLINE)
        for g in self.guests:
            fd.write(g.export_samples() + NEWLINE)

def scenario_5vm_nice_regular_host():
    """
    5 guests, 16GB host (3GB of that is host's own stable usage)
    2GB per guest, small memory intensive changes (+/- 10MB)
    All guests are starting at one moment (sligtly more difficult for MoM).
    """
    sim = Simulator(16000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)

    sim.host.start(5000)
    for guest in sim.guests:
        guest.no_change()
        #guest.start(1000)

    #sim.host.no_change()
    for index in xrange(len(sim.guests)):
        sim.guests[index].start(1000)
    #for i in xrange(2 * len(sim.guests)):
    #    sim.host.no_change()
    #    for index in xrange(len(sim.guests)):
    #        if i / 2 == index:
    #            sim.guests[index].start(1000)
    #        sim.guests[index].no_change()

    # save current used memory as constant mean for upcomming Gauss rand.
    sim.host.rand_mean_as_curr()
    map(lambda x: x.rand_mean_as_curr(), sim.guests)

    for i in xrange(25):
        sim.host.random_norm(mean=None, deviation=15)

        # simulate some memory activity on guests.
        map(lambda x: x.random_norm(mean=None, deviation=15), sim.guests)

    doc = scenario_5vm_nice_regular_host.__doc__
    sim.export('scenario_5vm_nice_regular_host', comment=doc)


def scenario_5vm_ugly_regular_host():
    """
    5 guests, 16GB host (3GB of that is host's own stable usage)
    2GB per guest, significant memory intensive changes (+/- 20MB)
    All guests are starting at one moment (sligtly more difficult for MoM).
    """
    sim = Simulator(16000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)
    sim.add_guest(2000, 2000)

    sim.host.start(5000)
    for guest in sim.guests:
        guest.no_change()

    # launch all guests at the same moment
    sim.host.no_change()
    map(lambda x: x.start(1000), sim.guests)

    # save current used memory as constant mean for upcomming Gauss random
    sim.host.rand_mean_as_curr()
    map(lambda x: x.rand_mean_as_curr(), sim.guests)

    for i in xrange(25):
        # simulate some memory activity on host
        sim.host.random_norm(mean=None, deviation=15)

        # simulate some memory activity on guests
        map(lambda x: x.random_norm(mean=None, deviation=20), sim.guests)

    doc = scenario_5vm_nice_regular_host.__doc__
    sim.export('scenario_5vm_nice_regular_host', comment=doc)

def simulator():
    host = Host('host', 10000)
    num_guests = 2
    guest = [Guest(g, 2000, 2000) for g in xrange(num_guests)]

    # 0.
    host.start(7000)
    guest[0].stop()
    guest[1].stop()

    for i in xrange(2):
        host.no_change()
        guest[0].no_change()
        guest[1].no_change()

    # 3. start guest-1
    host.no_change()
    guest[0].start(1000)
    guest[1].stop()

    for i in xrange(3):
        host.no_change()
        guest[0].no_change()
        guest[1].no_change()

    # 7.
    host.no_change()
    guest[0].no_change()
    guest[1].start(1000)

    for i in xrange(15):
        host.no_change()
        guest[0].no_change()
        guest[1].no_change()

    # 11.
    host.no_change()
    guest[0].stop()
    guest[1].stop()

    for i in xrange(5):
        host.no_change()
        guest[0].no_change()
        guest[1].no_change()

    print host.export_samples()
    for g in guest:
        print g.export_samples()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    simulator()
    #scenario_5vm_nice_regular_host()
