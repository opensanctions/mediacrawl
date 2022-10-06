from lxml import html, etree
from datetime import datetime
from functools import cached_property
from typing import AsyncGenerator, Optional
from pydantic import BaseModel, validator
from charset_normalizer import from_bytes
from aiohttp import ClientResponse
from sqlalchemy import or_, update
from sqlalchemy.future import select

from mediacrawl.url import URL
from mediacrawl.db import Conn, page_table, upsert


class Page(BaseModel):
    site: str
    url: URL
    original_url: URL
    method: str = "GET"
    ok: bool = False
    parse: bool = False
    retrieved: bool = False
    status: Optional[int] = None
    timestamp: datetime
    content_type: Optional[str] = None
    charset: Optional[str] = None
    content: Optional[bytes] = None

    @cached_property
    def text(self) -> Optional[str]:
        if self.content is None or self.content.startswith(b"%PDF-"):
            return None
        if len(self.content) < 100:
            return None
        res = from_bytes(self.content)
        match = res.best()
        if match is not None and match.encoding is not None:
            try:
                return self.content.decode(match.encoding, "strict")
            except UnicodeDecodeError:
                pass
        if self.charset is not None:
            try:
                return self.content.decode(self.charset, "strict")
            except UnicodeDecodeError:
                pass
        # return self.content.decode('utf-8', 'replace')
        return None

    @cached_property
    def doc(self) -> Optional[etree._Element]:
        if self.content is None:
            return None
        if self.text is None:
            return html.document_fromstring(self.content, base_url=self.url.url)
        try:
            return html.document_fromstring(self.text, base_url=self.url.url)
        except ValueError:
            return html.document_fromstring(self.content, base_url=self.url.url)

    @validator("url", "original_url")
    def convert_url(cls, url: Optional[str]) -> Optional[URL]:
        if url is None:
            return None
        return URL(url)

    class Config:
        keep_untouched = (cached_property,)

    @classmethod
    def from_response(
        cls, site: str, original_url: URL, resp: ClientResponse
    ) -> "Page":
        return cls(
            site=site,
            url=URL(str(resp.url)),
            original_url=original_url,
            method=resp.method,
            ok=resp.ok,
            status=resp.status,
            content_type=resp.content_type,
            charset=resp.charset,
            timestamp=datetime.utcnow(),
        )

    @classmethod
    async def find(cls, conn: Conn, url: URL) -> Optional["Page"]:
        stmt = select(page_table)
        clause = or_(
            page_table.c.url == url.url,
            page_table.c.original_url == url.url,
        )
        stmt = stmt.where(clause)
        stmt = stmt.limit(1)
        resp = await conn.execute(stmt)
        for row in resp.fetchall():
            page = cls.parse_obj(row)
            page.retrieved = True
            return page
        return None

    @classmethod
    async def iter_parse(cls, conn: Conn) -> AsyncGenerator["Page", None]:
        stmt = select(page_table)
        stmt = stmt.where(page_table.c.parse == True)
        result = await conn.stream(stmt)
        async for row in result:
            page = cls.parse_obj(row)
            page.retrieved = True
            yield page

    async def save(self, conn: Conn) -> None:
        data = self.dict(exclude={"retrieved", "doc", "url", "original_url", "text"})
        data["url"] = self.url.url
        data["original_url"] = self.original_url.url
        istmt = upsert(page_table).values([data])
        values = dict(
            ok=istmt.excluded.ok,
            parse=istmt.excluded.ok,
            status=istmt.excluded.status,
            content_type=istmt.excluded.content_type,
            charset=istmt.excluded.charset,
            content=istmt.excluded.content,
            timestamp=istmt.excluded.timestamp,
        )
        stmt = istmt.on_conflict_do_update(index_elements=["url"], set_=values)
        await conn.execute(stmt)

    async def update_parse(self, conn: Conn) -> None:
        stmt = update(page_table)
        stmt = stmt.where(page_table.c.url == self.url.url)
        stmt = stmt.values({"parse": self.parse})
        await conn.execute(stmt)
