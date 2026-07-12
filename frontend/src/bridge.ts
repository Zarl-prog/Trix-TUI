import { spawn, type ChildProcess } from "node:child_process";
import { createInterface } from "node:readline";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BACKEND_PATH = resolve(__dirname, "../../backend/bridge.py");

let proc: ChildProcess | null = null;
let idCounter = 0;

interface Pending {
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}

const pending = new Map<number, Pending>();
type NotificationHandler = (msg: Record<string, unknown>) => void;
const notificationHandlers = new Set<NotificationHandler>();

export function onNotification(fn: NotificationHandler): () => void {
  notificationHandlers.add(fn);
  return () => notificationHandlers.delete(fn);
}

export function startBridge(pythonCmd = "python3"): void {
  if (proc) return;

  proc = spawn(pythonCmd, [BACKEND_PATH], {
    stdio: ["pipe", "pipe", "pipe"],
  });

  const rl = createInterface({ input: proc.stdout! });
  rl.on("line", (line: string) => {
    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(line);
    } catch {
      return;
    }

    const rawId = msg.id;
    if (rawId !== undefined && rawId !== null) {
      const handler = pending.get(Number(rawId));
      if (handler) {
        if (msg.error) {
          handler.reject(msg.error);
        } else {
          handler.resolve(msg.result);
        }
        pending.delete(Number(rawId));
      }
    } else {
      for (const fn of notificationHandlers) {
        fn(msg);
      }
    }
  });

  proc.on("exit", (code) => {
    if (code !== 0) {
      for (const [, handler] of pending) {
        handler.reject(new Error(`Backend exited with code ${code}`));
      }
      pending.clear();
    }
  });
}

export function stopBridge(): void {
  if (proc) {
    proc.kill();
    proc = null;
  }
}

export function callBackend(method: string, params: object = {}): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const id = ++idCounter;
    pending.set(id, { resolve, reject });
    proc!.stdin!.write(JSON.stringify({ id, method, params }) + "\n");
  });
}
