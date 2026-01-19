---
title: 闭包提权(Closure-Privilege-Escalation)
date: 2024-06-12 00:22:51
tags: ["2024"]
categories: ["Summary"]
---

## 闭包提权：

```
var o = (function() {
    var obj = {
        a: 1,
        flag: "flag{test}",
    };
    return {
        get: function(k) {
            return obj[k];
        },
        add: function() {
            n++;
        }
    };
}
)();

console.log(o.get("flag"))  // flag{test}
```

首先，这里通过闭包实现了将obj这个对象让外面不可更改。实现只读的效果。

作用：比如在有些环境下，如第三方库当中，需要保持稳定性，防止一个库被另一个库修改。



利用：

```

console.log(o.get("valueOf"))  //[Function: valueOf]

console.log(o.get("valueOf")())  // TypeError: Cannot convert undefined or null to objec
// 由于valueOf是Object.prototype的方法，所以在调用时，this指向的是Object.prototype，而Object.prototype并没有flag属性，所以会报错


//定义一个原型，让obj[k]能拿到这个原型，然后返回this指向obj
Object.defineProperty(Object.prototype, "hacker", {
    get: function() {
        return this;
    }
});
console.log(o.get("flag")) // flag{test}

console.log(o.get("hacker"))  // { a: 1, flag: 'flag{test}' }
let obj1 = o.get("hacker");
obj1.flag = 2;

console.log(o.get("flag"))  // 2

if (o.get("flag") !== "flag{test}") {
    console.log("flag is correct!");
}
// flag is correct!
```

利用成功

防御的方法：

```
//防御1
var o = (function() {
    var obj = {
        a: 1,
        flag: "flag{test}",
    };
    Object.setPrototypeOf(obj, null);
    return {
        get: function(k) {
            return obj[k];
        },
    };
}
)();


//防御2,如果obj要使用它的原型的话可以用以下方法
var o = (function() {
    var obj = {
        a: 1,
        flag: "flag{test}",
    };
    // Object.setPrototypeOf(obj, null);
    return {
        get: function(k) {
            if(obj.hasOwnProperty(k)){
                return obj[k];
            }
        },
    };
}
)();

```

