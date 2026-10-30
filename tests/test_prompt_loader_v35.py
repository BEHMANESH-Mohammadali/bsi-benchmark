from bsi_benchmark import prompt_loader


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.encoding = None

    def raise_for_status(self):
        return None


def test_load_canonical_bsi_v35_fetches_master_and_all_authoritative_refs(monkeypatch):
    requested = []

    def fake_get(url, timeout):
        requested.append(url)
        return FakeResponse("# BSI v3.5 source\n")

    monkeypatch.setattr(prompt_loader.requests, "get", fake_get)

    prompt, provenance = prompt_loader.load_canonical_bsi_v35(
        repository="owner/repository",
        ref="test-branch",
    )

    assert "BSI v3.5 source" in prompt
    assert "{title}" in prompt
    assert "{abstract}" in prompt
    assert "{full_text}" in prompt
    assert len(requested) == 1 + len(prompt_loader.AUTHORITATIVE_REFERENCES)
    assert provenance["framework_version"] == "3.5"
    assert provenance["ref"] == "test-branch"
    assert provenance["master_prompt"]["sha256"]
    assert provenance["package_sha256"]
    assert set(provenance["authoritative_references"]) == set(
        prompt_loader.AUTHORITATIVE_REFERENCES
    )


def test_load_canonical_bsi_v35_fails_if_a_reference_is_missing(monkeypatch):
    calls = 0

    def fake_get(url, timeout):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise prompt_loader.requests.HTTPError("404")
        return FakeResponse("# source\n")

    monkeypatch.setattr(prompt_loader.requests, "get", fake_get)

    try:
        prompt_loader.load_canonical_bsi_v35(
            repository="owner/repository",
            ref="test-branch",
        )
    except prompt_loader.requests.HTTPError:
        pass
    else:
        raise AssertionError("Missing authoritative reference must fail closed")
