import sys
import json


def send(obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def send_result(req_id: int, result: object) -> None:
    send({"id": req_id, "result": result})


def send_error(req_id: int, message: str) -> None:
    send({"id": req_id, "error": {"message": message}})


def notify(method: str, params: object) -> None:
    send({"method": method, "params": params})


_HANDLERS: dict[str, callable] = {}


def register(method: str):
    def wrapper(fn):
        _HANDLERS[method] = fn
        return fn
    return wrapper


@register("file/read")
def _file_read(req_id: int, params: dict) -> None:
    path = params.get("path", "")
    send_result(req_id, {"path": path, "content": "# placeholder\nprint('hello')\n", "language": "python"})


@register("file/save")
def _file_save(req_id: int, params: dict) -> None:
    path = params.get("path", "")
    send_result(req_id, {"path": path, "saved": True})


@register("file/list")
def _file_list(req_id: int, params: dict) -> None:
    path = params.get("path", ".")
    send_result(req_id, {
        "path": path,
        "entries": [
            {"name": "src", "type": "directory"},
            {"name": "main.py", "type": "file"},
            {"name": "README.md", "type": "file"},
        ]
    })


@register("search/query")
def _search_query(req_id: int, params: dict) -> None:
    query = params.get("query", "")
    send_result(req_id, {
        "query": query,
        "results": [
            {"file": "src/main.py", "line": 10, "column": 5, "text": "def hello():"},
            {"file": "src/utils.py", "line": 3, "column": 1, "text": "import sys"},
        ]
    })


def dispatch(line: str) -> None:
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

    handler = _HANDLERS.get(method)
    if handler:
        try:
            handler(req_id, params)
        except Exception as exc:
            send_error(req_id, str(exc))
    else:
        send_error(req_id, f"Unknown method: {method}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    notify("hello", {"version": "0.1.0"})

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
