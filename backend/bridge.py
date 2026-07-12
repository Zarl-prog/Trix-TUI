import sys, json, os, pty, select, struct, fcntl, termios, signal, shutil

HANDLERS = {}

def register(method):
    def wrapper(fn):
        HANDLERS[method] = fn
        return fn
    return wrapper

def send(obj):
    line = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def send_result(req_id, result):
    send({"id": req_id, "result": result})

def send_error(req_id, message):
    send({"id": req_id, "error": {"message": message}})

def notify(method, params):
    send({"method": method, "params": params})

# ── Terminal PTY ──

TERM_PID = None
TERM_FD = None

@register("terminal/start")
def _term_start(req_id, params):
    global TERM_PID, TERM_FD
    if TERM_PID is not None:
        send_result(req_id, {"status": "already_running"})
        return

    shell = os.environ.get("SHELL", "/bin/bash")
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(shell, [shell])
    else:
        TERM_PID = pid
        TERM_FD = fd
        import threading
        def reader():
            while True:
                try:
                    data = os.read(fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    notify("terminal/output", {"data": text})
                except OSError:
                    break
                except Exception:
                    break
        t = threading.Thread(target=reader, daemon=True)
        t.start()
        send_result(req_id, {"status": "started", "pid": pid})

@register("terminal/write")
def _term_write(req_id, params):
    global TERM_FD
    if TERM_FD is None:
        send_error(req_id, "Terminal not started")
        return
    data = params.get("data", "")
    try:
        os.write(TERM_FD, data.encode("utf-8"))
        send_result(req_id, {"status": "ok"})
    except OSError as e:
        send_error(req_id, str(e))

@register("terminal/resize")
def _term_resize(req_id, params):
    global TERM_FD
    if TERM_FD is None:
        send_error(req_id, "Terminal not started")
        return
    rows = params.get("rows", 24)
    cols = params.get("cols", 80)
    try:
        s = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(TERM_FD, termios.TIOCSWINSZ, s)
        send_result(req_id, {"status": "ok"})
    except OSError as e:
        send_error(req_id, str(e))

@register("terminal/stop")
def _term_stop(req_id, params):
    global TERM_PID, TERM_FD
    if TERM_PID:
        try:
            os.kill(TERM_PID, signal.SIGTERM)
        except OSError:
            pass
        TERM_PID = None
        TERM_FD = None
    send_result(req_id, {"status": "stopped"})

# ── File Operations ──

LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".jsx": "javascript", ".json": "json", ".md": "markdown", ".html": "html",
    ".css": "css", ".rs": "rust", ".go": "go", ".c": "c", ".cpp": "cpp",
    ".h": "c", ".java": "java", ".rb": "ruby", ".sh": "bash", ".yaml": "yaml",
    ".yml": "yaml", ".toml": "toml", ".sql": "sql", ".txt": "text",
}

def detect_language(path):
    _, ext = os.path.splitext(path)
    return LANG_MAP.get(ext.lower(), "text")

@register("file/list")
def _file_list(req_id, params):
    path = params.get("path", ".")
    prefix = params.get("prefix", "")

    try:
        entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    except OSError as e:
        send_error(req_id, str(e))
        return

    result = []
    for name in entries:
        full = os.path.join(path, name)
        if name.startswith("."):
            continue
        entry = {"name": name, "type": "directory" if os.path.isdir(full) else "file"}
        if prefix:
            entry["prefix"] = prefix
        result.append(entry)

    send_result(req_id, {
        "path": os.path.abspath(path),
        "entries": result,
    })

@register("file/list-tree")
def _file_list_tree(req_id, params):
    path = params.get("path", ".")

    def build_tree(dir_path):
        entries = []
        try:
            names = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
        except OSError:
            return entries
        for name in names:
            if name.startswith("."):
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                children = build_tree(full)
                entries.append({"name": name, "type": "directory", "children": children})
            else:
                entries.append({"name": name, "type": "file"})
        return entries

    try:
        tree = build_tree(path)
        send_result(req_id, {"path": os.path.abspath(path), "tree": tree})
    except OSError as e:
        send_error(req_id, str(e))

@register("file/read")
def _file_read(req_id, params):
    path = params.get("path", "")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        send_result(req_id, {
            "path": os.path.abspath(path),
            "content": content,
            "language": detect_language(path),
        })
    except OSError as e:
        send_error(req_id, str(e))

@register("file/save")
def _file_save(req_id, params):
    path = params.get("path", "")
    content = params.get("content", "")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        send_result(req_id, {"path": os.path.abspath(path), "saved": True})
    except OSError as e:
        send_error(req_id, str(e))

@register("search/query")
def _search_query(req_id, params):
    query = params.get("query", "")
    root = params.get("root", ".")

    results = []
    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.startswith(".") or fn.startswith("node_modules"):
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                results.append({
                                    "file": os.path.relpath(full, root),
                                    "line": i,
                                    "column": line.lower().index(query.lower()) + 1,
                                    "text": line.rstrip("\n"),
                                })
                except (OSError, UnicodeDecodeError):
                    continue
    except OSError:
        pass

    send_result(req_id, {"query": query, "results": results[:200]})

# ── Dispatch ──

def dispatch(line):
    if not line.strip():
        return
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return

    req_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if req_id is None:
        return

    handler = HANDLERS.get(method)
    if handler:
        try:
            handler(req_id, params)
        except Exception as exc:
            send_error(req_id, str(exc))
    else:
        send_error(req_id, f"Unknown method: {method}")

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    notify("hello", {"version": "0.2.0"})

    buffer = ""
    while True:
        try:
            chunk = sys.stdin.read(4096)
            if not chunk:
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                dispatch(line)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception:
            continue

if __name__ == "__main__":
    main()
