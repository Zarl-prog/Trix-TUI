import { Box, Text } from "ink";

interface Props {
  title: string;
  isFocused: boolean;
  panelWidth: number;
}

export default function PanelHeader({ title, isFocused, panelWidth }: Props) {
  const label = ` ${title} `;
  const leftDashes = 2;
  const rightDashes = Math.max(0, panelWidth - leftDashes - label.length);
  const dashColor = "#3f4043";
  const textColor = isFocused ? "#5ac1fe" : "#bfbdb6";

  return (
    <Box height={1}>
      <Text color={dashColor}>{"─".repeat(leftDashes)}</Text>
      <Text bold color={textColor}>{label}</Text>
      <Text color={dashColor}>{"─".repeat(rightDashes)}</Text>
    </Box>
  );
}
