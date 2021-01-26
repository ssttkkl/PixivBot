from graia.application import AbstractLogger
from loguru import logger


class LoguruWarpper(AbstractLogger):
    def info(self, msg):
        logger.info(msg)

    def error(self, msg):
        logger.error(msg)

    def debug(self, msg):
        logger.debug(msg)

    def warn(self, msg):
        logger.warning(msg)

    def exception(self, msg):
        logger.exception(msg)
