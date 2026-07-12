import { useEffect, useMemo } from "react";
import { Box, Text, useFocus } from "ink";
import { useStore, type PaneId, type TreeNode } from "../store.js";
import PanelHeader from "./PanelHeader.js";

interface Props {
  id: PaneId;
  panelWidth: number;
}

function flattenTree(
  nodes: TreeNode[],
  expanded: Record<string, boolean>,
  parentPath: string = "",
  depth: number = 0
): (TreeNode & { _path: string; _depth: number })[] {
  const result: any[] = [];
  for (const node of nodes) {
    const fullPath = parentPath ? `${parentPath}/${node.name}` : node.name;
    result.push({ ...node, _path: fullPath, _depth: depth });
    if (node.type === "directory" && expanded[fullPath] && node.children) {
      result.push(...flattenTree(node.children, expanded, fullPath, depth + 1));
    }
  }
  return result;
}

export default function FileTree({ id, panelWidth }: Props) {
  const { isFocused } = useFocus({ id });
  const setActivePane = useStore((s) => s.setActivePane);

  useEffect(() => {
    if (isFocused) setActivePane(id);
  }, [isFocused, id, setActivePane]);

  const treeData = useStore((s) => s.treeData);
  const treeSelectedIndex = useStore((s) => s.treeSelectedIndex);
  const treeExpanded = useStore((s) => s.treeExpanded);
  const treeScroll = useStore((s) => s.treeScroll);

  const flat = useMemo(
    () => flattenTree(treeData, treeExpanded),
    [treeData, treeExpanded]
  );

  const visible = flat.slice(treeScroll, treeScroll + 100);

  return (
    <Box flexDirection="column" height="100%">
      <PanelHeader title="Files" isFocused={isFocused} panelWidth={panelWidth} />
      <Box flexGrow={1} flexDirection="column" paddingX={1}>
        {visible.length === 0 ? (
          <Text color="#4b4c4e">No files loaded</Text>
        ) : (
          visible.map((node, i) => {
            const absIdx = treeScroll + i;
            const selected = absIdx === treeSelectedIndex && isFocused;
            const indent = "  ".repeat(node._depth);
            const icon = node.type === "directory"
              ? (treeExpanded[node._path] ? "▼" : "▶")
              : "─";

            return (
              <Box key={node._path} height={1}>
                <Text
                  color={selected ? "#0d1016" : "#bfbdb6"}
                  backgroundColor={selected ? "#5ac1fe" : undefined}
                  bold={selected}
                >
                  {indent}{icon} {node.name}
                </Text>
              </Box>
            );
          })
        )}
      </Box>
    </Box>
  );
}
