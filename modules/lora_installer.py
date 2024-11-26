import hashlib
import json
import os
import re
import threading
import time
import tkinter as tk
import requests

from safetensors.torch import safe_open
from tkinter import messagebox
from datetime import datetime
from typing import *
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.devtools.v85.network import get_cookies
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import shared
from jsonutil import JsonUtilities, BuilderConfig
from modules.lora_metadata_util import LoRAMetadataReader
from modules.yield_util import new_yield, yielding_util


class LoRAModelInstaller:
    def __init__(self):
        self.data: Dict[str, Tuple[str, bool]] = {}

        self.obtained_data: list = list()

        self.COOKIE_PATH = "civitai_cookies.json"

    def save_cookies(self, driver):
        cookies = driver.get_cookies()
        with open(self.COOKIE_PATH, "w") as f:
            json.dump(cookies, f) # type: ignore

    def load_cookies(self, driver):
        if os.path.exists(self.COOKIE_PATH):
            with open(self.COOKIE_PATH, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                # 不要な属性を削除
                cookie.pop("sameSite", None)
                cookie.pop("secure", None)
                cookie.pop("httpOnly", None)

                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"[WARN]: Failed to load cookie ({str(e)})")
                    #print(f"Warning: Failed to add cookie: {str(e)} (Cookie: {cookie})")
                    # エラーが発生してもログインが成功しているなら問題なしと判断
                    continue

    def get_cookie(self):
        if os.path.exists(self.COOKIE_PATH):
            with open(self.COOKIE_PATH, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                # 不要な属性を削除
                cookie.pop("sameSite", None)
                cookie.pop("secure", None)
                cookie.pop("httpOnly", None)
            return cookies
        else:
            raise RuntimeError("[FATAL]: Cookies not found")
    @staticmethod
    def show_notification(title, message):
        # Tk ウィンドウの作成
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを隠す
        messagebox.showinfo(title, message)

    def run(self, file_edited_mode: bool = True):
        print(f"[LoRA-Model-Installer]: Starting.. (target: {len(self.data.keys())} / Batch: 1)")
        print("[INFO]: Starting Selenium/Chrome..", end=" ")
        chrome_options = Options()
        # chrome_options.add_argument("--user-data-dir=./selenium_profile")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # chrome_options.add_argument("--no-sandbox")  # サンドボックスモードを無効化
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        service = Service(executable_path=shared.driver_path)
        print("done")

        print("[INFO]: Initializing output directory..", end=" ")
        download_path = os.path.join(os.getcwd(), "outputs")
        if shared.sd_webui_exists:
            builder_cfg = BuilderConfig()
            builder_cfg.required = False
            webui_path = JsonUtilities("./a1111_webui_pth.json", builder_cfg)
            if webui_path.loadable:
                download_path = os.path.join(
                    webui_path.read()["path"], "models/Lora"
                )
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
        os.makedirs(download_path, exist_ok=True)

        # ダウンロードパスを設定したのちに Selenium を初期化する
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://civitai.com")
        time.sleep(1.5)
        database = LoRADatabaseProcessor()
        print("done")

        urls = list(self.data.keys())
        for (i, url) in enumerate(urls):
            print(f"[PHASE]: Phase 1/3 - Resize Download data (Target: {i + 1})")
            keys = list(self.data.keys())
            key = keys[i]
            fn: str = self.data[key][0]
            api: bool = self.data[key][1]
            if api:
                q = (url, fn, ["API modes cannot obtain Trigger words"], None, "")
                print(f"[INFO]: done ({q})")

            # APIモード外なら、すべてのデータを取得する
            else:
                print("[INFO]: Scraping model info..")
                try:
                    # Cookie の読み込み
                    self.load_cookies(driver)
                    if not os.path.exists(self.COOKIE_PATH):
                        print("[INFO]: No cookies found. Redirecting to login page...")
                        # self.show_notification("lunapy / SD-PEM", "Please log in to CivitAI. This step is required only once.")

                        # navigator.webdriver の削除で検出回避
                        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                        # ログインページに移動
                        driver.get("https://civitai.com/login")
                        print("[README] :: Please complete the login process manually. (see console) :: [README]")  # <<< ここで途切れる
                        input("[README] :: Press Enter after completing the login :: [README]")
                        self.save_cookies(driver)
                        print("[INFO]: Cookies saved successfully. You can now run the script without logging in.")

                    # モデルページにアクセス
                    driver.get(url)

                    # 読み込み待機
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.mantine-Title-root"))
                    )
                    print("[DEV]: site loaded.")

                    html = driver.page_source
                    soup = BeautifulSoup(html, "html.parser")

                    print("[INFO]: parsing html..")
                    download_button = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/api/download/']"))
                    )
                    api_link = download_button.get_attribute("href")
                    print(f"[DEV]: api_link: {api_link}")

                    # トリガーワードの取得
                    trigger_td = soup.find("td", class_="mantine-kimpif", string="Trigger Words")
                    if trigger_td:
                        parent_tr = trigger_td.find_parent("tr", class_="mantine-1avyp1d")
                        target_td = parent_tr.find("td", class_="mantine-e7hg0y")
                        if target_td:
                            trigger_divs = target_td.select("div > div > span > div")
                            trigger_words = [div.get_text(strip=True) for div in trigger_divs]
                        else:
                            print("[WARN]: Trigger words cannot found")
                            trigger_words = ["Trigger words cannot found"]
                    else:
                        trigger_words = ["Trigger words not defined"]
                    print(f"[DEV]: trigger_words: {trigger_words}")

                    # Selling Image 状態の取得
                    cant_sell_gend_image = False
                    parent_div = soup.find("div", class_="mantine-1ti00ln")
                    if parent_div:
                        target_div = parent_div.find("div", class_="mantine-tfrofo")
                        if target_div:
                            svg_element = target_div.find("svg", {
                                "xmlns": "http://www.w3.org/2000/svg",
                                "class": "tabler-icon tabler-icon-photo-off"
                            })
                            if svg_element:
                                cant_sell_gend_image = True

                    print(f"[DEV]: image_sellable: {not cant_sell_gend_image}")
                    q = (api_link, fn, trigger_words, not cant_sell_gend_image, url)
                except TimeoutException as e:
                    print("[ERROR]: TimeoutException. Skipping process..")
                    continue
                print(f"[INFO]: done ({q})")

            # Phase2
            print(f"[PHASE]: Phase 2/3 - Download Models and save (target: {i+1})")
            print(f"[DEV]: target path: {download_path}")
            url, fn, tws, sellable, raw_url = q #再代入
            # api_link, filename, trigger_words, sellable, raw_url
            print(f"[INFO]: Requesting to {url}")
            # フォーマットを検出
            formats = re.findall(r"&format=(safetensor|ckpt|pth|safetensors)", url.lower())
            if len(formats) > 0:
                if formats[0] == "safetensor": formats = ["safetensors"]
                format = "." + formats[0]
            else:
                format = ".safetensors"
            print(f"[DEV]: detected format: {format}")

            response = requests.get(url, cookies=self.get_requests_cookie(), stream=True, allow_redirects=True)
            if response.status_code != 200:
                if response.status_code == 401:
                    print(f"[FATAL]: respones == 401, if that models requires login, try refresh your cookies (to delete /civitai_cookies.json)")
                    continue
                #
                #     print(f"[ERROR]: 401 Unauthorized\n[INFO]: Switching Selenium model scraping..")
                #     # リクエスト失敗 (401) の時、Seleniumに切り替える
                #     prv_files = [
                #         x
                #         for x in os.listdir(download_path)
                #         if not os.path.splitext(x)[1].lower() in [".crdownload", ".tmp"]
                #     ]
                #     driver.get(url)
                #     print(f"[DEV]: starting download..")
                #     if file_edited_mode: # デフォルト: True
                #         # ファイル監視によってダウンロード完了を検出する
                #         while len(prv_files) == len([x for x in os.listdir(download_path) if not os.path.splitext(x)[1].lower() in [".crdownload", ".tmp"]]):
                #             time.sleep(0.5)
                #     else:
                #         time.sleep(15) # LoRA なのでそこまでかからない
                #     new_files = [
                #         x
                #         for x in os.listdir(download_path)
                #         if not os.path.splitext(x)[1].lower() in [".crdownload", ".tmp"]
                #     ]
                #     if len(prv_files) == len(new_files):
                #         # ダウンロードが検出されなかったら
                #         RuntimeError(f"[FATAL]: unHandled exception: files not changed")
                #     try:
                #         new_file = [
                #             x
                #             for x in new_files
                #             if not x in prv_files
                #         ][0]
                #     except IndexError as e:
                #         raise IndexError("[FATAL]: No new files detected. Some files might have been deleted or moved.")
                #
                #     fn += os.path.splitext(new_file)[1].lower()
                #     os.rename(
                #         os.path.join(download_path, new_file),
                #         os.path.join(download_path, fn)
                #     )
                #     print("[INFO]: Selenium API scraping done")
                #     print(f"[INFO]: saved at {download_path}/{fn}")
                # else:
                #     print(f"[CRITICAL]: request failed: {response.status_code}")
                #     continue
            else:
                # リクエスト成功時の処理
                file_size = int(response.headers.get("Content-Length", 0))
                print(f"[DEV]: Expected file size: {file_size / (1024 * 1024):.2f} MB")

                content = response.content
                print(f"[INFO]: Saving file..", end=" ")
                try:
                    fn += format
                    with open(os.path.join(download_path, f"{fn}"), "wb") as f:
                        f.write(content)
                        print(f"saved at {download_path}/{fn}")
                except Exception as e:
                    print("\n[ERROR]: Failed to save file. see console for more information")
                    print(e)
                    continue

            # safetensors から trigger を取得
            lora = ""
            if format.lower() == ".safetensors":
                try:
                    sft_path = os.path.join(download_path, fn)
                    reader = LoRAMetadataReader(sft_path)
                    lora_name = reader.get_output_name()
                    if lora_name is not None:
                        lora = f"<lora:{lora_name}:1>"
                        print(f"[DEV]: Detected lora trigger: {lora}")
                except Exception as e:
                    print("Error occurred in parse safetensors: ", end="")
                    print(e)
                    pass
            with open(os.path.join(download_path, fn), "rb") as f:
                # sha256を計算
                hash_obj = hashlib.sha256()
                hash_obj.update(f.read())
                sha256s = hash_obj.hexdigest()

            p = (url, tws, sellable, fn, sha256s, raw_url, lora)

            print(f"[PHASE]: Phase 3/3 - Saving model data to PEM-Database (target: {i+1})")
            api_url, tws, sell, fn, sh, raw_url, lora = p
            if raw_url == "": raw_url = "/"
            database.new(
                sh, True, **{
                    "trigger_words": tws,
                    "sellable": sell,
                    "file_name": fn,
                    "url": raw_url,
                    "api_url": api_url,
                    "name": raw_url.strip("/").split("/")[-1],
                    "lora": lora
                }
            )
            print(f"[INFO]: Model data saved successfully: {sh}")
            print(f"[DEV]: Completed Task: {i+1}")
        print("ALL Processes done.")
        driver.quit()
        return

    def push(self, url: str, fn: str, api: bool):
        self.data[url] = (fn, api)

    def get_requests_cookie(self):
        if os.path.exists(self.COOKIE_PATH):
            with open(self.COOKIE_PATH, "r") as f:
                cookies = json.load(f)

            cookie_dict = {}
            for cookie in cookies:
                name = cookie.get("name")
                value = cookie.get("value")
                if name and value:
                    cookie_dict[name] = value

            return cookie_dict


