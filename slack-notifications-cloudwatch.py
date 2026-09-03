"""Post CloudWatch alarm state changes to Slack.

Deploy as an AWS Lambda function subscribed to the SNS topic your CloudWatch
alarms notify. The Slack incoming webhook URL is read from the SLACK_WEBHOOK_URL
environment variable, so the secret lives in the function configuration (or
Secrets Manager) instead of in this file.

Runtime: Python 3.12+. urllib3 ships with the Lambda Python runtime, so the
function needs no dependency layer.
"""

import json
import os

import urllib3

SLACK_URL = os.environ["SLACK_WEBHOOK_URL"]
http = urllib3.PoolManager()

def get_alarm_attributes(sns_message):
    alarm = dict()

    alarm['name'] = sns_message['AlarmName']
    alarm['description'] = sns_message['AlarmDescription']
    alarm['reason'] = sns_message['NewStateReason']
    alarm['region'] = sns_message['Region']
    dimensions = sns_message.get('Trigger', {}).get('Dimensions') or []
    alarm['instance_id'] = dimensions[0]['value'] if dimensions else 'n/a'
    alarm['state'] = sns_message['NewStateValue']
    alarm['previous_state'] = sns_message['OldStateValue']

    return alarm

def register_alarm(alarm):
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":warning: " + alarm['name'] + " alarm was registered"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_" + alarm['description'] + "_"
                },
                "block_id": "text1"
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Region: *" + alarm['region'] + "*"
                    }
                ]
            }
        ]
    }

def activate_alarm(alarm):
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":red_circle: Alarm: " + alarm['name'],
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_" + alarm['reason'] + "_"
                },
                "block_id": "text1"
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Region: *" + alarm['region'] + "*"
                    }
                ]
            }
        ]
    }

def resolve_alarm(alarm):
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":large_green_circle: Alarm: " + alarm['name'] + " was resolved",
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_" + alarm['reason'] + "_"
                },
                "block_id": "text1"
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Region: *" + alarm['region'] + "*"
                    }
                ]
            }
        ]
    }

def lambda_handler(event, context):
    """Turn one SNS record into one Slack message."""
    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
    alarm = get_alarm_attributes(sns_message)

    transition = (alarm["previous_state"], alarm["state"])
    if transition == ("INSUFFICIENT_DATA", "OK"):
        msg = register_alarm(alarm)
    elif transition == ("OK", "ALARM"):
        msg = activate_alarm(alarm)
    elif transition == ("ALARM", "OK"):
        msg = resolve_alarm(alarm)
    else:
        # Every other transition (ALARM to INSUFFICIENT_DATA when an instance
        # goes away, or a repeated notification for the same state) carries no
        # news for a chat channel. The old version posted an empty message here.
        print({"skipped": transition, "alarm": alarm["name"]})
        return {"statusCode": 200, "skipped": f"{transition[0]} -> {transition[1]}"}

    response = http.request(
        "POST",
        SLACK_URL,
        body=json.dumps(msg).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        retries=urllib3.Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]),
    )

    # Slack answers 200 with the body "ok". Anything else is a failure worth a
    # Lambda error metric: a silent 403 from a rotated webhook is how alerting
    # dies without anyone noticing.
    if response.status != 200:
        raise RuntimeError(f"Slack rejected the message: {response.status} {response.data.decode('utf-8', 'replace')}")

    print({"alarm": alarm["name"], "transition": transition, "status_code": response.status})
    return {"statusCode": response.status}
