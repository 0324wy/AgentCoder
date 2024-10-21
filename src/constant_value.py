# API_KEY = ''

API_KEY = ''

model = "gpt-3.5-turbo-1106"

MBPP_PROGRAMMER_PROMPT_PATH = "../prompts/mbpp_prompt_update.txt"
MBPP_TEST_PROMPT_PATH = "../prompts/test_designer_mbpp_prompt_update.txt"
MBPP_DATASET_PATH = f"../dataset/{model}_mbpp_temp01.json"
MBPP_PATH_WITH_SUFFIX = MBPP_DATASET_PATH.replace(".json", "_test.json")

HUMAN_EVAL_PROGRAMMER_PROMPT_PATH = "../prompts/humaneval_prompt_update.txt"
HUMAN_EVAL_DATASET_PATH = f"../dataset/{model}_humaneval_temp01.json"
HUMAN_EVAL_TEST_PROMPT_PATH = "../prompts/test_designer_humaneval_prompt_update.txt"

# test