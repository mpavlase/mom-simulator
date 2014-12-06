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

import logging
import math

class EntityError(Exception):
    def __init__(self, message):
        self.message = message

class Entity:
    """
    An entity is an object that is designed to be inserted into the rule-
    processing namespace.  The properties and statistics elements allow it to
    contain a snapshot of Monitor data that can be used as inputs to rules.  The
    rule-accessible methods provide a simple syntax for referencing data.
    """
    def __init__(self, monitor=None):
        self.properties = {}
        self.variables = {}
        self.statistics = []
        self.controls = {}
        self.monitor = monitor
        self.logger = logging.getLogger('mom.Entity')

    def _set_property(self, name, val):
        self.properties[name] = val

    def _set_variable(self, name, val):
        self.variables[name] = val

    def _set_statistics(self, stats):
        for row in stats:
            self.statistics.append(row)

    def _store_variables(self):
        """
        Pass rule-defined variables back to the Monitor for storage
        """
        if self.monitor is not None:
            self.monitor.update_variables(self.variables)

    def _finalize(self):
        """
        Once all data has been added to the Entity, perform any extra processing
        """
        # Add the most-recent stats to the top-level namespace for easy access
        # from within rules scripts.
        if len(self.statistics) > 0:
            for stat in self.statistics[-1].keys():
                setattr(self, stat, self.statistics[-1][stat])

    def _disp(self, name=''):
        """
        Debugging function to display the structure of an Entity.
        """
        prop_str = ""
        stat_str = ""
        for i in self.properties.keys():
            prop_str = prop_str + " " + i

        if len(self.statistics) > 0:
            for i in self.statistics[0].keys():
                stat_str = stat_str + " " + i
        else:
            stat_str = ""
        print "Entity: %s {" % name
        print "    properties = { %s }" % prop_str
        print "    statistics = { %s }" % stat_str
        print "}"

    ### Rule-accesible Methods
    def Prop(self, name):
        """
        Get the value of a single property
        """
        return self.properties[name]

    def Stat(self, name):
        """
        Get the most-recently recorded value of a statistic
        Returns None if no statistics are available
        """
        if len(self.statistics) > 0:
            return self.statistics[-1][name]
        else:
            return None

    def StatAvg(self, name):
        """
        Calculate the average value of a statistic using all recent values.
        """
        if (len(self.statistics) == 0):
            raise EntityError("Statistic '%s' not available" % name)
        total = 0
        for row in self.statistics:
            if name in row:
                total = total + row[name]
        return float(total / len(self.statistics))

    def StatStdDeviation(self, name):
        """
        Calculate standart deviation of all values in statistic-stack.
        If there is not such name of statistic in past snapshot, return None.
        """
        vals = []
        for row in self.statistics:
            if name in row:
                vals.append(row[name])

        if not vals:
            return None

        count = len(vals)
        average = float(sum(vals)) / count
        sum_pow2 = sum(map(lambda x: x**2, vals))
        stdev = math.sqrt(1.0 / count * sum_pow2 - average ** 2)
        return stdev

    def SetVar(self, name, val):
        """
        Store a named value in this Entity.
        """
        self.variables[name] = val

    def UpdateStatVal(self, name, val):
        """
        Change value of 'name' stat. Updated value is propagated to Monitor,
        where is stored to another tick of interval. This can be used to
        calculate stats set of values that doesn't exists in collectors.
        """
        self.statistics[-1][name] = val
        setattr(self, name, self.statistics[-1][name])
        self.monitor.update_statistics_variable(name, val)

    def GetVmName(self):
        """
        Get name of VM
        """
        return self.monitor.name

    def GetVar(self, name):
        """
        Get the value of a potential variable in this instance.
        Returns None if the variable has not been defined.
        """
        if name in self.variables:
            return self.variables[name]
        else:
            return None

    def Control(self, name, val):
        """
        Set a control variable in this instance.
        """
        self.controls[name] = val

    def GetControl(self, name):
        """
        Get the value of a control variable in this instance if it exists.
        Returns None if the control has not been set.
        """
        if name in self.controls:
            return self.controls[name]
        else:
            return None
