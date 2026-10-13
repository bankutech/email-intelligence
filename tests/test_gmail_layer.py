"""Gmail layer tested against a fake `service` object (no network)."""
import httplib2
import pytest
from googleapiclient.errors import HttpError

from app.gmail.actions import GmailActions
from app.gmail.client import GmailAuthError, GmailClient, GmailError, GmailNotFound, GmailTransientError
from app.gmail.reader import GmailReader




class Req:
    def __init__(self, result=None, exc=None):
        self.result, self.exc = result, exc

    def execute(self):
        if self.exc:
            raise self.exc
        return self.result


def http_error(status, body=b"{}"):
    return HttpError(httplib2.Response({"status": status}), body)


class FakeService:
    """Minimal users().X().Y() chain recording calls."""

    def __init__(self):
        self.label_store = [{"id": "L1", "name": "INBOX"}]
        self.history_pages = []
        self.modified = []
        self.history_exc = None
        self.created = []

    def users(self): return self
    def getProfile(self, **kw): return Req({"historyId": "500"})
    def history(self): return self
    def messages(self): return self

    def list(self, **kw):
        if "startHistoryId" in kw:
            return Req(exc=self.history_exc) if self.history_exc else Req(self.history_pages.pop(0))
        return Req({"messages": [{"id": "r1"}, {"id": "r2"}]})

    def modify(self, userId, id, body):
        self.modified.append((id, body))
        return Req({})


class LabelsService(FakeService):
    def labels(self): return _Labels(self)


class _Labels:
    def __init__(self, svc): self.svc = svc
    def list(self, **kw): return Req({"labels": list(self.svc.label_store)})
    def create(self, userId, body):
        new = {"id": f"L{len(self.svc.label_store) + 1}", "name": body["name"]}
        self.svc.label_store.append(new)
        self.svc.created.append(body["name"])
        return Req(new)


class FakeClient(GmailClient):
    def __init__(self, svc):
        super().__init__("c.json", "t.json")
        self._service = svc


def test_discover_first_run_scans_recent_and_stores_history(db):
    r = GmailReader(FakeClient(FakeService()), db)
    assert r.discover() == (["r1", "r2"], "500")


def test_discover_uses_history_pagination_and_inbox_filter(db):
    svc = FakeService()
    svc.history_pages = [
        {"history": [{"messagesAdded": [{"message": {"id": "a", "labelIds": ["INBOX"]}},
                                        {"message": {"id": "sent1", "labelIds": ["SENT"]}}]}],
         "historyId": "601", "nextPageToken": "p2"},
        {"history": [{"messagesAdded": [{"message": {"id": "b", "labelIds": ["INBOX"]}},
                                        {"message": {"id": "a", "labelIds": ["INBOX"]}}]}], "historyId": "650"},
    ]
    assert GmailReader(FakeClient(svc), db).discover("600") == (["a", "b"], "650")


def test_discover_falls_back_when_history_expired(db):
    svc = FakeService()
    svc.history_exc = http_error(404)
    r = GmailReader(FakeClient(svc), db)
    assert r.discover("1") == (["r1", "r2"], "500")


def test_labels_created_once_then_cached_and_modify_payload():
    svc = LabelsService()
    actions = GmailActions(FakeClient(svc))
    assert actions.apply("m1", ["AI-URGENT", "AI-QUARANTINE", "SPAM"], remove_inbox=True) is True
    actions.apply("m2", ["AI-URGENT"])
    assert svc.created == ["AI-URGENT", "AI-QUARANTINE"]                    # no duplicate creation
    assert svc.modified[0][1] == {"addLabelIds": ["L2", "L3", "SPAM"], "removeLabelIds": ["INBOX"]}
    assert svc.modified[1][1]["removeLabelIds"] == []


@pytest.mark.parametrize("status,body,expected", [
    (401, b"{}", GmailAuthError), (404, b"{}", GmailNotFound), (429, b"{}", GmailTransientError),
    (503, b"{}", GmailTransientError), (403, b'{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}', GmailTransientError),
    (403, b'{"error":{"errors":[{"reason":"insufficientPermissions"}]}}', GmailError),
])
def test_http_errors_are_mapped(status, body, expected):
    client = FakeClient(None)
    client._service = type("S", (), {})()
    with pytest.raises(expected) as info:
        client.call(lambda s: Req(exc=http_error(status, body)))
    if expected is GmailError:
        assert type(info.value) is GmailError            # permanent: not retried as transient


def test_network_errors_are_transient():
    client = FakeClient(object())
    with pytest.raises(GmailTransientError):
        client.call(lambda s: Req(exc=ConnectionResetError("reset")))


def test_missing_token_gives_actionable_auth_error(tmp_path):
    with pytest.raises(GmailAuthError, match="python main.py auth"):
        GmailClient("c.json", str(tmp_path / "nope.json")).service()
