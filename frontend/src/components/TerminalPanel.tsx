import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
  panelWidth: number;
}

export default function TerminalPanel({ id, panelWidth }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader title="Terminal" isFocused={isFocused} panelWidth={panelWidth} />
      <Box flexGrow={1} flexDirection="column">
        <Box flexGrow={1} paddingX={1}>
          <Text color="#8a8986">Terminal ready.</Text>
        </Box>
        <Box height={1} paddingX={1}>
          <Text backgroundColor="#131721" color="#bfbdb6">
            ❯ {" ".repeat(Math.max(0, panelWidth - 2))}
          </Text>
        </Box>
      </Box>
    </Box>
  );
}
