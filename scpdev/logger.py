# -*- coding: utf-8 -*-

import logging


class SimpleFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        prepend = '  '
        if record.levelname == 'INFO':
            prepend = '=='
        if record.levelname == 'WARNING' or record.levelname == 'ERROR' or record.levelname == 'CRITICAL':
            prepend = '!!'
        try:
            prepend = record.__dict__['ext_level']
        except:
            pass

        return ' %s  %s'%(prepend, super().format(record))

