# CloudWatch alarms in Slack

[![Script Verification](https://github.com/heyvaldemar/slack-notifications-cloudwatch/actions/workflows/verification.yml/badge.svg?branch=main)](https://github.com/heyvaldemar/slack-notifications-cloudwatch/actions/workflows/verification.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AWS Lambda function that turns CloudWatch alarm state changes into readable Slack messages: a red header when an alarm fires, a green one when it clears, with the reason, the region and the instance in Block Kit blocks rather than a wall of JSON.

## Getting started

1. **Create a Slack incoming webhook** for the channel that should receive alarms.
2. **Create a Lambda function** on the Python 3.13 runtime and paste `slack-notifications-cloudwatch.py` in as the handler source. No dependency layer is needed: `urllib3` ships with the runtime.
3. **Set the environment variable** `SLACK_WEBHOOK_URL` to the webhook URL. The function reads it at import time and fails fast if it is missing.
4. **Subscribe the function to the SNS topic** your CloudWatch alarms notify.
5. **Give the function the `AWSLambdaBasicExecutionRole`** and nothing else. It reads the SNS event and calls no AWS API.

### What success looks like

Fire a test alarm, or publish a recorded event to the topic. Slack shows a message headed `:red_circle: Alarm: cpu-high was activated`, and the function log carries one line:

```json
{"alarm": "cpu-high", "transition": ["OK", "ALARM"], "status_code": 200}
```

### Common first-deploy issues

- **The function errors with `KeyError: 'SLACK_WEBHOOK_URL'`.** The environment variable is not set. That is deliberate: a webhook missing at deploy time is better than alerting that silently goes nowhere.
- **Slack returns 403 and the function reports an error.** The webhook was revoked or belongs to another workspace. Earlier revisions printed the status and continued, so alerting stayed dead until someone noticed the quiet.
- **Nothing arrives for some state changes.** Transitions other than the three that carry news (registered, activated, resolved) are logged and skipped on purpose, for example `ALARM` to `INSUFFICIENT_DATA` when an instance is terminated.

## Alarm on the alerter

The function raises when Slack rejects a message, which surfaces as the Lambda `Errors` metric. Put a CloudWatch alarm on that metric, notifying a different channel or an email address. An alerting path that cannot report its own failure is a single point of silence.

## Testing

`tests/test_handler.py` exercises the handler against recorded SNS events with the HTTP layer stubbed: each alarm transition, the skip path, a composite alarm that carries no dimensions, and a Slack rejection. The [Script Verification](https://github.com/heyvaldemar/slack-notifications-cloudwatch/actions/workflows/verification.yml?query=branch%3Amain) workflow runs Ruff and those tests on every push, pull request, and weekly.

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.example/not-called python3 tests/test_handler.py
```

---

## About the maintainer

<div align="center">

**Maintained by [Vladimir Mikhalev](https://github.com/heyvaldemar)** · Docker Captain · IBM Champion · AWS Community Builder

[YouTube](https://www.youtube.com/channel/UCf85kQ0u1sYTTTyKVpxrlyQ?sub_confirmation=1) · [Blog](https://heyvaldemar.com) · [LinkedIn](https://www.linkedin.com/in/heyvaldemar/)

</div>
