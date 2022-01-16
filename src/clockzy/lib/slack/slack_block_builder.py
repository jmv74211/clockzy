""""Block builder module for slack messages"""


def write_slack_divider():
    """Write a slack divider block.

    Returns:
        dict: Block message
    """
    return {
        "type": "divider"
    }


def write_slack_header(message):
    """Write a slack header block.

    Returns:
        dict: Block message
    """
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": message
        }
    }


def write_slack_markdown(message, image_url=None, alt_text='generic'):
    """Write a slack markdown section.

    Args:
        message (str): Message
        image_url (str): Image URL.
        alt_text (str): Image alternative text.

    Returns:
        dict: Block message
    """
    block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": message
        }
    }

    if image_url:
        block['accessory'] = {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text
        }

    return block
