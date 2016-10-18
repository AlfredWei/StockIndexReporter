from toolset.stockdb import *
from toolset.yahoocrawer import *
from toolset.confighelper import Config
import datetime as dt
from apscheduler.schedulers.blocking import BlockingScheduler as Scheduler
import smtplib
from email.mime.text import MIMEText

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
        msg = MIMEText(str(report))

        supported_attr = {
            'date': dt.date.today()
        }

        msg['Subject'] = config.get('subject', 'No Subtitle').format_map(supported_attr)
        msg['From'] = config.get('from', 'alfred.syw@gmail.com')
        msg['To'] = ';'.join(config.get('to', []))

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
        config = Config(config_path)

        if 'database' in config and config['database']['type'] == "sqlite":
            self.db = StockDatabase(config['database']['path'])
        else:
            self.db = StockDatabase()

        if 'monitor' in config and config['monitor']['stocks']:
            self.prepare_stocks(config['monitor']['stocks'])

    def prepare_stocks(self, stock_names):
        date_from = datetime.date.today() - datetime.timedelta(days=365)  # prepare 1 year
        date_to = datetime.date.today()

        for stock in stock_names:
            records = self.db.query_stock_by_name(stock, date_from, date_to)
            if records and list(records):
                self.check_and_update(records)
            else:
                self.get_records(stock, date_from, date_to)

    def get_records(self, stock_name, date_from, date_to):
        for record in gen_fetch_stock(stock_name, date_from, date_to, True):
            # name, date, open, high, low, close, volume, adj_close

            if '/' in record['Date']:
                fmt = '%Y/%m/%d'
            elif '-' in record['Date']:
                fmt = '%Y-%m-%d'
            else:
                fmt = '%Y %m %d'

            self.db.add_stock(stock_name,
                              dt.datetime.strptime(record['Date'], fmt).date(),
                              float(record['Open']),
                              float(record['High']),
                              float(record['Low']),
                              float(record['Close']),
                              int(record['Volume']),
                              float(record['Adj Close']))

    def check_and_update(self, records):
        sorted_stock = sorted(records, key=lambda x: x.date)
        if sorted_stock and sorted_stock[-1].date.date() < (datetime.date.today() - datetime.timedelta(days=1)):
            date_from = sorted_stock[-1].date + datetime.timedelta(days=1)
            self.get_records(sorted_stock[-1].name, date_from.date(), datetime.date.today())

    def show_all(self):
        for record in self.db.query_all_record():
            elog(ErrorLevel.VERBOSE, record)

    def gen_report(self):
        return {}


def run_period(config_path):
    elog(ErrorLevel.HIGHLIGHT, 'Run Period {}'.format(dt.date.today()))
    config = Config(config_path)
    mgr = StockReporter(config_path)
    report = mgr.gen_report()
    if 'report' in config:
        ReportSender.send(config['report'], report)


def start_schedule(config_path):
    config = Config(config_path)
    if 'schedule' in config and 'daily' == config['schedule']['period']:
        t = dt.datetime.strptime(config['schedule']["time"], '%H:%M:%S')
        sched.add_job(run_period, 'cron', hour=t.hour, minute=t.minute, second=t.second, args=['config.json'])
        # sched.add_job(run_period, 'interval', seconds=5, args=['config.json']) # debug purpose
        sched.start()


if __name__ == '__main__':
    app.verbose_level = ErrorLevel.VERBOSE
    start_schedule('config.json')
