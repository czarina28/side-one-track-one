import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const webDir = join(projectRoot, "www");

await rm(webDir, { recursive: true, force: true });
await mkdir(join(webDir, "data"), { recursive: true });

for (const file of ["index.html", "app.css", "app.js"]) {
  await cp(join(projectRoot, file), join(webDir, file));
}

await cp(
  join(projectRoot, "data", "albums.js"),
  join(webDir, "data", "albums.js")
);

console.log("Prepared clean Capacitor web bundle in www/");
