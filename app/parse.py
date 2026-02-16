from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

from dataclasses import dataclass
from urllib.parse import urljoin
from pathlib import Path

import csv


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

OUTPUT_PATH = Path(__file__).resolve().parent.parent


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_row(row: list[WebElement]) -> list[Product]:
    products = []

    for item in row:

        title = (
            item.find_element(By.CLASS_NAME, "title")
            .get_attribute("title")
        )

        description = item.find_element(
            By.CSS_SELECTOR, "p.description[itemprop='description']"
        ).text

        try:
            price_text = item.find_element(
                By.CSS_SELECTOR,
                "span[itemprop='price']"
            ).text
            price = float(price_text.replace("$", "").replace(",", ""))
        except NoSuchElementException:
            price_text = item.find_element(
                By.CLASS_NAME, "price"
            ).text
            price = float(price_text.replace("$", "").replace(",", ""))

        try:
            rating = int(
                item.find_element(By.CSS_SELECTOR, "p[data-rating]")
                    .get_attribute("data-rating")
            )
        except NoSuchElementException:
            rating_stars = item.find_elements(
                By.CSS_SELECTOR,
                ".ws-icon.ws-icon-star"
            )
            rating = len(rating_stars)

        num_of_reviews = int(
            item.find_element(
                By.CSS_SELECTOR,
                "span[itemprop='reviewCount']"
            ).text
        )

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def click_button(button: WebElement, driver: webdriver.Chrome) -> None:
    driver.execute_script("arguments[0].click();", button)


def get_products_from_page(
    page_url: str,
    driver: webdriver.Chrome
) -> list[Product]:
    driver.get(page_url)

    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        click_button(cookie_button, driver)
    except Exception:
        pass

    while True:
        more_button = driver.find_elements(
            By.CSS_SELECTOR,
            ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
        )

        if not more_button or not more_button[0].is_displayed():
            break

        click_button(more_button[0], driver)

    products = []
    row = driver.find_elements(
        By.CSS_SELECTOR,
        ".col-md-4.col-xl-4.col-lg-4"
    )
    products.extend(parse_row(row))

    return products


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(
        OUTPUT_PATH / filename, "w",
        newline="",
        encoding="utf-8"
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products(driver: webdriver.Chrome = webdriver.Chrome()) -> None:
    pages = [
        (HOME_URL, "home.csv"),
        (urljoin(HOME_URL, "computers"), "computers.csv"),
        (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
        (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
        (urljoin(HOME_URL, "phones"), "phones.csv"),
        (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
    ]

    for url, filename in pages:
        products = get_products_from_page(url, driver)
        write_products_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
