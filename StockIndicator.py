from toolset.stockdb import *
from toolset.yahoocrawer import *
from toolset.confighelper import Config
from toolset.indicatorplugin import RsiIndicator, PriceIndicator
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import datetime


__author__ = 'Alfred, S.-Y., Wei'

sched = Scheduler()


class ReportSender:
    @staticmethod
    def send(config, report):
        if config['method'] == 'email':
            ReportSender.send_email(report, config)
        pass

    @staticmethod
    def send_email(report, config):
        msg = MIMEMultipart('alternative')

        supported_attr = {
            'date': datetime.date.today()
        }

        msg['Subject'] = config.get('subject', 'No Subtitle').format_map(supported_attr)
        msg['From'] = config.get('from', 'alfred.syw@gmail.com')
        msg['To'] = ';'.join(config.get('to', []))
        msg.attach(MIMEText(str(report), 'plain'))
        msg.attach(MIMEText('<html><body>' + str(report) + '</body></html>', 'html'))
        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(config.get('smtp', 'localhost'))
        s.ehlo()
        s.starttls()
        s.login(config['user'], config['pwd'])
        s.sendmail(msg['From'], config.get('to', []), msg.as_string())
        s.quit()


class StockReporter:
    def __init__(self, config_path):
        self.config = Config(config_path)

        if 'database' in self.config and self.config['database']['type'] == "sqlite":
            self.db = StockDatabase(self.config['database']['path'])
        else:
            self.db = None

    def prepare(self, stock_id, indicators):

        required_days = int((max([indicator.required_days for indicator in indicators]) / 5) * 7 * 1.5)

        date_from = datetime.date.today() - datetime.timedelta(days=required_days)
        date_to = datetime.date.today()

        if self.db:  # use data base, fetch new data to db
            records = self.db.query_stock_by_name(stock_id, date_from, date_to)
            if records and list(records):
                sorted_records = sorted(records, key=lambda x: x.date)
                if sorted_records and sorted_records[-1].date.date() < (date_to - datetime.timedelta(days=1)):
                    new_date_from = sorted_records[-1].date + datetime.timedelta(days=1)
                    self._update(stock_id, new_date_from, date_to)
            else:
                self._update(stock_id, date_from, date_to)

            records = self.db.query_stock_by_name(stock_id, date_from, date_to)
            if list(records):
                return [{'Stock': stock_id, 'Date': r.date,
                         'Open': r.open, 'High': r.high,
                         'Low': r.low, 'Close': r.close,
                         'Volume': r.volume, 'Adj Close': r.adj_close} for r in records]
        else:  # use data from yahoo directly

            def _transform_(r):
                if '/' in r['Date']:
                    fmt = '%Y/%m/%d'
                elif '-' in r['Date']:
                    fmt = '%Y-%m-%d'
                else:
                    fmt = '%Y %m %d'
                return {
                    'Date': datetime.datetime.strptime(r['Date'], fmt).date(),
                    'Open': float(r['Open']),
                    'High': float(r['High']),
                    'Low': float(r['Low']),
                    'Close': float(r['Close']),
                    'Volume': int(r['Volume']),
                    'Adj Close': float(r['Adj Close'])
                }

            records = []
            for r in gen_fetch_stock(stock_id, date_from, date_to, True):
                d = {'Stock': stock_id}
                d.update(_transform_(r))
                records.append(d)
            return records

    def _update(self, stock_id, date_from, date_to):
        for record in gen_fetch_stock(stock_id, date_from, date_to, True):
            # name, date, open, high, low, close, volume, adj_close
            if '/' in record['Date']:
                fmt = '%Y/%m/%d'
            elif '-' in record['Date']:
                fmt = '%Y-%m-%d'
            else:
                fmt = '%Y %m %d'

            if self.db:
                self.db.add_stock(stock_id,
                                  datetime.datetime.strptime(record['Date'], fmt).date(),
                                  float(record['Open']),
                                  float(record['High']),
                                  float(record['Low']),
                                  float(record['Close']),
                                  int(record['Volume']),
                                  float(record['Adj Close']))

    def show_all(self):
        if self.db:
            for record in self.db.query_all_record():
                elog(ErrorLevel.VERBOSE, record)

    def do_report(self):

        indicators = [RsiIndicator(), PriceIndicator()]

        if self.config and 'monitor' in self.config:
            result = {'Buy': {}, 'Sale': {}}
            stocks = {id: {'score': 0, 'desc': ''} for id in self.config['monitor']['stocks']}
            for stock_id in self.config['monitor']['stocks']:
                records = self.prepare(stock_id, indicators)
                if not records:
                    continue

                for indexer in indicators:
                    indexer.feed(records)
                    index, desc = indexer.do_report()
                    stocks[stock_id]['score'] += index
                    if stocks[stock_id]['desc']:
                        stocks[stock_id]['desc'] += '; ' + desc
                    else:
                        stocks[stock_id]['desc'] += desc

            for stock_id, indices_result in reversed(sorted(stocks.items(), key=lambda k: k[1]['score'])):
                stock_cls = self.get_stock_type(stock_id)
                stock_rep = '{}(<a href="https://tw.stock.yahoo.com/q/q?s={}">{}</a>): {}'.format(
                    self.get_stock_name(stock_id), stock_id.split('.')[0], stock_id, indices_result['desc'])
                key = ''
                if indices_result['score'] > 0:
                    key = 'Buy'
                elif indices_result['score'] < 0:
                    key = 'Sale'
                if key:
                    if stock_cls in result[key]:
                        result[key][stock_cls].append(stock_rep)
                    else:
                        result[key][stock_cls] = [stock_rep]
            return result
        return {}

    def get_stock_type(self, stock_id):
        if 'stock_table' in self.config:
            for c, d_table in self.config['stock_table'].items():
                for id, name in d_table.items():
                    if id.lower() == stock_id.lower():
                        return c

    def get_stock_name(self, stock_id):
        if 'stock_table' in self.config:
            for c, d_table in self.config['stock_table'].items():
                for id, name in d_table.items():
                    if id.lower() == stock_id.lower():
                        return name
        return stock_id

    def gen_stocks_from_table(self):
        if 'stock_table' in self.config:
            for c, d_table in self.config['stock_table'].items():
                for id, name in d_table.items():
                    yield id

    def transform_to_msg(self, report):
        msg = []
        body = []
        if 'Buy' in report and report['Buy']:
            body.extend(('<div>' + 'Suggest to Buy', ''))
            for c, stocks in report['Buy'].items():
                body.append('<p><b>' + c + '</b></p>')
                body.extend(['<p><span>' + s + '</span></p>' for s in stocks])
            body.append('</div>')

        if body:
            if 'header' in self.config['report']:
                msg.append('<div>')
                msg.append('<br/>'.join(self.config['report']['header']))
                msg.extend(['<br/>'] * 3)
                msg.append('</div>')

            msg.extend(body)

            if 'footer' in self.config['report']:
                msg.append('<div>')
                msg.extend(['<br/>'] * 3)
                msg.extend('<br/>'.join(self.config['report']['footer']))
                msg.append('</div>')

        if msg:
            return ''.join(msg)
        return ''


def run_period(config_path):
    try:
        elog(ErrorLevel.HIGHLIGHT, 'Run Period {}'.format(datetime.date.today()))
        config = Config(config_path)
        mgr = StockReporter(config_path)
        report = mgr.transform_to_msg(mgr.do_report())
        if 'report' in config and report:
            ReportSender.send(config['report'], report)
    except:
        elog(ErrorLevel.ERROR, 'Something wrong')


def start_schedule(config_path):

    config = Config(config_path)
    if 'schedule' in config and 'daily' == config['schedule']['period']:
        t = datetime.datetime.strptime(config['schedule']["time"], '%H:%M:%S')
        sched.add_job(run_period, 'cron', hour=t.hour, minute=t.minute, second=t.second, args=['config.json'])
        # sched.add_job(run_period, 'interval', seconds=5, args=['config.json']) # debug purpose
        elog(ErrorLevel.HIGHLIGHT, 'Schedule start @ daily {}'.format(datetime.date.strftime(t, '%H:%M:%S')))
        sched.start()


if __name__ == '__main__':
    app.verbose_level = ErrorLevel.VERBOSE
    # run_period('config.json')
    start_schedule('config.json')
