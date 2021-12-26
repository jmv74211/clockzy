import urllib.parse

def decode_slack_args(data):
    """Function to decode slack response args from x=1&y=2&z=3 format to {x:1, y:2, z:3}

    Args:
        data (str): Slack string args to decode

    Returns
        dict: Slack args in dict format
    """
    data = urllib.parse.unquote(data)
    elements = [pair_value for item in data.split('&') for pair_value in item.split('=')]
    return dict(zip(elements[0::2], elements[1::2]))
