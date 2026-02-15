# Code Agent

最简洁的 LLM 驱动代码助手。基于 Python + OpenAI 兼容接口，通过 ReAct 循环实现文件读写和命令执行。

## 快速开始

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key、Base URL 和模型名称

# 启动（uv 自动创建虚拟环境并安装依赖）
uv run agent.py
```

## 配置

在 `.env` 中设置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | API 密钥 | 无（必填） |
| `OPENAI_BASE_URL` | API 地址，兼容任何 OpenAI 格式的接口 | `https://api.openai.com/v1` |
| `MODEL_NAME` | 模型名称 | `gpt-4o` |

## 内置工具

| 工具 | 参数 | 作用 |
|------|------|------|
| `read_file` | `path` | 读取文件内容 |
| `write_file` | `path`, `content` | 写入文件（自动创建目录） |
| `run_command` | `command` | 执行 shell 命令（30s 超时） |
| `list_files` | `path`（默认 `.`） | 列出目录树 |

## 使用示例

```
你: 帮我创建一个 hello.py，内容是打印 hello world
  🔧 write_file({"path": "hello.py", "content": "print('hello world')"})
  ✅ 完成
Agent: 已创建 hello.py 文件。

你: 运行 python hello.py
  🔧 run_command({"command": "python hello.py"})
  ✅ 完成
Agent: 运行结果：hello world

你: exit
再见！
```

## 架构

单文件 ReAct 循环：

```
用户输入 → LLM 思考 → 调用工具 → 观察结果 → 继续/返回
```

所有逻辑集中在 `agent.py` 一个文件中，约 200 行代码。
