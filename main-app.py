import sys
import time
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect, QDateTime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QGridLayout, QSpacerItem, QSizePolicy,
    QFrame, QAbstractScrollArea, QCheckBox, QComboBox, QMessageBox, QFormLayout,
    QPushButton as QtPushButton, QHeaderView, QTextEdit, QFileDialog, QInputDialog
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QDoubleValidator
from qfluentwidgets import PushButton, LineEdit, setTheme, Theme, ComboBox, DateTimeEdit
import pymysql
import json
import datetime
import os
import bcrypt

# region UserManualForm
class UserManualForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Правила пользования")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        rules_text = """
        ПРАВИЛА ПОЛЬЗОВАНИЯ

        1. **Основные положения**
            *   1.1 Настоящие правила регламентируют использование информационной системы.
            *   1.2 Пользоваться системой могут только авторизованные сотрудники.

        2. **Ввод данных**
            *   2.1 При вводе данных о багаже необходимо заполнять все обязательные поля.
            *   2.2 Данные должны быть достоверными и актуальными.

        3. **Отчеты**
            *   3.1 Система позволяет формировать отчеты по багажу за указанный период.
            *   3.2 Отчеты могут быть отсортированы по различным параметрам.

        4. **Ответственность**
            *   4.1 Пользователи несут ответственность за сохранность своих учетных данных.
            *   4.2 Запрещается передавать свои учетные данные третьим лицам.

        5. **Техническая поддержка**
            *   5.1 В случае возникновения проблем обращаться к администратору системы.
        """
        rules_label = QLabel(rules_text, self)
        rules_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        rules_label.setWordWrap(True)
        layout.addWidget(rules_label)
# endregion

# region qss
qss = """
QWidget {
    color: black;
    background-color: #f0f0f0;
}
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #a0a0a0;
    padding: 8px 15px;
    border-radius: 5px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
