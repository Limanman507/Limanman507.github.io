# Limanman 的博客

网站：https://limanman507.github.io

## 首次启用

在仓库 Settings → Pages → Build and deployment，将 Source 设为 **GitHub Actions**。
在 Actions 中查看 Publish blog。首次因 Pages 尚未启用而失败，启用后点 Re-run all jobs。

## 写文章和发布

1. 在 docs/ 中新建或编辑 .md 文件，例如 02.md 或 2026-11-03-learning.md。
2. 使用 # 文章标题，系统取第一个一级标题作为目录标题；没有一级标题时使用文件名。
3. 图片放在 docs/images/，文章引用 ![说明](images/example.png)。使用相对路径。
4. 保存后双击 publish.cmd。需要配置好 Git 用户身份和 GitHub SSH 登录。
5. 等待仓库 Actions 显示成功，再打开网站。

首页自动收集 docs 下的 Markdown，按文件路径倒序排列。推荐使用日期开头的文件名。
已有 YAML front matter 的文章保留其配置，可用 title 设置目录标题。
构建脚本只在临时构建目录添加元数据，不会修改原始文章。

publish.cmd 会提交博客目录中的改动并推送到 main。请只把准备公开的文章放进 docs。
本地无需安装 Ruby、Jekyll 或 Python，日常发布仅使用 Git 和 Windows PowerShell。
