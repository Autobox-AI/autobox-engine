def prompt(task: str, agents: str) -> str:
    return f"""<objective>
Your are an expert history summarizer. Your job is to summarize the conversation history between the agents which have been interacting with each other in order to achieve a task objective.
</objective>

<task objective>
${task}
</task objective>

<agents>
${agents}
</agents>


<output>
You should output the best summary as text.
</output>
  """