#left_buttons QPushButton {
    background-color: #d8d8d8;
    border: 1px solid #b0b0b0;
    padding: 10px 20px;
    border-radius: 7px;
    font-size: 15px;
    text-align: left;
}
#left_buttons QPushButton:hover {
    background-color: #c8c8c8;
}
QTableWidget::item:selected {
    background-color: #a0a0a0;
    color: black;
}
QLineEdit {
    color: black;
    background-color: white;
    border: 1px solid #a0a0a0;
    padding: 5px;
}
QLabel {
    color: black;
}
QDialog {
    background-color: #f0f0f0;
}
QComboBox QAbstractItemView {
    border: 1px solid gray;
    selection-background-color: lightblue;
}
QComboBox QAbstractItemView::item {
    padding: 3px;
    border: 1px solid transparent;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #a8d1ff;
    border: 1px solid #40a8ff;
}
QComboBox QAbstractItemView::item:checked {
    background-color: lightblue;
    border: 1px solid #40a8ff;
}
QComboBox {
    background-color: #e0e0e0;
    border: 1px solid #a0a0a0;
    padding: 5px;
}
QComboBox:hover {
    background-color: #d0d0d0;
}
QFrame {
    background-color: #f0f0f0;
}
"""
# endregion

# region ReportHistoryForm
class ReportHistoryForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_main_win = parent
        self.setWindowTitle("История отчетов")
        self.resize(800, 600)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("История отчетов", self)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        filter_layout = QGridLayout()
        self.filter_edit = LineEdit(self)
        self.filter_edit.setPlaceholderText("Фильтр")
        self.sort_combo = ComboBox(self)
        self.sort_combo.addItems(["По дате (сначала новые)", "По дате (сначала старые)"])
        self.sort_combo.setPlaceholderText("Сортировка")

        filter_layout.addWidget(self.sort_combo, 0, 0)
        filter_layout.addWidget(self.filter_edit, 0, 1)
        filter_layout.setColumnStretch(1, 1)

        main_layout.addLayout(filter_layout)

        self.report_table = QTableWidget(self)
        self.report_table.setColumnCount(4)
        self.report_table.setHorizontalHeaderLabels(["ID отчета", "Название отчета", "Дата создания", "Содержимое"])
        self.report_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.report_table)

        self.report_table.cellClicked.connect(self.on_report_clicked)
        self.filter_edit.textChanged.connect(self.apply_filter)
        self.sort_combo.currentIndexChanged.connect(self.load_reports)

        self.report_content_dialog = QDialog(self)
        self.report_content_dialog.setWindowTitle("Содержимое отчета")
        content_layout = QVBoxLayout(self.report_content_dialog)
        self.report_content_text_edit = QTextEdit(self.report_content_dialog)
        self.report_content_text_edit.setReadOnly(True)
        content_layout.addWidget(self.report_content_text_edit)
        self.report_content_dialog.setLayout(content_layout)

        self.reports_data = []
        self.load_reports()

    def load_reports(self):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        sort_order = self.sort_combo.currentText()
        order_by_clause = "ORDER BY created_at DESC"
        if sort_order == "По дате (сначала старые)":
            order_by_clause = "ORDER BY created_at ASC"

        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = f"SELECT id, report_name, report_data, created_at FROM reports WHERE user_id = %s {order_by_clause}"
            cursor.execute(sql_query, (self.parent_main_win.logged_in_user_id,)) # Filter by user_id
            self.reports_data = cursor.fetchall()
            cursor.close()

            self.display_reports(self.reports_data)

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю отчетов: {e}")

    def display_reports(self, reports_to_display):
        self.report_table.setRowCount(0)
        for report in reports_to_display:
            row_position = self.report_table.rowCount()
            self.report_table.insertRow(row_position)
            self.report_table.setItem(row_position, 0, QTableWidgetItem(str(report.get("id", ""))))
            self.report_table.setItem(row_position, 1, QTableWidgetItem(str(report.get("report_name", "Без имени"))))
            self.report_table.setItem(row_position, 2, QTableWidgetItem(str(report.get("created_at", ""))))

            report_data_json_str = str(report.get("report_data", ""))
            report_dates_str = "Нет данных о датах"
            try:
                report_data_dict = json.loads(report_data_json_str)
                start_date = report_data_dict.get("start_date", "Неизвестно")
                end_date = report_data_dict.get("end_date", "Неизвестно")
                report_dates_str = f"Отчет с {start_date} по {end_date}"
            except json.JSONDecodeError as e:
                report_dates_str = "Ошибка чтения данных отчета"

            self.report_table.setItem(row_position, 3, QTableWidgetItem(report_dates_str))

    def apply_filter(self):
        filter_text = self.filter_edit.text().lower()
        if not filter_text:
            self.display_reports(self.reports_data)
            return

        filtered_reports = []
        for report in self.reports_data:
            report_id_str = str(report.get("id", "")).lower()
            report_name_str = str(report.get("report_name", "Без имени")).lower()
            created_at_str = str(report.get("created_at", "")).lower()

            report_data_json_str = str(report.get("report_data", ""))
            report_content_str = ""
            try:
                report_data_dict = json.loads(report_data_json_str)
                start_date = report_data_dict.get("start_date", "Неизвестно")
                end_date = report_data_dict.get("end_date", "Неизвестно")
                report_content_str = f"Отчет с {start_date} по {end_date}".lower()
            except json.JSONDecodeError as e:
                report_content_str = "Ошибка чтения данных отчета".lower()

            if (filter_text in report_id_str or
                filter_text in report_name_str or
                filter_text in created_at_str or
                filter_text in report_content_str):
                filtered_reports.append(report)

        self.display_reports(filtered_reports)

    def on_report_clicked(self, row, column):
        if column == 3:
            report_id_item = self.report_table.item(row, 0)
            if report_id_item is not None:
                report_id = report_id_item.text()
                self.load_report_content(report_id)
        else:
            report_id_item = self.report_table.item(row, 0)
            if report_id_item is not None:
                report_id = report_id_item.text()

    def load_report_content(self, report_id):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT report_data FROM reports WHERE id = %s AND user_id = %s" # Filter by user_id
            cursor.execute(sql_query, (report_id, self.parent_main_win.logged_in_user_id)) # Pass user_id
            result = cursor.fetchone()
            cursor.close()

            if result:
                report_data_json_str = result.get("report_data", "")
                try:
                    report_data_dict = json.loads(report_data_json_str)
                    formatted_content = self.format_report_content(report_data_dict)
                    self.report_content_text_edit.setText(formatted_content)
                    self.report_content_dialog.resize(600, 400)
                    self.report_content_dialog.exec_()
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка чтения данных отчета: {e}")
            else:
                QMessageBox.warning(self, "Предупреждение", "Отчет не найден или не принадлежит вам.") # User aware message

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить содержимое отчета: {e}")

    def format_report_content(self, report_data):
        formatted_text = ""
        formatted_text += "<h2 style='text-align:center;'>Отчет о багаже</h2>"
        formatted_text += "<p><b>Период:</b> с {} по {}</p>".format(
            report_data.get('start_date', 'Неизвестно'),
            report_data.get('end_date', 'Неизвестно')
        )

        data = report_data.get("data", [])
        if not data:
            formatted_text += "<p>Нет данных о багаже за выбранный период.</p>"
        else:
            formatted_text += "<table style='border-collapse: collapse; width:100%;'>"
            formatted_text += "<thead style='font-weight: bold;'>"
            formatted_text += "<tr>"
            formatted_text += "<th style='border: 1px solid black; padding: 8px; text-align: left;'>Владелец</th>"
            formatted_text += "<th style='border: 1px solid black; padding: 8px; text-align: left;'>Номер багажа</th>"
            formatted_text += "<th style='border: 1px solid black; padding: 8px; text-align: left;'>Дата отправления</th>"
            formatted_text += "<th style='border: 1px solid black; padding: 8px; text-align: left;'>Дата прибытия</th>"
            formatted_text += "<th style='border: 1px solid black; padding: 8px; text-align: left;'>Описание</th>"
            formatted_text += "</tr>"
            formatted_text += "</thead>"
            formatted_text += "<tbody>"
            for item in data:
                formatted_text += "<tr>"
                formatted_text += "<td style='border: 1px solid black; padding: 8px;'>{}</td>".format(item.get('owner', ''))
                formatted_text += "<td style='border: 1px solid black; padding: 8px;'>{}</td>".format(item.get('number', ''))
                formatted_text += "<td style='border: 1px solid black; padding: 8px;'>{}</td>".format(item.get('dep_date', ''))
                formatted_text += "<td style='border: 1px solid black; padding: 8px;'>{}</td>".format(item.get('arr_date', ''))
                formatted_text += "<td style='border: 1px solid black; padding: 8px;'>{}</td>".format(item.get('desc', ''))
                formatted_text += "</tr>"
            formatted_text += "</tbody>"
            formatted_text += "</table>"
        return formatted_text

# region CreateAccountDialog
class CreateAccountDialog(QDialog):
    def __init__(self, parent=None, db_connection=None):
        super().__init__(parent)
        self.setWindowTitle("Создание аккаунта")
        self.db_connection = db_connection
        self.layout = QFormLayout(self)

        self.username_edit = LineEdit(self)
        self.layout.addRow("Имя пользователя:", self.username_edit)

        self.password_edit = LineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Пароль:", self.password_edit)

        self.confirm_password_edit = LineEdit(self)
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Подтвердите пароль:", self.confirm_password_edit)

        self.create_button = PushButton("Создать аккаунт", self)
        self.layout.addRow(self.create_button)
        self.create_button.clicked.connect(self.create_account)

        self.cancel_button = PushButton("Отмена", self)
        self.layout.addRow(self.cancel_button)
        self.cancel_button.clicked.connect(self.reject)

    def create_account(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                QMessageBox.warning(self, "Ошибка", "Имя пользователя уже занято.")
                return

            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            self.db_connection.commit()
            cursor.close()
            QMessageBox.information(self, "Успех", "Аккаунт успешно создан.")
            self.accept()
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании аккаунта: {e}")

# endregion

# region LoginDialog
class LoginDialog(QDialog):
    def __init__(self, parent=None, db_connection=None):
        super().__init__(parent)
        self.setWindowTitle("Аутентификация")
        self.db_connection = db_connection
        self.logged_in_user_id = None # To store user_id after login
        self.layout = QFormLayout(self)

        self.username_edit = LineEdit(self)
        self.layout.addRow("Имя пользователя:", self.username_edit)

        self.password_edit = LineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.layout.addRow("Пароль:", self.password_edit)

        self.login_button = PushButton("Войти", self)
        self.layout.addRow(self.login_button)
        self.login_button.clicked.connect(self.login_auth) # Renamed to login_auth to avoid confusion with accept()

        self.create_account_button = PushButton("Создать аккаунт", self)
        self.layout.addRow(self.create_account_button)
        self.create_account_button.clicked.connect(self.open_create_account_dialog)

    def login_auth(self): # Renamed to login_auth
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите имя пользователя и пароль.")
            return

        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,)) # Select id as well
            result = cursor.fetchone()
            cursor.close()

            if result:
                user_id = result['id'] # Get user_id
                stored_password_hash = result['password_hash']
                if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
                    QMessageBox.information(self, "Успех", "Аутентификация успешна.")
                    self.logged_in_user_id = user_id # Store user_id upon successful login
                    self.accept() # Close dialog and return Accepted
                    return
                else:
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка аутентификации: {e}")

    def open_create_account_dialog(self):
        create_account_dialog = CreateAccountDialog(self, self.db_connection)
        if create_account_dialog.exec_() == QDialog.Accepted:
            pass


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.LIGHT)
        self.setWindowTitle("Информационная система учета перевозки багажа")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.full_data = []
        self.current_data = []
        self.logged_in_user_id = None

        main_layout = QHBoxLayout(self.central_widget)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        left_buttons_widget = QWidget()
        left_buttons_widget.setObjectName("left_buttons")
        left_buttons_layout = QVBoxLayout(left_buttons_widget)
        left_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.btn1 = PushButton("Создать отчет", self)
        self.btn2 = PushButton("История отчетов", self)
        self.btn3 = PushButton("Правила пользования", self)
        left_buttons_layout.addWidget(self.btn1)
        left_buttons_layout.addWidget(self.btn2)
        left_buttons_layout.addWidget(self.btn3)

        left_layout.addWidget(left_buttons_widget)
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main_layout.addLayout(left_layout)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        top_panel_layout = QHBoxLayout()
        self.sort_btn = PushButton("Сортировка", self)
        self.filter_btn = PushButton("Фильтр", self)
        self.search_edit = LineEdit(self)
        self.search_edit.setPlaceholderText("Строка поиска")
        self.add_plane_btn = PushButton("Внести самолет \nотправителя", self)
        self.create_record_btn = PushButton("Создать запись", self)

        top_panel_layout.addWidget(self.sort_btn)
        top_panel_layout.addWidget(self.filter_btn)
        top_panel_layout.addWidget(self.search_edit)
        top_panel_layout.addWidget(self.add_plane_btn)
        top_panel_layout.addWidget(self.create_record_btn)

        right_layout.addLayout(top_panel_layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Владелец багажа\n(серия и номер\nпаспорта)", "Номер багажа", "Размер багажа", "Краткое описание",
            "Маршрут\nотправления", "Маршрут\nприбытия", "Дата отправления", "Дата прибытия", "Статус\nотправления",
            "Редактировать", "Удалить"
        ])
        self.table.setColumnWidth(3, 350)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 150)
        self.table.setColumnWidth(8, 150)
        self.table.setColumnWidth(10, 80)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_layout.addWidget(self.table)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout, 1)

        self.db_config = {
            "host": "localhost",
            "user": "admin",
            "password": "admin",
            "database": "new_baggage_accounting",
            "port": 3307
        }
        self.db_connection = None

        self.edit_icon = QIcon(QPixmap("edit.svg").scaled(QSize(24, 24), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.delete_icon = QIcon(QPixmap("delete.svg").scaled(QSize(24, 24), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.connect_to_database()

        login_dialog = LoginDialog(self, self.db_connection)
        if login_dialog.exec_() == QDialog.Accepted:
            self.logged_in_user_id = login_dialog.logged_in_user_id
        else:
            sys.exit()

        self.add_plane_btn.clicked.connect(self.show_add_aircraft_form)
        self.create_record_btn.clicked.connect(self.show_create_record_form)
        self.btn1.clicked.connect(self.show_create_report_form)
        self.btn2.clicked.connect(self.show_report_history_form)
        self.btn3.clicked.connect(self.show_user_manual_form)

        self.sort_frame = QFrame(self)
        self.sort_frame.setFrameShape(QFrame.StyledPanel)
        self.sort_frame.hide()

        sort_layout = QVBoxLayout(self.sort_frame)
        sort_layout.setSpacing(5)
        sort_layout.setContentsMargins(5, 5, 5, 5)

        self.sort_combo = ComboBox(self.sort_frame) # qfluentwidgets ComboBox
        self.sort_combo.setPlaceholderText("Выберите поля")
        sort_layout.addWidget(self.sort_combo)
        self.sort_combo.addItems(["По дате отпр.", "По дате приб.", "По имени"])

        self.reverse_checkbox = QCheckBox("Обратный порядок", self.sort_frame)
        sort_layout.addWidget(self.reverse_checkbox)

        self.apply_sort_button = PushButton("Применить", self.sort_frame)
        self.apply_sort_button.clicked.connect(self.apply_sort)
        sort_layout.addWidget(self.apply_sort_button)

        self.sort_frame.setLayout(sort_layout)

        self.filter_frame = QFrame(self)
        self.filter_frame.setFrameShape(QFrame.StyledPanel)
        self.filter_frame.hide()

        filter_layout = QVBoxLayout(self.filter_frame)
        filter_layout.setContentsMargins(5, 5, 5, 5)

        self.filter_field_combo = ComboBox(self.filter_frame) # qfluentwidgets ComboBox
        self.filter_field_combo.addItems(["Все поля"])
        self.filter_field_combo.setPlaceholderText("Выберите поле")
        filter_layout.addWidget(self.filter_field_combo)

        self.filter_line_edit = LineEdit(self.filter_frame)
        self.filter_line_edit.setPlaceholderText("Введите текст для фильтра")
        filter_layout.addWidget(self.filter_line_edit)

        self.apply_filter_button = PushButton("Применить", self.filter_frame)
        self.apply_filter_button.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.apply_filter_button)

        self.filter_frame.setLayout(filter_layout)

        self.sort_btn.clicked.connect(self.show_sort_panel)
        self.filter_btn.clicked.connect(self.show_filter_panel)
        self.search_edit.textChanged.connect(self.apply_filter)

        self.refresh_table()
        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_sort_panel()
        self.sort_frame.hide()
        self.show_filter_panel()
        self.filter_frame.hide()

    def connect_to_database(self):
        try:
            self.db_connection = pymysql.connect(**self.db_config)
            if self.db_connection:
                cursor = self.db_connection.cursor()

                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            password_hash BINARY(60) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                except pymysql.Error as e:
                    print(f"Ошибка при создании таблицы users: {e}")

                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS reports (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            report_name VARCHAR(255),
                            report_data JSON,
                            user_id INT,
                            FOREIGN KEY (user_id) REFERENCES users(id),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                except pymysql.Error as create_e:
                    error_code_create, error_message_create = create_e.args
                    print(f"Ошибка при создании таблицы reports: Код ошибки: {error_code_create}, Сообщение: {error_message_create}")

                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS baggage (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            owner VARCHAR(255),
                            number VARCHAR(255) UNIQUE,
                            type VARCHAR(255),
                            volume VARCHAR(255),
                            size VARCHAR(255),
                            weight VARCHAR(255),
                            aircraft VARCHAR(255),
                            dep_route VARCHAR(255),
                            arr_route VARCHAR(255),
                            dep_date DATETIME,
                            arr_date DATETIME,
                            status VARCHAR(255),
                            `desc` TEXT,
                            user_id INT,
                            FOREIGN KEY (user_id) REFERENCES users(id),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                except pymysql.Error as e:
                    print(f"Ошибка при создании таблицы baggage: {e}")

                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS aircraft (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            number VARCHAR(255) UNIQUE,
                            name VARCHAR(255),
                            capacity VARCHAR(255),
                            max_volume VARCHAR(255),
                            user_id INT,
                            FOREIGN KEY (user_id) REFERENCES users(id),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                except pymysql.Error as e:
                    print(f"Ошибка при создании таблицы aircraft: {e}")

                # --- Автоматическое добавление столбцов user_id, если их нет ---
                try:
                    cursor.execute("ALTER TABLE baggage ADD COLUMN user_id INT")
                except pymysql.Error as e:
                    if e.args[0] == 1060:
                        pass
                    else:
                        print(f"Ошибка при добавлении столбца user_id к таблице baggage: {e}")

                try:
                    cursor.execute("ALTER TABLE reports ADD COLUMN user_id INT")
                except pymysql.Error as e:
                    if e.args[0] == 1060:
                        pass
                    else:
                        print(f"Ошибка при добавлении столбца user_id к таблице reports: {e}")

                try:
                    cursor.execute("ALTER TABLE aircraft ADD COLUMN user_id INT")
                except pymysql.Error as e:
                    if e.args[0] == 1060:
                        pass
                    else:
                        print(f"Ошибка при добавлении столбца user_id к таблице aircraft: {e}")
                
                # --- Автоматическое добавление столбца max_volume, если его нет ---
                try:
                    cursor.execute("ALTER TABLE aircraft ADD COLUMN max_volume VARCHAR(255)")
                except pymysql.Error as e:
                    if e.args[0] == 1060:
                        pass
                    else:
                        print(f"Ошибка при добавлении столбца max_volume к таблице aircraft: {e}")

                # --- Добавление внешних ключей (отдельно, после добавления столбцов) ---
                try:
                    cursor.execute("ALTER TABLE baggage ADD FOREIGN KEY (user_id) REFERENCES users(id)")
                except pymysql.Error as e:
                    if e.args[0] == 1068:
                        pass
                    elif e.args[0] == 1005:
                        pass
                    elif e.args[0] == 1050:
                        pass
                    else:
                        print(f"Ошибка при добавлении внешнего ключа к таблице baggage для user_id: {e}")

                try:
                    cursor.execute("ALTER TABLE reports ADD FOREIGN KEY (user_id) REFERENCES users(id)")
                except pymysql.Error as e:
                     if e.args[0] == 1068:
                        pass
                     elif e.args[0] == 1005:
                        pass
                     elif e.args[0] == 1050:
                        pass
                     else:
                        print(f"Ошибка при добавлении внешнего ключа к таблице reports для user_id: {e}")

                try:
                    cursor.execute("ALTER TABLE aircraft ADD FOREIGN KEY (user_id) REFERENCES users(id)")
                except pymysql.Error as e:
                    if e.args[0] == 1068:
                        pass
                    elif e.args[0] == 1005:
                        pass
                    elif e.args[0] == 1050:
                        pass
                    else:
                        print(f"Ошибка при добавлении внешнего ключа к таблице aircraft для user_id: {e}")


                cursor.close()

                time.sleep(1)

                self.refresh_table()

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {e}")

    def close_database_connection(self):
        if self.db_connection:
            self.db_connection.close()

    def show_create_record_form(self):
        create_record_form = CreateRecordForm(self, self.current_data, self.logged_in_user_id)
        create_record_form.exec_()

    def show_add_aircraft_form(self):
        add_aircraft_form = AddAircraftForm(self, self.logged_in_user_id)
        add_aircraft_form.exec_()

    def show_report_history_form(self):
        report_history_form = ReportHistoryForm(self)
        report_history_form.exec_()

    def show_create_report_form(self):
        create_report_form = CreateReportForm(self, self.current_data, self.logged_in_user_id)
        create_report_form.exec_()

    def show_user_manual_form(self):
        user_manual_form = UserManualForm(self)
        user_manual_form.exec_()

    def refresh_table(self, data_to_display=None):
        if data_to_display is None:
            if not self.db_connection:
                return

            try:
                cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
                sql_query = "SELECT * FROM baggage WHERE user_id = %s"
                cursor.execute(sql_query, (self.logged_in_user_id,))
                self.full_data = cursor.fetchall()
                data_to_display = self.full_data
                cursor.close()
            except pymysql.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные из базы данных: {e}")
                return

        self.current_data = data_to_display

        try:
            self.table.setRowCount(0)
            if data_to_display:
                for row_index, row_data in enumerate(data_to_display):
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(row_data.get("owner", ""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(row_data.get("number", ""))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(row_data.get("size", ""))))
                    self.table.setItem(row, 3, QTableWidgetItem(str(row_data.get("desc", ""))))
                    self.table.setItem(row, 4, QTableWidgetItem(str(row_data.get("dep_route", ""))))
                    self.table.setItem(row, 5, QTableWidgetItem(str(row_data.get("arr_route", ""))))
                    self.table.setItem(row, 6, QTableWidgetItem(str(row_data.get("dep_date", ""))))
                    self.table.setItem(row, 7, QTableWidgetItem(str(row_data.get("arr_date", ""))))
                    self.table.setItem(row, 8, QTableWidgetItem(str(row_data.get("status", ""))))

                    edit_button = QtPushButton(self)
                    edit_button.setIcon(self.edit_icon)
                    edit_button.setToolTip("Редактировать запись")
                    edit_button.clicked.connect(lambda checked, index=row_index: self.edit_record(index))
                    self.table.setCellWidget(row, 9, edit_button)

                    delete_button = QtPushButton(self)
                    delete_button.setIcon(self.delete_icon)
                    delete_button.setToolTip("Удалить запись")
                    delete_button.clicked.connect(lambda checked, index=row_index: self.delete_record(index))
                    self.table.setCellWidget(row, 10, delete_button)

            else:
                pass
        except Exception as e:
            pass

    def edit_record(self, row_index):
        number = self.table.item(row_index, 1).text()

        if not self.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT * FROM baggage WHERE number = %s AND user_id = %s"
            cursor.execute(sql_query, (number, self.logged_in_user_id))
            record_data = cursor.fetchone()
            cursor.close()

            if record_data:
                edit_record_form = EditRecordForm(self, record_data, self.logged_in_user_id)
                edit_record_form.exec_()
                self.refresh_table()
            else:
                QMessageBox.warning(self, "Предупреждение", "Запись не найдена для редактирования или не принадлежит вам.")

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные для редактирования: {e}")

    def delete_record(self, row_index):
        number = self.table.item(row_index, 1).text()

        reply = QMessageBox.question(self, 'Подтверждение удаления',
            f"Вы уверены, что хотите удалить запись с номером багажа '{number}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if not self.db_connection:
                QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
                return

            try:
                cursor = self.db_connection.cursor()
                sql_query = "DELETE FROM baggage WHERE number = %s AND user_id = %s"
                cursor.execute(sql_query, (number, self.logged_in_user_id))
                self.db_connection.commit()
                cursor.close()
                QMessageBox.information(self, "Успех", f"Запись с номером багажа '{number}' успешно удалена.")
                self.refresh_table()
            except pymysql.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {e}")

    def show_sort_panel(self):
        if self.sort_frame.isVisible():
            self.sort_frame.hide()
        else:
            # Фиксированная ширина 200px для sort_frame и ComboBox
            self.sort_frame.setGeometry(self.sort_btn.x(), self.sort_btn.y() + self.sort_btn.height(),
                                        200, 150)
            self.sort_frame.show()

    def show_filter_panel(self):
        if self.filter_frame.isVisible():
            self.filter_frame.hide()
        else:
            # Фиксированная ширина 200px для filter_frame и ComboBox
            self.filter_frame.setGeometry(self.filter_btn.x(), self.filter_btn.y() + self.filter_btn.height(),
                                        200, 150)
            self.filter_frame.show()

    def apply_sort(self):
        selected_item_text = self.sort_combo.currentText() # Получаем текст выбранного элемента
        reverse = self.reverse_checkbox.isChecked()

        sort_options = {
            "По дате отпр.": "dep_date",
            "По дате приб.": "arr_date",
            "По имени": "owner"
        }

        selected_fields = [sort_options[selected_item_text]] if selected_item_text in sort_options else [] # Используем текст для поиска поля

        if not selected_fields or not selected_item_text: # Проверка и на текст и на наличие полей
            return

        order_by_clause = ", ".join(
            [f"{field} {'DESC' if reverse else 'ASC'}" for field in selected_fields])

        if not self.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = f"SELECT * FROM baggage WHERE user_id = %s ORDER BY {order_by_clause}"
            cursor.execute(sql_query, (self.logged_in_user_id,))
            sorted_data_from_db = cursor.fetchall()
            cursor.close()

            self.current_data = sorted_data_from_db
            self.refresh_table(self.current_data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отсортировать данные: {e}")

        self.sort_frame.hide()

    def apply_filter(self):
        filter_text = self.filter_line_edit.text().lower()
        search_text = self.search_edit.text().lower()
        selected_field = self.filter_field_combo.currentText()


        if not self.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        filtered_data = self.full_data[:] # Важно: создаем копию!

        if filter_text or search_text:
            filtered_data = [
                row for row in filtered_data
                if self.check_row_matches_filter(row, selected_field, filter_text, search_text)
            ]


        self.current_data = filtered_data
        self.refresh_table(self.current_data)


    def check_row_matches_filter(self, row, selected_field, filter_text, search_text):
        combined_filter_text = (filter_text + " " + search_text).strip().lower()
        filter_parts = combined_filter_text.split()

        if not combined_filter_text:
            return True

        if selected_field == "Все поля":
            matches = any( # Изменено с all на any
                any(part in str(value).lower() for part in filter_parts) # Изменено с all на any
                for value in row.values()
            )
            return matches
        elif selected_field and selected_field != "Выберите поле" and selected_field != "Все поля": # <-- Изменено условие!
            field_value = row.get(selected_field.strip().lower()) # <-- Добавили .strip()
            if field_value is None:
                return False

            matches = any(part in str(field_value).lower() for part in filter_parts) # Изменено с all на any
            return matches
        elif selected_field == "Выберите поле": # Добавлено явно условие для "Выберите поле"
            return True
        else: # Добавлено else для обработки других случаев (если вдруг selected_field будет None или еще что-то)
            return True


    def closeEvent(self, event):
        self.close_database_connection()
        event.accept()


# region EditRecordForm
class EditRecordForm(QDialog):
    def __init__(self, parent=None, record_data=None, user_id=None): # Added user_id
        super().__init__(parent)
        self.record_data = record_data
        self.parent_main_win = parent
        self.setWindowTitle("Редактировать запись")
        self.resize(500, 350)
        self.user_id = user_id # Store user_id

        main_layout = QGridLayout(self)

        left_layout = QGridLayout()
        left_layout.addWidget(QLabel("Владелец багажа:"), 0, 0)
        self.owner_edit = LineEdit(self)
        left_layout.addWidget(self.owner_edit, 0, 1)

        left_layout.addWidget(QLabel("Номер багажа:"), 1, 0)
        self.number_edit = LineEdit(self)
        self.number_edit.setEnabled(False)
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

        right_layout = QGridLayout()
        right_layout.addWidget(QLabel("Маршрут отправления:"), 0, 0)
        self.dep_route_edit = LineEdit(self)
        right_layout.addWidget(self.dep_route_edit, 0, 1)

        right_layout.addWidget(QLabel("Маршрут прибытия:"), 1, 0)
        self.arr_route_edit = LineEdit(self)
        right_layout.addWidget(self.arr_route_edit, 1, 1)

        right_layout.addWidget(QLabel("Дата отправления:"), 2, 0)
        self.dep_date_edit = DateTimeEdit(self)
        self.dep_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        right_layout.addWidget(self.dep_date_edit, 2, 1)

        right_layout.addWidget(QLabel("Дата прибытия:"), 3, 0)
        self.arr_date_edit = DateTimeEdit(self)
        self.arr_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        right_layout.addWidget(self.arr_date_edit, 3, 1)

        right_layout.addWidget(QLabel("Статус отправления:"), 4, 0)
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["Зарегистрирован", "В пути", "Прибыл", "Утерян"])
        right_layout.addWidget(self.status_combo, 4, 1)

        right_layout.addWidget(QLabel("Краткое описание:"), 5, 0)
        self.desc_edit = LineEdit(self)
        right_layout.addWidget(self.desc_edit, 5, 1)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding), 6, 0, 1, 2)

        main_layout.addLayout(left_layout, 0, 0)
        main_layout.addLayout(right_layout, 0, 1)

        self.save_button = PushButton("СОХРАНИТЬ", self)
        main_layout.addWidget(self.save_button, 1, 0, 1, 2)

        self.save_button.clicked.connect(self.save_edited_data)
        self.load_aircraft_numbers()
        self.populate_form_fields()
    
    def get_aircraft_data(self, aircraft_number):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return None

        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT capacity, max_volume FROM aircraft WHERE number = %s AND user_id = %s"
            cursor.execute(sql_query, (aircraft_number, self.user_id))
            aircraft_data = cursor.fetchone()
            cursor.close()
            return aircraft_data
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении данных о самолете: {e}")
            return None


    def populate_form_fields(self):
        if self.record_data:
            self.owner_edit.setText(self.record_data.get("owner", ""))
            self.number_edit.setText(self.record_data.get("number", ""))
            self.type_combo.setCurrentText(self.record_data.get("type", ""))
            self.volume_edit.setText(self.record_data.get("volume", ""))
            self.size_combo.setCurrentText(self.record_data.get("size", ""))
            self.weight_edit.setText(self.record_data.get("weight", ""))
            self.aircraft_combo.setCurrentText(self.record_data.get("aircraft", ""))
            self.dep_route_edit.setText(self.record_data.get("dep_route", ""))
            self.arr_route_edit.setText(self.record_data.get("arr_route", ""))
            dep_date_str = self.record_data.get("dep_date", "")
            arr_date_str = self.record_data.get("arr_date", "")

            if dep_date_str:
                self.dep_date_edit.setDateTime(QDateTime.fromString(str(dep_date_str), "yyyy-MM-dd HH:mm:ss"))
            if arr_date_str:
                self.arr_date_edit.setDateTime(QDateTime.fromString(str(arr_date_str), "yyyy-MM-dd HH:mm:ss"))

            self.status_combo.setCurrentText(self.record_data.get("status", ""))
            self.desc_edit.setText(self.record_data.get("desc", ""))

    def load_aircraft_numbers(self):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
           cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
           sql_query = "SELECT number FROM aircraft WHERE user_id = %s" # Filter by user_id
           cursor.execute(sql_query, (self.user_id,)) # Pass user_id
           aircraft_numbers = [row['number'] for row in cursor.fetchall()]
           cursor.close()
           self.aircraft_combo.clear()
           self.aircraft_combo.addItems(aircraft_numbers)
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить номера самолетов: {e}")

    def save_edited_data(self):
        edited_record = {
            "owner": self.owner_edit.text(),
            "number": self.number_edit.text(),
            "type": self.type_combo.currentText(),
            "volume": self.volume_edit.text(),
            "size": self.size_combo.currentText(),
            "weight": self.weight_edit.text(),
            "aircraft": self.aircraft_combo.currentText(),
            "dep_route": self.dep_route_edit.text(),
            "arr_route": self.arr_route_edit.text(),
            "dep_date": self.dep_date_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
            "arr_date": self.arr_date_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
            "status": self.status_combo.currentText(),
            "desc": self.desc_edit.text()
        }
        
        # --- НАЧАЛО ПРОВЕРКИ ОГРАНИЧЕНИЙ ---
        dep_date = self.dep_date_edit.dateTime().toPyDateTime().date()
        arr_date = self.arr_date_edit.dateTime().toPyDateTime().date()

        if dep_date == arr_date:
            aircraft_number = edited_record["aircraft"]
            if aircraft_number:
                aircraft_data = self.get_aircraft_data(aircraft_number)

                if aircraft_data:
                    try:
                        baggage_weight = float(edited_record["weight"]) if edited_record["weight"] else 0.0
                        baggage_volume = float(edited_record["volume"]) if edited_record["volume"] else 0.0
                        aircraft_capacity = float(aircraft_data["capacity"]) if aircraft_data["capacity"] else 0.0
                        aircraft_max_volume = float(aircraft_data["max_volume"]) if aircraft_data["max_volume"] else 0.0

                        if baggage_weight > aircraft_capacity or baggage_volume > aircraft_max_volume:
                            QMessageBox.warning(self, "Ошибка", "Вес или объем багажа превышает грузоподъемность или максимальный объем самолета для рейсов в один день.")
                            return
                    except ValueError:
                        QMessageBox.warning(self, "Ошибка", "Некорректные числовые значения для веса, объема, грузоподъемности или максимального объема.")
                        return
            else:
                QMessageBox.warning(self, "Предупреждение", "Выберите номер самолета для проверки ограничений.")
                return

        # --- КОНЕЦ ПРОВЕРКИ ОГРАНИЧЕНИЙ ---

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.parent_main_win.db_connection.cursor()
            sql_query = """
                UPDATE baggage SET
                    owner = %s,
                    type = %s,
                    volume = %s,
                    size = %s,
                    weight = %s,
                    aircraft = %s,
                    dep_route = %s,
                    arr_route = %s,
                    dep_date = %s,
                    arr_date = %s,
                    status = %s,
                    `desc` = %s
                WHERE number = %s AND user_id = %s
            """ # Filter by user_id in UPDATE
            cursor.execute(sql_query, (edited_record["owner"], edited_record["type"], edited_record["volume"], edited_record["size"],
                edited_record["weight"], edited_record["aircraft"], edited_record["dep_route"], edited_record["arr_route"],
                edited_record["dep_date"], edited_record["arr_date"], edited_record["status"], edited_record["desc"],
                edited_record["number"], self.user_id)) # Pass user_id in UPDATE
            self.parent_main_win.db_connection.commit()
            cursor.close()
            QMessageBox.information(self, "Успех", "Запись успешно обновлена в базе данных")

            self.parent_main_win.refresh_table()
            self.close()

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись в базе данных: {e}")
# endregion

# region CreateRecordForm
class CreateRecordForm(QDialog):
    def __init__(self, parent=None, data=None, user_id=None): # Added user_id
        super().__init__(parent)
        self.data = data
        self.parent_main_win = parent
        self.setWindowTitle("Создать запись")
        self.resize(500, 350)
        self.user_id = user_id # Store user_id

        main_layout = QGridLayout(self)

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

        right_layout = QGridLayout()
        right_layout.addWidget(QLabel("Маршрут отправления:"), 0, 0)
        self.dep_route_edit = LineEdit(self)
        right_layout.addWidget(self.dep_route_edit, 0, 1)

        right_layout.addWidget(QLabel("Маршрут прибытия:"), 1, 0)
        self.arr_route_edit = LineEdit(self)
        right_layout.addWidget(self.arr_route_edit, 1, 1)

        right_layout.addWidget(QLabel("Дата отправления:"), 2, 0)
        self.dep_date_edit = DateTimeEdit(self)
        self.dep_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        right_layout.addWidget(self.dep_date_edit, 2, 1)

        right_layout.addWidget(QLabel("Дата прибытия:"), 3, 0)
        self.arr_date_edit = DateTimeEdit(self)
        self.arr_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        right_layout.addWidget(self.arr_date_edit, 3, 1)

        right_layout.addWidget(QLabel("Статус отправления:"), 4, 0)
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["Зарегистрирован", "В пути", "Прибыл", "Утерян"])
        right_layout.addWidget(self.status_combo, 4, 1)

        right_layout.addWidget(QLabel("Краткое описание:"), 5, 0)
        self.desc_edit = LineEdit(self)
        right_layout.addWidget(self.desc_edit, 5, 1)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding), 6, 0, 1, 2)

        main_layout.addLayout(left_layout, 0, 0)
        main_layout.addLayout(right_layout, 0, 1)

        self.save_button = PushButton("СОХРАНИТЬ", self)
        main_layout.addWidget(self.save_button, 4, 0, 1, 2)

        self.save_button.clicked.connect(self.save_data)
        self.load_aircraft_numbers()

    def get_aircraft_data(self, aircraft_number):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return None

        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT capacity, max_volume FROM aircraft WHERE number = %s AND user_id = %s"
            cursor.execute(sql_query, (aircraft_number, self.user_id))
            aircraft_data = cursor.fetchone()
            cursor.close()
            return aircraft_data
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении данных о самолете: {e}")
            return None

    def load_aircraft_numbers(self):
        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
           cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
           sql_query = "SELECT number FROM aircraft WHERE user_id = %s" # Filter by user_id
           cursor.execute(sql_query, (self.user_id,)) # Pass user_id
           aircraft_numbers = [row['number'] for row in cursor.fetchall()]
           cursor.close()
           self.aircraft_combo.clear()
           self.aircraft_combo.addItems(aircraft_numbers)
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить номера самолетов: {e}")

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
            "dep_date": self.dep_date_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
            "arr_date": self.arr_date_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
            "status": self.status_combo.currentText(),
            "desc": self.desc_edit.text()
        }

        # --- НАЧАЛО ПРОВЕРКИ ОГРАНИЧЕНИЙ ---
        dep_date = self.dep_date_edit.dateTime().toPyDateTime().date()
        arr_date = self.arr_date_edit.dateTime().toPyDateTime().date()

        if dep_date == arr_date:
            aircraft_number = new_record["aircraft"]
            if aircraft_number:
                aircraft_data = self.get_aircraft_data(aircraft_number)
                if aircraft_data:
                    try:
                        baggage_weight = float(new_record["weight"]) if new_record["weight"] else 0.0
                        baggage_volume = float(new_record["volume"]) if new_record["volume"] else 0.0
                        aircraft_capacity = float(aircraft_data["capacity"]) if aircraft_data["capacity"] else 0.0
                        aircraft_max_volume = float(aircraft_data["max_volume"]) if aircraft_data["max_volume"] else 0.0
                        if baggage_weight > aircraft_capacity or baggage_volume > aircraft_max_volume:
                             QMessageBox.warning(self, "Ошибка", "Вес или объем багажа превышает грузоподъемность или максимальный объем самолета для рейсов в один день.")
                             return
                    except ValueError:
                         QMessageBox.warning(self, "Ошибка", "Некорректные числовые значения для веса, объема, грузоподъемности или максимального объема.")
                         return
            else:
                  QMessageBox.warning(self, "Предупреждение", "Выберите номер самолета для проверки ограничений.")
                  return

        # --- КОНЕЦ ПРОВЕРКИ ОГРАНИЧЕНИЙ ---

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.parent_main_win.db_connection.cursor()
            sql_query = """
                INSERT INTO baggage (owner, number, type, volume, size, weight, aircraft, dep_route, arr_route, dep_date, arr_date, status, `desc`, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """ # Added user_id to INSERT
            cursor.execute(sql_query, (new_record["owner"], new_record["number"], new_record["type"], new_record["volume"], new_record["size"],
                new_record["weight"], new_record["aircraft"], new_record["dep_route"], new_record["arr_route"],
                new_record["dep_date"], new_record["arr_date"], new_record["status"], new_record["desc"], self.user_id)) # Pass user_id in INSERT
            self.parent_main_win.db_connection.commit()
            cursor.close()
            QMessageBox.information(self, "Успех", "Запись успешно добавлена в базу данных")

            self.parent_main_win.refresh_table()
            self.close()

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись в базу данных: {e}")
# endregion

# region AddAircraftForm
class AddAircraftForm(QDialog):
    def __init__(self, parent=None, user_id=None): # Added user_id
        super().__init__(parent)
        self.parent_main_win = parent
        self.setWindowTitle("Добавление самолета")
        self.setMinimumSize(300, 200)
        self.user_id = user_id # Store user_id

        layout = QFormLayout(self)
        
        self.aircraft_number_edit = LineEdit(self)
        layout.addRow("Номер самолета:", self.aircraft_number_edit)

        self.aircraft_name_edit = LineEdit(self)
        layout.addRow("Наименование самолета:", self.aircraft_name_edit)

        self.aircraft_capacity_edit = LineEdit(self)
        layout.addRow("Грузоподъемность:", self.aircraft_capacity_edit)
        self.aircraft_capacity_edit.setValidator(QDoubleValidator()) # Только числа

        self.aircraft_max_volume_edit = LineEdit(self)
        layout.addRow("Максимальный объем:", self.aircraft_max_volume_edit)
        self.aircraft_max_volume_edit.setValidator(QDoubleValidator())  # Только числа
        
        self.save_button = PushButton("СОХРАНИТЬ", self)
        layout.addRow(self.save_button)

        self.save_button.clicked.connect(self.save_data)

    def save_data(self):
        aircraft_data = {
            "number": self.aircraft_number_edit.text(),
            "name": self.aircraft_name_edit.text(),
            "capacity": self.aircraft_capacity_edit.text(),
            "max_volume": self.aircraft_max_volume_edit.text()
        }

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.parent_main_win.db_connection.cursor()
            sql_query = """
                INSERT INTO aircraft (number, name, capacity, max_volume, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_query, (aircraft_data["number"], aircraft_data["name"], aircraft_data["capacity"], aircraft_data["max_volume"], self.user_id))
            self.parent_main_win.db_connection.commit()
            cursor.close()
            QMessageBox.information(self, "Успех", "Данные о самолете успешно добавлены")
            self.close()

        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить данные о самолете в базу данных: {e}")
# endregion

# region CreateReportForm
class CreateReportForm(QDialog):
    def __init__(self, parent=None, data=None, user_id=None): # Added user_id
        super().__init__(parent)
        self.data = data
        self.parent_main_win = parent
        self.setWindowTitle("Создание отчета")
        self.resize(600, 400)
        self.user_id = user_id # Store user_id

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Отчет", self)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        date_layout = QGridLayout()
        self.start_date_edit = DateTimeEdit(self)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.end_date_edit = DateTimeEdit(self)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")

        date_layout.addWidget(QLabel("С"), 0, 0)
        date_layout.addWidget(self.start_date_edit, 0, 1)
        date_layout.addWidget(QLabel("ПО"), 0, 2)
        date_layout.addWidget(self.end_date_edit, 0, 3)
        date_layout.setColumnStretch(1, 1)
        date_layout.setColumnStretch(3, 1)

        main_layout.addLayout(date_layout)

        self.sort_button = ComboBox(self)
        self.sort_button.addItems(["По владельцу", "По номеру", "По дате отпр.", "По дате приб."])
        self.sort_button.setPlaceholderText("Сортировка")
        main_layout.addWidget(self.sort_button)
        self.sort_button.currentIndexChanged.connect(self.update_report_table)

        self.report_table = QTableWidget(self)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels(["Владелец", "Номер", "Дата отправления", "Дата прибытия", "Краткое описание"])
        self.report_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.report_table)

        self.save_to_file_checkbox = QCheckBox("Сохранить в файл", self)
        main_layout.addWidget(self.save_to_file_checkbox)

        create_button = PushButton("СОЗДАТЬ", self)
        main_layout.addWidget(create_button)
        create_button.clicked.connect(self.create_report_dialog)
        create_button.clicked.connect(self.update_report_table)

    def create_report_dialog(self):
        report_name, ok = QInputDialog.getText(self, "Имя отчета", "Введите имя отчета:")
        if ok and report_name:
            self.create_report(report_name)
        elif ok:
            QMessageBox.warning(self, "Предупреждение", "Имя отчета не было введено. Отчет не будет создан.")

    def create_report(self, report_name="Отчет"):
        start_date_str = self.start_date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_date_str = self.end_date_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not self.start_date_edit.dateTime().isValid() or not self.end_date_edit.dateTime().isValid():
            QMessageBox.warning(self, "Ошибка", "Выберите даты начала и окончания периода.")
            return

        if self.start_date_edit.dateTime() > self.end_date_edit.dateTime():
            QMessageBox.warning(self, "Ошибка", "Дата начала периода должна быть меньше или равна дате окончания.")
            return

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return
        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT * FROM baggage WHERE user_id = %s" # Filter by user_id
            cursor.execute(sql_query, (self.user_id,)) # Pass user_id
            data_from_db = cursor.fetchall()
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные из базы данных: {e}")
            return
        finally:
            if cursor:
                cursor.close()

        filtered_data = []
        for row in data_from_db:
            dep_date_db_str = str(row.get("dep_date", ""))
            if start_date_str <= dep_date_db_str <= end_date_str:
                filtered_data.append(row)

        sort_field = {
            "По владельцу": "owner",
            "По номеру": "number",
            "По дате отпр.": "dep_date",
            "По дате приб.": "arr_date"
        }.get(self.sort_button.currentText())

        if sort_field:
            try:
                if sort_field in ["dep_date", "arr_date"]:
                    filtered_data.sort(key=lambda row: datetime.datetime.strptime(str(row.get(sort_field, "")), "%Y-%m-%d %H:%M:%S") if row.get(sort_field) else datetime.datetime.min)
                else:
                    filtered_data.sort(key=lambda row: row.get(sort_field, ""))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось отсортировать данные: {e}")
                return

        self.report_table.setRowCount(0)

        for row_data in filtered_data:
            row_position = self.report_table.rowCount()
            self.report_table.insertRow(row_position)
            self.report_table.setItem(row_position, 0, QTableWidgetItem(row_data.get("owner", "")))
            self.report_table.setItem(row_position, 1, QTableWidgetItem(row_data.get("number", "")))
            dep_date_str = str(row_data.get("dep_date", ""))
            arr_date_str = str(row_data.get("arr_date", ""))
            self.report_table.setItem(row_position, 2, QTableWidgetItem(dep_date_str))
            self.report_table.setItem(row_position, 3, QTableWidgetItem(arr_date_str))
            self.report_table.setItem(row_position, 4, QTableWidgetItem(row_data.get("desc", "")))

        self.save_report_to_database(filtered_data, start_date_str, end_date_str, report_name)

        if self.save_to_file_checkbox.isChecked():
            self.save_report_to_file(filtered_data, start_date_str, end_date_str, report_name)

    def format_report_content_txt(self, report_data, report_name, start_date, end_date):
        formatted_text = f"Отчет о багаже: {report_name}\n\n"
        formatted_text += f"Период: с {start_date} по {end_date}\n\n"

        data = report_data.get("data", [])
        if not data:
            formatted_text += "Нет данных о багаже за выбранный период.\n"
        else:
            formatted_text += "{:<20} {:<15} {:<20} {:<20} {:<50}\n".format("Владелец", "Номер багажа", "Дата отправления", "Дата прибытия", "Описание")
            formatted_text += "-" * 140 + "\n"
            for item in data:
                description = item.get('desc', '')
                wrapped_description = ""
                line_width = 50  # Максимальная длина строки для описания
                current_line = ""
                for word in description.split():
                    if len(current_line) + len(word) + 1 <= line_width:
                        current_line += (word + " " )
                    else:
                        wrapped_description += current_line.rstrip() + "\n"
                        current_line = word + " "
                wrapped_description += current_line.rstrip() # Добавляем последнюю строку

                # Форматируем даты в строку явно, если они есть
                dep_date_str = str(item.get('dep_date', ''))
                arr_date_str = str(item.get('arr_date', ''))

                formatted_text += "{:<20} {:<15} {:<20} {:<20} {:<50}\n".format(
                    item.get('owner', ''),
                    item.get('number', ''),
                    dep_date_str, # Используем отформатированные даты
                    arr_date_str, # Используем отформатированные даты
                    wrapped_description.rstrip()
                )
        return formatted_text

    def save_report_to_file(self, filtered_data, start_date, end_date, report_name):
        report_data_for_file = {
            "start_date": start_date,
            "end_date": end_date,
            "data": filtered_data
        }
        file_content = self.format_report_content_txt(report_data_for_file, report_name, start_date, end_date)

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Сохранить отчет в файл", f"{report_name}.txt", "Text Files (*.txt)")

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(file_content)
                QMessageBox.information(self, "Успех", f"Отчет сохранен в файл: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет в файл: {e}")


    def save_report_to_database(self, filtered_data, start_date, end_date, report_name):
        serialized_filtered_data = []
        for row in filtered_data:
            serialized_row = {}
            for key, value in row.items():
                serialized_row[key] = str(value)

            serialized_filtered_data.append(serialized_row)


        report_data = {
            "start_date": start_date,
            "end_date": end_date,
            "data": serialized_filtered_data
        }

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return

        try:
            cursor = self.parent_main_win.db_connection.cursor()
            report_json = json.dumps(report_data, ensure_ascii=False)
            sql_query = "INSERT INTO reports (report_name, report_data, user_id) VALUES (%s, %s, %s)" # Added user_id to INSERT
            cursor.execute(sql_query, (report_name, report_json, self.user_id)) # Pass user_id in INSERT
            self.parent_main_win.db_connection.commit()
            cursor.close()
            QMessageBox.information(self, "Успех", "Отчет успешно сохранен в базу данных")
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет в базу данных: {e}")


    def update_report_table(self):
        start_date = self.start_date_edit.dateTime()
        end_date = self.end_date_edit.dateTime()

        if not start_date.isValid() or not end_date.isValid():
            return

        if not self.parent_main_win.db_connection:
            QMessageBox.critical(self, "Ошибка", "Нет соединения с базой данных")
            return
        try:
            cursor = self.parent_main_win.db_connection.cursor(pymysql.cursors.DictCursor)
            sql_query = "SELECT * FROM baggage WHERE user_id = %s" # Filter by user_id
            cursor.execute(sql_query, (self.user_id,)) # Pass user_id
            data_from_db = cursor.fetchall()
            cursor.close()
        except pymysql.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные из базы данных: {e}")
            return

        filtered_data = []
        for row in data_from_db:
            dep_date_db_str = str(row.get("dep_date", ""))
            dep_datetime = datetime.datetime.strptime(dep_date_db_str, "%Y-%m-%d %H:%M:%S") if dep_date_db_str else datetime.datetime.min
            if start_date.toPyDateTime() <= dep_datetime <= end_date.toPyDateTime():
                filtered_data.append(row)

        sort_field = {
            "По владельцу": "owner",
            "По номеру": "number",
            "По дате отпр.": "dep_date",
            "По дате приб.": "arr_date"
        }.get(self.sort_button.currentText())

        if sort_field:
            try:
                if sort_field in ["dep_date", "arr_date"]:
                    filtered_data.sort(key=lambda row: datetime.datetime.strptime(str(row.get(sort_field, "")), "%Y-%m-%d %H:%M:%S") if row.get(sort_field) else datetime.datetime.min)
                else:
                    filtered_data.sort(key=lambda row: row.get(sort_field, ""))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось отсортировать данные: {e}")
                return

        self.report_table.setRowCount(0)

        for row_data in filtered_data:
            row_position = self.report_table.rowCount()
            self.report_table.insertRow(row_position)
            self.report_table.setItem(row_position, 0, QTableWidgetItem(row_data.get("owner", "")))
            self.report_table.setItem(row_position, 1, QTableWidgetItem(row_data.get("number", "")))
            dep_date_str = str(row_data.get("dep_date", ""))
            arr_date_str = str(row_data.get("arr_date", ""))
            self.report_table.setItem(row_position, 2, QTableWidgetItem(dep_date_str))
            self.report_table.setItem(row_position, 3, QTableWidgetItem(arr_date_str))
            self.report_table.setItem(row_position, 4, QTableWidgetItem(row_data.get("desc", "")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qss)
    win = MainWin()
    sys.exit(app.exec_())