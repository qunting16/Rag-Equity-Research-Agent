"""Morning brief agent for daily A-share investment report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.tools.china_multi_source_news_tool import ChinaMultiSourceNewsTool


class MorningBriefAgent:
    def __init__(self) -> None:
        self.news_tool = ChinaMultiSourceNewsTool()

    def generate(self, limit: int = 120) -> dict[str, Any]:
        articles = self.news_tool.get_global_news(limit=limit)
        today = datetime.now().strftime("%Y-%m-%d")

        sections: dict[str, list[dict[str, Any]]] = {
            "watchlist": [],
            "us_market": [],
            "macro": [],
            "affected_sectors": [],
            "company_news": [],
            "risks": [],
        }

        for article in articles:
            if self._is_noise(article):
                continue

            if not self._is_relevant(article):
                continue

            item = article.to_dict()

            if self._is_market_watch(article):
                sections["watchlist"].append(item)
            elif self._is_us_market(article):
                sections["us_market"].append(item)
            elif self._is_macro(article):
                sections["macro"].append(item)
            elif self._is_market_risk(article):
                sections["risks"].append(item)
            elif self._is_company_news(article):
                sections["company_news"].append(item)
            elif self._is_sector_related(article):
                sections["affected_sectors"].append(item)

        markdown = self._render_markdown(today, sections)

        return {
            "date": today,
            "report_type": "morning_brief",
            "sections": sections,
            "markdown": markdown,
        }

    def _text(self, article: Any) -> str:
        return f"{article.title} {article.summary or ''}"

    def _has_any(self, article: Any, keywords: list[str]) -> bool:
        text = self._text(article)
        return any(keyword in text for keyword in keywords)

    def _is_noise(self, article: Any) -> bool:
        return self._has_any(article, [
            "汉坦病毒",
            "涉疫邮轮",
            "洗钱团伙",
            "总统办公室前主任",
            "极端定居者",
            "乌克兰特别反腐败",
            "地方腐败",
            "伊朗议长",
            "委内瑞拉",
            "欧洲应考虑直接同俄罗斯对话",
        ])

    def _is_relevant(self, article: Any) -> bool:
        return self._has_any(article, [
            "A股", "港股", "沪深", "上证", "深成指",
            "创业板", "科创板", "北交所",
            "富时A50", "恒生", "中概股",

            "人民币", "美元", "美联储", "央行",
            "利率", "降息", "加息",
            "通胀", "CPI", "PPI", "GDP", "PMI",
            "汇率", "美债", "原油", "黄金",

            "AI", "人工智能",
            "半导体", "芯片", "存储芯片",
            "新能源", "光伏", "锂电",
            "机器人", "算力",
            "消费", "白酒",
            "医药", "创新药",
            "银行", "券商",
            "地产", "汽车", "电动车",

            "美股", "标普", "纳指", "道指", "纳斯达克",
            "英伟达", "苹果", "微软", "特斯拉",
            "OpenAI", "Amazon", "Google", "Meta",
            "AMD", "NVIDIA",

            "财报", "业绩", "营收", "利润",
            "净利润", "回购", "分红",
            "减持", "增持",
            "并购", "重组",
            "中标", "合同",
            "上市", "收购",
            "裁员",

            "制裁",
            "出口限制",
            "关税",
            "违约",
            "流动性",
            "地产风险",
            "债务风险",
            "芯片禁令",
            "监管政策",
        ])

    def _is_market_watch(self, article: Any) -> bool:
        return self._has_any(article, [
            "富时A50",
            "A50",
            "人民币",
            "离岸人民币",
            "恒生指数",
            "恒生",
            "原油",
            "黄金",
            "期银",
            "WTI",
            "布伦特",
        ])

    def _is_us_market(self, article: Any) -> bool:
        return self._has_any(article, [
            "美股",
            "标普",
            "纳指",
            "道指",
            "纳斯达克",
            "中概股",
            "英伟达",
            "苹果",
            "微软",
            "特斯拉",
            "OpenAI",
            "Amazon",
            "Google",
            "Meta",
            "AMD",
            "NVIDIA",
        ])

    def _is_macro(self, article: Any) -> bool:
        return self._has_any(article, [
            "央行",
            "利率",
            "降息",
            "加息",
            "通胀",
            "GDP",
            "PMI",
            "人民币",
            "美元",
            "原油",
            "黄金",
            "美联储",
            "CPI",
            "PPI",
            "美债",
        ])

    def _is_market_risk(self, article: Any) -> bool:
        return self._has_any(article, [
            "制裁",
            "出口限制",
            "关税",
            "违约",
            "流动性",
            "地产风险",
            "债务风险",
            "芯片禁令",
            "监管政策",
            "暴跌",
            "下调",
        ])

    def _is_company_news(self, article: Any) -> bool:
        return self._has_any(article, [
            "公司",
            "财报",
            "业绩",
            "利润",
            "净利润",
            "营收",
            "回购",
            "分红",
            "减持",
            "增持",
            "并购",
            "重组",
            "中标",
            "合同",
            "上市",
            "收购",
            "裁员",
        ])

    def _is_sector_related(self, article: Any) -> bool:
        return self._has_any(article, [
            "AI",
            "人工智能",
            "半导体",
            "芯片",
            "存储芯片",
            "新能源",
            "光伏",
            "锂电",
            "机器人",
            "算力",
            "汽车",
            "电动车",
            "消费",
            "白酒",
            "地产",
            "银行",
            "券商",
            "医药",
            "创新药",
        ])

    def _render_markdown(
        self,
        today: str,
        sections: dict[str, list[dict[str, Any]]],
    ) -> str:
        lines = [
            f"# A股投资早报 - {today}",
            "",

            "## 1. 今日开盘前观察",
            *self._render_items(sections["watchlist"]),
            "",

            "## 2. 昨夜美股重点",
            *self._render_items(sections["us_market"]),
            "",

            "## 3. 宏观与大宗商品",
            *self._render_items(sections["macro"]),
            "",

            "## 4. A股/港股可能受影响板块",
            *self._render_items(sections["affected_sectors"]),
            "",

            "## 5. 重要公司新闻",
            *self._render_items(sections["company_news"]),
            "",

            "## 6. 风险提示",
            *self._render_items(sections["risks"]),
            "",
        ]

        return "\n".join(lines)

    def _render_items(
        self,
        items: list[dict[str, Any]],
        limit: int = 8,
    ) -> list[str]:
        if not items:
            return ["- 暂无可靠数据"]

        lines: list[str] = []
        seen_titles: set[str] = set()

        for item in items:
            title = item.get("title") or ""
            normalized_title = self._normalize_title(title)

            if normalized_title in seen_titles:
                continue

            seen_titles.add(normalized_title)

            time = item.get("published_at") or "未知时间"
            platform = item.get("platform") or "未知来源"
            event_type = item.get("event_type") or "general"

            lines.append(f"- [{time}] [{platform}] [{event_type}] {title}")

            if len(lines) >= limit:
                break

        if not lines:
            return ["- 暂无可靠数据"]

        return lines

    def _normalize_title(self, title: str) -> str:
        title = title.strip()

        noise_tokens = [
            "【", "】", "财联社", "日电", "讯",
            "：", ":", "，", ",", "。", ".",
            " ", "\n", "\t",
        ]

        for token in noise_tokens:
            title = title.replace(token, "")

        return title[:45]
