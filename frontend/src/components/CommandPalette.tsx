import { Box, Text, useFocus } from "ink";
import { useStore } from "../store.js";

export default function CommandPalette() {
  useFocus({ id: "palette", autoFocus: true });

  const commands = useStore((s) => s.paletteCommands);
  const filter = useStore((s) => s.paletteFilter);
  const selectedIndex = useStore((s) => s.paletteSelectedIndex);

  const filtered = filter
    ? commands.filter((c) => c.label.toLowerCase().includes(filter.toLowerCase()))
    : commands;

  return (
    <Box flexDirection="column" alignItems="center" justifyContent="center">
      <Box flexDirection="column" width={50} borderStyle="single" borderColor="#5ac1fe">
        <Box>
          <Text bold color="#5ac1fe">
            {" "}Command Palette{" "}
          </Text>
        </Box>
        <Box marginY={1} paddingX={1}>
          <Text color="#bfbdb6">&gt; {filter || "Type to filter..."}</Text>
        </Box>
        <Box flexDirection="column" minHeight={5}>
          {filtered.map((cmd, i) => (
            <Text
              key={cmd.id}
              color={i === selectedIndex ? "#000000" : "#bfbdb6"}
              backgroundColor={i === selectedIndex ? "#5ac1fe" : undefined}
            >
              {" "}{cmd.label}
            </Text>
          ))}
          {filtered.length === 0 && (
            <Text color="#4b4c4e"> No matching commands</Text>
          )}
        </Box>
        <Box marginTop={1}>
          <Text color="#4b4c4e"> Enter: select | Esc: close</Text>
        </Box>
      </Box>
    </Box>
  );
}
