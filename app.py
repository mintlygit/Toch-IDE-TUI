import asyncio
import re
import subprocess
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, DirectoryTree, Log, TextArea, 
    Input, Static, TabbedContent, TabPane
)
from textual.containers import Horizontal, Vertical
from textual import work, on
from textual.binding import Binding

from core.config import LANGUAGE_MAP
from core.widgets import SystemMonitor, FileInfo, SearchWidget, CodeMinimap

class TochIDE(App):
    TITLE = "TochIDE Ultimate"
    CSS_PATH = "styles.tcss"
    
    BINDINGS = [
        Binding("ctrl+b", "toggle_zen_mode", "Zen Mode"),
        Binding("f1", "next_theme", "Switch Theme"),
        Binding("ctrl+g", "toggle_minimap", "Minimap"),
        Binding("ctrl+f", "search_focus", "Find"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+w", "close_tab", "Close"),
        Binding("ctrl+t", "focus_terminal", "Terminal"),
        Binding("ctrl+l", "clear_terminal", "Clear Log"),
        Binding("ctrl+q", "quit", "Exit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left-panel", classes="panel"):
                yield DirectoryTree("./", id="tree-view")
            
            with Vertical(id="center-panel"):
                with Horizontal(id="editor-container"):
                    with TabbedContent(id="tabs"):
                        with TabPane("Dashboard", id="welcome"):
                            yield Static("TochIDE Ready\n[b]F1[/]: Themes | [b]Ctrl+B[/]: Zen\n[b]Ctrl+T[/]: Terminal", id="welcome-msg")
                    yield CodeMinimap(id="minimap", classes="hidden")
                
                with Horizontal(id="bottom-panel"):
                    yield Log(id="terminal-log")
                    yield Input(placeholder="Shell command...", id="command-input")
            
            with Vertical(id="right-panel", classes="panel"):
                yield SystemMonitor(id="mon-widget", classes="tool-box")
                yield FileInfo(id="info-widget", classes="tool-box")
                yield SearchWidget(id="search-widget", classes="tool-box")
        
        with Horizontal(id="status-bar"):
            yield Static("📂 Ready", id="status-left")
            yield Static("", id="status-center", expand=True)
            yield Static("UTF-8", id="status-right")
        yield Footer()

    def on_mount(self):
        self.themes = ["dark", "light", "custom"]
        self.current_theme_idx = 0
        self.active_editor = None
        self.open_files = {}
        self.apply_theme("dark")
        self.run_resource_monitor()

    def apply_theme(self, theme_name: str):
        theme_file = Path(f"themes/{theme_name}.tcss")
        if not theme_file.exists(): return

        try:
            theme_vars = theme_file.read_text()
            base_style = Path("styles.tcss").read_text()
            self.app.refresh_css(theme_vars + "\n" + base_style)
            self.notify(f"Theme: {theme_name.upper()}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_next_theme(self):
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.themes)
        self.apply_theme(self.themes[self.current_theme_idx])

    def action_focus_terminal(self):
        self.query_one("#command-input").focus()

    def action_clear_terminal(self):
        self.query_one("#terminal-log").clear()

    @on(Input.Submitted, "#command-input")
    @work(thread=True)
    def run_shell_command(self, event: Input.Submitted):
        cmd = event.value.strip()
        if not cmd: return
        
        log = self.query_one("#terminal-log")
        log.write_line(f"\n[bold cyan]> {cmd}[/]")
        self.call_from_thread(event.input.set_value, "")

        try:
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate()
            if stdout: log.write_line(stdout)
            if stderr: log.write_line(f"[red]{stderr}[/]")
        except Exception as e:
            log.write_line(f"[bold red]Error:[/] {e}")

    def action_toggle_zen_mode(self):
        self.query_one("#left-panel").toggle_class("hidden")
        self.query_one("#right-panel").toggle_class("hidden")

    def action_toggle_minimap(self):
        m = self.query_one("#minimap")
        m.toggle_class("hidden")
        if self.active_editor and not m.has_class("hidden"):
            m.update_minimap(self.active_editor.text)

    def action_search_focus(self):
        self.query_one("#right-panel").remove_class("hidden")
        self.query_one("#search-input").focus()

    @on(Input.Changed, "#search-input")
    def on_search(self, event: Input.Changed):
        if self.active_editor and event.value:
            text = self.active_editor.text
            match = re.search(re.escape(event.value), text, re.IGNORECASE)
            if match:
                start = match.start()
                lines = text[:start].splitlines()
                row = len(lines) - 1 if lines else 0
                col = len(lines[-1]) if lines else start
                self.active_editor.selection = ((row, col), (row, col + len(event.value)))
                self.active_editor.cursor_location = (row, col)

    @on(DirectoryTree.FileSelected)
    def handle_file(self, event):
        self.open_file(Path(event.path))

    @work
    async def open_file(self, path: Path):
        if path.is_dir() or path in self.open_files:
            if path in self.open_files: self.query_one("#tabs").active = self.open_files[path]
            return
        try:
            content = path.read_text(encoding="utf-8")
            editor = TextArea(show_line_numbers=True, theme="monokai")
            editor.language = LANGUAGE_MAP.get(path.suffix, "python")
            editor.text = content
            
            tab_id = f"tab_{hash(str(path)) & 0xffff}"
            pane = TabPane(path.name, id=tab_id)
            pane.file_path = path
            
            await self.query_one("#tabs").add_pane(pane)
            await pane.mount(editor)
            self.query_one("#tabs").active = tab_id
            self.open_files[path] = tab_id
            self.active_editor = editor
            self.query_one("#info-widget").update_info(path)
            self.query_one("#status-left").update(f"📂 {path.name}")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(TabbedContent.TabActivated)
    def handle_tab_switch(self, event):
        if event.pane and event.pane.id != "welcome":
            self.active_editor = event.pane.query_one(TextArea)
            self.query_one("#info-widget").update_info(getattr(event.pane, "file_path", None))
        else:
            self.active_editor = None

    @on(TextArea.SelectionChanged)
    def on_cursor_move(self, event):
        m = self.query_one("#minimap")
        if not m.has_class("hidden"):
            m.sync_scroll(event.text_area.cursor_location[0])
        loc = event.text_area.cursor_location
        self.query_one("#status-center").update(f"LN {loc[0]+1}, COL {loc[1]+1}")

    @on(TextArea.Changed)
    def on_text_change(self, event):
        m = self.query_one("#minimap")
        if not m.has_class("hidden"):
            m.update_minimap(event.text_area.text)

    async def action_save_file(self):
        tabs = self.query_one("#tabs")
        if tabs.active and tabs.active != "welcome":
            pane = self.query_one(f"#{tabs.active}")
            if self.active_editor and hasattr(pane, "file_path"):
                pane.file_path.write_text(self.active_editor.text)
                sb = self.query_one("#status-bar")
                sb.add_class("saving")
                self.notify(f"Saved: {pane.file_path.name}")
                await asyncio.sleep(0.4)
                sb.remove_class("saving")

    def action_close_tab(self):
        tabs = self.query_one("#tabs")
        if tabs.active and tabs.active != "welcome":
            pane = self.query_one(f"#{tabs.active}")
            path = getattr(pane, "file_path", None)
            if path in self.open_files: del self.open_files[path]
            pane.remove()

    @work(exclusive=True)
    async def run_resource_monitor(self):
        while True:
            try: self.query_one("#mon-widget").update_stats()
            except: pass
            await asyncio.sleep(3)

if __name__ == "__main__":
    TochIDE().run()

