#! /usr/bin/env python
import pylab as pl
import logging

class Plotter(object):
    def __init__(self, fields=[]):
        self.data = {}
        self.fields = fields
        logger = logging.getLogger('mom.LivePlotter')
        self.logger = logger
        #pl.ioff()
        #pl.grid(True)
        self.figure = pl.figure()
        self.subplots = {}
        self.subplots_width = 2
        self.figure.show()

    def plot(self):
        pl.autoscale(tight=True)
        self.figure.canvas.draw()
        #self.logger.info('Current plot  data: %s' % self.data)

    def _refresh_plot(self):
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

    def set_data(self, data):
        # Only for first fime we need to populate all subplots
        if not self.data:
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
        #print self.data
        self._refresh_plot()

def run():
    p = Plotter(['balloon_cur', 'mem_free'])

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
    #p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4240164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    p.plot()

if __name__ == '__main__':
    run()
