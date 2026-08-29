import { mkdir, rm, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";

const distDir = join(import.meta.dir, "../dist");

await rm(distDir, { recursive: true, force: true });
await mkdir(join(distDir, "assets"), { recursive: true });

const result = await Bun.build({
  entrypoints: [join(import.meta.dir, "../src/main.jsx")],
  outdir: join(distDir, "assets"),
  target: "browser",
  minify: true,
  sourcemap: "external",
});

if (!result.success) {
  for (const log of result.logs) {
    console.error(log);
  }
  process.exit(1);
}

const entryOutput = result.outputs.find(
  (output) => output.path?.endsWith(".js") && !output.path.endsWith(".map"),
);
const cssOutputs = result.outputs.filter(
  (output) => output.path?.endsWith(".css") && !output.path.endsWith(".map"),
);

if (!entryOutput) {
  console.error("Build completed without a browser JavaScript output.");
  process.exit(1);
}

const entryScript = `/assets/${basename(entryOutput.path)}`;
const stylesheetLinks = cssOutputs
  .map(
    (output) =>
      `    <link rel="stylesheet" href="/assets/${basename(output.path)}" />`,
  )
  .join("\n");

await writeFile(
  join(distDir, "index.html"),
  `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RaceMesh</title>
${stylesheetLinks}
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="${entryScript}"></script>
  </body>
</html>
`,
);

console.log("Built RaceMesh web assets.");
