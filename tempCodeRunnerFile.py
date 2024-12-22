import sys
from PyQt5.QtCore import Qt, QSize, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QMenu,
    QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QGridLayout, QSpacerItem, QSizePolicy, QFrame, QAbstractScrollArea,
    QDialog, QFormLayout, QLabel
)
from qfluentwidgets import PushButton, LineEdit, ComboBox, DatePicker

# Стили для приложения
qss = """
    QWidget {
        color: black;
        background-color: #f0f0f0;
    }

    QPushButton {
        background-color: #e0e0e0;
        border: 1px solid #a0a0a0;
        padding: 5px;
    }

    QPushButton:hover {
        background-color: #d0d0d0;
    }

    QTableWidget::item:selected {
        background-color: #a0a0a0;
        color: black;
    }

    QLineEdit {
        color: black;
        background-color: white;
        border: 1px solid #a0a0a0;
    }
    QFrame[frameShape="5"] {
        color: #a0a0a0;
    }
    QLabel {
        color: black;
    }
    QDialog {
        background-color: #f0f0f0;
    }

"""

# Данные (пока что без базы данных, храним в памяти)
data = [
    {"owner": "1234 567890", "number": "BAG-001", "size": "Средний", "desc": "Чемодан",
     "dep_route": "Москва - Санкт-Петербург", "arr_route": "Санкт-Петербург - Москва",
     "status": "Зарегистрирован", "dep_date": "2024-07-15", "arr_date": "2024-07-16"},
    # ... другие тестовые данные
]

# Класс формы "Создать запись"
class CreateRecordForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать запись")
        self.resize(500, 350)

        main_layout = QGridLayout(self)

        # Левая колонка (теперь QGridLayout)
        left_layout = QGridLayout()
        left_layout.addWidget(QLabel("Владелец багажа:"), 0, 0)
        self.owner_edit = LineEdit(self)
        left_layout.addWidget(self.owner_edit, 0, 1)

        left_layout.addWidget(QLabel("Номер багажа:"), 1, 0)
        self.number_edit = LineEdit(self)
        left_layout.addWidget(self.number_edit, 1, 1)

        left_layout.addWidget(QLabel("Тип багажа:"), 2, 0)
        self.type_combo = ComboBox(self)
        self.type_combo.addItems(["Обычный", "Ценный", "Хрупкий"])
        left_layout.addWidget(self.type_combo, 2, 1)

        left_layout.addWidget(QLabel("Объем:"), 3, 0)
        self.volume_edit = LineEdit(self)
        left_layout.addWidget(self.volume_edit, 3, 1)

        left_layout.addWidget(QLabel("Размер багажа (по габаритам):"), 4, 0)
        self.size_combo = ComboBox(self)
        self.size_combo.addItems(["Маленький", "Средний", "Большой"])
        left_layout.addWidget(self.size_combo, 4, 1)

        left_layout.addWidget(QLabel("Вес багажа:"), 5, 0)
        self.weight_edit = LineEdit(self)
        left_layout.addWidget(self.weight_edit, 5, 1)

        left_layout.addWidget(QLabel("Номер самолета:"), 6, 0)
        self.aircraft_combo = ComboBox(self)
        self.aircraft_combo.addItems([""])
        left_layout.addWidget(self.aircraft_combo, 6, 1)
        left_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding), 7, 0, 1, 2)

        # Правая колонка (теперь QGridLayout)
        right_layout = QGridLayout()
        right_layout.addWidget(QLabel("Маршрут отправления:"), 0, 0)
        self.dep_route_edit = LineEdit(self)
        right_layout.addWidget(self.dep_route_edit, 0, 1)

        right_layout.addWidget(QLabel("Маршрут прибытия:"), 1, 0)
        self.arr_route_edit = LineEdit(self)
        right_layout.addWidget(self.arr_route_edit, 1, 1)

        right_layout.addWidget(QLabel("Дата отправления:"), 2, 0)
        self.dep_date_edit = DatePicker(self)
        right_layout.addWidget(self.dep_date_edit, 2, 1)

        right_layout.addWidget(QLabel("Дата прибытия:"), 3, 0)
        self.arr_date_edit = DatePicker(self)
        right_layout.addWidget(self.arr_date_edit, 3, 1)

        right_layout.addWidget(QLabel("Статус отправления:"), 4, 0)
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["Зарегистрирован", "В пути", "Прибыл", "Утерян"])
        right_layout.addWidget(self.status_combo, 4, 1)

        right_layout.addWidget(QLabel("Краткое описание:"), 5, 0)
        self.desc_edit = LineEdit(self)
        right_layout.addWidget(self.desc_edit, 5, 1)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding), 6, 0, 1, 2)

        # Добавляем колонки в основной layout
        main_layout.addLayout(left_layout, 0, 0)
        main_layout.addLayout(right_layout, 0, 1)

        # Кнопка "СОХРАНИТЬ"
        self.save_button = PushButton("СОХРАНИТЬ", self)
        main_layout.addWidget(self.save_button, 1, 0, 1, 2)

        self.save_button.clicked.connect(self.save_data)

    def save_data(self):
        new_record = {
            "owner": self.owner_edit.text(),
            "number": self.number_edit.text(),
            "type": self.type_combo.currentText(),
            "volume": self.volume_edit.text(),
            "size": self.size_combo.currentText(),
            "weight": self.weight_edit.text(),
            "aircraft": self.aircraft_combo.currentText(),
            "dep_route": self.dep_route_edit.text(),
            "arr_route": self.arr_route_edit.text(),
            "dep_date": self.dep_date_edit.date().toString("yyyy-MM-dd"),
            "arr_date": self.arr_date_edit.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "desc": self.desc_edit.text()
        }

        data.append(new_record)
        self.parent().refresh_table()
        self.close()

