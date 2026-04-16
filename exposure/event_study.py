"""Event Study: Cumulative Abnormal Return (CAR) Analysis.

Measures market reaction around regulation publication dates using
the standard event study methodology:

  1. Estimation window: [-120, -11] trading days (estimate normal returns)
  2. Event window:      [-5, +5] trading days (measure actual returns)
  3. Abnormal return:   AR_t = R_t - E[R_t]  (actual minus expected)
  4. CAR:               Σ AR_t over the event window

IMPORTANT (Forbidden Language):
  - NEVER say: "impact", "caused", "drove", "resulted in"
  - USE: "around the time of", "associated with", "coincided with"
  - CAR is an OBSERVATION, not a causal claim.
  - We measure market reaction, not regulatory effect.

Data source: Yahoo Finance API (free, delayed)
  - No API key needed for daily OHLCV
  - 1-day delay for free tier

Usage:
    from exposure.event_study import EventStudyEngine, EventStudyResult

    engine = EventStudyEngine()

    # Single ETF event study
    result = engine.run(
        ticker="XLE",
        event_date=date(2026, 4, 10),
        event_name="EPA GHG Rule",
    )
    print(result.car)        # e.g., -0.0234 = -2.34% CAR
    print(result.t_stat)     # e.g., -2.15 (statistically significant)

    # Batch: regulation → all exposed ETFs
    results = engine.run_regulation_study(
        etf_tickers=["XLE", "XLU", "XOP"],
        event_date=date(2026, 4, 10),
        regulation_title="EPA GHG Emissions Rule",
    )
"""

from __future__ import annotations

import json
import logging
import math
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class DailyReturn:
    """Single day's return data."""
    trade_date: date
    close: float
    return_pct: float       # daily return (close-to-close)
    volume: int = 0


@dataclass
class EventStudyResult:
    """Result of an event study for one ticker."""
    ticker: str
    event_date: date
    event_name: str = ""

    # Returns
    car: float = 0.0                    # Cumulative Abnormal Return
    car_pre: float = 0.0                # CAR for pre-event window [-5, -1]
    car_post: float = 0.0               # CAR for post-event window [0, +5]
    abnormal_returns: list[tuple[int, float]] = field(default_factory=list)
    # Each tuple: (relative_day, AR)

    # Statistics
    t_stat: float = 0.0                 # t-statistic for CAR
    p_value: float = 1.0               # two-sided p-value
    is_significant: bool = False        # |t_stat| > 1.96

    # Model parameters
    alpha: float = 0.0                  # OLS intercept
    beta: float = 0.0                   # OLS slope (market sensitivity)
    beta_smb: float = 0.0              # FF3: size factor loading
    beta_hml: float = 0.0              # FF3: value factor loading
    r_squared: float = 0.0             # model fit
    estimation_std: float = 0.0         # residual std from estimation
    model_type: str = "market"          # "market" or "ff3"

    # Metadata
    estimation_days: int = 0
    event_window_days: int = 0
    benchmark: str = "SPY"
    data_source: str = "yahoo_finance"

    @property
    def car_pct(self) -> str:
        """CAR as formatted percentage string."""
        sign = "+" if self.car >= 0 else ""
        return f"{sign}{self.car*100:.2f}%"

    @property
    def significance_label(self) -> str:
        """Human-readable significance level."""
        abs_t = abs(self.t_stat)
        if abs_t >= 2.576:
            return "highly significant (p<0.01)"
        elif abs_t >= 1.96:
            return "significant (p<0.05)"
        elif abs_t >= 1.645:
            return "marginally significant (p<0.10)"
        return "not significant"

    def summary(self) -> str:
        """Generate a plain-language summary (forbidden language compliant).

        Uses "around the time of", "associated with" — never "caused", "drove".
        """
        direction = "positive" if self.car > 0 else "negative"
        abs_car = abs(self.car * 100)

        lines = [
            f"{self.ticker}: {self.car_pct} CAR around the time of {self.event_name}",
        ]

        if self.is_significant:
            lines.append(
                f"  A {direction} abnormal return of {abs_car:.2f}% was observed, "
                f"{self.significance_label} (t={self.t_stat:.2f})."
            )
        else:
            lines.append(
                f"  A {direction} abnormal return of {abs_car:.2f}% was observed, "
                f"but this was {self.significance_label} (t={self.t_stat:.2f})."
            )

        if abs(self.car_pre) > abs(self.car_post):
            lines.append(
                f"  Most of the movement occurred before the announcement "
                f"(pre: {self.car_pre*100:+.2f}%, post: {self.car_post*100:+.2f}%), "
                f"suggesting possible information leakage or anticipation."
            )
        elif abs(self.car_post) > 0.01:
            lines.append(
                f"  The movement was concentrated after the announcement "
                f"(pre: {self.car_pre*100:+.2f}%, post: {self.car_post*100:+.2f}%)."
            )

        return "\n".join(lines)


