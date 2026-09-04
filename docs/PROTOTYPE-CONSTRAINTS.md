# What works (and what doesn't) on this hosting

Every prototype deploys as a **static site on Netlify**, optionally backed
by **Netlify Functions** (short-lived, stateless serverless functions).
That's a real hosting environment with real limits — a lot of things a
prototype-builder might casually ask for won't work here, and will fail
in confusing ways late in a build rather than obviously up front.

This doc is written for two audiences: a human prototype-builder deciding
what to ask for, and Claude reading it programmatically while working in a
prototype repo. If you're Claude and a user asks for something, check it
against this list *before* starting to build it, and say so immediately if
it won't work — don't attempt it and let it fail silently later.

## Works fine

- Static HTML, CSS, and client-side JavaScript.
- Any frontend framework that builds down to static output (React, Vue,
  Svelte, plain Vite/esbuild bundles, etc.) — as long as the *build output*
  is what gets deployed, not a dev server.
- Client-side routing, client-side state, `localStorage`/`sessionStorage`
  in the browser.
- Calling third-party APIs directly from the browser (subject to that
  API's own CORS and auth rules).
- **Netlify Functions** for light, stateless serverless logic: a single
  request in, a single response out, no persistent connection, no shared
  in-memory state between invocations, execution capped at Netlify's
  function timeout (short — seconds, not minutes; verify the current
  limit for your plan in the Netlify dashboard).
- **Netlify Edge Functions** (`netlify/edge-functions/*.ts`, registered via
  a `[[edge_functions]]` block in `netlify.toml`) for logic that needs to
  run in front of every request — this pathway's own Basic-Auth gate is
  one (see `prototype-template/netlify/edge-functions/basic-auth.ts`).
  Same request/response, no-persistent-state model as Functions, but they
  run on Netlify's edge network rather than a regional one and can
  short-circuit or modify a request before it reaches static assets or a
  Function. Free-tier compatible.
- Reading/writing to an **external managed service** from a Function or
  from the browser — e.g. Supabase, Firebase, Airtable, a hosted Postgres
  provider. The prototype itself stores nothing; the external service does.

## Doesn't work — and what to do instead

| Doesn't work | Why | Alternative |
|---|---|---|
| A persistent server process (Express/Flask/Rails app, etc.) that stays running | Netlify hosts static files + on-demand Functions, not a long-running process | Move the logic into one or more Netlify Functions if it's simple request/response; if it genuinely needs a long-running process, this prototype has outgrown static hosting — talk to the admin about different hosting |
| WebSockets / long-lived connections (live chat, live cursors, streaming) | Functions are short-lived and request/response only, no persistent connection | Use a managed realtime service (e.g. Supabase Realtime, Pusher, Ably) called from the browser |
| Server-side sessions or a database running *in* the prototype | No persistent disk or process to hold session/database state between requests | Use an external managed database/auth service (Supabase, Firebase, etc.) and call it from Functions or the browser |
| Cron jobs / background jobs running inside the prototype | Nothing runs unless a request (or a scheduled Netlify Function, see note) triggers it | Netlify does support *scheduled* Functions on some plans — verify in your dashboard; otherwise use an external scheduler (e.g. a cron-based webhook service) to hit a Function |
| Large file storage / uploads kept in the prototype itself | No persistent filesystem across deploys | Use an external object storage service (e.g. S3, Supabase Storage, Cloudinary) |
| Anything requiring a fixed outbound IP, VPN, or private network access | Functions run in Netlify's shared, ephemeral infrastructure | Not solvable within this hosting model — escalate to the admin |

## If a request doesn't fit

Two honest options, and the choice is the user's, not Claude's to make
silently:

1. **Reshape it** to fit the model above — usually "put the logic in a
   Netlify Function and use an external service for anything stateful."
2. **Escalate** — tell the user plainly that this prototype has outgrown
   what static hosting + Functions can do, and that they should talk to
   the org admin about different hosting for it. Don't attempt a workaround
   that will quietly break in production.
