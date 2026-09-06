'''
局域网信息传输系统 (LMTS) v1.5.01 - 接收端
v1.5 改进：
  - 加急：系统音量拉满 + 尖锐蜂鸣警报（时长受控，不伤听力）
  - 可回复消息：弹窗里直接输入回复内容发回发送端
  - 自定义背景配色与字体大小（读取 lmts_settings.json）
v1.5 补丁：
v1.5.01 改进：
  - IP 上报间隔改为每 8 秒一次
  - 修复双击无界面问题：增加常驻主窗口，服务器放后台
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License.
'''
import socket
import time
import threading
import json
import os
import tkinter as tk
from tkinter import messagebox
import webbrowser
import winsound
import subprocess
import re
import ctypes
import traceback

# ===== UDP广播发现 =====
BROADCAST_PORT = 54321
BROADCAST_INTERVAL = 3
ONLINE_TIMEOUT = 15
MULTICAST_GROUP = '239.255.61.61'
online_senders = {}  # {ip: last_timestamp}

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

def cleanup_online_senders():
    now = int(time.time())
    dead = [ip for ip, ts in online_senders.items() if now - ts > ONLINE_TIMEOUT]
    for ip in dead:
        del online_senders[ip]

# 接收端：广播自己的存在
def start_broadcast_sender(school_cfg, stop_event):
    def worker():
        sock = socket.socket(type=socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        while not stop_event.is_set():
            send_discovery_packet(sock, make_broadcast_packet('DISPLAY', school_cfg))
            if stop_event.wait(BROADCAST_INTERVAL):
                break
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t

# 接收端：监听广播，发现匹配的发送端
def start_broadcast_listener(school_cfg, stop_event):
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
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                pkt = parse_broadcast_packet(data)
                if pkt and pkt['role'] == 'SEND' and config_matches(pkt, school_cfg):
                    online_senders[addr[0]] = int(time.time())
                    cleanup_online_senders()
                    # 收到发送端发现包后单播回应，避免回程广播被路由器过滤。
                    try:
                        reply = make_broadcast_packet('DISPLAY', school_cfg)
                        # 沿发送端广播包的实际来源端口回传，避免随机端口收不到回应。
                        sock.sendto(reply, addr)
                    except OSError:
                        pass
            except socket.timeout:
                continue
            except Exception:
                continue
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t

APP_NAME = '局域网信息传输系统 (LMTS) v1.6'

# ===== 学校配置功能 =====
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

CONFIG_FILE = os.path.join(_APP_DIR, 'lmts_settings.json')

DEFAULT_CONFIG = {
    'bg': '#1e2a3a',
    'panel': '#27364a',
    'text': '#eef3f8',
    'accent': '#ffd166',
    'btn': '#2f80ed',
    'font_size': 30,
}
THEMES = {
    '深蓝':   {'bg': '#1e2a3a', 'panel': '#27364a', 'text': '#eef3f8', 'accent': '#ffd166', 'btn': '#2f80ed'},
    '暗黑':   {'bg': '#141414', 'panel': '#1f1f1f', 'text': '#e8e8e8', 'accent': '#00e676', 'btn': '#00b0ff'},
    '浅色':   {'bg': '#eef2f6', 'panel': '#ffffff', 'text': '#243447', 'accent': '#c56a00', 'btn': '#2563eb'},
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

def set_volume_percent(percent):
    try:
        volume = max(0, min(100, percent))
        value = int(0xFFFFFFFF * volume / 100)
        ctypes.windll.winmm.waveOutSetVolume(0, value)
    except Exception:
        pass

def play_urgent_alarm():
    try:
        time.sleep(0.3)
        set_volume_percent(100)
        for _ in range(3):
            winsound.Beep(2500, 300)
            time.sleep(0.1)
    except Exception as e:
        print(f'警报播放失败: {e}')

class LMTSServer:
    def __init__(self):
        self.socket = socket.socket(type=socket.SOCK_DGRAM)
        self.ip_count = {}
        self.current_message = ''
        self.sender_address = None
        self.PORT = 12345
        self.RATE_LIMIT_SECONDS = 5
        self.MESSAGE_WIDTH = 30
        self.display_callback = None

    def get_process_using_port(self, port):
        try:
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'UDP'],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return None
            for line in result.stdout.split('\n'):
                match = re.search(r'UDP\s+[^:]+:(\d+)\s+.*?\s+(\d+)$', line.strip())
                if match and int(match.group(1)) == port:
                    pid = match.group(2)
                    try:
                        task_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        if task_result.returncode == 0 and task_result.stdout.strip():
                            process_name = task_result.stdout.strip().split(',')[0].strip('"')
                        else:
                            process_name = '未知进程'
                        return {'pid': pid, 'name': process_name}
                    except Exception:
                        return {'pid': pid, 'name': '未知进程'}
            return None
        except Exception:
            return None

    def kill_process_by_pid(self, pid):
        try:
            result = subprocess.run(
                ['taskkill', '/F', '/PID', pid],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                time.sleep(1)
                return True
            return False
        except Exception:
            return False

    def setup_socket(self):
        try:
            self.socket.bind(('0.0.0.0', self.PORT))
            print(f'服务器已启动，监听端口 {self.PORT}')
            return
        except Exception as e:
            print(f'绑定端口失败: {e}')

        root = tk.Tk()
        root.withdraw()
        process_info = self.get_process_using_port(self.PORT)
        if process_info:
            message = (f'端口 {self.PORT} 已被进程占用：\n\n进程ID: {process_info["pid"]}\n'
                       f'进程名: {process_info["name"]}\n\n是否终止该进程以释放端口？')
        else:
            message = f'端口 {self.PORT} 已被占用。\n是否尝试强制终止占用端口的进程？'
        if messagebox.askyesno('端口被占用', message):
            pid = process_info['pid'] if process_info else None
            if not pid:
                try:
                    result = subprocess.run(
                        f'netstat -ano -p UDP | findstr ":{self.PORT}"',
                        shell=True, capture_output=True, text=True,
                    )
                    for line in result.stdout.strip().split('\n'):
                        m = re.search(r'\s+(\d+)$', line.strip())
                        if m:
                            pid = m.group(1)
                            break
                except Exception:
                    pid = None
            if pid and self.kill_process_by_pid(pid):
                self.socket.close()
                self.socket = socket.socket(type=socket.SOCK_DGRAM)
                try:
                    self.socket.bind(('0.0.0.0', self.PORT))
                    messagebox.showinfo('成功', f'服务器已启动，监听端口 {self.PORT}')
                    root.destroy()
                    return
                except Exception as e2:
                    messagebox.showerror('错误', f'重新绑定端口失败: {e2}')
            else:
                messagebox.showerror('错误', '无法终止进程，请手动关闭占用端口的程序。')
        root.destroy()
        exit(0)

    def format_message(self, raw_message):
        if not raw_message:
            return '', False
        message = raw_message
        need_alarm = False
        if message.endswith('\a'):
            need_alarm = True
            message = message[:-1]
        if '\n' in message:
            return message, need_alarm
        lines = [message[i:i + self.MESSAGE_WIDTH] for i in range(0, len(message), self.MESSAGE_WIDTH)]
        return '\n'.join(lines), need_alarm

    def open_website(self):
        try:
            webbrowser.open('https://hbzsoft.github.io/', new=0)
        except Exception:
            pass

    def copy_to_clipboard(self, text=None):
        value = text if text is not None else self.current_message
        try:
            import pyperclip
            pyperclip.copy(value)
            return
        except Exception:
            pass
        try:
            tmp = tk.Tk()
            tmp.withdraw()
            tmp.clipboard_clear()
            tmp.clipboard_append(value)
            tmp.update()
            tmp.destroy()
        except Exception:
            messagebox.showerror('错误', '复制到剪贴板失败')

    def send_reply(self, reply_entry, root_win, cfg):
        text = reply_entry.get('1.0', 'end-1c').strip()
        if not text:
            messagebox.showwarning(APP_NAME, '回复内容不能为空。')
            return
        if not self.sender_address:
            messagebox.showerror(APP_NAME, '没有可回复的发送端。')
            return
        try:
            self.socket.sendto(text.encode('gbk'), self.sender_address)
            messagebox.showinfo(APP_NAME, f'回复已发送给 {self.sender_address[0]}')
        except UnicodeEncodeError:
            try:
                self.socket.sendto(text.encode('utf-8'), self.sender_address)
                messagebox.showinfo(APP_NAME, f'回复已发送给 {self.sender_address[0]}')
            except OSError:
                messagebox.showerror(APP_NAME, '回复发送失败（网络错误）')
        except OSError:
            messagebox.showerror(APP_NAME, '回复发送失败（网络错误）')

    def handle_message(self, data, address):
        ip = address[0]
        # 真实消息到达即视为在线，避免广播被网络设备过滤时仍显示 0。
        online_senders[ip] = int(time.time())
        cleanup_online_senders()
        current_time = int(time.time())
        last_time = self.ip_count.get(ip)
        if last_time and (current_time - last_time) <= self.RATE_LIMIT_SECONDS:
            try:
                self.socket.sendto('refused'.encode(), address)
            except OSError:
                pass
            print(f'频率限制: 拒绝来自 {ip} 的消息')
            return False
        self.ip_count[ip] = current_time
        try:
            decoded_message = data.decode('gbk')
        except UnicodeDecodeError:
            decoded_message = data.decode('utf-8', errors='ignore')
        self.current_message = decoded_message
        self.sender_address = address
        try:
            self.socket.sendto('received'.encode(), address)
        except OSError:
            pass
        print(f'收到来自 {ip} 的消息: {decoded_message[:50]}...')
        if self.display_callback:
            self.display_callback(decoded_message, address)
        return True

    def start_server(self):
        self.setup_socket()
        print('等待接收消息...')
        while True:
            try:
                data, address = self.socket.recvfrom(2048)
                self.handle_message(data, address)
            except socket.error as e:
                print(f'Socket错误: {e}')
            except Exception as e:
                print(f'处理消息时发生错误: {e}')

    def cleanup(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        print('服务器已关闭')

# ===== 在主线程显示消息（基于 Toplevel） =====
def show_message_in_main(parent, server, msg, addr):
    if not msg:
        return
    cfg = load_config()
    try:
        win = tk.Toplevel(parent)
        win.title(f'{APP_NAME} - 接收端')
        win.configure(bg=cfg['bg'])
        win.attributes('-topmost', True)
        win.transient(parent)

        formatted_msg, need_alarm = server.format_message(msg)
        size = max(30, int(cfg.get('font_size', 30)))
        text_widget = tk.Text(win, font=('楷体', size), fg='white',
                              bg=cfg['panel'], width=25, height=8, wrap=tk.WORD)
        text_widget.insert('1.0', formatted_msg)
        text_widget.tag_configure('center', justify='center')
        text_widget.tag_add('center', '1.0', 'end')
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(padx=12, pady=6)

        # 弹窗内提供与发送端一致的主题及整体字号调节。
        control_row = tk.Frame(win, bg=cfg['bg'])
        control_row.pack(fill='x', padx=12, pady=(0, 4))
        def set_scale(delta):
            nonlocal size
            size = max(20, min(60, size + delta))
            text_widget.configure(font=('楷体', size))
            ui_size = max(9, min(18, round(size * 0.38)))
            reply_entry.configure(font=('Microsoft YaHei UI', ui_size))
            def resize_widgets(parent):
                for child in parent.winfo_children():
                    if isinstance(child, tk.Button): child.configure(font=('Microsoft YaHei UI', ui_size, 'bold'))
                    elif isinstance(child, tk.Label): child.configure(font=('Microsoft YaHei UI', ui_size))
                    if child.winfo_children(): resize_widgets(child)
            resize_widgets(win)
            # 统一按比例扩大整个窗口，确保底部控制条始终在可视区域内。
            scale = size / 30.0
            win.geometry(f'{int(760 * scale)}x{int(900 * scale)}')
            win.update_idletasks()
        tk.Button(control_row, text='−', command=lambda: set_scale(-2), bg=cfg['panel'], fg=cfg['text'], relief='flat', width=4).pack(side='left', padx=2)
        tk.Button(control_row, text='+', command=lambda: set_scale(2), bg=cfg['panel'], fg=cfg['text'], relief='flat', width=4).pack(side='left', padx=2)
        for name, colors in THEMES.items():
            tk.Button(control_row, text=name, command=lambda c=colors: (win.configure(bg=c['bg']), control_row.configure(bg=c['bg']), text_widget.configure(bg=c['panel'])), bg=colors['btn'], fg='white', relief='flat', padx=4).pack(side='left', padx=1)

        tk.Label(win, text=f'由 {addr[0]} 发送',
                 fg=cfg['text'], bg=cfg['bg']).pack(pady=2)

        reply_frame = tk.Frame(win, bg=cfg['bg'])
        reply_frame.pack(fill='x', padx=12, pady=4)
        tk.Label(reply_frame, text='回复：', bg=cfg['bg'], fg=cfg['accent'],
                 font=('Microsoft YaHei UI', 10, 'bold')).pack(anchor='w')
        reply_entry = tk.Text(reply_frame, bg='#ffffff', fg='#222222', relief='flat',
                              font=('Microsoft YaHei UI', 11), width=40, height=3, wrap='word')
        reply_entry.pack(fill='x', pady=(2, 4))
        tk.Button(reply_frame, text='发送回复',
                  command=lambda: server.send_reply(reply_entry, win, cfg),
                  bg=cfg['btn'], fg='#ffffff', relief='flat', cursor='hand2',
                  font=('Microsoft YaHei UI', 10, 'bold'), padx=16, pady=4).pack(side='left')

        button_row = tk.Frame(win, bg=cfg['bg'])
        button_row.pack(pady=6)
        tk.Button(button_row, text='复制', command=server.copy_to_clipboard,
                  bg=cfg['panel'], fg=cfg['text'], relief='flat', cursor='hand2',
                  font=('Microsoft YaHei UI', 10), padx=12, pady=4).pack(side='left', padx=4)
        tk.Button(button_row, text='关闭', command=win.destroy,
                  bg=cfg['panel'], fg=cfg['text'], relief='flat', cursor='hand2',
                  font=('Microsoft YaHei UI', 10), padx=12, pady=4).pack(side='left', padx=4)

        tk.Button(win, text='官方网站: hbzsoft.github.io', font=('Arial', 8),
                  command=server.open_website, fg='#9fb3c8', bg=cfg['bg'],
                  activebackground=cfg['bg'], borderwidth=0, cursor='hand2').pack(pady=(0, 8))
        # 控制条固定放在弹窗最底部。
        control_row.pack_forget()
        control_row.pack(fill='x', padx=12, pady=(0, 8))

        if need_alarm:
            threading.Thread(target=play_urgent_alarm, daemon=True).start()
    except Exception as e:
        print(f'显示消息窗口时出错: {e}')

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

    # 创建常驻主窗口
    root = tk.Tk()
    root.title(f'{APP_NAME} - 接收端')
    cfg = load_config()
    root.configure(bg=cfg['bg'])
    root.geometry('400x280')
    root.resizable(False, False)

    info_frame = tk.Frame(root, bg=cfg['bg'])
    info_frame.pack(pady=20, padx=20, fill='both', expand=True)
    tk.Label(info_frame, text='✅ 接收端已启动', font=('Microsoft YaHei UI', 16, 'bold'),
             fg=cfg['accent'], bg=cfg['bg']).pack(pady=10)
    tk.Label(info_frame, text=f'本机 IP: {get_lan_ip()}', font=('Consolas', 12),
             fg=cfg['text'], bg=cfg['bg']).pack(pady=4)
    online_label = tk.Label(info_frame, text='在线发送端: 0', font=('Consolas', 12),
                            fg=cfg['text'], bg=cfg['bg'])
    online_label.pack(pady=4)
    def request_exit():
        root.quit()

    root.protocol('WM_DELETE_WINDOW', request_exit)
    tk.Button(root, text='退出', command=request_exit,
              bg='#e74c3c', fg='white', relief='flat', cursor='hand2',
              font=('Microsoft YaHei UI', 10), padx=16, pady=6).pack(pady=15)

    def update_online():
        online_label.config(text=f'在线发送端: {len(online_senders)}')
        root.after(3000, update_online)
    root.after(1000, update_online)

    # 启动服务器
    server = LMTSServer()
    server.display_callback = lambda msg, addr: root.after(0, lambda: show_message_in_main(root, server, msg, addr))

    stop_event = threading.Event()
    start_broadcast_sender(school_cfg, stop_event)
    start_broadcast_listener(school_cfg, stop_event)

    server_thread = threading.Thread(target=server.start_server, daemon=True)
    server_thread.start()

    print(f'本机局域网 IP: {get_lan_ip()}（UDP广播发现，端口 {BROADCAST_PORT}）')
    print('接收端已启动，主窗口可见。')
    try:
        root.mainloop()
    finally:
        stop_event.set()
        server.cleanup()
        try:
            root.destroy()
        except tk.TclError:
            pass

if __name__ == '__main__':
    try:
        main()
    except Exception:
        details = traceback.format_exc()
        try:
            with open(os.path.join(_APP_DIR, 'display_error.log'), 'w', encoding='utf-8') as f:
                f.write(details)
        except OSError:
            pass
        try:
            messagebox.showerror(APP_NAME, '接收端运行失败，详情已写入 display_error.log。')
        except Exception:
            pass

