import os
from tkinter import filedialog

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, HorizontalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Footer, Header, Label, Select, TextArea


class Settings(ModalScreen):
    THEMES = (
        ("Textual Dark", "textual-dark"),
        (
            "Textual Light",
            "textual-light",
        ),
        ("Monokai", "monokai"),
    )
    theme: str

    def __init__(self):
        super().__init__()
        self.theme = self.app.theme

    def compose(self) -> ComposeResult:
        with Vertical(classes="border padded"):
            yield Select(self.THEMES, prompt="choose theme", id="theme")
            yield Button("save", id="save", variant="primary")
            yield Button("cancel", id="cancel", variant="error")

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "theme":
            self.theme = str(event.select.value)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            self.app.theme = self.theme
            self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()


class PyTUIEditorApp(App):
    BINDINGS = [
        ("ctrl+n", "new_file", "new"),
        ("ctrl+o", "open_file", "open"),
        ("ctrl+t", "save", "save"),
        ("ctrl+r", "save_as", "save as"),
        ("ctrl+l", "options", "options"),
    ]
    CSS_PATH = "style.tcss"
    path = reactive("")
    dirty = reactive(False)
    recent_files = reactive(list(), recompose=True)

    def __init__(self):
        super().__init__()
        self.theme = "monokai"

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(
                id="main",
            ):
                yield Header(show_clock=True)
                yield Label(str(self.path), id="top_bar")
                yield TextArea("", id="text_field", show_line_numbers=True)
                yield Label("", id="bottom_bar")
                yield Footer(show_command_palette=True)
            with VerticalScroll(classes="sidebar"):
                with HorizontalScroll():
                    with Collapsible(title="recent files"):
                        for file in self.recent_files:
                            name = os.path.basename(file)
                            yield Button(
                                f"open {name}",
                                classes="recent",
                                name=f"{file}",
                                variant="primary",
                            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if "recent" in event.button.classes:
            file_path = event.button.name
            if os.path.exists(str(file_path)):
                self.path = file_path

    def update_recent_buttons(self):
        sidebar = self.query(".sidebar").first()
        collapsible = sidebar.query(Collapsible).first()
        collapsible.remove_children()

        for file in self.recent_files:
            name = os.path.basename(file)
            btn = Button(f"open {name}", name=file, classes="recent", variant="primary")
            collapsible.mount(btn)

    def add_recent_file(self, path: str):
        if path in self.recent_files:
            return
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]
        self.update_recent_buttons()

    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.dirty = True
        top_bar = self.query_one("#top_bar", Label)
        top_bar.update(f"{self.path}{' *' if self.dirty else ''}")

    async def watch_path(self, new_value: str) -> None:
        if new_value == "" or new_value.isspace():
            return
        with open(new_value) as curr_file:
            inp = self.query_one("#text_field", TextArea)
            top_bar = self.query_one("#top_bar", Label)

            inp.text = curr_file.read()
            top_bar.update(f"{self.path}{' *' if self.dirty else ''}")
            self.recent_files.append(new_value)
            self.add_recent_file(new_value)

    async def action_options(self) -> None:
        await self.push_screen(Settings())

    async def action_exit(self):
        self.exit(0)

    async def action_open_file(self) -> None:
        path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save As...",
        )
        if path == "" or path is None:
            return
        self.path = path

    async def action_new_file(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save As...",
        )
        if path == "" or path is None:
            return
        with open(path, "w+") as curr_file:
            curr_file.write("")
        self.path = path

    async def action_save_as(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save As...",
        )
        if path == "" or path is None:
            return
        with open(path, "w+") as curr_file:
            inp = self.query_one("#text_field", TextArea)
            curr_file.write(inp.text)
        self.path = path
        self.dirty = False

    def action_save(self) -> None:
        if self.path == "" or str(self.path).isspace():
            return
        with open(str(self.path), "w+") as curr_file:
            inp = self.query_one("#text_field", TextArea)
            curr_file.write(inp.text)
            self.dirty = False


if __name__ == "__main__":
    app = PyTUIEditorApp()
    app.run()
