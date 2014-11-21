# Memory Overcommitment Manager
# Copyright (C) 2010 Adam Litke, IBM Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import re
import sys
import logging

class Collector:
    """
    Collectors are plugins that return a specific set of data items pertinent to
    a given Monitor object every time their collect() method is called.  Context
    is given by the Monitor properties that are used to init the Collector.
    """
    def __init__(self, properties):
        """
        The Collector constructor should use the passed-in properties to
        establish context from its owning Monitor.
        Override this method when creating new collectors.
        """
        pass

    def collect(self):
        """
        The principle interface for every Collector.  This method is called by a
        monitor to initiate data collection.
        Override this method when creating new collectors.
        Return: A dictionary of statistics.
        """
        return {}

    def getFields(self=None):
        """
        Used to query the names of mandatory statistics fields that this
        Collector will return.
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set()

    def getOptionalFields(self=None):
        """
        Used to query the names of optional statistics fields that this
        Collector will return.
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set()

    @staticmethod
    def getConstants():
        """
        Some rules may contain constants (tresholds etc.), this method provide
        these as dict. These values can be present in file with rules itself,
        or can be read from XML definition of libirt domain from <qos> element
        (inside <metadata>).
        Return: dict of constants, that can be "injected" into rules.
        """
        return {}

    def refreshConstants(self):
        """
        Sometimes we need to let collector reload values of constats. It can be
        done automaticly just by clear their values.
        """

        # TODO: Vicked, vicked, Zoot!
        try:
            self.const_fields = {}.fromkeys(self.getConstants().keys())
        except AttributeError:
            """
            const_fields are not used on current collector.
            """
            logger = logging.getLogger('mom.Collector.refreshConstants')
            logger.info('Cleanup without any effect - collector does\'t '\
                        'provide any constants.')

    def _collect_const_fields(self):
        """
        Values are used only if hypervisor isn't able to provide its own values.
        """

        # do not anything if collector doesn't provide any constants
        # TODO: Vicked, vicked, Zoot!
        try:
            if self.const_fields:
                pass
        except AttributeError:
            return {}

        logger = logging.getLogger('mom.Collector._collect_const_fields')
        ret_fields = {}
        metadata_xml = self.hypervisor_iface.getXMLQoSMetadata(self.uuid)
        hv_consts = self.getConstants()
        for k, v in self.const_fields.iteritems():
            if v:
                #logger.info('%s = %s' % (k, v))
                ret_fields[k] = v
            else:
                try:
                    hv_field = self.hypervisor_iface.getXMLElementValue( \
                        metadata_xml, k)
                    self.const_fields[k] = float(hv_field)
                    logger.debug('Using default value %s for %s provided '\
                                 'by XML of VM.' % (self.const_fields[k], k))
                except IndexError as e:
                    self.const_fields[k] = hv_consts[k]
                    logger.warning('Using default value %s for %s from ' \
                                   'collector plugin.' % \
                                    (self.const_fields[k], k))
                ret_fields[k] = self.const_fields[k]
        return ret_fields

def get_collectors(config_str, properties, global_config):
    """
    Initialize a set of new Collector instances for a Monitor.
    Return: A list of initialized Collectors
    """
    logger = logging.getLogger('mom.Collector')
    collectors = []

    # Make sure we don't clobber an existing entry in the properties dict
    if 'config' in properties:
        logger.error("Internal Error: 'config' not allowed in Monitor properties")
        return None

    for name in config_str.split(','):
        name = name.lstrip()
        if name == '':
            continue

        # Check for Collector-specific configuration in the global config
        section = "Collector: %s" % name
        if global_config.has_section(section):
            properties['config'] = dict(global_config.items(section, raw=True))

        # Create an instance
        try:
            module = __import__('mom.Collectors.' + name, None, None, name)
            collectors.append(getattr(module, name)(properties))
        except ImportError, e:
            logger.warn("Unable to import collector: %s, because:\n%s" % (name, e))
            return None
        except FatalError, e:
            logger.error("Fatal Collector error: %s", e.msg)
            return None
    return collectors

#
# Collector Exceptions
#
class CollectionError(Exception):
    """
    This exception should be raised if a Collector has a problem during its
    collect() operation and it cannot return a complete, coherent data set.
    """
    def __init__(self, msg):
        self.msg = msg

class FatalError(Exception):
    """
    This exception should be raised if a Collector has a permanent problem that
    will prevent it from initializing or collecting any data.
    """
    def __init__(self, msg):
        self.msg = msg

#
# Collector utility functions
#
def open_datafile(filename):
    """
    Open a data file for reading.
    """
    try:
        filevar = open(filename, 'r')
    except IOError, (errno, strerror):
        logger = logging.getLogger('mom.Collector')
        logger.error("Cannot open %s: %s" % (filename, strerror))
        sys.exit(1)
    return filevar

def parse_int(regex, src):
    """
    Parse a body of text according to the provided regular expression and return
    the first match as an integer.
    """
    m = re.search(regex, src, re.M)
    if m:
        return int(m.group(1))
    else:
        return None

def count_occurrences(regex, src):
    """
    Parse a body of text according to the provided regular expression and return
    the count of matches as an integer.
    """
    m = re.findall(regex, src, re.M)
    if m:
        return len(m)
    else:
        return None
