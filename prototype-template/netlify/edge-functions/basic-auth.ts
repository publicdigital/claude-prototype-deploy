// Enforces HTTP Basic-Auth on every request to this prototype.
//
// Netlify's declarative `_headers` file `Basic-Auth` directive
// (https://docs.netlify.com/manage/domains-https/basic-auth/) is the
// simpler way to do this, but it silently no-ops on Free-plan Netlify
// accounts created in 2026 or later — confirmed against a live prototype,
// not just read in the docs. This Edge Function is the Free-tier
// equivalent: Edge Functions run on every Netlify plan.
//
// {{USERNAME}} and {{PASSWORD}} are replaced by the `new-prototype` skill
// with a freshly generated, unique-per-prototype random username and
// password at scaffolding time. Do not commit real placeholder text here —
// if you ever see the literal tokens below in a deployed repo, generation
// was skipped and this prototype has NO effective password (verify before
// sharing the URL).

export default async (request: Request, context: Netlify.Context) => {
  const expected = "Basic " + btoa("{{USERNAME}}:{{PASSWORD}}");

  if (request.headers.get("authorization") === expected) {
    return context.next();
  }

  return new Response("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Prototype"' },
  });
};

export const config = { path: "/*" };