@dataclass
class RegulationStudyResult:
    """Aggregate event study results for a regulation across multiple ETFs."""
    regulation_title: str
    event_date: date
    etf_results: list[EventStudyResult]

    @property
    def avg_car(self) -> float:
        if not self.etf_results:
            return 0.0
        return sum(r.car for r in self.etf_results) / len(self.etf_results)

    @property
    def significant_count(self) -> int:
        return sum(1 for r in self.etf_results if r.is_significant)

    def generate_report(self) -> str:
        """Generate a markdown report for this regulation study."""
        lines = [
            f"## Event Study: {self.regulation_title}",
            f"**Event Date:** {self.event_date.isoformat()}",
            f"**ETFs Analyzed:** {len(self.etf_results)}",
            f"**Average CAR:** {self.avg_car*100:+.2f}%",
            f"**Significant Results:** {self.significant_count}/{len(self.etf_results)}",
            "",
            "| ETF | CAR | t-stat | Significance | Pre | Post |",
            "|-----|-----|--------|--------------|-----|------|",
        ]

        for r in sorted(self.etf_results, key=lambda x: abs(x.car), reverse=True):
            sig = "***" if abs(r.t_stat) >= 2.576 else ("**" if abs(r.t_stat) >= 1.96 else ("*" if abs(r.t_stat) >= 1.645 else ""))
            lines.append(
                f"| {r.ticker} | {r.car*100:+.2f}% | {r.t_stat:.2f}{sig} | "
                f"{r.significance_label} | {r.car_pre*100:+.2f}% | {r.car_post*100:+.2f}% |"
            )

        lines.extend([
            "",
            "*Note: CAR measures abnormal returns around the time of the regulatory announcement. "
            "This is an observation of market reaction and does not establish causation.*",
            "",
            "Significance: *** p<0.01, ** p<0.05, * p<0.10",
        ])

        return "\n".join(lines)


# ── Price Data Fetcher ────────────────────────────────────────────────

def fetch_yahoo_prices(
    ticker: str,
    start: date,
    end: date,
) -> list[DailyReturn]:
    """Fetch daily closing prices from Yahoo Finance.

    Returns list of DailyReturn objects, sorted by date ascending.
    Uses the free Yahoo Finance chart API (no key needed).
    """
    # Yahoo Finance v8 chart API
    period1 = int(datetime.combine(start, datetime.min.time()).timestamp())
    period2 = int(datetime.combine(end + timedelta(days=1), datetime.min.time()).timestamp())

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&includePrePost=false"
    )

    req = urllib.request.Request(url, headers={
        "User-Agent": "Legalize/0.1",
        "Accept": "application/json",
    })

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    result = data.get("chart", {}).get("result", [{}])[0]
    timestamps = result.get("timestamp", [])
    quotes = result.get("indicators", {}).get("quote", [{}])[0]
    closes = quotes.get("close", [])
    volumes = quotes.get("volume", [])

    returns: list[DailyReturn] = []
    prev_close = None

    for i, ts in enumerate(timestamps):
        trade_date = date.fromtimestamp(ts)
        close = closes[i] if i < len(closes) and closes[i] is not None else None
        vol = volumes[i] if i < len(volumes) and volumes[i] is not None else 0

        if close is None:
            continue

        ret = 0.0
        if prev_close and prev_close > 0:
            ret = (close - prev_close) / prev_close

        returns.append(DailyReturn(
            trade_date=trade_date,
            close=close,
            return_pct=ret,
            volume=vol,
        ))
        prev_close = close

    return returns


