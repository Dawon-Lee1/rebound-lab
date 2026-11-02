// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// https://astro.build/config
export default defineConfig({
  // The only place the site address lives: canonical, og:url, sitemap, robots.txt and llms.txt all read it.
  site: "https://rebound-lab-1iq.pages.dev",
  integrations: [sitemap({ filter: (page) => !/\/404\/?$/.test(page) })],
});
