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


class PriceIndicator(Indicator):
    boundary = 15

    def __init__(self):
        super(Indicator, self).__init__()
        self.data = []

    @property
    def required_days(self):
        return 1

    @property
    def name(self):
        return 'Current Price Filter'

    def feed(self, records):
        self.data = list(reversed(sorted(list(records), key=lambda x: x['Date'])))

    def do_report(self):
        if self.data:
            if self.data[0]['Close'] >= PriceIndicator.boundary:
                return 0, '價格可參考, 現價{}'.format(self.data[0]['Close'])
            else:
                return -100, '價格太低，有風險'


class RsiIndicator(Indicator):
    """
        Simple RSI indicator. Use Culter's RSI with 14 days as default.

    """
    oversale = 25  # oversale -> buy
    overbuy = 60  # overbuy -> sale

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
        val_base = self.rsi(self.n)
        val_now = self.rsi(6)
        if RsiIndicator.oversale <= val_now < RsiIndicator.overbuy and val_now > val_base:
            return 100 - val_now, '買進 {0:.2f}%, 市場持續購買'.format(val_now)
        elif val_now >= RsiIndicator.overbuy and val_now < val_base:
            return -val_now, '賣出 {0:.2f}% 持續下探'.format(val_now)
        else:
            return 0, '觀察 {0:.2f}% '.format(val_now)

    def rsi(self, days):
        if len(self.data) < days or days == 0:
            raise ArithmeticError('Not enough data, you should provide at least {} data'.format(self.n + 1))
        last_data = self.data[1:days]
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

        if U + D == 0:
            return 0
        else:
            _rsi = ((U / days) / (U / days + D / days)) * 100.0
        return _rsi
