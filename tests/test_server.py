"""The server of the Model Context Protocol (specification/conformance.md#the-server):
revision 2026-07-28 served statelessly, the earlier revisions after `initialize`, one tool
for each function of the API that adds nothing to it, the resources a writer reads, and
the transport over standard input and output; and, against the protocol's own client, a
check that a host can use it in each way a host connects."""
import base64
import inspect
import io
import json
import os
import queue
import sys
import threading

import pytest

from rowih import api, data, structured
from rowih.server import (INVALID_PARAMS, INVALID_REQUEST, LEGACY, LEGACY_RESOURCE_NOT_FOUND,
                          MAX_SUBSCRIPTIONS, METHOD_NOT_FOUND, MODERN, PARSE_ERROR,
                          UNSUPPORTED_PROTOCOL_VERSION, Server, _reader, _send, run, serve)
from rowih.server_tools import MAX_TEXT, ToolInputError, check
from rowih.writer import Envelope

from corpus import messages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOCK = 1761300000
SERVER = Server(clock=lambda: CLOCK)
META = {"io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {}}
NOTATION = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (OBSERVATION-TIME 5 "
            "MINUTE AGO) (situation run POLARITY.NEGATIVE (UNDERGOER (term service "
            "DEFINITE)))))")
TEXT = messages()[0][3]


def request(method, params=None, ident=1, server=SERVER, meta=META):
    p = dict(params or {})
    if meta is not None:
        p["_meta"] = meta
    return server.handle({"jsonrpc": "2.0", "id": ident, "method": method, "params": p})


def result(method, params=None, **kw):
    out = request(method, params, **kw)
    assert len(out) == 1 and "result" in out[0], out
    return out[0]["result"]


def error(method, params=None, **kw):
    out = request(method, params, **kw)
    assert len(out) == 1 and "error" in out[0], out
    return out[0]["error"]


def call(name, arguments):
    return result("tools/call", {"name": name, "arguments": arguments})


# ------------------------------------------------------------------- the protocol
def test_discovery_states_the_versions_capabilities_and_identity():
    r = result("server/discover")
    assert r["resultType"] == "complete"
    assert r["supportedVersions"] == [MODERN] + list(LEGACY)
    assert r["capabilities"] == {"tools": {}, "resources": {}}
    assert r["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "rowih"
    assert r["ttlMs"] > 0 and r["cacheScope"] == "public"
    assert "write" in r["instructions"] and "inert" in r["instructions"]


def test_every_modern_result_says_it_is_complete_and_who_served_it():
    for method in ("tools/list", "resources/list", "resources/templates/list"):
        r = result(method)
        assert r["resultType"] == "complete" and r["cacheScope"] == "public"
        assert r["_meta"]["io.modelcontextprotocol/serverInfo"]["version"] == \
            __import__("rowih").__version__


def test_an_unsupported_version_is_refused_with_the_versions_supported():
    e = error("tools/list", meta=dict(META, **{
        "io.modelcontextprotocol/protocolVersion": "1900-01-01"}))
    assert e["code"] == UNSUPPORTED_PROTOCOL_VERSION
    assert e["data"] == {"supported": [MODERN] + list(LEGACY), "requested": "1900-01-01"}


def test_a_handshake_version_stated_per_request_is_unsupported_not_served():
    e = error("tools/list", meta=dict(META, **{
        "io.modelcontextprotocol/protocolVersion": LEGACY[0]}))
    assert e["code"] == UNSUPPORTED_PROTOCOL_VERSION


def test_a_request_without_its_version_or_capabilities_is_malformed():
    assert error("tools/list", meta=None, server=Server())["code"] == INVALID_PARAMS
    e = error("tools/list", meta={"io.modelcontextprotocol/protocolVersion": MODERN})
    assert e["code"] == INVALID_PARAMS and "capabilities" in e["message"]


def test_initialize_agrees_the_version_asked_or_the_newest_handshake_version():
    for asked, agreed in [("2025-06-18", "2025-06-18"), ("2024-11-05", "2024-11-05"),
                          ("2099-01-01", LEGACY[0])]:
        server = Server()
        r = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": asked, "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}}})[0]["result"]
        assert r["protocolVersion"] == agreed
        assert r["capabilities"] == {"tools": {}, "resources": {}}
        assert r["serverInfo"]["name"] == "rowih" and r["instructions"]


