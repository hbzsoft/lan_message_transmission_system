'''
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.'''

from tkinter import *
import webbrowser
import socket
import time
import threading
import pyperclip
import winsound
s=socket.socket(type=socket.SOCK_DGRAM)
s.bind(('0.0.0.0',12345))
count={}
c=''
msg=''
def break_down(s):
    if s[-1]=='\a':
        x=''
        for i in range(len(s)-1):
            x+=s[i]
        s=x
        if s.find('\n'):
            return s
        else:
            return '\n'.join([s[i:i+30] for i in range(0, len(s), 30)])
    if s.find('\n'):
        return s
    else:
        return '\n'.join([s[i:i+30] for i in range(0, len(s), 30)])

def open_url():
    webbrowser.open('https://hbzsoft.github.io/',new=0)
def cp():
    pyperclip.copy(msg)
def show():
    
    if msg[-1]=='\a':
        winsound.Beep(1000, 1000)
    root = Tk()
    root.config(bg='black')
    root.wm_attributes('-topmost', True)
    # 设置窗口属性
    root.title('局域网信息传输系统 (LMTS) v1.3 by 韩邦泽 - 接收端')
    
    # 向窗口添加组件


    label = Text(root, font=('仿宋',30),fg='white',bg='black',width=25,height=10)
    label.insert('1.0',break_down(msg))
    label.tag_configure("center",justify="center")
    label.tag_add("center","1.0",'end')
    label.config(state=DISABLED)
    label.pack()
    
    frm_addr=Label(root,text='由  '+addr[0]+' 发送',fg='white',bg='black')
    frm_addr.pack()
    copy = Button(root,text='复制',command=cp)
    copy.pack()
    
    link = Button(root, text='官方网站: hbzsoft.github.io', font=('Arial', 8),command=open_url,fg="white",bg="black",borderwidth=0)
    
    link.pack()
    root.mainloop()

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
    thd=threading.Thread(target=show)
    thd.start()
