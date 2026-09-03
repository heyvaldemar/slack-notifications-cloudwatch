# Security Policy

## Supported versions

| Version                                        | Status             |
|------------------------------------------------|--------------------|
| Current `main` and the latest tagged release   | :white_check_mark: |
| Older tags                                     | :x:                |

Fixes land on `main` and ship as a new tag; older tags are not patched in place.

## Reporting a vulnerability

Send reports to v@valdemar.ai. Encrypted email is preferred; the PGP public key is published at [heyvaldemar.com/security](https://heyvaldemar.com/security).

You can expect an acknowledgment within 7 days. This project does not operate a bounty program; researchers who submit valid, responsibly disclosed reports receive public credit in the release notes and the changelog.

Please do not open public GitHub issues for security reports.

## Running this script safely

The Slack incoming webhook URL is a secret: anyone holding it can post into your channel. It is read from the `SLACK_WEBHOOK_URL` environment variable, so it lives in the Lambda function configuration or in Secrets Manager, never in this repository. Earlier revisions carried the URL as a literal in the source, which is how webhooks end up in a public fork.

Give the function the smallest role that works: `AWSLambdaBasicExecutionRole` for logs, and nothing else. It reads its input from the SNS event and needs no AWS API calls.

GitHub Actions used by this repository are pinned by commit SHA, and CI runs on every push and weekly.
