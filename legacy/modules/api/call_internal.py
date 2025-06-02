import requests
from requests import Response

from modules.api.server_ip import server_ip

import urllib
import urllib.request
import urllib.error
import gradio as gr
import json

def send_request(url, data, method="POST", header=None):
    """Sends a request to the specified URL with the given data.

    Args:
        url: The URL to send the request to.
        data: The data to send with the request.

    Returns:
        The response from the server, or None if an error occurred.
    """
    if header is None:
        header = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(
            f"http://{server_ip.ip}:{server_ip.port}"+url,
            headers=header,
            data=json.dumps(data).encode("utf-8"),
            method=method,
        )

        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} - {e.reason}")
        raise gr.Error(f"HTTP error: {e.code} - {e.reason}.\nDid you launch SD-WebUI with --api argument?")
    except urllib.error.URLError as e:
        print(f"URL error: {e.reason}.\nre-check custom IP and try again.")
        return None

def get_request_with_status(url, data, *, header=None) -> Response:
    if header is None:
        header = {"Content-Type": "application/json"}

    return requests.get(
        f"http://{server_ip.ip}:{server_ip.port}"+url,
        headers=header,
        data=json.dumps(data).encode("utf-8")
    )