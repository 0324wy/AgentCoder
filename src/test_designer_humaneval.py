import json
from tqdm import tqdm
import copy
from openai import OpenAI
from constant_value import API_KEY, HUMAN_EVAL_DATASET_PATH, HUMAN_EVAL_TEST_PROMPT_PATH
from process_data import preprocess_data

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time

client = OpenAI(api_key=API_KEY)

def fetch_completion(construct_few_shot_prompt, data_entry, model, times=1):
    if "need_reproduce" in data_entry.keys() and not data_entry["need_reproduce"]:
        return data_entry

    prompt = data_entry["prompt"]
    # TODO
    entry_point = data_entry["entry_point"]

    text = f"""
    {construct_few_shot_prompt}

    **Input Code Snippet**:
    ```python
    {prompt}
    ```
    """
    test_case_list = []
    for i in range(times):
        while True:
            try:
                completions = client.chat.completions.create(
                    model=model,
                    stream=False,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a code developer assistant.",
                        },
                        {"role": "user", "content": text},
                    ],
                    timeout=100,
                    temperature=0,
                )
                test_case = completions.choices[0].message.content
                # if data_entry["task_id"] == "HumanEval/17":
                #     print(test_case)
                test_case = preprocess_data(test_case)
            except Exception as e:
                time.sleep(20)
                print(e)
                test_case = ""
            if test_case != "":
                break
        test_case_list.append(test_case)
    data_entry["test_case_list"] = test_case_list
    return data_entry


def call_fetch_test_completion_helper(dataset, model, lg):
    print("Fixing bug...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_entry = {
            executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry
            for entry in tqdm(dataset)
        }
        for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))
    return dataset


if __name__ == "__main__":
    # TODO: decompose model list to script
    model_list = ["gpt-3.5-turbo-1106"]
    # TODO
    language = ["python"]

    with open(HUMAN_EVAL_TEST_PROMPT_PATH, "r") as f:
        construct_few_shot_prompt = f.read()

    for model in model_list:
        for lg in language:
            
            # TODO: dataset is split test data
            with open(HUMAN_EVAL_DATASET_PATH, "r") as f:
                dataset = json.load(f)
            dataset = [entry for entry in dataset]
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_entry = {
                    executor.submit(
                        fetch_completion,
                        construct_few_shot_prompt,
                        copy.deepcopy(entry),
                        model,
                    ): entry
                    for entry in tqdm(dataset)
                }
                for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
                    entry = future_to_entry[future]
                    try:
                        updated_entry = future.result()
                        idx = dataset.index(entry)
                        dataset[idx] = updated_entry
                    except Exception as e:
                        print(repr(e))

            with open(HUMAN_EVAL_DATASET_PATH, "w") as f:
                json.dump(dataset, f, indent=4)
