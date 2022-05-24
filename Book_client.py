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
from email.mime.text import MIMEText # 이메일 전송을 위한 라이브러리 import

BUF_SIZE = 1024
IP= "127.0.0.1"
Port = 2091
check_msg=""


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
        id = self.id_Edit.text()
        pw = self.pw_Edit.text()
        lo = id +"/"+pw
        
        sock.send(lo.encode())

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
        self.email_Btn.clicked.connect(self.send_email)
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
    def send_email(self):
        #이메일 체크
        global check_msg
        email = self.email_Edit.text()
        check = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        
        if check.match(email) != None:
            ses = smtplib.SMTP('smtp.gmail.com', 587) # smtp 세션 설정
            ses.starttls()
            ses.login('saverock1235@gmail.com', "ohjo tynp pojs xjcx") # 이메일을 보낼 gmail 계정에 접속
            
            check_msg = str(random.randrange(1000, 10000))
            msg = MIMEText('인증번호: '+check_msg) # 보낼 메세지 내용을 적는다
            msg['subject'] = '의혀닝책방에서 인증코드를 발송했습니다.' # 보낼 이메일의 제목을 적는다
            ses.sendmail("saverock1235@gmail.com", email, msg.as_string()) # 앞에는 위에서 설정한 계정, 두번째에는 이메일을 보낼 계정을 입력

            ses.quit() # 세선종료  
                 
        self.emailnum_Edit.setEnabled(True)
        self.email_C_Btn.setEnabled(True)
    def check_E_num(self):
        check_num = self.emailnum_Edit.text()
        if check_num == check_msg:
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