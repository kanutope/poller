""" module: poller module

    v2.0 - introducing priority levels
        which allows to have multipple tasks (functions) executed at the same time,
        i.e. with the same frequency, though in order of priority.
"""
from dataclasses import dataclass
from decimal import Decimal, getcontext
from math import log10
import time

from commons import epoch2str


@dataclass
class Periodic:
    """ base record structure
    """
    def __init__(self, period, func=None, delay=0, prio=0):
        """ initialising
        """
        tim = time.time()
        self.period = period
        div, rem = divmod(tim, period)
        self.previous = div * period
        self.passed = 0
        self.function = func
        self.delay = delay
        self.upper = period
        self.prio = prio

    def __str__(self):
        """
        ' *** PRIVATE MEMBER FUNCTION ***
        ' print complete structure in an informal, readable format
        """
        func = '<none>' if self.function is None else self.function.__name__
        return f"PER:{self.period:.3f}, DLAY:{self.delay:.3f}, " \
            f"UPPR:{self.upper:.3f}, PREV:{self.previous:.3f} , PASS:{self.passed:d} - FUNC:{func:s}"


class Poller:
    """ actual poller, the one polling for tasks to be executed
        i.e. by calling the configured functions
    """
    MAXPRIO = 4

    def __init__(self):
        """
        ' Constructor.
        """
        self.max_prio = 0
        self.entries = {}
        self.poll_period = 0
        self.minimum = 99999999

        self.schedules = []
        for i in range(self.MAXPRIO):
            self.schedules.append({})

    def set_period(self, name, period, func=None, delay=0, prio=0):
        """ adding a new interval to the array, identified by its 'name'.

            v2.0: list of periodics has now as top-level index the priority:
                0, 1, 2 ...
        """

        # period must greater than 0
        if period <= 0:
            return None

        # if the same name is re-entered, just delete it, as priority might have changed
        if name in self.entries:
            curr = self.entries[name]   # current priority
            self.entries.pop(name)
            self.schedules[curr].pop(name)

        self.max_prio = max(self.max_prio, prio)

        self.entries[name] = prio
        self.schedules[prio][name] = Periodic(period, func, delay, prio)

        p = self.schedules[prio][name]
        self.minimum = min(self.minimum, p.period)
        self.poll_period = self.__set_polling()

        ####
        # principle:
        # those schedules that share the same period but have a different delay
        # have an upper limit in their 'execution window'
        #    ('period' + 'delay') <= 'trigger' < ('period' + 'next')
        # with 'next' being of the smallest next delay (of another function)
        #
        # Observe:
        # This check and adjustment is only relevant / applicable for those schedules
        # with the same priority - other (lower) priorities are supposed not to conflict.
        #
        # For now, this is a premise. It that premise would change, the code must be adjusted.
        ####

        for schedule in self.schedules:
            for namx, x in schedule.items():
                if x.period == period:
                    for namy, y in schedule.items():
                        if (x.delay < y.delay) and (x.upper > y.delay):
                            x.upper = y.delay

        return p

    def check_by_name(self, name):
        """
        ' check the period matching the given name for its period being passed ('passed' = 1).
        ' This function clears 'passed' at every call. Hence when it returns '1', all
        ' dependent events must be handled following this one check.
        ' Observe the update of 'passed' is done through the global 'refresh' method.
        """
        for schedule in self.schedules:
            if name in schedule:
                p = schedule[name]
                passed = p.passed
                p.passed = 0
                return passed

        return -1

    def exec_by_name(self, name):
        """ execute entry (function) by name.
        """
        for schedule in self.schedules:
            if name in schedule:
                p = schedule[name]
                passed = p.passed
                p.passed = 0
                if passed:
                    p.function(name)

                return passed

        return -1

    def exec_function(self, name, periodic):
        """ executes one specific function
        """
        if periodic.passed:
            periodic.passed = 0
            periodic.function(name)
            return 1

        return 0

    def exec_all(self):
        """ loop all entries (functions) and execute them
        """
        passed = 0

        # Observe:
        # by implementation, the functions are triggered in priority decreasing (in value)
        # through the initialization of the array self.schedules (0, 1, 2, ...)
        for schedule in self.schedules:
            for nam, p in schedule.items():
                passed = passed + self.exec_function(nam, p)

        return passed

    def check_all(self):
        """ loop all entries and get those 'passed'
        """
        lst = []
        for schedule in self.schedules:
            for nam, struct in schedule.items():
                if struct.passed:
                    lst.append(nam)

        return lst

    def refresh_all(self):
        """
        ' taking the current time, mark the periodics matching the given index
        ' for its delay being passed => setting 'passed' to 1.
        """
        tim = time.time()

        # loop all entries
        for schedule in self.schedules:
            for nam, p in schedule.items():
                dif = tim - p.previous

                # skip for passed periods
                while dif > p.period:
                    print(f"{tim:16.3f} - {nam} {p.previous:16.3f} - adjusting")
                    p.previous+= p.period
                    dif = tim - p.previous

                # check for triggering
                if (p.delay <= dif) and (dif < p.upper):
                    p.passed = 1
                    p.previous+= p.period

        return 0

    def sleep(self):
        """
        ' execute sleep as per the calculated polling period
        """
        # calculate lost time after previous wake-up
        div, rem = divmod(time.time(), self.poll_period)
        # adjust polling period with lost (milli)seconds
        time.sleep(self.poll_period - rem)
        # refresh as close as possible after sleep
        self.refresh_all()

    def __set_status_all(self, __status=0):
        """
        ' reset the whole array of periodics (intervals), updating the 'previous' time
        ' to the current time and clearing 'passed' - or setting passed to __status given.
        """
        tim = time.time()

        for schedule in self.schedules:
            for nam, p in schedule.items():
                div, rem = divmod(tim, p.period)
                p.previous = (div + 1) * p.period
                p.passed = __status

        return len(self.schedules)

    def reset_all(self):
        """
        ' reset the whole array of periodics (intervals), updating the 'previous' time
        ' to the current time and *setting* 'passed' to 0.
        ' Purpose is to start the period measurement from this call onwards.
        """
        return self.__set_status_all(0)

    def set_all(self, status: int):
        """
        ' reset the whole array of periodics (intervals), updating the 'previous' time
        ' to the current time and *setting* 'passed' to 'status'.
        ' Purpose is to restart the period measurement from this call onwards.
        """
        return self.__set_status_all(status)

    def __str__(self):
        """ private function:
        ' print all entries in an informal, readable format
        """
        if len(self.schedules) > 0:
            tmp = F"Minimum: {self.minimum:8.3f} - polling: {self.poll_period:8.3f}\n"

            for schedule in self.schedules:
                for nam, p in schedule.items():
                    tmp = f"{tmp}{nam} - {p}\n"

        else:
            tmp = 'Poller: <empty>'
        return tmp

    def __set_polling(self):
        """ private function:
        ' Calculates the common divisor of all periodics,
        ` aiming for the recommended polling period to ensure
        ' that each period is validated as close as possible to the wanted timeframe.
        """
        getcontext().prec = 6  # in order to have 0.000000...x evaluated as 0

        # step 1 - try to find a common divisor between 1 and 100
        # i.e. the smallest poll_period that has no fractional remainder
        # for either 'p.delay'.
        per = Decimal(1)
        for i in range(100):
            div = Decimal(self.minimum) / per
            # divisor must fit the minimum period, at least
            if Decimal(div - int(div)) == 0:
                tot = Decimal(0)

                # loop all schedules
                for schedule in self.schedules:
                    for nam, p in schedule.items():
                        div = Decimal(p.delay) / per
                        tot = tot + Decimal(div - int(div))

                if tot == 0:
                    # per is a common divisor for *all* periods/delays.
                    return float(per)

            per = Decimal(self.minimum / (i + 1)) # even dividers only

        # step 2 - no common divisor is found
        return 0.01