def create_simulated_prices(
    ticker: str,
    start: date,
    end: date,
    base_price: float = 100.0,
    daily_vol: float = 0.015,
    seed: int = 42,
) -> list[DailyReturn]:
    """Create simulated price data for testing.

    Uses a simple random walk model with configurable volatility.
    Deterministic given the same seed.
    """
    import random
    rng = random.Random(seed + hash(ticker))

    returns: list[DailyReturn] = []
    current = start
    price = base_price

    while current <= end:
        # Skip weekends
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        ret = rng.gauss(0.0003, daily_vol)  # small positive drift
        price *= (1 + ret)

        returns.append(DailyReturn(
            trade_date=current,
            close=round(price, 2),
            return_pct=ret,
            volume=rng.randint(5_000_000, 50_000_000),
        ))
        current += timedelta(days=1)

    return returns


# ── OLS Market Model ─────────────────────────────────────────────────

def _ols_market_model(
    stock_returns: list[float],
    market_returns: list[float],
) -> tuple[float, float, float, float]:
    """Fit OLS market model: R_stock = alpha + beta * R_market + epsilon.

    Returns (alpha, beta, r_squared, residual_std).
    No external dependencies — pure Python OLS.
    """
    n = len(stock_returns)
    if n < 10:
        return 0.0, 1.0, 0.0, 0.01

    # Means
    mean_x = sum(market_returns) / n
    mean_y = sum(stock_returns) / n

    # Beta = Cov(X,Y) / Var(X)
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(market_returns, stock_returns)) / n
    var_x = sum((x - mean_x) ** 2 for x in market_returns) / n

    if var_x < 1e-12:
        return mean_y, 0.0, 0.0, 0.01

    beta = cov_xy / var_x
    alpha = mean_y - beta * mean_x

    # Residuals
    residuals = [y - (alpha + beta * x) for x, y in zip(market_returns, stock_returns)]
    ss_res = sum(r ** 2 for r in residuals)
    ss_tot = sum((y - mean_y) ** 2 for y in stock_returns)

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    residual_std = math.sqrt(ss_res / (n - 2)) if n > 2 else 0.01

    return alpha, beta, max(0, r_squared), residual_std


# ── FF3 Factor Data ──────────────────────────────────────────────────

# Kenneth French Data Library: daily Fama-French 3 factors
# URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
# Format: CSV with date, Mkt-RF, SMB, HML, RF (all in percent)

_FF3_CACHE: dict[str, dict[date, tuple[float, float, float, float]]] = {}


def fetch_ff3_factors(start: date, end: date) -> dict[date, tuple[float, float, float, float]]:
    """Fetch daily Fama-French 3 factors from Kenneth French Data Library.

    Returns dict mapping date → (mkt_rf, smb, hml, rf) as decimals (not percent).
    Uses cached data if available.

    [src:kothari-warner-2007] Minimum standard: CAPM + FF3. Results should
    hold across both to be considered robust.
    """
    cache_key = "ff3_daily"
    if cache_key in _FF3_CACHE:
        return _FF3_CACHE[cache_key]

    import io
    import zipfile

    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "legalize-bot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            csv_name = [n for n in zf.namelist() if n.endswith(".CSV") or n.endswith(".csv")][0]
            raw = zf.read(csv_name).decode("utf-8")

        factors: dict[date, tuple[float, float, float, float]] = {}
        in_data = False

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                if in_data:
                    break  # End of daily data section
                continue

            # Skip header lines until we find data rows (start with a date like 19260701)
            parts = line.split(",")
            if len(parts) >= 5 and parts[0].strip().isdigit() and len(parts[0].strip()) == 8:
                in_data = True
                try:
                    date_str = parts[0].strip()
                    d = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                    mkt_rf = float(parts[1].strip()) / 100.0  # Convert from percent
                    smb = float(parts[2].strip()) / 100.0
                    hml = float(parts[3].strip()) / 100.0
                    rf = float(parts[4].strip()) / 100.0
                    factors[d] = (mkt_rf, smb, hml, rf)
                except (ValueError, IndexError):
                    continue

        logger.info("Loaded %d days of FF3 factor data", len(factors))
        _FF3_CACHE[cache_key] = factors
        return factors

    except Exception as e:
        logger.warning("Failed to fetch FF3 factors: %s. Falling back to Market Model.", e)
        return {}


