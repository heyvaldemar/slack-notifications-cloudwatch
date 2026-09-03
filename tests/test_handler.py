"""Exercise the Lambda handler without touching Slack.

Runs the four cases that matter: an alarm firing, an alarm resolving, an alarm
being registered, and a transition that carries no news. The HTTP layer is
replaced with a stub, so this proves the payload is built and the outcome is
decided correctly, not that Slack is reachable.
"""

import importlib.util
import json
import os
import pathlib
import sys

os.environ.setdefault("SLACK_WEBHOOK_URL", "https://hooks.slack.example/not-called")

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("handler", ROOT / "slack-notifications-cloudwatch.py")
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)


class Response:
    def __init__(self, status=200, data=b"ok"):
        self.status = status
        self.data = data


class StubHttp:
    """Records what would have been posted."""

    def __init__(self, status=200):
        self.status = status
        self.calls = []

    def request(self, method, url, body=None, headers=None, retries=None):
        self.calls.append({"method": method, "url": url, "body": json.loads(body.decode())})
        return Response(self.status)


def sns_event(old_state, new_state, dimensions=None):
    message = {
        "AlarmName": "cpu-high",
        "AlarmDescription": "CPU above 90 percent for 5 minutes",
        "NewStateReason": "Threshold Crossed",
        "Region": "EU (Frankfurt)",
        "NewStateValue": new_state,
        "OldStateValue": old_state,
        "Trigger": {"Dimensions": dimensions if dimensions is not None else [{"value": "i-0123456789abcdef0"}]},
    }
    return {"Records": [{"Sns": {"Message": json.dumps(message)}}]}


def check(name, condition):
    print(f"  {'PASS' if condition else 'FAIL'}: {name}")
    if not condition:
        sys.exit(1)


def main():
    print("=== alarm fires")
    handler.http = StubHttp()
    result = handler.lambda_handler(sns_event("OK", "ALARM"), None)
    check("one message posted", len(handler.http.calls) == 1)
    check("status returned", result["statusCode"] == 200)
    check("headline names the alarm", "cpu-high" in json.dumps(handler.http.calls[0]["body"]))

    print("=== alarm resolves")
    handler.http = StubHttp()
    handler.lambda_handler(sns_event("ALARM", "OK"), None)
    check("one message posted", len(handler.http.calls) == 1)
    check("says resolved", "resolved" in json.dumps(handler.http.calls[0]["body"]))

    print("=== alarm registered")
    handler.http = StubHttp()
    handler.lambda_handler(sns_event("INSUFFICIENT_DATA", "OK"), None)
    check("one message posted", len(handler.http.calls) == 1)

    print("=== transition with no news")
    handler.http = StubHttp()
    result = handler.lambda_handler(sns_event("ALARM", "INSUFFICIENT_DATA"), None)
    check("nothing posted", len(handler.http.calls) == 0)
    check("reported as skipped", "skipped" in result)

    print("=== composite alarm without dimensions")
    handler.http = StubHttp()
    handler.lambda_handler(sns_event("OK", "ALARM", dimensions=[]), None)
    check("still posts", len(handler.http.calls) == 1)

    print("=== Slack rejects the message")
    handler.http = StubHttp(status=403)
    try:
        handler.lambda_handler(sns_event("OK", "ALARM"), None)
        check("raises on a non-200 answer", False)
    except RuntimeError:
        check("raises on a non-200 answer", True)

    print("all checks passed")


if __name__ == "__main__":
    main()
