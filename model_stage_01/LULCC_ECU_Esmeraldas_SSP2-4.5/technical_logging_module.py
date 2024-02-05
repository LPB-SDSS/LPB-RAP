########## logging ###########
import os
import logging
import sys


def create_logger(log_file_name):
    """The created logger should be used for output (instead of 'print' statements)
    Returns:
        A logger.
    """
    logger = logging.getLogger('main logger')
    logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # create console handler and set level to debug
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # add formatter
    ch.setFormatter(formatter)  # <- remove if time stamps should not be added to console

    logger.addHandler(ch)

    output_dir = os.path.join('technical_log_files')
    os.makedirs(output_dir, exist_ok=True)

    log_file = os.path.join(output_dir, log_file_name)
    if os.path.exists(log_file):
        os.remove(log_file)

    # create file handler and set level to debug
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = create_logger(log_file_name='technical_log_file_LPB-basic.txt')
##############################
