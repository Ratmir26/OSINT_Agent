#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный скрапер на Selenium для JS-сайтов
Использует headless Chrome для обхода защит и рендеринга JavaScript
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def create_driver(headless=True):
    """Создание headless Chrome драйвера"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def scrape_with_selenium(url: str, wait_for=None, timeout=20) -> str:
    """
    Скрапинг страницы через Selenium
    
    Args:
        url: URL страницы
        wait_for: CSS-селектор элемента для ожидания загрузки
        timeout: Таймаут ожидания
    
    Returns:
        HTML-код страницы
    """
    driver = create_driver(headless=True)
    try:
        driver.get(url)
        
        if wait_for:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )
        else:
            time.sleep(5)
        
        # Скролл для подгрузки lazy-контента
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        html = driver.page_source
        return html
    finally:
        driver.quit()


def scrape_2gis_page(organization_url: str) -> dict:
    """Скрапинг страницы организации в 2GIS"""
    print(f"[Selenium] Скрапинг 2GIS: {organization_url}")
    html = scrape_with_selenium(organization_url, wait_for="[class*=contact]", timeout=25)
    
    data = {
        "phones": re.findall(r'\+996\s?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}', html),
        "emails": re.findall(r'[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}', html),
        "socials": {},
    }
    
    # Соцсети
    ig = re.findall(r'instagram\.com/[\w.]+', html)
    if ig:
        data["socials"]["Instagram"] = f"https://{ig[0]}"
    
    wa = re.findall(r'wa\.me/\d+', html)
    if wa:
        data["socials"]["WhatsApp"] = f"https://{wa[0]}"
    
    print(f"[Selenium] Найдено: {len(data['phones'])} телефонов")
    return data


def scrape_instagram_profile(username: str) -> dict:
    """Получение базовой информации об Instagram профиле"""
    url = f"https://www.instagram.com/{username}/"
    print(f"[Selenium] Instagram: {url}")
    
    try:
        html = scrape_with_selenium(url, wait_for="header", timeout=15)
        
        # Мета-данные
        meta_desc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
        description = meta_desc.group(1) if meta_desc else ""
        
        followers_match = re.search(r'(\d[\d,\s]*)\s*followers', html, re.I)
        followers = followers_match.group(1).strip() if followers_match else ""
        
        return {
            "username": username,
            "url": url,
            "description": description[:200],
            "followers": followers,
        }
    except Exception as e:
        print(f"[Selenium] Ошибка Instagram: {e}")
        return {"username": username, "url": url, "error": str(e)}


if __name__ == "__main__":
    # Пример использования
    import sys
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scraper_selenium.py 2gis <url>")
        print("  python scraper_selenium.py instagram <username>")
        sys.exit(1)
    
    mode = sys.argv[1]
    target = sys.argv[2]
    
    if mode == "2gis":
        result = scrape_2gis_page(target)
        print(result)
    elif mode == "instagram":
        result = scrape_instagram_profile(target)
        print(result)
