import requests


def send_pushover_notification(user_key, api_token, message, title="Notification", image_path=None):
    """
    Send a notification using Pushover with an optional image.

    :param user_key: Pushover user key
    :param api_token: Pushover API token
    :param message: Message to send
    :param title: Title of the notification (default is "Notification")
    :param image_path: Path to the image file to send (default is None)
    :return: Response status
    """
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": api_token,
        "user": user_key,
        "message": message,
        "title": title
    }

    files = None
    if image_path:
        files = {'attachment': open(image_path, 'rb')}

    try:
        response = requests.post(url, data=payload, files=files)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return None
    finally:
        # Close the file if it was opened
        if files:
            files['attachment'].close()
