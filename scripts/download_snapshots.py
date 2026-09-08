"""Collect cumulative GitHub asset counters; replay the saved events to PostHog."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen
import uuid

REPOSITORY = "Brevilabs/miyo-releases"
ENDPOINT = "https://us.i.posthog.com/batch/"


def request_json(url, headers, data=None):
    with urlopen(Request(url, data=data, headers=headers), timeout=60) as response:
        return json.load(response)


def pages(path):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    page = 1
    while True:
        rows = request_json(f"https://api.github.com{path}?per_page=100&page={page}", headers)
        if not isinstance(rows, list):
            raise ValueError("GitHub did not return a list")
        yield from rows
        if len(rows) < 100:
            return
        page += 1


def platform(name):
    name = name.lower()
    if name.endswith((".dmg", "-mac.zip", ".mac.zip")):
        return "macos"
    if name.endswith(".exe"):
        return "windows"
    if name.endswith((".appimage", ".deb", ".rpm")):
        return "linux"
    return None


def collect():
    repo = REPOSITORY
    events = []
    seen = set()
    for release in pages(f"/repos/{repo}/releases"):
        if release["draft"]:
            continue
        tag = release["tag_name"]
        channel = "prerelease" if release["prerelease"] or re.search(r"\d\.\d\.\d+-", tag) else "stable"
        # The dedicated endpoint guarantees complete asset pagination.
        for asset in pages(f"/repos/{repo}/releases/{release['id']}/assets"):
            os_name = platform(asset["name"])
            if os_name is None:
                continue
            count, asset_id = asset["download_count"], asset["id"]
            if type(count) is not int or count < 0 or type(asset_id) is not int or asset_id <= 0:
                raise ValueError("Invalid asset counter or identity")
            if asset_id in seen:
                raise ValueError("Duplicate asset; release list changed during collection")
            seen.add(asset_id)
            observed = datetime.now(timezone.utc).isoformat()
            events.append({
                "event": "release_download_snapshot", "timestamp": observed,
                "uuid": str(uuid.uuid4()), "properties": {
                    "distinct_id": f"github:{repo}", "$process_person_profile": False,
                    "product": "miyo", "asset_id": asset_id,
                    "asset_kind": "mac_zip" if asset["name"].lower().endswith(".zip") else asset["name"].rsplit(".", 1)[-1].lower(),
                    "release_tag": tag, "platform": os_name, "channel": channel,
                    "cumulative_download_count": count, "asset_created_at": asset["created_at"],
                    "observed_at": observed,
                },
            })
    if not events:
        raise ValueError("No distribution assets found; refusing an empty snapshot")
    snapshot_id = str(uuid.uuid4())
    for event in events:
        event["properties"].update(snapshot_id=snapshot_id, snapshot_asset_count=len(events))
    return events


def upload(events, token):
    if not token or not events:
        raise ValueError("A project token and nonempty snapshot are required")
    for offset in range(0, len(events), 100):
        payload = json.dumps({"api_key": token, "batch": events[offset:offset + 100]}).encode()
        result = request_json(ENDPOINT, {"Content-Type": "application/json"}, payload)
        if not isinstance(result, dict) or result.get("status") != 1:
            raise ValueError("PostHog did not acknowledge the batch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="download-snapshot.json")
    parser.add_argument("--input", help="Replay saved events without recollecting counters")
    parser.add_argument("--dry-run", action="store_true", help="Save only; no PostHog request")
    args = parser.parse_args()
    events = json.loads(Path(args.input).read_text()) if args.input else collect()
    Path(args.output).write_text(json.dumps(events, indent=2) + "\n")
    if not args.dry_run:
        upload(events, os.environ.get("POSTHOG_PROJECT_TOKEN", ""))
    print(f"Saved {len(events)} asset observations to {args.output}")


if __name__ == "__main__":
    main()
