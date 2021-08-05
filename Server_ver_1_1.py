import socket
import threading
import os
import requests
import json
import pickle
import schedule
import time
from datetime import date
from waiting import wait
# --- functions ---

def dang_ky(conn, addr):
    file_registry = open('DS_ng_dung.txt', 'a')
    try:
        while True:
            file_read = open('DS_ng_dung.txt', 'r')
            username_recv = conn.recv(1024).decode("utf8")
            password_recv = conn.recv(1024).decode("utf8")
            pass_again_recv = conn.recv(1024).decode("utf8")
            check_exist = username_recv
            success = True
            print("flag")
            while file_read.tell() != os.fstat(file_read.fileno()).st_size:
                line = file_read.readline()
                line_split = line.split(" ")

                if line_split[0] == check_exist or pass_again_recv != password_recv:
                    print("vô đây")
                    conn.sendall(bytes("Ten dang nhap ton tai", "utf8"))
                    success = False
                    break
            if success == True:
                file_registry.writelines(username_recv + " " + password_recv + "\n")
                conn.sendall(bytes("Dang ky thanh cong", "utf8"))
                break
        file_read.close()
        file_registry.close()
    except socket.error:
        return


def dang_nhap(conn, addr):
    while True:
        try:
            file_Login = open('DS_ng_dung.txt', 'r')
            user_name = conn.recv(1024).decode("utf8")
            password = conn.recv(1024).decode("utf8")
            success = False
            while file_Login.tell() != os.fstat(file_Login.fileno()).st_size:
                line = file_Login.readline()
                if line == user_name + " " + password + "\n":
                    conn.sendall(bytes("Ban da dang nhap thanh cong", "utf8"))
                    success = True
                    break
            if success == False:
                conn.sendall(bytes("Ten dang nhap hoac mat khau khong dung", "utf8"))
            else:
                break
        except socket.error:
            return

def update_json_file():
    url = 'https://tygia.com/json.php?ran=0&rate=0&gold=1&bank=VIETCOM&date=now'
    r = requests.get(url)
    r = r.text.encode("UTF8")
    data = json.loads(r)
    file_data = open('data.json', 'wb')
    file_data.write(r)
    file_data.close()

def update_json_data_after_30m():

    schedule.every(30).minutes.do(update_json_file)
    while 1:
        schedule.run_pending()
        time.sleep(1)



def Luu_va_cap_nhat_du_lieu(nam, thang, ngay):
    url = 'https://tygia.com/json.php?ran=0&rate=0&gold=1&bank=VIETCOM&date=' + nam + thang + ngay

    r = requests.get(url)
    print('request thành công')
    r = r.text.encode("UTF8")
    data = json.loads(r)
    file_data = open('data.json', 'wb')
    file_data.write(r)
    file_data.close()


def tra_cuu_implement(nam, thang, ngay, vang):
    today = date.today()
    if nam+"-"+thang+"-"+ngay != today:
        Luu_va_cap_nhat_du_lieu(nam, thang, ngay)
        print("flag")
    f = open('data.json', "r", encoding='utf-8-sig')
    infor = json.load(f)
    try:
        for name in infor['golds'][0]['value']:
            if name['company'] + " " + name['brand'] == vang:
                reply = pickle.dumps(name)
                conn.send(reply)
        check = {"id": 0}
        success = pickle.dumps(check)
        conn.send(success)
        f.close()
        print("Code chay toi day")
        return
    except socket.error:
        return


def tra_cuu(conn, addr):
    while True:
        try:
            msg = conn.recv(1024).decode("utf8")
            if msg == "dung tra cuu":
                return
            msg_nam = conn.recv(1024).decode("utf8")
            msg_thang = conn.recv(1024).decode("utf8")
            msg_ngay = conn.recv(1024).decode("utf8")
            msg_vang = conn.recv(1024).decode("utf8")
            tra_cuu_implement(msg_nam, msg_thang, msg_ngay, msg_vang)
        except socket.error:
            # print(f'{addr} đã thoát khỏi server')
            # conn.close()
            return



def client_exit(conn, addr):
    conn.close()
    print(f"{addr} da thoat khoi server")

def is_something_ready(command):
    if command.ready():
        return True
    return False

def handle_client(conn, addr):
    while True:
        print('[handle_client] read command')

        try:
            command = conn.recv(1024).decode("utf8")
        except :
            print(f'{addr} đã thoát 1 cách đột ngột')
            conn.close()
            break

        command = command.lower()
        print('[handle_client] run command:', command)
        if command == "dang ky":
            dang_ky(conn, addr)
        elif command == "dang nhap":
            dang_nhap(conn, addr)
        elif command == "tra cuu":
            tra_cuu(conn, addr)
        elif command == "exit":
            client_exit(conn, addr)
            break



# --------------------------- main ------------------------------------


HOST = ''  # PEP8: spaces around `=`
PORT = 65432  # PEP8: spaces around `=`

print('Starting ...')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # PEP8: space after `,`
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
             1)  # solution for "[Error 89] Address already in use". Use before bind()
s.bind((HOST, PORT))
s.listen()

all_threads = []
all_clients = []
try:
    while True:
        t2 = threading.Thread(target=update_json_data_after_30m, args=())
        t2.start()
        print('Waiting for client')
        conn, addr = s.accept()
        print(f"{addr} da ket noi den server")
        print(f"Handle client: {addr}")

        # run in current thread - only one client can connect
        # handle_client(conn, addr)
        # all_clients.append((conn, addr))

        # run in separated thread - many clients can connect
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()
        all_threads.append(t)
except KeyboardInterrupt:
    print('Stopped by Ctrl+C')
finally:
    s.close()
    for t in all_threads:
        t.join()
    # for conn, addr in all_clients:
    #     conn.close()
