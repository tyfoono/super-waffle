import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem

from database import Database
from player import Ui_MainWindow


class Player(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.data = Database()
        self.btn_add.clicked.connect(self.add_files)
        self.btn_update_playlist.clicked.connect(self.update_playlist)

    def update_playlist(self):
        cur = self.data.con.cursor()
        result = list(map(list, cur.execute("""SELECT id, albumId, title FROM Track""").fetchall()))

        for item in result:
            item.append(*cur.execute(
                f"""SELECT name FROM Artist JOIN Track_Artist ON Artist.id = Track_Artist.artistId 
                WHERE Track_Artist.trackId = {item[0]}""").fetchone())
            item.append(*cur.execute(f"""SELECT title FROM Album WHERE id = {item[1]}""").fetchone())

        if not result:
            warning = QMessageBox.question(self, '', 'Необходимо добавить файлы', buttons=QMessageBox.StandardButton.Ok)
            if warning == QMessageBox.StandardButton.Ok:
                return

        self.playlist.setRowCount(len(result))
        self.playlist.setColumnCount(len(result[0]) - 2)

        for i, elem in enumerate(result):
            for j, val in enumerate(elem[2:]):
                self.playlist.setItem(i, j, QTableWidgetItem(str(val)))

    def add_files(self):
        files = QFileDialog.getOpenFileNames(self, filter="Music (*.mp3 *.m4a *.flac)")
        self.data.fill_database_from_files(files[0])


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Player()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
