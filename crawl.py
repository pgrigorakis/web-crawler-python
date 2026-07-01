from typing import TypedDict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def crawl_page(
    base_url: str, current_url: str = None, page_data: dict[str, PageData] = None
):
    parsed_base_url = urlparse(base_url)
    parsed_current_url = urlparse(current_url)

    if parsed_base_url.netloc != parsed_current_url.netloc:
        return

    norm_current_url = normalize_url(current_url)
    if norm_current_url in page_data.keys():
        return

    html_body = safe_get_html(current_url)
    extracted_html_elems = extract_page_data(html_body, current_url)
    page_data[norm_current_url] = extracted_html_elems

    for url in extracted_html_elems["outgoing_links"]:
        crawl_page(base_url, url, page_data)


def get_html(url):
    try:
        res = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    except Exception as e:
        raise Exception(f"network error while fetching {url}: {e}")

    if res.status_code > 399:
        raise Exception(f"{res.status_code} error: {res.reason}")

    content_type = res.headers.get("Content-Type")
    if "text/html" not in content_type:
        raise Exception(f"content type not text/html: {content_type}")

    return res.text


def safe_get_html(url: str) -> str | None:
    try:
        return get_html(url)
    except Exception as e:
        print(f"{e}")
        return None


def normalize_url(url: str) -> str:
    parsedURL = urlparse(url)

    normalised = f"{parsedURL.netloc}{parsedURL.path}".lower().rstrip("/")

    return normalised


def extract_page_data(html: str, page_url: str) -> PageData:
    page_data: PageData = {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }

    return page_data


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    if heading is None:
        heading = soup.find("h2")

    return heading.get_text(strip=True) if isinstance(heading, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main_tag = soup.find("main")
    if main_tag is None:
        p_tag = soup.find("p")
    else:
        p_tag = main_tag.find("p")

    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""


def get_urls_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = soup.find_all("a")

    url_list = []
    for url in urls:
        if not isinstance(url, Tag):
            continue
        href = url.get("href")
        if isinstance(href, str) and href:
            try:
                absolute_url = urljoin(base_url, href)
                url_list.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {href}")

    return url_list


def get_images_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    imgs = soup.find_all("img")

    img_list = []
    for img in imgs:
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            try:
                absolute_url = urljoin(base_url, src)
                img_list.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {src}")

    return img_list
