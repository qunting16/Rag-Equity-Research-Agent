"""Market Data Agent for fetching real-time financial data."""

from dataclasses import dataclass
from typing import Any

import structlog

from src.tools import YFinanceTool
from src.tools.akshare_tool import AkShareTool

logger = structlog.get_logger()


@dataclass
class MarketDataResult:
    """Result from market data agent."""

    quotes: dict[str, Any]
    financials: dict[str, Any]
    pe_comparison: dict[str, float | None]
    market_summary: str
    errors: list[str]


class MarketDataAgent:
    """Agent for fetching and analyzing market data.

    Responsibilities:
    - Fetch real-time stock quotes
    - Get financial metrics
    - Compare P/E ratios across stocks
    - Handle API errors gracefully
    """

    def __init__(self) -> None:
        """Initialize market data agent."""
        self._yfinance = YFinanceTool()
        self._akshare = AkShareTool()

    def _is_a_share(self, ticker: str) -> bool:
        """Detect China A-share symbols."""
        t = ticker.lower()
        return (
            t.startswith("sh")
            or t.startswith("sz")
            or t.startswith("bj")
            or (len(t) == 6 and t.isdigit())
        )

    def _normalize_a_share_symbol(self, ticker: str) -> str:
        """Normalize A-share symbol for AkShare Sina source."""
        t = ticker.lower()
        if t.startswith(("sh", "sz", "bj")):
            return t
        if t.startswith("6"):
            return "sh" + t
        if t.startswith(("0", "3")):
            return "sz" + t
        if t.startswith(("8", "4", "9")):
            return "bj" + t
        return t

    def _format_price(self, price: float | None, currency: str = "$") -> str:
        """Format price for display."""
        if price is None:
            return "N/A"
        return f"{currency}{price:,.2f}"

    def _format_large_number(self, num: float | None) -> str:
        """Format large numbers (billions, millions)."""
        if num is None:
            return "N/A"
        if num >= 1e12:
            return f"${num / 1e12:.2f}T"
        if num >= 1e9:
            return f"${num / 1e9:.2f}B"
        if num >= 1e6:
            return f"${num / 1e6:.2f}M"
        return f"${num:,.0f}"

    def _format_percent(self, pct: float | None) -> str:
        """Format percentage."""
        if pct is None:
            return "N/A"
        return f"{pct * 100:.2f}%" if abs(pct) < 1 else f"{pct:.2f}%"

    def analyze(self, tickers: list[str]) -> MarketDataResult:
        """Analyze market data for given tickers.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            MarketDataResult with all gathered data
        """
        quotes = {}
        financials = {}
        errors = []

        for ticker in tickers:
            ticker = ticker.upper()

            # Get quote
            try:
                if self._is_a_share(ticker):
                    a_symbol = self._normalize_a_share_symbol(ticker)
                    quote = self._akshare.get_quote(a_symbol)
                    if quote:
                        quotes[ticker] = quote.to_dict()
                        quotes[ticker]["market"] = "China A-share"
                    else:
                        errors.append(f"No A-share quote data for {ticker}")
                else:
                    quote = self._yfinance.get_quote(ticker)
                    if quote:
                        quotes[ticker] = quote.to_dict()
                        quotes[ticker]["market"] = "US"
                    else:
                        errors.append(f"No quote data for {ticker}")
            except Exception as e:
                errors.append(f"Error fetching quote for {ticker}: {str(e)}")
                logger.error("quote_fetch_error", ticker=ticker, error=str(e))

            # Get financials
            try:
                if self._is_a_share(ticker):
                    a_symbol = self._normalize_a_share_symbol(ticker)
                    metrics = self._akshare.get_financials(a_symbol)
                    if metrics:
                        financials[ticker] = metrics.to_dict()
                else:
                    metrics = self._yfinance.get_financials(ticker)
                    if metrics:
                        financials[ticker] = metrics.to_dict()
            except Exception as e:
                errors.append(f"Error fetching financials for {ticker}: {str(e)}")
                logger.error("financials_fetch_error", ticker=ticker, error=str(e))

        # Compare P/E ratios
        pe_comparison = {ticker: quotes.get(ticker, {}).get("pe_ratio") for ticker in tickers}

        # Generate market summary
        summary = self._generate_summary(quotes, financials, pe_comparison)

        logger.info(
            "market_data_analyzed",
            tickers=tickers,
            quotes_count=len(quotes),
            errors_count=len(errors),
        )

        return MarketDataResult(
            quotes=quotes,
            financials=financials,
            pe_comparison=pe_comparison,
            market_summary=summary,
            errors=errors,
        )

    def _generate_summary(
        self,
        quotes: dict[str, Any],
        financials: dict[str, Any],
        pe_comparison: dict[str, float | None],
    ) -> str:
        """Generate a summary of market data."""
        if not quotes:
            return "No market data available."

        lines = ["## Market Data Summary\n"]

        for ticker, quote in quotes.items():
            currency = "¥" if quote.get("market") == "China A-share" else "$"
            price = self._format_price(quote.get("price"), currency=currency)
            change_pct = quote.get("change_percent", 0)
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
            market_cap = self._format_large_number(quote.get("market_cap"))
            pe = quote.get("pe_ratio")
            pe_str = f"{pe:.2f}" if pe else "N/A"

            lines.append(f"### {ticker} ({quote.get('name', ticker)})")
            lines.append(f"- **Price**: {price} ({change_str})")
            lines.append(f"- **Market**: {quote.get('market', 'Unknown')}")
            lines.append(f"- **Market Cap**: {market_cap}")
            lines.append(f"- **P/E Ratio**: {pe_str}")
            lines.append(f"- **Market State**: {quote.get('market_state', 'Unknown')}")

            # Add financial metrics if available
            if ticker in financials:
                fin = financials[ticker]
                lines.append(
                    f"- **Revenue**: {self._format_large_number(fin.get('revenue')).replace('$', '¥') if quote.get('market') == 'China A-share' else self._format_large_number(fin.get('revenue'))}"
                )
                lines.append(
                    f"- **Net Income**: {self._format_large_number(fin.get('net_income')).replace('$', '¥') if quote.get('market') == 'China A-share' else self._format_large_number(fin.get('net_income'))}"
                )
                lines.append(
                    f"- **Profit Margin**: {self._format_percent(fin.get('profit_margin'))}"
                )

            lines.append("")

        # P/E Comparison
        if len(pe_comparison) > 1:
            lines.append("### P/E Ratio Comparison")
            sorted_pe = sorted(
                [(t, p) for t, p in pe_comparison.items() if p is not None],
                key=lambda x: x[1],
            )
            for ticker, pe in sorted_pe:
                lines.append(f"- **{ticker}**: {pe:.2f}")

        return "\n".join(lines)


def run_market_data_node(state: dict) -> dict:
    """LangGraph node function for market data agent.

    Args:
        state: Current graph state

    Returns:
        Updated state with market data
    """
    tickers = state.get("tickers", [])

    if not tickers:
        return {
            "market_data": None,
            "errors": state.get("errors", []) + ["No tickers provided"],
        }

    agent = MarketDataAgent()
    result = agent.analyze(tickers)

    return {
        "market_data": {
            "quotes": result.quotes,
            "financials": result.financials,
            "pe_comparison": result.pe_comparison,
            "summary": result.market_summary,
        },
        "errors": state.get("errors", []) + result.errors,
    }
