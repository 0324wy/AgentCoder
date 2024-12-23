import argparse
import os
import json
from tqdm import tqdm
import copy
from openai import OpenAI
from constant_value import API_KEY, MBPP_DATASET_PATH, MBPP_PATH_WITH_SUFFIX, MBPP_TEST_PROMPT_PATH
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from datasets import load_dataset
from process_data import extract_fun_name_and_parameters

client = OpenAI(api_key=API_KEY)

def preprocess_data(test_case_string):
    if f"```python" in test_case_string:
        test_case_string = test_case_string[
            test_case_string.find(f"```python") + len(f"```python") :
        ]
        test_case_string = test_case_string[: test_case_string.find("```")]
    return test_case_string


def fetch_completion(construct_few_shot_prompt, data_entry, model, lg, times=5):
    if "need_reproduce" in data_entry.keys() and not data_entry["need_reproduce"]:
        return data_entry
    prompt = data_entry["prompt"]
    test_case_0 = data_entry["test_list"][0]
    function_name = extract_fun_name_and_parameters(test_case_0)

    text = f"""
    {construct_few_shot_prompt}

    **Input Code Snippet**:
    ```python
    {prompt}
    ```
    
    **Function Name and the Example of Parameters**:
    ```python
    {function_name}
    ```
    """
    
    # print(text)
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
                )
                test_case = completions.choices[0].message.content
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
    model_list = ["gpt-3.5-turbo-1106"]
    language = ["python"]
    
    with open(MBPP_TEST_PROMPT_PATH, "r") as f:
        construct_few_shot_prompt = f.read()
    
    with open(MBPP_DATASET_PATH, "r") as f:
        dataset = json.load(f)
    dataset = [entry for entry in dataset]
    
    for model in model_list:
        for lg in language:
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_entry = {
                    executor.submit(
                        fetch_completion, construct_few_shot_prompt, copy.deepcopy(entry), model, lg
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

            with open(MBPP_DATASET_PATH, "w") as f:
                json.dump(dataset, f, indent=4)
