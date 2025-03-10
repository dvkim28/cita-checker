import os
import time
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from telegram import send_telegram_message
from datetime import datetime

load_dotenv()

NIE = os.getenv("NIE")
NAME = os.getenv("NAME")
URL = "https://icp.administracionelectronica.gob.es/icpplus/index.html"


def wait_random():
    """Случайная задержка для имитации реального пользователя"""
    time.sleep(random.uniform(2, 5))


def get_cita_cite():
    cita = False  # Изначально считаем, что записей нет

    while not cita:
        formatted_time = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Запуск Playwright... {formatted_time}")


        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=500)  # Отключаем headless для отладки
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Отключаем `navigator.webdriver`, чтобы браузер выглядел "человеческим"
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = context.new_page()
            print("Открытие страницы...")
            page.goto(URL, wait_until="networkidle")  # Ждем полной загрузки сети
            wait_random()

            print("Выбор провинции Валенсия...")
            page.select_option("#form", "Valencia")
            page.click("#btnAceptar")
            wait_random()

            print("Выбор услуги...")
            page.select_option("#tramiteGrupo\\[0\\]", "4112")
            wait_random()
            page.click("#btnAceptar")
            wait_random()

            print("Закрытие куки-баннера...")
            try:
                page.evaluate("document.getElementById('cookie-law-info-bar').style.display = 'none';")
            except:
                print("Куки-баннер не найден.")

            print("Вход в систему...")
            page.click("#btnEntrar")
            wait_random()

            print("Выбор страны происхождения...")
            page.select_option("#txtPaisNac", "153")

            print("Заполнение NIE и имени...")
            page.fill("#txtIdCitado", NIE)
            wait_random()
            page.fill("#txtDesCitado", NAME)
            wait_random()

            print("Кликаем кнопку подтверждения...")
            btn = page.query_selector_all(".mf-button.primary")[0]
            btn.click()
            wait_random()
            btn= page.query_selector_all(".mf-button.primary")[0]
            btn.click()

            print("Анализ содержимого страницы...")
            cita = parse_page_content(page.content())

            browser.close()
            print("Браузер закрыт.")
            time.sleep(600)


def parse_page_content(page_content):
    soup = BeautifulSoup(page_content, "html.parser")
    print(soup.prettify())
    notification = soup.find("p", {"class": "mf-msg__info"})

    if notification:
        print("Записей нет (no cita)")
        return False
    else:
        CHAT_ID = os.getenv("TELEGRAM_OWN")
        send_telegram_message(CHAT_ID)
        print("Есть свободные записи (citas)!")
        return True


if __name__ == "__main__":
    get_cita_cite()