"""
/configs/lora_database.json を1次元的に処理するための機構を持つクラス
"""
class LoRADatabaseProcessor:
    def __init__(self):
        buildercfg = BuilderConfig()
        buildercfg.required = True
        self.database = JsonUtilities(os.path.join(os.getcwd(), "configs/lora_database.json"), buildercfg)

    @staticmethod
    def time_now():
        return datetime.now().isoformat()

    def load(self) -> dict:
        return self.database.read()

    def save(self, new):
        # バックアップ
        with open(os.path.join(os.getcwd(), f"logs/lora_database/{self.time_now().replace(':', '-')}-backup.json"), "w", encoding="utf-8") as f:
            json.dump(self.load(), f, indent=4, ensure_ascii=False)  # type: ignore
        self.database.save(new)

    @staticmethod
    def get_default() -> dict:
        return {
            "version": 1,  # DO NOT CHANGE
            "name": "",
            "trigger_words": [],
            "sellable": False,
            "file_name": "",
            "url": "",
            "api_url": "",
            "lora": "",
            "timestamp": None
        }

    def new(
            self, key: str, overwrite: bool = False, **kwargs
    ):
        prv = self.load()
        new = self.get_default()

        if key in prv.keys():
            print("keys already defined.")
            if not overwrite:
                return

        for (k, v) in kwargs.items():
            if k == "version" or k == "timestamp":
                continue

            if not k in new.keys():
                print(f"Unknown key: {k}")
                continue

            if new[k] is None:
                new[k] = v
                continue

            # bool 型の特別なチェック
            if isinstance(new[k], bool) and not isinstance(v, bool):
                print(f"Type mismatch for key '{k}': Expected bool, got {type(v).__name__}")
                continue

            # 型が一致するかチェック
            if not isinstance(v, type(new[k])):
                print(f"Type mismatch for key '{k}': Expected {type(new[k]).__name__}, got {type(v).__name__}")
                continue

            new[k] = v
        new["timestamp"] = self.time_now()

        prv[key] = [
            new
        ]
        self.save(prv)
