import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";

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
    <Box
      flexDirection="column"
      flexGrow={1}
      borderStyle={isFocused ? "bold" : "single"}
      borderColor={isFocused ? "#5ac1fe" : "#3f4043"}
    >
      <Box>
        <Text bold color={isFocused ? "#5ac1fe" : "#bfbdb6"}>
          {" "}Editor{" "}
        </Text>
        {activeFile && (
          <Text color="#8a8986">— {activeFile.path}</Text>
        )}
      </Box>
      <Box flexGrow={1} flexDirection="column" paddingX={1}>
        {activeFile ? (
          <Text color="#bfbdb6">{activeFile.content}</Text>
        ) : (
          <Text color="#4b4c4e">
            No file open{'\n'}Press Ctrl+O to open a file
          </Text>
        )}
      </Box>
    </Box>
  );
}
