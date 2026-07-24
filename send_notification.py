#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

DEFAULT_API_URL = "http://localhost:8000/api/v1/notifications/"


def build_sample_payloads() -> List[Dict[str, Any]]:
    run_id = uuid4().hex[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return [
        {
            "user_id": f"user_{run_id}_1",
            "template_type": "transactional",
            "channel": "email",
            "recipient": f"test+{run_id}+1@gmail.com",
            "variables": {
                "name": f"Chandan-{run_id}",
                "order_id": f"ORD-{timestamp}-1",
            },
            "metadata": {"subject": f"Welcome to our platform ({run_id})"},
            "priority": "medium",
        },
        {
            "user_id": f"user_{run_id}_2",
            "template_type": "transactional",
            "channel": "sms",
            "recipient": f"+1555{timestamp[-6:]}{run_id[:4]}",
            "variables": {
                "otp": f"{int(timestamp[-4:]) + 1000}",
                "minutes": str((int(timestamp[-2:]) % 5) + 1),
            },
            "metadata": {"sender": f"demo-service-{run_id}"},
            "priority": "high",
        },
        {
            "user_id": f"user_{run_id}_3",
            "template_type": "transactional",
            "channel": "push",
            "recipient": f"device-{run_id}-abc",
            "variables": {"order_id": f"ORD-{timestamp}-2"},
            "metadata": {"title": f"Order shipped ({run_id})"},
            "priority": "medium",
        },
        {
            "user_id": f"user_{run_id}_4",
            "template_type": "promotional",
            "channel": "email",
            "recipient": f"promo+{run_id}@example.com",
            "variables": {
                "name": f"Asha-{run_id}",
                "discount": str((int(timestamp[-2:]) % 20) + 10),
            },
            "metadata": {"subject": f"Special offer ({run_id})"},
            "priority": "low",
        },
    ]


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
    parser = argparse.ArgumentParser(description="Send sample notification requests.")
    parser.add_argument(
        "--url",
        default=DEFAULT_API_URL,
        help="Notification API URL (default: %(default)s)",
    )
    args = parser.parse_args()

    payloads = build_sample_payloads()
    print(f"Sending {len(payloads)} requests to: {args.url}")

    for index, payload in enumerate(payloads, start=1):
        print(f"\n[{index}/{len(payloads)}] Payload:")
        print(json.dumps(payload, indent=2))

        try:
            result = send_notification(args.url, payload)
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
