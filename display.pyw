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
from tkinter import *
import socket
from random import *
import time
import threading
import pyperclip
import pyttsx3
s=socket.socket(type=socket.SOCK_DGRAM)
s.bind(('0.0.0.0',12345))
count={}
c=''
msg=''
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
lice=Tk()
lice.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) v1.1')
a=Label(lice,text=lic)
a.pack()
lice.mainloop()
def cp():
    pyperclip.copy(c.decode('gbk'))
def show():
    
    root = Tk()
    root.config(bg='black')
    root.wm_attributes('-topmost', True)
    
    root.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) v1.1')
    
   
    
    label = Label(root, text=msg, font=('仿宋',30),fg='white',bg='black')
    label.pack(pady=50)
    frm_addr=Label(root,text='From  '+addr[0],font=('Lucida Handwriting',12),fg='white',bg='black')
    frm_addr.pack()
    copy = Button(root,text='Copy',command=cp)
    copy.pack()
    
    root.mainloop()
def say():
    engine = pyttsx3.init()
    engine.say(msg)
    engine.runAndWait()
    
    engine.stop()
while True:
    (c,addr)=s.recvfrom(2048)
    ip=addr[0]
    cnt=count.get(ip)
    if cnt==None:
        count[ip]=int(time.time())
    else:
        diff=int(time.time())-cnt
        if diff<=5:
            s.sendto('refused'.encode(),addr)
            continue
        else:
            count[ip]=int(time.time())
    msg=c.decode('gbk')
    s.sendto('received'.encode(),addr)
    thd1=threading.Thread(target=say)
    thd1.start()
    thd=threading.Thread(target=show)
    thd.start()