def _ols_ff3_model(
    stock_returns: list[float],
    mkt_rf: list[float],
    smb: list[float],
    hml: list[float],
    rf: list[float],
) -> tuple[float, float, float, float, float, float]:
    """Fit OLS Fama-French 3-factor model.

    R_i - R_f = α + β₁(R_m - R_f) + β₂·SMB + β₃·HML + ε

    Returns (alpha, beta_mkt, beta_smb, beta_hml, r_squared, residual_std).
    Pure Python — no numpy dependency.
    """
    n = len(stock_returns)
    if n < 20:
        return 0.0, 1.0, 0.0, 0.0, 0.0, 0.01

    # Excess returns
    y = [stock_returns[i] - rf[i] for i in range(n)]

    # X matrix: [1, mkt_rf, smb, hml] for each observation
    # Normal equations: (X'X)β = X'y
    # For 4 regressors, solve 4x4 system

    # Compute X'X and X'y
    k = 4  # intercept + 3 factors
    xty = [0.0] * k
    xtx = [[0.0] * k for _ in range(k)]

    for i in range(n):
        x = [1.0, mkt_rf[i], smb[i], hml[i]]
        for j in range(k):
            xty[j] += x[j] * y[i]
            for m in range(k):
                xtx[j][m] += x[j] * x[m]

    # Solve via Gaussian elimination (4x4 is tiny)
    coeffs = _solve_linear_system(xtx, xty)
    if coeffs is None:
        return 0.0, 1.0, 0.0, 0.0, 0.0, 0.01

    alpha, beta_mkt, beta_smb, beta_hml = coeffs

    # Residuals
    mean_y = sum(y) / n
    ss_res = 0.0
    ss_tot = 0.0
    for i in range(n):
        predicted = alpha + beta_mkt * mkt_rf[i] + beta_smb * smb[i] + beta_hml * hml[i]
        residual = y[i] - predicted
        ss_res += residual ** 2
        ss_tot += (y[i] - mean_y) ** 2

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    residual_std = math.sqrt(ss_res / (n - k)) if n > k else 0.01

    return alpha, beta_mkt, beta_smb, beta_hml, max(0, r_squared), residual_std


def _solve_linear_system(A: list[list[float]], b: list[float]) -> list[float] | None:
    """Solve Ax = b via Gaussian elimination with partial pivoting.

    For small systems (4x4). Returns None if singular.
    """
    n = len(b)
    # Augmented matrix
    aug = [A[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        # Partial pivoting
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]

        if abs(aug[col][col]) < 1e-12:
            return None

        # Eliminate below
        for row in range(col + 1, n):
            factor = aug[row][col] / aug[col][col]
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]

    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = aug[i][n]
        for j in range(i + 1, n):
            x[i] -= aug[i][j] * x[j]
        x[i] /= aug[i][i]

    return x


# ── Event Study Engine ────────────────────────────────────────────────

