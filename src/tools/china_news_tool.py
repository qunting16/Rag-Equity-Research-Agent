"""Chinese financial news aggregation tool for A-share stocks."""

from dataclasses import dataclass
from typing import Any

import akshare as ak

from src.tools.investment_memory import InvestmentMemory


@dataclass
class ChinaNewsArticle:
    title: str
    content: str | None = None
    url: str | None = None
    source: str | None = None
    published_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "summary": self.content,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
        }


class ChinaNewsTool:
    """Aggregate Chinese financial news from multiple sources."""

    def __init__(self) -> None:
        self._memory = InvestmentMemory()

    def get_stock_news(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[ChinaNewsArticle]:
        articles: list[ChinaNewsArticle] = []

        articles.extend(self._fetch_eastmoney_stock_news(ticker))

        articles = self._dedupe(articles)

        fresh_articles: list[ChinaNewsArticle] = []
        for article in articles:
            if not self._memory.is_news_seen(article.title, article.url):
                fresh_articles.append(article)

        fresh_articles = fresh_articles[:limit]

        for article in fresh_articles:
            self._memory.mark_news_seen(ticker, article.to_dict())

        return fresh_articles

    def _fetch_eastmoney_stock_news(
        self,
        ticker: str,
    ) -> list[ChinaNewsArticle]:
        try:
            df = ak.stock_news_em(symbol=ticker)
        except Exception:
            return []

        articles: list[ChinaNewsArticle] = []

        for _, row in df.iterrows():
            data = row.to_dict()

            title = self._pick(data, ["新闻标题", "标题", "title"])
            if not title:
                continue

            article = ChinaNewsArticle(
                title=str(title),
                content=self._pick(data, ["新闻内容", "内容", "summary"]),
                url=self._pick(data, ["新闻链接", "链接", "url"]),
                source=self._pick(data, ["文章来源", "来源", "source"]),
                published_at=self._pick(data, ["发布时间", "时间", "date"]),
            )
            articles.append(article)

        return articles

    def _pick(self, data: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            value = data.get(key)
            if value is not None and str(value).strip():
                return value
        return None

    def _dedupe(
        self,
        articles: list[ChinaNewsArticle],
    ) -> list[ChinaNewsArticle]:
        seen: set[str] = set()
        result: list[ChinaNewsArticle] = []

        for article in articles:
            key = article.url or article.title

            if not key:
                continue

            key = key.strip()

            if key in seen:
                continue

            seen.add(key)
            result.append(article)

        return result
