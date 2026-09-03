# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_(no unreleased changes yet)_

## [1.0.0] - 2026-09-03

### Fixed

- **A transition with no news posted an empty message.** Any state change
  outside the three handled cases fell through with `msg` still an empty
  string, and that empty payload was sent to Slack. Those transitions are now
  logged and skipped.
- **A rejected message looked like a delivered one.** The response status was
  printed and then ignored, so a rotated webhook returning 403 left alerting
  silently dead. The handler now raises, which surfaces as a Lambda error
  metric you can alarm on.
- **A composite or metric-math alarm crashed the function.** The first trigger
  dimension was read unconditionally, and those alarms carry none.

### Added

- **The webhook URL comes from the `SLACK_WEBHOOK_URL` environment variable.**
  It used to be a literal in the source, which is how a webhook ends up in a
  public fork.
- Retries with backoff on 429 and 5xx answers from Slack.
- **`tests/test_handler.py`**: six cases against recorded SNS events with the
  HTTP layer stubbed, covering each alarm transition, the skip path, a
  dimensionless alarm, and a Slack rejection. CI runs it on every push.

[Unreleased]: https://github.com/heyvaldemar/slack-notifications-cloudwatch/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/heyvaldemar/slack-notifications-cloudwatch/releases/tag/v1.0.0
