import undetected_chromedriver as uc
import time
import random
import os
import requests
import json
from datetime import datetime

def load_proxies(file_path="proxy_list.txt"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def load_devices(file_path="device_profiles.json"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def load_links(file_path="adsterra_links.txt"):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []

PROXY_LIST = load_proxies()
DEVICES = load_devices()
ADSTERRA_LINKS = load_links()

def get_geolocation_info():
    try:
        res = requests.get("https://ipapi.co/json/")
        return res.json()
    except Exception as e:
        print(f"[!] Geolocation lookup failed: {e}")
        return {}

def simulate_human_behavior(driver):
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    current = 0
    while current < scroll_height:
        step = random.randint(100, 250)
        current += step
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.5, 1.2))

def open_multiple_tabs(driver, base_url, count=3):
    print(f"[*] Opening {count} tabs")
    for i in range(1, count):
        driver.execute_script(f"window.open('{base_url}', '_blank');")
        time.sleep(random.uniform(0.8, 2))
    tabs = driver.window_handles
    for idx, tab in enumerate(tabs):
        driver.switch_to.window(tab)
        print(f"[*] Tab {idx+1}: {driver.current_url}")
        simulate_human_behavior(driver)
        time.sleep(random.uniform(3, 6))

def test_device(device_name, link, profile, proxy_override=None):
    print(f"\n=== Simulating {device_name.upper()} on link {link} ===")
    options = uc.ChromeOptions()
    options.add_argument(f"--window-size={profile['window_size']}")
    options.add_argument(f"user-agent={profile['user_agent']}")
    # Removed problematic options below
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    if proxy_override:
        options.add_argument(f'--proxy-server=http://{proxy_override}')
        print(f"[*] Using proxy: {proxy_override}")

    driver = None
    try:
        driver = uc.Chrome(options=options, headless=False)
        geo = get_geolocation_info()
        print(f"[*] IP: {geo.get('ip', 'N/A')} ({geo.get('country_name', 'N/A')})")
        print(f"[*] Navigating to: {link}")
        driver.get(link)
        time.sleep(random.uniform(4, 7))
        open_multiple_tabs(driver, link, count=random.randint(2, 3))
        windows = driver.window_handles
        for handle in windows:
            driver.switch_to.window(handle)
            if driver.current_url != link:
                print(f"[!] Detected redirect or popup: {driver.current_url}")
                time.sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        os.makedirs("screenshots", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shot_path = f"screenshots/{device_name}_{ts}.png"
        driver.save_screenshot(shot_path)
        print(f"[*] Screenshot saved: {shot_path}")
    except Exception as e:
        print("[!] Error:", e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"[!] Error while quitting driver: {e}")
            finally:
                try:
                    driver.service = None
                    del driver
                except Exception:
                    pass
        print("[*] Closed browser.\n")

if __name__ == "__main__":
    proxy_list_shuffled = PROXY_LIST[:]
    random.shuffle(proxy_list_shuffled)
    proxy_pool = iter(proxy_list_shuffled * 10)  # repeat proxies
    for link in ADSTERRA_LINKS:
        for device_name, profile in DEVICES.items():
            proxy = next(proxy_pool, None)
            test_device(device_name, link, profile, proxy_override=proxy)
            time.sleep(random.randint(6, 12))
