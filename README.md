# leetcode-to-github

把 LeetCode 题目和代码整理成规范、可长期复习的中文 Markdown 题解，保存到本地 Git 仓库并提交到 GitHub 的 Codex Agent Skill。

## 目录结构

```text
leetcode-to-github/
├── SKILL.md                 Skill 行为、工作流程、分析规则与 GitHub 操作规则
├── config.yaml             仓库、目录、文档、Git 与语言扩展名配置（无敏感信息）
├── README.md               本文件：安装、配置与使用说明
├── templates/
│   ├── solution.md         单题题解模板
│   └── index.md            仓库根目录索引模板
├── references/
│   ├── algorithms.md       常见算法模式参考
│   └── complexity.md       复杂度分析参考
└── scripts/
    ├── validate.py         校验目录/README/敏感信息/重复题号
    └── generate_index.py   生成/更新根目录题目索引
```

## 各文件作用

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 定义 Agent 触发后的行为：收集信息、分析用户代码、生成题解、防重复、提交推送等完整流程与安全边界 |
| `config.yaml` | 配置仓库 owner/name、本地路径、目录命名、文档语言、commit 模板、`auto_push` 等；用占位符，不硬编码 Token |
| `templates/solution.md` | 单题 `README.md` 模板，包含题目、我的思路、代码、代码分析、复杂度、易错点、总结、复盘 |
| `templates/index.md` | 仓库根 `README.md` 模板，带 `<!-- leetcode-index:start/end -->` 标记供脚本更新 |
| `references/algorithms.md` | 双指针、滑动窗口、二分、DP、DFS/BFS、栈、链表、树、图、贪心、前缀和、位运算等模式识别参考 |
| `references/complexity.md` | 时间/空间复杂度估算规范与常见来源 |
| `scripts/validate.py` | 校验目录命名、README 段落、solution 文件、重复题号、敏感信息、Markdown 围栏 |
| `scripts/generate_index.py` | 扫描题目目录并生成/更新根目录 README 的 Problems 表格 |

## 安装

把整个 `leetcode-to-github` 目录复制到 Codex 的 skills 目录即可：

```bash
# macOS / Linux
cp -r leetcode-to-github ~/.codex/skills/

# Windows PowerShell
Copy-Item -Recurse -Force leetcode-to-github "$env:USERPROFILE\.codex\skills\leetcode-to-github"
```

如果已经设置了 `CODEX_HOME`，则安装到 `$CODEX_HOME/skills/leetcode-to-github`。

安装后，对 Codex 说"整理 LeetCode 53"或 `$leetcode-to-github` 即可触发。

## 配置

编辑 [config.yaml](config.yaml)，至少填好：

```yaml
repository:
  owner: YOUR_GITHUB_USERNAME   # 改成你的 GitHub 用户名
  name: leetcode-solutions      # 改成你的仓库名
  root: ""                      # 题解放在仓库根目录；如放在 solutions/ 下填 solutions
  local_path: ""                # 本地克隆路径，例如 C:/Users/you/leetcode-solutions
  default_branch: main
```

不要把 GitHub Token、密码写进 `config.yaml`。认证交给 `git` 凭据助手或 `gh auth login`。

## 连接 GitHub

1. 在 GitHub 上创建一个空仓库，例如 `leetcode-solutions`。
2. 克隆到本地并填写 `config.yaml` 的 `local_path`：

   ```bash
   git clone https://github.com/<你的用户名>/leetcode-solutions.git
   ```

3. 用以下任一方式完成认证：
   - 已安装 GitHub CLI：`gh auth login`（推荐）
   - 或配置 Git 凭据助手：`git config --global credential.helper store` 后首次 push 输入 Token

之后 Agent 会先在 `local_path` 目录里核对 `git remote -v` 与分支，再执行提交。

## 第一次测试

1. 装好 skill 并填好 `config.yaml`。
2. 准备一个本地仓库（可为空克隆）。
3. 对 Codex 说：

   ```
   整理 LeetCode 53
   我的代码：
   ```cpp
   class Solution {
   public:
       int maxSubArray(vector<int>& nums) {
           int cur = nums[0], best = nums[0];
           for (int i = 1; i < nums.size(); ++i) {
               cur = max(nums[i], cur + nums[i]);
               best = max(best, cur);
           }
           return best;
       }
   };
   ```
   ```

4. Agent 会生成 `0053-maximum-subarray/README.md` 和 `solution.cpp`，更新根索引，展示修改并等待确认。
5. 运行校验脚本确认：

   ```bash
   python scripts/validate.py --repo <仓库路径> --config config.yaml
   ```

## 使用示例

**单题，仅整理（不提交）：**

> 整理 LeetCode 1，代码：...（粘贴代码）

Agent 生成 `0001-two-sum/`，更新索引，展示修改，等待你确认后才 commit，且默认不 push。

**单题，整理并提交：**

> 整理并提交 LeetCode 206，代码：...

Agent 完成检查后直接 commit（不 push，除非 `auto_push: true` 或你明确说"推送"）。

**批量整理：**

> 整理这些题：
> LeetCode 1
> 代码：...
>
> LeetCode 20
> 代码：...
>
> LeetCode 206
> 代码：...

Agent 依次生成三个目录，最后汇总：

```text
本次整理：
✓ 0001 Two Sum
✓ 0020 Valid Parentheses
✓ 0206 Reverse Linked List

共 3 道题。
```

**更新已存在的题：**

如果 `0053-maximum-subarray/` 已存在，Agent 会先告诉你已存在，并列出文件和检测到的新代码，询问"是否更新现有解法？"，确认后才修改，使用 `refactor(leetcode): improve 0053 maximum subarray` 作为提交信息。

## 脚本用法

```bash
# 校验仓库结构
python scripts/validate.py --repo <仓库路径> --config config.yaml

# 生成/更新根目录索引
python scripts/generate_index.py --repo <仓库路径> --config config.yaml
```

两个脚本只使用 Python 标准库，无第三方依赖。

## 安全说明

- 默认 `auto_push: false`，只有明确说"推送 / 提交到 GitHub"才 push。
- 用户代码原样保存，不修改、不替换；README 记录用户真实解法。
- 只有实际运行过代码才声称"通过编译/测试"；否则如实写"无法确定"。
- 提交前用 `validate.py` 检查敏感信息，不提交 Token/密钥/密码。
