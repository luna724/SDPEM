import json
import os
import time
from typing import *

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.common import TimeoutException

import shared

class ChromeDriverUtil:
    def __init__(self, env_name = ""):
        self.DRIVER_PATH = shared.driver_path
        self.PREFIX = f"[{env_name}]: " if env_name != "" else ""
        self.DRIVER: webdriver.Chrome = None

    def get_driver(self, headless: bool = False, download_path: str = None, options_arguments: List[str] = None) -> webdriver.Chrome:
        """
        バックグラウンドタスクに適した状態でDriverを呼び出す

        :return: driver
        """
        if options_arguments is None:
            options_arguments = []
        print(f"{self.PREFIX}Initializing ChromeDriver..")

        # ChromeDriverの設定
        # arguments を options_arguments に追加する
        # arguments に含まれているものがデフォルトにも含まれている場合、明示的にそれを削除する (実質的な削除処理)
        default_args = [
            "--start-maximized", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage",
            "--remote-debugging-port=9222", "--disable-gpu", "--disable-software-rasterizer",
            "--disable-extensions", "--no-first-run", "--no-default-browser-check"
        ]
        chrome_arguments = [
            x
            for x in options_arguments
            if x.startswith("--")
            if not x in default_args
            if not x in ["--headless"] # ブラックリスト
        ] + [
            x
            for x in default_args
            if not x in options_arguments
        ]
        if headless or "--headless" in options_arguments:
            chrome_arguments.append("--headless")

        chrome_options = Options()
        for arg in chrome_arguments: # 追加
            chrome_options.add_argument(arg)

        if download_path is None:
            download_path = os.path.join(os.getcwd(), "chromedriver-outputs")
        prefs = {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.default_content_setting_values.popups": 0,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)

        service = Service(self.DRIVER_PATH)
        os.makedirs(download_path, exist_ok=True)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.DRIVER = driver
        print(f"{self.PREFIX}ChromeDriver Initialized.")
        return driver


    def get_cookie(self, driver: webdriver.Chrome = None) -> Dict[str, Any]:
        """
        ドライバーからクッキーを取得する
        """
        driver = driver or self.DRIVER
        cookies = driver.get_cookies()
        return {
            k: v
            for k, v in cookies[0].items()
            if not k in ["sameSite", "secure", "httpOnly"]
        }

    def set_cookie(self, driver: webdriver.Chrome = None, cookies: Dict[str, Any] = None):
        """
        ドライバーにクッキーをセットする
        """
        driver = driver or self.DRIVER
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"{self.PREFIX}Failed to set cookie: {e}")
                continue
        return driver