class EventStudyEngine:
    """Run event studies measuring market reaction to regulatory events.

    Methodology:
      1. Estimation window: [-120, -11] business days before event
         Fit market model: R_i = α + β*R_m + ε
      2. Event window: [-5, +5] business days around event
         Calculate AR_t = R_i,t - (α + β*R_m,t)
      3. CAR = Σ AR_t across event window
      4. t-stat = CAR / (σ_ε * √T)

    Args:
        benchmark: Market benchmark ticker (default: SPY)
        estimation_days: Days in estimation window (default: 110)
        pre_gap: Gap between estimation and event window (default: 10)
        event_window: Tuple (pre_days, post_days) for event window
        use_simulated: Use simulated data instead of live Yahoo data
    """

    def __init__(
        self,
        benchmark: str = "SPY",
        estimation_days: int = 110,
        pre_gap: int = 10,
        event_window: tuple[int, int] = (5, 5),
        use_simulated: bool = False,
        model: str = "market",  # "market" (CAPM) or "ff3" (Fama-French 3)
    ):
        self.benchmark = benchmark
        self.estimation_days = estimation_days
        self.pre_gap = pre_gap
        self.event_pre = event_window[0]
        self.event_post = event_window[1]
        self.use_simulated = use_simulated
        self.model = model
        self._price_cache: dict[str, list[DailyReturn]] = {}
        self._ff3_factors: dict[date, tuple[float, float, float, float]] = {}

    def run(
        self,
        ticker: str,
        event_date: date,
        event_name: str = "",
    ) -> EventStudyResult:
        """Run event study for a single ticker.

        Args:
            ticker: ETF ticker
            event_date: Date of the regulatory event
            event_name: Name/title of the regulation (for reporting)
        """
        result = EventStudyResult(
            ticker=ticker,
            event_date=event_date,
            event_name=event_name,
            benchmark=self.benchmark,
        )

        # Calculate date range needed
        # We need: estimation_days + pre_gap + event_pre + event_post
        # Plus buffer for weekends/holidays (~1.5x calendar days)
        total_bdays = self.estimation_days + self.pre_gap + self.event_pre + self.event_post
        calendar_buffer = int(total_bdays * 1.5) + 30
        fetch_start = event_date - timedelta(days=calendar_buffer)
        fetch_end = event_date + timedelta(days=int(self.event_post * 1.5) + 10)

        try:
            # Fetch price data
            stock_data = self._get_prices(ticker, fetch_start, fetch_end)
            market_data = self._get_prices(self.benchmark, fetch_start, fetch_end)

            if len(stock_data) < 30 or len(market_data) < 30:
                logger.warning(f"Insufficient data for {ticker}: {len(stock_data)} days")
                result.data_source = "insufficient_data"
                return result

            # Align dates
            stock_by_date = {r.trade_date: r for r in stock_data}
            market_by_date = {r.trade_date: r for r in market_data}
            common_dates = sorted(set(stock_by_date.keys()) & set(market_by_date.keys()))

            # Find event date index (nearest trading day)
            event_idx = self._find_nearest_trading_day(common_dates, event_date)
            if event_idx is None:
                logger.warning(f"Event date {event_date} not found in trading dates for {ticker}")
                return result

            # Split into estimation and event windows
            est_end_idx = event_idx - self.pre_gap
            est_start_idx = est_end_idx - self.estimation_days

            evt_start_idx = event_idx - self.event_pre
            evt_end_idx = event_idx + self.event_post

            if est_start_idx < 1 or evt_end_idx >= len(common_dates):
                logger.warning(f"Not enough data around event for {ticker}")
                return result

            # Estimation window returns
            est_stock = [stock_by_date[common_dates[i]].return_pct for i in range(est_start_idx, est_end_idx)]
            est_market = [market_by_date[common_dates[i]].return_pct for i in range(est_start_idx, est_end_idx)]

            # Fit model (Market Model or FF3)
            if self.model == "ff3":
                result.model_type = "ff3"
                # Fetch FF3 factors if not cached
                if not self._ff3_factors:
                    self._ff3_factors = fetch_ff3_factors(fetch_start, fetch_end)

                if self._ff3_factors:
                    # Build aligned factor arrays for estimation window
                    est_mkt_rf, est_smb, est_hml, est_rf = [], [], [], []
                    est_stock_ff3 = []
                    for i in range(est_start_idx, est_end_idx):
                        d = common_dates[i]
                        if d in self._ff3_factors:
                            mkt_rf, smb, hml, rf = self._ff3_factors[d]
                            est_mkt_rf.append(mkt_rf)
                            est_smb.append(smb)
                            est_hml.append(hml)
                            est_rf.append(rf)
                            est_stock_ff3.append(stock_by_date[d].return_pct)

                    if len(est_stock_ff3) >= 20:
                        alpha, beta, beta_smb, beta_hml, r_sq, res_std = _ols_ff3_model(
                            est_stock_ff3, est_mkt_rf, est_smb, est_hml, est_rf,
                        )
                        result.alpha = alpha
                        result.beta = beta
                        result.beta_smb = beta_smb
                        result.beta_hml = beta_hml
                        result.r_squared = r_sq
                        result.estimation_std = res_std
                        result.estimation_days = len(est_stock_ff3)
                    else:
                        logger.warning("Insufficient FF3 data, falling back to Market Model")
                        result.model_type = "market"
                        alpha, beta, r_sq, res_std = _ols_market_model(est_stock, est_market)
                        result.alpha = alpha
                        result.beta = beta
                        result.r_squared = r_sq
                        result.estimation_std = res_std
                        result.estimation_days = len(est_stock)
                else:
                    logger.warning("FF3 factors unavailable, falling back to Market Model")
                    result.model_type = "market"
                    alpha, beta, r_sq, res_std = _ols_market_model(est_stock, est_market)
                    result.alpha = alpha
                    result.beta = beta
                    result.r_squared = r_sq
                    result.estimation_std = res_std
                    result.estimation_days = len(est_stock)
            else:
                result.model_type = "market"
                alpha, beta, r_sq, res_std = _ols_market_model(est_stock, est_market)
                result.alpha = alpha
                result.beta = beta
                result.r_squared = r_sq
                result.estimation_std = res_std
                result.estimation_days = len(est_stock)

            # Event window: calculate abnormal returns
            abnormal_returns = []
            car = 0.0
            car_pre = 0.0
            car_post = 0.0

            for i in range(evt_start_idx, min(evt_end_idx + 1, len(common_dates))):
                d = common_dates[i]
                relative_day = i - event_idx

                actual = stock_by_date[d].return_pct

                # Expected return depends on model
                if result.model_type == "ff3" and d in self._ff3_factors:
                    mkt_rf, smb, hml, rf = self._ff3_factors[d]
                    expected = rf + result.alpha + result.beta * mkt_rf + result.beta_smb * smb + result.beta_hml * hml
                else:
                    expected = result.alpha + result.beta * market_by_date[d].return_pct

                ar = actual - expected

                abnormal_returns.append((relative_day, ar))
                car += ar

                if relative_day < 0:
                    car_pre += ar
                else:
                    car_post += ar

            result.abnormal_returns = abnormal_returns
            result.car = car
            result.car_pre = car_pre
            result.car_post = car_post
            result.event_window_days = len(abnormal_returns)

            # t-statistic
            if res_std > 0 and len(abnormal_returns) > 0:
                result.t_stat = car / (res_std * math.sqrt(len(abnormal_returns)))
            else:
                result.t_stat = 0.0

            # p-value (approximate using normal distribution for large samples)
            result.p_value = 2 * (1 - _norm_cdf(abs(result.t_stat)))
            result.is_significant = abs(result.t_stat) >= 1.96

            result.data_source = "simulated" if self.use_simulated else "yahoo_finance"

        except Exception as e:
            logger.error(f"Event study failed for {ticker}: {e}")
            result.data_source = f"error: {e}"

        return result

    def run_regulation_study(
        self,
        etf_tickers: list[str],
        event_date: date,
        regulation_title: str = "",
    ) -> RegulationStudyResult:
        """Run event studies for all ETFs exposed to a regulation.

        Args:
            etf_tickers: List of exposed ETF tickers
            event_date: Publication date of the regulation
            regulation_title: Title of the regulation (for reporting)
        """
        results = []
        for ticker in etf_tickers:
            result = self.run(ticker, event_date, event_name=regulation_title)
            results.append(result)

        return RegulationStudyResult(
            regulation_title=regulation_title,
            event_date=event_date,
            etf_results=results,
        )

    def _get_prices(self, ticker: str, start: date, end: date) -> list[DailyReturn]:
        """Get price data from cache or fetch."""
        cache_key = f"{ticker}_{start}_{end}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        if self.use_simulated:
            data = create_simulated_prices(ticker, start, end)
        else:
            data = fetch_yahoo_prices(ticker, start, end)

        self._price_cache[cache_key] = data
        return data

    @staticmethod
    def _find_nearest_trading_day(
        trading_dates: list[date], target: date
    ) -> Optional[int]:
        """Find the index of the nearest trading day to the target date."""
        best_idx = None
        best_diff = timedelta(days=999)

        for i, d in enumerate(trading_dates):
            diff = abs(d - target)
            if diff < best_diff:
                best_diff = diff
                best_idx = i

        # Don't accept if more than 5 days away
        if best_diff > timedelta(days=5):
            return None

        return best_idx


# ── Normal CDF approximation ─────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    # Good to ~5 decimal places
    if x < -8:
        return 0.0
    if x > 8:
        return 1.0
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    p = d * math.exp(-x * x / 2) * (
        t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 +
        t * (-1.821255978 + t * 1.330274429))))
    )
    return 1.0 - p if x > 0 else p
