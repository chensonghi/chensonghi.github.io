
日常维护你可以按“只维护 Hugo 源码、让 Actions 自动发布”的思路来。

写新文章

新建目录：site/content/posts/文章名/
index.md
图片/附件：直接丢在同目录（和 index.md 同级），正文里用 ![](./xxx.png) 引用
建议：正文里在合适位置加 <!--more-->，这样首页显示摘要不乱
本地预览

在仓库目录运行：cd /Users/chleynx/Desktop/code/chleynx-blog/chensonghi.github.io
启动：hugo server --source site -D
访问：http://localhost:1313/
修改站点配置/菜单/社交链接

hugo.toml
主题：site/themes/archie（submodule，尽量别直接改主题源码；要改样式更推荐加自定义 CSS/覆盖 layouts）
发布上线（最常用流程）

git add -A && git commit -m "new" && git push
GitHub Actions 会自动构建并部署到 Pages（你现在已经是这个模式）
更新主题（偶尔做）

cd site/themes/archie && git pull origin master（或主题的默认分支）
回到仓库根目录提交 submodule 更新：git add site/themes/archie && git commit -m "Update theme" && git push
备份/迁移电脑

只要保留这个仓库（含 site/ 和 submodule），新电脑装 Hugo 后一样能跑