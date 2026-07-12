import { useEffect, useRef } from "react";
import { useInput, useFocusManager, useStdout, Box } from "ink";
import { useStore } from "./store.js";
import { startBridge, callBackend, onNotification } from "./bridge.js";
import Header from "./components/Header.js";
import BottomBar from "./components/BottomBar.js";
import FileTree from "./components/FileTree.js";
import Editor from "./components/Editor.js";
import TerminalPanel from "./components/TerminalPanel.js";
import Divider from "./components/Divider.js";
import CommandPalette from "./components/CommandPalette.js";

export default function App() {
  const { focusNext, focusPrevious } = useFocusManager();
  const { stdout } = useStdout();
  const cols = stdout.columns;
  const fileTreeWidth = useStore((s) => s.fileTreeWidth);
  const showPalette = useStore((s) => s.showPalette);
  const activePane = useStore((s) => s.activePane);

  const terminalInputRef = useRef("");

  useEffect(() => {
    startBridge();
    callBackend("file/list-tree", { path: "." }).then((res: any) => {
      useStore.getState().setTreeData(res.tree || []);
      useStore.getState().setFolderPath(res.path || "");
    }).catch(() => {});

    const unsub = onNotification((msg) => {
      if (msg.method === "terminal/output") {
        const data = (msg.params as any)?.data || "";
        useStore.getState().appendTerminalOutput(data);
      }
    });

    callBackend("terminal/start", {}).catch(() => {});

    return () => unsub();
  }, []);

  useInput((input, key) => {
    const { keybindingLayer, showPalette, treeData, treeSelectedIndex,
            setTreeSelectedIndex, treeExpanded, toggleExpanded,
            setTreeScroll, treeScroll, terminalInput } = useStore.getState();

    if (showPalette || keybindingLayer === "palette") {
      if (key.escape) { useStore.getState().closePalette(); return; }
      if (key.return) { useStore.getState().paletteSelect(); return; }
      if (key.upArrow) { useStore.getState().palettePrevious(); return; }
      if (key.downArrow) { useStore.getState().paletteNext(); return; }
      if (key.backspace) {
        const f = useStore.getState().paletteFilter;
        useStore.getState().setPaletteFilter(f.slice(0, -1));
        return;
      }
      if (input && input.length === 1 && input.charCodeAt(0) >= 32) {
        const f = useStore.getState().paletteFilter;
        useStore.getState().setPaletteFilter(f + input);
        return;
      }
      return;
    }

    if (key.tab && !key.shift) { focusNext(); return; }
    if (key.tab && key.shift) { focusPrevious(); return; }

    if (key.ctrl) {
      const ch = input ? String.fromCharCode(input.charCodeAt(0) + 96) : "";
      switch (ch) {
        case "p": useStore.getState().openPalette(); return;
        case "q": process.exit(0); return;
        case "c":
          if (activePane === "editor") {
            callBackend("file/save", {
              path: useStore.getState().openFiles[useStore.getState().activeFileIndex]?.path || "",
              content: useStore.getState().editorContent,
            }).catch(() => {});
          }
          return;
      }
    }

    if (key.escape) {
      if (activePane !== "tree") {
        useStore.getState().setActivePane("tree");
      }
      return;
    }

    if (key.return && activePane === "terminal") {
      const input = terminalInput;
      callBackend("terminal/write", { data: input + "\n" }).catch(() => {});
      useStore.getState().setTerminalInput("");
      return;
    }

    if (key.backspace && activePane === "terminal") {
      const cur = terminalInput;
      if (cur.length > 0) useStore.getState().setTerminalInput(cur.slice(0, -1));
      return;
    }

    if (activePane === "terminal" && input && input.length === 1 && input.charCodeAt(0) >= 32) {
      useStore.getState().setTerminalInput(terminalInput + input);
      return;
    }

    if (activePane === "tree") {
      const flat = flattenTree(treeData, treeExpanded, "");
      if (key.upArrow) {
        setTreeSelectedIndex(Math.max(0, treeSelectedIndex - 1));
        if (treeSelectedIndex <= treeScroll) setTreeScroll(Math.max(0, treeSelectedIndex - 1));
        return;
      }
      if (key.downArrow) {
        setTreeSelectedIndex(Math.min(flat.length - 1, treeSelectedIndex + 1));
        const panelHeight = Math.floor(stdout.rows * 0.8);
        if (treeSelectedIndex >= treeScroll + panelHeight - 3) {
          setTreeScroll(treeScroll + 1);
        }
        return;
      }
      if (key.leftArrow || key.rightArrow) {
        const node = flat[treeSelectedIndex];
        if (node && node.type === "directory") {
          toggleExpanded(node._path);
        }
        return;
      }
      if (key.return) {
        const node = flat[treeSelectedIndex];
        if (node) {
          if (node.type === "directory") {
            toggleExpanded(node._path);
          } else {
            callBackend("file/read", { path: node._path }).then((res: any) => {
              useStore.getState().openFile({
                path: res.path,
                language: res.language || "text",
                content: res.content || "",
              });
              useStore.getState().setEditorContent(res.content || "");
              useStore.getState().setCursor(0, 0);
              useStore.getState().setActivePane("editor");
            }).catch(() => {});
          }
        }
        return;
      }
    }

    if (activePane === "editor") {
      if (key.return) {
        const content = useStore.getState().editorContent;
        const lines = content.split("\n");
        const cl = useStore.getState().cursorLine;
        lines.splice(cl + 1, 0, "");
        const newContent = lines.join("\n");
        useStore.getState().setEditorContent(newContent);
        useStore.getState().setCursor(cl + 1, 0);
        return;
      }
      if (key.backspace) {
        const content = useStore.getState().editorContent;
        const cl = useStore.getState().cursorLine;
        const cc = useStore.getState().cursorCol;
        const lines = content.split("\n");
        if (cc > 0) {
          const line = lines[cl];
          lines[cl] = line.slice(0, cc - 1) + line.slice(cc);
          useStore.getState().setEditorContent(lines.join("\n"));
          useStore.getState().setCursor(cl, cc - 1);
        } else if (cl > 0) {
          const prevLen = lines[cl - 1].length;
          lines[cl - 1] += lines[cl];
          lines.splice(cl, 1);
          useStore.getState().setEditorContent(lines.join("\n"));
          useStore.getState().setCursor(cl - 1, prevLen);
        }
        return;
      }
      if (key.upArrow) {
        const cl = useStore.getState().cursorLine;
        if (cl > 0) useStore.getState().setCursor(cl - 1, useStore.getState().cursorCol);
        return;
      }
      if (key.downArrow) {
        const cl = useStore.getState().cursorLine;
        const lines = useStore.getState().editorContent.split("\n");
        if (cl < lines.length - 1) useStore.getState().setCursor(cl + 1, useStore.getState().cursorCol);
        return;
      }
      if (key.leftArrow) {
        const cc = useStore.getState().cursorCol;
        if (cc > 0) useStore.getState().setCursor(useStore.getState().cursorLine, cc - 1);
        return;
      }
      if (key.rightArrow) {
        const cc = useStore.getState().cursorCol;
        const cl = useStore.getState().cursorLine;
        const line = useStore.getState().editorContent.split("\n")[cl] || "";
        if (cc < line.length) useStore.getState().setCursor(cl, cc + 1);
        return;
      }
      if (input === "1") { useStore.getState().setActivePane("tree"); return; }
      if (input === "2") { useStore.getState().setActivePane("editor"); return; }
      if (input === "3") { useStore.getState().setActivePane("terminal"); return; }
      if (input && input.length === 1 && input.charCodeAt(0) >= 32) {
        const content = useStore.getState().editorContent;
        const cl = useStore.getState().cursorLine;
        const cc = useStore.getState().cursorCol;
        const lines = content.split("\n");
        lines[cl] = lines[cl].slice(0, cc) + input + lines[cl].slice(cc);
        useStore.getState().setEditorContent(lines.join("\n"));
        useStore.getState().setCursor(cl, cc + 1);
        return;
      }
    }
  });

  if (showPalette) {
    return <CommandPalette />;
  }

  const fileW = Math.max(10, Math.floor(cols * fileTreeWidth / 100));
  const restW = cols - fileW - 2;
  const editW = Math.floor(restW / 2);
  const termW = restW - editW;

  return (
    <Box flexDirection="column" height="100%">
      <Header />
      <Box flexGrow={1} flexDirection="row">
        <Box width={fileW} flexShrink={0}>
          <FileTree id="tree" panelWidth={fileW} />
        </Box>
        <Divider />
        <Box flexGrow={2}>
          <Editor id="editor" panelWidth={editW} />
        </Box>
        <Divider />
        <Box flexGrow={2}>
          <TerminalPanel id="terminal" panelWidth={termW} />
        </Box>
      </Box>
      <BottomBar />
    </Box>
  );
}

function flattenTree(
  nodes: any[],
  expanded: Record<string, boolean>,
  parentPath: string,
  depth: number = 0
): any[] {
  const result: any[] = [];
  for (const node of nodes) {
    const fullPath = parentPath ? `${parentPath}/${node.name}` : node.name;
    const flat = { ...node, _path: fullPath, _depth: depth };
    result.push(flat);
    if (node.type === "directory" && expanded[fullPath] && node.children) {
      result.push(...flattenTree(node.children, expanded, fullPath, depth + 1));
    }
  }
  return result;
}
