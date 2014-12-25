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

# Guests which doesn't support balloon driver will utilize whole amount
# given memory from host. 
WITHOUT_BALLOON_DRIVER = 'c'

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
        self.balloon_available = True
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
        max_mem = self.max_mem * self.scale
        if not self.balloon_available:
            max_mem = WITHOUT_BALLOON_DRIVER + str(max_mem)
        ret.append(max_mem)

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

    def get_max_memory(self):
        return self.max_mem

    def add(self, amount):
        """
        Increase amount to current memory usage.
        """
        if self.memory + amount <= self.max_mem:
            self.memory += amount
            self.samples.append(self.memory)
        else:
            self.logger.error('.add exceedes max available memory (%s +%s > %s)'
                % (self.memory, amount, self.max_mem))

    def reduce(self, amount):
        """
        Substract amount from current memory usage.
        """
        new_mem = self.memory - amount
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
    def balloon_disable(self):
        self.balloon_available = False

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

        # adjust spaces to align guests samples (there is first fake sample)
        fmt_long = '%'+str(width*2 + 1)+'s,'
        fmt = '%'+str(width)+'s,'

        i = 0
        for s in ret:
            if i == 1:
                ret_str += fmt_long % s
            else:
                ret_str += fmt % s
            i += 1

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

###############################################################################
def scenario_1_host_swap():
    #sim.export('scenario_5vm_big_host', comment=doc)
    sim = Simulator(32000)
    sim.add_guest(8000, 8000)
    sim.add_guest(4000, 4000)
    sim.add_guest(12000, 12000)
    #[sim.guests[i].no_change() for i in [0, 4, 5]]
    #sim.guests[1].balloon_disable()
    g_dev = 20

    # Tick!
    sim.host.start(16000)
    sim.host.rand_mean_as_curr()

    # Tick!
    for i in xrange(2):
        sim.host.random_norm(mean=None, deviation=10)
        map(lambda guest: guest.no_change(), sim.guests)

    # Tick!
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].start(6000)
    sim.guests[0].rand_mean_as_curr()
    sim.guests[1].no_change()
    sim.guests[2].no_change()

    # Tick!
    for i in range(5):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        sim.guests[1].no_change()
        sim.guests[2].no_change()

    # Tick!
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].random_norm(mean=None, deviation=10)
    sim.guests[1].start(2000)
    sim.guests[1].rand_mean_as_curr()
    sim.guests[2].no_change()

    # Tick!
    for i in xrange(5):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        sim.guests[1].random_norm(mean=None, deviation=10)
        sim.guests[2].no_change()

    # Tick!
    sim.host.no_change()
    sim.guests[0].random_norm(mean=None, deviation=10)
    sim.guests[1].random_norm(mean=None, deviation=10)
    sim.guests[2].start(4500)
    sim.guests[2].rand_mean_as_curr()

    for x in range(30):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        sim.guests[1].random_norm(mean=None, deviation=10)
        sim.guests[2].random_norm(mean=None, deviation=10)

    sim.export('scenario.1.csv')

def scenario_2_big_host():
    sim = Simulator(64000)
    sim.add_guest(12000, 12000)
    sim.add_guest(12000, 12000)
    sim.add_guest(12000, 12000)

    # Tick! - start host
    sim.host.start(18000)
    sim.host.rand_mean_as_curr()

    # Tick!
    for i in xrange(2):
        sim.host.no_change()
        sim.guests[0].no_change()
        sim.guests[1].no_change()
        sim.guests[2].no_change()

    # Tick! - start 0
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].start(5000)
    sim.guests[0].rand_mean_as_curr()
    sim.guests[1].no_change()
    sim.guests[2].no_change()

    # Tick!
    for x in range(2):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        sim.guests[1].no_change()
        sim.guests[2].no_change()

    # Tick! - start 1
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].random_norm(mean=None, deviation=10)
    sim.guests[1].start(5000)
    sim.guests[1].rand_mean_as_curr()
    sim.guests[2].no_change()

    # Tick!
    for x in range(2):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        sim.guests[1].random_norm(mean=None, deviation=10)
        sim.guests[2].no_change()

    # Tick! - start 2
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].random_norm(mean=None, deviation=10)
    sim.guests[1].random_norm(mean=None, deviation=10)
    sim.guests[2].start(9500)
    sim.guests[2].rand_mean_as_curr()

    # Tick!
    guest1_start = 27
    for x in range(40):
        sim.host.random_norm(mean=None, deviation=10)
        sim.guests[0].random_norm(mean=None, deviation=10)
        #if sim.guest[1].get != SHUTOFF:
        #    guest1_latest = 
        if 15 < x < guest1_start:
            sim.guests[1].stop()
        elif x == guest1_start:
            sim.guests[1].start(5000)
        else:
            sim.guests[1].add(10)

        if x % 5 == 0:
            sim.guests[2].add(40)
            sim.guests[2].rand_mean_as_curr()
        else:
            sim.guests[2].random_norm(mean=None, deviation=10)

    sim.export('scenario.2.csv')

