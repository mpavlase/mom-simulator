#! /usr/bin/env python
import pylab as pl
import logging

import gtk
import gobject

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
import random
from time import sleep
import Queue

class UpdatePlotThread(Thread):
    def __init__(self, plot):
        super(UpdatePlotThread, self).__init__()
        self.plot = plot

    def run(self):
        print 'start worker...'
        while True:
            print 'waiting to next item...'
            data = self.plot.queue.get()
            #data = self.plot.queue.get_nowait()
            print 'thread worker: New data arrived! %s' % data
            self.plot.set_data(data)
            self.plot.queue.task_done()

class Plot(object):
    def __init__(self, fields=[]):
        self.data = {}
        self.fields = fields
        self.logger = logging.getLogger('mom.Plot')
        #pl.ioff() # disable interactivity on plot in window
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 2

        # maintain ability asynchronous data update
        self.queue = Queue.Queue()
        t = UpdatePlotThread(self)
        t.daemon = True

        win = gtk.Window()
        win.connect("destroy", lambda x: gtk.main_quit())
        win.set_default_size(400,300)
        win.set_title("MoM live plot")

        vbox = gtk.VBox()
        win.add(vbox)
        # ----------------------------
        self.canvas = FigureCanvas(self.figure)  # a gtk.DrawingArea
        vbox.pack_start(self.canvas)
        toolbar = NavigationToolbar(self.canvas, win)
        vbox.pack_start(toolbar, False, False)
        win.show_all()
        # ----------------------------
        i = 7
        data = {'host': {'mem_free': i}, 'fake-vm-1': {'balloon_cur': i if i % 2 == 0 else -i }}
        self.queue.put(data)
        #self.set_data(data)
        # ----------------------------
        t.start()

    def get_queue(self):
        """
        Return reference to interprocess shared queue. Put new item to this
        queue will cause add new set of data to plot and refresh that window.
        """
        return self.queue

    def show_window(self):
        """
        This method is blocking until window with plot is closed.
        """
        gtk.main()

    def _refresh_plot(self):
        # Example of data:
        # self.data[guest][field] = {'data': [1,2,3], 'line': <pylab.plot>}

        # subplot for each guest
        for guest in self.data:
            self.logger.info('Refreshing guest ' + guest)
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
            sub_plot = self.figure.add_subplot(rows, cols, i)
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
        self.canvas.draw_idle()
        self.canvas.draw()

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

    #p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.set_data({'host': {'mem_free': 1355836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4240164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    #p.plot()

    q = p.get_queue()

    i = 12
    data = {'host': {'mem_free': i}, 'fake-vm-1': {'balloon_cur': i if i % 2 == 0 else -i }}
    print 'a 12'
    q.put(data)
    print 'b 12'

    i = 3
    data = {'host': {'mem_free': i}, 'fake-vm-1': {'balloon_cur': i if i % 2 == 0 else -i }}
    ##p.set_data(data)
    print 'a 3'
    q.put(data)
    print 'b 3'

    #i = 7
    #data = {'host': {'mem_free': i}, 'fake-vm-1': {'balloon_cur': i if i % 2 == 0 else -i }}
    ##p.set_data(data)
    #print 'a'
    #q.put(data)
    #print 'b'



    #i = 0
    #global i
    #def update():
    #    #try:
    #    #    i = q.get()
    #    #except Exception:
    #    #    return True

    #    #i = random.randrange(1, 20)
    #    global i
    #    print 'worker i=%s' % i
    #    data = {'host': {'mem_free': i}, 'fake-vm-1': {'balloon_cur':
    #        i if i % 2 == 0 else -i }}
    #    p.set_data(data)
    #    #q.task_done()
    #    i += 1
    #    return True
    #gobject.timeout_add(5000, update)
    #gobject.idle_add(lambda: True)
    #gobject.timeout_add(1000, lambda: True)
    p.show_window()

#class Worker(Thread):
#    def __init__(self, queue, plot=None):
#        super(Worker, self).__init__()
#        self.plot = plot
#        self.queue = queue
#        #self.i = 0
#
#    def run(self):
#        print 'start worker...'
#        while True:
#            data = self.queue.get()
#            #i = self.i
#            print 'thread worker: New data arrived! %s' % data
#            #data = {'host': {'mem_free': 10 + i}, 'fake-vm-1': {'balloon_cur':
#            #    i if i % 2 == 0 else -i }}
#            self.p.set_data(data)
#            self.queue.task_done()
#            #global q
#            #q.put(self.i)
#            #self.i += 1
#            #sleep(6)

#class WorkerWindow(Thread):
#    def __init__(self, plot):
#        super(WorkerWindow, self).__init__()
#        self.p = plot
#
#    def run(self):
#        #print 'pre run %s' % self.p.show_window()
#        while True:
#            try:
#                self.p.show_window()
#            except:
#                pass
#        #print 'post run'


if __name__ == '__main__':
    run()
