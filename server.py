import socket
import threading
import sqlite3
import datetime
from datetime import date
import sys

PORT = 2091
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
        sys.stdout.flush()
        clnt_msg = clnt_sock.recv(BUF_SIZE)

        if not clnt_msg:
            lock.acquire()
            delete_imfor(clnt_sock)
            lock.release()
            break
        clnt_msg = clnt_msg.decode()

        sys.stdin.flush()

        if 'signup' == clnt_msg:
            sign_up(clnt_sock, clnt_num)
        elif clnt_msg.startswith('login/'):
            clnt_msg = clnt_msg.replace('login/', '')  # clnt_msg에서 login/ 자름
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
        elif clnt_msg.startswith('rental'):
            clnt_msg = clnt_msg.replace('rental', '')
            rental(clnt_num, clnt_msg)
        elif clnt_msg.startswith('return'):
            clnt_msg = clnt_msg.replace('return', '')
            return_book(clnt_num, clnt_msg)
        elif clnt_msg.startswith('myinfo'):
            clnt_msg = clnt_msg.replace('myinfo', '')
            send_user_information(clnt_num)
        elif clnt_msg.startswith('reset'):
            clnt_msg = clnt_msg.replace('reset', '')
            reset(clnt_num, clnt_msg)
        elif clnt_msg.startswith('remove'):
            remove(clnt_num)
        else:
            continue


def reset(clnt_num, clnt_msg):
    print(clnt_msg)
    id = clnt_imfor[clnt_num][1]
    con, c = dbcon()
    if clnt_msg.startswith('_name/'):
        clnt_msg = clnt_msg.replace('_name/', '')
        lock.acquire()
        c.execute("UPDATE Users SET name = ? WHERE id = ?", (clnt_msg, id))
        con.commit()
        lock.release()
        con.close()
    elif clnt_msg.startswith('_pw/'):
        clnt_msg = clnt_msg.replace('_pw/', '')
        lock.acquire()
        c.execute("UPDATE Users SET password = ? WHERE id = ?", (clnt_msg, id))
        con.commit()
        lock.release()
        con.close()
    elif clnt_msg.starswith('_pp/'):
        clnt_msg = clnt_msg.replace('_pp/', '')
        lock.acquire()
        c.excute("UPDATE Users SET pp = ? WHERE id = ?", (clnt_msg, id))
        con.commit()
        lock.release()
        con.close()
    else:
        con.close()
        return


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
                check = 1
                break
        if check == 1:
            continue

        clnt_sock.send('!OK'.encode())  # 중복된 id 없으면 !OK 전송

        lock.acquire()
        user_data.append(imfor)  # user_data에 id 추가
        imfor = clnt_sock.recv(BUF_SIZE)  # password/name/email
        imfor = imfor.decode()
        if imfor == "Q_reg":  # 회원가입 창 닫을 때 함수 종료
            con.close()
            break

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

    c.execute("SELECT password FROM Users where id=?",
              (user_id,))  # DB에서 id 같은 password 컬럼 선택

    user_pw = c.fetchone()             # 한 행 추출

    if not user_pw:  # DB에 없는 id 입력시
        clnt_sock.send('iderror'.encode())
        con.close()
        return

    if (data[1],) == user_pw:
        # 로그인성공 시그널
        print("login sucess")
        clnt_imfor[num].append(data[0])
        c.execute("SELECT book1, book2, book3 FROM Users where id=?", (user_id,))
        books = c.fetchone()
        books = list(books)
        overdue(books[0], books[1], books[2], user_id)
        send_user_information(num)
    else:
        # 로그인실패 시그널
        clnt_sock.send('!NO'.encode())
        print("login failure")

    con.close()
    return


def remove(clnt_num):
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    lock.acquire()
    c.execute("DELETE FROM Users WHERE id = ?", (id,))
    c.execute("DELETE FROM Return WHERE id = ?", (id,))
    clnt_imfor[clnt_num].remove(id)
    con.commit()
    lock.release()
    con.close()


