import json
from typing import Optional

from attr import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from logger.logger import logger


@dataclass
class NetWorkRecord:
    url: str
    params: dict
    response: any


def get_networks(driver: WebDriver, target: str):
    logs = driver.get_log("performance")
    responses: list[NetWorkRecord] = []

    for entry in logs:
        try:
            log = json.loads(entry["message"])["message"]

            if log["method"] == "Network.responseReceived":
                params = log['params']
                url = params['response']['url']

                if target in url:
                    request_id = params['requestId']
                    response = get_request_body(driver, request_id)
                    responses.append(NetWorkRecord(url, params, response))
        except Exception as e:
            logger.error(f'Get network data error: {e}')

    return responses


def get_request_body(driver: WebDriver, request_id: str):
    response = driver.execute(
        driver_command="executeCdpCommand",
        params={
            "cmd": "Network.getResponseBody",
            "params": {"requestId": request_id},
        },
    )
    return response


def find_element_on_loaded(driver: WebDriver, by=By.ID, value: Optional[str] = None, timeout: int = 10):
    return WebDriverWait(driver, timeout).until(expected_conditions.presence_of_element_located((by, value)))


def find_element_on_visible(driver: WebDriver, by=By.ID, value: Optional[str] = None, timeout: int = 10):
    return WebDriverWait(driver, timeout).until(expected_conditions.visibility_of_element_located((by, value)))
