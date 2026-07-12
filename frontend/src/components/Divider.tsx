import { useEffect } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId } from "../store.js";

interface Props {
  id: PaneId;
}

export default function Divider({ id }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  return (
    <Box width={1} flexShrink={0}>
      <Text color={isFocused ? "#5ac1fe" : "#3f4043"}>│</Text>
    </Box>
  );
}
