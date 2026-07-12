import { Box, Text } from "ink";

const KEYBINDINGS = [
  { key: "^q", desc: "Quit" },
  { key: "F1", desc: "Help" },
  { key: "^g", desc: "Git" },
  { key: "^t", desc: "Theme" },
  { key: "^b", desc: "Files" },
  { key: "^o", desc: "Open" },
  { key: "^s", desc: "Save" },
  { key: "^f", desc: "Search" },
  { key: "^p", desc: "Palette" },
];

export default function BottomBar() {
  return (
    <Box height={1} paddingX={1}>
      {KEYBINDINGS.map((kb, i) => (
        <Box key={i}>
          <Text bold color="#5ac1fe">
            {kb.key}
          </Text>
          <Text color="#8a8986">
            {" "}{kb.desc}{"  "}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
