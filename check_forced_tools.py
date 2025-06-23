import asyncio

from app.agent.manus_core import Manus


async def check_forced_tools():
    agent = await Manus.create()
    agent.original_user_request = (
        "review sketchxpress.tech and write a comprehensive report on the future"
    )

    # Generate forced tools to see what they look like
    tools = agent._generate_forced_multi_task_tools(agent.original_user_request)

    print("Generated tools:")
    for i, tool in enumerate(tools):
        print(f"Tool {i+1}: {tool.function.name}")
        if hasattr(tool.function, "parameters"):
            params = tool.function.parameters
            print(f"Parameters: {list(params.keys())}")
            if "code" in params:
                print(f'Code:\n{params["code"]}\n')
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(check_forced_tools())
