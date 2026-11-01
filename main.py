from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from screens.console import Console
from screens.home import Home

import ui_globals

class RoboarmControllerApp(App):
    SCREENS = { 
               "console": Console,
               "home": Home,
    }
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS

    def on_mount(self) -> None:
        self.sub_title = "disconnected"
        self.push_screen('home')

def main():
    app = RoboarmControllerApp()
    app.run()

if __name__ == "__main__":
    main()
