import socket
import threading
import sqlite3

PORT = 2090
BUF_SIZE = 1024
lock = threading.Lock()
clnt_imfor = []  # [[소켓, id]]
clnt_cnt = 0


def dbcon():
    con = sqlite3.connect('Book.db')  # DB 연결
    c = con.cursor()                  # 커서
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
            clnt_msg = clnt_msg.replace('login/', '')       #clnt_msg에서 login/ 자름
            log_in(clnt_sock, clnt_msg, clnt_num)
        elif clnt_msg.startswith('find_id/'):
            clnt_msg = clnt_msg.replace('find_id/', '')
            find_id(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('find_pw/'):
            clnt_msg = clnt_msg.replace('find_pw/', '')
            find_pw(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('search'):
            clnt_msg = clnt_msg.replace('search', '')
            search(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('donate/'):
            clnt_msg = clnt_msg.replace('donate/', '')
            donation(clnt_sock, clnt_msg)
        elif clnt_msg.startswith('return'):
            clnt_msg = clnt_msg.replace('return', '')
            return_book(clnt_sock, clnt_msg)
        else:
            continue


def sign_up(clnt_sock, clnt_num):
    con, c = dbcon()
    check = 0
    user_data = []

    while True:
        check = 0
        imfor = clnt_sock.recv(BUF_SIZE)
        imfor = imfor.decode()
        if imfor == "Q_reg":      # 회원가입 창 닫을 때 함수 종료
            con.close()
            break
        c.execute("SELECT id FROM Users")  # Users 테이블에서 id 컬럼 추출

        for row in c:  # id 컬럼
            if imfor in row:       # 클라이언트가 입력한 id가 DB에 있으면
                clnt_sock.send('!NO'.encode())
                print("중복확인")
                check = 1
                break
        if check == 1:
            continue
        clnt_sock.send('!OK'.encode()) # 중복된 id 없으면 !OK 전송
        
        lock.acquire()

        user_data.append(imfor)  #user_data에 id 추가
        imfor = clnt_sock.recv(BUF_SIZE)  # password/name/email
        imfor = imfor.decode()
        if imfor == "Q_reg":  # 회원가입 창 닫을 때 함수 종료
            con.close()
            break
        print(imfor)
        imfor = imfor.split('/')  # 구분자 /로 잘라서 리스트 생성
        for i in range(3):
            user_data.append(imfor[i])       # user_data 리스트에 추가
        query = "INSERT INTO Users(id, password, name, email) VALUES(?, ?, ?, ?)"
        c.executemany(query, (user_data,))  # DB에 user_data 추가
        con.commit()            # DB에 커밋
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
        con.close()
        return

    if (data[1],) == user_pw:
        # 로그인성공 시그널
        c.execute("SELECT * FROM Users where id=?", (user_id,))
        row = c.fetchone()
        row = list(row)
        for i in range(0, len(row)):     # None인 항목 찾기
            if row[i] == None:
                row[i] = 'X'             # None을 X로 바꾸기
        row = '/'.join(row)              # row 리스트 원소 /넣어서 문자열로 합치기
        clnt_sock.send(('!OK/' + row).encode()) # 회원정보 전송
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
       
    c.execute("SELECT id FROM Users where email=?", (email,)) # DB에 있는 email과 일치시 id 가져오기
    id = c.fetchone()
    id = ''.join(id)       #문자열로 바꾸기

    if id == None:      # DB에 없는 email이면 None이므로 !NO 전송
        clnt_sock.send('!NO'.encode())
        print('fail')
        con.close()
        return
    else:              
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == "Q_id_Find":    # Q_id_Find 전송받으면 find_id 함수 종료
            pass
        elif msg == 'plz_id':     # plz_id 전송받으면 id 전송
            clnt_sock.send(id.encode())
            print('sendid')
        con.close()
        return


def find_pw(clnt_sock, id):
    con, c = dbcon()
    c.execute("SELECT password, email FROM Users where id=?", (id,))    # DB에 있는 id와 일치하면 비밀번호, 이메일 정보 가져오기
    row = c.fetchone()
    print(row)
    if row == None:                      # DB에 없는 id면 None
        clnt_sock.send('!NO'.encode())
        print('iderror')
        con.close()
        return

    clnt_sock.send('!OK'.encode())       # DB에 id 있으면 !OK 전송
    email = clnt_sock.recv(BUF_SIZE)
    email = email.decode()
    if email == "Q_pw_Find":             # Q_pw_Find 전송받으면 find_pw 함수 종료
        con.close()
        return

    if row[1] == email:                   # 전송받은 email변수 값이 DB에 있는 email과 같으면 
        clnt_sock.send('!OK'.encode())
        msg = clnt_sock.recv(BUF_SIZE)
        msg = msg.decode()
        if msg == "Q_pw_Find":
            pass
        elif msg == 'plz_pw':             # plz_pw 전송받으면 
            pw = ''.join(row[0])          # 비밀번호 문자열로 변환
            clnt_sock.send(pw.encode())   
            print('sendpw')
    con.close() 
    return


def search(clnt_sock, msg):
    con, c = dbcon()
    if msg.startswith('BN'):
        msg = msg.replace('BN', '')

        arg = '%' + msg + '%'
        c.execute("SELECT code, name, writer FROM Books WHERE rental = 0 AND name LIKE ?", (arg, )) # DB에 있는 책이름 찾아서 저자와 대출정보 가져오기
        rows = c.fetchall()

        for row in rows:
            #책 정보 보내기
            row = '/'.join(row)   
            print(row)
            clnt_sock.send(row.encode())   # name, writer
        clnt_sock.send('search_done'.encode())
        con.close()
        return

    elif msg.startswith('WN'):
        msg = msg.replace('WN', '')
        #저자명 검색 후 전달

        arg = '%' + msg + '%'
        c.execute("SELECT code, name, writer FROM Books WHERE rental = 0 AND writer LIKE ?", (arg, )) # DB에 있는 저자 이름 찾아서 책이름,대출정보 가져오기
        rows = c.fetchall()

        for row in rows:
            #책 정보 보내기
            row = '/'.join(row)   
            print(row)
            clnt_sock.send(row.encode())  
        clnt_sock.send('search_done'.encode())
        con.close()
        return
    else:
        con.close()
        return


def return_book(clnt_sock, msg):
    con, c = dbcon()
    check = 0
    if msg.startswith('BN'):
        msg = msg.replace('BN', '') # id랑 책 이름 받아와야함
        # msg에서 id, name 자르기
        c.execute("SELECT book1, book2, book3 FROM Users WHERE id=?", (id,))
        row = c.fetchone()
        for i in range(1, 4):
            if name in row[i-1]:
                book = "book" + str(i)
                query = "UPDATE Users SET %s = NULL WHERE id=?" % book
                c.execute("UPDATE Books SET rental = 0 WHERE name=?", (name,))
                c.execute(query, (id,))
                check = 1
        
    elif msg.startswith('CD'):
        msg = msg.replace('CD', '')
        # msg에서 id, book_code 자르기
        c.execute("SELECT book1, book2, book3 FROM Users WHERE id=?", (id,))
        row = c.fetchone()
        for i in range(1, 4):
            if book_code in row[i-1]:
                book = "book"  + str(i)
                query = "UPDATE Users SET %s = NULL WHERE id=?" % book
                c.execute("UPDATE Books SET rental =  0 WHERE code=?", (book_code,))
                c.execute(query, (id,))
                check = 1

    if check == 0:
        clnt_sock.send('!NO'.encode()) # 대출목록에 없는 도서명/도서코드
    else:
        clnt_sock.send('!OK'.encode()) # 반납완료
    con.commit()  
    con.close()
    return



def donation(clnt_sock, msg):
    con, c = dbcon()
    msg = msg.split('/')
    print(msg) # 확인
    c.executemany("INSERT INTO Books(name, writer) VALUES(?, ?)", (msg,))  # DB에 기증한 책 추가
    con.commit()            # DB에 커밋
    con.close()


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