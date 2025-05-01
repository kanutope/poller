# module: poller

## purpose

use case is when you have different functions that need to be executed recurrently,
each with its own period. Key is that it is not interrupt driven.

Actually it deals with these timely repeated execution by **controlled *sleep***. It wakes up at regular intervals, short enough to make sure it can handle the smallest period (highest frequency) demanded.

The implementation is for low frequency periodical execution: the smallest '*polling*' period is 0,01 sec. When the
objective is to use it for *heavy* time consuming functions, they should rather have a period greater than 0,1 sec.
All depends on the use case.

## concepts

The center piece is a single *Poller* instance that manages a list of *Periodics*. The latter is basically a *named* function and a period (seconds) in which it has to be executed repeatedly.

## sequencing

In order to sequence certain functions such that one is executed - sufficient time - ahead of the other, it supports *delay*. In other words, the execution of a repeated function is parameterized by **period** and *optionally* **delay**.

In version 2.0, the concept of ***priority*** is introduced. The function can have a priority, starting from 0 upwards. The higher the number the lower the priority. Through this priority qualifier, one can execute several functions with the same period one **after** the other, in a specific order. **Key assumption** here is that the functions are synchronious - at least the ones that are dependent on each other: they doen't return before completion.

## principles

If multiple functions have dependencies, meaning that the execution of *func2* depends on the completion of *func1*, than
they either have a different *delay* or they get a different *priority* assigned.

When a function has a non-zero ***delay***, that *delay* is always smaller than its ***period***.

## implications

Bear in mind that it may happen that two functions are triggered at the same time. E.g.

- *func1* has period 3 sec
- *func2* has period 4 sec
- every 12 seconds, *func1* and *func2* will be triggered at the same time

Hence, if there is any dependency between these two functions, you might consider either to add a *delay* (<> 0) or a different priority.

## implementation

### finding the *polling period (poll_period)*

When a *periodic* is added, that is a function that must be executed repeatedly in a given period - the smallest period
is saved. In order to find the biggest polling period that matches both the given periods and potential delays, there
are two steps.

1. it iterates with a divider from 1 to 100 - starting with  
    *`<minimum periode> / 1`*.  
    That iteration returns succesful when a common divisor is found for all periods and delays, when for all *periodics* the division  
    *`(<minimum period> + <delay>) / <div>`* has no fractional remainder.  

2. if that common divisor is not found, the ***polling period*** is set to **0.01** seconds.

## caveats

At execution time, since the functions are executed by one and the same controller, they
cannot take a variable set of parameters, since the controller is agnostic about them
