import random
import json
from typing import Optional, Callable, Dict
import ast
import doctest
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import numpy as np
import sys

sys.path.append('./CodeGeeX/')
import contextlib
import faulthandler
import io
import os
import multiprocessing
import platform
import signal
from tqdm import tqdm
from programmer_mbpp import call_completion
from codegeex.benchmark.utils import read_dataset, IMPORT_HELPER
from codegeex.benchmark.execution import check_correctness
import tempfile
from constant_value import MBPP_DATASET_PATH, MBPP_PATH_WITH_SUFFIX
from process_data import transform_to_check_function

correct_doctest = 0
correct_before_doctest = 0
correct_after_doctest = 0
result_original = 0
result_canonical_solution = 0
result_fuzzer = 0
result_fuzzer_canonical_solution = 0
idx_run_tests_orginal = []
idx_run_tests_canonical_solution = []
idx_run_tests_fuzzer = []
idx_run_tests_fuzzer_canonical_solution = []

language = ["python", "cpp", "js", "go", "js"]


def process_test(sample, dataset, language=language, test_case=True, canonical_solution=False):
    task_id = sample["task_id"]
    # task_id = problems.index(sample)
    prompt = sample["prompt"]
    code = sample["completion"]
    if canonical_solution:
        code = sample["code"]
    # Pre-process for different languages
    if language == "python" or language == "py":
        if test_case:
            test_case = sample["test_case_list"]
            tests = ""
            for test in test_case:
                tests += "\n" + test
        else:
            test_case = sample["test_list"]
            tests = ""
            for test in test_case:
                tests += "\n" + test
                
        test_string = code + "\n" + tests
    return test_string





class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'


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


# def check_correctness_mbpp(code_string):


def test_report(dataset, lg):
    correct_list = []
    correct = 0
    for i in tqdm(range(len(dataset))):
        dataset[i]["test_code"] = process_test(dataset[i], dataset, language=lg, test_case=False, canonical_solution=False)
        dataset[i]["generation"] = dataset[i]["completion"]

        result = check_correctness(dataset[i]["task_id"], dataset[i], lg, 5, "./tmp")
        if result["passed"] == True:
            correct += 1
            correct_list.append(dataset[i]["task_id"])
        # dataset[i]["report_passed"] = result["passed"]
        # dataset[i]["report_result"] = result["result"]
    print("==============Start Report Testing==============")
    # correct_percent = correct / len(dataset) * 100
    # print(f"test_report, {correct_percent:0.2f}")
    print(correct_list)
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
        # print("dataset[i]=======:", i)
        if "need_reproduce" in dataset[i].keys() and dataset[i]["need_reproduce"]==False:
            # dataset[i]["need_reproduce"] = True
            return dataset[i]["max_correct"], dataset[i]["idx"], dataset[i]["result"]
        completion_list = []
        completion_list.append(dataset[i]["completion"])
        dataset[i]["completion_list"] = completion_list
        # completion_list = dataset[i]["completion_list"]
        test_case_list = dataset[i]["test_case_list"]
        test_case_0 = dataset[i]["test_list"][0]
        function_name = test_case_0.split("(")[0].split(" ")[-1]
        correct_list = []
        result_list = []
        for j in range(len(completion_list)):
            correct = 0
            result = None
            if f"def {function_name}" not in completion_list[j]:
                # print(f"NameError: name '{dataset[i]['entry_point']}' is not defined")
                
                correct_list.append(correct)
                result_list.append(f"NameError: name '{function_name}' is not defined")
                continue
            for k in range(len(test_case_list)):
                # TODO
                # if f"assert {dataset[i]['entry_point']}(" not in test_case_list[k]:
                #     continue
                dataset[i]["full_code"] = test_setup + "\n" + completion_list[j] + "\n" + transform_to_check_function(test_case_list[k]) + "\n" + f"check({function_name})"
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


def test_agent(dataset, lg):
    correct = 0
    for i in tqdm(range(len(dataset))):
        dataset[i]["test_code"] = process_test(dataset[i], dataset, language=lg, test_case=True, canonical_solution=False)
        dataset[i]["generation"] = dataset[i]["completion"]

        result = check_correctness(dataset[i]["task_id"], dataset[i], lg, 5, "./tmp")
        if result["passed"] == True:
            correct += 1
            print(dataset[i]["task_id"])
        # dataset[i]["result"] = result["result"]
        # dataset[i]["passed"] = result["passed"]
    print("============Start Agent Testing=================")
    correct_percent = correct / len(dataset) * 100
    print(f"agent_report, {correct_percent:0.2f}")
    return dataset


if __name__ == "__main__":
    model_list = ["gpt-3.5-turbo-1106"]
    language = ["python"]

    for model_name in model_list:
        for lg in language:
            path = MBPP_PATH_WITH_SUFFIX
            with open(path, "r") as f:
                dataset = json.load(f)
            epoch = 5
            for current_epoch in range(epoch):
                print(lg, current_epoch)
                # test_report(dataset, lg)
                test_agent_concurrency2(dataset, lg)
            #     dataset = call_completion(dataset, model_name, lg)
            #     epoch_path = MBPP_PATH_WITH_SUFFIX.replace("mbpp_temp01.json", f"{current_epoch}_mbpp_temp01.json")
            #     total_path = MBPP_PATH_WITH_SUFFIX.replace("mbpp_temp01.json",
            #                                                f"{current_epoch}_mbpp_temp01_total.json")
            #     with open(epoch_path, "w") as f:
            #         json.dump(dataset, f, indent=4)
            # with open(total_path, "w") as f:
            #     json.dump(dataset, f, indent=4)
