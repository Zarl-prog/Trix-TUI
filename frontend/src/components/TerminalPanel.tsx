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

  const terminalOutput = useStore((s) => s.terminalOutput);
  const terminalInput = useStore((s) => s.terminalInput);

  const lines = terminalOutput.split("\n").filter(Boolean);
  const recentLines = lines.slice(-100);

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader title="Terminal" isFocused={isFocused} panelWidth={panelWidth} />
      <Box flexGrow={1} flexDirection="column">
        <Box flexGrow={1} paddingX={1} flexDirection="column">
          {recentLines.length === 0 ? (
            <Text color="#8a8986">Terminal ready.</Text>
          ) : (
            recentLines.map((line, i) => (
              <Box key={i} height={1}>
                <Text color="#8a8986">{line}</Text>
              </Box>
            ))
          )}
        </Box>
        <Box height={1} paddingX={1}>
          <Text backgroundColor="#131721" color="#bfbdb6">
            {"❯ "}{terminalInput}{" ".repeat(Math.max(0, panelWidth - terminalInput.length - 4))}
          </Text>
        </Box>
      </Box>
    </Box>
  );
}
