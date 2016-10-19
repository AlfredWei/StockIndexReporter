import globaldef as app
from globaldef import *

__author__ = 'Alfred, S.-Y., Wei'


class Indicator:
    def __init__(self):
        pass

    def feed(self, records):
        pass

    def do_report(self):
        return False, []

    @property
    def name(self):
        return 'Base Report'

    @property
    def required_days(self):
        return 30


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

    @property
    def required_days(self):
        return self.n + 1

    @property
    def name(self):
        return 'RSI Report'

    def feed(self, records):
        if len(records) < self.n + 1:
            raise ArithmeticError('Not enough data, you should provide at least {} data'.format(self.n + 1))
        self.data = list(reversed(sorted(list(records), key=lambda x: x['Date'])))

    def do_report(self):
        val = self.rsi()
        if val <= RsiIndicator.oversale:
            return 1, 'Buy {}, index shows market over sale'.format(val)
        elif val >= RsiIndicator.overbuy:
            return -1, 'Sale {} index shows market over buy'.format(val)
        else:
            return 0, 'Average {} index shows market is on average'.format(val)

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

            if today_item['Close'] > lastday_item['Close']:
                U += (today_item['Close'] - lastday_item['Close'])
            elif today_item['Close'] < lastday_item['Close']:
                D += (lastday_item['Close'] - today_item['Close'])

        _rsi = ((U / self.n) / (U / self.n + D / self.n)) * 100.0
        return _rsi
