' daemon_cloudflared.vbs — Cloudflare Tunnel 静默守护进程
' 无限循环：隐藏窗口运行 cloudflared，崩溃后 5 秒自动重启
' 用法：wscript.exe daemon_cloudflared.vbs
' 配合 Task Scheduler 实现开机自启（无需管理员）

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 工作目录 — 根据老电脑实际情况修改
workDir = "E:\amechan-daily"
logFile = workDir & "\daemon_cloudflared.log"

Sub WriteLog(msg)
    On Error Resume Next
    Set log = fso.OpenTextFile(logFile, 8, True)
    log.WriteLine Now & " " & msg
    log.Close
End Sub

WriteLog "=== daemon_cloudflared 启动 ==="

Do
    WriteLog "启动 cloudflared tunnel..."
    ' 0 = 隐藏窗口, True = 等待进程退出
    returnCode = WshShell.Run("cmd /c cd /d " & workDir & " && cloudflared tunnel --config config.yml run >> " & logFile & " 2>&1", 0, True)
    WriteLog "进程退出 (code=" & returnCode & ")，5秒后重启..."
    WScript.Sleep 5000
Loop
