# main.py
from agent import Agent

if __name__ == "__main__":
    agent = Agent()
    print("🤖 AI Agent 启动！输入 'quit' 退出。\n")
    
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        reply = agent.chat(user_input)
        print(f"🧠 Agent: {reply}\n")