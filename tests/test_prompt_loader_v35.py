from bsi_benchmark import prompt_loader


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.body = body
        self.status_code = status_code
        self.url = "https://example.invalid/test"

    @property
    def ok(self):
        return 200 <= self.status_code < 300


class FakeHttpClient:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return FakeResponse("# BSI v3.5 source\n")


def test_load_canonical_bsi_v35_fetches_master_and_all_authoritative_refs(monkeypatch):
    client = FakeHttpClient()
    monkeypatch.setattr(prompt_loader, "HttpClient", lambda: client)

    prompt, provenance = prompt_loader.load_canonical_bsi_v35(
        repository="owner/repository",
        ref="test-branch",
    )

    assert "BSI v3.5 source" in prompt
    assert "{title}" in prompt
    assert "{abstract}" in prompt
    assert "{full_text}" in prompt
    assert len(client.requested) == 1 + len(prompt_loader.AUTHORITATIVE_REFERENCES)
    assert provenance["framework_version"] == "3.5"
    assert provenance["ref"] == "test-branch"
    assert provenance["master_prompt"]["sha256"]
    assert provenance["package_sha256"]
    assert set(provenance["authoritative_references"]) == set(
        prompt_loader.AUTHORITATIVE_REFERENCES
    )


def test_load_canonical_bsi_v35_fails_if_a_reference_is_missing(monkeypatch):
    client = FakeHttpClient(
        [FakeResponse("# source\n"), FakeResponse("# source\n"),
         FakeResponse("Not Found", status_code=404)]
    )
    monkeypatch.setattr(prompt_loader, "HttpClient", lambda: client)

    try:
        prompt_loader.load_canonical_bsi_v35(
            repository="owner/repository",
            ref="test-branch",
        )
    except RuntimeError as exc:
        assert "HTTP 404" in str(exc)
    else:
        raise AssertionError("Missing authoritative reference must fail closed")
