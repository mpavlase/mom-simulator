#! /usr/bin/env python

import threading
import logging
from PlotLib import Plot

class LivePlotter(threading.Thread):
    def __init__(self, config, fields):
        super(LivePlotter, self).__init__(name='mom.LivePlotter')
        self.config = config
        self.logger = logging.getLogger('mom.LivePlotter')

        self.plot = Plot(fields)

    def set_data(self, data):
        self.plot.set_data(data)

    def run(self):
        try:
            print 'Live plotter start'
            self.logger.info("Live plotter starting")
            self.plot.show_window()
            print 'Live plotter end'
        except Exception as e:
            self.logger.error("Live plotter crashed", exc_info=True)
        else:
            self.logger.info("Live plotter ending")

