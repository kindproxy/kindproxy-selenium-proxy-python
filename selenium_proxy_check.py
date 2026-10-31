#!/usr/bin/env python3
"""
Verify that a Selenium-controlled Chrome browser uses an HTTP/HTTPS proxy.

Authentication in this example is based on IP allowlisting. It does not
implement HTTP proxy username/password authentication.

Required environment variables:
    PROXY_SERVER   Proxy host and port, e.g. gw.kindproxy.com:12200
    TARGET_URL     A website you own or are authorized to test

Optional environment variables:
    EXPECTED_TEXT       Text expected on the target page; empty disables assertion
    CHROME_BINARY       Chrome executable; default /usr/bin/google-chrome
    CHROMEDRIVER_PATH   ChromeDriver executable; default /usr/local/bin/chromedriver
    HEADLESS            true/false; default true
    PAGE_LOAD_TIMEOUT   Seconds; default 60
    IP_CHECK_TIMEOUT    Seconds; default 20
    TARGET_WAIT_TIMEOUT Seconds; default 30
"""

import json
import os
import sys
import urllib.error
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait


def positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name, str(default))
    try:
        value = int(raw_value)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        raise SystemExit(
            f"{name} must be a positive integer; received {raw_value!r}."
        )


def get_direct_ip(timeout: int) -> str:
    """Get this machine's public IP without using proxy environment variables."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(
        "https://api.ipify.org?format=json", timeout=timeout
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))

    ip_address = payload.get("ip")
    if not ip_address:
        raise ValueError("The direct IP service did not return an IP address.")
    return ip_address


def get_browser_exit_ip(driver: webdriver.Chrome, timeout: int) -> str:
    """Get the public IP observed by the Selenium-controlled browser."""
    driver.set_page_load_timeout(timeout)
    driver.get("https://api.ipify.org?format=json")

    body_text = WebDriverWait(driver, timeout).until(
        lambda browser: browser.find_element(
            By.TAG_NAME, "body"
        ).text.strip()
    )
    payload = json.loads(body_text)

    ip_address = payload.get("ip")
    if not ip_address:
        raise ValueError("The browser IP-check service did not return an IP.")
    return ip_address


def main() -> int:
    proxy_server = os.environ.get("PROXY_SERVER", "").strip()
    target_url = os.environ.get("TARGET_URL", "").strip()
    expected_text = os.environ.get("EXPECTED_TEXT", "")

    chrome_binary = os.environ.get(
        "CHROME_BINARY", "/usr/bin/google-chrome"
    ).strip()
    chromedriver_path = os.environ.get(
        "CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver"
    ).strip()

    headless = os.environ.get("HEADLESS", "true").strip().lower() in {
        "1", "true", "yes", "on"
    }

    page_load_timeout = positive_int_env("PAGE_LOAD_TIMEOUT", 60)
    ip_check_timeout = positive_int_env("IP_CHECK_TIMEOUT", 20)
    target_wait_timeout = positive_int_env("TARGET_WAIT_TIMEOUT", 30)

    if not proxy_server:
        print(
            "Missing PROXY_SERVER. Example: "
            "export PROXY_SERVER='gw.kindproxy.com:12200'",
            file=sys.stderr,
        )
        return 2

    if not target_url:
        print(
            "Missing TARGET_URL. Set it to a website you own "
            "or are authorized to test.",
            file=sys.stderr,
        )
        return 2

    # This example uses IP allowlisting. The proxy endpoint is configured
    # without embedding credentials in the URL.
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = proxy_server
    proxy.ssl_proxy = proxy_server

    options = webdriver.ChromeOptions()
    options.binary_location = chrome_binary
    options.proxy = proxy

    if headless:
        options.add_argument("--headless=new")

    # Common options for running Chrome on a Linux server/container.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Supplying the local driver path avoids Selenium Manager's runtime
    # driver download. Chrome and ChromeDriver must be compatible.
    service = Service(executable_path=chromedriver_path)
    driver = None

    try:
        try:
            direct_ip = get_direct_ip(ip_check_timeout)
            print(f"Direct connection IP: {direct_ip}")
        except (
            OSError,
            TimeoutError,
            urllib.error.URLError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            direct_ip = None
            print(
                f"Direct IP check could not be completed: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

        driver = webdriver.Chrome(service=service, options=options)

        browser_exit_ip = get_browser_exit_ip(driver, ip_check_timeout)
        print(f"Browser exit IP: {browser_exit_ip}")

        if direct_ip:
            if direct_ip == browser_exit_ip:
                print(
                    "WARNING: Direct and browser IPs match. "
                    "Check the proxy endpoint, allowlist, and browser routing."
                )
            else:
                print(
                    "Direct and browser IPs are different; "
                    "the proxy route appears active."
                )

        # Test the destination separately from the IP-check service.
        driver.set_page_load_timeout(page_load_timeout)
        driver.get(target_url)

        WebDriverWait(driver, target_wait_timeout).until(
            lambda browser: browser.execute_script(
                "return document.readyState"
            ) in ("interactive", "complete")
        )

        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Page title: {driver.title!r}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page content preview: {page_text[:500]!r}")

        if expected_text and expected_text not in page_text:
            raise AssertionError(
                f"Expected text {expected_text!r} was not present "
                "on the target page."
            )

        print(f"Target page loaded: {driver.current_url}")
        print("Target page check: passed")
        return 0

    except TimeoutException:
        print(
            "A browser wait timed out. Check proxy connectivity, the "
            "destination response, and timeout settings.",
            file=sys.stderr,
        )
        raise
    except WebDriverException as exc:
        print(
            f"WebDriver error: {type(exc).__name__}: {exc.msg}",
            file=sys.stderr,
        )
        raise
    except (
        OSError,
        urllib.error.URLError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print(
            f"Network or response error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
