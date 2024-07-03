from tkinter import *
import socket
from random import *
import time
import threading
import pyperclip
s=socket.socket(type=socket.SOCK_DGRAM)
s.bind(('0.0.0.0',12345))
count={}
c=''
msg=''

def cp():
    pyperclip.copy(c.decode('gbk'))
def show():
    root = Tk()
    root.config(bg='black')
    root.wm_attributes('-topmost', True)
    # 设置窗口属性
    root.title('LAN MESSAGE TRANSPORTATION SYSTEM (LMTS) by 20220803 韩邦泽')
    
    # 向窗口添加组件
    
    
    label = Label(root, text=msg, font=('仿宋',30),fg='white',bg='black')
    label.pack(pady=50)
    frm_addr=Label(root,text='From  '+addr[0],font=('Lucida Handwriting',12),fg='white',bg='black')
    frm_addr.pack()
    copy = Button(root,text='Copy',command=cp)
    copy.pack()
    '''
    try:
        while True:
            a1=randint(0,255)
            b1=randint(0,255)
            c1=randint(0,255)
            label.configure(fg=rgbtcol(a1,b1,c1),bg=rgbtcol(255-a1,255-b1,255-c1))
            label.update()
            time.sleep(0.2)
    except:
    s.sendto(b'ok',addr)
    '''
        
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
