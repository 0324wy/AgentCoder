from constant_value import HUMAN_EVAL_DATASET_PATH
import json
import re
import ast


def preprocess_data(test_case_string):
    if f"```python" in test_case_string:
        test_case_string = test_case_string[test_case_string.find(f"```python")+len(f"```python"):]
        test_case_string = test_case_string[:test_case_string.find("```")]
    elif f"```" in test_case_string:
        test_case_string = test_case_string[test_case_string.find("```")+len("```"):]
        test_case_string = test_case_string[:test_case_string.find("```")]
    else:
        print("Error: No code block found")
    return test_case_string


def remove_last_comment_in_quotes(assert_string):
    # Regular expression to find and remove the last quoted string (wrapped with "")
    pattern = re.compile(r',\s*".*?"$')
    
    result = []
    for line in assert_string.splitlines():
        # Remove the last quoted string and strip trailing whitespace
        clean_line = re.sub(pattern, '', line).rstrip()
        if clean_line:  # Only add non-empty lines
            result.append(clean_line)
    
    return "\n".join(result)


def transform_to_check_function(assert_string):
    """
    Transforms a string containing assert statements into a check function with metadata.
    
    Parameters:
        assert_string (str): A string containing multiple assert statements.
    
    Returns:
        str: A string representing the transformed check function with metadata.
    """
    # Remove comments first
    cleaned_string = remove_last_comment_in_quotes(assert_string)
    
    # Metadata block
    metadata = (
        "METADATA = {\n"
        "    'author': 'jt',\n"
        "    'dataset': 'test'\n"
        "}\n\n"
    )
    
    # Define the regex pattern to match multi-line assert statements
    pattern = re.compile(
        r'assert\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([\s\S]*?)\s*\)\s*==\s*([\s\S]*?)(?=\nassert|\Z)',
        re.MULTILINE
    )
    
    # Find all matches
    matches = pattern.findall(cleaned_string)
    
    if not matches:
        print("No assert statements found.")
        return metadata + "def check():\n    pass  # No assertions found\n"
    
    # Extract the function name from the first assert statement
    first_func_name = matches[0][0]
    
    # Start the check function with the extracted function name
    check_function = f"def check({first_func_name}):\n"
    
    # Loop through the assert statements and format them into the check function
    for func_name, params_str, expected_str in matches:
        # Clean up the captured strings
        params_str = params_str.strip()
        expected_str = expected_str.strip()
        
        # Attempt to evaluate the parameters and expected result safely
        try:
            # Wrap parameters in parentheses to form a valid tuple if necessary
            if not (
                params_str.startswith('[') or
                params_str.startswith('{') or
                params_str.startswith('(') or
                params_str.startswith('"') or
                params_str.startswith("'") or
                params_str.isdigit()
            ):
                params_str = f"({params_str})"
            
            # Safely evaluate the parameters
            parameters = ast.literal_eval(params_str)
        except (ValueError, SyntaxError):
            # If evaluation fails, keep parameters as raw string
            parameters = params_str
        
        try:
            # Safely evaluate the expected result
            expected_output = ast.literal_eval(expected_str)
        except (ValueError, SyntaxError):
            # If evaluation fails, keep expected output as raw string
            expected_output = expected_str
        
        # Reconstruct the left side of the assert statement
        if isinstance(parameters, tuple):
            params_repr = ", ".join(repr(p) for p in parameters)
        else:
            params_repr = repr(parameters)
        
        left_side = f"{func_name}({params_repr})"
        
        # Check if the expected output is a float for approximate comparison
        if isinstance(expected_output, float):
            check_function += f"    assert abs({left_side} - {expected_output}) < 1e-6\n"
        else:
            check_function += f"    assert {left_side} == {repr(expected_output)}\n"
    
    # Combine metadata and check_function
    result = metadata + check_function
    return result

def extract_fun_name_and_parameters(test_case):
    # Regex pattern to capture function name and parameters
    pattern = r'(\w+\s*\([^)]*\))'

    # Search for the pattern in the test case
    match = re.search(pattern, test_case)

    function_call = 0
    # Extract and print the function call
    if match:
        function_call = match.group(1)
        # print(function_call)
    else:
        print("No function call found.")
    return function_call




    