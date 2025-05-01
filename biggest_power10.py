""" module: biggest_power10
"""
from math import log10

def biggest_power10(x, digits=3):
    """ given the number <x>, calculates the power of ten (10Ex)
        aligning with <digits> of relevant digits, e.g.
        biggest_power10(9.33, 3) = 0.01
        biggest_power10(9.33, 2) = 0.1
        biggest_power10(2534, 3) = 10

    Args:
        x (float or integer):
        digits (integer): the number of significant digits

    Returns:
        number: 1 * pow(10, z)
    """
    log = log10(x)
    return pow(10, int(log) - (digits if log < 0 else (digits-1)))
