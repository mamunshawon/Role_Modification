import threading
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class SessionManager:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.login_via_selenium()
        self._start_auto_refresh()
        self.logger.info("Session auto-refresh started")

    # =============================
    # SELENIUM LOGIN
    # =============================

    def login_via_selenium(self):
        self.logger.info("Starting Selenium login for configured user")

        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # If you have local chromedriver path, use Service("path")
        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(self.config["environment"]["login_url"])

            time.sleep(2)

            driver.find_element(By.NAME, "username").send_keys(
                self.config["credentials"]["username"]
            )

            driver.find_element(By.NAME, "password").send_keys(
                self.config["credentials"]["password"]
            )

            driver.find_element(By.TAG_NAME, "button").click()

            time.sleep(3)

            selenium_cookies = driver.get_cookies()
            self.logger.info("Selenium login returned %s cookie(s)", len(selenium_cookies))

            # Transfer cookies to requests session
            self.session.cookies.clear()

            for cookie in selenium_cookies:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain")
                )

            self.logger.info("Selenium login successful. Cookies transferred.")

        finally:
            driver.quit()

    # =============================
    # AUTO REFRESH THREAD
    # =============================

    def _refresh_loop(self):
        interval = self.config["processing"]["session_refresh_interval"]

        while True:
            time.sleep(interval)
            try:
                self.logger.info("Refreshing session via Selenium...")
                self.login_via_selenium()
            except Exception as e:
                self.logger.error(f"Session refresh failed: {e}")

    def _start_auto_refresh(self):
        thread = threading.Thread(target=self._refresh_loop, daemon=True)
        thread.start()

    # =============================
    # THREAD SAFE REQUEST
    # =============================

    def request(self, method, url, **kwargs):
        self.logger.debug("Sending %s request to %s", method, url)
        with self.lock:
            response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            self.logger.warning("401 detected. Re-login via Selenium.")
            self.login_via_selenium()
            with self.lock:
                response = self.session.request(method, url, **kwargs)

        self.logger.debug("%s %s returned status=%s", method, url, response.status_code)
        return response
