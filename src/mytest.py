from constant_value import HUMAN_EVAL_DATASET_PATH
import json

import re

# def transform_to_check_function(test_string):
#     # Metadata block
#     metadata = "METADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n"
    
#     # Start the check function
#     check_function = "def check(candidate):\n"

#     # Split the test_string into individual lines
#     lines = test_string.strip().split("\n")

#     # Regular expression to match the assert pattern
#     assert_pattern = re.compile(r'assert\s+([^\s,]+)\s*==\s*([^\s,]+)')
    
#     # Loop through the lines and format them into the check function
#     for line in lines:
#         if 'assert' in line:
#             # Strip away the comment part after the comma (if it exists)
#             line = line.split(',')[0].strip()
            
#             # Find the actual assert statements
#             match = assert_pattern.search(line)
#             if match:
#                 left = match.group(1).strip()
#                 right = match.group(2).strip()
                
#                 # Check if it's a floating-point number
#                 if '.' in right:
#                     check_function += f"    assert abs({left} - {right}) < 1e-6\n"
#                 else:
#                     check_function += f"    assert {left} == {right}\n"

#     # Combine metadata and check_function
#     result = metadata + check_function
#     return result

import re

def remove_last_comment_in_quotes(assert_string):
    # Regular expression to find and remove the last quoted string (wrapped with "")
    pattern = re.compile(r'(\".*\")$')
    
    result = []
    for line in assert_string.splitlines():
        # Remove the last quoted string and strip trailing whitespace
        clean_line = re.sub(pattern, '', line).rstrip()
        if clean_line:  # Only add non-empty lines
            result.append(clean_line)
    
    return "\n".join(result)


def transform_to_check_function(assert_string):
    # Remove comments first
    cleaned_string = remove_last_comment_in_quotes(assert_string)

    # Extract the function name from the first assert statement
    first_line = cleaned_string.splitlines()[0]
    function_name = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\(', first_line).group(1)

    # Metadata block
    metadata = "METADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n"
    
    # Start the check function with the extracted function name
    check_function = f"def check({function_name}):\n"

    # Split the cleaned string into individual lines
    lines = cleaned_string.strip().split("\n")

    # Loop through the lines and format them into the check function
    for line in lines:
        if 'assert' in line:
            # Remove the 'assert' keyword and split at '=='
            line = line.strip().replace('assert ', '')
            left, right = line.split("==")
            left = left.strip()
            right = right.strip().rstrip(',')

            # Check if the right side is a floating-point number
            if '.' in right:
                check_function += f"    assert abs({left} - {right}) < 1e-6\n"
            else:
                check_function += f"    assert {left} == {right}\n"

    # Combine metadata and check_function
    result = metadata + check_function
    return result



with open(HUMAN_EVAL_DATASET_PATH, "r") as f:
    dataset = json.load(f)

for i in range(len(dataset)):
    input = dataset[i]["test_case_list"][0]
    print("=========input===========", i)
    print(input)
    
    
    output = transform_to_check_function(input)
    print("=========output===========", i)
    print(output)
    
    