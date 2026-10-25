# M1racle Visual Director — 快速安装执行契约

适用于拿到 `https://github.com/ldohgfsdu/m1racle-visual-director` 进行安装或更新的 Codex、Claude Code、OpenCode、CodeBuddy、WorkBuddy 等终端 Agent。

## 0. 绝对限制

- **禁止自动执行 `git clone`（包括浅克隆、代理克隆）**；它只可在用户**另外明确要求**克隆源码时执行，不能作为安装失败回退。
- **禁止 60～150 秒甚至无限时网络重试**。优先短时检查、失败即停；严禁反复探测大量域名。
- **禁止将 `scripts/install.py` 说成“快速联网安装器”**；它仅复制已存在的本地仓库。`scripts/quick_install.py` 才是无 Git 的有界 ZIP 下载安装器。
- **禁止要求用户先安装 Node.js、Git 或额外依赖**。已有 Python 3.9+ 足够。
- 安装验收不必跑 `scripts/test_install.py`、`scripts/test_quick_install.py`。这些是 CI 开发测试，不是用户安装验证。
- **禁止声称能将技能注册到 WorkBuddy 手机 App**。本流程只影响执行环境的 skills 文件目录。`scripts/package_workbuddy.py` 不存在，禁止建议该功能。
- 不应单凭环境变量里的代理地址认定它真正能访问 GitHub，也不能把云端 `127.0.0.1` 当成用户本地代理。

## 1. 确定目标和安装意图

识别运行时**实际** skills 扫描路径；若 CodeBuddy/WorkBuddy 声明 `~/.codebuddy/skills/` 为活动目录，优先使用 `--agent codebuddy`。

- 仅安装且本地已有有效 Skill：无需联网，先用本地 `scripts/quick_install.py --doctor`，或直接检查 `SKILL.md`、`references/`、`gallery/`；返回已安装。不要自动覆盖。
- 用户明确要求更新：用 `--force` 替换有效安装；安装器会做临时目录写入及回滚。
- 如果用户要求 App「我的技能」显示，不应继续把文件写进云沙箱冒充账号注册；报告产品侧功能限制。

## 2. 只下载一个小型启动脚本，短时失败

首先用已有 HTTP 客户端（例如 curl、PowerShell）从以下官方源取约 10 KB 脚本：
`https://raw.githubusercontent.com/ldohgfsdu/m1racle-visual-director/main/scripts/quick_install.py`

**单次 5 秒连接超时、10 秒总超时，禁止多次重复尝试相同失效路径。**

官方源不可达时，不要 `git clone`。优先使用环境里已经被**实际证明可达**的受信任 HTTP(S) 代理。如果只能通过第三方 GitHub 镜像访问，**必须得到用户对第三方镜像的许可**，且明确告诉用户代理可以接触下载内容。

这个运行环境此前曾报告 `ghproxy.net` 可获取 raw 文件，但**不能推导它永远在线、也不能推导 ZIP 地址一定可用**。用户授权后，可尝试：
`https://ghproxy.net/https://raw.githubusercontent.com/ldohgfsdu/m1racle-visual-director/main/scripts/quick_install.py`

代理下载的脚本应按已有可信来源的哈希校验（若提供）；没有可信哈希时，不要宣称下载来源获得密码学验证。不允许自动改用任何其他未知第三方站点。

## 3. ZIP 安装，绝不回退到 git clone

脚本拿到后运行（CodeBuddy 示例；替换为真实 Agent）：

```sh
python /tmp/m1racle-quick-install.py --agent codebuddy --force --timeout 8 --max-seconds 24
```

若用户**已许可**且已验证第三方代理提供的是合法 GitHub ZIP，可用 `--mirror-url` 明确指定完整 ZIP URL：

```sh
python /tmp/m1racle-quick-install.py --agent codebuddy --force --mirror-url 'https://ghproxy.net/https://codeload.github.com/ldohgfsdu/m1racle-visual-director/zip/refs/heads/main' --timeout 8 --max-seconds 24
```

这些代理示例必须先验证此环境确实能下载 ZIP；只验证 raw 脚本 200 并不够。脚本会检查 ZIP 基本结构和必要文件；不保证第三方代理内容可信。ZIP 不可用就停下来报告，不要改回 `git clone --depth 1`。

已经有经核验的本地 ZIP 时更快，直接 `--archive-file <本地ZIP>`，完全不联网。

## 4. 最小验收与输出

在**实际安装目标目录**运行（不必为了验证重新克隆）：
- `python <实际安装目录>/scripts/validate_skill.py`
- `python <实际安装目录>/scripts/verify_gallery.py`
- 验证 `SKILL.md` 的 `metadata.version`、`name` 与实际目录。

只报告：是否成功、版本、真实安装路径、使用的下载渠道、是否第三方代理、总执行耗时和真实加载是否已验证。**没有真实加载记录则记为未验证**；不要说已在 App 安装或账号同步。

## 5. 失败策略

首选官方源和**用户已批准**的代理均失效：快速停止并说明具体失败点，建议用户提供可信 HTTPS 镜像或者本地 ZIP。**禁止为追求成功无限等待、自动授权第三方镜像或重试整个流程**。