##############################################################################
##############################################################################
##############################################################################

def scenario_3_w_wo_balloon():
    sim = Simulator(24000)
    sim.add_guest(4000, 4000)
    sim.add_guest(4000, 4000)
    sim.add_guest(4000, 4000)
    sim.add_guest(4000, 4000)
    sim.add_guest(2000, 2000)
    sim.guests[2].balloon_disable()
    sim.guests[3].balloon_disable()

    # Tick!
    sim.host.start(3000)

    #sim.host.random_norm(mean=None, deviation=15)
    sim.host.rand_mean_as_curr()

    # Tick! - nothing
    for i in xrange(2):
        sim.host.no_change()
        map(lambda guest: guest.no_change(), sim.guests)

    # Tick! - start 0, 2
    sim.host.random_norm(mean=None, deviation=10)
    sim.guests[0].start(2000)
    sim.guests[0].rand_mean_as_curr()
    sim.guests[1].no_change()
    sim.guests[2].start(1000)
    sim.guests[2].rand_mean_as_curr()
    sim.guests[3].no_change()
    sim.guests[4].no_change()

    # Tick! - nothing
    for x in range(2):
        sim.host.no_change()
        map(lambda guest: guest.no_change(), sim.guests)

    # Tick! - start 4
    sim.host.no_change()
    sim.guests[4].start(1000)
    sim.guests[4].rand_mean_as_curr()
    map(lambda i: sim.guests[i].no_change(), [0, 1, 2, 3])

    # Tick! - nothing
    for x in range(2):
        sim.host.no_change()
        map(lambda guest: guest.no_change(), sim.guests)

    # Tick! - start 1, 3
    sim.host.no_change()
    map(lambda i: sim.guests[i].start(3000), [1, 3])
    map(lambda i: sim.guests[i].rand_mean_as_curr(), [1, 3])
    map(lambda i: sim.guests[i].no_change(), [0, 2, 4])

    # Tick!
    for x in range(30):
        sim.host.random_norm(mean=None, deviation=15)
        sim.guests[0].random_norm(mean=None, deviation=15)
        sim.guests[1].random_norm(mean=None, deviation=15)

        if x == 10:
            sim.guests[2].stop()
        elif x < 16:
            sim.guests[2].no_change()
        elif x == 16:
            sim.guests[2].start(700)
            sim.guests[2].rand_mean_as_curr()
        elif x > 16:
            sim.guests[2].random_norm(mean=None, deviation=15)

        sim.guests[3].random_norm(mean=None, deviation=15)
        sim.guests[4].add(15)

    sim.export('scenario.3.csv')

##############################################################################
##############################################################################
##############################################################################

def scenario_4_continous_reboot():
    sim = Simulator(16000)
    sim.add_guest(3000, 3000)
    sim.add_guest(3000, 3000)
    sim.add_guest(3000, 3000)
    sim.add_guest(3000, 3000)
    sim.add_guest(3000, 3000)

    # Tick!
    sim.host.start(3000)
    map(lambda guest: guest.no_change(), sim.guests)

    # each VM is described by (offset, on-length, cycle-length)
    program = [
        (1, 2, 4),
        (0, 5, 6),
        (1, 3, 6),
        (0, 4, 6),
        (0, 2, 3)]

    # main counter
    for i in xrange(25):
        sim.host.no_change()
        # iterate around all guests
        for g in range(5):
            offset, on, cycle = program[g]
            index = (i + offset) % cycle
            if index < on:
                sim.guests[g].start(1200)
            else:
                sim.guests[g].stop()

    sim.export('scenario.4.csv')

def pokus():
    sim = Simulator(10000)
    guest = sim.add_guest(5000, 5000)

    # Tick!
    sim.host.start(7000)
    guest.no_change()

    sim.host.no_change()
    guest.start(1200)

    for x in range(2):
        sim.host.no_change()
        guest.no_change()

    for x in range(3):
        sim.host.no_change()
        guest.stop()

    sim.host.no_change()
    guest.start(1200)

    for x in range(2):
        sim.host.no_change()
        guest.no_change()

    sim.export('scenario.4.csv')

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)

    scenario_1_host_swap()          # done
    scenario_2_big_host()           # done
    scenario_3_w_wo_balloon()
    scenario_4_continous_reboot()
    #pokus()
