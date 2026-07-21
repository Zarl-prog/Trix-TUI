#!/usr/bin/env node
const { spawnSync, execSync } = require("child_process");

function pipInstall() {
  console.log("Installing trix-ide via pip...");
  try {
    execSync("pip install -U trix-ide", { stdio: "inherit" });
  } catch {
    console.error("Failed to install trix-ide. Make sure Python and pip are installed.");
    process.exit(1);
  }
}

const result = spawnSync("trix", process.argv.slice(2), {
  stdio: "inherit",
  shell: true,
});

if (result.error) {
  if (result.error.code === "ENOENT") {
    console.log("trix command not found.");
    pipInstall();
    const retry = spawnSync("trix", process.argv.slice(2), {
      stdio: "inherit",
      shell: true,
    });
    process.exit(retry.status ?? 1);
  }
  console.error("Failed to run trix:", result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 0);