def test_after_initialize_requests_are_served_in_the_earlier_revision():
    server = Server()
    server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2025-11-25", "capabilities": {}}})
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) == []
    assert server.handle({"jsonrpc": "2.0", "id": 2, "method": "ping"})[0]["result"] == {}
    tools = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})[0]["result"]
    assert set(tools) == {"tools"}
    missing = server.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/read",
                             "params": {"uri": "rowih://none"}})[0]["error"]
    assert missing["code"] == LEGACY_RESOURCE_NOT_FOUND
    # a modern request on the same process is still served statelessly
    assert result("tools/list", server=server)["resultType"] == "complete"


def test_a_modern_resource_not_found_is_invalid_params():
    e = error("resources/read", {"uri": "rowih://none"})
    assert e["code"] == INVALID_PARAMS and e["data"] == {"uri": "rowih://none"}


@pytest.mark.parametrize("message,code", [
    ([], INVALID_REQUEST), ({"id": 1, "method": "tools/list"}, INVALID_REQUEST),
    ({"jsonrpc": "2.0", "id": None, "method": "tools/list"}, INVALID_REQUEST),
    ({"jsonrpc": "2.0", "id": True, "method": "tools/list"}, INVALID_REQUEST),
    ({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": []}, INVALID_REQUEST),
])
def test_a_message_that_is_not_a_request_is_refused(message, code):
    assert SERVER.handle(message)[0]["error"]["code"] == code


def test_methods_the_server_lacks_are_not_found():
    for method in ("prompts/list", "ping", "logging/setLevel", "completion/complete"):
        assert error(method)["code"] == METHOD_NOT_FOUND


def test_every_list_is_one_page():
    assert "nextCursor" not in result("tools/list")
    assert error("tools/list", {"cursor": "next"})["code"] == INVALID_PARAMS


def test_a_response_or_an_unknown_notification_draws_nothing():
    assert SERVER.handle({"jsonrpc": "2.0", "id": 1, "result": {}}) == []
    assert SERVER.handle({"jsonrpc": "2.0", "method": "notifications/progress"}) == []


def test_a_subscription_is_acknowledged_held_until_cancelled_and_closed_at_the_end():
    server = Server()
    ack = request("subscriptions/listen", {"notifications": {"toolsListChanged": True}},
                  ident=7, server=server)
    assert ack == [{"jsonrpc": "2.0", "method": "notifications/subscriptions/acknowledged",
                    "params": {"_meta": {"io.modelcontextprotocol/subscriptionId": 7},
                               "notifications": {}}}]
    request("subscriptions/listen", {"notifications": {}}, ident=8, server=server)
    server.handle({"jsonrpc": "2.0", "method": "notifications/cancelled",
                   "params": {"requestId": 7}})
    assert server.close() == [{"jsonrpc": "2.0", "id": 8, "result": {
        "resultType": "complete", "_meta": {"io.modelcontextprotocol/subscriptionId": 8}}}]
    assert server.close() == []


def test_subscriptions_are_bounded():
    server = Server()
    for i in range(MAX_SUBSCRIPTIONS):
        request("subscriptions/listen", ident=i, server=server)
    assert error("subscriptions/listen", ident="over", server=server)["message"] == \
        "Subscription limit reached"


# -------------------------------------------------------------------- the tools
def test_the_tools_are_the_api_and_write():
    public = {name for name, f in inspect.getmembers(api, inspect.isfunction)
              if not name.startswith("_") and f.__module__ == "rowih.api"}
    names = [t["name"] for t in result("tools/list")["tools"]]
    assert set(names) == public
    assert names == [t["name"] for t in result("tools/list")["tools"]]   # deterministic


def test_every_tool_reads_nothing_and_closes_its_arguments():
    for t in result("tools/list")["tools"]:
        assert t["inputSchema"]["type"] == "object"
        assert t["inputSchema"]["additionalProperties"] is False
        assert t["annotations"]["readOnlyHint"] is True
        assert t["annotations"]["openWorldHint"] is False
        assert t["description"] and t["title"]


def _undescribed(schema: dict, path: str) -> list:
    """The properties of a schema, nested ones included, that carry no description."""
    out = []
    for name, prop in schema.get("properties", {}).items():
        if not prop.get("description"):
            out.append(path + name)
        if prop.get("type") == "object":
            out += _undescribed(prop, path + name + ".")
        items = prop.get("items")
        if isinstance(items, dict) and items.get("type") == "object":
            out += _undescribed(items, path + name + "[].")
    return out


def test_every_parameter_of_every_tool_is_described():
    """A host shows a model each tool's parameters by their descriptions alone."""
    tools = result("tools/list")["tools"]
    missing = [t["name"] + ": " + p for t in tools for p in _undescribed(t["inputSchema"], "")]
    assert missing == []
    assert all(len(t["description"]) >= 200 for t in tools), \
        [t["name"] for t in tools if len(t["description"]) < 200]


def test_write_writes_the_message_api_write_writes_and_checks_it():
    r = call("write", {"notation": NOTATION, "sender": 3, "recipients": [1, 2],
                       "time": "1761300000.5", "identifier": 4, "first_entry": 9,
                       "semantic": True})
    s = r["structuredContent"]
    text, diags = api.write(NOTATION, Envelope(3, (1, 2), "1761300000.5", identifier=4,
                                               first_entry=9, semantic=True))
    assert s["message"] == text and s["ok"] is True and s["diagnostics"] == [] == diags
    assert s["envelope"]["sender"] == "3" and s["envelope"]["recipients"] == ["1", "2"]
    assert s["envelope"]["communication time"] == "1761300000.5"
    assert s["envelope"]["identifier"] == "000004" and s["envelope"]["first entry"] == "9"
    assert s["envelope"]["semantic check value"] is not None
    assert s["explanation"] == api.translate(text, "english")[0]
    assert s["moves"][0]["literal semantic form"].startswith("(move ASSERTED-POSITION")
    assert json.loads(r["content"][0]["text"]) == s and "isError" not in r


def test_write_takes_the_current_time_where_none_is_given():
    s = call("write", {"notation": NOTATION, "sender": 1, "recipients": [2]})
    assert s["structuredContent"]["envelope"]["communication time"] == str(CLOCK)


def test_write_reports_what_reading_its_message_finds():
    s = call("write", {"notation": "(move)", "sender": 1, "recipients": [2]})
    assert "isError" not in s
    assert s["structuredContent"]["ok"] is False and s["structuredContent"]["diagnostics"]


@pytest.mark.parametrize("arguments,says", [
    ({"notation": "(move FOO)", "sender": 1, "recipients": [2]}, "NotationError"),
    ({"notation": "(move", "sender": 1, "recipients": [2]}, "NotationError"),
    ({"notation": NOTATION, "sender": 1, "recipients": [2], "time": "noon"}, "EnvelopeError"),
    ({"notation": NOTATION, "sender": 1, "recipients": [2], "dialects": [[99, "0.1"]]},
     "EnvelopeError"),
    ({"notation": NOTATION, "sender": 1}, "needs recipients"),
    ({"notation": NOTATION, "sender": -1, "recipients": [2]}, "at least 0"),
    ({"notation": NOTATION, "sender": "1", "recipients": [2]}, "is integer"),
    ({"notation": NOTATION, "sender": 1, "recipients": []}, "at least 1 items"),
    ({"notation": NOTATION, "sender": 1, "recipients": [2], "mode": "loud"}, "one of"),
    ({"notation": NOTATION, "sender": 1, "recipients": [2], "colour": "red"},
     "no argument colour"),
    ({"notation": "x" * (MAX_TEXT + 1), "sender": 1, "recipients": [2]}, "at most"),
])
def test_an_input_that_cannot_be_written_is_a_tool_error_saying_why(arguments, says):
    r = call("write", arguments)
    assert r["isError"] is True and says in r["structuredContent"]["error"]


def test_an_unknown_tool_is_a_protocol_error():
    e = error("tools/call", {"name": "delete_everything", "arguments": {}})
    assert e["code"] == INVALID_PARAMS and "delete_everything" in e["message"]
    assert error("tools/call", {"name": "write", "arguments": []})["code"] == INVALID_PARAMS


def test_parse_gives_the_analysis_as_structured_data():
    s = call("parse", {"text": TEXT})["structuredContent"]
    a = api.parse(TEXT)
    assert s == json.loads(json.dumps(structured.analysis(a, data.load())))
    assert s["ok"] is True and s["confidence"] == "verified"


@pytest.mark.parametrize("name,arguments,key", [
    ("validate", {"text": TEXT}, "ok"), ("lookup", {"term": "run"}, "items"),
    ("translate", {"text": TEXT, "to": "english"}, "text"),
    ("translate", {"text": TEXT, "to": "formal"}, "changes"),
    ("gloss", {"text": TEXT}, "gloss"), ("normalise", {"text": TEXT}, "normal text"),
    ("check_values", {"text": TEXT}, "integrity"), ("analyze", {"text": TEXT}, "times"),
    ("discourse", {"texts": [TEXT], "participant": "2"}, "structure"),
    ("generate", {"notation": NOTATION}, "transliteration"),
    ("convert", {"text": TEXT, "to": "native"}, "text"),
    ("render", {"text": TEXT, "format": "svg"}, "text"),
    ("speak", {"text": TEXT}, "lines"), ("sound", {"text": TEXT}, "sound"),
    ("tokenize", {"text": TEXT, "lexicon": "1.0"}, "words"), ("version", {}, "language"),
])
def test_each_tool_answers_with_its_function_s_result(name, arguments, key):
    r = call(name, arguments)
    assert "isError" not in r and key in r["structuredContent"]
    assert json.loads(r["content"][0]["text"]) == r["structuredContent"]


def test_generate_keeps_the_fixed_envelope_unless_one_is_given():
    fixed = call("generate", {"notation": NOTATION})["structuredContent"]
    assert fixed == json.loads(json.dumps(api.generate(NOTATION)))
    given = call("generate", {"notation": NOTATION, "sender": 5, "recipients": [6],
                              "time": 1761300000})["structuredContent"]
    assert api.parse(given["standard form"]).message.envelope.sender.text == "5"


def test_a_png_is_an_image_and_audio_is_audio():
    r = call("render", {"text": TEXT, "format": "png"})
    image = [c for c in r["content"] if c["type"] == "image"]
    assert image[0]["mimeType"] == "image/png"
    assert base64.b64decode(image[0]["data"]) == api.render(TEXT, "png")[0]
    spoken = call("speak", {"text": TEXT})
    out, _ = api.speak(TEXT)
    audio = [c for c in spoken["content"] if c["type"] == "audio"]
    assert len(audio) == (1 if out["audio"] else 0)


def test_lookup_says_how_the_notation_writes_each_word():
    items = call("lookup", {"term": "run"})["structuredContent"]["items"]
    written = {i["kind"]: i["written"] for i in items}
    assert written["root"] == "run" and written["idiom"] == "(idiom run-run)"


def test_the_version_names_the_package():
    s = call("version", {})["structuredContent"]
    assert s["package"] == __import__("rowih").__version__ and s["language"] == "1.0"


def test_the_schema_check_refuses_what_the_schema_refuses():
    schema = {"type": "object", "properties": {"n": {"type": "integer", "minimum": 0},
                                               "pair": {"type": "array", "prefixItems": [
                                                   {"type": "integer"}, {"type": "string"}]},
                                               "t": {"type": ["string", "integer"]}},
              "required": ["n"], "additionalProperties": False}
    check(schema, {"n": 0, "pair": [1, "a"], "t": 3}, "x")
    for bad in ({}, {"n": True}, {"n": 1.5}, {"n": -1}, {"n": 0, "pair": ["a", 1]},
                {"n": 0, "t": 1.5}, {"n": 0, "m": 1}):
        with pytest.raises(ToolInputError):
            check(schema, bad, "x")


# ---------------------------------------------------------------- the resources
def test_the_resources_are_the_summary_the_listing_and_the_specification():
    listed = {r["uri"]: r for r in result("resources/list")["resources"]}
    chapters = sorted(n[:-3] for n in os.listdir(os.path.join(ROOT, "specification"))
                      if n.endswith(".md"))
    assert set(listed) == {"rowih://grammar", "rowih://lexicon"} | {
        "rowih://specification/%s" % c for c in chapters}
    for uri, r in listed.items():
        contents = result("resources/read", {"uri": uri})["contents"]
        assert contents[0]["uri"] == uri and contents[0]["mimeType"] == r["mimeType"]
        assert contents[0]["text"].startswith("# ")
    notation = result("resources/read", {"uri": "rowih://specification/notation"})
    with open(os.path.join(ROOT, "specification", "notation.md"), encoding="utf-8") as f:
        assert notation["contents"][0]["text"] == f.read()


# ---------------------------------------------------------------- the transport
def _lines(*messages) -> io.BytesIO:
    return io.BytesIO(b"".join((m if isinstance(m, bytes) else json.dumps(m).encode())
                               + b"\n" for m in messages))


def _served(stdin) -> list:
    out = io.BytesIO()
    assert serve(stdin, out, Server(clock=lambda: CLOCK)) == 0
    return [json.loads(line) for line in out.getvalue().splitlines()]


def test_the_transport_answers_one_line_a_message_until_the_input_ends():
    answers = _served(_lines(
        {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}},
        b"{not json", b"",
        {"jsonrpc": "2.0", "id": 2, "method": "subscriptions/listen",
         "params": {"_meta": META, "notifications": {}}}))
    assert answers[0]["id"] == 1 and answers[0]["result"]["resultType"] == "complete"
    assert answers[1] == {"jsonrpc": "2.0", "id": None,
                          "error": {"code": PARSE_ERROR, "message": "Parse error"}}
    assert answers[2]["method"] == "notifications/subscriptions/acknowledged"
    # the end of the input closes the subscription with its completion result
    assert answers[3]["id"] == 2 and answers[3]["result"]["resultType"] == "complete"
    assert len(answers) == 4


def test_a_line_too_long_is_refused_and_the_next_is_read(monkeypatch):
    monkeypatch.setattr("rowih.server.MAX_LINE", 400)
    # a line of 803 bytes, read in three pieces of at most 401, then a request of fewer
    # than 400
    answers = _served(_lines(b"[" + b"1," * 400 + b"1]",
                             {"jsonrpc": "2.0", "id": 3, "method": "tools/list",
                              "params": {"_meta": META}}))
    assert answers[0]["error"]["code"] == INVALID_REQUEST and answers[0]["id"] is None
    assert answers[1]["id"] == 3


def test_the_reader_notes_a_cancellation_as_it_arrives():
    inbox, cancelled = queue.Queue(), set()
    _reader(_lines({"jsonrpc": "2.0", "method": "notifications/cancelled",
                    "params": {"requestId": "a"}}), inbox, cancelled, threading.Lock())
    assert cancelled == {'"a"'} and inbox.get()[0] == "message" and inbox.get()[0] == "end"


def test_the_answer_to_a_request_cancelled_while_it_ran_is_withheld():
    inbox, sent, lock = queue.Queue(), [], threading.Lock()
    cancelled = {json.dumps(1)}   # as the reader notes it while request 1 is answered
    for m in ({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": META}},
              {"jsonrpc": "2.0", "method": "notifications/cancelled",
               "params": {"requestId": 1}},
              {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": META}}):
        inbox.put(("message", m))
    inbox.put(("end", None))
    assert run(inbox, Server(), sent.append, cancelled, lock) == 0
    # the first answer is withheld; the cancellation is then spent, and the identifier,
    # used again, is answered
    assert [m["id"] for m in sent] == [1] and cancelled == set()


def test_a_cancellation_after_the_answer_is_spent_without_effect():
    inbox, sent, lock = queue.Queue(), [], threading.Lock()
    inbox.put(("message", {"jsonrpc": "2.0", "id": 1, "method": "tools/list",
                           "params": {"_meta": META}}))
    cancelled = set()
    inbox.put(("message", {"jsonrpc": "2.0", "method": "notifications/cancelled",
                           "params": {"requestId": 1}}))
    inbox.put(("end", None))

    def send(m):
        sent.append(m)
        cancelled.add(json.dumps(1))   # the reader sees the cancellation only now
    run(inbox, Server(), send, cancelled, lock)
    assert [m["id"] for m in sent] == [1] and cancelled == set()


def test_a_failure_inside_the_library_is_an_internal_error_and_the_server_goes_on():
    class Broken(Server):
        def handle(self, message):
            if message.get("id") == 1:
                raise KeyError("a defect")
            return super().handle(message)
    inbox, sent = queue.Queue(), []
    for i in (1, 2):
        inbox.put(("message", {"jsonrpc": "2.0", "id": i, "method": "tools/list",
                               "params": {"_meta": META}}))
    inbox.put(("end", None))
    run(inbox, Broken(), sent.append, set(), threading.Lock())
    assert sent[0]["error"] == {"code": -32603, "message": "Internal error: KeyError"}
    assert sent[1]["id"] == 2 and "result" in sent[1]


def test_each_message_is_one_line_with_the_unicode_separators_escaped():
    out = io.BytesIO()
    _send(out, {"text": "a\nb c d"})
    line = out.getvalue()
    assert line.count(b"\n") == 1 and line.endswith(b"\n")
    assert " ".encode() not in line and json.loads(line)["text"] == "a\nb c d"


# --------------------------------------------- against the protocol's own client
@pytest.mark.parametrize("mode,version", [("auto", MODERN), ("legacy", LEGACY[0]),
                                          (MODERN, MODERN)])
def test_the_protocol_s_client_uses_the_server_in_each_way_a_host_connects(mode, version):
    anyio = pytest.importorskip("anyio")
    from mcp import Client, StdioServerParameters
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "rowih.cli", "serve"], cwd=ROOT,
        env={"PYTHONPATH": os.path.join(ROOT, "python")})

    async def session():
        async with Client(params, mode=mode, read_timeout_seconds=120) as client:
            assert client.protocol_version == version
            names = [t.name for t in (await client.list_tools()).tools]
            assert names[0] == "write" and "parse" in names
            written = await client.call_tool("write", {
                "notation": NOTATION, "sender": 1, "recipients": [2], "time": CLOCK})
            assert not written.is_error and written.structured_content["ok"] is True
            message = written.structured_content["message"]
            read = await client.call_tool("parse", {"text": message})
            assert read.structured_content["moves"][0]["class"] == ["inert"]
            refused = await client.call_tool("write", {
                "notation": "(move FOO)", "sender": 1, "recipients": [2]})
            assert refused.is_error
            uris = [str(r.uri) for r in (await client.list_resources()).resources]
            assert "rowih://grammar" in uris
            grammar = await client.read_resource("rowih://grammar")
            assert grammar.contents[0].text.startswith("# Rowih: the grammar summary")
            return message
    message = anyio.run(session)
    assert message == api.write(NOTATION, Envelope(1, (2,), CLOCK))[0]


def test_state_writes_a_protocol_message_and_reads_it_back():
    s = call("state", {"kind": "send-again", "sender": 2, "recipient": 1,
                       "channels": [{"recipients": [2], "serials": [4, 5]}],
                       "entries": [7]})["structuredContent"]
    assert s["ok"] is True and s["statement"]["kind"] == "send-again"
    assert s["message"] == api.state("send-again", 2, 1, CLOCK, channels=[((2,), (4, 5))],
                                     entries=[7])[0]
    refused = call("state", {"kind": "holds", "sender": 2, "recipient": 1})
    assert refused["isError"] is True and "StatementError" in \
        refused["structuredContent"]["error"]
