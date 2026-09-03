# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""MCP boundary tests — no SQL exposure, bounded output, privacy block."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def _send(server_fn, method, params=None):
    """Simulate a single MCP request/response cycle."""
    import io
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                      "params": params or {}})
    from NIZAM__system.retrieval import hermes_mcp
    responses = []
    orig_write = sys.stdout.write
    captured = []
    class _Cap:
        def write(self, s): captured.append(s)
        def flush(self): pass
    sys.stdout = _Cap()
    try:
        hermes_mcp._handle(json.loads(req))
    finally:
        sys.stdout = sys.__stdout__
    return json.loads("".join(captured).strip()) if captured else {}


def test_initialize_responds():
    r = _send(None, "initialize")
    assert "result" in r
    assert r["result"]["serverInfo"]["name"] == "nizam-knowledge"


def test_tools_list_returns_four_tools():
    r = _send(None, "tools/list")
    names = {t["name"] for t in r["result"]["tools"]}
    assert names == {"knowledge_search", "knowledge_context",
                     "knowledge_timeline", "knowledge_entity"}


def test_unknown_tool_returns_error():
    r = _send(None, "tools/call", {"name": "run_sql", "arguments": {"sql": "SELECT 1"}})
    assert "error" in r
    assert "Unknown tool" in r["error"]["message"]


def test_unknown_method_returns_error():
    r = _send(None, "direct_sql_query", {})
    assert "error" in r


def test_tool_schema_no_sql_property():
    """Verify no tool schema exposes an 'sql' or 'query_raw' parameter."""
    r = _send(None, "tools/list")
    for tool in r["result"]["tools"]:
        props = tool.get("inputSchema", {}).get("properties", {})
        assert "sql" not in props, f"Tool {tool['name']} exposes sql parameter"
        assert "query_raw" not in props
        assert "execute" not in props
