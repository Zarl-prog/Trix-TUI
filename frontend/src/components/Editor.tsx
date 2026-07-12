import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
}

export default function Editor({ id }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  const openFiles = useStore((s) => s.openFiles);
  const activeFileIndex = useStore((s) => s.activeFileIndex);
  const activeFile = activeFileIndex >= 0 ? openFiles[activeFileIndex] : null;

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader
        title={activeFile ? activeFile.path.split("/").pop() || "Editor" : "Editor"}
        isFocused={isFocused}
      />
      <Box flexGrow={1} flexDirection="column" paddingX={1} paddingY={0}>
        {activeFile ? (
          <Text color="#bfbdb6">{activeFile.content}</Text>
        ) : (
          <Box flexGrow={1} alignItems="center" justifyContent="center">
            <Box flexDirection="column" alignItems="center">
              <Text bold color="#4b4c4e">
                No file open
              </Text>
              <Text color="#4b4c4e">
                Press Ctrl+O to open a file
              </Text>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
