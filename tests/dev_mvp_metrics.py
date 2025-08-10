import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import compute_mvp_metrics

API_KEY = 'ilp96LS93HjMQOCCyXwbt5UmOKf5da16'


def run_dev_checks(symbols=None):
    if symbols is None:
        symbols = ['CRM', 'DELL']
    for sym in symbols:
        metrics = compute_mvp_metrics(sym, API_KEY)
        print(sym, metrics)


if __name__ == '__main__':
    run_dev_checks()
