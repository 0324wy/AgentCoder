To execute AgentCoder, you should have API key from OpenAI or other similar third-party. AgentCoder is done with AIOHUB (https://api.aiohub.org/) since it provide funding for AgentCoder.

You should add you API key in agent_1 and agent_2 py file.

```
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = 'API Here'
```

Then, for code generation, you can just directly run the code with:
```
python agent_1_code_generation.py
```
to generate code that will be used to assistant test case generation.

Then test case generation:
```
python agent_2_test_case_generation.py
```

Finally, self-optimization process:

```
python agent_3_validator.py
```

### Importance

Since THUDM's Humaneval-X does not contains entry_point for python language. So you can directly use 