from textual.widgets import Static, Label, Input
from textual.containers import Vertical
import psutil
from datetime import datetime

class SystemMonitor(Vertical):
    def compose(self):
        yield Label("💻 SYSTEM", classes="tool-label")
        yield Static("CPU: 0% | RAM: 0%", id="sys-stats")

    def update_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.query_one("#sys-stats").update(f"CPU: {cpu}% | RAM: {ram}%")
        except: pass

class FileInfo(Vertical):
    def compose(self):
        yield Label("📊 INFO", classes="tool-label")
        yield Static("No file active", id="file-data")

    def update_info(self, path=None):
        if path and path.exists():
            size = path.stat().st_size / 1024
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime('%H:%M')
            self.query_one("#file-data").update(f"[b]{path.name}[/]\nSize: {size:.1f}KB\nMod: {mtime}")
        else:
            self.query_one("#file-data").update("No file active")

class SearchWidget(Vertical):
    def compose(self):
        yield Label("🔍 SEARCH", classes="tool-label")
        yield Input(placeholder="Find text...", id="search-input")

class CodeMinimap(Vertical):
    def compose(self):
        yield Label("🗺️ MAP", classes="tool-label")
        with Vertical(id="minimap-scroll-area"):
            yield Static("", id="minimap-content")

    def update_minimap(self, text: str):
        content = self.query_one("#minimap-content", Static)
        lines = text.splitlines()[:100]
        map_text = "\n".join(line[:20] for line in lines)
        content.update(map_text)

    def sync_scroll(self, y_offset: int):
        try:
            self.query_one("#minimap-scroll-area").scroll_to(y=max(0, y_offset - 4), animate=True, duration=0.1)
        except: pass

