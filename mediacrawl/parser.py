import orjson
import logging
from pathlib import Path
from io import BufferedWriter
from typing import Dict, List, Optional
from articledata import Article
from trafilatura import bare_extraction

from mediacrawl.config import CrawlConfig, SiteConfig
from mediacrawl.language import detect_language
from mediacrawl.page import Page
from mediacrawl.db import engine
from mediacrawl.url import URL

log = logging.getLogger(__name__)


class Parser(object):
    def __init__(self, config: CrawlConfig):
        self.config = config

    def get_site_config(self, name: str) -> Optional[SiteConfig]:
        for site in self.config.sites:
            if name == site.name:
                return site
        return None

    def check_parse(self, page: Page) -> bool:
        config = self.get_site_config(page.site)
        if config is None:
            return False
        if config.parse is None:
            return True
        if config.parse.check(page.url, page) is False:
            return False
        return True

    async def parse(self, page: Page) -> Optional[Article]:
        if not self.check_parse(page):
            return None
        log.info("Parsing: %r", page.url)
        article = Article(
            id=page.url.id,
            url=page.url.url,
            title=page.url.url,
            site=page.site,
            bylines=[],
            language="xxx",
            locale="xx",
            text="",
            extracted_at=page.timestamp.isoformat(),
        )
        if page.text is None:
            return None

        extract: Dict[str, str] = bare_extraction(
            page.text, url=page.url.url, include_comments=False
        )
        if extract is not None:
            article.title = extract.get("title", article.title)
            article.date = extract.get("date")
            article.text = extract.get("text", article.text)
            author = extract.get("author")
            if author is not None:
                article.bylines.append(author)

        lang = detect_language(article.text)
        if lang is not None:
            article.language = lang
        return article

    async def run(self, outpath: Path, sites: List[str]):
        outpath.mkdir(parents=True, exist_ok=True)
        handles: Dict[str, BufferedWriter] = {}
        async with engine.connect() as conn:
            async for page in Page.iter_parse(conn, sites=sites):
                article = await self.parse(page)
                if article is None:
                    continue
                if article.site not in handles:
                    path = outpath.joinpath(f"{article.site}.ijson")
                    handles[article.site] = open(path, "wb")
                line = orjson.dumps(article.dict(), option=orjson.OPT_APPEND_NEWLINE)
                handles[article.site].write(line)

        for fh in handles.values():
            fh.close()
