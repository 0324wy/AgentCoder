import json
from tqdm import tqdm
import copy
from openai import OpenAI
from constant_value import API_KEY, HUMAN_EVAL_PROGRAMMER_PROMPT_PATH, HUMAN_EVAL_DATASET_PATH

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from datasets import load_dataset
from process_data import preprocess_data

client = OpenAI(api_key=API_KEY)


def fetch_completion(construct_few_shot_prompt, data_entry, model, lg, times=1, api_dict=None):
    if "need_reproduce" in data_entry.keys() and not data_entry["need_reproduce"]:
        return data_entry

    prompt = data_entry["prompt"]

    text = f"""
    {construct_few_shot_prompt}

    **Input Code Snippet**:
    ```python
    {prompt}
    ```
    ## Completion 3:
    """

    # TODO: why list?
    completions_code = []
    if api_dict:
        client = OpenAI(base_url=api_dict["base_url"], api_key=api_dict["api_key"])
    else:
        client = OpenAI(api_key=API_KEY)

    for i in range(times):
        while True:
            try:
                completions = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a software programmer."},
                        {"role": "user", "content": text},
                    ],
                    top_p=0.95,
                    temperature=0.8,
                )
                # TODO: completion includes function definition
                completion = completions.choices[0].message.content
                completion = preprocess_data(completion)

            except Exception as e:
                print(e)
                time.sleep(10)
                completion = ""
            if completion != "":
                break
        completions_code.append(completion)
    data_entry["completion_list"] = completions_code
    return data_entry


def call_fetch_completion_helper(dataset, model, lg):
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
    with open(HUMAN_EVAL_PROGRAMMER_PROMPT_PATH, "r") as f:
        construct_few_shot_prompt = f.read()

    for model in model_list:
        for lg in language:
            from datasets import load_dataset

            dataset = load_dataset("openai_humaneval", split="test")
            dataset = [entry for entry in dataset]
            dataset = dataset[:5]
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_entry = {
                    executor.submit(
                        fetch_completion,
                        construct_few_shot_prompt,
                        copy.deepcopy(entry),
                        model,
                        lg,
                    ): entry
                    for entry in tqdm(dataset)
                }
                for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
                    entry = future_to_entry[future]
                    try:
                        updated_entry = future.result()
                        if updated_entry is not None:
                            idx = dataset.index(entry)
                            dataset[idx] = updated_entry
                        else:
                            print(
                                f"Warning: fetch_completion returned None for entry: {entry}"
                            )
                    except TypeError as e:
                        print(f"TypeError occurred: {repr(e)}")
                        print(f"Entry causing the error: {entry}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {repr(e)}")

            with open(HUMAN_EVAL_DATASET_PATH, "w") as f:
                json.dump(dataset, f, indent=4)
