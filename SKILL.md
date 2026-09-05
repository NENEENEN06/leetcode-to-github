---
name: leetcode-to-github
description: 把用户提供的 LeetCode 题目和代码整理成规范的中文 Markdown 题解，保存到本地 Git 仓库并提交到 GitHub。适用于整理刷题笔记、生成题解、分析用户代码、同步 LeetCode 记录到 GitHub；不用于其他 GitHub 操作。
---

# LeetCode to GitHub

把用户发来的 LeetCode 题目和代码整理成统一、可长期复习的中文 Markdown 题解，保存到本地 Git 仓库，并在用户明确允许后提交和推送到 GitHub。

## 核心原则（始终遵守）

1. **用户代码最重要。** 原样保存，不修改、不重新格式化、不替换成"更优"代码；仅正确标注语言。
2. **记录用户的真实解法。** 思路、复杂度、总结都基于用户实际代码，不擅自改写为另一个算法。
3. **诚实判断正确性。** 能确定就说明结论；不能确定就写"无法确定"；只有实际运行过代码，才能声称"通过编译/测试"。
4. **发现问题要指出，但不擅自改。** 明确指出问题、分析原因、给出修改建议；未经允许绝不修改用户原始代码。
5. **默认不自动 push。** 只有用户明确说"推送"或"提交到 GitHub"时才 push；commit 也应在展示修改并得到确认后进行（除非用户说"整理并提交"）。

## 工作流程

按顺序执行：

1. 收集信息
2. 确认仓库与目录约定
3. 分析用户代码
4. 生成题解与保存代码
5. 重复题检测
6. 更新索引
7. 展示修改、等待确认
8. 提交并推送（在允许范围内）

## 1. 收集信息

从用户消息提取：题目编号、标题、链接、难度、标签、题目描述、代码及语言。可选项：解题思路、卡点、复盘。

- 只追问缺失且确实影响结果的字段；用户已提供的信息不要重复索要。
- 至少要拿到题目编号或链接（用于生成文件名）和代码（用于分析与保存）。
- 批量时先按"LeetCode <编号>"等分隔拆成多题，逐题处理，最后统一汇总。

## 2. 确认仓库与目录约定

- 先读 [config.yaml](config.yaml)，按其 `repository` / `structure` / `documentation` / `git` 配置执行。
- 在目标仓库目录内用 `git status`、`git remote -v`、`git branch --show-current` 核对状态，避免写错仓库或分支。
- 若 `repository.local_path` 未填写、目录不存在或 remote 与预期不符，先向用户确认并回填，不凭猜测写死仓库地址。
- 不要硬编码或提交 GitHub Token、密码等敏感信息。

## 3. 分析用户代码（核心）

按用户实际代码分析，必要时参考 [references/algorithms.md](references/algorithms.md) 和 [references/complexity.md](references/complexity.md)。

- **正确性**：判断逻辑、边界、数据结构使用。结论为"正确 / 存在问题 / 无法确定"三者之一，并说明理由。
- **思路**：归纳用户算法的核心思想、使用的数据结构、流程、关键状态/变量、为何能得到正确答案。
- **复杂度**：按实际代码逐块估算，而不是照搬理论最优复杂度。
- **易错点 / 复盘**：指出边界条件、常见坑、用户本次的卡点或错误。

若语言不明，按代码特征判断（C++ / Python / Java / JavaScript 等）。代码文件扩展名按 [config.yaml](config.yaml) 的 `extensions` 映射。

## 4. 生成题解与保存代码

- 用 [templates/solution.md](templates/solution.md) 生成单题目录下的 `README.md`。
- 目录名：`{四位题号}-{kebab-case 标题}`，如 `0001-two-sum`、`0053-maximum-subarray`。
- 代码文件：`solution.<扩展名>`，按语言自动确定（C++ → `.cpp`、Python → `.py`、Java → `.java`、JavaScript → `.js`）。
- 用户代码**原样**写入代码文件，不重新格式化。
- 题目描述简要概括，不要大段复制 LeetCode 原文。
- 语言以中文为主，保留英文术语；遵守 `documentation` 配置。

## 5. 重复题检测（防覆盖）

生成前先检查目标目录是否已存在。

- 若不存在：正常生成。
- 若已存在：列出已存在的目录和文件；检测到新代码时，询问用户是否更新现有解法。得到确认后再修改；更新时用 `refactor` 提交信息。

## 6. 更新索引

- 运行 `python scripts/generate_index.py --repo <仓库路径>` 自动生成/更新根目录 `README.md` 的题目索引表；或按 [templates/index.md](templates/index.md) 手动更新。
- 索引表用 `<!-- leetcode-index:start -->` 与 `<!-- leetcode-index:end -->` 标记，脚本会保留标记外的内容。

## 7. 展示修改、等待确认

提交前用 `git status` 和文件差异向用户展示将要提交的内容，说明生成/修改了哪些文件。默认等待用户确认后再 commit；用户说"整理并提交"时，可在完成检查后直接 commit。

## 8. 提交与推送（安全边界）

- commit 信息：新增用 `feat(leetcode): add {四位题号} {标题}`；更新用 `refactor(leetcode): improve {四位题号} {标题}`。不要用 `update`、`test`、`changes` 等无意义信息。
- 只 `git add` 本次生成的题解目录和索引文件，不混入无关改动。
- 不提交密钥、Token、凭据、大文件或用户未明确要求的内容；提交前可用 `python scripts/validate.py --repo <仓库路径>` 校验。
- push 前核对 `git remote -v` 和当前分支。`auto_push` 为 false 时，只有用户明确说"推送 / 提交到 GitHub"才 push。失败时报告原因，不反复重试或改用无关手段。

## 9. 批量处理与学习知识库

- 一次多题时逐题处理，最后汇总"本次整理"清单与总题数。
- 在每题 README 中沉淀算法模式（pattern）、数据结构、易错点（mistakes）、关键洞察（key_insight），便于以后用 `generate_index.py` 或检索仓库来回答"我刷过哪些动态规划题"等问题。

## 脚本

- `scripts/validate.py`：校验目录命名、README 模板、solution 文件、重复题号、敏感信息、Markdown 基本格式。
- `scripts/generate_index.py`：自动生成/更新根目录 README 的题目索引。

用法详见 [README.md](README.md)。

## 边界

本 skill 只负责"整理 LeetCode 题解为 Markdown 并提交到 GitHub"。不处理其他 GitHub 操作、其他平台题目或题库整理，除非用户在同一请求中明确要求。
