import time
from datetime import date
from decimal import Decimal, getcontext
from math import log10


class PeriodStruct:
    """
    ' base record structure
    """
    def __init__(self, period, func=None, delay=0):
        tim = time.time()
        div, rem = divmod(tim, period)
        self.period = period
        self.previous = div * period
        self.passed = 0
        self.function = func
        self.delay = delay
        self.upper = period

    def __str__(self):
        """
        ' *** PRIVATE MEMBER FUNCTION ***
        ' print complete structure in an informal, readable format
        """
        func = '<none>' if self.function is None else self.function.__name__
        return f"PER:{self.period:.3f}, DLAY:{self.delay:.3f}, \
UPPR:{self.upper:.3f}, PREV:{self.previous:.3f} , PASS:{self.passed:d} - FUNC:{func:s}"


class Poller:
    getcontext().prec = 3

    def __init__(self):
        """
        ' Constructor.
        """
        self.periods = {}
        self.minimum = 99999999
        self.polling = 0

    def check_by_name(self, name):
        """
        ' check the period matching the given name for its period being passed ('passed' = 1).
        ' This function clears 'passed' at every call. Hence when it returns '1', all
        ' dependendt events must be handled following this one check.
        ' Observe the update of 'passed' is done through the global 'refresh' method.
        """
        if name in self.periods:
            p = self.periods[name]

            passed = p.passed
            p.passed = 0

            return passed
        else:
            return -1

    def exec_by_name(self, name):
        """
        """
        if name in self.periods:
            p = self.periods[name]
            passed = p.passed
            if passed:
                p.passed = 0
                p.function(name=name)

            return passed
        else:
            return -1

    def exec_all(self):
        """
        """
        passed = 0
        for name in self.periods:
            passed = passed + self.exec_by_name(name)

        return passed

    def check_all(self):
        """
        """
        lst = []
        for name in self.periods:
            if self.periods[name].passed:
                lst.append(name)

        return lst

    def set_period(self, name, period, func=None, delay=0):
        """
        ' adding a new interval to the array, identified by its 'name'.
        """
        if name in self.periods:
            p = self.periods[name]
            p.period = period
            p.delay = delay
            p.function = func
        else:
            self.periods[name] = PeriodStruct(period, func, delay)
            p = self.periods[name]

        if p.period < self.minimum:
            self.minimum = p.period

        self.__set_polling()
        for namX, x in self.periods.items():
            if x.period == period:
                for namY, y in self.periods.items():
                    if x.delay < y.delay:
                        if x.upper > y.delay:
                            x.upper = y.delay

        return p

    def refresh_all(self):
        """
        ' taking the current time, mark the periods matching the given index
        ' for its delay being passed => setting 'passed' to 1.
        """
        tim = time.time()
        
        # loop all entries
        for nam, p in self.periods.items():
            dif = tim - p.previous
            
            # skip for passed periods
            while dif > p.period:
                p.previous = p.previous + p.period
                dif = tim - p.previous

            # check for triggering
            if (p.delay <= dif) and (dif < p.upper):
                p.previous = p.previous + p.period
                p.passed = 1

        return 0

    def sleep(self):
        """
        ' execute sleep as per the calculated polling period
        """
        div, rem = divmod(time.time(), self.polling)   # calculate lost time after previous wake-up
        time.sleep(self.polling - rem)                  # adjust polling period with lost (milli)seconds
        self.refresh_all()                               # refresh as close as possible after sleep

    def __set_status_all(self, __status=0):
        """
        ' reset the whole array of periods (intervals), updating the 'previous' time
        ' to the current time and clearing 'passed' - or setting passed to __status given.
        """
        tim = time.time()
        for name, p in self.periods.items():
            div, rem = divmod(tim, p.period)
            p.previous = (div + 1) * p.period
            p.passed = __status

        return len(self.periods)

    def reset_all(self):
        """
        ' reset the whole array of periods (intervals), updating the 'previous' time
        ' to the current time and *setting* 'passed' to 0.
        ' Purpose is to start the period measurement from this call onwards.
        """
        return self.__set_status_all(0)

    def set_all(self, status: int):
        """
        ' reset the whole array of periods (intervals), updating the 'previous' time
        ' to the current time and *setting* 'passed' to 'status'.
        ' Purpose is to restart the period measurement from this call onwards.
        """
        return self.__set_status_all(status)

    def __str__(self):
        """
        ' *** PRIVATE MEMBER FUNCTION ***
        ' print all entries in an informal, readable format
        """
        if len(self.periods) > 0:
            tmp = F"Minimum: {self.minimum:8.3f} - polling: {self.polling:8.3f}\n"
            for name, p in self.periods.items():
                tmp = f"{tmp}{name} - {p}\n"

        else:
            tmp = 'Poller: <empty>'
        return tmp

    def __set_polling(self):
        """
        ' *** PRIVATE MEMBER FUNCTION ***
        ' Calculates the common denominator of all periods, aiming for the recommended polling period
        ' to ensure that each period is validated as close as possible to the wanted timeframe.
        """
        for i in range(100):
            tot = Decimal(0)
            per = Decimal(self.minimum) / Decimal(i + 1)
            for name, p in self.periods.items():
                if p.delay > 0:
                    div = Decimal(p.delay) / per
                else:
                    div = Decimal(p.period) / per
                tot = tot + Decimal(div - int(div))

            if tot == 0:
                # per is a common denominator for *all* periods/delays.
                self.polling = float(per)
                return

        minim = self.minimum
        for name, p in self.periods.items():
            if minim < p.delay:
                minim = p.delay

        log = log10(minim)
        self.polling = pow(10, int(log) - (3 if log < 0 else 2))
