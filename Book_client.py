import sys
import socket

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import QCoreApplication

BUF_SIZE = 1024
IP= "127.0.0.1"
Port = 2091
a="3"
b="4"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP, Port))

class Login(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Login.ui",self)

        #버튼 누를시 작동되는것들
        self.join_Btn.clicked.connect(self.join)
        self.pw_Edit.returnPressed.connect(self.try_login)
    
    def try_login(self):
        print("로그인시도")

    def join(self):
        sock.send("signup".encode())
        #새로운 UI 열기
        reg_window = reg()
        reg_window.exec_()

class reg(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("register.ui", self)

        #버튼 이벤트들
        self.id_Btn.clicked.connect(self.check_id)
        self.pw_Btn.clicked.connect(self.check_pw)
        self.email_Btn.clicked.connect(self.check_email)
        self.email_C_Btn.clicked.connect(self.check_E_num)
        self.join_Btn.clicked.connect(self.join)

    def check_id(self):
        id=self.id_Edit.text()#텍스트창에 있는걸 id라는 변수에 집어넣는다
        sock.send(id.encode())
        
        while True:
            ck = sock.recv(BUF_SIZE)
            ck = ck.decode()
            if sys.getsizeof(ck) >= 1:
                break
        if ck == "!OK" :
            #아이디 중복확인이 완료했을시 입력칸 잠금해제
            self.pw_Edit.setEnabled(True)
            self.repw_Edit.setEnabled(True)
            self.pw_Btn.setEnabled(True)
    def check_pw(self):
        a=self.pw_Edit.text()
        b=self.repw_Edit.text()
        if a == b:
            #비밀번호 확인이 완료했을시 입력칸 잠금해제
            self.name_Edit.setEnabled(True)
            self.email_Edit.setEnabled(True)
            self.email_Btn.setEnabled(True)
    def check_email(self):
        #이메일 체크
        self.emailnum_Edit.setEnabled(True)
        self.email_C_Btn.setEnabled(True)
    def check_E_num(self):
        self.join_Btn.setEnabled(True)
    def join(self):
        #텍스트창에 있는걸 변수에 집어넣는다
        pw=self.pw_Edit.text()
        name=self.name_Edit.text()
        email=self.email_Edit.text()
        #msg에 합쳐서 전송한다
        msg=pw+"/"+name+"/"+email
        sock.send(msg.encode())
        print(msg)
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_window = Login()
    chat_window.show()
    app.exec_()