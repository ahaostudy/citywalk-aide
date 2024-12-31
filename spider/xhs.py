import json
import os
import time
from datetime import datetime
from urllib.parse import quote

from clickhouse_orm import Database
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from common.constant import HDFS_PATH_XHS
from logger.logger import logger
from persistent.hdfs_client import HDFSClient
from model.note import NoteInfo, UserInfo, ImageInfo
from spider.util import get_networks
from utils.utils import json_encode


class XHSSpider:
    def __init__(self, driver: WebDriver, cities: list[str], hdfs_client: HDFSClient, clickhouse_client: Database):
        self.driver = driver
        self.base_url = 'https://www.xiaohongshu.com'
        self.cities = cities
        self.hdfs_client = hdfs_client
        self.hdfs_base_url = '/user/spider/xhs/note'
        self.clickhouse_client = clickhouse_client

    def login(self):
        # enter phone number
        account_input = self.driver.find_element(
            By.CSS_SELECTOR,
            '#app > div:nth-child(1) > div > div.login-container > div.right > div.input-container.mt-20px > form > label.phone > input[type=text]'
        )
        account_input.send_keys(os.getenv('USER_PHONE'))

        time.sleep(1)

        # send verification code
        send_verify_button = self.driver.find_element(
            By.CSS_SELECTOR,
            '#app > div:nth-child(1) > div > div.login-container > div.right > div.input-container.mt-20px > form > label.auth-code > span'
        )
        send_verify_button.click()

        # get code
        verify_code = input('Input your verification code: ')

        # enter verification code
        verify_code_input = self.driver.find_element(
            By.CSS_SELECTOR,
            '#app > div:nth-child(1) > div > div.login-container > div.right > div.input-container.mt-20px > form > label.auth-code > input[type=number]'
        )
        verify_code_input.send_keys(verify_code)

        # click agree button
        agree_button = self.driver.find_element(
            By.CSS_SELECTOR,
            '#app > div:nth-child(1) > div > div.login-container > div.right > div.agreements > span > div'
        )
        agree_button.click()

        # click to login
        login_button = self.driver.find_element(
            By.CSS_SELECTOR,
            '#app > div:nth-child(1) > div > div.login-container > div.right > div.input-container.mt-20px > form > button'
        )
        login_button.click()

        logger.info(f'Logging {self.base_url} ...')
        self.sleep()

    def login_with_cookie(self):
        cookies = os.getenv('XHS_COOKIES')
        logger.info(f'Logging with cookies: {cookies}')

        cookies_dict = {}
        for cookie in cookies.split(';'):
            name, value = cookie.strip().split('=', 1)
            logger.info(f'name: {name}, value: {value}')
            cookies_dict[name] = value

        for name, value in cookies_dict.items():
            self.driver.add_cookie({'name': name, 'value': value, 'domain': ".xiaohongshu.com", 'path': "/"})

        self.sleep()

    def search_node(self, keyword: str) -> list[NoteInfo]:
        encode_keyword = quote(quote(keyword, encoding='utf-8'), encoding='utf-8')
        self.driver.get(self.base_url + f'/search_result?keyword={encode_keyword}&source=web_explore_feed')

        logger.info(f'Searching {keyword} ...')
        self.sleep()

        self.load_full_page()

        networks = get_networks(self.driver, '/search/notes')

        result = []

        for network in networks:
            resp = json.loads(network.response.get('value', {}).get('body', '{}'))

            for item in resp.get('data', {}).get('items', []):
                item_model_type = item.get('model_type', '')
                if item_model_type != 'note':
                    continue

                item_id = item.get('id', '')
                item_xsec_token = item.get('xsec_token', '')

                item_note_card = item.get('note_card', {})
                item_display_title = item_note_card.get('display_title', '')
                item_liked_count = int(item_note_card.get('interact_info', {}).get('liked_count', 0))
                item_cover = item_note_card.get('cover', {})
                item_image_list = item_note_card.get('image_list', [])
                item_user = item_note_card.get('user', {})

                url = f'/explore/{item_id}?xsec_token={item_xsec_token}&xsec_source=pc_search&source='

                cover = ImageInfo(width=item_cover.get('width'), height=item_cover.get('height'),
                                  url=item_cover.get('url_default'))

                image_list = []
                for image in item_image_list:
                    image_list.append(ImageInfo(
                        width=image.get('width'),
                        height=image.get('height'),
                        url=image.get('info_list', [{}])[0].get('url'),
                    ))

                user_info = UserInfo(nick_name=item_user.get('nick_name'), avatar=item_user.get('avatar'),
                                     user_id=item_user.get('user_id'), nickname=item_user.get('nickname'),
                                     xsec_token=item_user.get('xsec_token'))

                result.append(NoteInfo(
                    id=item_id,
                    xsec_token=item_xsec_token,
                    url=url,
                    type=item_model_type,
                    display_title=item_display_title,
                    liked_count=item_liked_count,
                    cover=json_encode(cover),
                    image_list=json_encode(image_list),
                    user=json_encode(user_info),
                ))

        return result

    def get_node_page(self, note_url: str):
        self.driver.get(self.base_url + note_url)
        self.sleep(1)
        return self.driver.page_source

    def load_full_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            logger.info('Loading page ...')
            self.sleep(1)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break

            last_height = new_height

    @staticmethod
    def sleep(secs: int = 3):
        time.sleep(secs)

    def is_exists_note(self, note_id: str):
        try:
            return NoteInfo.objects_in(self.clickhouse_client).filter(id=note_id).count() > 0
        except Exception as e:
            logger.error(f'Get is exists note error: {e}')
            return False

    def run(self, city: str):
        try:
            self.driver.get(self.base_url)
            self.login_with_cookie()
            logger.info(f'Logged in {self.base_url}')
        except Exception as e:
            logger.error('Login XiaoHongShu error: %s', e)
            raise e

        logger.info(f'Start spider city {city}')

        try:
            logger.info(f'Start search city {city} note')
            note_list = self.search_node(f'{city} citywalk')
            logger.info(f'Get city {city} note count {len(note_list)}')
        except Exception as e:
            logger.error(f'Search city {city} note error: {e}')
            return

        for note in note_list:
            if self.is_exists_note(note_id=note.id):
                continue

            try:
                logger.info(f'Getting note {note.display_title} - {note.url}')
                note_page = self.get_node_page(note_url=note.url)
                logger.info(f'Get note {note.display_title} success')
            except Exception as e:
                logger.error(f'Get note {note.display_title} error: {e}')
                return

            # Save to HDFS
            try:
                note.page_hdfs_path = os.path.join(HDFS_PATH_XHS, f'{note.id}.html')
                self.hdfs_client.write_file(str(note.page_hdfs_path), note_page)
                logger.info(f'Save note {note.display_title} to hdfs {note.page_hdfs_path} success')
            except Exception as e:
                logger.error(f'Save note {note.display_title} to hdfs {note.page_hdfs_path} error: {e}')
                continue

            # Save to Clickhouse
            try:
                note.city = city
                note.created_at = datetime.now()
                self.clickhouse_client.insert([note])
                logger.info(f'Insert note {note.display_title} to clickhouse success')
            except Exception as e:
                logger.error(f'Insert note {note.display_title} to clickhouse error: {e}')
                continue

        logger.info('Finish spider citywalk data for %s city', city)
