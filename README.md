# Selenium Proxy Example for Python

A small Selenium 4 + Python example that configures an HTTP/HTTPS proxy in Chrome, checks the browser's public exit IP, and then loads a target page.

The example is intended for authorized website testing, QA, and regional content verification.

## What it demonstrates

- Configure an HTTP/HTTPS proxy through Selenium 4 browser options.
- Use Chrome with a locally installed ChromeDriver.
- Compare the machine's direct public IP with the IP observed by Chrome.
- Test a target page separately from the IP-check request.
- Read settings from environment variables instead of hard-coding them.
- Use explicit waits and close the browser in a `finally` block.

> **Authentication note:** This example uses proxy IP allowlisting. It does not implement HTTP proxy username/password authentication. Selenium's standard Python `Proxy` object configures proxy endpoints, but it does not provide general HTTP proxy username/password fields. Verify browser-specific authentication methods separately before adapting this example.

## Tested environment

The original end-to-end test for this example was run with:

| Component | Tested environment |
|---|---|
| OS | Ubuntu 24.04 LTS (x86_64) |
| Python | 3.12 |
| Selenium | Selenium 4 |
| Browser | Google Chrome 156.0.8078.79 |
| Driver | ChromeDriver 156.0.8078.79 |
| Proxy protocol | HTTP/HTTPS |
| Proxy authentication | IP allowlisting |
| Browser mode | Headless Chrome |

The tested run confirmed that Chrome's observed public IP differed from the server's direct public IP, and that the target page loaded successfully.

These are the versions used in that test, not a claim that other versions are incompatible. Keep Chrome and ChromeDriver compatible.

## Requirements

- Python 3.9 or newer (the tested environment used Python 3.12).
- Google Chrome installed on the machine that runs the script.
- A compatible ChromeDriver installed on that same machine.
- A reachable HTTP/HTTPS proxy endpoint.
- For IP allowlisting, the public egress IP of the machine running Chrome must be added to the proxy provider's allowlist.
- Network access to the IP-check service and the target website.

For Selenium Grid or Remote WebDriver, the browser node—not necessarily the Python client—must be able to reach the proxy. The IP to allowlist is generally the browser node's public egress IP.

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Chrome and a compatible ChromeDriver separately if they are not already installed. On the tested Ubuntu setup, the paths were:

```text
/usr/bin/google-chrome
/usr/local/bin/chromedriver
```

Check the installed versions:

```bash
google-chrome --version
chromedriver --version
```

The browser and driver versions should be compatible.

### Why specify a local ChromeDriver?

The script passes an explicit `Service` path to Selenium:

```python
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)
```

This avoids relying on Selenium Manager to download a driver at runtime. This can be useful when the machine's network or proxy authentication prevents Selenium Manager from reaching the driver download service.

## Configuration

Set the proxy gateway and target page in your shell:

```bash
export PROXY_SERVER="gw.kindproxy.com:12200"
export TARGET_URL="https://example.com/"
export EXPECTED_TEXT="Example Domain"
```

Optional settings:

```bash
export CHROME_BINARY="/usr/bin/google-chrome"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
export HEADLESS="true"
export PAGE_LOAD_TIMEOUT="60"
export IP_CHECK_TIMEOUT="20"
export TARGET_WAIT_TIMEOUT="30"
```

`EXPECTED_TEXT` is optional. If it is empty or unset, the script loads the target page without checking for a specific body-text marker.

Do not commit real proxy credentials, private endpoints, or other secrets to a public repository. This example does not need a username or password when the proxy is configured for IP allowlisting.

### Windows PowerShell

Set the same variables in PowerShell:

```powershell
$env:PROXY_SERVER = "gw.kindproxy.com:12200"
$env:TARGET_URL = "https://example.com/"
$env:EXPECTED_TEXT = "Example Domain"
$env:CHROME_BINARY = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$env:CHROMEDRIVER_PATH = "C:\tools\chromedriver.exe"
$env:HEADLESS = "true"
```

Adjust the browser and driver paths to match your machine.

## Run

```bash
python selenium_proxy_check.py
```

Typical successful output looks like:

```text
Direct connection IP: <your-server-public-ip>
Browser exit IP: <proxy-exit-ip>
Direct and browser IPs are different; the proxy route appears active.
Page title: 'Example Domain'
Current URL: https://example.com/
Page content preview: '...'
Target page loaded: https://example.com/
Target page check: passed
```

The actual IP addresses will differ. The script does not expect a fixed proxy exit IP.

## How the test works

1. Python makes a direct IP-check request with environment proxy variables disabled.
2. Selenium starts Chrome with the configured HTTP and HTTPS proxy endpoint.
3. Chrome opens the IP-check service and reports the browser-observed exit IP.
4. The script compares the direct IP and browser exit IP.
5. Chrome opens `TARGET_URL` and checks the page independently.
6. The browser is closed even if a check fails.

An IP difference is evidence that the browser is using a different network exit. It does not guarantee that every destination will load or return a particular regional version.

## Troubleshooting

### `NoSuchDriverException` or Selenium Manager cannot download ChromeDriver

Install Chrome and a compatible ChromeDriver locally, then set `CHROME_BINARY` and `CHROMEDRIVER_PATH` to their actual paths. The script uses the explicit local driver path to avoid a runtime driver download.

### `407 Proxy Authentication Required`

The proxy did not accept the current authentication. If using IP allowlisting, confirm that the public egress IP of the machine running Chrome is allowlisted. Also verify the gateway host, port, and protocol.

This repository's example does not implement HTTP username/password proxy authentication.

### Browser exit IP check times out

Check the proxy endpoint, allowlist, port, outbound network access, and whether the IP-check service is reachable through the proxy. The browser may start successfully even when its first proxied request cannot complete.

### Direct IP and browser exit IP are the same

Confirm that the proxy object is attached to the Chrome options passed to `webdriver.Chrome()`. Recheck the endpoint and the browser's effective proxy route.

### IP check succeeds but the target page fails

The IP-check destination and target website are separate tests. The target may be unavailable, slow, require cookies, show a challenge, or use account and browser settings for regional behavior.

### Expected text assertion fails

Check the printed page title, current URL, and body preview. Set `EXPECTED_TEXT` to text that actually appears in the target page, or leave it empty to disable the text assertion.

## Security and responsible use

- Use the script only on websites you own or are authorized to test.
- Do not hard-code proxy usernames, passwords, or other secrets in source code.
- Avoid printing credentials or sensitive session data in logs.
- Respect the target website's terms, access controls, and applicable laws.

## Related tutorial

Read the companion guide:

**How to Use a Proxy with Selenium in Python**  
https://www.kindproxy.com/blog/en/blog/selenium-proxy-python-2026/

## License

No license is included yet. Add a license file if you want to grant others explicit permission to use, modify, and redistribute this repository.
