from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTime, QTimer
from PyQt5 import QtWidgets, uic
import sqlite3
import datetime
import logging

logging.basicConfig(filename="log.txt", level=logging.DEBUG)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi('ui_3.ui', self)
        self.setWindowTitle("Электронный журнал")
        # print(dir(self.tableWidget_2))
        # self.setupUi(self)
        self.username = user
        self.table1 = [["" for i in range(7)] for j in range(8)]
        self.table2 = [["" for i in range(7)] for j in range(self.tableWidget_2.rowCount())]
        for i in range(7):
            self.tableWidget_2.setColumnWidth(i, 35)
        self.tableWidget_2.setColumnWidth(7, 120)
        self.tableWidget_2.setColumnWidth(8, 120)

        self.actual_day = 0
        self.actual_week = self.get_week_borders_and_number(0)[0]

        self.dbase = sqlite3.connect("teacher.sqlite")
        self.cursor = self.dbase.cursor()

        self.print_week(0)
        self.pushButton.clicked.connect(self.add_student)
        self.pushButton_4.clicked.connect(self.swap_week_left)
        self.pushButton_5.clicked.connect(self.sqap_week_right)
        self.pushButton_2.clicked.connect(self.swap_week_left)
        self.pushButton_3.clicked.connect(self.sqap_week_right)

        self.pixmap = QPixmap('logo.jpg')
        self.label_6.setPixmap(self.pixmap)
        self.label_7.setPixmap(self.pixmap)
        self.label.resize(self.pixmap.width(), self.pixmap.height())

        self.label_4.setText(datetime.datetime.now().strftime("%m.%d.%y"))

        self.update_lcd()
        timer = QTimer(self)
        timer.timeout.connect(self.update_lcd)
        timer.start(1000)
        self.show_empty_table2()

        self.get_data_from_db_table1()
        self.update_table1()
        self.get_data_from_db_table2()
        self.update_table2()
        timer_tables = QTimer(self)
        timer_tables.timeout.connect(self.process_table)
        # timer_tables.start(40000)
        self.read_table1()
        self.read_table2()
        logging.info("Программа запущена")

    def update_lcd(self):
        time = QTime.currentTime().toString("hh:mm")
        self.lcdNumber.display(time)
        logging.info("Обновлено значение LCD дисплея")

    # @staticmethod
    def get_week_borders_and_number(self, day):
        today_date = datetime.datetime.now() + datetime.timedelta(days=day)
        calendar = today_date.isocalendar()
        week_number = calendar.week
        weekday = calendar.weekday
        start_date = today_date + datetime.timedelta(days=1 - weekday)
        end_date = today_date + datetime.timedelta(days=7 - weekday)
        return week_number, str(start_date.day) + "." + str(start_date.month), str(end_date.day) + "." + str(
            end_date.month)

    def print_week(self, day):
        current_week = self.get_week_borders_and_number(day)
        self.actual_week = current_week[0]
        # print(self.actual_week)
        logging.info(f"Текущая неделя изменена на {self.actual_week}")
        self.label_2.setText(current_week[1] + " - " + current_week[2])
        self.label_3.setText(current_week[1] + " - " + current_week[2])

    def swap_week_left(self):
        self.read_table1()
        self.read_table2()
        self.actual_day -= 7
        self.print_week(self.actual_day)
        # self.show_empty_table2()
        self.clear_cache()
        self.get_data_from_db_table1()
        self.update_table1()
        self.get_data_from_db_table2()
        self.update_table2()

    def sqap_week_right(self):
        self.read_table1()
        self.read_table2()
        self.actual_day += 7
        self.print_week(self.actual_day)
        self.clear_cache()
        self.get_data_from_db_table1()
        self.update_table1()
        self.get_data_from_db_table2()
        self.update_table2()

    def clear_cache(self):
        for i in range(self.tableWidget_2.rowCount()):
            for j in range(len(self.table2[0])):
                self.tableWidget_2.setItem(i, j, QtWidgets.QTableWidgetItem(""))
                self.table2[i][j] = ""

    def add_student(self):
        name_1 = self.lineEdit_3.text()
        name_2 = self.lineEdit_2.text()
        name_3 = self.lineEdit.text()
        if name_1 != "" and name_2 != "" and name_3 != "":
            full_name = "{0} {1} {2}".format(name_1, name_2, name_3)
            self.cursor.execute(f"select id_student from students where full_name='{full_name}';")
            a = self.cursor.fetchall()
            if len(a) != 0:
                show_dialog(f"Этот ученик уже записан в журнал!\n{full_name}", "Предупреждение")
                self.lineEdit_3.setText("")
                self.lineEdit_2.setText("")
                self.lineEdit.setText("")
                return

            self.cursor.execute(f"INSERT INTO students(full_name) VALUES ('{full_name}');")
            self.dbase.commit()
            self.cursor.execute(f"select distinct week_numder from progress;")
            weeks = self.cursor.fetchall()
            for week in weeks:
                for i in range(7):
                    self.cursor.execute(f"insert into progress(id_student,week_numder,day_of_week,mark) "
                                        f"values((select (select id_student from students where full_name=='{full_name}')), "
                                        f"{int(week[0])},{i},'');")
                self.dbase.commit()
            self.statusbar.showMessage("Ученик успешно сохранен в базе данных ")
            logging.info(f"Добавлен новый студент: {full_name}")
            self.read_table2()

            self.show_empty_table2()
            self.get_data_from_db_table2()
            self.update_table2()
            self.read_table2()
            self.lineEdit_3.setText("")
            self.lineEdit_2.setText("")
            self.lineEdit.setText("")
        else:
            # todo добавить сообщение
            pass

    def process_table(self):
        self.read_table1()
        self.read_table2()
        self.get_data_from_db_table1()
        self.update_table1()
        self.get_data_from_db_table2()
        self.update_table2()

    def read_table1(self):
        t1_row = self.tableWidget.rowCount()
        t1_col = self.tableWidget.columnCount()
        try:
            for row in range(t1_row):
                for col in range(t1_col):
                    item = self.tableWidget.item(row, col).text() if self.tableWidget.item(row, col) is not None else ""
                    if self.table1[row][col] != item:
                        self.table1[row][col] = item

            logging.info("Таблица расписания сохраняется в базу данных...")
            self.save_table1_to_db()
        except Exception as e:
            logging.error("Ошибка при чтении таблицы расписания из интерфейса")

    def read_table2(self):
        try:
            print("read_table2, ", self.tableWidget_2.rowCount())
            for row in range(self.tableWidget_2.rowCount()):
                for col in range(7):
                    item = self.tableWidget_2.item(row, col).text() \
                        if self.tableWidget_2.item(row,col) is not None else ""
                    if self.table2[row][col] != item:
                        self.table2[row][col] = item
            logging.info("Таблица успеваемости сохраняется в базу данных...")
            self.save_table2_to_db()
        except Exception as e:
            logging.error("Ошибка при чтении таблицы успеваемости из интерфейса")

    def save_table1_to_db(self):
        try:
            for row in range(len(self.table1)):
                for col in range(len(self.table1[0])):
                    self.cursor.execute(
                        f"SELECT item FROM timetable WHERE week_numder={int(self.actual_week)} AND day_of_week={int(col)} AND lesson_number={int(row)};")
                    a = self.cursor.fetchall()  # [] [("hello",)]
                    if len(a) == 0:
                        self.cursor.execute(
                            f"INSERT INTO timetable(week_numder, day_of_week, lesson_number, item) VALUES ({int(self.actual_week)}, {int(col)},{int(row)}, '{self.table1[row][col]}');")
                    else:
                        self.cursor.execute(
                            f"UPDATE timetable SET item='{self.table1[row][col]}' WHERE week_numder={int(self.actual_week)} AND day_of_week={int(col)} AND lesson_number={int(row)};")
                    self.dbase.commit()
            logging.info("Таблица расписания успешно сохранена в базу данных")
        except Exception as e:
            logging.error(f"Ошибка при сохранении в БД таблицы расписания: {e}")

    def save_table2_to_db(self):
        try:
            for row in range(self.tableWidget_2.rowCount()):
                for col in range(len(self.table2[0])):
                    self.cursor.execute(
                        f"select mark from progress join students s on progress.id_student = s.id_student where week_numder={int(self.actual_week)} and day_of_week = {int(col)} and full_name = '{self.tableWidget_2.verticalHeaderItem(int(row)).text()}';")
                    a = self.cursor.fetchall()  # [] [("hello",)]
                    if len(a) == 0:
                        self.cursor.execute(
                            f"INSERT INTO progress(week_numder, day_of_week, id_student, mark)  VALUES ({int(self.actual_week)}, {int(col)}, (select id_student from students where students.full_name='{self.tableWidget_2.verticalHeaderItem(int(row)).text()}'), '{self.table2[row][col]}');")
                    else:
                        self.cursor.execute(
                            f"UPDATE progress SET mark='{self.table2[row][col]}' WHERE week_numder={int(self.actual_week)} AND day_of_week={int(col)} AND id_student= (select id_student from students where students.full_name='{self.tableWidget_2.verticalHeaderItem(int(row)).text()}');")
                    self.dbase.commit()
                logging.info("Таблица успеваемости успешно сохранена в базу данных")
        except Exception as e:
            logging.error(f"Ошибка при сохранении в БД таблицы успеваемости: {e}")

    def get_data_from_db_table1(self):
        try:
            self.cursor.execute(
                f"SELECT day_of_week, lesson_number, item FROM timetable WHERE week_numder={int(self.actual_week)};")
            res = self.cursor.fetchall()  # [(0,0,""), (0,0,""), (3,0,"география")] - day_of_week, lesson_number, item
            if len(res) == 0:
                for i in range(len(self.table1)):
                    for j in range(len(self.table1[i])):
                        self.table1[i][j] = ""
            else:
                for row in res:
                    self.table1[int(row[1])][int(row[0])] = row[2]
        except Exception as e:
            print(e)

    def get_data_from_db_table2(self):
        try:
            self.cursor.execute(
                f"select students.full_name, day_of_week, mark from progress join students on students.id_student=progress.id_student WHERE week_numder={int(self.actual_week)} order by students.full_name;")
            res = self.cursor.fetchall()

            if len(res) != 0:
                row = 0
                for i in range(0, len(res)):
                    if i % 7 == 0 and i != 0:
                        row += 1
                    self.table2[row][res[i][1]] = res[i][2]
            else:
                print(self.tableWidget_2.rowCount())
                for row in range(self.tableWidget_2.rowCount()):
                    for col in range(7):
                        self.table2[row][col] = ""
            for i in self.table2:
                print(i)
        except Exception as e:
            logging.error(f"Ошибка при загрузке из БД таблицы успеваемости: {e}")

    def update_table2(self):
        for i in range(self.tableWidget_2.rowCount()):
            for j in range(7):
                self.tableWidget_2.setItem(i, j, QtWidgets.QTableWidgetItem(self.table2[i][j]))
        self.show_marks_and_n()

    def show_marks_and_n(self):
        try:
            self.cursor.execute(f"select id_student, full_name from students order by full_name;")
            stud_list = self.cursor.fetchall() # [(1, "ФИО"), (2,"фио2"), ]
            # print(stud_list)
            row_num = 0
            for t in stud_list:
                self.cursor.execute(f"select mark from progress where id_student={i[0]};")
                res = self.cursor.fetchall() #[("2",)("5",), ] or []
                # print(res)
                if len(res) != 0:
                    marks = [int(i[0]) for i in res if (i[0].isdigit() and int(i[0]) in [1,2,3,4,5])]
                    nk = len([i[0] for i in res if i[0] in ["N", "n", "Н", "н"]])
                    # print(marks)
                    # print(nk)
                    if len(marks) != 0:
                        self.tableWidget_2.setItem(row_num, 7,
                                                   QtWidgets.QTableWidgetItem(str(round(sum(marks) / len(marks), 2))))
                    self.tableWidget_2.setItem(row_num, 8, QtWidgets.QTableWidgetItem(str(nk)))
                    row_num += 1
        except Exception as e:
            logging.error(f"Ошибка при загрузке из БД таблицы успеваемости: {e}")

    def update_table1(self):
        for row in range(len(self.table1)):
            for col in range(len(self.table1[0])):
                self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(self.table1[row][col]))
        print("updated")

    def show_empty_table2(self):
        x = self.tableWidget_2.rowCount()
        for i in range(x):
            self.tableWidget_2.removeRow(0)
        self.cursor.execute(f"SELECT full_name FROM students ORDER BY full_name;")
        res = self.cursor.fetchall() # [("ФИО",), ("ФИО",) , ...]
        for i in range(len(res)):
            if len(self.table2) < len(res):
                self.table2.append(["" for i in range(7)])
            self.tableWidget_2.insertRow(i)
            self.tableWidget_2.setVerticalHeaderItem(i, QtWidgets.QTableWidgetItem(res[i][0]))

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Закрытие программы', 'Закрыть программу?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.Yes)

        if reply == QtWidgets.QMessageBox.Yes:
            self.read_table1()
            self.read_table2()
            event.accept()
            logging.info("Программа закрыта")
        else:
            event.ignore()


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('loginui.ui', self)
        self.username = None
        self.entrance_button.pressed.connect(self.button_entr_pushed)
        logging.info("Открыто окно входа")

    def open_main_window(self):
        global main_window
        main_window = MainWindow(self.username)
        main_window.show()

    def button_entr_pushed(self):
        self.username = self.login_line_edit.text()
        if self.username != "" and len(self.username) > 1:
            if show_dialog("Добро пожаловать, " + str(self.username) + "!", "Greeting"):
                self.open_main_window()
                self.close()
                logging.info(f"Пользователь {self.username} вошел в приложение")
        else:
            self.label_login_err.setText("Неверное имя пользователя")
            self.login_line_edit.setText("")


def show_dialog(message: str, title: str):
    dialog = QtWidgets.QMessageBox()
    dialog.setWindowTitle(str(title))
    dialog.setText(str(message))
    button = dialog.exec()
    if button == QtWidgets.QMessageBox.Ok:
        return True


app = QtWidgets.QApplication([])
main_window = None
window = LoginWindow()
# window = MainWindow("")
window.show()
app.exec_()
