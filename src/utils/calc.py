from decimal import Decimal
import decimal

from typing import Union

Number = Union[int, float]

'''Ex: A change of 20 to 15 is -25%'''
def percent_change(y_val: Number, y_val_prev: Number) -> float:
    if y_val_prev == 0:
        raise ValueError("y_val_prev cannot be zero for percent change calculation")
    return ((y_val - y_val_prev) * 100) / y_val_prev

'''Ex: 15 is 75% of 20, or what percent of 20 is 15'''
def what_percent_is(part: Number, whole: Number) -> float:
    if whole == 0:
        raise ValueError("whole cannot be zero for portion calculation")
    return (part / whole) * 100

'''Ex: 5% of 38,000 is 1900'''
def percent_of(percent: Number, whole: Number) -> float:
    return (percent * whole) / 100

def percent_difference(val_1: Number, val_2: Number) -> float:
    if (val_1 + val_2) == 0:
        raise ValueError("Sum of val_1 and val_2 cannot be zero for percent difference")
    return (abs(val_1 - val_2) / ((val_1 + val_2) / 2)) * 100



def most_recent_complete_timestamp(timestamp, granularity):
    return timestamp - (timestamp % granularity)

'''Gemini rounds to nearest 6th decimal when using more digits'''
quanitize_value = Decimal('1.000000')

def quantize(num):
    return num.quantize(quanitize_value, rounding=decimal.ROUND_DOWN)