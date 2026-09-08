This repo is used for hosting public releases of Miyo.

## miyo agent skill

`skills/miyo` plus the `.claude-plugin` manifests make this repo a Claude Code
plugin marketplace for the miyo skill:

```bash
claude plugin marketplace add Brevilabs/miyo-releases
claude plugin install miyo@miyo-releases
```

The skill's source of truth is `skills/miyo` in the main
[Brevilabs/miyo](https://github.com/Brevilabs/miyo) repo, where it evolves
together with the `miyo` CLI it documents. Each Miyo release publishes it here
automatically (`scripts/publish-agent-skill.sh` in that repo) and stamps the
release version into `.claude-plugin/plugin.json`.

**Don't edit `skills/miyo` in this repo** — changes here are overwritten by
the next release publish. Change the skill in Brevilabs/miyo instead.

## Daily download snapshots

[Download snapshots](.github/workflows/download-snapshots.yml) reads every non-draft
release and every asset page in **Brevilabs/miyo-releases**, daily at 16:17 UTC
(09:17 PDT / 08:17 PST; GitHub schedules can be delayed), or via Run workflow.
Configure repository secret `POSTHOG_PROJECT_TOKEN` with the existing US PostHog
project's ingestion key. GitHub reads use the workflow's read-only `GITHUB_TOKEN`.
Pull requests run the standard-library tests without collecting or ingesting.

Each `.dmg`, `.exe`, `.AppImage`, `.deb`, `.rpm`, or `-mac.zip`/`.mac.zip` asset
produces one `release_download_snapshot` event at its actual observation time.
Properties are `product=miyo`, `asset_id`, `release_tag`, `platform`, `asset_kind`,
`channel` (`stable` or `prerelease`), `cumulative_download_count`, `observed_at`,
`asset_created_at`, `snapshot_id`, and `snapshot_asset_count`. GitHub's prerelease flag or a semver prerelease tag marks
`prerelease`. Generic ZIPs and metadata files are excluded. Events use synthetic
`distinct_id=github:Brevilabs/miyo-releases` and `$process_person_profile=false`;
no person data, raw URLs, or arbitrary GitHub fields are sent. Only the fixed
US capture endpoint `https://us.i.posthog.com/batch/` receives events.

The primary production series should filter stable DMG, EXE, and AppImage
installers; keep `mac_zip` separate because it includes updater downloads.
Other package kinds and prereleases are separate series. These counters measure
asset downloads, not unique users, installations, activation, or web referrals.
Compute differences between consecutive observations **per asset ID**. A first
observation is a lifetime baseline, not that day's downloads; only attribute a
new asset's initial counter to an interval when its creation time falls within
that interval. A missing run is unknown, not zero; a later difference spans the
gap. Negative differences require investigation, not silent clamping. There is
no historical daily backfill or access to the separate alpha repository.

The workflow saves a token-free JSON artifact before ingestion (90-day retention).
For inspection, run `python3 scripts/download_snapshots.py --dry-run` locally;
set `GITHUB_TOKEN` if needed for API limits. Tests: `python3 -m unittest discover
-s tests -v`. Collection failures or zero eligible assets fail the run before
upload. PostHog must return a positive batch acknowledgment; this confirms
acceptance, not downstream query visibility.

To retry ingestion after a failed or partially accepted upload, download that
run's artifact and run `python3 scripts/download_snapshots.py --input
/path/to/download-snapshot.json` with `POSTHOG_PROJECT_TOKEN` in the environment.
Replay preserves event UUIDs and timestamps so PostHog can deduplicate; no token
is stored in the artifact. A GitHub workflow rerun intentionally collects a new
observation with a new timestamp/UUID; it is not a replay of the failed run.
Daily charts should select the last observation per asset per UTC day before
computing differences, so manual runs do not inflate totals. Use only complete
`snapshot_id` groups (unique `asset_id` count equals `snapshot_asset_count`)
for aggregate comparisons and freshness. A partially ingested snapshot is
incomplete data, not zero downloads or declining demand.
There are no automatic transport retries or synthetic download-delta events.
