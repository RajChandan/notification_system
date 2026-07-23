#!/usr/bin/env python3
import argparse
import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API_URL = "http://localhost:8000/api/v1/notifications/"

SAMPLE_PAYLOAD: Dict[str, Any] = {
    "user_id": "user_123",
    "template_type": "transactional",
    "channel": "email",
    "recipient": "test@gmail.com",
    "variables": {"name": "Chandan"},
    "metadata": {"subject": "Welcome"},
    "priority": "medium",
}


def send_notification(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        api_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request) as response:
        response_body = response.read().decode("utf-8")
        return {
            "status_code": response.getcode(),
            "body": json.loads(response_body) if response_body else None,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a sample notification request.")
    parser.add_argument(
        "--url",
        default=DEFAULT_API_URL,
        help="Notification API URL (default: %(default)s)",
    )
    args = parser.parse_args()

    print(f"Sending request to: {args.url}")
    print("Payload:")
    print(json.dumps(SAMPLE_PAYLOAD, indent=2))

    try:
        result = send_notification(args.url, SAMPLE_PAYLOAD)
        print("\nResponse status:", result["status_code"])
        print("Response body:")
        print(json.dumps(result["body"], indent=2))
    except HTTPError as err:
        print(f"HTTP error: {err.code} {err.reason}")
        print(err.read().decode("utf-8"))
    except URLError as err:
        print(f"Failed to connect: {err.reason}")
    except ValueError as err:
        print(f"Failed to decode JSON response: {err}")
