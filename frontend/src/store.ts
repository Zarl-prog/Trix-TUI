import { create } from "zustand";

export type PaneId = "tree" | "editor" | "terminal";
export type KeybindingLayer = "normal" | "insert" | "palette";

export interface OpenFile {
  path: string;
  language: string;
  content: string;
}

export interface TreeNode {
  name: string;
  type: "file" | "directory";
  children?: TreeNode[];
}

export interface SearchResult {
  file: string;
  line: number;
  column: number;
  text: string;
}

export interface PaletteCommand {
  id: string;
  label: string;
  action: () => void;
}

export interface AppState {
  activePane: PaneId;
  setActivePane: (id: PaneId) => void;

  folderPath: string;
  setFolderPath: (path: string) => void;

  themeName: string;
  setThemeName: (name: string) => void;

  keybindingLayer: KeybindingLayer;
  previousLayer: KeybindingLayer;
  setKeybindingLayer: (layer: KeybindingLayer) => void;
  restorePreviousLayer: () => void;

  showPalette: boolean;
  paletteSelectedIndex: number;
  paletteFilter: string;
  paletteCommands: PaletteCommand[];
  openPalette: () => void;
  closePalette: () => void;
  setPaletteFilter: (filter: string) => void;
  paletteNext: () => void;
  palettePrevious: () => void;
  paletteSelect: () => void;

  openFiles: OpenFile[];
  activeFileIndex: number;
  openFile: (file: OpenFile) => void;
  closeFile: (index: number) => void;

  fileTreeWidth: number;
  setFileTreeWidth: (width: number) => void;

  treeData: TreeNode[];
  setTreeData: (data: TreeNode[]) => void;
  treeSelectedIndex: number;
  setTreeSelectedIndex: (idx: number) => void;
  treeExpanded: Record<string, boolean>;
  toggleExpanded: (path: string) => void;
  treeScroll: number;
  setTreeScroll: (scroll: number) => void;

  editorContent: string;
  setEditorContent: (content: string) => void;
  cursorLine: number;
  cursorCol: number;
  setCursor: (line: number, col: number) => void;

  terminalOutput: string;
  appendTerminalOutput: (data: string) => void;
  clearTerminalOutput: () => void;
  terminalInput: string;
  setTerminalInput: (val: string) => void;

  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;
}

export const useStore = create<AppState>((set, get) => ({
  activePane: "tree",
  setActivePane: (id) => set({ activePane: id }),

  folderPath: "",
  setFolderPath: (path) => set({ folderPath: path }),

  themeName: "Ayu Dark",
  setThemeName: (name) => set({ themeName: name }),

  keybindingLayer: "normal",
  previousLayer: "normal",
  setKeybindingLayer: (layer) =>
    set((s) => ({ keybindingLayer: layer, previousLayer: s.keybindingLayer })),
  restorePreviousLayer: () =>
    set((s) => ({ keybindingLayer: s.previousLayer })),

  showPalette: false,
  paletteSelectedIndex: 0,
  paletteFilter: "",
  paletteCommands: [
    { id: "toggle-files", label: "Toggle File Tree", action: () => {} },
    { id: "save", label: "Save File", action: () => {} },
    { id: "quit", label: "Quit", action: () => process.exit(0) },
  ],
  openPalette: () =>
    set((s) => ({
      showPalette: true,
      previousLayer: s.keybindingLayer,
      keybindingLayer: "palette",
      paletteSelectedIndex: 0,
      paletteFilter: "",
    })),
  closePalette: () =>
    set((s) => ({
      showPalette: false,
      keybindingLayer: s.previousLayer,
      paletteFilter: "",
    })),
  setPaletteFilter: (filter) => set({ paletteFilter: filter, paletteSelectedIndex: 0 }),
  paletteNext: () =>
    set((s) => {
      const cmds = s.paletteCommands.filter((c) =>
        c.label.toLowerCase().includes(s.paletteFilter.toLowerCase())
      );
      return { paletteSelectedIndex: Math.min(s.paletteSelectedIndex + 1, cmds.length - 1) };
    }),
  palettePrevious: () =>
    set((s) => ({
      paletteSelectedIndex: Math.max(s.paletteSelectedIndex - 1, 0),
    })),
  paletteSelect: () => {
    const s = get();
    const filtered = s.paletteCommands.filter((c) =>
      c.label.toLowerCase().includes(s.paletteFilter.toLowerCase())
    );
    const cmd = filtered[s.paletteSelectedIndex];
    if (cmd) {
      cmd.action();
      s.closePalette();
    }
  },

  openFiles: [],
  activeFileIndex: -1,
  openFile: (file) =>
    set((s) => {
      const existing = s.openFiles.findIndex((f) => f.path === file.path);
      if (existing !== -1) return { activeFileIndex: existing };
      return { openFiles: [...s.openFiles, file], activeFileIndex: s.openFiles.length };
    }),
  closeFile: (index) =>
    set((s) => {
      const files = s.openFiles.filter((_, i) => i !== index);
      const activeIdx = s.activeFileIndex >= files.length ? files.length - 1 : s.activeFileIndex;
      return { openFiles: files, activeFileIndex: activeIdx };
    }),

  fileTreeWidth: 20,
  setFileTreeWidth: (width) => set({ fileTreeWidth: Math.max(10, Math.min(60, width)) }),

  treeData: [],
  setTreeData: (data) => set({ treeData: data }),
  treeSelectedIndex: 0,
  setTreeSelectedIndex: (idx) => set({ treeSelectedIndex: idx }),
  treeExpanded: {},
  toggleExpanded: (path) =>
    set((s) => ({
      treeExpanded: { ...s.treeExpanded, [path]: !s.treeExpanded[path] },
    })),
  treeScroll: 0,
  setTreeScroll: (scroll) => set({ treeScroll: scroll }),

  editorContent: "",
  setEditorContent: (content) => set({ editorContent: content }),
  cursorLine: 0,
  cursorCol: 0,
  setCursor: (line, col) => set({ cursorLine: line, cursorCol: col }),

  terminalOutput: "",
  appendTerminalOutput: (data) =>
    set((s) => {
      const maxLen = 50000;
      const out = s.terminalOutput + data;
      return { terminalOutput: out.length > maxLen ? out.slice(-maxLen) : out };
    }),
  clearTerminalOutput: () => set({ terminalOutput: "" }),
  terminalInput: "",
  setTerminalInput: (val) => set({ terminalInput: val }),

  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),
}));