def overdue(book1, book2, book3, id):
    con, c = dbcon()
    today = date.today()  # 오늘 날짜
    list = [book1, book2, book3]  # 대여한 책 리스트
    cur = datetime.timedelta(days=7)  # 7일 datetime 타입

    for i in range(0, len(list)):
        if list[i] == None:
            con.close()
            return
        elif list[i].endswith('연체'):
            continue
        else:
            data = list[i].split('|')  # / 기준으로 잘라서 리스트 생성
            data[3] = data[3].replace('-', '')  # 날짜에서 - 없애기
            data[3] = datetime.datetime.strptime(
                data[3], '%Y%m%d').date()  # 문자열  datetime 타입으로 바꾸기
            result = today - data[3]  # 오늘 날짜에서 빌린 날짜 빼기
            if result > cur:          # 연체이면
                book_info = data[1] + '|연체'  # 도서코드/도서명 뒤에 '|연체' 붙이기
                book = "book" + str((i+1))
                lock.acquire()
                query = "UPDATE Users SET %s = ? WHERE id=?" % book
                c.execute(query, (book_info, id))  # '|연체' 추가한 내용으로 DB 수정
                con.commit()
                lock.release()
            else:         # 연체 아니면
                pass
    con.close()
    return


def send_user_information(clnt_num):
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    clnt_sock = clnt_imfor[clnt_num][0]
    books = []

    c.execute(
        "SELECT name, pp, book1, book2, book3, can_rental FROM Users where id=?", (id,))  # 이름, 대여한 책 찾기
    row = c.fetchone()
    row = list(row)
    for i in range(0, len(row)):     # None인 항목 찾기
        if row[i] == None:
            row[i] = 'X'

    c.execute("SELECT book_name FROM Return where id=?", (id,))  # 반납한 책
    while 1:
        book = c.fetchone()        # 반납한 책 한 권씩 찾기
        if book is None:
            break
        book = list(book)         # 리스트로 변환
        books = books + book      # books 리스트에 추가

    user_data = row + books  # 이름,대여한 책 + 반납한 책
    user_data = '/'.join(user_data)
    # 버퍼 비우기

    clnt_sock.send(('!OK/'+user_data).encode())
    con.close()


def find_id(clnt_sock, email):
    con, c = dbcon()

    c.execute("SELECT id FROM Users where email=?",
              (email,))  # DB에 있는 email과 일치시 id 가져오기
    id = c.fetchone()
    id = ''.join(id)  # 문자열로 바꾸기

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
            print('send_id')
        con.close()
        return


def find_pw(clnt_sock, id):
    con, c = dbcon()
    c.execute("SELECT password, email FROM Users where id=?",
              (id,))    # DB에 있는 id와 일치하면 비밀번호, 이메일 정보 가져오기
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
            print('send_pw')
        else:
            pass
    con.close()
    return


def search(clnt_sock, msg):
    con, c = dbcon()

    if msg.startswith('BN'):
        msg = msg.replace('BN', '')
        arg = '%' + msg + '%'
        # DB에 있는 책이름 찾아서 저자와 대출정보 가져오기
        c.execute(
            "SELECT code, name, writer FROM Books WHERE rental = 0 AND name LIKE ?", (arg, ))
        rows = c.fetchall()

        for row in rows:
            # 책 정보 보내기
            row = list(row)
            row[0] = str(row[0])
            row = '/'.join(row)
            clnt_sock.send(row.encode())   # name, writer

        clnt_sock.send('search_done'.encode())
        con.close()
        return
    elif msg.startswith('WN'):
        msg = msg.replace('WN', '')
        # 저자명 검색 후 전달

        arg = '%' + msg + '%'
        # DB에 있는 저자 이름 찾아서 책이름,대출정보 가져오기
        c.execute(
            "SELECT code, name, writer FROM Books WHERE rental = 0 AND writer LIKE ?", (arg, ))
        rows = c.fetchall()

        for row in rows:
            # 책 정보 보내기
            row = list(row)
            row[0] = str(row[0])
            row = '/'.join(row)
            clnt_sock.send(row.encode())

        clnt_sock.send('search_done'.encode())
        con.close()
        return
    else:
        con.close()
        return


