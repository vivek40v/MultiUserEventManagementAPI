import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta

root_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(root_dir, 'logs/')
data_dir = os.path.join(root_dir, 'entity_data/')
dirs = [logs_dir, data_dir]
# dirs = [logs_dir, provider_dir]
status = [os.makedirs(_dir, exist_ok=True) for _dir in dirs if not os.path.exists(_dir)]

holidays_23 = ['2023-01-26', '2023-03-07', '2023-03-30', '2023-04-04', '2023-04-07', '2023-04-14', '2023-05-01', '2023-06-29', '2023-08-15', '2023-09-19', '2023-10-02', '2023-10-24', '2023-11-14', '2023-11-27', '2023-12-25']
holidays_24 = ['2024-01-22', '2024-01-26', '2024-03-08', '2024-03-25', '2024-03-29', '2024-04-11', '2024-04-17', '2024-05-01', '2024-05-20', '2024-06-17', '2024-07-17', '2024-08-15', '2024-10-02', '2024-11-01', '2024-11-15', '2024-12-25']
holidays_25 = ['2025-02-26', '2025-03-14', '2025-03-31', '2025-04-10', '2025-04-14', '2025-04-18', '2025-05-01',
               '2025-08-15', '2025-08-27', '2025-10-02', '2025-10-21', '2025-10-22', '2025-11-05', '2025-12-25']
holidays = holidays_23 + holidays_24 + holidays_25  # List of date objects
b_days = pd.bdate_range(start=datetime.now()-relativedelta(months=3), end=datetime.now(), freq='C', weekmask='1111100',
                        holidays=holidays)
b_days = b_days.append(pd.DatetimeIndex([pd.Timestamp(year=2024, month=1, day=20), pd.Timestamp(year=2024, month=3, day=2),
                                         pd.Timestamp(year=2024, month=5, day=4), pd.Timestamp(year=2024, month=5, day=18),
                                         pd.Timestamp(year=2024, month=6, day=1), pd.Timestamp(year=2024, month=7, day=6),
                                         pd.Timestamp(year=2024, month=8, day=3), pd.Timestamp(year=2024, month=9, day=14),
                                         pd.Timestamp(year=2024, month=10, day=5), pd.Timestamp(year=2024, month=11, day=9),
                                         pd.Timestamp(year=2024, month=12, day=7),
                                         pd.Timestamp(year=2025, month=2, day=1),])
                       )
# May 4, 2024
# June 1, 2024
# July 6, 2024
# August 3, 2024
# September 14, 2024
# October 5, 2024
# November 9, 2024
# December 7, 2024
b_days = b_days[b_days <= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)].drop_duplicates().sort_values()
today, yesterday = b_days[-1], b_days[-2]
IST = pytz.timezone('Asia/Kolkata')


def define_logger():
    # Logging Definitions
    log_lvl = logging.DEBUG
    console_log_lvl = logging.INFO
    _logger = logging.getLogger('event')
    # logger.setLevel(log_lvl)
    _logger.setLevel(console_log_lvl)
    log_file = os.path.join(logs_dir, f'{datetime.now().strftime("%Y%m%d")}.log')
    handler = TimedRotatingFileHandler(log_file, when='D', delay=True)
    handler.setLevel(log_lvl)
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(console_log_lvl)
    # formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')  #NOSONAR
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(funcName)s %(message)s')
    formatter = logging.Formatter('%(asctime)s %(levelname)s <%(funcName)s> %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    _logger.addHandler(handler)  # Comment to disable file logs
    _logger.addHandler(console)
    # logger.propagate = False  # Removes AWS Level Logging as it tracks root propagation as well
    return _logger


logger = define_logger()
