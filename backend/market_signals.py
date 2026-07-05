"""Real external market signals — genuinely live, free, and key-less.

Two public sources (no API key, no account):
  • Wikipedia pageviews  — real search/interest for the product category.
  • Hacker News (Algolia) — real recent industry headlines.

Results are cached in-memory for 15 minutes so we don't hammer the sources.
Everything degrades gracefully: if the network is down, the app still runs and
the caller just gets empty lists — nothing here can break a request.
"""
import time
import re
from datetime import date, timedelta
import httpx

_UA = "AxiomOS/1.0 (business-growth-os; contact: demo@axiom.local)"
_CACHE: dict[str, tuple[float, dict]] = {}
_TTL = 900  # 15 minutes


def _wiki_title(industry: str) -> str:
    """Map a business industry to a reasonable Wikipedia article title."""
    s = (industry or "").lower()
    if "skin" in s or "beauty" in s or "cosmetic" in s:
        return "Skin_care"
    if "food" in s or "beverage" in s:
        return "Food_industry"
    if "fashion" in s or "apparel" in s:
        return "Fast_fashion"
    if "fitness" in s or "health" in s:
        return "Health_club"
    # fall back to the first meaningful word, Title_Cased
    words = re.findall(r"[A-Za-z]+", industry or "Retail")
    base = next((w for w in words if len(w) > 2), "Retail")
    return base.capitalize()


def _news_query(industry: str) -> str:
    """Use the full industry phrase — Google News relevance is far better with it."""
    words = re.findall(r"[A-Za-z0-9]+", industry or "")
    return " ".join(words) or "startup"


async def wikipedia_interest(title: str) -> dict:
    """Last ~30 days of daily pageviews for a topic — a real interest signal."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=29)
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/all-agents/{title}/daily/"
        f"{start.strftime('%Y%m%d')}00/{end.strftime('%Y%m%d')}00"
    )
    async with httpx.AsyncClient(timeout=12, headers={"User-Agent": _UA}) as client:
        r = await client.get(url)
        r.raise_for_status()
        items = r.json().get("items", [])
    points = [{"date": it["timestamp"][:8], "views": it["views"]} for it in items]
    total = sum(p["views"] for p in points)
    half = max(len(points) // 2, 1)
    first_half = sum(p["views"] for p in points[:half]) or 1
    second_half = sum(p["views"] for p in points[half:])
    change_pct = round((second_half - first_half) / first_half * 100, 1)
    return {
        "topic": title.replace("_", " "),
        "points": points,
        "total_views": total,
        "trend_pct": change_pct,   # +ve => interest rising over the window
        "source": "Wikipedia pageviews",
    }


def _clean(s: str) -> str:
    return (s or "").replace("<![CDATA[", "").replace("]]>", "").strip()


async def industry_news(query: str, limit: int = 5) -> list[dict]:
    """Recent real, on-topic industry headlines from Google News RSS (no key)."""
    q = httpx.QueryParams({"q": f"{query} India", "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    url = f"https://news.google.com/rss/search?{q}"
    async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "Mozilla/5.0 (AxiomOS)"}) as client:
        r = await client.get(url)
        r.raise_for_status()
        xml = r.text
    out = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)[:limit]:
        title = _clean((re.search(r"<title>(.*?)</title>", block, re.DOTALL) or [None, ""])[1])
        link = _clean((re.search(r"<link>(.*?)</link>", block, re.DOTALL) or [None, ""])[1])
        pub = _clean((re.search(r"<pubDate>(.*?)</pubDate>", block, re.DOTALL) or [None, ""])[1])
        src = _clean((re.search(r"<source[^>]*>(.*?)</source>", block, re.DOTALL) or [None, ""])[1])
        # Google News titles are "Headline - Source"; drop the trailing source.
        if src and title.endswith(f" - {src}"):
            title = title[: -(len(src) + 3)]
        if title:
            out.append({"title": title, "url": link, "date": pub[:16], "source": src or "Google News"})
    return out


async def live_signals(industry: str) -> dict:
    """Combined real market signals for an industry, cached for 15 minutes."""
    key = (industry or "").lower().strip() or "default"
    now = time.time()
    if key in _CACHE and now - _CACHE[key][0] < _TTL:
        return _CACHE[key][1]

    title = _wiki_title(industry)
    query = _news_query(industry)
    result: dict = {"interest": None, "news": [], "fetched_at": None, "errors": []}
    try:
        result["interest"] = await wikipedia_interest(title)
    except Exception as e:
        result["errors"].append(f"wikipedia: {e}")
    try:
        result["news"] = await industry_news(query)
    except Exception as e:
        result["errors"].append(f"news: {e}")
    result["fetched_at"] = date.today().isoformat()
    result["live"] = bool(result["interest"] or result["news"])
    _CACHE[key] = (now, result)
    return result


def signals_summary(sig: dict) -> str:
    """Compact text summary for injecting real signals into an LLM prompt."""
    if not sig or not sig.get("live"):
        return "No live external signals available."
    parts = []
    it = sig.get("interest")
    if it:
        arrow = "rising" if it["trend_pct"] > 3 else "falling" if it["trend_pct"] < -3 else "flat"
        parts.append(
            f"Real category interest ({it['topic']}, Wikipedia): {it['total_views']:,} views "
            f"over 30 days, trend {it['trend_pct']:+.1f}% ({arrow})."
        )
    news = sig.get("news") or []
    if news:
        heads = "; ".join(f"\"{n['title']}\"" for n in news[:4])
        parts.append(f"Recent real industry headlines (Google News): {heads}.")
    return " ".join(parts)
