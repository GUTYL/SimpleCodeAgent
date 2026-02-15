import os
import json
import subprocess

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
MODEL = os.getenv("MODEL_NAME", "gpt-4o")

WORKDIR = os.path.join(os.getcwd(), "action")
os.makedirs(WORKDIR, exist_ok=True)

SYSTEM_PROMPT = f"""你是一个代码助手 Agent。你可以通过工具来读写文件、执行命令和浏览目录结构。
所有操作都在工作目录 {WORKDIR} 下进行，文件路径均为相对于该目录的相对路径。
请根据用户的需求，合理调用工具来完成任务。每次操作后观察结果，决定下一步行动。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定路径的文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入指定路径的文件，如果目录不存在会自动创建",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行 shell 命令并返回输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的文件和子目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径，默认为当前目录", "default": "."},
                },
                "required": [],
            },
        },
    },
]


def _resolve(path: str) -> str:
    """将相对路径解析为 WORKDIR 下的绝对路径。"""
    if os.path.isabs(path):
        return path
    return os.path.join(WORKDIR, path)


def read_file(path: str) -> str:
    path = _resolve(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"错误: {e}"


def write_file(path: str, content: str) -> str:
    path = _resolve(path)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入 {path}（{len(content)} 字符）"
    except Exception as e:
        return f"错误: {e}"


def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30,
            cwd=WORKDIR,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[返回码: {result.returncode}]"
        return output or "(无输出)"
    except subprocess.TimeoutExpired:
        return "错误: 命令执行超时（30秒）"
    except Exception as e:
        return f"错误: {e}"


def list_files(path: str = ".") -> str:
    path = _resolve(path)
    try:
        entries = []
        for root, dirs, files in os.walk(path):
            # 跳过隐藏目录和常见的无关目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]
            level = root.replace(path, "").count(os.sep)
            indent = "  " * level
            entries.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = "  " * (level + 1)
            for file in files:
                entries.append(f"{sub_indent}{file}")
        return "\n".join(entries)
    except Exception as e:
        return f"错误: {e}"


TOOL_MAP = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_files": list_files,
}


def execute_tool(name: str, arguments: dict) -> str:
    func = TOOL_MAP.get(name)
    if not func:
        return f"未知工具: {name}"
    return func(**arguments)


def chat(user_input: str, messages: list) -> str:
    messages.append({"role": "user", "content": user_input})

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"  🔧 {name}({args})")
            result = execute_tool(name, args)
            print(f"  ✅ 完成")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


def main():
    print(f"Code Agent 已启动（工作目录: {WORKDIR}）")
    print("输入 exit 退出")
    print("-" * 40)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("再见！")
            break

        reply = chat(user_input, messages)
        print(f"\nAgent: {reply}")


if __name__ == "__main__":
    main()
