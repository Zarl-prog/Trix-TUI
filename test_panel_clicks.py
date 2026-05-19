import asyncio
from pathlib import Path
from main import TrixApp
from ClickableDirectoryTree import ClickableDirectoryTree if False else None # dynamic import check
from textual.events import Click
from textual.widgets import DirectoryTree, TextArea, Input

class ClickTestApp(TrixApp):
    async def on_ready(self) -> None:
        out = []
        out.append("APP READY FOR CLICK TEST!")
        
        # We will simulate click events at coordinates corresponding to the center of each panel region.
        files_panel = self.query_one("#files-panel")
        editor_panel = self.query_one("#editor-panel")
        terminal_panel = self.query_one("#terminal-panel")
        
        # 1. Click Files Panel
        fx = files_panel.region.x + files_panel.region.width // 2
        fy = files_panel.region.y + files_panel.region.height // 2
        out.append(f"Simulating click on Files Panel at ({fx}, {fy})")
        
        click_event = Click(
            x=fx, y=fy, screen_x=fx, screen_y=fy,
            button=1, ctrl=False, shift=False, meta=False
        )
        # Post the click event to the screen
        self.screen.post_message(click_event)
        await asyncio.sleep(0.1) # yield control to event loop
        
        focused = self.focused
        out.append(f"  Focused widget after Files click: {focused.__class__.__name__ if focused else 'None'}")
        
        # 2. Click Editor Panel
        ex = editor_panel.region.x + editor_panel.region.width // 2
        ey = editor_panel.region.y + editor_panel.region.height // 2
        out.append(f"Simulating click on Editor Panel at ({ex}, {ey})")
        
        click_event = Click(
            x=ex, y=ey, screen_x=ex, screen_y=ey,
            button=1, ctrl=False, shift=False, meta=False
        )
        self.screen.post_message(click_event)
        await asyncio.sleep(0.1)
        
        focused = self.focused
        out.append(f"  Focused widget after Editor click: {focused.__class__.__name__ if focused else 'None'}")
        
        # 3. Click Terminal Panel (Input area at the bottom)
        tx = terminal_panel.region.x + terminal_panel.region.width // 2
        ty = terminal_panel.region.y + terminal_panel.region.height - 2 # near bottom
        out.append(f"Simulating click on Terminal Panel Input at ({tx}, {ty})")
        
        click_event = Click(
            x=tx, y=ty, screen_x=tx, screen_y=ty,
            button=1, ctrl=False, shift=False, meta=False
        )
        self.screen.post_message(click_event)
        await asyncio.sleep(0.1)
        
        focused = self.focused
        out.append(f"  Focused widget after Terminal Input click: {focused.__class__.__name__ if focused else 'None'}")
        
        # Write results
        Path("click_test_results.txt").write_text("\n".join(out))
        self.exit()

if __name__ == "__main__":
    app = ClickTestApp()
    app.run()
