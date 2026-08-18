// PaperLife landing render check — no horizontal overflow at 375/768/1280px.
// Usage: node verify-render.mjs   (requires: npx playwright install chromium)
// Exits non-zero if any viewport overflows horizontally.

import { chromium } from "playwright";
import { fileURLToPath } from "url";
import path from "path";
import { pathToFileURL } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const pageUrl = pathToFileURL(path.join(here, "index.html")).href;

const VIEWPORTS = [
  { width: 375, height: 812, name: "mobile" },
  { width: 768, height: 1024, name: "tablet" },
  { width: 1280, height: 800, name: "desktop" },
];

const browser = await chromium.launch();
let failed = 0;

for (const vp of VIEWPORTS) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto(pageUrl, { waitUntil: "load" });
  await page.waitForTimeout(300); // let images/layout settle

  const metrics = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
    scrollH: document.documentElement.scrollHeight,
  }));

  const overflow = metrics.scrollW > metrics.clientW + 1;
  const screenshot = path.join(process.env.TEMP || "/tmp", `paperlife_${vp.name}.png`);
  await page.screenshot({ path: screenshot, fullPage: true });

  console.log(
    `${vp.name.padEnd(8)} ${vp.width}px -> scrollW=${metrics.scrollW} clientW=${metrics.clientW}` +
    ` overflow=${overflow ? "YES (FAIL)" : "no"} height=${metrics.scrollH} consoleErrors=${errors.length}`
  );
  if (overflow || errors.length) {
    failed++;
    if (errors.length) console.log("  console errors:", errors.slice(0, 5));
  }
  await page.close();
}

await browser.close();
console.log(failed ? `RENDER CHECK FAILED (${failed} viewport(s))` : "RENDER CHECK PASSED");
process.exit(failed ? 1 : 0);
