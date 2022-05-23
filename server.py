# ㅎㅇ

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

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', PORT))
    sock.listen(5)

    while True:
        clnt_sock, addr = sock.accept()

        lock.acquire()

        lock.release()
