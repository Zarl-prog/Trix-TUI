package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	backgroundColor   = lipgloss.Color("#0d1016")
	borderColor       = lipgloss.Color("#3f4043")
	activeColor        = lipgloss.Color("#5ac1fe")
	inactiveColor      = lipgloss.Color("#bfbdb6")
	headerFolderColor = lipgloss.Color("#4b4c4e")
	bottomBarBg       = lipgloss.Color("#131721")
	dividerBg          = lipgloss.Color("#1a1d23")
	fileColor         = lipgloss.Color("#8a8986")
	folderColor       = lipgloss.Color("#bfbdb6")
)

type FileNode struct {
	Name     string     `json:"name"`
	Path     string     `json:"path"`
	IsDir    bool       `json:"is_dir"`
	Children []FileNode `json:"children,omitempty"`
}

type model struct {
	bridge   *Bridge
	err      error
	width    int
	height   int
	active   string // "files", "editor", "terminal"
	rootNode FileNode
	cursor   int
	flatTree []FileNode
}

func flattenTree(node FileNode, depth int) []FileNode {
	// Simple flattening for now, can be improved with expansion state
	res := []FileNode{node}
	for _, child := range node.Children {
		res = append(res, flattenTree(child, depth+1)...)
	}
	return res
}

func fetchFileTree(b *Bridge, path string) tea.Cmd {
	return func() tea.Msg {
		res, err := b.Call("get_file_tree", map[string]string{"path": path})
		if err != nil {
			return err
		}
		var result struct {
			Status string   `json:"status"`
			Tree   FileNode `json:"tree"`
		}
		if err := json.Unmarshal(res, &result); err != nil {
			return err
		}
		return result.Tree
	}
}

func initialModel() model {
	b, _ := NewBridge("python")
	return model{
		bridge: b,
		active: "terminal",
	}
}

func (m model) Init() tea.Cmd {
	return fetchFileTree(m.bridge, ".")
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case FileNode:
		m.rootNode = msg
		m.flatTree = flattenTree(m.rootNode, 0)
	case error:
		m.err = msg
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			if m.bridge != nil {
				m.bridge.Close()
			}
			return m, tea.Quit
		case "up":
			if m.active == "files" && m.cursor > 0 {
				m.cursor--
			}
		case "down":
			if m.active == "files" && m.cursor < len(m.flatTree)-1 {
				m.cursor++
			}
		case "ctrl+r":
			return m, fetchFileTree(m.bridge, ".")
		case "ctrl+]":
			switch m.active {
			case "files":
				m.active = "editor"
			case "editor":
				m.active = "terminal"
			case "terminal":
				m.active = "files"
			}
		}
	}
	return m, nil
}

func renderFileTree(m model, width, height int) string {
	var s strings.Builder
	for i, node := range m.flatTree {
		if i >= height {
			break
		}

		cursor := "  "
		style := lipgloss.NewStyle()
		if i == m.cursor && m.active == "files" {
			cursor = "> "
			style = style.Background(activeColor).Foreground(backgroundColor).Bold(true)
		} else {
			if node.IsDir {
				style = style.Foreground(folderColor)
			} else {
				style = style.Foreground(fileColor)
			}
		}

		icon := "─ "
		if node.IsDir {
			icon = "▶ "
		}

		line := fmt.Sprintf("%s%s%s", cursor, icon, node.Name)
		if len(line) > width {
			line = line[:width]
		}
		s.WriteString(style.Width(width).Render(line) + "\n")
	}
	return s.String()
}

func renderPanelHeader(title string, width int, active bool) string {
	textColor := inactiveColor
	if active {
		textColor = activeColor
	}

	label := fmt.Sprintf(" %s ", title)
	leftDashes := 2
	rightDashes := width - leftDashes - len(label)
	if rightDashes < 0 {
		rightDashes = 0
	}

	header := lipgloss.NewStyle().Foreground(borderColor).Render("──") +
		lipgloss.NewStyle().Foreground(textColor).Render(label) +
		lipgloss.NewStyle().Foreground(borderColor).Render(strings.Repeat("─", rightDashes))

	return header
}

