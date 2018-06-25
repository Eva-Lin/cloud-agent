#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import optparse
import logging

from modules.utils.load_config import Config_file, Config_data

generic_logger = None

def config_action(*args, **kwargs):
    print(args, kwargs)


def handle_args():
    parser = optparse.OptionParser()
    # parser.add_option(
    #     "-f", "--config_file", action=config_action, default=-1, dest="config_file", help="sepcify the config file."
    # )
    parser.add_option(
        "-c", "--config_file", default="D:\Linux工具\Develop\jyyall_by_myself\config\server.conf", dest="config_file", help="sepcify the config file."
    )
    parser.add_option(
        "-l", "--log_level", default="info", dest="log_level", help="sepcify the log's level.[debug|info|error]."
    )
    parser.add_option(
        "-r", "--reload", default=False, help="reload and build code."
    )
    args_data = parser.parse_args()[0]  # {'log_level': 'info', 'reload': False, 'config_file': '/etc/bs_agent/bs_agent.conf'}

    config_data = Config_file(args_data.config_file)
    Config_data.set_config_data(config_data)



def handle_log(level='INFO', log_file=None, *args, **kwargs):

    # create logger and set level
    generic_logger = logging.getLogger()
    generic_logger.setLevel(level='DEBUG')

    # create filehandler
    # file_handler = logging.FileHandler(log_file)
    import logging.handlers as log_handlers
    file_handler = logging.handlers.TimedRotatingFileHandler(log_file, 'D', 1)
    file_handler.setLevel(level)

    # create consolehandler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level='DEBUG')

    # create frommatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)s - [%(filename)s:%(lineno)s] - %(funcName)s - %(message)s')

    # bind formatter to handler
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # bind logger to handler
    generic_logger.addHandler(file_handler)
    generic_logger.addHandler(console_handler)

    return generic_logger


def printlog(somethings):
    generic_logger.debug(somethings)
    generic_logger.info(somethings)
    generic_logger.warning(somethings)
    generic_logger.error(somethings)
    generic_logger.critical(somethings)


def main():
    handle_args()   # load args from user to updata module Config_data
    log_config = Config_data.get_config_data("LOG")
    print(log_config)

    global generic_logger
    generic_logger = handle_log(**log_config)

    generic_logger = logging.getLogger("start_agent")
    generic_logger.info("starting server ....")

    from tests.temp import callprint
    callprint('tests printlog')

    from tests.temp import get_config_msg
    get_config_msg()

    generic_logger.info("stoping server ....")

if __name__ == '__main__':
    main()




