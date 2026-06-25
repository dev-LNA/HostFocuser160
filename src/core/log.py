# log.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import logging
import logging.handlers
import time
from datetime import datetime, timedelta, UTC
from pathlib import Path
try:
    from src.core.config import Config    
    CONFIG_FILE = True
except:
    CONFIG_FILE = False

import os

def init_logging():

    if not CONFIG_FILE:
        raise RuntimeError("Config file not found")
    
    logs_dir_path = os.path.join('logs')
    log_reference_date = datetime.now(UTC).replace(tzinfo=None)
    # log_path = r"logs/focuser.log"
    if log_reference_date.hour < 12:
        # If the logger is being created before noon it must consider as being from the previous day
        log_reference_date = log_reference_date - timedelta(days=1)

    # The log file path name is saved according to its start reference date
    # log_path = f"logs/focuser_{datetime.now().strftime("%Y_%m_%d")}"
    log_path = f"logs/focuser_{log_reference_date.strftime("%Y_%m_%d")}.log"

    try:
        #TODO: Adicionar lógica para que um novo arquivo de logger seja
        #   criado todos os dias. Um novo arquivo de logger deve ser 
        #   criado ao meio dia.
        # If the folder do not exist creates it
        if not os.path.exists(logs_dir_path):
            os.makedirs(logs_dir_path)
        
        start_date = log_reference_date
        log_reference_date = log_reference_date + timedelta(days=1)
        # Open the file in exclusive write mode, if the file do not
        # exist creates it, if the file already exists raises an error
        with open(log_path, 'x') as file:
            file.write("-" * 20 + "\n")
            file.write("     LOG FILE      \n")
            file.write("-" * 20 + "\n\n")
            file.write(f"This is a file to log all the important events occurred during the execution of the {Config.name}.\n\n")

            # file.write(f"This file was created in: {datetime.month}/{datetime.day}/{datetime.year} {datetime.hour}:{datetime.minute}:{datetime.second}")
            file.write("_" * 100 + "\n\n")
            file.write(f"This file was created in: {datetime.now(UTC).strftime("%m/%d/%Y %I:%M:%S %p")}\n")

            # start_date = log_reference_date
            # log_reference_date = log_reference_date + timedelta(days=1)

            file.write(f"This logger will reference the activities from [{start_date.strftime("%m/%d/%Y")} at 12:00] to [{log_reference_date.strftime("%m/%d/%Y")} at 12:00]\n")
            file.write(f"The log level is: {Config.log_level}\n")
            file.write("_" * 100 + "\n\n")

            file.close()
    except Exception as e:
        print(f"{e}")

    logging.basicConfig(level=Config.log_level)
    logger = logging.getLogger()                # Root logger, see above
    logger.propagate = False


    # formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s %(message)s', '%Y-%m-%dT%H:%M:%S')
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d [ %(levelname)s ] --> %(message)s', '%Y-%m-%dT%H:%M:%S')
    formatter.converter = time.gmtime           # UTC time
    # logger.handlers[0].setFormatter(formatter)  # This is the stdout handler, level set above
    # Add a logfile handler, same formatter and level
    handler = logging.handlers.RotatingFileHandler(log_path,
                                                    mode='a',
                                                    delay=True,     # Prevent creation of empty logs
                                                    maxBytes=Config.log_max_size_mb * 1000000,
                                                    backupCount=Config.log_num_keep)
 
    handler.setLevel(Config.log_level)
    handler.setFormatter(formatter)
    # handler.doRollover()                                            
    
    logger.addHandler(handler)
    if not Config.log_to_stdout:        
        logger.debug('Logging to stdout disabled in settings')
        logger.removeHandler(logger.handlers[0])    


    logger.path = log_path
    logger.reference_date = start_date

    return logger


def end_log_file(logger: logging.Logger):
        # Open the file in exclusive write mode, if the file do not
        # exist creates it, if the file already exists raises an error

        path = Path(logger.path)
        if path.is_file():

            with open(logger.path, 'a') as file:
                file.write("_" * 100 + "\n")
                file.write(' ' * 44 + 'END OF FILE' + ' ' * 26)
                file.write(datetime.now(UTC).replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S') + '\n')
                