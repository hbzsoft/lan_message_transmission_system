'''
    LAN Message Transportation System (LMTS) allows users to send messages using LAN.

    Copyright (C) 2024  Bangze Han

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import socket
import tkinter as tk
import json
from tkinter import messagebox
lic='''
    LAN Message Transportation System (LMTS) allows users to send messages using LAN.

    Copyright (C) 2024  Bangze Han

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
lice=tk.Tk()
lice.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) v1.1')
a=tk.Label(lice,text=lic)
a.pack()
lice.mainloop()
windows=tk.Tk()
ipaddr_frm=tk.Frame(windows)
ipaddr_frm.pack()
ip_hint=tk.Label(ipaddr_frm,text='接收端备注名: ')
ip_hint.pack(side='left')
ip=tk.Entry(ipaddr_frm)
ip.pack(side='right')
windows.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) v1.1')
msg=tk.Text(windows,width=100,height=20)
msg.pack()
hosts={}
ip_addr_1=''
try:
    f=open('ip.json','r')
    hosts=json.load(f)
    f.close()
except Exception:
    f=open('ip.json','w')
    json.dump(hosts,f)
    f.close()
def zc(name,a):
    #print('zc',a)
    ip_addr_1=a
    #print('b',ip_addr_1)
    hosts[name]=ip_addr_1
    f=open('ip.json','w')
    json.dump(hosts,f)
    f.close()
def update_ip(name):
    
    get_ip=tk.Tk()
    get_ip.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) v1.1')
    ipaddr_frm1=tk.Frame(get_ip)
    ipaddr_frm1.pack()
    ip_hint1=tk.Label(ipaddr_frm1,text='IP: ')
    ip_hint1.pack(side='left')
    ip1=tk.Entry(ipaddr_frm1)
    ip1.pack(side='right')
    btn1=tk.Button(get_ip,text='确认',command=lambda: [zc(name,ip1.get()),get_ip.destroy()])
    btn1.pack()
    
    get_ip.mainloop()
    
def send_socket():
    s=socket.socket(type=socket.SOCK_DGRAM)
    s.settimeout(1)
    s.bind(('0.0.0.0',14514))
    name=ip.get()
    if hosts.get(name)==None:
        update_ip(name)
    #print(hosts[name])
    s.sendto(msg.get('1.0','end-1c').encode('gbk'),(hosts[name],12345))
    #print('sent')
    try:
        (c,addr)=s.recvfrom(1024)
    except ConnectionResetError:
        messagebox.showerror('LAN MESSAGE TRANSPORTATION SYSTEN (LMTS) v1.1','接收端未开启。')
    except socket.timeout:
        messagebox.showerror('LAN MESSAGE TRANSPORTATION SYSTEN (LMTS) v1.1','接收端未开启。')
    else:
        if c.decode()=='received':
            messagebox.showinfo('LAN MESSAGE TRANSPORTATION SYSTEN (LMTS) v1.1','接收端已接受到信息。')
        elif c.decode()=='refused':
            messagebox.showerror('LAN MESSAGE TRANSPORTATION SYSTEN (LMTS) v1.1','发送过于频繁。')
send=tk.Button(windows,text='发送',command=send_socket)
send.pack()
tk.mainloop()
