import { Box, Text } from "ink";
import { useStore } from "../store.js";

export default function Header() {
  const folderPath = useStore((s) => s.folderPath);
  const themeName = useStore((s) => s.themeName);

  return (
    <Box height={1} paddingX={1}>
      <Text bold color="#5ac1fe">
        TRIX
      </Text>
      <Box flexGrow={1} justifyContent="center">
        <Text color="#4b4c4e">
          {folderPath || ""}
        </Text>
      </Box>
      <Text color="#4b4c4e">
        {themeName}
      </Text>
    </Box>
  );
}
