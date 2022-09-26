import logging
from typing import TYPE_CHECKING, Generator, Optional, Set
from asyncio.exceptions import TimeoutError
from aiohttp import ClientSession, ClientResponse
from aiohttp.client_exceptions import ClientConnectionError, ClientPayloadError

from mediacrawl.url import URL
from mediacrawl.page import Page
from mediacrawl.db import db_connect

if TYPE_CHECKING:
    from mediacrawl.site import Site

MAX_CONTENT: int = 1024 * 1024 * 20
log = logging.getLogger(__name__)


class Task(object):
    def __init__(self, site: "Site", url: URL) -> None:
        self.site = site
        self.crawler = site.crawler
        self.url = url

    async def enqueue(self, url: URL) -> None:
        if url.scheme not in ["http", "https"]:
            return
        url = url.clean(self.site.config.query_ignore)

        # Check url-based rules only:)
        if not self.check_crawl(url, None):
            return

        if url in self.crawler.seen:
            return
        self.crawler.seen.add(url)
        task = Task(self.site, url)
        await self.crawler.queue.put(task)

    def check_crawl(self, url: URL, page: Optional[Page]) -> bool:
        if self.site.config.crawl is not None:
            if self.site.config.crawl.check(url, page) is False:
                return False
        return True

    def check_parse(self, url: URL, page: Optional[Page]) -> bool:
        if self.site.config.parse is not None:
            if self.site.config.parse.check(url, page) is False:
                return False
        return True

    def extract_urls(self, page: Page) -> Generator[URL, None, None]:
        suffixes: Set[Optional[str]] = set()
        for link in page.doc.findall(".//a"):
            suffixes.add(link.get('href'))
            
        for frame in page.doc.findall(".//iframe"):
            suffixes.add(frame.get('src'))

        for suffix in suffixes:
            if suffix is None:
                continue
            next_url = page.url.join(suffix)
            if next_url is not None:
                yield next_url


    async def handle_page(self, page: Page) -> None:
        page.parse = False
        if page.content is None or len(page.content) < 100:
            return
        if not self.check_crawl(self.url, page):
            return
        if not page.ok:
            return

        if self.check_parse(self.url, page):
            page.parse = True

        for next_url in self.extract_urls(page):
            await self.enqueue(next_url)

    async def retrieve_content(self, page: Page, response: ClientResponse) -> None:
        content = b""
        try:
            while True:
                buffer = await response.content.read(MAX_CONTENT)
                if not len(buffer):
                    break
                content = content + buffer
                if len(content) >= MAX_CONTENT:
                    break
        except ClientPayloadError as payerr:
            log.warning("Did not load full page: %s", payerr)
        page.retrieved = True
        page.content = content

    async def crawl(self, http: ClientSession) -> None:
        if self.url not in self.site.config.urls:
            async with db_connect() as conn:
                cached = await Page.find(conn, self.url)
                if cached is not None:
                    # log.info("Cache hit: %r", cached.url)
                    await self.handle_page(cached)
                    await cached.update_parse(conn)
                    return

        # if self.site.is_delay_locked(self.url):
        #     # log.info("Locked, going to wait...")
        # #     # log.info("Putting %r back on the queue", self)
        # #     self.site.crawler.seen.remove(self.url)
        #     await self.site.crawler.queue.put(self)
        #     return

        async with self.site.delay_url(self.url):
            try:
                async with http.get(self.url.url) as response:
                    if response.status > 299:
                        return
                    log.info("Crawl [%d]: %r", response.status, self.url)
                    page = Page.from_response(self.site.config.name, self.url, response)
                    await self.retrieve_content(page, response)
            except (ClientConnectionError, TimeoutError) as ce:
                log.error("Error [%r]: %r", self, ce)
                return

        await self.handle_page(page)
        async with db_connect() as conn:
            await page.save(conn)

    def __repr__(self) -> str:
        return f"<Task({self.site!r}, {self.url!r})>"

    def __str__(self) -> str:
        return self.url.url
