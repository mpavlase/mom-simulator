#! /usr/bin/env python

from argparse import ArgumentParser
import pylab as pl
import logging
import json
import sys
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, FuncFormatter
import time
import math

# Special name of guest that actually mean host (hypervisor). It was used to
# determine total amount of samples. Guests can be shutted of during mom run.
HOST = 'host'

def bit_formatter(size, pos):
    sign = ''
    if size < 0:
        sign = '-'
        size = abs(size)
    scale = ('kB', 'MB', 'GB')
    print size
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size/p, 2)
    if (s > 0):
        return '%s%s %s' % (sign, s, scale[i])
    else:
        return '0'

class Plot(object):
    def __init__(self):
        self._setup_logger()
        self.data = {}
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 1
        self.set_source_data('plot.json')
        self.benchmark = False

    def set_plot_width(self, n):
        self.subplots_width = n

    def set_source_data(self, filename):
        self.filename = filename

    def _setup_logger(self):
        self.logger = logging.getLogger('show_plot')
        self.logger.propagate = False
        self.logger.setLevel(logging.ERROR)
        #self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)

        self.logger.addHandler(handler)

    def enable_benchmark(self):
        self.benchmark = True

    def plot(self):
        # clear plot window from previous data-lines
        pl.clf()

        t = time.time()
        # benchmark - start
        self._load()
        self._refresh_plot()
        # benchmark - end
        td = time.time() - t
        if self.benchmark:
            self.logger.info('Benchmark: load and process input: %s', td)

        #pl.autoscale(tight=True)
        self.figure.canvas.draw()

    def _load(self):
        try:
            with open(self.filename, 'r') as f:
                new_data = json.load(f)
                self.subplots = {}
                self._preprocess_data(new_data)
                #self.logger.info(self.data)
        except Exception, e:
            self.logger.error(e)

    def _preprocess_data(self, data):
        # Setup layout of all subplots
        # this is index of subplot in figure (window)
        i = 1
        self.data = {}
        count = len(data)
        rows = math.ceil(1.0 * count / self.subplots_width)
        cols = self.subplots_width
        if count <= self.subplots_width:
            cols = count
            rows = 1
        elif count == 1:
            cols = 1

        # Key each sample is loaded from json as str() but for sorting etc. we
        # need it as ordinal int().a
        y_formatter = FuncFormatter(bit_formatter)
        all_guests = set(data.keys())
        guests_list = all_guests - set([HOST])
        guests_list = sorted(guests_list)
        guests_list.insert(0, HOST)
        for guest in guests_list:
            self.data[guest] = {}
            sub_plot = self.figure.add_subplot(rows, cols, i)
            sub_plot.grid(True, which='both')
            #sub_plot.xaxis.set_minor_locator(MultipleLocator(1))
            #sub_plot.xaxis.set_minor_formatter(FormatStrFormatter('%d'))
            #sub_plot.yaxis.set_major_formatter(y_formatter)
            #sub_plot.minorticks_on()
            sub_plot.set_xlabel('No. sample [-]')
            sub_plot.set_ylabel('Memory [MB]')
            sub_plot.set_title(guest)
            self.subplots[guest] = sub_plot
            i += 1

            for field in data[guest]:
                orig = data[guest][field]
                self.data[guest][field] = {}

                plot_line = self.subplots[guest].plot([], [], '.-')[0]

                # label that starts with '_' is not shown in legend.
                label = '(' + field + ')' if field[0] == '_' else field
                self.logger.debug(label)
                plot_line.set_label(label)
                self.subplots[guest].legend(loc='best', fontsize='medium')

                line = {
                    'samples': {},
                    'line': plot_line,
                }
                self.data[guest][field] = line

                for key, val in orig.iteritems():
                    key = int(key)
                    self.data[guest][field]['samples'][key] = val
                self.logger.warn('guest %s, field %s: %s' % (guest, field, self.data[guest][field]))
                self.logger.info('.')

        self.logger.info(self.data)

    def show(self):
        """
        This method blocks exection until is plot window closed.
        """
        pl.show()

    def _fill_gaps_in_samples(self, samples):
        """
        samples are dict, key = index in data row. It's not necessary to
        have it continuous. This method will fill missing gaps with None,
        that makes graph also non-continuous. Working 'in place'.
        """
        list_indexes = samples.keys()
        current_indexes = set(list_indexes)
        # pick last used index as whole continuous array
        size = list_indexes[-1]
        all_indexes = set(range(size))

        missing_keys = all_indexes.difference(current_indexes)

        for index in missing_keys:
            samples[index] = None

    def _refresh_plot(self):
        all_guests = set(self.data.keys())
        guests = all_guests - set([HOST])

        if HOST in all_guests:
            range_x = self._refresh_guest(HOST)
            self.logger.debug('host has %s samples.' % range_x)
        else:
            self.logger.warn('Input data doesn\'t contain host samples, plot '
                             'would be probablu broken')
            range_x = None

        for g in guests:
            self._refresh_guest(g, range_x)

    def _refresh_guest(self, guest, range_x=None):
        """
        Updates values in displayed plot.
        Example of data:
        self.data[guest][field] = {
            'samples': {4: 100, 5: 110, 6: 105}, 'line': <pylab.plot>}
        """

        range_max = None
        for field in self.data[guest]:
            fl = self.data[guest][field]
            self.logger.info('guest %s, field %s:%s' % (guest, field, fl))
            samples = fl['samples']
            self._fill_gaps_in_samples(fl['samples'])
            x = samples.keys()
            y = samples.values()

            if len(x) > range_max:
                range_max = len(x) - 1

            self.logger.debug('guest: %s, field: %s, X=%s, Y=%s' %
                              (guest, field, x, y))
            line = fl['line']
            line.set_xdata(x)
            line.set_ydata(y)
        self.subplots[guest].relim()
        subplot = self.subplots[guest]

        self.subplots[guest].set_xlim([0, max(range_x, range_max)])
        self.subplots[guest].autoscale_view(True, False, True)

        return range_max

if __name__ == '__main__':
    parser = ArgumentParser(description='Simple utility for displaying output '
                                        'of MoM (Memory overcommit Manager)')
    parser.add_argument('-f', '--file', action='store', default='plot.json',
                        dest='file', required=False,
                        help='Input file as source data to plot. '
                             'Default: %(default)s')
    parser.add_argument('-i', '--interval', nargs='?', const='1',
                        dest='interval', required=False,
                        help='Enable auto-reload source file, interval in '
                             'seconds. By default is disable.')
    parser.add_argument('-w', '--width', required=False,
                        dest='width', action='store',
                        help='Width grid of subplots, default 1')
    params = parser.parse_args()


    p = Plot()
    p.set_source_data(params.file)
    if params.width:
        p.set_plot_width(int(params.width))

    p.plot()

    if params.interval:
        i = int(int(params.interval) * 1000)
        timer = p.figure.canvas.new_timer(interval=i)
        timer.add_callback(p.plot)
        timer.start()

    p.show()
