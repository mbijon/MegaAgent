import config
import llm


def test_build_request_body_without_web_search(monkeypatch):
    monkeypatch.setattr(config, "enable_web_search", False)
    monkeypatch.setattr(config, "temperature", None)
    llm.written_files.clear()
    body = llm.build_request_body([
        {"role": "user", "content": "ping"}
    ], enable_tools=True, agent_name="Bob", use_web_search=False)

    assert "functions" in body
    assert body["model"] == config.model
    assert "tools" not in body
    assert "temperature" not in body


def test_build_request_body_honors_configured_temperature(monkeypatch):
    monkeypatch.setattr(config, "enable_web_search", False)
    monkeypatch.setattr(config, "temperature", 1.25)

    body = llm.build_request_body([
        {"role": "user", "content": "ping"}
    ], enable_tools=False, agent_name="Bob", use_web_search=False)

    assert body["temperature"] == 1.25


def test_build_request_body_with_web_search(monkeypatch):
    monkeypatch.setattr(config, "enable_web_search", True)
    monkeypatch.setattr(config, "web_search_provider", "gpt-5-web")
    monkeypatch.setattr(config, "web_search_model", "gpt-5.1-search")
    monkeypatch.setattr(config, "temperature", None)

    body = llm.build_request_body([
        {"role": "user", "content": "ping"}
    ], enable_tools=False, use_web_search=None)

    assert "functions" not in body
    assert body["tools"][0]["provider"] == {
        "type": "gpt-5-web",
        "model": "gpt-5.1-search",
    }


def test_get_llm_response_with_web_search(monkeypatch):
    llm.input_token = 0
    llm.output_token = 0
    monkeypatch.setattr(config, "temperature", None)

    class DummyResponse:
        def json(self):
            return {
                "choices": [
                    {"message": {"content": "ok"}}
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            }

    captured = {}

    def fake_post(url, headers, json):  # noqa: A002 - keep parity with requests
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return DummyResponse()

    monkeypatch.setattr(llm.requests, "post", fake_post)

    response = llm.get_llm_response(
        [{"role": "user", "content": "hello"}],
        enable_tools=False,
        agent_name="Tester",
        use_web_search=True,
    )

    assert response["choices"][0]["message"]["content"] == "ok"
    assert captured["json"]["tools"][0]["provider"]["type"] == config.web_search_provider
    assert llm.input_token == 3
    assert llm.output_token == 2
