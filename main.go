package main

import (
	"fmt"
	"os"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	backgroundColor = lipgloss.Color("#0d1016")
	borderColor     = lipgloss.Color("#3f4043")
	activeColor      = lipgloss.Color("#5ac1fe")
	inactiveColor    = lipgloss.Color("#bfbdb6")
	headerFolderColor = lipgloss.Color("#4b4c4e")
	bottomBarBg      = lipgloss.Color("#131721")
	dividerBg        = lipgloss.Color("#1a1d23")
)

type model struct {
	bridge *Bridge
	err    error
	width  int
	height int
	active string // "files", "editor", "terminal"
}

func initialModel() model {
	b, _ := NewBridge("python")
	return model{
		bridge: b,
		active: "terminal",
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
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
	filesContent := lipgloss.NewStyle().Width(filesWidth).Height(mainHeight - 1).Render("File Tree...")
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
