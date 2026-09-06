LMTS 1.6 修正版
================

方法一：编译 EXE
1. 安装 Python 3，并确保 Python 已加入 PATH。
2. 双击 build_exe.bat。
3. 编译结果在 dist 文件夹：send.exe、display.exe、lmts_school.json。
4. 在两台电脑上分别运行一次 allow_firewall.bat，并同意管理员提示。

方法二：直接运行 PYW（编译失败时使用）
1. 双击 run_pyw.bat。
2. BAT 会检测 Python；没有 Python 时会优先通过 winget 自动安装。
3. 自动安装不可用时会打开 Python 下载页面，安装后重新运行此 BAT。
4. BAT 会创建独立的 .run-venv 环境，然后可选择启动发送端、接收端或同时启动。
5. 命令行也可使用：run_pyw.bat send、display、both、debug-send、debug-display。

局域网使用
1. 两台电脑连接同一局域网，学校、届数、班级配置必须完全一致。
2. 两台电脑都运行一次 allow_firewall.bat。
3. 先启动接收端，再启动发送端，等待约 3 秒。
4. 自动发现同时使用 UDP 广播和局域网组播，并以实际来源 IP 为准。
5. 如果仍无法发现，请检查无线路由器是否启用了 AP 隔离/客户端隔离。

故障排查
- send.exe 启动异常：查看 EXE 同目录的 send_error.log。
- display.exe 异常：查看 EXE 同目录的 display_error.log。
- build_exe.bat 失败：使用 run_pyw.bat 的 debug-send/debug-display 选项。
- 旧 EXE 正在运行时，build_exe.bat 会只关闭本项目 dist 目录中的旧程序。
