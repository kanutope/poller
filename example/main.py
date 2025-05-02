""" sample program demonstrating the use of the Poller

    Observe: the application of the Poller implies entering an endless loop.
        Hence `poll.polling()` should always be the last executable statement.
        Anything after that statement will never be executed
        - unless one wants to implement some error trapping...
"""

from time import time
from datetime import datetime
from math import ceil
from poller import Poller

poll = Poller()  # object managing the interval based scheduling

HOUR = 60.0 * 60.0  # number of seconds in 1 hour
PER = 1 * 60
FRQ = 4
siz = ceil(PER / FRQ)       # 5 minutes

def printf(lbl):
    """ print timestamp and label
    """
    print(f"{datetime.fromtimestamp(time()).isoformat(timespec='milliseconds')} - {lbl}")
    

def func1(lbl=''):
    """ just for demo purpose
    """
    printf(lbl)

def func2(lbl=''):
    """ just for demo purpose
    """
    printf(lbl)

def func3(lbl=''):
    """ just for demo purpose
    """
    printf(lbl)
    
def initialize():
    """ initializing the Poller
    """
    poll.add_period("func1", 1.0, func1, delay=0, prio=1)
    poll.add_period("func2", 1.2, func2, delay=0.3, prio=0)
    poll.add_period("func3", 0.5, func3, delay=0.1, prio=1)
    print(poll)


initialize()
poll.polling()
