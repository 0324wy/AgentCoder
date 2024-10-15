from constant_value import MBPP_PATH_WITH_SUFFIX
import json
from tqdm import tqdm
from codegeex.benchmark.execution import check_correctness


path = MBPP_PATH_WITH_SUFFIX
with open(path, "r") as f:
    dataset = json.load(f)

correct = 0

list = [12, 14, 16, 17, 18, 57, 58, 59, 61, 62, 63, 64, 65, 66, 67, 70, 71, 74, 75, 77, 79, 82, 84, 86, 88, 92, 93, 94, 95, 96, 97, 99, 100, 103, 104, 105, 106, 108, 111, 117, 118, 119, 120, 127, 128, 129, 130, 132, 135, 140, 141, 142, 160, 161, 162, 164, 165, 166, 168, 170, 171, 172, 222, 226, 227, 230, 232, 233, 234, 237, 240, 244, 245, 250, 251, 256, 257, 259, 261, 262, 264, 265, 266, 267, 269, 270, 271, 272, 273, 274, 277, 278, 280, 281, 282, 283, 284, 285, 286, 287, 290, 291, 292, 297, 305, 308, 309, 388, 389, 390, 391, 393, 398, 399, 401, 404, 405, 406, 407, 409, 413, 414, 417, 419, 420, 421, 424, 425, 426, 428, 429, 432, 434, 435, 437, 441, 446, 447, 450, 451, 456, 457, 458, 459, 460, 463, 464, 465, 470, 471, 473, 474, 475, 476, 477, 478, 479]

for i in tqdm(range(len(dataset))):
    sample = dataset[i]
    if sample
    sample["generation"] = sample["completion"]
    sample["test_code"] = sample["test_list"]

    result = check_correctness(sample["task_id"], sample, "python", 5, "./tmp")

    # print(result["passed"])

    if result["passed"] == True:
        correct += 1

print("==============Start Report Testing==============")
correct_percent = correct / len(dataset) * 100
print(f"test_report, {correct_percent:0.2f}")

# print(len(dataset))

# print(dataset[0])




# Convert and pretty-print the dictionary as a JSON string
# json_data = json.dumps(sample, indent=4)

# # Print the readable JSON
# print(json_data)








# print(result)

