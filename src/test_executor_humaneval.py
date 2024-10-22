# test
import random
import json
from typing import Optional, Callable, Dict
import ast
import doctest
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import numpy as np
import sys
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
import concurrent.futures
from tqdm import tqdm
from tqdm import tqdm
from programmer_humaneval import call_fetch_completion_helper
from test_designer_humaneval import call_fetch_test_completion_helper
import copy

sys.path.append("./CodeGeeX/")
from codegeex.benchmark.utils import read_dataset, IMPORT_HELPER
from codegeex.benchmark.execution import check_correctness
import tempfile
from constant_value import HUMAN_EVAL_DATASET_PATH, API_KEY
from openai import OpenAI
from process_data import transform_to_check_function, preprocess_data

client = OpenAI(api_key=API_KEY)

class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """StringIO that throws an exception when it's read from"""

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """Returns True if the IO object can be read."""
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = "stdin"


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def test_report(dataset, lg):
    correct = 0
    test_setup = "\n".join(IMPORT_HELPER["python"]) + "\n"
    
    
    for i in tqdm(range(len(dataset))):
        result = check_code(dataset[i]["task_id"], dataset[i])
        if result["passed"]:
            correct += 1
    print("==============Start Report Testing==============")
    print(f"test_report: {(correct/len(dataset)*100):.1f}")



def fix_bug(data_entry, model,lg, times, api_dict=None):
    if "need_reproduce" in data_entry.keys() and data_entry["need_reproduce"]==False:
        return data_entry
    else:
        completion_list = []
        for i in range(times):
            # TODO
            gpt_prompt = (
                "Please re-completion the code to fix the error message. "+
                f"\nHere is the previous version:\n```{lg}\n" +
                data_entry['completion'] + f"\n```\nWhen we use this test cases: ```{lg}\n"+data_entry['test_case_list'][0]+f"\n``` to evaluate the code. It raise the error:\n```{lg}\n" + data_entry["result"] +
                f"\n```\nPlease fix the bug and return the code. The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
            )
            # if api_dict:
            #     client = openai.OpenAI(
            #         base_url=api_dict['base_url'],
            #         api_key=api_dict['api_key']
            #     )
            # else:
            #     client = openai.OpenAI(api_key=API_KEY)
            try:
                completions = client.chat.completions.create(
                    model = model,
                    messages=[
                {"role": "system", "content": "You are a code developer assistant."},
                {"role": "user", "content":gpt_prompt},
                    ],
                    temperature=0.8,
                    top_p=0.95,
                )
                completion = completions.choices[0].message.content
                # print("======completion:", completion)
                completion = preprocess_data(completion)
                completion_list.append(completion)
            except Exception as e:
                # print(repr(e))
                pass
    data_entry["completion_list"] = completion_list
    return data_entry

def call_fix_bug(dataset, model,lg, times = 1, api_dict=None):
    print("==============Start Bug Fixing==============")
    with ThreadPoolExecutor() as executor:
        future_to_entry = {executor.submit(fix_bug, copy.deepcopy(entry), model, lg, times, api_dict=api_dict): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(dataset)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                # print(repr(e))
                pass
    return dataset


def check_code(task_id: str, sample: dict, completion_id: Optional[int] = None):
    try:
        with swallow_io():
            with time_limit(2.0):
                exec(sample["full_code"])
                result = "passed"
                
    except TimeoutException:
        result="timed out"
    except AssertionError as e:
        result=f"failed: AssertionError:{e}"
    except BaseException as e:
        result=(f"failed: {e}")
    except Exception as e:
        result = f"Exception{e}"
        pass

    # print("result:======", task_id, result)
    return {
        "task_id": task_id,
        "completion_id": completion_id,
        "full_code": sample["full_code"],
        "prompt": sample["prompt"],
        "completion": sample["completion"],
        "result": result,
        "passed": result == "passed",
        "finish": -1 if "finish" not in sample else sample["finish"],
        "file": "" if "file" not in sample else sample["file"],
        "output": [] if "output" not in sample else sample["output"],
    }


def test_agent_concurrency2(dataset, lg):
    test_setup = "\n".join(IMPORT_HELPER["python"]) + "\n"
    total_correct = 0
    _for_completion = 0
    
    def process_item(i):
        if "need_reproduce" in dataset[i].keys() and not dataset[i]["need_reproduce"]:
            # dataset[i]["need_reproduce"] = True
            return dataset[i]["max_correct"], dataset[i]["idx"], dataset[i]["result"]
        completion_list = dataset[i]["completion_list"]
        test_case_list = dataset[i]["test_case_list"]
        correct_list = []
        result_list = []
        for j in range(len(completion_list)):
            correct = 0
            result = None
            if f"def {dataset[i]['entry_point']}" not in completion_list[j]:
                # print(f"NameError: name '{dataset[i]['entry_point']}' is not defined")
                
                correct_list.append(correct)
                result_list.append(f"NameError: name '{dataset[i]['entry_point']}' is not defined")
                continue
            for k in range(len(test_case_list)):
                # TODO
                # if f"assert {dataset[i]['entry_point']}(" not in test_case_list[k]:
                #     continue
                dataset[i]["full_code"] = test_setup + "\n" + completion_list[j] + "\n" + transform_to_check_function(test_case_list[k]) + "\n" + f"check({dataset[i]['entry_point']})"
                dataset[i]["completion"] = completion_list[j]
                #  test_case_list[k]
                result = check_code(dataset[i]["task_id"], dataset[i])
                # print(f"result: {result['result']}")
                if result["passed"]:
                    correct += 1
            if not result:
                result_list.append("Error: AssertionError")
            else:
                result_list.append(result['result'])
            correct_list.append(correct)

        max_correct = max(correct_list)
        idx = correct_list.index(max_correct)
        result = result_list[idx]
        # print(f"max_correct: {max_correct}, idx: {idx}")
        return max_correct, idx, result
    
    for i in range(len(dataset)):
        max_correct, idx, result = process_item(i)
        if max_correct >= np.ceil(len(dataset[i]["test_case_list"]) * 0.6): # GPT-3.5-turbo-1106's test case accuracy is about 67%. So we choice 60% as the bar.
            dataset[i]["completion"] = dataset[i]["completion_list"][idx]
            dataset[i]["need_reproduce"] = False
            dataset[i]["idx"] = idx
            dataset[i]["max_correct"] = max_correct
            dataset[i]["result"] = result
            _for_completion += 1
            total_correct += 1
        else:
            # print(f"max_correct: {max_correct}, idx: {idx}")
            dataset[i]["completion"] = dataset[i]["completion_list"][idx]
            dataset[i]["result"] = result
    print("==============Start Agent Testing==============")
    print(f"test_report: {(total_correct/len(dataset)*100):.1f}")
    print(f"test_for_completion: {(_for_completion/len(dataset)*100):.1f}")
    return dataset


if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo-1106"]
    language = ["python"]

    for model in model_list:
        for lg in language:
            with open(HUMAN_EVAL_DATASET_PATH, "r") as f:
                dataset = json.load(f)
            dataset = [entry for entry in dataset]
            epoch = 5
            for current_epoch in range(epoch):
                # TODO: check test and test code list
                dataset = test_agent_concurrency2(dataset, lg)
                epoch_path = HUMAN_EVAL_DATASET_PATH.replace("humaneval_temp01.json", f"{current_epoch}_humaneval_temp01.json")
                with open(epoch_path, "w") as f:
                    json.dump(dataset, f, indent=4)
                dataset = call_fix_bug(dataset,model,lg)
            dataset = test_agent_concurrency2(dataset,lg)

