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
