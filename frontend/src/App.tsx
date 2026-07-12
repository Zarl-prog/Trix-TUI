import { useInput, useFocusManager, useStdout, Box } from "ink";
import { useStore } from "./store.js";
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

  useInput((input, key) => {
    const { keybindingLayer, activePane } =
      useStore.getState();

    if (showPalette || keybindingLayer === "palette") {
      if (key.escape) {
        useStore.getState().closePalette();
        return;
      }
      if (key.return) {
        useStore.getState().paletteSelect();
        return;
      }
      if (key.upArrow) {
        useStore.getState().palettePrevious();
        return;
      }
      if (key.downArrow) {
        useStore.getState().paletteNext();
        return;
      }
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

    if (keybindingLayer === "insert") {
      return;
    }

    if (key.tab) {
      if (key.shift) {
        focusPrevious();
      } else {
        focusNext();
      }
      return;
    }

    if (input === "1") {
      useStore.getState().setActivePane("tree");
      return;
    }
    if (input === "2") {
      useStore.getState().setActivePane("editor");
      return;
    }
    if (input === "3") {
      useStore.getState().setActivePane("terminal");
      return;
    }

    if (input === ":") {
      useStore.getState().openPalette();
      return;
    }

    if (key.ctrl) {
      const ch = String.fromCharCode(input.charCodeAt(0) + 96);
      switch (ch) {
        case "p":
          useStore.getState().openPalette();
          return;
        case "q":
          process.exit(0);
          return;
      }
    }

    if (activePane === "tree") {
      if (key.leftArrow && key.ctrl) {
        useStore.getState().setFileTreeWidth(fileTreeWidth - 5);
        return;
      }
      if (key.rightArrow && key.ctrl) {
        useStore.getState().setFileTreeWidth(fileTreeWidth + 5);
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
