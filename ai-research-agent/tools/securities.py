import pandas as pd
import yfinance as yf

US_EXCHANGES = ["NMS", "NYQ", "ASE"]
MIN_MARKET_CAP = 2_000_000_000  # filters out illiquid / micro-cap noise


def screen_securities(
    asset_type: str,
    sector: str | None = None,
    max_pe: float | None = None,
    min_dividend_yield: float | None = None,
    max_expense_ratio: float | None = None,
    min_historical_growth: float | None = None,
    limit: int = 5,
) -> list[dict]:
    """Screen stocks or ETFs by P/E ratio, dividend yield, expense ratio, and
    historical growth, using Yahoo Finance (via yfinance) - no API key required.

    `asset_type` selects between individual stocks and ETFs/funds. `max_expense_ratio`
    only applies to (and is only fetched for) ETFs, since individual stocks don't
    have an expense ratio. `min_historical_growth` means trailing 5-year average
    annual return for ETFs, and the most recent earnings (or revenue) growth rate
    for stocks.
    """
    if asset_type not in ("stock", "etf"):
        raise ValueError("asset_type must be 'stock' or 'etf'")

    limit = max(1, min(limit, 10))
    candidate_pool = min(limit * 3, 15)

    candidates = _find_candidates(asset_type, sector, max_pe, max_expense_ratio, candidate_pool)

    results = []
    for symbol in candidates:
        try:
            info = yf.Ticker(symbol).info
        except Exception:
            continue

        pe_ratio = info.get("trailingPE")
        if max_pe is not None and (pe_ratio is None or pe_ratio > max_pe):
            continue

        dividend_yield_pct = info.get("dividendYield")
        if min_dividend_yield is not None and (
            dividend_yield_pct is None or dividend_yield_pct < min_dividend_yield
        ):
            continue

        expense_ratio_pct = None
        if asset_type == "etf":
            expense_ratio_pct = info.get("netExpenseRatio")
            if max_expense_ratio is not None and (
                expense_ratio_pct is None or expense_ratio_pct > max_expense_ratio
            ):
                continue

        growth_pct = _historical_growth_pct(asset_type, info)
        if min_historical_growth is not None and (
            growth_pct is None or growth_pct < min_historical_growth
        ):
            continue

        results.append(
            {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "price": info.get("regularMarketPrice") or info.get("navPrice"),
                "pe_ratio": pe_ratio,
                "dividend_yield_pct": dividend_yield_pct,
                "expense_ratio_pct": expense_ratio_pct,
                "historical_growth_pct": growth_pct,
            }
        )

        if len(results) >= limit:
            break

    return results


def compare_securities(symbols: list[str]) -> list[dict]:
    """Fetch expense ratio, dividend yield, and historical price performance
    (1/3/5-year total returns) for a list of stock or ETF symbols, for
    side-by-side comparison. Uses live Yahoo Finance data (via yfinance) -
    no API key required.
    """
    results = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
        except Exception as exc:
            results.append({"symbol": symbol, "error": str(exc)})
            continue

        results.append(
            {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "price": info.get("regularMarketPrice") or info.get("navPrice"),
                "expense_ratio_pct": info.get("netExpenseRatio"),
                "dividend_yield_pct": info.get("dividendYield"),
                "historical_performance_pct": _historical_performance_pct(ticker),
            }
        )

    return results


