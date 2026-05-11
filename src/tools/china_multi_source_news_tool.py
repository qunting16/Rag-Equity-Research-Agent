"""Free Chinese financial news sources via AkShare."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import akshare as ak


@dataclass
class NewsArticle:
    title: str
    url: str | None = None
    source: str | None = None
    platform: str | None = None
    published_at: str | None = None
    summary: str | None = None
    event_type: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "platform": self.platform,
            "published_at": self.published_at,
            "summary": self.summary,
            "event_type": self.event_type,
        }


class ChinaMultiSourceNewsTool:
    def get_global_news(self, limit: int = 50) -> list[NewsArticle]:
        articles: list[NewsArticle] = []

        articles.extend(self._fetch_sina())
        articles.extend(self._fetch_cls())
        articles.extend(self._fetch_ths())

        articles = self._dedupe(articles)
        articles = self._classify_events(articles)
        articles = self._sort_by_time_desc(articles)

        return articles[:limit]

    def _fetch_sina(self) -> list[NewsArticle]:
        try:
            df = ak.stock_info_global_sina()
        except Exception:
            return []

        articles: list[NewsArticle] = []

        for _, row in df.iterrows():
            data = row.to_dict()
            content = data.get("内容")

            if not content:
                continue

            articles.append(
                NewsArticle(
                    title=str(content).strip(),
                    summary=str(content).strip(),
                    platform="新浪财经",
                    source="新浪财经",
                    published_at=str(data.get("时间")) if data.get("时间") else None,
                )
            )

        return articles

    def _fetch_cls(self) -> list[NewsArticle]:
        try:
            df = ak.stock_info_global_cls()
        except Exception:
            return []

        articles: list[NewsArticle] = []

        for _, row in df.iterrows():
            data = row.to_dict()
            title = data.get("标题")
            content = data.get("内容")

            if not title:
                continue

            published_at = None
            if data.get("发布日期") and data.get("发布时间"):
                published_at = f"{data.get('发布日期')} {data.get('发布时间')}"
            elif data.get("发布时间"):
                published_at = str(data.get("发布时间"))

            articles.append(
                NewsArticle(
                    title=str(title).strip(),
                    summary=str(content).strip() if content else None,
                    platform="财联社",
                    source="财联社",
                    published_at=published_at,
                )
            )

        return articles

    def _fetch_ths(self) -> list[NewsArticle]:
        try:
            df = ak.stock_info_global_ths()
        except Exception:
            return []

        articles: list[NewsArticle] = []

        for _, row in df.iterrows():
            data = row.to_dict()
            title = data.get("标题")
            content = data.get("内容")

            if not title:
                continue

            articles.append(
                NewsArticle(
                    title=str(title).strip(),
                    summary=str(content).strip() if content else None,
                    url=str(data.get("链接")) if data.get("链接") else None,
                    platform="同花顺",
                    source="同花顺",
                    published_at=str(data.get("发布时间")) if data.get("发布时间") else None,
                )
            )

        return articles

    def _dedupe(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        seen: set[str] = set()
        result: list[NewsArticle] = []

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

    def _classify_events(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        for article in articles:
            article.event_type = self._detect_event_type(article)

        return articles

    def _detect_event_type(self, article: NewsArticle) -> str:
        text = f"{article.title} {article.summary or ''}"

        event_keywords = {
            "earnings": ["财报", "业绩", "营收", "利润", "净利润", "亏损", "预增", "预亏"],
            "shareholder_return": ["回购", "分红", "派息", "股息"],
            "shareholder_change": ["减持", "增持", "质押", "解禁"],
            "regulatory": ["监管", "处罚", "调查", "立案", "问询函", "警示函"],
            "capital_market": ["定增", "配股", "融资", "发债", "可转债"],
            "corporate_action": ["并购", "重组", "收购", "资产出售", "停牌", "复牌"],
            "contract": ["合同", "中标", "订单", "合作协议"],
            "price": ["涨价", "降价", "提价"],
            "macro": ["央行", "利率", "通胀", "GDP", "汇率", "原油", "美联储"],
        }

        for event_type, keywords in event_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return event_type

        return "general"

    def _sort_by_time_desc(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        return sorted(
            articles,
            key=lambda article: self._parse_time(article.published_at),
            reverse=True,
        )

    def _parse_time(self, value: str | None) -> datetime:
        if not value:
            return datetime.min

        value = str(value).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        return datetime.min
