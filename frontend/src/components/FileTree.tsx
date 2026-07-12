import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
}

export default function FileTree({ id }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  const entries = useStore((s) => s.fileTreeData);

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader title="Files" isFocused={isFocused} />
      <Box flexGrow={1} flexDirection="column" paddingX={1}>
        {entries.length === 0 ? (
          <Text color="#4b4c4e">No files loaded</Text>
        ) : (
          entries.map((entry, i) => (
            <Text key={i} color={entry.type === "directory" ? "#bfbdb6" : "#8a8986"}>
              {entry.type === "directory" ? "▶" : "─"} {entry.name}
            </Text>
          ))
        )}
      </Box>
    </Box>
  );
}
