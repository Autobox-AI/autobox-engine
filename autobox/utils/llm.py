from openai.types.chat import ChatCompletion


def extract_chat_completion(completion: ChatCompletion):
    tool_calls = completion.choices[0].message.tool_calls
    extracted_tool_calls = []
    if tool_calls is not None and len(tool_calls):
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            extracted_tool_calls.append(
                {"function_name": function_name, "arguments": arguments}
            )
    else:
        return completion.choices[0].message.content, False

    return extracted_tool_calls, True
