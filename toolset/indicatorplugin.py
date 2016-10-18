import globaldef as app
from globaldef import *

__author__ = 'Alfred, S.-Y., Wei'


class Indicator:
    def __init__(self):
        pass

    def feed(self, records):
        pass

    def gen_report(self):
        return False, []


class RsiIndicator(Indicator):
    """
        Simple RSI indicator. Use Culter's RSI with 14 days as default.

    """
    oversale = 30  # oversale -> buy
    overbuy = 70  # overbuy -> sale

    def __init__(self, n=14):
        super(Indicator, self).__init__()
        self.n = n
        self.data = []

    def feed(self, records):
        if len(records) < self.n + 1:
            raise ArithmeticError('Not enough data, you should provide at least {} data'.format(self.n + 1))
        self.data = reversed(sorted(list(records), key=lambda x: x.date))

    def gen_report(self):
        val = self.rsi()
        if val <= RsiIndicator.oversale:
            return 1, 'Buy {}'.format(val), 'Market over sale'
        elif val >= RsiIndicator.overbuy:
            return -1, 'Sale {}'.format(val), 'Market over buy'
        else:
            return 0, 'Average {}'.format(val), 'Market in observation'

    def rsi(self):
        if len(self.data) < self.n:
            raise ArithmeticError('Not enough data, you should provide at least {} data'.format(self.n + 1))
        last_data = self.data[1:self.n]
        last_data.append(None)

        U = 0
        D = 0

        for today_item, lastday_item in list(zip(self.data, last_data)):
            if lastday_item is None:
                break

            if today_item.close > lastday_item.close:
                U += (today_item.close - lastday_item.close)
            elif today_item.close < lastday_item.close:
                D += (lastday_item.close - today_item.close)

        RSI = ((U/self.n) / (U/self.n + D/self.n)) * 100.0