func (m model) View() string {
	if m.err != nil {
		return fmt.Sprintf("Error: %v\n", m.err)
	}
	if m.width == 0 || m.height == 0 {
		return "Initializing..."
	}

	// Calculate dimensions
	headerHeight := 1
	footerHeight := 1
	mainHeight := m.height - headerHeight - footerHeight
	
	// Panel widths
	filesWidth := m.width / 5
	dividerWidth := 1
	remainingWidth := m.width - filesWidth - (dividerWidth * 2)
	editorWidth := remainingWidth / 2
	terminalWidth := remainingWidth - editorWidth

	// Header
	headerStyle := lipgloss.NewStyle().
		Height(headerHeight).
		Width(m.width).
		Background(backgroundColor)
	
	brand := lipgloss.NewStyle().Foreground(activeColor).Bold(true).Render("TRIX")
	folder := lipgloss.NewStyle().Foreground(headerFolderColor).Width(m.width - 15).Align(lipgloss.Center).Render(".")
	theme := lipgloss.NewStyle().Foreground(headerFolderColor).Render("Ayu Dark")
	header := headerStyle.Render(lipgloss.JoinHorizontal(lipgloss.Left, brand, folder, theme))

	// Main Area
	panelStyle := lipgloss.NewStyle().Height(mainHeight).Background(backgroundColor)
	dividerStyle := lipgloss.NewStyle().Width(dividerWidth).Height(mainHeight).Background(dividerBg)

	// Files Panel
	filesHeader := renderPanelHeader("Files", filesWidth, m.active == "files")
	filesContent := renderFileTree(m, filesWidth, mainHeight-1)
	filesPanel := panelStyle.Width(filesWidth).Render(lipgloss.JoinVertical(lipgloss.Left, filesHeader, filesContent))

	// Editor Panel
	editorHeader := renderPanelHeader("Editor", editorWidth, m.active == "editor")
	editorContent := lipgloss.NewStyle().Width(editorWidth).Height(mainHeight - 1).Render("Editor Content...")
	editorPanel := panelStyle.Width(editorWidth).Render(lipgloss.JoinVertical(lipgloss.Left, editorHeader, editorContent))

	// Terminal Panel
	terminalHeader := renderPanelHeader("Terminal", terminalWidth, m.active == "terminal")
	terminalContent := lipgloss.NewStyle().Width(terminalWidth).Height(mainHeight - 1).Render("Terminal Content...")
	terminalPanel := panelStyle.Width(terminalWidth).Render(lipgloss.JoinVertical(lipgloss.Left, terminalHeader, terminalContent))

	mainArea := lipgloss.JoinHorizontal(lipgloss.Top,
		filesPanel,
		dividerStyle.Render(""),
		editorPanel,
		dividerStyle.Render(""),
		terminalPanel,
	)

	// Footer
	footerStyle := lipgloss.NewStyle().
		Height(footerHeight).
		Width(m.width).
		Background(bottomBarBg)
	
	keyStyle := lipgloss.NewStyle().Foreground(activeColor).Bold(true)
	descStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#8a8986"))
	
	footer := footerStyle.Render(lipgloss.JoinHorizontal(lipgloss.Left,
		keyStyle.Render(" ^q "), descStyle.Render("Quit  "),
		keyStyle.Render(" f1 "), descStyle.Render("Help  "),
		keyStyle.Render(" ^g "), descStyle.Render("Git   "),
		keyStyle.Render(" ^t "), descStyle.Render("Theme "),
		keyStyle.Render(" ^b "), descStyle.Render("Files "),
		keyStyle.Render(" ^o "), descStyle.Render("Open  "),
	))

	return lipgloss.JoinVertical(lipgloss.Left, header, mainArea, footer)
}


func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Alas, there's been an error: %v", err)
		os.Exit(1)
	}
}
