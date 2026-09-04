# Admin setup (one-time)

These are the manual, one-time steps a human org admin needs to do before
anyone can use the `new-prototype` skill. None of this is automated —
it's dashboard clicking, done once. Wherever the exact UI path might have
moved since this was written, that's flagged below — check your own
dashboard if a step doesn't match what you see.

## 1. Create or confirm a Netlify team for the org

If `publicdigital` doesn't already have a Netlify team, create one at
[app.netlify.com](https://app.netlify.com) — *verify current signup/team
creation steps in the Netlify dashboard, this can change.* Every prototype
site will be created inside this team.

## 2. Generate a Netlify auth token and add it as a GitHub secret

**GitHub Free-org limitation:** organization-level Actions secrets are only
visible to *public* repos. Prototype repos are private by default (see
`skills/new-prototype/SKILL.md`), so a plain org secret scoped to prototype
repos — the original approach here — silently never reaches them on a Free
plan. *(Verify this against GitHub's current docs/plan — Actions secret
visibility rules have changed before and may again. If your org is on
GitHub Team/Enterprise, org secrets DO reach private repos, and you can
skip the bridge workflow below and just scope the org secret to the
prototype repos directly.)*

If you're on GitHub Free, the setup below keeps `NETLIFY_AUTH_TOKEN` as an
org secret (visible to this repo, since it's public) and uses a bridge
workflow (`.github/workflows/provision-prototype-secret.yml`, in this repo)
to copy it into each new prototype repo as an ordinary *repository* secret
at creation time. Nobody has to touch this per prototype — the
`new-prototype` skill triggers the bridge automatically.

1. In Netlify: **User settings → Applications → Personal access tokens →
   New access token**. Name it something like `publicdigital-prototypes`.
   *(Verify this exact path in your Netlify dashboard — Netlify's settings
   layout changes periodically.)*
2. Copy the token immediately — Netlify won't show it again.
3. In GitHub: go to the `publicdigital` organization → **Settings →
   Secrets and variables → Actions → New organization secret**.
4. Name it exactly `NETLIFY_AUTH_TOKEN`, paste the token as the value.
5. Under **Repository access**, scope it to **Selected repositories** →
   just `claude-prototype-deploy`. (No need to add prototype repos here —
   they'll get their own copy of the token as a repo secret via the bridge
   workflow, not via this org secret.)

## 3. Create the secrets bridge token (`ORG_SECRETS_BRIDGE_TOKEN`)

The bridge workflow needs a credential that can write Actions secrets into
*other* repos in the org — `GITHUB_TOKEN` inside a workflow run cannot do
this, it's scoped to the repo the workflow runs in.

1. Create a **fine-grained personal access token** (or an organization-owned
   GitHub App installation token, if you'd rather not tie this to a
   personal account — *verify current best practice in GitHub's docs, this
   area has evolved*) with:
   - **Secrets: write** access, and **Metadata: read** access, for all repos
     in the org (or at minimum, all repos carrying the `claude-prototype`
     topic — but note fine-grained PATs scope by explicit repo selection or
     "all repos," not by topic, same caveat as the old approach to step 2
     above).
2. In GitHub: `publicdigital` org → **Settings → Secrets and variables →
   Actions → New organization secret**.
3. Name it exactly `ORG_SECRETS_BRIDGE_TOKEN`, scope it to
   **Selected repositories** → just `claude-prototype-deploy` (same
   reasoning as `ORG_READ_TOKEN` in step 4 below — it never needs to be
   visible to prototype repos themselves).

Anyone using the `new-prototype` skill also needs permission to trigger
`workflow_dispatch` on `claude-prototype-deploy` itself (GitHub requires at
least **write** access to a repo to dispatch its workflows). If your org
members only have read access to this repo by default, either grant
prototype-builders write access to `claude-prototype-deploy`, or have the
skill authenticate as a GitHub App installation with `actions: write` on
this repo instead of the individual user's own token — *decide based on
how much you trust members to have write access to the deploy tooling repo
itself.*

## 4. Generate an org-read GitHub token for the fleet audit

The daily `fleet-check.yml` workflow (in this repo) needs to search and
read files across *every* repo in the org, which the default per-repo
`GITHUB_TOKEN` cannot do.

1. Create a **fine-grained personal access token** (or an organization-owned
   GitHub App token, if you'd rather not tie this to a personal account —
   *verify current best practice for org-wide read tokens in GitHub's docs,
   this area has evolved*) with:
   - Read-only access to **Contents** and **Metadata** for all repos in the
     org (or at minimum, all repos carrying the `claude-prototype` topic).
2. In GitHub: `publicdigital` org → **Settings → Secrets and variables →
   Actions → New organization secret**.
3. Name it exactly `ORG_READ_TOKEN`, scope it to this repo
   (`claude-prototype-deploy`) only — it doesn't need to be visible to
   prototype repos themselves.

## 5. Confirm who can create repositories in the org

The `new-prototype` skill's first step checks whether the person running
it can create a repo in `publicdigital`. Whether that's possible at all
depends on an org setting:

1. GitHub: `publicdigital` org → **Settings → Member privileges →
   Repository creation**.
2. If repo creation is **off** for members, the skill's permission check
   will correctly tell users to ask you to pre-create their repo instead
   of failing confusingly later. Decide which mode you want:
   - **On**: simplest, fully self-service.
   - **Off**: more control, but you (the admin) become a manual step for
     every new prototype — pre-create an empty repo and tell the skill to
     use it.

## 6. Enable the `new-prototype` skill for your org's Claude Code users

This repo is itself a Claude Code plugin marketplace (see
`.claude-plugin/marketplace.json`), shipping the skill at
`skills/new-prototype/SKILL.md`. To enable it for your org's members, have
each person (or your org-wide Claude Code admin config) run:

```
/plugin marketplace add publicdigital/claude-prototype-deploy
/plugin install new-prototype@claude-prototype-deploy
```

*Confirm the current steps for installing/enabling an org-wide plugin
source in your Claude Code admin settings* — this is evolving and not
something to take on faith from this doc.

## 7. Verify: does Basic-Auth via `_headers` need a paid Netlify plan?

This whole design depends on Netlify's `_headers` file `Basic-Auth`
directive (per-site username+password, fully scriptable, no dashboard
clicking required per prototype). **This was not confirmed against a live
Netlify plan at design time.** Before relying on it:

1. Deploy one test prototype through the full pathway.
2. Confirm the `Basic-Auth` header in `_headers` actually prompts for a
   username/password on the live URL.
3. If it doesn't (or Netlify's docs say it requires Pro), you'll need to
   either upgrade the team's plan or reconsider the auth approach — do
   this before telling prototype-builders the pathway is ready to use.

---

Once all seven steps are done, prototype-builders can use the
`new-prototype` skill from their own Claude Code sessions without ever
touching Netlify or these secrets directly.
