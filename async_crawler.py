import asyncio
from urllib.parse import urlparse
from types import TracebackType

import aiohttp

from crawl import PageData, extract_page_data, normalize_url


async def crawl_site_async(
    base_url: str, max_concurrency: int, max_pages: int
) -> dict[str, PageData]:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()


class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int, max_pages: int) -> None:
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session: aiohttp.ClientSession | None = None
        self.should_stop = False
        self.all_tasks: set[asyncio.Task[None]] = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        assert self.session is not None
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
            if normalized_url in self.page_data:
                return False
            if len(self.page_data) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                for task in self.all_tasks:
                    if not task.done():
                        task.cancel()
                return False
            return True

    async def get_html(self, url):
        try:
            async with self.session.get(
                url, headers={"User-Agent": "BootCrawler/1.0"}
            ) as response:
                if response.status > 399:
                    print(f"Error: HTTP {response.status}: {response.reason}")
                    return None

                content_type = response.headers.get("Content-Type")
                if "text/html" not in content_type:
                    print(f"content type not text/html: {content_type}")
                    return None

                return await response.text()
        except Exception as e:
            print(f"network error while fetching {url}: {e}")
            return None

    async def crawl_page(self, current_url: str):
        if self.should_stop:
            return

        parsed_current_url = urlparse(current_url)

        if self.base_domain != parsed_current_url.netloc:
            return

        norm_current_url = normalize_url(current_url)
        if not await self.add_page_visit(norm_current_url):
            return

        async with self.semaphore:
            html_body = await self.get_html(current_url)
            if html_body is None:
                return
        extracted_html_elems = extract_page_data(html_body, current_url)

        async with self.lock:
            self.page_data[norm_current_url] = extracted_html_elems

        if self.should_stop:
            return

        next_urls = extracted_html_elems["outgoing_links"]
        tasks: list[asyncio.Task[None]] = []
        for next_url in next_urls:
            task = asyncio.create_task(self.crawl_page(next_url))
            tasks.append(task)
            self.all_tasks.add(task)

        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                for task in tasks:
                    self.all_tasks.discard(task)

    async def crawl(self) -> dict[str, PageData]:
        await self.crawl_page(self.base_url)
        return self.page_data
