import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";

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
    <Box
      flexDirection="column"
      height={10}
      borderStyle={isFocused ? "bold" : "single"}
      borderColor={isFocused ? "#5ac1fe" : "#3f4043"}
    >
      <Box>
        <Text bold color={isFocused ? "#5ac1fe" : "#bfbdb6"}>
          {" "}Terminal{" "}
        </Text>
      </Box>
      <Box flexGrow={1} paddingX={1}>
        <Text color="#8a8986">Terminal ready.</Text>
      </Box>
    </Box>
  );
}
