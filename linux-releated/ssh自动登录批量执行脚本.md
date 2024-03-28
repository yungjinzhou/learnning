ssh自动登录后，执行对应脚本



```
#!/usr/cmd/expect

set username "root"
set password "comleader@123"

# 机器列表
set machines {
    "192.168.8.79"
    "192.168.8.69"
    "192.168.8.68"
}

foreach machine $machines {
    spawn ssh $username@$machine

    expect {
        "*password:" {
            send "$password\r"
            exp_continue
        }
        "yes/no" {
            send "yes\r"
            exp_continue
        }
        "*$username*" {
            # 成功登录后，匹配到提示符后发送命令
          #  send "echo Hello, I'm connected to $machine\r"
            send "/usr/bin/bash /root/clear_all_containers.sh\r"
   #  send "echo done\r"
            # 添加更多需要执行的命令
          #  send "exit\r"
            expect eof
        }
    }
}
```