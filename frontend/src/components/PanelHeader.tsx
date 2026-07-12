import { Box, Text } from "ink";

interface Props {
  title: string;
  isFocused: boolean;
}

export default function PanelHeader({ title, isFocused }: Props) {
  return (
    <Box height={1} paddingX={1}>
      <Text color="#3f4043">── </Text>
      <Text bold color={isFocused ? "#5ac1fe" : "#bfbdb6"}>
        {title}
      </Text>
      <Text color="#3f4043"> ──</Text>
    </Box>
  );
}
