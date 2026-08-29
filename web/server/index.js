import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { createDashboardCache } from "./cache.js";
import { loadConfig } from "./config.js";

const config = loadConfig();
const cache = createDashboardCache(config);
const distDir = resolve(import.meta.dir, "../dist");
const indexPath = join(distDir, "index.html");

function json(data, status = 200) {
  return Response.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

async function serveStatic(pathname) {
  const filePath = pathname === "/" ? indexPath : join(distDir, pathname);

  if (existsSync(filePath)) {
    return new Response(Bun.file(filePath));
  }

  if (existsSync(indexPath)) {
    return new Response(Bun.file(indexPath), {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }

  return new Response("RaceMesh web assets are not built. Run `bun run build`.", {
    status: 404,
  });
}

Bun.serve({
  port: config.port,
  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/api/health") {
      return json(cache.getHealth());
    }

    if (url.pathname === "/api/dashboard") {
      try {
        return json(await cache.getDashboard());
      } catch (error) {
        return json({ error: error.message, stale: true }, 503);
      }
    }

    if (url.pathname.startsWith("/api/")) {
      return json({ error: "Not found" }, 404);
    }

    return serveStatic(url.pathname);
  },
});

console.log(`RaceMesh web service listening on http://localhost:${config.port}`);
