// Frontend test runner: bundles the JSX tests with esbuild (installed together with vite) and runs everything with node's built-in test runner.
//   npm install && npm test        (FRONTEND_NODE_MODULES=/path/to/node_modules lets you point at another install of react/esbuild)
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { mkdirSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extra = process.env.FRONTEND_NODE_MODULES;
const req = createRequire(path.join(root, "package.json"));
const find = (name) => req.resolve(name, { paths: [path.join(root, "node_modules"), ...(extra ? [extra] : [])] });
const esbuild = req(find("esbuild"));
const out = path.join(root, "tests", ".build"); mkdirSync(out, { recursive: true });
const alias = extra ? { react: path.join(extra, "react"), "react-dom": path.join(extra, "react-dom") } : {};
const tests = readdirSync(path.join(root, "tests")).filter((f) => f.endsWith(".test.jsx"));
for (const f of tests) {
  await esbuild.build({ entryPoints: [path.join(root, "tests", f)], bundle: true, platform: "node", format: "esm", jsx: "automatic", loader: { ".js": "jsx", ".css": "empty" }, alias,
    define: { "import.meta.env.VITE_API": '"http://test"', "import.meta.env.DEV": "false" }, outfile: path.join(out, f.replace(".jsx", ".mjs")),
    banner: { js: "import { createRequire as __cr } from 'node:module'; const require = __cr(import.meta.url);" }, logLevel: "error" });
}
const files = [...readdirSync(path.join(root, "tests")).filter((f) => f.endsWith(".test.mjs")).map((f) => path.join("tests", f)), ...tests.map((f) => path.join("tests", ".build", f.replace(".jsx", ".mjs")))];
process.exit(spawnSync(process.execPath, ["--test", ...files], { cwd: root, stdio: "inherit" }).status ?? 1);
