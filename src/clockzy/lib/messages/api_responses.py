"""API RESPONSE MESSAGES"""

ALIVE_MESSAGE = 'Alive'
NON_SLACK_REQUEST = 'Unauthorized. Only slack app can use this API.'
BAD_SLACK_HEADERS_REQUEST = f"{NON_SLACK_REQUEST} Missing 'X-Slack-Signature' and 'X-Slack-Request-Timestamp headers'"
BAD_SLACK_TIMESTAMP_REQUEST = f"{NON_SLACK_REQUEST} Bad timestamp"
