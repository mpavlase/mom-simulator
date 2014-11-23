#! /usr/bin/env python

import threading
import logging
from PlotLib import Plot

class LivePlotter(threading.Thread):
    def __init__(self, config, fields):
        super(LivePlotter, self).__init__(name='mom.LivePlotter')
        self.config = config
        self.logger = logging.getLogger('mom.LivePlotter')

        #self.plot = Plot(fields)
        self.queue = self.plot.get_queue()

    def set_data(self, data):
        """
        Allow innter plot timer to pickup new data when it will be available,
        not just now.
        """
        #self.plot.queue.put_task(data)
        pass

    #def run(self):
    #    try:
    #        print 'Live plotter start'
    #        self.logger.info("Live plotter starting")
    #        self.plot.show_window()
    #        print 'Live plotter end'
    #    except Exception as e:
    #        self.logger.error("Live plotter crashed", exc_info=True)
    #    else:
    #        self.logger.info("Live plotter ending")

