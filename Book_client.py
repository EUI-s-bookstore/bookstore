import sys
import socket
import smtplib
import re
import random

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication
from email.mime.text import MIMEText  # 이메일 전송을 위한 라이브러리 import

BUF_SIZE = 1024
IP = "127.0.0.1"
Port = 2090
check_msg = ""
user = ""
shopping_Cart = []
rent = []
search_mode = 'BN'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP, Port))


def send_email_to_clnt(self):  # 이메일 체크 시작
    global check_msg
    email = self.email_Edit.text()
    check = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    if check.match(email) != None:
        ses = smtplib.SMTP('smtp.gmail.com', 587)  # smtp 세션 설정
        ses.starttls()
        # 이메일을 보낼 gmail 계정에 접속
        ses.login('uihyeon.bookstore@gmail.com', 'ttqe mztd lljo tguh')

        check_msg = str(random.randrange(1000, 10000))
        msg = MIMEText('인증번호: '+check_msg)  # 보낼 메세지 내용을 적는다
        msg['subject'] = '의혀닝책방에서 인증코드를 발송했습니다.'  # 보낼 이메일의 제목을 적는다
        # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력
        ses.sendmail('uihyeon.bookstore@gmail.com', email, msg.as_string())
        result_value = "success"
    else:
        QMessageBox().about(self, "error", "이메일 형식이 아닙니다.\n다시 시도해주세요.")
        result_value = "fail"

    ses.quit()  # 이메일 체크 종료
    return result_value
# 이메일 체크 종료


def check_rcv():  # 서버에서 받아오기
    while True:
        ck = sock.recv(BUF_SIZE)
        ck = ck.decode()
        if sys.getsizeof(ck) >= 1:
            break
    return ck
# 받아오기 종료


def Window_move(self, window_name):
    if window_name == "home":
        window = Main_Window()
    elif window_name == "search":
        window = search_Window()
    elif window_name == "shopping":
        window = shopping_Window()
    elif window_name == "return":
        window = return_Window()
    elif window_name == "donate":
        window = donate_Window()
    elif window_name == "user":
        window = user_Window()

    self.close()
    window.exec_()


class Login(QDialog):  # 로그인창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("login.ui", self)

        # 버튼 누를시 작동되는것들
        self.login_Btn.clicked.connect(self.try_login)
        self.id_Find.clicked.connect(self.find_id)
        self.pw_Find.clicked.connect(self.find_pw)
        self.join_Btn.clicked.connect(self.join)
        self.pw_Edit.returnPressed.connect(self.try_login)

    def try_login(self):
        global user, rent
        id = self.id_Edit.text()
        pw = self.pw_Edit.text()
        lo = "login/" + id + "/"+pw
        sock.send(lo.encode())
        ck = check_rcv()
        user = ck.split("/")
        if user[0] == "!OK":
            i = 5
            while i == 7:
                if user[i] != 'X':
                    rent = rent.append(user[i])
                i = i+1
            # 메인화면 열기
            m_window = Main_Window()
            self.close()
            m_window.exec_()
            # 로그인화면 종료
        else:
            QMessageBox().about(self, "error", "아이디 혹은 비밀번호가 틀렸습니다.\n다시 시도해주세요.")

    def join(self):
        sock.send("signup".encode())
        # 새로운 UI 열기
        reg_window = reg()
        reg_window.exec_()

    def find_id(self):
        id_find_window = ID_Find()
        id_find_window.exec_()

    def find_pw(self):
        pw_find_window = PW_Find()
        pw_find_window.exec_()
# 로그인창 종료


class ID_Find(QDialog):  # 아이디찾기 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("find_id.ui", self)

        self.email_Btn.clicked.connect(self.check_email)
        self.email_C_Btn.clicked.connect(self.check_code)
        self.join_Btn.clicked.connect(self.end)

    def check_email(self):
        e_mail = self.email_Edit.text()
        e_mail = "find_id/"+e_mail
        sock.send(e_mail.encode())
        ck = check_rcv()
        if ck == "!OK":  # 아이디 중복확인이 완료했을시 입력칸 잠금해제
            func_result = send_email_to_clnt(self)
            if func_result == "success":
                self.emailnum_Edit.setEnabled(True)
                self.email_C_Btn.setEnabled(True)

    def check_code(self):
        ck_code = self.emailnum_Edit.text()
        if ck_code == check_msg:
            self.join_Btn.setEnable(True)

    def end(self):
        sock.send("plz_id".encode())
        ck = check_rcv()
        # 아이디를 이메일로 보내주고 종료
        self.close()

    def closeEvent(self, event):
        sock.send("Q_id_Find".encode())
# 아이디찾기 종료


