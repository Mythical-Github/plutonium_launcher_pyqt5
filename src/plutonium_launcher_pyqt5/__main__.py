import os
import sys
import json
import subprocess
from pathlib import Path
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


if getattr(sys, 'frozen', False):
    script_dir = Path(sys.executable).parent
else:
    script_dir = Path(__file__).resolve().parent


SETTINGS_JSON = f'{script_dir}/settings.json'


color_1 = "color: white; border: 1px solid teal"
style_1 = f"background: #222222; {color_1};"
style_2 = f"background: #666666; {color_1};"
background_1 = "background-color: #111111;"

class ButtonHoverEventFilter(QObject):
    def __init__(self, button):
        super().__init__(button)
        self.button = button
        self.original_style = button.styleSheet()

    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == QEvent.Enter:
                self.button.setStyleSheet(style_1)
            elif event.type() == QEvent.Leave:
                self.button.setStyleSheet(self.original_style)
            elif event.type() == QEvent.MouseButtonPress:
                self.button.setStyleSheet(style_2)
            elif event.type() == QEvent.MouseButtonRelease:
                self.button.setStyleSheet(self.original_style)
        return super().eventFilter(obj, event)

class StyledButton(QPushButton):
    def __init__(self, title, highlightable=True):
        super().__init__(title)
        self.setMinimumHeight(25)
        self.highlightable = highlightable
        self.original_style = ""
        self.setStylesheet()
        self.installEventFilter(ButtonHoverEventFilter(self))

    def setStylesheet(self):
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setColorAt(0, QColor(70, 70, 70))
        gradient.setColorAt(1, QColor(128, 0, 0))
        gradient_stops = gradient.stops()
        gradient_str = "qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,"
        for stop in gradient_stops:
            color = stop[1].darker(200).name()
            pos = 1 - stop[0]
            gradient_str += f" stop: {pos} {color},"
        gradient_str = gradient_str.rstrip(",") + ")"
        self.original_style = f"QPushButton {{background: {gradient_str}; color: white; border: 1px solid black; border-radius: 5px;}}"
        self.setStyleSheet(self.original_style)


