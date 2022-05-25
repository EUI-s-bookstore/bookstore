import socket
import threading
import sqlite3

PORT = 2090
BUF_SIZE = 1024
lock = threading.Lock()
clnt_imfor = []  # [[소켓, id]]
clnt_cnt = 0


def dbcon():
    con = sqlite3.connect('Book.db')
    c = con.cursor()
    return (con, c)


def handle_clnt(clnt_sock):
    for i in range(0, clnt_cnt):
        if clnt_imfor[i][0] == clnt_sock:
            clnt_num = i
            break

    while True:
        clnt_msg = clnt_sock.recv(BUF_SIZE)
        if not clnt_msg:
            lock.acquire()
            delete_imfor(clnt_sock)
            lock.release()
            break
        clnt_msg = clnt_msg.decode()
        
        print(clnt_msg)

        if 'signup' == clnt_msg:
            sign_up(clnt_sock, clnt_num)
        elif clnt_msg.startwith('login'):
            clnt_msg = clnt_msg.replace('login', '')
            print(clnt_msg)
            log_in(clnt_sock, clnt_msg)
        else:
            continue

def sign_up(clnt_sock, clnt_num):
    con, db = dbcon()
    check = 0
    user_data = []

    while True:
        check = 0
        imfor = clnt_sock.recv(BUF_SIZE)
        imfor = imfor.decode()
        db.execute("SELECT id FROM Users") # Users 테이블에서 id 컬럼 추출
        

        for row in db: # id 컬럼
            if imfor in row:       # 클라이언트가 입력한 id가 DB에 있으면
                clnt_sock.send('!NO'.encode())
                print("중복확인")
                check = 1
                break
        if check == 1:
            continue
        clnt_sock.send('!OK'.encode())

        lock.acquire()

        user_data.append(imfor)
        imfor = clnt_sock.recv(BUF_SIZE)  # password/name/email
        imfor = imfor.decode()
        imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
        for i in range(3):
            user_data.append(imfor[i])       # user_data 리스트에 추가
        query = "INSERT INTO Users(id, password, name, email) VALUES(?, ?, ?, ?)"
        db.executemany(query, (user_data,))  # DB에 user_data 추가
        con.commit()
        con.close
        lock.release()
        break


def log_in(clnt_sock, data):
    print('hi')
    con, c = dbcon()

    while True:
        data = data.split('/')
        user_id = data[0]
        c.execute("SELECT password FROM Users where id=?", user_id)  # DB에서 id 같은 password 컬럼 선택
        user_pw = c.fetchone()             # 한 행 추출
        print(user_pw)

        if user_pw is None:  # DB에 없는 id 입력시
            clnt_sock.send('iderror')
            print('iderror')
            continue

        if data[1] == user_pw:
            # 로그인성공 시그널
            # clnt_sock.send('OK'.encode())
            print("login sucess")
            break
        else:
            # 로그인실패 시그널
            # clnt_sock.send('NO'.encode())
            print("login failure")
            continue


# def find_id(clnt_sock):
#     while True:
#         imfor = clnt_sock.recv(BUF_SIZE)  # name/email
#         imfor = imfor.split('/')
#         user_name = imfor[0]
#         c.execute("SELECT id, email FROM Users where name=?", user_name)
#         row = c.fetchone()

#         if row == NULL:
#             continue

#         user_id = row[0]
#         user_email = row[1]
#         if imfor[1] == user_email:
#             # id 보내기(메일로?)
#             # clnt_sock.send(user_id.encode())
#             break
#         else:
#             # 정보일치x
#             continue

'''
def find_pw(clnt_sock):
    while True:
        imfor = clnt_sock.recv(BUF_SIZE)  # id/name/email
        imfor = imfor.split('/')
        user_id = imfor[0]
        c.execute("SELECT password, name, email FROM Users where id=?", user_id)
        row = c.fetchone()
        user_name = row[1]
        user_email = row[2]
        if imfor[1] == user_name:
            if imfor[2] == user_email:
                # password 보내기
                # clnt_sock.send(user_email.encode())
                break
            else:
                # 정보일치x
                continue
        else:
            # 정보일치x
            continue
        '''


def delete_imfor(clnt_sock):
    global clnt_cnt
    for i in range(0, clnt_cnt):
        if clnt_sock == clnt_imfor[i][0]:
            print('exit client')
            while i < clnt_cnt - 1:
                clnt_imfor[i] = clnt_imfor[i + 1]
                i += 1
            break
    clnt_cnt -= 1


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()

        lock.acquire()

        clnt_imfor.insert(clnt_cnt, [clnt_sock])
        clnt_cnt += 1
        print(clnt_sock)
        lock.release()

        t = threading.Thread(target=handle_clnt, args=(clnt_sock,))
        t.start()