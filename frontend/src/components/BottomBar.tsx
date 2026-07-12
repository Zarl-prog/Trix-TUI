import { Box, Text } from "ink";

const KEYBINDINGS = [
  { key: " ^q ", desc: "Quit  " },
  { key: " f1 ", desc: "Help  " },
  { key: " ^g ", desc: "Git  " },
  { key: " ^t ", desc: "Theme  " },
  { key: " ^b ", desc: "Files  " },
  { key: " ^o ", desc: "Open  " },
];

export default function BottomBar() {
  return (
    <Box height={1} paddingX={1}>
      <Text backgroundColor="#131721">
        {KEYBINDINGS.map((kb, i) => (
          <Text key={i}>
            <Text bold color="#5ac1fe">
              {kb.key}
            </Text>
            <Text color="#8a8986">
              {kb.desc}
            </Text>
          </Text>
        ))}
      </Text>
    </Box>
  );
}
