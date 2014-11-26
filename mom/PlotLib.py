#! /usr/bin/env python
import logging
import json

class Plot(object):
    def __init__(self, filename='plot.json', fields=[], scale=1.0):
        self.data = {}
        self.fields = fields
        self.scale = scale
        self.filename = filename
        self.i = 0
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger('mom.PlotLib')
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)

        self.logger.addHandler(handler)

    def save(self):
        """
        Export all stats info one JSON file, that can be easily read by other
        scripts.
        """
        self.logger.info(self.data)

        with open(self.filename, 'w+') as f:
            s = json.dumps(self.data, encoding='ascii', indent=2)
            print >> f, s

    def scale_value(self, value):
        """
        Increase/decrease values from set_data before save them into JSON.
        Can be used to recalculate values from kB to GB etc.
        """
        return value * self.scale

    def set_data(self, data):
        """
        This method add new set of data. Multiple call add new values to
        existing lines in plot.
        Accept dict by this example:
            {'guest-1': {'mem_free': 123, 'mem_available': 300}}
        """
        for guest, vals in data.iteritems():
            self.data.setdefault(guest, {})
            for field, value in vals.iteritems():
                # filter out unwanted data lines
                if field not in self.fields:
                    continue

                self.data[guest].setdefault(field, {})

                # Using dict for storing values of index, because guest can be
                # spawned in the middle simulation and therefore samples
                # wouldn't be continous.
                self.data[guest][field][self.i] = self.scale_value(value)
        self.i += 1
        self.save()

def run():
    p = Plot(['balloon_cur', 'mem_free'])

    p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    sleep(1.5)
    p.set_data({'host': {'mem_free': 1355836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4244164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    sleep(1.5)
    p.set_data({'host': {'mem_free': 1755836, 'mem_available': 10000000}, 'fake-vm-1': {'swap_usage': None, 'balloon_cur': 4240164, 'min_guest_free_percent': 0.201, 'min_balloon_change_percent': 0.0025, 'swap_total': None, 'max_balloon_change_percent': 0.05, 'balloon_min': 0, 'balloon_max': 5000000, 'mem_unused': 3244164}})
    sleep(1.5)


if __name__ == '__main__':
    run()
