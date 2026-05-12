"""CNInfo / 巨潮资讯 announcement tool."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import akshare as ak


class CNInfoTool:
    """Fetch A-share disclosure announcements from CNInfo."""

    def get_recent_announcements(
        self,
        symbol: str = "",
        days: int = 3,
        category: str = "",
        keyword: str = "",
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        end = datetime.now()
        start = end - timedelta(days=days)

        df = ak.stock_zh_a_disclosure_report_cninfo(
            symbol=symbol,
            market="沪深京",
            category=category,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )

        items: list[dict[str, Any]] = []

        for _, row in df.iterrows():
            item = {str(k): v for k, v in row.to_dict().items()}

            title = str(
                item.get("公告标题")
                or item.get("标题")
                or item.get("announcementTitle")
                or ""
            )

            if keyword and keyword not in title:
                continue

            items.append(
                {
                    "title": title,
                    "code": item.get("代码") or item.get("证券代码") or item.get("secCode"),
                    "name": item.get("简称") or item.get("证券简称") or item.get("secName"),
                    "time": str(item.get("公告时间") or item.get("公告日期") or item.get("announcementTime")),
                    "url": item.get("公告链接") or item.get("adjunctUrl"),
                    "source": "巨潮资讯",
                    "category": category or "公告",
                }
            )

            if len(items) >= limit:
                break

        return items
