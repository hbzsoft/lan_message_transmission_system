import socket
import tkinter as tk
from tkinter import messagebox
windows=tk.Tk()
ipaddr_frm=tk.Frame(windows)
ipaddr_frm.pack()
ip_hint=tk.Label(ipaddr_frm,text='目标IP: ')
ip_hint.pack(side='left')
ip=tk.Entry(ipaddr_frm)
ip.pack(side='right')
windows.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) by 20220803 韩邦泽')
msg=tk.Text(windows,width=100,height=20)
msg.pack()
def send_socket():
    s=socket.socket(type=socket.SOCK_DGRAM)
    s.settimeout(1)
    s.bind(('0.0.0.0',14514))
    s.sendto(msg.get('1.0','end-1c').encode('gbk'),(ip.get(),12345))
    try:
        (c,addr)=s.recvfrom(1024)
    except ConnectionResetError:
        messagebox.showerror('信息发送器 by 20220803 韩邦泽','接收端未开启。')
    except socket.timeout:
        messagebox.showerror('信息发送器 by 20220803 韩邦泽','接收端未开启。')
    else:
        if c.decode()=='received':
            messagebox.showinfo('信息发送器 by 20220803 韩邦泽','接收端已接受到信息。')
        elif c.decode()=='refused':
            messagebox.showerror('信息发送器 by 20220803 韩邦泽','发送过于频繁。')
send=tk.Button(windows,text='发送',command=send_socket)
send.pack()
tk.mainloop()
