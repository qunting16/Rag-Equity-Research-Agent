from typing import Any

from src.tools.investment_memory import InvestmentMemory


class NewsImpactAgent:
    def __init__(self) -> None:
        self.memory = InvestmentMemory()

    def evaluate_news(
        self,
        ticker: str,
        article: dict[str, Any],
    ) -> dict[str, Any]:

        thesis_data = self.memory.get_stock_thesis(ticker)

        existing_thesis = None
        if thesis_data:
            existing_thesis = thesis_data.get("thesis")

        title = article.get("title", "")
        summary = article.get("summary", "")

        text = f"{title}\n{summary}"

        # very early heuristic version
        affects_thesis = False
        impact_level = "low"
        direction = "neutral"
        decision = "no_change"
        reason = "暂无可靠数据表明该新闻改变投资逻辑。"
        updated_thesis = None

        positive_keywords = [
            "增长",
            "新高",
            "突破",
            "扩产",
            "回购",
            "分红",
        ]

        negative_keywords = [
            "下滑",
            "处罚",
            "减持",
            "亏损",
            "暴跌",
            "调查",
        ]

        for kw in positive_keywords:
            if kw in text:
                affects_thesis = True
                impact_level = "medium"
                direction = "positive"
                decision = "review"
                reason = f"新闻包含正面关键词: {kw}"
                break

        for kw in negative_keywords:
            if kw in text:
                affects_thesis = True
                impact_level = "high"
                direction = "negative"
                decision = "review"
                reason = f"新闻包含负面关键词: {kw}"
                break

        result = {
            "ticker": ticker,
            "affects_thesis": affects_thesis,
            "impact_level": impact_level,
            "direction": direction,
            "decision": decision,
            "reason": reason,
            "existing_thesis": existing_thesis,
            "updated_thesis": updated_thesis,
        }
        news_id = self.memory.news_id(article.get("title"), article.get("url"))

        self.memory.log_decision(
            ticker=ticker,
            news_id=news_id,
            decision=decision,
            reason=reason,
            previous_thesis=existing_thesis,
            new_thesis=updated_thesis,
        )
        return result

