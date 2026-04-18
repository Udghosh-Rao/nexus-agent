import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, Optional

import requests
from langchain_core.tools import tool

from shared_store import BASE64_STORE, url_time

cache = defaultdict(int)
RETRY_LIMIT = 4


@tool
def post_request(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Send an HTTP POST request. Handles Base64 placeholder resolution,
    retry logic, and next-URL chaining for sequential task workflows.

    Parameters
    ----------
    url     : str               Endpoint to POST to.
    payload : Dict[str, Any]    JSON-serializable request body.
    headers : Dict, optional    HTTP headers (defaults to JSON content-type).

    Returns
    -------
    Any  Server response (parsed JSON) or raw text on failure.
    """
    ans = payload.get("answer", "")
    if isinstance(ans, str) and ans.startswith("BASE64_KEY:"):
        key = ans.split(":", 1)[1]
        payload["answer"] = BASE64_STORE.get(key, ans)

    headers = headers or {"Content-Type": "application/json"}

    try:
        cur_url = os.getenv("url", "")
        cache[cur_url] += 1

        preview = {
            "answer": str(payload.get("answer", ""))[:80] + "...",
            "email": payload.get("email", ""),
        }
        print(f"\nPOST → {url}\nPayload preview: {json.dumps(preview, indent=2)}")

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f"Response:\n{json.dumps(data, indent=2)}")

        next_url = data.get("url")
        if not next_url:
            return "Tasks completed"

        if next_url not in url_time:
            url_time[next_url] = time.time()

        correct = data.get("correct")
        delay = time.time() - url_time.get(cur_url, time.time())
        offset = os.getenv("offset", "0")

        if not correct:
            cur_time = time.time()
            timeout = (
                cache[cur_url] >= RETRY_LIMIT
                or delay >= 180
                or (offset != "0" and (cur_time - float(offset)) > 90)
            )
            if timeout:
                print("Timeout reached — moving to next question.")
                data = {"url": next_url}
            else:
                print("Wrong answer — retrying.")
                os.environ["offset"] = str(url_time.get(next_url, time.time()))
                data["url"] = cur_url
                data["message"] = "Retry"

        forward_url = data.get("url", "")
        os.environ["url"] = forward_url
        if forward_url == next_url:
            os.environ["offset"] = "0"

        return data

    except requests.HTTPError as e:
        try:
            err = e.response.json()
        except ValueError:
            err = e.response.text
        print("HTTP Error:", err)
        return err
    except Exception as e:
        print("Unexpected error:", e)
        return str(e)
