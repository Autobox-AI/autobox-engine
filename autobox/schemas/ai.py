from enum import Enum

DEFAULT_PROMPT = "default"


class OpenAIModel(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4O_2024_08_06 = "gpt-4o-2024-08-06"
    GPT_4_5_PREVIEW = "gpt-4.5-preview"
    O3_MINI = "o3-mini"
    O1_PREVIEW = "o1-preview"
    GPT_5_NANO = "gpt-5-nano"
    O4_MINI = "o4-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
