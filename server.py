import socket
import threading
import sqlite3

PORT = 2090
BUF_SIZE = 1024
lock = threading.Lock()
clnt_imfor = []
clnt_cnt = 0

con = sqlite3.connect('Book.db')

c = con.cursor()

def handle_clnt(clnt_sock):
    for i in range(0, clnt_cnt):
        if clnt_imfor[i][1] == clnt_sock:
            clnt_num = i
            break

        while True:
            clnt_msg = clnt_sock.recv(BUF_SIZE)

            if not clnt_msg:
                lock.acquire()
                delete_imfor(clnt_sock)
                lock.release()
                break

            clnt_msg = clnt_msg.encode()

            if 'signup' in clnt_msg:
                sign_up(clnt_sock)


def sign_up(clnt_sock):
    check = 0
    user_data = []
    while True:
        imfor = clnt_sock.recv(BUF_SIZE)
        imfor = imfor.decode("UTF–8")

        c.execute("SELECT id FROM Users")
        for row in c.fetchall():
            if row == imfor:
                clnt_sock.send('NO'.encode())
                check = 1
                break
        if check == 1:
            continue
        clnt_sock.send('OK'.encode())
        user_data.append(imfor)
        print(user_data)
        imfor = clnt_sock.recv(BUF_SIZE) # password/name/email

        user_data.append(imfor.split('/'))       # 구분자 /로 잘라서 리스트 생성
        print(user_data)
        query = "insert into Users values (:id, :password, :name, :email)"
        c.executemany(query, user_data)
        con.commit()

    

def delete_imfor(clnt_sock):
    global clnt_cnt
    for i in range(0, clnt_cnt):
        if clnt_sock == clnt_imfor[i][1]:
            print("%s님께서 접속 종료하셨습니다." %clnt_imfor[i][0])
            while i < clnt_cnt - 1:
                # clnt_imfor[i][0] = clnt_imfor[i + 1][0]
                # clnt_imfor[i][1] = clnt_imfor[i + 1][1]
                # clnt_imfor[i][2] = clnt_imfor[i + 1][2]
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

        lock.release()

        t = threading.Thread(target=handle_clnt, args=(clnt_sock,))
        t.start()