class GameLauncher(QWidget):
    def __init__(self, games, lan_username):
        super().__init__()
        self.games = games
        self.lan_username = lan_username
        self.settings = QSettings("Mythical", "Plutonium Launcher")
        self.initUI()

    def initUI(self):
        self.resize(self.settings.value("size", QSize(400, 200)))
        self.move(self.settings.value("pos", QPoint(100, 100)))

        with open(SETTINGS_JSON) as f:
            data = json.load(f)
            self.selected_game = data.get('selected_game', self.games[0])
            self.delay = data.get('delay', 1.0) 
            self.selected_index = data.get('selected_index', 0)
            self.global_args = data.get('global_args', [])

        layout = QVBoxLayout()

        for game in self.games:
            button_layout = QHBoxLayout()
            game_button = StyledButton(game["name"])
            game_button.clicked.connect(lambda _, arg=game["arg"], directory=game.get("directory", ""): self.launchGame(arg, directory))
            button_layout.addWidget(game_button)

            dir_button = StyledButton("..", highlightable=False)
            dir_button.setFixedSize(40, 25)
            dir_button.clicked.connect(lambda _, game=game: self.setGameDirectory(game))
            button_layout.addWidget(dir_button)

            layout.addLayout(button_layout)

        self.user_button = StyledButton(f'User: {self.lan_username}', highlightable=False)
        self.user_button.setObjectName("UserButton")
        self.user_button.clicked.connect(self.change_username)
        layout.addWidget(self.user_button)

        # Add new horizontal layout with two buttons
        link_buttons_layout = QHBoxLayout()

        docs_button = StyledButton("Plutonium Docs", highlightable=False)
        docs_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://plutonium.pw/docs/")))
        link_buttons_layout.addWidget(docs_button)

        forums_button = StyledButton("Plutonium Forums", highlightable=False)
        forums_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://forum.plutonium.pw/")))
        link_buttons_layout.addWidget(forums_button)

        layout.addLayout(link_buttons_layout)

        global_args_scroll = QScrollArea()
        global_args_widget = QWidget()
        global_args_layout = QVBoxLayout(global_args_widget)
        global_args_scroll.setWidgetResizable(True)

        for arg in self.global_args:
            arg_button = StyledButton(arg)
            global_args_layout.addWidget(arg_button)

        global_args_scroll.setWidget(global_args_widget)
        global_args_scroll.setMaximumHeight(80)
        
        add_arg_button = StyledButton("Add Global Argument")
        add_arg_button.clicked.connect(self.addGlobalArg)

        remove_arg_button = StyledButton("Remove Global Argument")
        remove_arg_button.clicked.connect(self.removeGlobalArg)

        button_layout = QVBoxLayout()
        button_layout.addWidget(add_arg_button)
        button_layout.addWidget(remove_arg_button)

        main_layout = QHBoxLayout()
        main_layout.addWidget(global_args_scroll)
        main_layout.addLayout(button_layout)

        layout.addLayout(main_layout)

        panel_layout = QHBoxLayout()

        self.game_label = QLabel("Select Game:")
        panel_layout.addWidget(self.game_label)

        self.game_combobox = QComboBox()
        panel_layout.addWidget(self.game_combobox)

        self.delay_label = QLabel("Delay:")
        panel_layout.addWidget(self.delay_label)

        self.delay_spinbox = QDoubleSpinBox()
        self.delay_spinbox.setSingleStep(0.1)
        self.delay_spinbox.setValue(float(self.delay))
        panel_layout.addWidget(self.delay_spinbox)

        self.auto_execute_checkbox = QCheckBox("Auto Execute")
        self.auto_execute_checkbox.setChecked(self.settings.value("auto_execute", True, type=bool))
        self.auto_execute_checkbox.stateChanged.connect(self.updateSettings)
        panel_layout.addWidget(self.auto_execute_checkbox)

        layout.addLayout(panel_layout)

        self.setLayout(layout)
        self.setWindowTitle('Plutonium Launcher')

        self.setWindowIcon(QIcon('assets/plutonium_icon.ico'))

        self.setStyleSheet("""
            QWidget {
                background-color: #4d0000;
                color: white;
            }
            QPushButton#UserButton {
                background-color: #8b0000;
                border: 1px solid #8b0000;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton#UserButton:hover {
                background-color: #a30000;
                border: 1px solid #a30000;
            }
            QPushButton {
                min-height: 25px;
            }
        """)

        self.populateGameComboBox()

        for index, game in enumerate(self.games):
            if game == self.selected_game:
                self.game_combobox.setCurrentIndex(index)
                break

        self.game_combobox.setCurrentIndex(self.selected_index)
        self.delay_spinbox.valueChanged.connect(self.updateDelay)
        self.game_combobox.currentIndexChanged.connect(self.updateSelectedGame)
        self.show()
        self.updateSettings()

    def updateSelectedGame(self, index):
        self.selected_index = index
        self.settings.setValue("selected_index", index)
        self.saveSettings()

    def updateDelay(self, value):
        self.delay = value
        self.settings.setValue("delay", value)
        self.saveSettings()

    def populateGameComboBox(self):
        for index, game in enumerate(self.games):
            self.game_combobox.addItem(game["name"], game)

    def updateSettings(self):
        self.settings.setValue("auto_execute", self.auto_execute_checkbox.isChecked())
        self.saveSettings()

    def launchSelectedGame(self):
        selected_game_data = self.game_combobox.currentData()
        if selected_game_data:
            arg = selected_game_data.get("arg")
            directory = selected_game_data.get("directory", "")
            self.launchGame(arg, directory)

    def launchGame(self, arg, directory):
        if not directory:
            selected_directory = QFileDialog.getExistingDirectory(self, f"Select Directory for {arg}", "")
            if selected_directory:
                for game in self.games:
                    if game["arg"] == arg:
                        game["directory"] = selected_directory
                        directory = selected_directory
                        break
                self.saveSettings()

        os.chdir(os.path.join(os.environ['LOCALAPPDATA'], 'Plutonium'))
        cmd = [f'{os.getcwd()}/bin/plutonium-bootstrapper-win32.exe', arg, directory, '+name', self.lan_username, '-lan']
        
        for global_arg in self.global_args:
            cmd.append(global_arg)
        
        subprocess.Popen(cmd)
        self.close()

    def setGameDirectory(self, game):
        selected_directory = QFileDialog.getExistingDirectory(self, f"Select Directory for {game['arg']}", "")
        if selected_directory:
            game["directory"] = selected_directory
            self.saveSettings()

    def change_username(self):
        new_username, okPressed = QInputDialog.getText(self, "Change LAN Username", "Enter your new LAN Username:", QLineEdit.Normal, "")
        if okPressed and new_username != '':
            self.lan_username = new_username
            self.user_button.setText(f'User: {self.lan_username}')
            self.saveSettings()

    def closeEvent(self, event):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.saveSettings()

    def saveSettings(self):
        selected_game_index = self.game_combobox.currentIndex()

        with open(SETTINGS_JSON, 'r+') as f:
            data = json.load(f)
            data["auto_execute"] = self.auto_execute_checkbox.isChecked()
            data["delay"] = self.delay_spinbox.value()
            data["selected_index"] = selected_game_index
            data["lan_username"] = self.lan_username
            data["global_args"] = self.global_args
            data["games"] = self.games
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()


    def addGlobalArg(self):
        arg, okPressed = QInputDialog.getText(self, "Add Global Argument", "Enter the global argument:", QLineEdit.Normal, "")
        if okPressed and arg.strip() != '':
            self.global_args.append(arg)
            self.saveSettings()
            arg_button = StyledButton(arg)
            self.layout().itemAt(1).widget().layout().addWidget(arg_button)


    def removeGlobalArg(self):
        if self.global_args:
            arg, okPressed = QInputDialog.getItem(self, "Remove Global Argument", "Select the global argument to remove:", self.global_args, 0, False)
            if okPressed:
                self.global_args.remove(arg)
                self.saveSettings()
                scroll_layout = self.layout().itemAt(1).widget().layout()
                for i in range(scroll_layout.count()):
                    item = scroll_layout.itemAt(i)
                    if item.widget().text() == arg:
                        widget = item.widget()
                        scroll_layout.removeWidget(widget)
                        widget.deleteLater()
                        break



def prompt_lan_username():
    username, okPressed = QInputDialog.getText(None, "Enter LAN Username", "Your LAN Username:", QLineEdit.Normal, "")
    if okPressed and username != '':
        return username
    return None

def main():
    with open(SETTINGS_JSON) as f:
        data = json.load(f)
        games_data = data['games']
        lan_username = data.get('lan_username', '')

    app = QApplication(sys.argv)
    if not lan_username:
        lan_username = prompt_lan_username()
        if not lan_username:
            print("LAN username not provided. Exiting.")
            sys.exit(1)
        with open(SETTINGS_JSON, 'w') as f:
            json.dump({'games': games_data, 'lan_username': lan_username}, f, indent=4)
    launcher = GameLauncher(games_data, lan_username)
    app.exec_()

if __name__ == '__main__':
    main()
