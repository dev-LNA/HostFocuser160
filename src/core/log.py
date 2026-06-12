# log.py - Main code
# Part of the Focus160MQ template device interface and communication
#
# Author:   Ramon C. Gargalhone <rgargalhone@lna.br> (RCG)
#
# Python Compatibility: Requires Python 3.10 or later

import logging
import logging.handlers
import time
from datetime import datetime, timedelta
from pathlib import Path
try:
    from src.core.config import Config    
    CONFIG_FILE = True
except:
    CONFIG_FILE = False

import os

# class LogCreationDate(logging.NullHandler):
#     def __init__(self, filename, *args, **kwargs):
#         super().__init__(filename, *args, **kwargs)

#         absolute_position = 0

#         # The logger header will have this text before the file creation time
#         search_text = "This file was created in: "

#         with open(filename, "r", encoding="utf-8") as file:
#             for line_num, line in enumerate(file, 1):
#                 # Check if the word is in the current line
#                 column_index = line.find(search_text)
                
#                 if column_index != -1:  # .find() returns -1 if not found
#                     exact_file_position = absolute_position + column_index

#                 # Update the absolute position by adding the length of the current line
#                 absolute_position += len(line)

#             # Sets the position and adds the size of the searched text
#             file.seek(exact_file_position + len(search_text))

#             # Reads the date, format is month/day/year
#             month = int(file.read(2))
#             file.read(1)                # Dummy read to account for '/'
#             self.day = int(file.read(2))
#             file.read(1)                # Dummy read to account for '/'
#             year = int(file.read(4))

def log_creation_date(filename):

        absolute_position = 0

        # The logger header will have this text before the file creation time
        search_text = "This file was created in: "

        with open(filename, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                # Check if the word is in the current line
                column_index = line.find(search_text)
                
                if column_index != -1:  # .find() returns -1 if not found
                    exact_file_position = absolute_position + column_index

                # Update the absolute position by adding the length of the current line
                absolute_position += len(line)

            # Sets the position and adds the size of the searched text
            file.seek(exact_file_position + len(search_text))

            # Reads the date, format is month/day/year
            month = int(file.read(2))
            file.read(1)                # Dummy read to account for '/'
            day = int(file.read(2))
            file.read(1)                # Dummy read to account for '/'
            year = int(file.read(4))

            return day
            
def init_logging():
    if not CONFIG_FILE:
        return
    logs_dir_path = os.path.join('logs')
    log_reference_date = datetime.now()
    # log_path = r"logs/focuser.log"
    if log_reference_date.hour < 12:
        # If the logger is being created before noon it must consider as being from the previous day
        log_reference_date = log_reference_date - timedelta(days=1)

    # log_path = f"logs/focuser_{datetime.now().strftime("%Y_%m_%d")}"
    log_path = f"logs/focuser_{log_reference_date.strftime("%Y_%m_%d")}"

    try:
        #TODO: Adicionar lógica para que um novo arquivo de logger seja
        #   criado todos os dias. Um novo arquivo de logger deve ser 
        #   criado ao meio dia.
        if not os.path.exists(logs_dir_path):
            os.makedirs(logs_dir_path)
            
        with open(log_path, 'x') as file:
            file.write("-" * 20 + "\n")
            file.write("     LOG FILE      \n")
            file.write("-" * 20 + "\n\n")
            file.write("This is a file to log all the important events occurred during the execution of the Focuser.\n\n")

            # file.write(f"This file was created in: {datetime.month}/{datetime.day}/{datetime.year} {datetime.hour}:{datetime.minute}:{datetime.second}")
            file.write("_" * 50 + "\n\n")
            file.write(f"This file was created in: {datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")}\n")
            if log_reference_date.hour < 12:
                start_date = log_reference_date - timedelta(days=1)
            else:
                start_date = log_reference_date
                log_reference_date = log_reference_date + timedelta(days=1)

            file.write(f"This logger will reference the activities from [{start_date.strftime("%m/%d/%Y")} at 12:00] to [{log_reference_date.strftime("%m/%d/%Y")} at 12:00]\n")
            file.write(f"The log level is: {Config.log_level}\n")
            file.write("_" * 50 + "\n\n")

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

    # creation_time_handler = LogCreationDate(filename=log_path)
    # logger.addHandler(creation_time_handler)
    logger.creation_day = log_creation_date(log_path)

    return logger