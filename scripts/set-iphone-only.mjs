import { access, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const projectFile = join(
  projectRoot,
  "ios",
  "App",
  "App.xcodeproj",
  "project.pbxproj"
);

try {
  await access(projectFile);
} catch {
  console.error("iOS project not found. Run npm run ios:add first.");
  process.exit(1);
}

const original = await readFile(projectFile, "utf8");
const updated = original.replace(
  /TARGETED_DEVICE_FAMILY = [^;]+;/g,
  'TARGETED_DEVICE_FAMILY = "1";'
);

if (!updated.includes('TARGETED_DEVICE_FAMILY = "1";')) {
  console.error("Could not set TARGETED_DEVICE_FAMILY to iPhone.");
  process.exit(1);
}

await writeFile(projectFile, updated, "utf8");
console.log("Configured native target for iPhone only (device family 1).");
