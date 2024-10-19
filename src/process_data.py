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