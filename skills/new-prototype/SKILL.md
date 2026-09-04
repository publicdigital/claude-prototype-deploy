---
name: new-prototype
description: >-
  Use this skill when the user wants to create a new prototype for the
  publicdigital org, deploy a prototype to a live URL, or wants to know
  whether something they're asking for will work on this hosting (static
  site + Netlify Functions). Triggers on requests like "start a new
  prototype", "deploy this", "push this live", "set up a repo for this",
  or "will X work here" about a publicdigital prototype.
---

# new-prototype

This skill scaffolds a new prototype repo in the `publicdigital` GitHub
org, deploys it to a live HTTPS URL behind HTTP Basic Auth, and keeps
watch afterwards for requests that won't work on this hosting.

Follow the steps below in order. Do not skip the permission check in
step 1 — failing there cleanly and early is much better than failing
partway through repo creation.

Throughout, read `docs/PROTOTYPE-CONSTRAINTS.md` from the
`publicdigital/claude-prototype-deploy` repo (fetch it via the GitHub API
or raw content URL — don't assume you have this repo cloned locally) when
you need it; you don't need to load it up front.

## Step 1 — Check whether this user can actually create the repo

Before asking the user anything else, confirm you (acting as this user)
can create a repository in the `publicdigital` GitHub org.

- Try to determine this via the GitHub API/tooling available to you (e.g.
  checking the authenticated user's org role/permissions, or attempting a
  dry-run check if your GitHub tooling supports one).
- If you cannot create org repos (org repo-creation is restricted — see
  `docs/ADMIN-SETUP.md` step 5 in `claude-prototype-deploy`), **stop here**
  and tell the user exactly this:
  > "I can't create a new repository in the `publicdigital` org — repo
  > creation looks like it's restricted to admins. Ask your admin to
  > either turn on member repo creation (GitHub org Settings → Member
  > privileges → Repository creation), or to pre-create an empty repo in
  > `publicdigital` for this prototype and tell you its name so I can use
  > it instead. See `docs/ADMIN-SETUP.md` in the `claude-prototype-deploy`
  > repo for the exact steps to send them."
  Do not proceed past this point until the user has either fixed the
  permission or given you a pre-created repo name to use.
- If a pre-created empty repo name is given instead, use that repo in
  place of creating a new one in step 3, but still do everything else
  (topic, description, template files, commit, push).

## Step 2 — Gather and validate prototype details

Ask the user for:

1. **Client** — who this is for (e.g. "Acme Corp" or "Internal — Marketing").
2. **Project name** — a short name for the prototype. Use this to derive a
   repo name (lowercase, hyphenated, e.g. "Onboarding Redesign" →
   `onboarding-redesign`) and confirm the derived name with the user before
   creating anything.
3. **Switch-off date** — the date this prototype should be turned off.

Validate the switch-off date yourself:

- It must be a real future date.
- It must be **no more than 100 days from today**.
- If the user gives a date more than 100 days out, **refuse to proceed**
  with that date. Explain why (org policy caps prototype lifetime at 100
  days to keep the fleet from accumulating forgotten live sites) and ask
  for a date within range. Don't silently clamp it — get an explicit
  in-range date from the user.

## Step 3 — Create the repo and seed it from prototype-template/

1. Create the new repo (or use the pre-created one from step 1) in
   `publicdigital`. Private by default unless the user says otherwise.
2. Fetch every file under `prototype-template/` from
   `publicdigital/claude-prototype-deploy` (via the GitHub API's contents
   endpoint, or the raw content URLs — do not assume a local clone of
   `claude-prototype-deploy` exists).
3. Generate a random username and a random, strong password (e.g. a
   URL-safe token of at least 16 characters) for this prototype's Basic
   Auth. Generate these yourself — don't ask the user to supply them.
4. Substitute into the fetched files:
   - In `netlify/edge-functions/basic-auth.ts`: replace `{{USERNAME}}` and
     `{{PASSWORD}}` with the generated credentials. (This Edge Function is
     the auth mechanism — not a `_headers` `Basic-Auth` directive, which
     silently no-ops on Free-plan Netlify accounts created in 2026 or
     later; see the comment at the top of that file.)
   - In `PROTOTYPE.yml`: replace `{{CLIENT}}`, `{{PROJECT}}`,
     `{{OWNER_GITHUB}}` (the creating user's GitHub login — look this up,
     don't guess), `{{CREATED_DATE}}` (today, `YYYY-MM-DD`), and
     `{{SWITCH_OFF_DATE}}` (validated in step 2, `YYYY-MM-DD`).
   - In `README.md`: replace `{{PROJECT}}`.
   - `index.html`, `netlify.toml`, and `.github/workflows/deploy.yml` are
     copied as-is, no substitution needed. Don't skip `netlify.toml` — it's
     what makes Netlify actually register `basic-auth.ts` as an Edge
     Function rather than silently deploying it as a plain static file.
5. Write all of these files into the new repo, preserving the directory
   structure (`.github/workflows/deploy.yml` must land at that exact path
   in the new repo).
6. Trigger the secrets bridge so the deploy workflow has something to
   deploy with: dispatch the `provision-prototype-secret.yml` workflow in
   `publicdigital/claude-prototype-deploy` via the GitHub API
   (`workflow_dispatch`, input `repo` = this repo's bare name, no
   `publicdigital/` prefix). Then poll that workflow run until it finishes.
   This copies `NETLIFY_AUTH_TOKEN` into the new repo as a repository
   secret — do this *before* Step 5's push, since the push triggers the
   deploy workflow and it will fail without the secret in place. If the
   dispatch call fails with a permission error, this user likely lacks
   write access to `claude-prototype-deploy` — see
   `docs/ADMIN-SETUP.md` step 3 and tell the user to ask their admin.

## Step 4 — Set topic and description

On the new repo:

- Add the topic `claude-prototype` (this is how the fleet-check audit and
  any org-wide search finds it — don't skip it).
- Set the repo description to something like: `<client> — <project> —
  switch off <switch_off_date>`.

There's no dedicated tool for either of these in every GitHub toolset —
if yours doesn't have one (e.g. no `gh` CLI and no generic REST-call
tool), use whatever raw GitHub API access you do have to call
`PATCH /repos/{owner}/{repo}` (for `description`) and
`PUT /repos/{owner}/{repo}/topics` (for topics, body
`{"names": ["claude-prototype"]}`). If you genuinely have no way to make
either call, don't block on it — tell the user plainly, in your Step 7
report, that these two need setting by hand (link the repo's Settings
page) so the fleet-check audit can still find the prototype.

## Step 5 — Commit and push to main

Commit all the seeded files and push to `main`. If you created the repo
fresh in step 3, this is the initial commit. If you're using a
pre-created repo, check first whether it already has content (don't
blindly overwrite something the admin may have already set up) — if it's
genuinely empty this is straightforward; if it has unexpected existing
content, stop and ask the user how to proceed rather than overwriting it.

## Step 6 — Explain what happens next

Tell the user, in your own words, something like:

> This push just triggered the deploy workflow — it'll build and publish
> automatically. From now on, every push to `main` in this repo redeploys
> the live site, so committing and pushing is literally how you update it.

## Step 7 — Report back once deployed

Check the GitHub Actions run this push triggered. Once it succeeds, tell
the user:

- The live URL (from the Netlify deploy step's output, or the Actions log).
- The generated username and password, with an explicit note: **store
  these somewhere safe now — they will not be shown again.**
- A reminder of the switch-off date and what it means (see
  `PROTOTYPE.yml`'s comments — it's a commitment to turn the site off by
  then, tracked by a daily audit, not a technical kill switch).

If the deploy workflow fails, read the failure from the Actions log and
help the user fix it rather than just reporting failure. Common causes,
roughly in the order you're likely to hit them:

- `NETLIFY_AUTH_TOKEN` not yet available to this repo — check whether
  Step 3's secrets-bridge dispatch actually succeeded before the push.
  If the dispatch itself failed with a 404 fetching the repo's secrets
  public key, that's `ORG_SECRETS_BRIDGE_TOKEN` not covering this repo —
  an admin setup issue, see `docs/ADMIN-SETUP.md` step 3.
- The reusable workflow call fails to parse at all (zero jobs run, no
  logs) — a YAML/syntax problem in `deploy-prototype.yml` itself on
  `main`, not something to work around in the prototype repo; report it
  against `claude-prototype-deploy`.
- Netlify CLI errors during site creation — see the comments throughout
  the "Create Netlify site" step in `deploy-prototype.yml` for the
  specific failure modes already worked through (needing
  `--account-slug`, site name collisions, etc.).
- The site deploys and is reachable but shows Netlify's own "This site is
  private" sign-in gate instead of this repo's Basic-Auth prompt — that's
  Netlify's "Project visibility" feature, not this pathway; see
  `docs/ADMIN-SETUP.md` step 8.
- The site deploys and is reachable but has *no* auth prompt at all
  (open access) — check the deploy log for a "Bundling edge functions"
  line and a `Configuration path: .../netlify.toml` line. If either is
  missing, `netlify.toml` didn't make it into the repo (Step 3 above) or
  wasn't committed at the repo root — the Edge Function silently deploys
  as an inert static file without it.

## Step 8 — Ongoing: guard against requests that won't work on this hosting

For the rest of the working session (and any future session working in
this prototype repo), before building something the user asks for, check
it against `docs/PROTOTYPE-CONSTRAINTS.md` in
`publicdigital/claude-prototype-deploy`. This hosting is a static site
plus optional short-lived Netlify Functions — no persistent server,
websockets, server-side sessions/database, cron/background jobs, or large
file storage.

If a request won't work as asked:

1. Say so immediately, before attempting it — don't build something that
   will fail silently once deployed.
2. Explain briefly why (which constraint it hits).
3. Suggest a concrete alternative from `PROTOTYPE-CONSTRAINTS.md` — usually
   either "move this into a Netlify Function" or "use an external managed
   service (e.g. Supabase/Firebase) for the stateful part."
4. If the request genuinely doesn't fit this hosting model at all (e.g. it
   needs a real persistent backend), say clearly that this prototype has
   outgrown static hosting and the user should talk to the admin about
   different hosting — don't attempt a workaround that will quietly break.