def rental(clnt_num, msg):
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    clnt_sock = clnt_imfor[clnt_num][0]
    cur = 1
    rental_date = date.today()  # 오늘 날짜
    rental_date = rental_date.isoformat()  # 날짜 문자열로 바꾸기

    c.execute("SELECT book1, book2, book3 FROM Users WHERE id=?", (id, ))
    row = c.fetchone()
    row = list(row)
    print(row)
    divide_msg = msg.split('|')
    book_code = int(divide_msg[0])
    for i in range(0, 3):
        if row[i] == None:  # 대여한 책 없으면
            lock.acquire()
            c.execute("UPDATE Books SET rental=? WHERE code=?",
                      ('1', book_code,))  # Books 테이블에서 rental 값 1로 만들기
            data = 'book' + (str(cur))
            query = "UPDATE Users SET %s=? WHERE id=?" % data
            bookname_date = str(msg) + '|' + rental_date
            c.execute(query, (bookname_date, id))  # Users 테이블에 대여한 책이름/빌린날짜 추가
            # clnt_sock.send('!OK'.encode())
            con.commit()
            lock.release()
            con.close()
            return
        cur = cur + 1

    con.close()


def return_book(clnt_num, msg):
    con, c = dbcon()
    id = clnt_imfor[clnt_num][1]
    clnt_sock = clnt_imfor[clnt_num][0]
    check = 0
    book_code = int(msg)
    today = date.today()+datetime.timedelta(days=14) 
    today = today.isoformat()

    c.execute("SELECT book1, book2, book3 FROM Users WHERE id=?",
              (id,))  # 대여한 책 고유번호 찾기
    row = c.fetchone()
    row = list(row)

    for i in range(1, 4):  # 3번 반복
        if row[i-1] == None:  # 대여한 책 없을 때
            continue
        if row[i-1].startswith(str(book_code)):  # 고유번호로 시작할 때
            book_data = row[i-1].split('|')
            if book_data[4] == '연체':
                c.execute("UPDATE Users SET can_rental = ? WHERE id=?", (today, id))
                con.commit()
            book = "book" + str(i)
            lock.acquire()
            query = "UPDATE Users SET %s = NULL WHERE id=?" % book
            c.execute("UPDATE Books SET rental = '0' WHERE code=?",
                      (book_code,))  # Books에서 rental컬럼 0으로 바꾸기
            con.commit()
            # DB에서 대여한 책 있던 컬럼(book1,book2,book3) NULL로 비우기
            c.execute(query, (id,))
            con.commit()
            data = []  # 반납 DB에 넣을 data 리스트 생성
            data.append(id)  # data리스트에 id 추가
            c.execute("SELECT name FROM Books WHERE code=?",
                      (book_code,))  # book_code로 도서명 찾기
            name = c.fetchone()
            name = ''.join(name)  # 찾은 도서명 문자열로 바꾸기
            data.append(name)  # data리스트에 name 추가
            # 반납 DB에 data리스트 추가
            c.executemany(
                "INSERT INTO Return(id, book_name) VALUES (?, ?)", (data,))
            con.commit()
            lock.release()

    con.close()
    return


def donation(clnt_sock, msg):
    con, c = dbcon()
    msg = msg.replace('|', '')  # 클라이언트에서 | 보낸 것 없애기
    msg = msg.split('/')
    print(msg)  # 확인
    lock.acquire()
    c.executemany("INSERT INTO Books(name, writer) VALUES(?, ?)",
                  (msg,))  # DB에 기증한 책 추가
    con.commit()            # DB에 커밋
    lock.release()
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
