'''
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.'''
import socket
import tkinter as tk
from tkinter import messagebox
import webbrowser
def open_url():
    webbrowser.open('https://hanbangze.tech/',new=0)
def send_socket():
    s=socket.socket(type=socket.SOCK_DGRAM)
    s.settimeout(1)
    s.bind(('0.0.0.0',14514))
    try:
        if var.get()!=1:
            s.sendto(msg.get('1.0','end-1c').encode('gbk'),(ip.get(),12345))
        else:
            s.sendto((msg.get('1.0','end-1c')+'\a').encode('gbk'),(ip.get(),12345))
    except OSError:
        messagebox.showerror('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','网络错误')
    except Exception:
        messagebox.showerror('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','未知错误')
    try:
        (c,addr)=s.recvfrom(1024)
    except ConnectionResetError:
        messagebox.showerror('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','网络错误')
    except socket.timeout:
        messagebox.showerror('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','网络错误')
    else:
        if c.decode()=='received':
          
            messagebox.showinfo('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','接受端收到了您的信息。')
            
        elif c.decode()=='refused':
            messagebox.showerror('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端','发送过于频繁。稍后再试。')
        
windows=tk.Tk()
ipaddr_frm=tk.Frame(windows)
ipaddr_frm.pack()
ip_hint=tk.Label(ipaddr_frm,text='接收端IP地址: ')
ip_hint.pack(side='left')
ip=tk.Entry(ipaddr_frm)
ip.pack(side='right')
windows.title('局域网信息传输系统 (LMTS) v1.4 by 韩邦泽 & 王润阳 - 发送端')
msg=tk.Text(windows,width=100,height=20)
msg.pack()

var=tk.IntVar()
options=tk.Checkbutton(windows,text="加急 (接收端将发出提示音)",variable=var)
options.pack()
send=tk.Button(windows,text='发送',command=send_socket)
send.pack()
link = tk.Button(windows, text='官方网站: hanbangze.tech', font=('Segoe UI', 8),command=open_url,borderwidth=0)
    
link.pack()
tk.mainloop()
