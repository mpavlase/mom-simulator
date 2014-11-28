#! /usr/bin/env python
import pylab as pl
import logging
import json
import sys

import time

# Special name of guest that actually mean host (hypervisor). It was used to
# determine total amount of samples. Guests can be shutted of during mom run.
HOST = 'host'

class Plot(object):
    def __init__(self):
        self._setup_logger()
        self.data = {}
        #pl.ioff() # disable interactivity on plot in window
        #pl.ion()
        #self.logger.info('Interactive: %s', pl.isinteractive())
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 2
        self.filename = 'plot.json'
        self.benchmark = False

    def _setup_logger(self):
        self.logger = logging.getLogger('show_plot')
        self.logger.propagate = False
        self.logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)

        self.logger.addHandler(handler)

    def enable_benchmark(self):
        sefl.benchmark = True

    def plot(self):
        # clear plot window from previous data-lines
        pl.clf()

        t = time.time()
        # benchmark - start
        self.load()
        self._refresh_plot()
        # benchmark - end
        td = time.time() - t
        if self.benchmark:
            self.logger.info('Benchmark: load and process input: %s', td)

        #pl.autoscale(tight=True)
        self.figure.canvas.draw()

    def load(self):
        try:
            with open(self.filename, 'r') as f:
                new_data = json.load(f)
                self.data = new_data
                self.subplots = {}
                self._preprocess_data()
                #self.logger.info(self.data)
        except Exception, e:
            self.logger.error(e)

    def _preprocess_data(self):
        # Setup layout of all subplots
        i = 1
        count = len(self.data)
        cols = int(count % self.subplots_width) + 1
        rows = int(count / self.subplots_width) + 1
        if count <= self.subplots_width:
            cols = count
            rows = 1
        elif count == 1:
            cols = 1

        # Key each sample is loaded from json as str() but for sorting etc. we
        # need it as ordinal int().
        for guest in self.data:
            sub_plot = self.figure.add_subplot(rows, cols, i)
            sub_plot.grid(True, which='both')
            #sub_plot.minorticks_on()
            sub_plot.set_title(guest)
            self.subplots[guest] = sub_plot
            i += 1

            for field in self.data[guest]:
                orig = self.data[guest][field]
                self.data[guest][field] = {}

                plot_line = self.subplots[guest].plot([], [], '.-')[0]
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

        #self.logger.info(self.data)

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
                range_max = len(x)

            #print 'guest: %s, field: %s, X=%s, Y=%s' % (guest, field, x, y)
            line = fl['line']
            line.set_xdata(x)
            line.set_ydata(y)
        self.subplots[guest].relim()
        subplot = self.subplots[guest]

        self.subplots[guest].set_xlim([0, max(range_x, range_max)])
        self.subplots[guest].autoscale_view(True, False, True)

        return range_max

if __name__ == '__main__':
    p = Plot()

    timer = p.figure.canvas.new_timer(interval=1000)
    timer.add_callback(p.plot)
    timer.start()

    p.plot()
    p.show()
