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
        elif clnt_msg.startswith('login/'):
            clnt_msg = clnt_msg.replace('login/', '')
            log_in(clnt_sock, clnt_msg, clnt_num)
        elif clnt_msg.startswith('find_id/'):
            clnt_msg = clnt_msg.replace('find_id/', '')
            find_id(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('find_pw/'):
            clnt_msg = clnt_msg.replace('find_pw/', '')
            find_pw(clnt_sock, clnt_msg)
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
        db.execute("SELECT id FROM Users")  # Users 테이블에서 id 컬럼 추출

        for row in db:  # id 컬럼
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
        print(imfor)
        imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
        for i in range(3):
            user_data.append(imfor[i])       # user_data 리스트에 추가
        query = "INSERT INTO Users(id, password, name, email) VALUES(?, ?, ?, ?)"
        db.executemany(query, (user_data,))  # DB에 user_data 추가
        con.commit()
        con.close()
        lock.release()
        break


def log_in(clnt_sock, data, num):
    con, c = dbcon()

    data = data.split('/')
    user_id = data[0]
    c.execute("SELECT password FROM Users where id=?", (user_id,))  # DB에서 id 같은 password 컬럼 선택
    user_pw = c.fetchone()             # 한 행 추출

    if user_pw == None:  # DB에 없는 id 입력시
        clnt_sock.send('iderror'.encode())
        con.close
        return

    if (data[1],) == user_pw:
        # 로그인성공 시그널
        c.execute("SELECT * FROM Users where id=?", (user_id,))
        row = c.fetchone()
        print(row)
        clnt_sock.send('!OK'.encode())
        print("login sucess")
        clnt_imfor[num].append(data[0])
    else:
        # 로그인실패 시그널
        clnt_sock.send('!NO'.encode())
        print("login failure")

    con.close()
    return   


def find_id(clnt_sock, email):
    con, c = dbcon()
       
    c.execute("SELECT id FROM Users where email=?", (email,))
    id = c.fetchone()
    id = ''.join(id)

    if id == None:
        clnt_sock.send('!NO'.encode())
        print('fail')
        con.close()
        return
    else:
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == 'plz_id':
            clnt_sock.send(id.encode())
            print('sendid')
        con.close()
        return


def find_pw(clnt_sock, id):
    con, c = dbcon()
    c.execute("SELECT password, email FROM Users where id=?", (id,))
    row = c.fetchone()
    print(row)
    if row == None:
        clnt_sock.send('!NO'.encode())
        print('iderror')
        con.close()
        return

    clnt_sock.send('!OK'.encode())              #DB에 id 있으면 !OK 전송
    email = clnt_sock.recv(BUF_SIZE)
    email = email.decode()

    if row[1] == email:
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == 'plz_pw':
            pw = ''.join(row[1])
            clnt_sock.send(pw.encode())
            print('sendpw')
    con.close() 
    return

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