import globaldef as app
from globaldef import *
import tqdm
import requests
import os
import datetime
import csv
import tempfile

__author__ = 'Alfred, S.-Y., Wei'


def download_text_file(url, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    response = requests.get(url, stream=True)
    try:
        if response.status_code != 200:
            return ""
        with open(dst, 'wb') as f:
            for chunk in tqdm.tqdm(response.iter_content(chunk_size=1024)):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        return dst
    except:
        elog(ErrorLevel.ERROR, "Cannot download url to file")
        return ""


sample_dl_cfg = {
    "stock": "0050.TW",
    "from": datetime.date(2016, 10, 1),
    "to": datetime.date(2016, 10, 31)
}


def download_stock_csv_by_cfg(_cfg, _save_dir, _save_name=""):
    attr = {
        "stock": _cfg["stock"],
        "from_y": _cfg["from"].year,
        "from_m": _cfg["from"].month - 1,  # month is from 0
        "from_d": _cfg["from"].day,
        "to_y": _cfg["to"].year,
        "to_m": _cfg["to"].month - 1,
        "to_d": _cfg["to"].day,
    }
    _url = "http://chart.finance.yahoo.com/table.csv?s={stock}&a={from_m}&b={from_d}" \
           "&c={from_y}&d={to_m}&e={to_d}&f={to_y}&g=d&ignore=.csv".format_map(attr)

    if _save_name:
        _dst = os.path.join(_save_dir, _save_name)
    else:
        _dst = os.path.join(_save_dir,
                            "report_{stock}_{from_y}_{from_m}_{from_d}_{to_y}_{to_m}_{to_d}.csv".format_map(
                                attr))

    elog(ErrorLevel.VERBOSE, 'Download url <{}>.'.format(_url))

    if download_text_file(_url, _dst):
        elog(ErrorLevel.HIGHLIGHT, 'Download report of <{}> success.'.format(_cfg["stock"]))
        return _dst
    elog(ErrorLevel.HIGHLIGHT, 'Download report of <{}> empty.'.format(_cfg["stock"]))
    return ""


def download_stock_csv(stock, from_date, end_date, _save_dir="", _save_name=""):
    cfg = {"stock": stock,
           "from": from_date,
           "to": end_date}

    if not _save_dir:
        _save_dir = tempfile.gettempdir()
    return download_stock_csv_by_cfg(cfg, _save_dir, _save_name)


def gen_fetch_stock(stock, from_date, end_date, isRemoveTemp=False):
    csv_path = download_stock_csv(stock, from_date, end_date)
    if csv_path:
        with open(csv_path) as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, dialect=dialect)
            for record in reader:
                yield record
        if isRemoveTemp:
            os.remove(csv_path)


if __name__ == '__main__':
    app.verbose_level = ErrorLevel.VERBOSE
    for item in gen_fetch_stock('0050.TW', datetime.date(2016, 1, 1), datetime.date.today(), isRemoveTemp=True):
        elog(ErrorLevel.VERBOSE, item)