class PW_Find(QDialog):  # 비밀번호찾기 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("find_pw.ui", self)

        self.id_Btn.clicked.connect(self.check_id)
        self.email_Btn.clicked.connect(self.send_email)
        self.email_C_Btn.clicked.connect(self.check_E_num)
        self.join_Btn.clicked.connect(self.end)

    def check_id(self):
        id = self.id_Edit.text()  # 텍스트창에 있는걸 id 변수에 넣는다
        id = "find_pw/"+id
        sock.send(id.encode())
        ck = check_rcv()
        if ck == "!OK":  # 아이디 중복확인이 완료했을시 입력칸 잠금해제
            self.email_Edit.setEnabled(True)
            self.email_Btn.setEnabled(True)
        else:
            QMessageBox().about(self, "error", "존재하지 않는 아이디입니다.\n다시 시도해주세요.")

    def send_email(self):
        email = self.email_Edit.text()
        sock.send(email.encode())
        ck = check_rcv()
        if ck == "!OK":  # 아이디 중복확인이 완료했을시 입력칸 잠금해제
            func_result = send_email_to_clnt(self)
            if func_result == "success":
                self.emailnum_Edit.setEnabled(True)
                self.email_C_Btn.setEnabled(True)

    def check_E_num(self):
        check_num = self.emailnum_Edit.text()
        if check_num == check_msg:
            self.join_Btn.setEnabled(True)

    def end(self):
        sock.send("plz_pw".encode())
        ck = check_rcv()
        # 비밀번호를 이메일로 보내주고 종료
        self.close()

    def closeEvent(self, event):
        sock.send("Q_pw_Find".encode())
# 비밀번호찾기 종료


class reg(QDialog):  # 가입창 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("register.ui", self)

        # 버튼 이벤트들
        self.id_Btn.clicked.connect(self.check_id)
        self.pw_Btn.clicked.connect(self.check_pw)
        self.email_Btn.clicked.connect(self.send_email)
        self.email_C_Btn.clicked.connect(self.check_E_num)
        self.join_Btn.clicked.connect(self.join)

    def check_id(self):
        id = self.id_Edit.text()  # 텍스트창에 있는걸 id라는 변수에 집어넣는다
        sock.send(id.encode())
        ck = check_rcv()
        if ck == "!OK":  # 아이디 중복확인이 완료했을시 입력칸 잠금해제
            QMessageBox().information(self, "    ", "사용 가능한 아이디입니다.")
            self.pw_Edit.setEnabled(True)
            self.repw_Edit.setEnabled(True)
            self.pw_Btn.setEnabled(True)
        else:
            QMessageBox().about(self, "   ", "중복되는 아이디입니다.\n다시 시도해주세요.")

    def check_pw(self):
        a = self.pw_Edit.text()
        b = self.repw_Edit.text()
        if a == b:  # 비밀번호 확인이 완료했을시 입력칸 잠금해제
            QMessageBox().information(self, "    ", "비밀번호가 일치합니다.")
            self.name_Edit.setEnabled(True)
            self.email_Edit.setEnabled(True)
            self.email_Btn.setEnabled(True)
        else:
            QMessageBox().about(self, "    ", "비밀번호가 일치하지 않습니다.\n다시 시도해주세요.")

    def send_email(self):
        func_result = send_email_to_clnt(self)
        if func_result == "success":
            QMessageBox().information(self, "    ", "인증번호가 전송되었습니다.")
            self.emailnum_Edit.setEnabled(True)
            self.email_C_Btn.setEnabled(True)

    def check_E_num(self):
        check_num = self.emailnum_Edit.text()
        if check_num == check_msg:
            QMessageBox().information(self, "    ", "인증이 완료되었습니다.")
            self.join_Btn.setEnabled(True)
        else:
            QMessageBox().information(self, "    ", "인증번호가 일치하지않습니다.")

    def join(self):  # 텍스트창에 있는걸 변수에 집어넣는다
        pw = self.pw_Edit.text()
        name = self.name_Edit.text()
        email = self.email_Edit.text()
        msg = pw+"/"+name+"/"+email  # msg에 합쳐서 전송한다
        sock.send(msg.encode())
        self.close()

    def closeEvent(self, event):
        sock.send("Q_reg".encode())
# 가입창 종료


class Main_Window(QDialog):  # 메인화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("main.ui", self)

        print(user)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))
# 메인화면 종료


class search_Window(QDialog):  # 도서찾기화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("search.ui", self)

        self.book_check.setChecked(True)
        self.writer_check.setChecked(False)  # 라디오 버튼 초기화
        self.book_check.clicked.connect(self.search_type_change)
        self.writer_check.clicked.connect(self.search_type_change)  # 라디오 버튼 제어

        self.search_Btn.clicked.connect(self.search_func)  # 검색 버튼 제어
        self.search_box.returnPressed.connect(self.search_func)

        self.search_add.clicked.connect(self.add_Cart)
        self.search_clear.clicked.connect(self.clear_Cart)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))

    def search_type_change(self):
        global search_mode
        if self.book_check.isChecked():
            search_mode = "BN"
        else:
            search_mode = "WN"

    def search_func(self):
        global search_mode

        search_text = self.search_box.text()
        search_msg = "search"+search_mode + search_text
        sock.send(search_msg.encode())
        self.search_list.clear()
        while True:
            rcv = sock.recv(BUF_SIZE)
            rcv = rcv.decode()
            if "search_done" in rcv:
                rcv = rcv.replace('search_done', '')
                print(rcv)
                self.search_list.addItem(rcv)
                break
            else:
                self.search_list.addItem(rcv)

    def add_Cart(self):
        global shopping_Cart
        select_item = self.search_list.currentItem().text()
        if select_item not in shopping_Cart:
            shopping_Cart.append(select_item)
            select_item = select_item.split('/')
            QMessageBox().information(
                self, "    ", "%s(을)를\n장바구니에 추가하였습니다." % select_item[1])

    def clear_Cart(self):
        self.search_list.clear()