# Класс формы "Добавить самолет"
class AddAircraftForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление самолета")
        self.setMinimumSize(300, 200)

        layout = QFormLayout(self)

        self.aircraft_number_edit = LineEdit(self)
        layout.addRow("Номер самолета:", self.aircraft_number_edit)

        self.aircraft_name_edit = LineEdit(self)
        layout.addRow("Наименование самолета:", self.aircraft_name_edit)

        self.aircraft_capacity_edit = LineEdit(self)
        layout.addRow("Грузоподъемность:", self.aircraft_capacity_edit)

        self.save_button = PushButton("СОХРАНИТЬ", self)
        layout.addRow(self.save_button)

        self.save_button.clicked.connect(self.save_data)

    def save_data(self):
        # Тут будет логика сохранения данных о самолете
        # ...

        # Вывод в консоль для проверки
        print("Номер самолета:", self.aircraft_number_edit.text())
        print("Наименование самолета:", self.aircraft_name_edit.text())
        print("Грузоподъемность:", self.aircraft_capacity_edit.text())

        self.close()

# Класс главного окна
class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Информационная система учета перевозки багажа")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Кнопки
        self.sort_btn = ComboBox(self)
        self.sort_btn.addItems(["По дате", "По имени", "По времени"])
        self.sort_btn.setPlaceholderText("Сортировка")
        self.filter_edit = LineEdit(self)
        self.filter_edit.setPlaceholderText("Фильтр")
        self.search_edit = LineEdit(self)
        self.search_edit.setPlaceholderText("Строка поиска")

        self.add_plane_btn = PushButton("Внести самолет \nотправителя", self)
        self.create_record_btn = PushButton("Создать запись", self)
        self.create_record_btn.clicked.connect(self.show_create_record_form)

        self.btn1 = PushButton("Создать отчет", self)
        self.btn2 = PushButton("История отчетов", self)
        self.btn3 = PushButton("Правила пользования", self)

        # Установка размеров
        button_size = QSize(140, 50)
        self.sort_btn.setMinimumSize(button_size)
        self.sort_btn.setMaximumSize(button_size)
        self.add_plane_btn.setMinimumSize(button_size)
        self.add_plane_btn.setMaximumSize(button_size)
        self.create_record_btn.setMinimumSize(button_size)
        self.create_record_btn.setMaximumSize(button_size)

        large_button_size = QSize(140, 90)
        self.btn1.setMinimumSize(large_button_size)
        self.btn1.setMaximumSize(large_button_size)
        self.btn2.setMinimumSize(large_button_size)
        self.btn2.setMaximumSize(large_button_size)
        self.btn3.setMinimumSize(large_button_size)
        self.btn3.setMaximumSize(large_button_size)

        # Таблица
        self.table = QTableWidget(self)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Владелец багажа\n(серия и номер\nпаспорта)", "Номер багажа", "Размер багажа", "Краткое описание",
            "Маршрут\nотправления", "Маршрут\nприбытия", "Дата отправления", "Дата прибытия", "Статус\nотправления"
        ])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 115)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # Разметка
        layout = QGridLayout(self.central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Верхняя панель
        top_layout = QGridLayout()
        top_layout.addWidget(self.sort_btn, 0, 0)
        top_layout.addWidget(self.filter_edit, 0, 1)
        top_layout.addWidget(self.search_edit, 0, 2)
        top_layout.addWidget(self.add_plane_btn, 0, 3)
        top_layout.addWidget(self.create_record_btn, 0, 4)
        top_layout.setColumnStretch(2, 1)

        # Левая колонка
        left_layout = QVBoxLayout()
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        left_layout.addWidget(self.btn1)
        left_layout.addWidget(self.btn2)
        left_layout.addWidget(self.btn3)
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Вертикальный разделитель
        separator = QFrame(self)
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Основная компоновка
        layout.addLayout(left_layout, 0, 0, 2, 1)
        layout.addWidget(separator, 0, 1, 2, 1)
        layout.addLayout(top_layout, 0, 2, 1, 1)
        layout.addWidget(self.table, 1, 2)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(1, 1)

        self.refresh_table()

        self.add_plane_btn.clicked.connect(self.show_add_aircraft_form)

    def show_create_record_form(self):
        create_record_form = CreateRecordForm(self)
        create_record_form.exec_()

    def show_add_aircraft_form(self):
        add_aircraft_form = AddAircraftForm(self)
        add_aircraft_form.exec_()

    # Обновление таблицы
    def refresh_table(self):
        self.table.setRowCount(0)
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data["owner"]))
            self.table.setItem(row, 1, QTableWidgetItem(row_data["number"]))
            self.table.setItem(row, 2, QTableWidgetItem(row_data["size"]))
            self.table.setItem(row, 3, QTableWidgetItem(row_data["desc"]))
            self.table.setItem(row, 4, QTableWidgetItem(row_data["dep_route"]))
            self.table.setItem(row, 5, QTableWidgetItem(row_data["arr_route"]))
            self.table.setItem(row, 6, QTableWidgetItem(row_data["dep_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(row_data["arr_date"]))
            self.table.setItem(row, 8, QTableWidgetItem(row_data["status"]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qss)

    win = MainWin()
    win.show()
    sys.exit(app.exec_())