# chensonghi.github.io

此仓库正在迁移为 Hugo 博客（参考风格：Hugo + [athul/archie](https://github.com/athul/archie)）。

## Hugo 源码

Hugo 站点源码位于 `site/`。

## 本地预览

```bash
brew install hugo
hugo server --source site -D
```

## 构建

```bash
hugo --source site --minify
```

产物输出到 `site/public/`（已在 `.gitignore` 中忽略）。

## GitHub Pages 部署（推荐）

仓库已包含 GitHub Actions 工作流：`.github/workflows/hugo-pages.yml`。

在 GitHub 仓库 Settings → Pages：将 Source 选择为 **GitHub Actions**。