def calculate_returns(
    symbols: list[str],
    investment: float,
    years: list[int] | None = None,
) -> list[dict]:
    """Calculate what a fixed investment would be worth today if made 1, 3, 5
    (or any set of) years ago, for each symbol. Uses live Yahoo Finance price
    history (adjusted closes = total return including dividends).

    Returns one entry per symbol with a breakdown per time period showing
    total return %, gain/loss in dollars, and ending portfolio value.
    """
    if years is None:
        years = [1, 3, 5]
    max_years = max(years)
    results = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=f"{max_years + 1}y")
            info = ticker.info
        except Exception as exc:
            results.append({"symbol": symbol, "error": str(exc)})
            continue

        closes = history["Close"] if not history.empty else None
        if closes is None or len(closes) < 2:
            results.append({"symbol": symbol, "error": "No price history available"})
            continue

        latest_date = closes.index[-1]
        latest_price = closes.iloc[-1]
        earliest_date = closes.index[0]
        earliest_price = closes.iloc[0]

        periods = {}
        for y in sorted(years):
            cutoff = latest_date - pd.DateOffset(years=y)
            past_prices = closes[closes.index <= cutoff]

            if not past_prices.empty:
                past_price = past_prices.iloc[-1]
            elif (cutoff - earliest_date) <= pd.Timedelta(days=10):
                past_price = earliest_price
            else:
                periods[f"{y}y"] = None
                continue

            if past_price > 0:
                total_return_pct = round((latest_price / past_price - 1) * 100, 2)
                gain_loss = round(investment * total_return_pct / 100, 2)
                periods[f"{y}y"] = {
                    "total_return_pct": total_return_pct,
                    "gain_loss": gain_loss,
                    "end_value": round(investment + gain_loss, 2),
                }

        results.append(
            {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "investment": investment,
                "periods": periods,
            }
        )

    return results


def _historical_performance_pct(ticker: "yf.Ticker") -> dict:
    """Total price return (%) over the trailing 1, 3, and 5 years."""
    history = ticker.history(period="5y")
    closes = history["Close"] if not history.empty else None
    if closes is None or len(closes) < 2:
        return {}

    latest_date, latest_price = closes.index[-1], closes.iloc[-1]
    earliest_date, earliest_price = closes.index[0], closes.iloc[0]
    performance = {}
    for label, years in (("1y", 1), ("3y", 3), ("5y", 5)):
        cutoff = latest_date - pd.DateOffset(years=years)
        past_prices = closes[closes.index <= cutoff]
        if not past_prices.empty:
            past_price = past_prices.iloc[-1]
        elif (cutoff - earliest_date) <= pd.Timedelta(days=10):
            # "5y" of data is often a few days short of a full 5 years - close enough
            past_price = earliest_price
        else:
            continue
        if past_price > 0:
            performance[label] = round((latest_price / past_price - 1) * 100, 2)
    return performance


def _historical_growth_pct(asset_type: str, info: dict) -> float | None:
    if asset_type == "etf":
        value = info.get("fiveYearAverageReturn")
    else:
        value = info.get("earningsGrowth") or info.get("revenueGrowth")
    return round(value * 100, 2) if value is not None else None


def _find_candidates(asset_type, sector, max_pe, max_expense_ratio, count) -> list[str]:
    if asset_type == "stock":
        conditions = [
            yf.EquityQuery("is-in", ["exchange", *US_EXCHANGES]),
            yf.EquityQuery("gt", ["intradaymarketcap", MIN_MARKET_CAP]),
        ]
        if sector:
            conditions.append(yf.EquityQuery("eq", ["sector", sector]))
        if max_pe is not None:
            conditions.append(yf.EquityQuery("lt", ["peratio.lasttwelvemonths", max_pe]))
        query = yf.EquityQuery("and", conditions)
    else:
        conditions = [yf.ETFQuery("eq", ["region", "us"])]
        if max_expense_ratio is not None:
            # yfinance's screener expresses this field as a fraction (0.002 == 0.2%),
            # while per-ticker .info reports it as a percentage (0.0945 == 0.0945%).
            conditions.append(yf.ETFQuery("lt", ["annualreportnetexpenseratio", max_expense_ratio / 100]))
        query = conditions[0] if len(conditions) == 1 else yf.ETFQuery("and", conditions)

    result = yf.screen(query, size=count, sortField="eodvolume", sortAsc=False)
    return [item["symbol"] for item in result.get("quotes", [])]
