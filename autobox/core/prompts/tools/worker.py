from typing import Dict


def get_tools(agents: Dict[str, str]):
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thinking_process": {
                            "type": "string",
                            "description": f"Explain step-by-step why the decision-making process requires {name} intervention.",
                        },
                        "task_status": {
                            "type": "string",
                            "description": "A summary of the task state resolution based on all agents' contributions. Max 50 words.",
                        },
                        "instruction": {
                            "type": "string",
                            "description": f"Instructions for the {name} agent to follow. This should be a clear instruction. It can be a question, a requirement, suggestion of any other action for contribution for the agent. Max 50 words.",
                        },
                    },
                    "required": ["thinking_process", "task_status", "instruction"],
                },
                "description": f"Call this function when you need to a collaboration and contribution from {name}. This function role is: {role}.",
            },
        }
        for name, role in agents.items()
    ]
