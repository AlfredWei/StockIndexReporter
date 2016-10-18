import globaldef as app
from globaldef import *
import os
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Sequence
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager

__author__ = 'Alfred, S.-Y., Wei'

Base = declarative_base()
SessionMaker = sessionmaker()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionMaker()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class TableNameMixin(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class Stock(TableNameMixin, Base):
    # Here we define columns for the table Stocks
    # Notice that each column is also a normal Python instance attribute.
    # id, stock, date, open, high, low, close, volume, adj_close
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(250), nullable=False, index=True)
    date = Column(DateTime(), nullable=False, index=True)
    open = Column(Float(), nullable=False)
    high = Column(Float(), nullable=False)
    low = Column(Float(), nullable=False)
    close = Column(Float(), nullable=False)
    volume = Column(Integer(), nullable=True, default=0)
    adj_close = Column(Float(), nullable=False)

    def __repr__(self):
        return '<Stock( name:{}, date:{:%Y-%m-%d}, open:{}, high:{}, low{})>'.format(self.name, self.date, self.open,
                                                                                     self.high, self.low)


class StockDatabase:
    def __init__(self, db_path=':memory:'):
        self.engine = self.create_database(db_path)
        SessionMaker.configure(bind=self.engine)
        Base.metadata.bind = self.engine

    @staticmethod
    def create_database(db_path):

        if not db_path.startswith(':'):
            if not os.path.exists(db_path) and os.path.dirname(db_path):
                os.makedirs(os.path.dirname(db_path))

        engine = create_engine('sqlite:///{}'.format(db_path))

        Base.metadata.create_all(engine)

        return engine

    @staticmethod
    def raw_add_stock(stock):
        with session_scope() as session:
            session.add(stock)

    @staticmethod
    def raw_add_stocks(stocks):
        with session_scope() as session:
            session.addall(stocks)

    @staticmethod
    def add_stock(name, date, open, high, low, close, volume, adj_close):
        return StockDatabase.raw_add_stock(
            Stock(name=name, date=date, open=open, high=high,
                  low=low, close=close, volume=volume, adj_close=adj_close))

    @staticmethod
    def add_stocks(iter_stocks):
        stocks = [Stock(name, date, open, high, low, close, volume, adj_close)
                  for (name, date, open, high, low, close, volume, adj_close) in iter_stocks]
        return StockDatabase.raw_add_stocks(stocks)

    @staticmethod
    def query_stock_by_name(name, _from=None, _to=None):
        with session_scope() as session:
            if _from and _to:
                return session.query(Stock).filter(Stock.name.contains(name), Stock.date >= _from, Stock.date <= _to). \
                    order_by(Stock.date)
            else:
                return session.query(Stock).filter(Stock.name.contains(name)).order_by(Stock.date)

    @staticmethod
    def query_all_record():
        with session_scope() as session:
            return session.query(Stock).order_by(Stock.name)


if __name__ == '__main__':
    db = StockDatabase()

    app.verbose_level = ErrorLevel.VERBOSE
    db.add_stock(Stock(name='0050.TW', date=datetime.date(2016, 10, 1), open=56, high=58, low=55,
                       close=57, volume=0, adj_close=56))
    for record in db.query_all_record():
        elog(ErrorLevel.VERBOSE, record)

    for record in db.query_stock_by_name('0050', datetime.date(2016, 9, 1), datetime.date(2016, 10, 31)):
        elog(ErrorLevel.VERBOSE, record)

    for record in db.query_stock_by_name('0050.TW'):
        elog(ErrorLevel.VERBOSE, record)
