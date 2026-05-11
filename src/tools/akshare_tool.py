"""AkShare tool for China A-share market data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import akshare as ak


@dataclass
class AShareQuote:
    symbol: str
    name: str
    price: float
    change_percent: float
    change_amount: float
    volume: float
    turnover: float
    high: float
    low: float
    open: float
    previous_close: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AShareFinancials:
    symbol: str
    revenue: float | None
    net_income: float | None
    return_on_equity: float | None
    gross_margin: float | None
    debt_to_asset_ratio: float | None
    market_cap: float | None
    industry: str | None
    pe_ratio: float | None = None
    pb_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class AkShareTool:
    def _pure_symbol(self, symbol: str) -> str:
        return symbol.lower().replace("sh", "").replace("sz", "").replace("bj", "")

    def _safe_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except Exception:
            return None

    def get_quote(self, symbol: str) -> AShareQuote | None:
        df = ak.stock_zh_a_spot()
        pure = self._pure_symbol(symbol)
        row = df[
            (df["代码"].astype(str) == symbol.lower()) | (df["代码"].astype(str) == pure)
        ].head(1)

        if row.empty:
            return None

        r = row.iloc[0]

        return AShareQuote(
            symbol=symbol,
            name=str(r["名称"]),
            price=self._safe_float(r["最新价"]) or 0,
            change_percent=self._safe_float(r["涨跌幅"]) or 0,
            change_amount=self._safe_float(r["涨跌额"]) or 0,
            volume=self._safe_float(r["成交量"]) or 0,
            turnover=self._safe_float(r["成交额"]) or 0,
            high=self._safe_float(r["最高"]) or 0,
            low=self._safe_float(r["最低"]) or 0,
            open=self._safe_float(r["今开"]) or 0,
            previous_close=self._safe_float(r["昨收"]) or 0,
            timestamp=datetime.now(),
        )

    def get_financials(self, symbol: str) -> AShareFinancials | None:
        pure = self._pure_symbol(symbol)

        info = {}
        fin_df = ak.stock_financial_abstract(symbol=pure)

        date_cols = [c for c in fin_df.columns if str(c).isdigit()]
        latest_col = date_cols[0] if date_cols else None

        def metric(name: str) -> float | None:
            if latest_col is None:
                return None
            row = fin_df[fin_df["指标"] == name]
            if row.empty:
                return None
            return self._safe_float(row.iloc[0][latest_col])

        return AShareFinancials(
            symbol=symbol,
            revenue=metric("营业总收入"),
            net_income=metric("归母净利润"),
            return_on_equity=metric("净资产收益率(ROE)"),
            gross_margin=metric("毛利率"),
            debt_to_asset_ratio=metric("资产负债率"),
            market_cap=self._safe_float(info.get("总市值")),
            industry=str(info.get("行业")) if info.get("行业") else None,
        )
