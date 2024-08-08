import requests


def send_pushover_notification(user_key, api_token, message, title="Notification"):
    """
    Send a notification using Pushover.

    :param user_key: Pushover user key
    :param api_token: Pushover API token
    :param message: Message to send
    :param title: Title of the notification (default is "Notification")
    :return: Response status
    """
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": api_token,
        "user": user_key,
        "message": message,
        "title": title
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return None