"""
Stratosphere - UI Showcase (demo server)

Serves the complete Stratosphere web interface using SAMPLE data only.
The private core (AI models, backtester, indicator logic, broker integration)
is intentionally NOT part of this repository, so any action that needs it
returns a friendly "demo mode" message instead of real results.

Run:  uvicorn demo_server:app --reload      then open http://127.0.0.1:8000
"""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
MOCK = BASE / "mock_data"

SNAP = json.loads((MOCK / "get_snapshots.json").read_text(encoding="utf-8"))
SAMPLES = json.loads((MOCK / "analyzer_samples.json").read_text(encoding="utf-8"))

app = FastAPI(title="Stratosphere UI Showcase", version="demo")
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")
templates = Jinja2Templates(directory=WEB / "templates")

DEMO_MSG = ("Demo mode: this action runs the private core engine, "
            "which is not included in this public repository.")


def _render(request: Request, name: str, **ctx):
    return templates.TemplateResponse(request, name, context=ctx)


class _Obj(SimpleNamespace):
    """Lets Jinja read dict data with attribute access (ind.category.value)."""


def _indicators_for_template():
    out = []
    for i in SNAP["indicators"]["body"]:
        i = copy.deepcopy(i)
        i["category"] = _Obj(value=i["category"])
        for o in i.get("outputs", []):
            o["output_type"] = _Obj(value=o["output_type"])
        i["parameters"] = [_Obj(**p) for p in i.get("parameters", [])]
        i["outputs"] = [_Obj(**o) for o in i.get("outputs", [])]
        out.append(_Obj(**i))
    return out


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def dashboard(request: Request):
    inds = SNAP["indicators"]["body"]
    return _render(request, "dashboard.html",
                   indicators_count=len(inds),
                   categories_count=len({i["category"] for i in inds}),
                   schema_version="1.0.0")


@app.get("/indicators")
async def indicators(request: Request):
    inds = _indicators_for_template()
    cats, seen = [], set()
    for i in inds:
        if i.category.value not in seen:
            seen.add(i.category.value)
            cats.append(i.category)
    return _render(request, "indicators.html", indicators=inds, categories=cats)


@app.get("/validate")
async def validate(request: Request):
    example = json.dumps({
        "schema_version": "1.0.0", "name": "Example Strategy",
        "primary_timeframe": "DAILY",
        "entry": {"direction": "LONG", "condition": {
            "type": "leaf", "indicator_id": "rsi", "indicator_params": {"period": 14},
            "comparison": "CROSSES_BELOW", "threshold": {"type": "static", "value": 30}}},
        "exit": {"stop_loss": {"type": "fixed_pct", "pct": 2.0}},
        "sizing": {"type": "fixed_qty", "quantity": 100}}, indent=2)
    return _render(request, "validate.html", example_json=example)


PAGES = {"/schema": "schema.html", "/builder": "builder.html",
         "/analyzer": "analyzer.html", "/convergence": "convergence.html",
         "/ai": "ai_scorer.html", "/results": "results.html",
         "/intraday": "intraday.html", "/ai-tower": "ai_tower.html",
         "/kite/auth": "kite_auth.html", "/trading": "trading.html",
         "/paper-trade": "paper_trade.html"}


def _make_page(tpl):
    async def page(request: Request):
        return _render(request, tpl)
    return page


for _path, _tpl in PAGES.items():
    app.add_api_route(_path, _make_page(_tpl), methods=["GET"], include_in_schema=False)

# ── Read-only data endpoints (sample snapshots) ──────────────────────────────
GET_MAP = {
    "/api/builder/metadata": "builder_metadata", "/api/schema": "schema",
    "/api/indicators": "indicators", "/api/stocks": "stocks",
    "/api/convergence/sources": "convergence_sources", "/api/ai/meta": "ai_meta",
    "/api/ai/status": "ai_status", "/api/ai/nifty-status": "nifty_status",
    "/api/ai/nifty-results": "nifty_results",
    "/api/ai/nifty-wfv-status": "nifty_wfv_status",
    "/api/ai/nifty-wfv-results": "nifty_wfv_results",
    "/api/ai/scorer-validate-status": "scorer_validate_status",
    "/api/ai/scorer-validate-results": "scorer_validate_results",
    "/api/kite/status": "kite_status", "/api/backtest/status": "backtest_status",
    "/api/backtest/results": "backtest_results", "/api/paper/status": "paper_status",
    "/api/paper/strategies": "paper_strategies", "/api/data/status": "data_status",
    "/api/angel/cache-info": "angel_cache_info",
    "/api/angel/collect-status": "angel_collect_status",
    "/api/trade/positions": "trade_positions", "/api/fno/eligible": "fno_eligible",
}


def _make_get(key):
    async def handler():
        snap = SNAP[key]
        return JSONResponse(snap["body"], status_code=snap["status"])
    return handler


for _p, _k in GET_MAP.items():
    app.add_api_route(_p, _make_get(_k), methods=["GET"], include_in_schema=False)


# ── Sample-result endpoints (pre-computed on sample data) ────────────────────
async def _body(request: Request):
    try:
        return await request.json()
    except Exception:
        return {}


def _sample(key):
    async def handler(request: Request):
        body = await _body(request)
        data = copy.deepcopy(SAMPLES[key])
        sym = (body.get("symbol") or "").strip().upper().replace(".NS", "")
        if sym and isinstance(data, dict):
            if "symbol" in data:
                data["symbol"] = sym + ".NS"
            if "stock_name" in data:
                data["stock_name"] = sym.title() + " Ltd (sample data)"
        return JSONResponse(data)
    return handler


app.add_api_route("/api/analyze", _sample("analyze"), methods=["POST"], include_in_schema=False)
app.add_api_route("/api/analyze/combine", _sample("combine"), methods=["POST"], include_in_schema=False)
app.add_api_route("/api/analyze/single", _sample("single"), methods=["POST"], include_in_schema=False)
app.add_api_route("/api/analyze/sweep", _sample("sweep"), methods=["POST"], include_in_schema=False)
app.add_api_route("/api/validate", _sample("validate"), methods=["POST"], include_in_schema=False)


# ── Everything else that needs the private engine ────────────────────────────
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"],
               include_in_schema=False)
async def demo_only(path: str):
    return JSONResponse({"error": DEMO_MSG, "demo": True}, status_code=503)
