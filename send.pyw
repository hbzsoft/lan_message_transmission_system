'''
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.'''
import socket
import tkinter as tk
from tkinter import messagebox
import webbrowser
def open_url():
    webbrowser.open('https://hbzsoft.github.io/',new=0)
def send_socket():
    s=socket.socket(type=socket.SOCK_DGRAM)
    s.settimeout(1)
    s.bind(('0.0.0.0',14514))
    s.sendto(msg.get('1.0','end-1c').encode('gbk'),(ip.get(),12345))
    try:
        (c,addr)=s.recvfrom(1024)
    except ConnectionResetError:
        messagebox.showerror('LAN MESSAGE TRANSMISSION SYSTEM (LMTS) v1.2 by Bangze Han','Network issue/Client not running')
    except socket.timeout:
        messagebox.showerror('LAN MESSAGE TRANSMISSION SYSTEM (LMTS) v1.2 by Bangze Han','Network issue/Client not running')
    else:
        if c.decode()=='received':
            messagebox.showinfo('LAN MESSAGE TRANSMISSION SYSTEM (LMTS) v1.2 by Bangze Han','Client has received your message')
        elif c.decode()=='refused':
            messagebox.showerror('LAN MESSAGE TRANSMISSION SYSTEM (LMTS) v1.2 by Bangze Han','Too frequent. Try again later.')
windows=tk.Tk()
ipaddr_frm=tk.Frame(windows)
ipaddr_frm.pack()
ip_hint=tk.Label(ipaddr_frm,text='Target IP: ')
ip_hint.pack(side='left')
ip=tk.Entry(ipaddr_frm)
ip.pack(side='right')
windows.title('LAN MESSAGE TRANSMISSION SYSTEM (LMTS) v1.2 by Bangze Han')
msg=tk.Text(windows,width=100,height=20)
msg.pack()

send=tk.Button(windows,text='发送',command=send_socket)
send.pack()
link = tk.Button(windows, text='Official Website: hbzsoft.github.io', font=('Arial', 8),command=open_url,borderwidth=0)
    
link.pack()
tk.mainloop()