# 도서찾기화면 종료


class shopping_Window(QDialog):  # 도서대여화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("shopping.ui", self)
        self.initUI()
        self.shopping_Btn.clicked.connect(self.send_rent)
        self.shopping_clear.clicked.connect(self.clear_rent)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))

    def initUI(self):
        for list in shopping_Cart:
            self.shopping_list.addItem(list)

    def send_rent(self):
        global rent, rent_cnt, shopping_Cart
        if len(rent) <= 2:
            if sys.getsizeof(shopping_Cart) >= 90:
                data = self.shopping_list.currentItem().text()
                rent.append(data)
                j = 0
                for i in shopping_Cart:
                    if data in i:
                        del shopping_Cart[j]  # 대여한 책 리스트에서 삭제
                    j = j+1
                self.shopping_list.clear()
                for list in shopping_Cart:
                    self.shopping_list.addItem(list)
                data = data.split('/')
                # 서버로 책 고유번호 전송
                sock.send(
                    ('rental' + data[0] + '|' + data[1] + '|' + data[2]).encode())
                QMessageBox().information(
                    self, "    ", "%s(을)를 빌렸습니다." % data[1])
            else:
                QMessageBox().information(self, "    ", "아무것도 선택하지 않았습니다.")
        else:
            QMessageBox().information(self, "    ", "최대 대여개수를 초과하였습니다.")

    def clear_rent(self):
        global shopping_Cart
        data = self.shopping_list.currentItem().text()
        j = 0
        for i in shopping_Cart:
            if data in i:
                del shopping_Cart[j]
            j = j+1
        self.shopping_list.clear()
        for list in shopping_Cart:
            self.shopping_list.addItem(list)
# 도서대여화면 종료


class return_Window(QDialog):  # 도서반납화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("return.ui", self)
        self.initUI()

        self.return_end.clicked.connect(self.return_book)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))

    def initUI(self):
        for list in rent:
            self.return_list.addItem(list)

    def return_book(self):
        global rent
        if sys.getsizeof(rent) >= 1:
            data = self.return_list.currentItem().text()
            j = 0
            for i in rent:
                if data in i:
                    del rent[j]
                j = j+1
            self.return_list.clear()
            for list in rent:
                self.return_list.addItem(list)
            data = data.split('/')
            sock.send(('return' + data[0]).encode())
            QMessageBox().information(
                self, "    ", "%s(을)를\n반납했습니다." % data[1])
        else:
            QMessageBox().information(self, "    ", "아무것도 선택하지 않았습니다.")
# 도서반납화면 종료


class donate_Window(QDialog):  # 도서기증화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("donation.ui", self)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))

        self.donation_Btn.clicked.connect(self.donate_books)

    def donate_books(self):
        books_name = self.book_name.text()
        writer_name = self.book_writer.text()
        donate_msg = "donate/"+books_name+"/"+writer_name
        sock.send(donate_msg.encode())
        self.book_name.clear()
        self.book_writer.clear()
# 도서기증화면 종료


class user_Window(QDialog):  # 나의정보화면 시작
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("user.ui", self)

        self.init_User()

        self.name_change.clicked.connect(self.change_name)
        self.pw_change.clicked.connect(self.change_pw)

        self.home_icon.clicked.connect(
            lambda: Window_move(self, "home"))  # 메뉴 버튼들 제어
        self.search_icon.clicked.connect(lambda: Window_move(self, "search"))
        self.shopping_icon.clicked.connect(
            lambda: Window_move(self, "shopping"))
        self.return_icon.clicked.connect(lambda:  Window_move(self, "return"))
        self.donation_icon.clicked.connect(lambda: Window_move(self, "donate"))
        self.user_icon.clicked.connect(lambda: Window_move(self, "user"))

    def init_User(self):
        self.user_name.setPlainText(user[1])
        self.user_name.setAlignment(QtCore.Qt.AlignCenter)  # 가운데 정렬
        for book in rent:
            self.rent_list.append(book)

    def change_name(self):
        print("아이디 변경")

    def change_pw(self):
        print('비번변경')

# 나의정보메뉴 종료


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_window = Login()
    #chat_window = Main_Window()
    chat_window.show()
    app.exec_()
