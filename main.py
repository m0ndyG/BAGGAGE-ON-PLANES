import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, QMenu,
                             QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
                             QCalendarWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QMessageBox, QLabel, QListWidget, QTextEdit, QRadioButton,
                             QGroupBox, QGridLayout, QSpacerItem, QSizePolicy, QFrame, QAbstractScrollArea)
from qfluentwidgets import (PushButton, ComboBox, LineEdit, CalendarPicker,
                            TableWidget, ListWidget, TextEdit,
                            RadioButton, setTheme, Theme, Action)

qss = """
    QWidget {
        color: black; /* Цвет текста для всех виджетов */
        background-color: #f0f0f0; /* Светло-серый фон */
    }

    /* Стили для кнопок */
    QPushButton {
        background-color: #e0e0e0; /* Светло-серый фон */
        border: 1px solid #a0a0a0; /* Серая рамка */
        padding: 5px;
    }

    /* Стили для выделенной строки */
    QTableWidget::item:selected {
        background-color: #a0a0a0; /* Серый фон */
        color: black; /* Черный текст */
    }

    /* Стили для полей ввода */
    QLineEdit {
        color: black; /* Черный текст */
        background-color: white; /* Белый фон */
        border: 1px solid #a0a0a0; /* Серая рамка */
    }
"""

# Временное хранилище данных (заменится на базу данных в будущем)
temp_data = [
    {"owner": "1234 567890", "number": "BAG-001", "size": "Средний", "description": "Чемодан",
     "departure_route": "Москва - Санкт-Петербург", "arrival_route": "Санкт-Петербург - Москва",
     "status": "Зарегистрирован", "departure_date": "2024-07-15", "arrival_date": "2024-07-16"},
    # ... другие тестовые данные
]

temp_reports = []
temp_planes = []

class AddRecordWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить запись")
        # ... (Создание полей ввода и кнопки "Сохранить" с использованием qfluentwidgets)
        self.save_button = PushButton("Сохранить", self)
        # ... (Размещение элементов на форме)
        self.save_button.clicked.connect(self.save_record)

    def save_record(self):
        # ... (Получение данных из полей ввода)
        record = {
            "owner": self.owner_edit.text(),
            # ... (другие поля)
        }
        temp_data.append(record)
        self.parent().refresh_table()
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # setTheme(Theme.DARK)  - убрали
        self.setWindowTitle("Информационная система учета перевозки багажа")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Кнопки
        self.create_report_button = PushButton("Создать отчет", self)
        self.report_history_button = PushButton("История отчетов", self)
        self.help_button = PushButton("Правила пользования", self)
        self.add_plane_button = PushButton("Внести самолет\nотправителя", self)
        self.add_record_button = PushButton("Создать запись", self)
        self.sort_button = PushButton("Сортировка", self)

        # Установка минимального размера для кнопок слева
        self.create_report_button.setMinimumSize(120, 60)
        self.report_history_button.setMinimumSize(120, 60)
        self.help_button.setMinimumSize(120, 60)

        # Установка максимальной ширины для кнопки "Внести самолет отправителя"
        self.add_plane_button.setMaximumWidth(150)

        # Элементы поиска
        self.filter_line_edit = LineEdit(self)
        self.filter_line_edit.setPlaceholderText("Фильтр")
        self.filter_line_edit.setMaximumWidth(150)
        self.search_line_edit = LineEdit(self)
        self.search_line_edit.setPlaceholderText("Строка поиска")
        self.search_line_edit.setMaximumWidth(350)

        # Таблица
        self.table = TableWidget(self)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Владелец багажа\n(серия и номер\nпаспорта)", "Номер багажа", "Размер багажа", "Краткое описание",
            "Маршрут\nотправления", "Маршрут\nприбытия", "Дата отправления", "Дата прибытия", "Статус\nотправления"
        ])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 115)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Добавляем горизонтальную прокрутку
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)  # Подстраиваем размер под содержимое

        # Разметка
        grid_layout = QGridLayout(self.central_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(5)

        # Вертикальный разделитель
        separator = QFrame(self)
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Вертикальный SpacerItem для выравнивания кнопок по центру
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        grid_layout.addWidget(self.create_report_button, 0, 0)
        grid_layout.addWidget(self.report_history_button, 1, 0)
        grid_layout.addWidget(self.help_button, 2, 0)
        grid_layout.addItem(vertical_spacer, 3, 0)

        grid_layout.addWidget(separator, 0, 1, 4, 1)

        grid_layout.addWidget(self.sort_button, 0, 2)
        grid_layout.addWidget(self.filter_line_edit, 0, 3)
        grid_layout.addWidget(self.search_line_edit, 0, 4)
        grid_layout.addWidget(self.add_plane_button, 0, 5)
        grid_layout.addWidget(self.add_record_button, 0, 6)

        grid_layout.addWidget(self.table, 1, 2, 3, 5)

        # Задаем политику растяжения для строки с таблицей
        grid_layout.setRowStretch(3, 1)

        # Обработчики событий
        self.add_record_button.clicked.connect(self.open_add_record_window)
        self.sort_button.clicked.connect(self.show_sort_menu)

        self.refresh_table()

    def show_sort_menu(self):
        """Отображает меню с вариантами сортировки"""
        menu = QMenu(self)
        sort_by_date_action = Action("По дате", self)
        sort_by_name_action = Action("По имени", self)
        sort_by_time_action = Action("По времени", self)

        menu.addAction(sort_by_date_action)
        menu.addAction(sort_by_name_action)
        menu.addAction(sort_by_time_action)

        # Обработчики для действий сортировки (заглушки)
        sort_by_date_action.triggered.connect(lambda: print("Сортировка по дате"))
        sort_by_name_action.triggered.connect(lambda: print("Сортировка по имени"))
        sort_by_time_action.triggered.connect(lambda: print("Сортировка по времени"))

        # Позиционируем меню относительно кнопки
        pos = self.sort_button.mapToGlobal(self.sort_button.rect().bottomLeft())
        menu.exec_(pos)

    def refresh_table(self):
        self.table.setRowCount(0)
        for row_data in temp_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data["owner"]))
            self.table.setItem(row, 1, QTableWidgetItem(row_data["number"]))
            self.table.setItem(row, 2, QTableWidgetItem(row_data["size"]))
            self.table.setItem(row, 3, QTableWidgetItem(row_data["description"]))
            self.table.setItem(row, 4, QTableWidgetItem(row_data["departure_route"]))
            self.table.setItem(row, 5, QTableWidgetItem(row_data["arrival_route"]))
            self.table.setItem(row, 6, QTableWidgetItem(row_data["departure_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(row_data["arrival_date"]))
            self.table.setItem(row, 8, QTableWidgetItem(row_data["status"]))

    def open_add_record_window(self):
        self.add_record_window = AddRecordWindow(self)
        self.add_record_window.show()

    # ... (Методы для обработки событий кнопок, открытия других окон и т.д.)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qss)  # Применяем ТОЛЬКО qss

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())