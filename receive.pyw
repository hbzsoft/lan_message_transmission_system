'''
局域网信息传输系统 (LMTS) v1.4 - 接收端 by 韩邦泽&王润阳
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License.
'''
import socket
import time
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser
import pyperclip
import winsound
import subprocess
import re
import ctypes

class LMTSServer:
    def __init__(self):
        # 初始化socket和变量
        self.socket = socket.socket(type=socket.SOCK_DGRAM)  # UDP socket
        self.ip_count = {}  # 记录每个IP的发送频率
        self.current_message = ''  # 当前接收到的消息
        self.sender_address = None  # 发送者地址

        # 常量定义
        self.PORT = 12345
        self.RATE_LIMIT_SECONDS = 5  # 频率限制：5秒内同一IP只能发送一次
        self.MESSAGE_WIDTH = 30     # 消息自动换行宽度

    def set_volume_to_max(self):
        """将系统主音量设置为100%"""
        try:
            MAXIMUM_VOLUME = 0xFFFFFFFF  # 对应100%音量
            result = ctypes.windll.winmm.waveOutSetVolume(0, MAXIMUM_VOLUME)
            if result == 0:
                print("✅ 音量已设置为100%")
            else:
                print(f"❌ 设置音量失败，错误代码: {result}")
        except Exception as e:
            print(f"❌ 设置音量时发生错误: {e}")

    def get_process_using_port(self, port):
        """使用netstat获取占用指定端口的进程信息"""
        try:
            # 使用netstat命令获取UDP端口占用信息
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'UDP'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0:
                return None

            lines = result.stdout.split('\n')

            # 查找占用指定端口的行
            for line in lines:
                # 匹配UDP行，格式如: UDP    0.0.0.0:12345          *:*                                    1234
                match = re.search(r'UDP\s+[^:]+:(\d+)\s+.*?\s+(\d+)$', line.strip())
                if match:
                    found_port = int(match.group(1))
                    pid = match.group(2)

                    if found_port == port:
                        # 尝试获取进程名称
                        try:
                            # 使用tasklist命令获取进程名
                            task_result = subprocess.run(
                                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                                capture_output=True,
                                text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )

                            if task_result.returncode == 0 and task_result.stdout.strip():
                                # 解析CSV格式的输出，获取进程名
                                process_line = task_result.stdout.strip()
                                if ',' in process_line:
                                    process_name = process_line.split(',')[0].strip('"')
                                else:
                                    process_name = "未知进程"
                            else:
                                process_name = "未知进程"

                            return {
                                'pid': pid,
                                'name': process_name,
                                'status': '运行中'
                            }
                        except Exception:
                            return {'pid': pid, 'name': '未知进程', 'status': '未知'}

            return None
        except Exception as e:
            print(f"获取进程信息失败: {e}")
            return None

    def kill_process_by_pid(self, pid):
        """根据PID终止进程"""
        try:
            # 使用taskkill命令终止进程
            result = subprocess.run(
                ['taskkill', '/F', '/PID', pid],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                # 等待进程终止
                time.sleep(1)
                # 验证进程是否已终止
                check_result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                # 如果进程列表中找不到该PID，说明已成功终止
                return f"PID {pid}" not in check_result.stdout
            else:
                print(f"终止进程失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"终止进程时出错: {e}")
            return False

    def setup_socket(self):
        """设置并绑定socket到指定端口"""
        try:
            self.socket.bind(('0.0.0.0', self.PORT))
            print(f"服务器已启动，监听端口 {self.PORT}")
        except Exception as e:
            print(f"绑定端口失败: {e}")

            # 创建隐藏的根窗口用于显示对话框
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口

            # 获取占用端口的进程信息
            process_info = self.get_process_using_port(self.PORT)

            # 构建消息文本
            if process_info:
                message = (
                    f"端口 {self.PORT} 已被以下进程占用：\n\n"
                    f"进程ID: {process_info['pid']}\n"
                    f"进程名: {process_info['name']}\n\n"
                    "是否要终止此进程以释放端口？"
                )
            else:
                message = f"端口 {self.PORT} 已被占用，但无法获取进程信息。\n是否尝试强制终止占用端口的进程？"

            # 询问用户是否终止进程
            if messagebox.askyesno("端口被占用", message):
                if process_info:
                    # 尝试终止进程
                    if self.kill_process_by_pid(process_info['pid']):
                        # 重新创建socket并尝试绑定
                        self.socket.close()
                        self.socket = socket.socket(type=socket.SOCK_DGRAM)
                        try:
                            self.socket.bind(('0.0.0.0', self.PORT))
                            messagebox.showinfo("成功", f"服务器已启动，监听端口 {self.PORT}")
                            root.destroy()
                            return
                        except Exception as e2:
                            messagebox.showerror("错误", f"重新绑定端口失败: {e2}")
                    else:
                        messagebox.showerror("错误", "无法终止进程，请手动关闭占用端口的程序。")
                else:
                    # 无法获取进程信息，尝试使用netstat和taskkill组合命令
                    try:
                        # 查找占用端口的PID
                        result = subprocess.run(
                            f'netstat -ano -p UDP | findstr ":{self.PORT}"',
                            shell=True,
                            capture_output=True,
                            text=True
                        )

                        if result.returncode == 0:
                            # 提取PID
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                match = re.search(r'\s+(\d+)$', line.strip())
                                if match:
                                    pid = match.group(1)
                                    # 尝试终止进程
                                    if self.kill_process_by_pid(pid):
                                        # 重新创建socket并尝试绑定
                                        self.socket.close()
                                        self.socket = socket.socket(type=socket.SOCK_DGRAM)
                                        try:
                                            self.socket.bind(('0.0.0.0', self.PORT))
                                            messagebox.showinfo("成功", f"服务器已启动，监听端口 {self.PORT}")
                                            root.destroy()
                                            return
                                        except Exception as e2:
                                            messagebox.showerror("错误", f"重新绑定端口失败: {e2}")
                                    else:
                                        messagebox.showerror("错误", "无法终止进程，请手动关闭占用端口的程序。")
                                    break
                        else:
                            messagebox.showerror("错误", "无法找到占用端口的进程。")
                    except Exception as e2:
                        messagebox.showerror("错误", f"处理端口占用时出错: {e2}")

            # 如果用户选择不终止进程或终止失败，退出程序
            root.destroy()
            exit(0)

    def format_message(self, raw_message):
        """
        格式化接收到的消息
        - 处理蜂鸣提示标记
        - 自动换行处理
        """
        if not raw_message:
            return "", False

        message = raw_message
        need_beep = False

        # 检查是否需要蜂鸣提醒（消息以\a结尾）
        if message.endswith('\a'):
            need_beep = True
            message = message[:-1]  # 移除蜂鸣控制字符

        # 如果消息中已包含换行符，则保持原样
        # 否则按指定宽度自动换行
        if '\n' in message:
            formatted_message = message
        else:
            # 每30个字符插入一个换行符
            lines = []
            for i in range(0, len(message), self.MESSAGE_WIDTH):
                lines.append(message[i:i + self.MESSAGE_WIDTH])
            formatted_message = '\n'.join(lines)

        return formatted_message, need_beep

    def play_beep_sound(self):
        """播放蜂鸣声音"""
        try:
            time.sleep(0.5)
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        except Exception as e:
            print(f"播放声音失败: {e}")

    def open_website(self):
        """打开项目官方网站"""
        try:
            webbrowser.open('https://hbzsoft.github.io/', new=0)
        except Exception as e:
            print(f"打开网站失败: {e}")

    def copy_to_clipboard(self):
        """复制消息到剪贴板"""
        try:
            pyperclip.copy(self.current_message)
        except Exception as e:
            print(f"复制到剪贴板失败: {e}")
            messagebox.showerror("错误", "复制到剪贴板失败")

    def show_message_window(self):
        """
        创建并显示消息窗口
        使用tkinter创建置顶的消息显示界面
        """
        if not self.current_message:
            return

        try:
            # 创建主窗口
            root = tk.Tk()
            root.title('局域网信息传输系统 (LMTS) v1.4 - 接收端 by 韩邦泽&王润阳')
            root.config(bg='SteelBlue')
            root.wm_attributes('-topmost', True)  # 窗口置顶

            # 创建消息显示文本框
            text_widget = tk.Text(
                root,
                font=('楷体', 30),
                fg='white',
                bg='#2a51a7',
                width=25,
                height=10,
                wrap=tk.WORD  # 自动换行
            )

            # 插入格式化后的消息并居中显示
            formatted_msg, need_beep = self.format_message(self.current_message)
            text_widget.insert('1.0', formatted_msg)
            text_widget.tag_configure("center", justify="center")
            text_widget.tag_add("center", "1.0", 'end')
            text_widget.config(state=tk.DISABLED)  # 设置为只读
            text_widget.pack(padx=10, pady=10)

            # 显示发送者地址
            address_label = tk.Label(
                root,
                text=f'由 {self.sender_address[0]} 发送',
                fg='white',
                bg='SteelBlue'
            )
            address_label.pack(pady=5)

            # 复制按钮
            copy_button = tk.Button(
                root,
                text='复制',
                command=self.copy_to_clipboard
            )
            copy_button.pack(pady=5)

            # 网站链接
            website_button = tk.Button(
                root,
                text='官方网站: hbzsoft.github.io',
                font=('Arial', 8),
                command=self.open_website,
                fg="white",
                bg="SteelBlue",
                borderwidth=0
            )
            website_button.pack(pady=5)

            # 先显示窗口
            root.update()  # 强制更新窗口显示

            # 如果需要蜂鸣，则在显示窗口后播放声音
            if need_beep:
                beep_thread = threading.Thread(target=self.play_beep_sound)
                beep_thread.daemon = True
                beep_thread.start()

            # 启动GUI事件循环
            root.mainloop()

        except Exception as e:
            print(f"显示消息窗口时出错: {e}")

    def handle_message(self, data, address):
        """
        处理接收到的消息
        - 频率限制检查
        - 消息解码
        - 发送确认
        """
        ip = address[0]
        current_time = int(time.time())

        # 频率限制检查
        last_time = self.ip_count.get(ip)
        if last_time and (current_time - last_time) <= self.RATE_LIMIT_SECONDS:
            # 5秒内重复发送，拒绝接收
            self.socket.sendto('refused'.encode(), address)
            print(f"频率限制: 拒绝来自 {ip} 的消息")
            return False

        # 更新该IP的最后发送时间
        self.ip_count[ip] = current_time

        # 解码消息 (使用GBK编码以支持中文)
        try:
            decoded_message = data.decode('gbk')
        except UnicodeDecodeError:
            print(f"解码消息失败，使用默认编码")
            decoded_message = data.decode('utf-8', errors='ignore')

        # 保存消息和发送者信息
        self.current_message = decoded_message
        self.sender_address = address

        # 发送接收确认
        self.socket.sendto('received'.encode(), address)

        print(f"收到来自 {ip} 的消息: {decoded_message[:50]}...")
        return True

    def start_server(self):
        """启动服务器主循环"""
        self.setup_socket()

        print("等待接收消息...")
        while True:
            try:
                # 接收数据包
                data, address = self.socket.recvfrom(2048)

                # 处理消息
                if self.handle_message(data, address):
                    # 在新线程中显示消息窗口
                    display_thread = threading.Thread(target=self.show_message_window)
                    display_thread.daemon = True  # 设置为守护线程
                    display_thread.start()

            except socket.error as e:
                print(f"Socket错误: {e}")
            except Exception as e:
                print(f"处理消息时发生错误: {e}")

    def cleanup(self):
        """清理资源"""
        if self.socket:
            self.socket.close()
        print("服务器已关闭")

def main():
    """主函数"""
    server = LMTSServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在关闭服务器...")
    finally:
        server.cleanup()

if __name__ == "__main__":
    main()
