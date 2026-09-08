import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import download_snapshots as collector


class SnapshotsTest(unittest.TestCase):
    def test_pagination(self):
        with patch.object(collector, "request_json", side_effect=[list(range(100)), [100]]) as request:
            self.assertEqual(list(collector.pages("/example")), list(range(101)))
            self.assertTrue(request.call_args.args[0].endswith("page=2"))

    def test_platforms(self):
        for name, expected in [("Miyo.dmg", "macos"), ("Miyo-mac.zip", "macos"),
                               ("Miyo.exe", "windows"), ("Miyo.AppImage", "linux"),
                               ("Miyo.deb", "linux"), ("Miyo.rpm", "linux"),
                               ("Miyo.zip", None), ("Miyo.exe.blockmap", None)]:
            self.assertEqual(collector.platform(name), expected)

    def collect(self, count=2, tag="v1.2.3", prerelease=False):
        release = {"id": 1, "tag_name": tag, "draft": False, "prerelease": prerelease}
        asset = {"id": 5, "name": "Miyo.dmg", "download_count": count, "created_at": "2026-01-01T00:00:00Z"}
        with patch.object(collector, "pages", side_effect=[[release], [asset]]) as pages:
            result = collector.collect()
            self.assertTrue(pages.call_args.args[0].endswith("/1/assets"))
            return result

    def test_channel_counter_and_identity(self):
        for tag, flag, expected in [("v1.2.3", False, "stable"), ("v1.2.3-beta.1", False, "prerelease"), ("v1.2.3", True, "prerelease")]:
            event = self.collect(tag=tag, prerelease=flag)[0]
            self.assertEqual(event["properties"]["channel"], expected)
            self.assertEqual(event["properties"]["cumulative_download_count"], 2)
            self.assertEqual(event["timestamp"], event["properties"]["observed_at"])
            self.assertFalse(event["properties"]["$process_person_profile"])
            self.assertNotEqual(event["uuid"], self.collect()[0]["uuid"])

    def test_bad_or_empty_source(self):
        for count in [-1, True, "2"]:
            with self.assertRaises(ValueError):
                self.collect(count=count)
        with patch.object(collector, "pages", return_value=[]), self.assertRaises(ValueError):
            collector.collect()
        with patch.object(collector, "request_json", return_value={"message": "error"}), self.assertRaises(ValueError):
            list(collector.pages("/example"))
        with patch.object(collector, "pages", return_value=[{"draft": True}]), self.assertRaises(ValueError):
            collector.collect()

    def test_capture_allowlist(self):
        event = self.collect()[0]
        self.assertEqual(set(event), {"event", "timestamp", "uuid", "properties"})
        self.assertEqual(set(event["properties"]), {
            "distinct_id", "$process_person_profile", "product", "asset_id", "asset_kind",
            "release_tag", "platform", "channel", "cumulative_download_count",
            "asset_created_at", "observed_at", "snapshot_id", "snapshot_asset_count",
        })

    def test_multiple_releases_and_duplicate_asset(self):
        releases = [{"id": i, "tag_name": f"v1.0.{i}", "draft": False, "prerelease": False} for i in [1, 2]]
        assets = [{"id": i, "name": "Miyo.exe", "download_count": 1, "created_at": "2026-01-01T00:00:00Z"} for i in [10, 20, 30]]
        with patch.object(collector, "pages", side_effect=[releases, assets[:2], assets[2:]]):
            events = collector.collect()
            self.assertEqual(len(events), 3)
            self.assertEqual(len({event["properties"]["snapshot_id"] for event in events}), 1)
            self.assertEqual({event["properties"]["snapshot_asset_count"] for event in events}, {3})
        with patch.object(collector, "pages", side_effect=[releases, assets, assets]), self.assertRaises(ValueError):
            collector.collect()

    def test_batch_boundary_http_failure_and_dry_run(self):
        events = [self.collect()[0] for _ in range(101)]
        with patch.object(collector, "request_json", return_value={"status": 1}) as request:
            collector.upload(events, "test-project-key")
            batches = [json.loads(call.args[2])["batch"] for call in request.call_args_list]
            self.assertEqual([len(batch) for batch in batches], [100, 1])
            self.assertEqual(batches[0] + batches[1], events)
        from urllib.error import HTTPError
        with patch.object(collector, "request_json", side_effect=HTTPError("https://example.com", 503, "unavailable", {}, None)), self.assertRaises(HTTPError):
            collector.upload(events, "test-project-key")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            with patch.object(sys, "argv", ["collector", "--dry-run", "--output", str(path)]), patch.object(collector, "collect", return_value=events), patch.object(collector, "upload") as upload:
                collector.main()
                upload.assert_not_called()
                self.assertEqual(json.loads(path.read_text()), events)

    def test_replay_and_rejected_acknowledgment(self):
        events = self.collect()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            path.write_text(json.dumps(events))
            with patch.object(sys, "argv", ["collector", "--input", str(path), "--output", str(path)]), patch.object(collector, "upload") as upload:
                collector.main()
                self.assertEqual(upload.call_args.args[0], events)
        for response in [{"status": 0}, {}, "OK"]:
            with patch.object(collector, "request_json", return_value=response), self.assertRaises(ValueError):
                collector.upload(events, "test-project-key")
        with patch.object(collector, "request_json", return_value={"status": 1}) as request:
            collector.upload(events, "test-project-key")
            self.assertEqual(json.loads(request.call_args.args[2])["batch"], events)


if __name__ == "__main__":
    unittest.main()
