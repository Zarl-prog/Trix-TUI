import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
  panelWidth: number;
}

export default function Editor({ id, panelWidth }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  const openFiles = useStore((s) => s.openFiles);
  const activeFileIndex = useStore((s) => s.activeFileIndex);
  const editorContent = useStore((s) => s.editorContent);
  const cursorLine = useStore((s) => s.cursorLine);
  const cursorCol = useStore((s) => s.cursorCol);
  const activeFile = activeFileIndex >= 0 ? openFiles[activeFileIndex] : null;

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader
        title={activeFile ? activeFile.path.split("/").pop() || "Editor" : "Editor"}
        isFocused={isFocused}
        panelWidth={panelWidth}
      />
      <Box flexGrow={1} flexDirection="column" paddingX={1} paddingY={0}>
        {activeFile ? (
          <Box flexGrow={1}>
            <Box flexDirection="column">
              {editorContent.split("\n").map((line, i) => (
                <Box key={i} height={1}>
                  <Text color={cursorLine === i ? "#5ac1fe" : "#3f4043"} bold={cursorLine === i}>
                    {String(i + 1).padStart(3, " ")}{" "}
                  </Text>
                  <Text
                    backgroundColor={cursorLine === i && isFocused ? "#131721" : undefined}
                    color="#bfbdb6"
                  >
                    {line || " "}
                  </Text>
                </Box>
              ))}
            </Box>
          </Box>
        ) : (
          <Box flexGrow={1} alignItems="center" justifyContent="center">
            <Box flexDirection="column" alignItems="center">
              <Text bold color="#4b4c4e">Welcome to TRIX</Text>
              <Text color="#4b4c4e">{"\n"}Open a file from the Files panel</Text>
              <Text color="#4b4c4e">or press Ctrl+O to open a folder</Text>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
