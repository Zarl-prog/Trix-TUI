import { useInput, useFocusManager, Box } from "ink";
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

  useInput((input, key) => {
    const { keybindingLayer, activePane, showPalette } =
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
  });

  const fileTreeWidth = useStore((s) => s.fileTreeWidth);
  const showPalette = useStore((s) => s.showPalette);

  if (showPalette) {
    return <CommandPalette />;
  }

  return (
    <Box flexDirection="column" height="100%">
      <Header />
      <Box flexGrow={1} flexDirection="row">
        <Box width={`${fileTreeWidth}%`} flexShrink={0} minWidth={10}>
          <FileTree id="tree" />
        </Box>
        <Divider />
        <Box flexGrow={2}>
          <Editor id="editor" />
        </Box>
        <Divider />
        <Box flexGrow={2}>
          <TerminalPanel id="terminal" />
        </Box>
      </Box>
      <BottomBar />
    </Box>
  );
}
