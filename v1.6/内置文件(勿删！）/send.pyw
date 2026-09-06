'''
局域网信息传输系统 (LMTS) v1.5.01 - 发送端
v1.5 改进：
  - 修复端口占用导致发不出去的问题
  - 接收端可回复消息，本端实时弹窗显示
  - 自定义背景配色与字体大小
v1.5 补丁：
  - 修复"发送后收不到确认/回复"：改用监听 socket 发送，接收端回包才能回到 14514
v1.5.01 改进：
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
'''
import socket
import time
import threading
import json
import os
import tkinter as tk
from tkinter import messagebox
import webbrowser
import urllib.request
import traceback

# ===== UDP广播发现（新增） =====
BROADCAST_PORT = 54321
BROADCAST_INTERVAL = 3
ONLINE_TIMEOUT = 15
MULTICAST_GROUP = '239.255.61.61'

def get_lan_ip():
    for target in ('192.0.2.1', '8.8.8.8'):
        try:
            s = socket.socket(type=socket.SOCK_DGRAM)
            s.connect((target, 80))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith('127.'):
                return ip
        except OSError:
            pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return '127.0.0.1'

def send_discovery_packet(sock, packet):
    """广播与组播同时发送，提高不同路由器/无线网络下的发现成功率。"""
    for host in ('255.255.255.255', MULTICAST_GROUP):
        try:
            sock.sendto(packet, (host, BROADCAST_PORT))
        except OSError:
            pass

def make_broadcast_packet(role, school_cfg):
    ip = get_lan_ip()
    ts = int(time.time())
    return f"LMTS|{role}|{school_cfg['school']}|{school_cfg['grade']}|{school_cfg['class']}|{ip}|{ts}".encode('utf-8')

def parse_broadcast_packet(data):
    try:
        parts = data.decode('utf-8').split('|')
        if len(parts) >= 7 and parts[0] == 'LMTS':
            return {'role': parts[1], 'school': parts[2], 'grade': parts[3], 'class': parts[4], 'ip': parts[5], 'timestamp': int(parts[6])}
    except Exception:
        pass
    return None

def config_matches(pkt, school_cfg):
    return (pkt['school'] == school_cfg['school'] and 
            pkt['grade'] == school_cfg['grade'] and 
            pkt['class'] == school_cfg['class'])

def start_broadcast_listener(root, school_cfg, ip_entry, status_label, online_displays):
    def worker():
        sock = socket.socket(type=socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', BROADCAST_PORT))
        try:
            membership = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton('0.0.0.0')
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        except OSError:
            pass
        sock.settimeout(1)
        while True:
            try:
                data, addr = sock.recvfrom(2048)
                pkt = parse_broadcast_packet(data)
                if pkt and pkt['role'] == 'DISPLAY' and config_matches(pkt, school_cfg):
                    remote_ip = pkt.get('ip') or addr[0]
                    online_displays[remote_ip] = int(time.time())
                    root.after(0, lambda ip=remote_ip: (
                        ip_entry.delete(0, 'end'),
                        ip_entry.insert(0, ip),
                        save_last_ip(ip),
                        status_label.config(text=f'已发现接收端：{ip}（班级匹配）')
                    ))
            except socket.timeout:
                continue
            except Exception:
                continue
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t

def start_broadcast_sender(school_cfg, stop_event):
    def worker():
        sock = socket.socket(type=socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        while not stop_event.is_set():
            send_discovery_packet(sock, make_broadcast_packet('SEND', school_cfg))
            if stop_event.wait(BROADCAST_INTERVAL):
                break
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
# ===== UDP广播发现结束 =====
import re

APP_NAME = '局域网信息传输系统 (LMTS) v1.6'

# ===== 学校配置功能（新增） =====
import sys as _sys
if getattr(_sys, 'frozen', False):
    _APP_DIR = os.path.dirname(_sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
SCHOOL_CONFIG_FILE = os.path.join(_APP_DIR, 'lmts_school.json')

def load_school_config():
    try:
        if os.path.exists(SCHOOL_CONFIG_FILE):
            with open(SCHOOL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_school_config(cfg):
    try:
        with open(SCHOOL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

class SchoolConfigDialog:
    def __init__(self, parent):
        self.result = None
        self.win = tk.Toplevel(parent)
        self.win.title('初始配置')
        self.win.configure(bg='#1e2a3a')
        self.win.resizable(False, False)
        self.win.attributes('-topmost', True)
        self.win.grab_set()
        frame = tk.Frame(self.win, bg='#1e2a3a', padx=24, pady=20)
        frame.pack()
        tk.Label(frame, text='学校（如 nfls）', bg='#1e2a3a', fg='#eef3f8',
                 font=('Microsoft YaHei UI', 10)).grid(row=0, column=0, sticky='w', pady=(0, 4))
        self.school_entry = tk.Entry(frame, bg='#ffffff', fg='#222222', relief='flat',
                                      font=('Consolas', 12), width=20)
        self.school_entry.grid(row=1, column=0, pady=(0, 12), ipady=4)
        self.school_entry.insert(0, 'nfls')
        tk.Label(frame, text='届数（如 2025）', bg='#1e2a3a', fg='#eef3f8',
                 font=('Microsoft YaHei UI', 10)).grid(row=2, column=0, sticky='w', pady=(0, 4))
        self.grade_entry = tk.Entry(frame, bg='#ffffff', fg='#222222', relief='flat',
                                     font=('Consolas', 12), width=20)
        self.grade_entry.grid(row=3, column=0, pady=(0, 12), ipady=4)
        self.grade_entry.insert(0, '2025')
        tk.Label(frame, text='班级（2位数字，如 08）', bg='#1e2a3a', fg='#eef3f8',
                 font=('Microsoft YaHei UI', 10)).grid(row=4, column=0, sticky='w', pady=(0, 4))
        self.class_entry = tk.Entry(frame, bg='#ffffff', fg='#222222', relief='flat',
                                     font=('Consolas', 12), width=20)
        self.class_entry.grid(row=5, column=0, pady=(0, 16), ipady=4)
        self.class_entry.insert(0, '08')
        btn_frame = tk.Frame(frame, bg='#1e2a3a')
        btn_frame.grid(row=6, column=0, sticky='ew')
        tk.Button(btn_frame, text='确定', command=self.on_ok,
                  bg='#2f80ed', fg='#ffffff', relief='flat', cursor='hand2',
                  font=('Microsoft YaHei UI', 10, 'bold'), padx=24, pady=5).pack(side='right')
        self.win.protocol('WM_DELETE_WINDOW', self.on_cancel)
        self.win.wait_window()

    def on_ok(self):
        import re as _re
        school = self.school_entry.get().strip()
        grade = self.grade_entry.get().strip()
        cls = self.class_entry.get().strip()
        if not school or not grade or not cls:
            messagebox.showwarning('提示', '请填写完整信息。', parent=self.win)
            return
        if not _re.match(r'^\d{4}$', grade):
            messagebox.showwarning('提示', '届数应为4位数字（如 2025）。', parent=self.win)
            return
        if not _re.match(r'^\d{2}$', cls):
            messagebox.showwarning('提示', '班级应为2位数字（如 08）。', parent=self.win)
            return
        self.result = {'school': school, 'grade': grade, 'class': cls}
        self.win.destroy()

    def on_cancel(self):
        self.result = None
        self.win.destroy()
# ===== 学校配置功能结束 =====

CONFIG_FILE = os.path.join(_APP_DIR, 'lmts_settings.json')

# 默认配色（深蓝）
DEFAULT_CONFIG = {
    'bg': '#1e2a3a',
    'panel': '#27364a',
    'text': '#eef3f8',
    'accent': '#ffd166',
    'btn': '#2f80ed',
    'font_size': 11,
    'last_ip': '',
}
# 预设配色方案
THEMES = {
    '深蓝':   {'bg': '#1e2a3a', 'panel': '#27364a', 'text': '#eef3f8', 'accent': '#ffd166', 'btn': '#2f80ed'},
    '暗黑':   {'bg': '#141414', 'panel': '#1f1f1f', 'text': '#e8e8e8', 'accent': '#00e676', 'btn': '#00b0ff'},
    '浅色':   {'bg': '#f0f4f8', 'panel': '#ffffff', 'text': '#1a2733', 'accent': '#e65100', 'btn': '#1565c0'},
    '紫夜':   {'bg': '#1a1025', 'panel': '#2a1a3f', 'text': '#f0e6ff', 'accent': '#ffd166', 'btn': '#7c4dff'},
    '薄荷':   {'bg': '#0f2b23', 'panel': '#174234', 'text': '#eafff5', 'accent': '#ffb74d', 'btn': '#26a69a'},
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                for k in cfg:
                    if k in saved:
                        cfg[k] = saved[k]
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def is_valid_ipv4(value):
    parts = value.strip().split('.')
    return (len(parts) == 4 and
            all(part.isdigit() and 0 <= int(part) <= 255 for part in parts))

def save_last_ip(value, cfg=None):
    value = value.strip()
    if not is_valid_ipv4(value):
        return False
    target_cfg = cfg if cfg is not None else load_config()
    if target_cfg.get('last_ip') != value:
        target_cfg['last_ip'] = value
        save_config(target_cfg)
    return True


def open_url():
    webbrowser.open('https://hbzsoft.github.io/', new=0)


# ---- 常驻监听：接收端回复 / 确认 ----
listener_socket = None
listener_running = False


def start_listener(root, on_message):
    """后台线程：绑定 14514 端口，接收接收端发回的确认与回复。"""
    global listener_socket, listener_running
    if listener_running:
        return
    listener_running = True

    def worker():
        global listener_socket
        s = socket.socket(type=socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', 14514))
        except OSError:
            # 端口被占：改用随机端口（接收端回包会发到本 socket 源端口，仍可收到）
            s = socket.socket(type=socket.SOCK_DGRAM)
            try:
                s.bind(('0.0.0.0', 0))
            except OSError:
                pass
        s.settimeout(1)
        listener_socket = s
        while listener_running:
            try:
                data, addr = s.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                text = data.decode('gbk')
            except UnicodeDecodeError:
                text = data.decode('utf-8', errors='ignore')
            if text == 'received':
                root.after(0, lambda: on_message('confirm'))
            elif text == 'refused':
                root.after(0, lambda: on_message('refused'))
            else:
                root.after(0, lambda t=text, a=addr: on_message('reply', t, a))
        try:
            s.close()
        except Exception:
            pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()


def send_message(root, ip_entry, msg_text, urgent_var, status_label, cfg=None):
    target = ip_entry.get().strip()
    if not target:
        messagebox.showwarning(APP_NAME, '请先填写接收端 IP 地址。')
        return
    if not is_valid_ipv4(target):
        messagebox.showwarning(APP_NAME, 'IP 地址格式不正确。')
        return
    save_last_ip(target, cfg)
    content = msg_text.get('1.0', 'end-1c').strip()
    if not content:
        messagebox.showwarning(APP_NAME, '消息内容不能为空。')
        return
    # 用监听 socket 发送：源端口 = 监听端口（14514），
    # 接收端的确认/回复才能发回监听端口，本端才收得到（v1.5 补丁）
    payload = content + ('\a' if urgent_var.get() == 1 else '')
    try:
        raw = payload.encode('gbk')
    except UnicodeEncodeError:
        raw = payload.encode('utf-8')
    try:
        if listener_socket is not None:
            listener_socket.sendto(raw, (target, 12345))
        else:
            s = socket.socket(type=socket.SOCK_DGRAM)
            try:
                s.sendto(raw, (target, 12345))
            finally:
                s.close()
        status_label.config(text='已发送，等待接收端确认…')
    except OSError:
        messagebox.showerror(APP_NAME, '网络错误，发送失败。')


def build_ui(root):
    cfg = load_config()
    online_displays = {}

    def apply_theme(name):
        theme = THEMES.get(name)
        if not theme:
            return
        for k, v in theme.items():
            cfg[k] = v
        save_config(cfg)
        # 重刷背景色
        root.configure(bg=cfg['bg'])
        title_bar.configure(bg=cfg['bg'])
        sub_label.configure(bg=cfg['bg'], fg=cfg['accent'])
        ip_frame.configure(bg=cfg['panel'])
        for w in ip_frame.winfo_children():
            w.configure(bg=cfg['panel'])
        ip_entry.configure(bg='#ffffff', fg='#222222')
        msg_frame.configure(bg=cfg['panel'])
        msg_label.configure(bg=cfg['panel'])
        msg_text.configure(font=('Microsoft YaHei UI', cfg['font_size']))
        opt_frame.configure(bg=cfg['bg'])
        options.configure(bg=cfg['bg'], fg=cfg['text'], activebackground=cfg['bg'])
        btn_frame.configure(bg=cfg['bg'])
        send_btn.configure(bg=cfg['btn'], font=('Microsoft YaHei UI', 12, 'bold'))
        status_label.configure(bg=cfg['bg'])
        link.configure(bg=cfg['bg'])
        theme_frame.configure(bg=cfg['bg'])
        theme_label.configure(bg=cfg['bg'], fg=cfg['text'])
        for b in theme_buttons:
            b.configure(bg=cfg['panel'], fg=cfg['text'])
        font_label.configure(bg=cfg['bg'], fg=cfg['text'])

    def change_font(delta):
        cfg['font_size'] = max(9, min(20, cfg['font_size'] + delta))
        save_config(cfg)
        msg_text.configure(font=('Microsoft YaHei UI', cfg['font_size']))

    # 品牌标题
    title_bar = tk.Frame(root, bg=cfg['bg'])
    title_bar.pack(fill='x', padx=16, pady=(14, 4))
    tk.Label(title_bar, text='局域网信息传输系统', bg=cfg['bg'], fg=cfg['text'],
             font=('Microsoft YaHei UI', 16, 'bold')).pack(anchor='w')
    sub_label = tk.Label(title_bar, text='v1.6 发送端',
                         bg=cfg['bg'], fg=cfg['accent'], font=('Microsoft YaHei UI', 9, 'bold'))
    sub_label.pack(anchor='w', pady=(2, 0))

    # IP 输入区
    ip_frame = tk.Frame(root, bg=cfg['panel'], padx=14, pady=10)
    ip_frame.pack(fill='x', padx=16, pady=8)
    tk.Label(ip_frame, text='接收端 IP：', bg=cfg['panel'], fg=cfg['text'],
             font=('Microsoft YaHei UI', 10)).pack(side='left')
    ip_entry = tk.Entry(ip_frame, bg='#ffffff', fg='#222222', relief='flat',
                        font=('Consolas', 11), width=16)
    ip_entry.pack(side='left', padx=8, ipady=4)
    saved_ip = cfg.get('last_ip', '').strip()
    if is_valid_ipv4(saved_ip):
        ip_entry.insert(0, saved_ip)

    # 消息区
    msg_frame = tk.Frame(root, bg=cfg['panel'], padx=14, pady=10)
    msg_frame.pack(fill='both', expand=True, padx=16, pady=8)
    msg_label = tk.Label(msg_frame, text='消息内容：', bg=cfg['panel'], fg=cfg['text'],
                         font=('Microsoft YaHei UI', 10))
    msg_label.pack(anchor='w')
    msg_text = tk.Text(msg_frame, width=64, height=10, bg='#ffffff', fg='#222222',
                       relief='flat', font=('Microsoft YaHei UI', cfg['font_size']), wrap='word')
    msg_text.pack(fill='both', expand=True, pady=(4, 0))

    # 选项与发送
    opt_frame = tk.Frame(root, bg=cfg['bg'])
    opt_frame.pack(fill='x', padx=16, pady=4)
    urgent_var = tk.IntVar()
    options = tk.Checkbutton(opt_frame, text='加急（接收端响警报）', variable=urgent_var,
                             bg=cfg['bg'], fg=cfg['text'], selectcolor=cfg['bg'],
                             activebackground=cfg['bg'], activeforeground=cfg['text'],
                             font=('Microsoft YaHei UI', 10), cursor='hand2')
    options.pack(side='left')

    btn_frame = tk.Frame(root, bg=cfg['bg'])
    btn_frame.pack(fill='x', padx=16, pady=(6, 4))
    send_btn = tk.Button(btn_frame, text='发 送', command=lambda: send_message(root, ip_entry, msg_text, urgent_var, status_label, cfg),
                         bg=cfg['btn'], fg='#ffffff', activebackground='#1e6fd9', relief='flat',
                         cursor='hand2', font=('Microsoft YaHei UI', 12, 'bold'), padx=28, pady=8)
    send_btn.pack(side='left')

    # 主题与字体
    theme_frame = tk.Frame(root, bg=cfg['bg'])
    theme_frame.pack(fill='x', padx=16, pady=(2, 0))
    theme_label = tk.Label(theme_frame, text='配色：', bg=cfg['bg'], fg=cfg['text'],
                           font=('Microsoft YaHei UI', 9))
    theme_label.pack(side='left')
    theme_buttons = []
    for name in THEMES:
        b = tk.Button(theme_frame, text=name, command=lambda n=name: apply_theme(n),
                      bg=cfg['panel'], fg=cfg['text'], relief='flat', cursor='hand2',
                      font=('Microsoft YaHei UI', 9), padx=8, pady=2)
        b.pack(side='left', padx=3)
        theme_buttons.append(b)
    tk.Button(theme_frame, text='−', command=lambda: change_font(-1),
              bg=cfg['panel'], fg=cfg['text'], relief='flat', cursor='hand2',
              font=('Microsoft YaHei UI', 9, 'bold'), padx=8, pady=2).pack(side='left', padx=2)
    tk.Button(theme_frame, text='+', command=lambda: change_font(1),
              bg=cfg['panel'], fg=cfg['text'], relief='flat', cursor='hand2',
              font=('Microsoft YaHei UI', 9, 'bold'), padx=8, pady=2).pack(side='left', padx=2)

    # 状态栏
    initial_status = ('使用上次保存的 IP，等待自动发现…'
                      if is_valid_ipv4(saved_ip) else '就绪，等待自动发现接收端…')
    status_label = tk.Label(root, text=initial_status, bg=cfg['bg'], fg='#9fb3c8', anchor='w',
                            font=('Microsoft YaHei UI', 9))
    status_label.pack(fill='x', padx=18, pady=(2, 0))

    def remember_typed_ip(_event=None):
        value = ip_entry.get().strip()
        if save_last_ip(value, cfg):
            status_label.config(text=f'已保存接收端 IP：{value}')

    ip_entry.bind('<FocusOut>', remember_typed_ip)
    ip_entry.bind('<Return>', remember_typed_ip)

    link = tk.Button(root, text='官方网站: hbzsoft.github.io', font=('Segoe UI', 8),
                     command=open_url, bg=cfg['bg'], fg='#9fb3c8', activebackground=cfg['bg'],
                     activeforeground=cfg['accent'], borderwidth=0, cursor='hand2')
    link.pack(pady=(0, 8))

    # 接收回复弹窗
    def on_message(kind, text='', addr=None):
        if kind == 'confirm':
            status_label.config(text='接收端已收到消息')
            messagebox.showinfo(APP_NAME, '接收端收到了您的消息。')
        elif kind == 'refused':
            status_label.config(text='发送过于频繁，稍后再试')
            messagebox.showerror(APP_NAME, '发送过于频繁，稍后再试。')
        elif kind == 'reply':
            status_label.config(text=f'收到来自 {addr[0]} 的回复')
            reply_win = tk.Toplevel(root)
            reply_win.title(f'{APP_NAME} - 回复')
            reply_win.configure(bg=cfg['bg'])
            reply_win.attributes('-topmost', True)
            tk.Label(reply_win, text=f'接收端（{addr[0]}）回复：', bg=cfg['bg'], fg=cfg['accent'],
                     font=('Microsoft YaHei UI', 10, 'bold')).pack(padx=16, pady=(12, 4), anchor='w')
            reply_text = tk.Text(reply_win, bg='#ffffff', fg='#222222', relief='flat',
                                 font=('Microsoft YaHei UI', 12), width=40, height=6, wrap='word')
            reply_text.pack(padx=16, pady=4)
            reply_text.insert('1.0', text)
            reply_text.config(state='disabled')
            tk.Button(reply_win, text='关闭', command=reply_win.destroy,
                      bg=cfg['btn'], fg='#ffffff', relief='flat', cursor='hand2',
                      font=('Microsoft YaHei UI', 10), padx=16, pady=4).pack(pady=(4, 12))

    start_listener(root, on_message)
    school_cfg_for_broadcast = load_school_config()
    if school_cfg_for_broadcast:
        start_broadcast_listener(root, school_cfg_for_broadcast, ip_entry, status_label, online_displays)
    return root


def main():
    school_cfg = load_school_config()
    if not school_cfg or not all(k in school_cfg for k in ('school', 'grade', 'class')):
        tmp = tk.Tk()
        tmp.withdraw()
        dlg = SchoolConfigDialog(tmp)
        if not dlg.result:
            tmp.destroy()
            return
        school_cfg = dlg.result
        save_school_config(school_cfg)
        tmp.destroy()
    root = tk.Tk()
    root.title(f'{APP_NAME} - 发送端')
    root.configure(bg=load_config()['bg'])
    root.resizable(False, False)
    build_ui(root)
    stop_event = threading.Event()
    school_cfg_main = load_school_config()
    if school_cfg_main:
        start_broadcast_sender(school_cfg_main, stop_event)
    try:
        root.mainloop()
    finally:
        stop_event.set()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        details = traceback.format_exc()
        try:
            with open(os.path.join(_APP_DIR, 'send_error.log'), 'w', encoding='utf-8') as f:
                f.write(details)
        except OSError:
            pass
        try:
            messagebox.showerror(APP_NAME, '发送端启动失败，详情已写入 send_error.log。')
        except Exception:
            pass

