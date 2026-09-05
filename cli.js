#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const pkg = require('./package.json');

// 从 GitHub 通过 npx 安装/执行的规范用法。
const GITHUB_SPEC = 'github:NENEENEN06/leetcode-to-github';

// 支持的 Agent 及其 skills 目录约定。
const AGENTS = {
  codex: {
    label: 'Codex',
    env: 'CODEX_HOME',
    envRel: ['skills'],
    homeRel: ['.codex', 'skills'],
  },
  claude: {
    label: 'Claude Code',
    env: 'CLAUDE_CONFIG_DIR',
    envRel: ['skills'],
    homeRel: ['.claude', 'skills'],
  },
};

// 需要安装到 skills 目录的文件/目录（npm 打包文件和 .git 等不复制）。
const EXCLUDE = new Set([
  'package.json',
  'package-lock.json',
  'cli.js',
  'node_modules',
  '.git',
  '.idea',
  '.agents',
  '.codex',
  '.claude',
]);

// 检测当前机器上已安装（或通过环境变量指向）的 Agent。
function detectInstalledAgents() {
  const found = [];
  for (const [id, spec] of Object.entries(AGENTS)) {
    if (process.env[spec.env]) {
      found.push(id);
      continue;
    }
    const dir = path.join(os.homedir(), ...spec.homeRel);
    if (fs.existsSync(dir)) found.push(id);
  }
  return found;
}

// 根据 Agent 约定计算 skills 目录。
function agentDest(agent) {
  const spec = AGENTS[agent];
  if (!spec) return null;
  const env = process.env[spec.env];
  if (env) return path.join(env, ...spec.envRel, pkg.name);
  return path.join(os.homedir(), ...spec.homeRel, pkg.name);
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (EXCLUDE.has(entry.name)) continue;
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(from, to);
    } else {
      fs.copyFileSync(from, to);
    }
  }
}

function showHelp() {
  const agents = Object.keys(AGENTS).join('|');
  console.log(`\n${pkg.name} v${pkg.version}\n把 leetcode-to-github 技能安装到所用 Agent。\n
用法（从 GitHub 经 npx 执行）:
  npx ${GITHUB_SPEC}                      自动检测已安装的 Agent 并安装（优先 Codex）
  npx ${GITHUB_SPEC} --agent ${agents}    安装到指定 Agent 的 skills 目录
  npx ${GITHUB_SPEC} --dest <目录>        安装到任意目录（任何 Agent 通用）
  npx ${GITHUB_SPEC} --help               显示帮助
  npx ${GITHUB_SPEC} --version            显示版本\n`);
}

function parseArgs(args) {
  const get = (opt) => {
    const i = args.indexOf(opt);
    return i !== -1 && args[i + 1] ? args[i + 1] : null;
  };
  return {
    agent: get('--agent'),
    dest: get('--dest'),
    help: args.includes('--help') || args.includes('-h'),
    version: args.includes('--version') || args.includes('-v'),
  };
}

function install(dest, label) {
  const src = __dirname;
  if (fs.existsSync(dest) && fs.statSync(dest).isDirectory()) {
    const backup = `${dest}.bak-${Date.now()}`;
    fs.renameSync(dest, backup);
    console.log(`检测到已有安装，已备份到 ${backup}`);
  }
  copyDir(src, dest);
  console.log(`✅ 已安装 ${pkg.name} v${pkg.version} 到 ${label}`);
  console.log('   重启对应 Agent 后即可使用：直接提及技能名 "leetcode-to-github"（Codex 亦可写 $leetcode-to-github）。');
}

function main() {
  const { agent, dest, help, version } = parseArgs(process.argv.slice(2));
  if (help) return showHelp();
  if (version) return console.log(pkg.version);

  if (dest) {
    const destPath = path.resolve(dest);
    install(destPath, `自定义目录 ${destPath}`);
    return;
  }

  if (agent) {
    const targetAgent = agent.toLowerCase();
    if (!AGENTS[targetAgent]) {
      console.error(`未知 Agent：${targetAgent}。支持 ${Object.keys(AGENTS).join(', ')}，或用 --dest 指定目录。`);
      process.exit(1);
    }
    const p = agentDest(targetAgent);
    install(p, `${AGENTS[targetAgent].label}（${p}）`);
    return;
  }

  const found = detectInstalledAgents();
  if (found.length === 0) {
    console.error('未检测到已安装的 Agent。请用 --agent codex|claude 或 --dest <目录> 指定安装位置。');
    process.exit(1);
  }
  const picked = found.includes('codex') ? 'codex' : found[0];
  const p = agentDest(picked);
  install(p, `${AGENTS[picked].label}（${p}）`);
}

main();
