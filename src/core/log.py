# log.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import logging
import logging.handlers
import time
from datetime import datetime
try:
    from src.core.config import Config    
    CONFIG_FILE = True
except:
    CONFIG_FILE = False

import os

def init_logging():
    if not CONFIG_FILE:
        return
    logs_dir_path = os.path.join('logs')
    log_path = r"logs/focuser.log"

    try:
        #TODO: Adicionar lógica para que um novo arquivo de logger seja
        #   criado todos os dias. Um novo arquivo de logger deve ser 
        #   criado ao meio dia.
        if not os.path.exists(logs_dir_path):
            os.makedirs(logs_dir_path)
            
        with open(log_path, 'x') as file:
            file.write("-------------------\n")
            file.write("     LOG FILE      \n")
            file.write("-------------------\n\n")
            file.write("This is a file to log all the important events occurred during the execution of the Focuser.\n\n")

            # file.write(f"This file was created in: {datetime.month}/{datetime.day}/{datetime.year} {datetime.hour}:{datetime.minute}:{datetime.second}")
            file.write(f"This file was created in: {datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")}\n")
            file.write(f"The log level is: {Config.log_level}\n\n\n")

            file.close()
    except Exception as e:
        print(f"{e}")

    logging.basicConfig(level=Config.log_level)
    logger = logging.getLogger()                # Root logger, see above
    # formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s %(message)s', '%Y-%m-%dT%H:%M:%S')
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d [ %(levelname)s ] --> %(message)s', '%Y-%m-%dT%H:%M:%S')
    formatter.converter = time.gmtime           # UTC time
    logger.handlers[0].setFormatter(formatter)  # This is the stdout handler, level set above
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
    return logger