#! /usr/bin/env python
import pylab as pl
import logging

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

from threading import Thread
import Queue

def work(plot):
    try:
        data = plot.queue.get_nowait()
        print 'New data arrived from Q.'
        plot.set_data(data)
        pl.draw()
        print 'Plot now should be updated...'
    except Queue.Empty:
        pass

class Plot(object):
    def __init__(self, fields=[]):
        self.data = {}
        self.fields = fields
        self.logger = logging.getLogger('mom.Plot')
        #pl.ioff() # disable interactivity on plot in window
        #pl.ion()
        self.logger.info('Interactive: %s', pl.isinteractive())
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 2

        # maintain ability asynchronous data update
        self.queue = Queue.Queue()

        # really necessary?
        self._refresh_plot()

        timer2 = self.figure.canvas.new_timer(interval=100)
        timer2.add_callback(work, self)

        # detach plot window to separate thread
        self.logger.info(pl)
        t = Thread(target=pl.show)
        t.daemon = True

        #t.start()
        timer2.start()
        #import pdb; pdb.set_trace()
        pl.show(block=False)

    def get_queue(self):
        """
        Return reference to interprocess shared queue. Put new item to this
        queue will cause add new set of data to plot and refresh that window.
        """
        return self.queue


    def _refresh_plot(self):
        # Example of data:
        # self.data[guest][field] = {'data': [1,2,3], 'line': <pylab.plot>}

        # subplot for each guest
        for guest in self.data:
            self.logger.info('Refreshing guest ' + guest + ', data: ' + str(self.data[guest]))
            for field in self.data[guest]:
                fl = self.data[guest][field]
                x = range(len(fl['data']))
                y = fl['data']

                #print 'guest: %s, field: %s, X=%s, Y=%s' % (guest, field, x, y)

                fl['line'].set_xdata(x)
                fl['line'].set_ydata(y)
            self.subplots[guest].relim()
            self.subplots[guest].autoscale_view(True, 'both', True)

    def _populate_subplots(self, data):
        """
        Prepare subplots according to sample data.
        It creates one subplot per host.
        """
        count = len(data)
        cols = int(count % self.subplots_width) + 1
        rows = int(count / self.subplots_width) + 1
        if count == self.subplots_width:
            cols = count
            rows = 1

        i = 1
        self.logger.info('Setup subplots: %s rows, %s cols' % (rows, cols))
        for guest in data:
            self.logger.debug("i %s", i)
            sub_plot = self.figure.add_subplot(rows, cols, i)
            self.logger.debug("add %s", i)
            sub_plot.grid(True)
            sub_plot.set_title(guest)
            self.subplots[guest] = sub_plot
            i += 1

    def set_data(self, data):
        """
        This method add new set of data. Multiple call add new values to
        existing lines in plot.
        Accept dict by this example:
            {'guest-1': {'mem_free': 123, 'mem_available': 300}}
        """
        # Only for first fime we need to populate all subplots
        if not self.data:
            self._populate_subplots(data)

        for guest, vals in data.iteritems():
            self.data.setdefault(guest, {})
            for field, value in vals.iteritems():
                # filter out unwanted data lines
                if field not in self.fields:
                    continue

                if field not in self.data[guest]:
                    plot_line = self.subplots[guest].plot([], [], 'o-')[0]
                    plot_line.set_label(field)
                    self.subplots[guest].legend()

                    line = {
                        'data': [],
                        'line': plot_line,
                    }
                    self.data[guest][field] = line

                #if self.data[guest][field]['data'] != []):
                self.data[guest][field]['data'].append(value)
        self._refresh_plot()
        pl.autoscale(tight=True)
        self.figure.canvas.draw()

def run():
    p = Plot(['balloon_cur', 'mem_free'])

    l = logging.getLogger('mom.LivePlotter')
    l.propagate = False
    l.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    l.addHandler(handler)
    p.logger = l

    p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    p.set_data({'host': {'mem_free': 1355836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4240164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.plot()

    t = Thread(target=pl.show)
    t.daemon = True

    # detach plot window to separate thread
    t.start()

    work(p, gen)
    sleep(0.5)
    work(p, gen)
    sleep(0.5)
    work(p, gen)
    sleep(0.5)
    work(p, gen)
    sleep(0.5)
    work(p, gen)
    sleep(0.5)

    #sleep(10)


if __name__ == '__main__':
    run()
