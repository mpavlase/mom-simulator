#! /usr/bin/env python
import pylab as pl
import logging
import json

import gtk

from matplotlib.figure import Figure
from numpy import arange, sin, pi

# uncomment to select /GTK/GTKAgg/GTKCairo
#from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

# or NavigationToolbar for classic
#from matplotlib.backends.backend_gtk import NavigationToolbar2GTK as NavigationToolbar
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler

import time

class Plot(object):
    def __init__(self):
        self.data = {}
        self.logger = logging.getLogger('mom.Plot')
        #pl.ioff() # disable interactivity on plot in window
        #pl.ion()
        #self.logger.info('Interactive: %s', pl.isinteractive())
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 2
        self.filename = 'plot.json'

    def plot(self):
        # clear plot window from previous data-lines
        pl.clf()

        t = time.time()
        # benchmark - start
        self.load()
        self._refresh_plot()
        # benchmark - end
        td = time.time() - t
        #self.logger.info('Benchmark: load and process input: %s', td)

        pl.autoscale(tight=True)
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
        if count == self.subplots_width:
            cols = count
            rows = 1

        # Key each sample is loaded from json as str() but for sorting etc. we
        # need it as ordinal int().
        for guest in self.data:
            sub_plot = self.figure.add_subplot(rows, cols, i)
            sub_plot.grid(True)
            sub_plot.set_title(guest)
            self.subplots[guest] = sub_plot
            i += 1

            for field in self.data[guest]:
                orig = self.data[guest][field]
                self.data[guest][field] = {}

                plot_line = self.subplots[guest].plot([], [], 'o-')[0]
                plot_line.set_label(field)
                self.subplots[guest].legend()

                line = {
                    'samples': {},
                    'line': plot_line,
                }
                self.data[guest][field] = line

                for key, val in orig.iteritems():
                    key = int(key)
                    self.data[guest][field]['samples'][key] = val
                #self.logger.warn(self.data[guest][field])
                #self.logger.info('.')

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
        """
        Updates values in displayed plot.
        Example of data:
        self.data[guest][field] = {
            'samples': {4: 100, 5: 110, 6: 105}, 'line': <pylab.plot>}
        """

        # subplot for each guest
        for guest in self.data:
            #self.logger.info('Refreshing guest ' + guest + ', data: ' + str(self.data[guest]))
            for field in self.data[guest]:
                fl = self.data[guest][field]
                samples = fl['samples']
                self._fill_gaps_in_samples(fl['samples'])
                x = samples.keys()
                y = samples.values()

                #print 'guest: %s, field: %s, X=%s, Y=%s' % (guest, field, x, y)

                fl['line'].set_xdata(x)
                fl['line'].set_ydata(y)
            self.subplots[guest].relim()
            self.subplots[guest].autoscale_view(True, 'both', True)

def run():
    p = Plot()

    l = logging.getLogger('mom.LivePlotter')
    l.propagate = False
    l.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    l.addHandler(handler)
    p.logger = l

    #p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.set_data({'host': {'mem_free': 1355836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4240164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})

    timer = p.figure.canvas.new_timer(interval=1000)
    timer.add_callback(p.plot)
    timer.start()

    p.plot()
    p.show()
    #p.set_data(data)
    #pl.draw()


if __name__ == '__main__':
    run()
