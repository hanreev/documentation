# -*- coding: utf-8 -*-

import logging
import sys


def create_logger(filename: str):
    logging.basicConfig(filename=filename, filemode='w',
                        format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.WARNING)
    logger = logging.getLogger()

    if '-v' in sys.argv or '--verbose' in sys.argv:
        logger.setLevel(logging.DEBUG)

    return logger
