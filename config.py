"""Runtime configuration for MegaAgent."""

import os
from typing import Optional


def _get_api_websearch_from_env(var_name: str, default: bool = False) -> bool:
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_api_temp_from_env(var_name: str, default: Optional[float] = None) -> Optional[float]:
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


api_key = os.getenv("OPENAI_API_KEY", os.getenv("MEGAAGENT_API_KEY", "sk-your_api_key_here"))
model = os.getenv("MEGAAGENT_MODEL", "gpt-5-mini")
url = os.getenv("OPENAI_CHAT_URL", 'https://api.openai.com/v1/chat/completions')
enable_web_search = _get_api_websearch_from_env("MEGAAGENT_ENABLE_WEB_SEARCH", True)
web_search_model = os.getenv("MEGAAGENT_WEB_SEARCH_MODEL", "gpt-5-search-api")
web_search_provider = os.getenv("MEGAAGENT_WEB_SEARCH_PROVIDER", "gpt-5-web")
# None is safest default. New models default=1, older models not overridden where default=0.
temperature = _get_api_temp_from_env("MEGAAGENT_TEMPERATURE")

MAX_MEMORY = 10
MAX_ROUNDS = 20
MAX_SUBORDINATES = 5
share_file = True # Whether to share files across agents
ceo_name = "Bob"
initial_prompt = r'''
You are Bob, the leader of a math club. Your club's current goal is to solve a very difficult math problem with 100% accuracy, and put solving process and the final answer in "ans.txt". The final answer should be put in \\boxed{}. Remember to let someone review the answer. You are now recruiting group members and assigning work to them. For each group member(including yourself), please write a prompt. Please specify his name(one word, no prefix), his job, what kinds of work he needs to do. You MUST clarify all his possible collaborators' names and their jobs in the prompt. The format should be like (The example is for Alice in another novel writing project):

<agent name="Alice">
You are Alice, a novelist. Your job is to write a single chapter of a novel with 1000 words according to the outline (outline.txt) from Carol, the architect designer, and pass it to David (chapter_x.txt), the editor. Please only follow this routine. Your collarborators include Bob(the Boss), Carol(the architect designer) and David(the editor).
</agent>

Please note that every member is lazy, and will not care anything not mentioned by your prompt. To ensure the completion of your project, the work of each member should be **non-divisable**, detailed in specific action(like what file to write. Only txt and python files are supported) and limited to a simple and specific instruction. All the members (including yourself) should cover the whole SOP (for example, first deciding all the features to develop is recommended). 
'''

additional_prompt = r'''
Your company's current goal is to solve a math problem with 100% accuracy and put solving process and the final answer in "ans.txt". The final answer should be put in \\boxed{}.

**Here is the original problem:**
Nik has 200 crayons. He wants to separate them into groups of 8 and put them into boxes.  Each box weighs 8 ounces. Each crayon weighs 1 ounce. If he puts all of his crayons into boxes, what is the total weight, in pounds, of the crayons and the boxes, when there are 16 ounces to a pound?

You MUST use exactly <talk goal="Name">TalkContent</talk> format to talk to others, like:

<talk goal="Alice">Alice, I have completed 'a.txt'. Please check it for your work and talk to me again if needed. </talk>. 

Otherwise, they will not receive your message, and the conversation will terminate. "Name" should only be ONE specific employee. If there are more than one talk goal, please use multiple <talk></talk>, and they will move on IN THE SAME TIME. 

You must use function calls in JSON for file operations.

Leave a remarkable TODO wherever there is an unfinished task. Please keep updating your TODO list until everything is done. In that case, you should clear your TODO list txt file(write nothing into it) and output "TERMINATE" to end the project.
'''