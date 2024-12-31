import logging

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# file_handler = logging.FileHandler('app.log')
# file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
# file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
# logger.addHandler(file_handler)

if __name__ == '__main__':
    logger.info('hello world')
