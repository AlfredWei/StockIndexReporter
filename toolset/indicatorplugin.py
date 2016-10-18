import globaldef as app
from globaldef import *

__author__ = 'Alfred, S.-Y., Wei'


class Indicator:
    def feed(self, records):
        pass

    def gen_report(self):
        pass


class RsiIndicator(Indicator):
    def __iter__(self):
        super(Indicator, self).__init__()

    def rsi(stocks):
        sorted_stocks = sorted(list(stocks), key=lambda x: x.date)
