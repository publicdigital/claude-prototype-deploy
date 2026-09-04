# claude-prototype-deploy

This repo is the backbone of `publicdigital`'s self-service pathway for turning a
Claude Code session into a live, password-protected prototype URL — without the
person building the prototype ever needing direct access to Netlify or deep git
experience.

## How the pieces fit together

```
prototype-builder's Claude Code session
        │
        │  runs the `new-prototype` skill (skills/new-prototype/SKILL.md)
        ▼
new GitHub repo in `publicdigital`, seeded from prototype-template/
        │
        │  every push to main triggers the caller workflow
        │  (prototype-template/.github/workflows/deploy.yml)
        ▼
.github/workflows/deploy-prototype.yml  (reusable workflow, lives HERE)
        │
        │  deploys the static site (+ optional Netlify Functions) to Netlify
        ▼
live HTTPS URL, protected by a per-prototype username+password
(Netlify `_headers` Basic-Auth — see prototype-template/_headers)
```

A separate, org-wide safety net runs on a schedule from this same repo:

```
.github/workflows/fleet-check.yml  (daily cron, THIS repo)
        │
        │  finds every repo tagged `claude-prototype` across the org,
        │  reads each PROTOTYPE.yml, runs scripts/check_expiry.py
        ▼
a single tracking issue in THIS repo, listing every prototype's
switch-off status (OK / due soon / OVERDUE) — reporting only, no
automatic deletion (yet)
```

## Contents

| Path | Purpose |
|---|---|
| `.github/workflows/deploy-prototype.yml` | Reusable workflow every prototype repo calls to deploy to Netlify |
| `.github/workflows/fleet-check.yml` | Daily audit of every prototype's switch-off date |
| `prototype-template/` | Files copied into each new prototype repo by the `new-prototype` skill |
| `skills/new-prototype/SKILL.md` | The Claude Code skill a prototype-builder invokes to scaffold + deploy |
| `scripts/check_expiry.py` | Stdlib-only helper used by `fleet-check.yml` to compute prototype status |
| `docs/ADMIN-SETUP.md` | One-time manual setup for the org admin (start here if you're new) |
| `docs/PROTOTYPE-CONSTRAINTS.md` | What does/doesn't work on this hosting, for builders and for Claude |

## Where to start

If you're the org admin setting this up for the first time, start with
[`docs/ADMIN-SETUP.md`](docs/ADMIN-SETUP.md).

If you're a prototype-builder, you don't need to read this repo at all — just
invoke the `new-prototype` skill from your own Claude Code session and follow
its prompts.
