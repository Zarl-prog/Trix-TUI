import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
}

export default function TerminalPanel({ id }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader title="Terminal" isFocused={isFocused} />
      <Box flexGrow={1} flexDirection="column" paddingX={1}>
        <Box flexGrow={1}>
          <Text color="#8a8986">Terminal ready.</Text>
        </Box>
        <Box height={1} paddingX={1}>
          <Text color="#bfbdb6">❯ </Text>
        </Box>
      </Box>
    </Box>
  );
}
