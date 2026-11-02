import type { APIRoute } from "astro";

// All crawlers allowed on purpose, AI search crawlers included. The sitemap URL comes from astro.config `site`.
export const GET: APIRoute = ({ site }) =>
  new Response(
    [
      "# All crawlers welcome, including AI search crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).",
      "User-agent: *",
      "Allow: /",
      "",
      `Sitemap: ${new URL("sitemap-index.xml", site).href}`,
      "",
    ].join("\n"),
    { headers: { "Content-Type": "text/plain; charset=utf-8" } },
  );
