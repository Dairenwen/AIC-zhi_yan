"""Scrape public server-rendered paper data from arXivDaily."""

from __future__ import annotations

import json
import time

import httpx
from bs4 import BeautifulSoup
from langchain_core.runnables import RunnableLambda

from config.constants import CS_MAJOR, SOURCE_URL, USER_AGENT
from src.schemas.paper import Category, Paper


class ArxivDailyScraper:
    """Small, rate-conscious scraper for the source's public HTML."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7"},
        )
        self.normalizer = RunnableLambda(self._to_paper)

    def close(self) -> None:
        self.client.close()

    def fetch_categories(self) -> list[Category]:
        soup = self._get_soup({"major": CS_MAJOR})
        major_input = soup.select_one('input[name="category"][value="major:CS"]')
        if not major_input:
            raise RuntimeError("源站 CS 分类选择器结构已变化")
        group = major_input.find_parent("div", class_="category-picker-group")
        categories: list[Category] = []
        for item in group.select("label.category-choice-sub"):
            code = item.select_one(".choice-code")
            name = item.select_one(".choice-name")
            if code and name:
                categories.append(Category(code.get_text(strip=True), name.get_text(strip=True)))
        if len(categories) != 41:
            raise RuntimeError(f"预期 41 个 CS 分类，实际抓取到 {len(categories)} 个")
        return categories

    def fetch_papers(self, category: str) -> list[Paper]:
        """Fetch the newest batch published by arXivDaily for one CS category.

        arXivDaily publishes according to its own release schedule and timezone.  A
        local-calendar date filter can therefore point at an unpublished day and
        produce an empty result even when the source has a complete newest batch.
        Omitting that filter deliberately follows the source site's latest view.
        """
        params = {"category": f"subcat:{category}"}
        soup = self._get_soup(params)
        papers: list[Paper] = []
        for card in soup.select("article.paper-card"):
            data_node = card.select_one("script[data-paper-share-json]")
            if not data_node or not data_node.string:
                continue
            try:
                source = json.loads(data_node.string)
                source = self._enrich_card_payload(card, source)
                papers.append(self.normalizer.invoke(source))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return papers

    @staticmethod
    def _enrich_card_payload(card, source: dict) -> dict:
        """Merge complete details rendered in the source card into its share payload.

        arXivDaily's compact JSON is designed for sharing, so it deliberately
        omits the PDF URL and both abstracts.  They are already server-rendered
        in the same card, which makes parsing them both faster and more reliable
        than issuing a second request per paper.
        """
        payload = dict(source)

        pdf_link = card.select_one("a.pdf-button[href]")
        if pdf_link and pdf_link.get("href"):
            payload["pdf_url"] = pdf_link["href"].strip()

        chinese_abstract = card.select_one(".detail-abstract-cn p")
        if chinese_abstract:
            payload["abstract_cn"] = chinese_abstract.get_text(" ", strip=True)

        english_abstract = next(
            (
                item.select_one("p").get_text(" ", strip=True)
                for item in card.select(".detail-abstract")
                if "detail-abstract-cn" not in (item.get("class") or []) and item.select_one("p")
            ),
            "",
        )
        if english_abstract:
            payload["abstract"] = english_abstract
        return payload

    def _get_soup(self, params: dict[str, str]) -> BeautifulSoup:
        for attempt in range(3):
            response = self.client.get(SOURCE_URL, params=params)
            if response.status_code != 429:
                response.raise_for_status()
                return BeautifulSoup(response.text, "html.parser")
            if attempt == 2:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After", "30")
            try:
                delay = max(1.0, min(float(retry_after), 120.0))
            except ValueError:
                delay = 30.0
            time.sleep(delay)
        raise RuntimeError("unreachable")

    @staticmethod
    def _to_paper(source: dict) -> Paper:
        affiliations = source.get("affiliations") or []
        if isinstance(affiliations, str):
            affiliations = [affiliations]
        normalized_affiliations: list[str] = []
        for affiliation in affiliations:
            if isinstance(affiliation, dict):
                english = str(affiliation.get("en", "")).strip()
                chinese = str(affiliation.get("zh", "")).strip()
                normalized_affiliations.append(f"{english}（{chinese}）" if english and chinese else english or chinese)
            else:
                normalized_affiliations.append(str(affiliation))
        return Paper(
            arxiv_id=str(source.get("arxiv_id", "")),
            title=str(source.get("title", "")),
            title_cn=str(source.get("title_cn", "暂无中文翻译标题")),
            summary_cn=str(source.get("summary_cn", "暂无 AI 总结")),
            pdf_url=str(source.get("pdf_url", "")),
            authors=str(source.get("authors", "")),
            affiliations=normalized_affiliations,
            abstract_cn=str(source.get("abstract_cn", "暂无 AI 中文摘要")),
            abstract=str(source.get("abstract", "暂无英文摘要")),
            categories=[str(item) for item in source.get("categories", [])],
            updated=str(source.get("updated", "")),
            submission_label=str(source.get("submission_label", "")),
        )
