#!/usr/bin/env node
import { render } from "ink";
import App from "./App.js";
import { startBridge } from "./bridge.js";

startBridge();

const { waitUntilExit } = render(<App />, { exitOnCtrlC: false });
await waitUntilExit();
