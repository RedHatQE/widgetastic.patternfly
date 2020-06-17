# -*- coding: utf-8 -*-

import allure
import pytest

import codecs
import os
import sys

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from widgetastic.browser import Browser

selenium_browser = None


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return '1.0.0'


@pytest.fixture(scope='session')
def browser_name():
    return os.environ['BROWSER']


@pytest.fixture(scope='session')
def selenium(request, browser_name):
    if browser_name == 'firefox':
        driver = webdriver.Remote(desired_capabilities=DesiredCapabilities.FIREFOX)
    elif browser_name == 'chrome':
        caps = DesiredCapabilities.CHROME.copy()
        caps['chromeOptions'] = {'args': ['disable-dev-shm-usage', 'no-sandbox']}
        driver = webdriver.Remote(desired_capabilities=caps)
    else:
        sys.exit('Please provide BROWSER environment variable')
    request.addfinalizer(driver.quit)
    global selenium_browser
    selenium_browser = driver
    return driver


@pytest.fixture(scope='function')
def browser(selenium, httpserver, request):
    this_module = sys.modules[__name__]
    path = os.path.dirname(this_module.__file__)
    testfilename = path + '/testing_page.html'
    server_root = '/'
    httpserver.expect_request(server_root).respond_with_data(
        codecs.open(testfilename, mode='r', encoding='utf-8').read(),
        headers=[('Content-Type', 'text/html')])
    selenium.get(httpserver.url_for(server_root))
    return CustomBrowser(selenium)


def pytest_exception_interact(node, call, report):
    if selenium_browser is not None:
        allure.attach(
            selenium_browser.get_screenshot_as_png(),
            'Error screenshot',
            allure.attachment_type.PNG
        )
        allure.attach(
            str(report.longrepr),
            'Error traceback',
            allure.attachment_type.TEXT
        )
