from typing import Optional
import schedule
import time

from clickhouse_orm import Database
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from logger.logger import logger
from persistent.clickhouse_client import ClickhouseClient
from persistent.hdfs_client import HDFSClient
from spider.xhs import XHSSpider

from dotenv import load_dotenv


class Spider:
    def __init__(self, hdfs_client: HDFSClient, clickhouse_client: Database):
        self.driver: Optional[WebDriver] = None
        self.hdfs_client = hdfs_client
        self.clickhouse_client: Database = clickhouse_client
        self.cities = ["佛山", "杭州", "天津", "东莞"]

    def init(self):
        selenium_grid_url = 'http://localhost:4444/wd/hub'

        option = webdriver.ChromeOptions()
        option.set_capability("browserName", "chrome")
        option.set_capability("browserVersion", "131.0")
        option.set_capability("platformName", "linux")
        option.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        option.add_experimental_option(
            "prefs",
            {
                "intl.accept_languages": "en,en_US",
                "profile.managed_default_content_settings.images": 2,
            },
        )
        option.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Remote(command_executor=selenium_grid_url, options=option)

        logger.info('Initializing driver ...')
        self.driver.implicitly_wait(10)

    def spider(self):
        for city in self.cities:
            try:
                self.init()
                xhs_spider = XHSSpider(self.driver, self.cities, self.hdfs_client, self.clickhouse_client)
                xhs_spider.run(city)
            except Exception as e:
                logger.error('Run spider job error: %s', e)
            finally:
                try:
                    self.driver.quit()
                    logger.info("Quit driver")
                except Exception as e:
                    logger.error('Quit driver error: %s', e)

    def run(self):
        self.spider()
        schedule.every().day.at("00:00").do(self.spider)

        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == '__main__':
    load_dotenv()

    hdfs_client = HDFSClient('http://localhost:50070', 'root')
    clickhouse_client = ClickhouseClient('citywalk_aide')

    spider = Spider(hdfs_client, clickhouse_client)
    spider.run()
