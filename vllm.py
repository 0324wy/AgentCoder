# from datasets import load_dataset
# from tqdm import tqdm


# dataset = load_dataset("mbpp",name="sanitized",split="test")

# print(type(dataset))

# # for entry in tqdm(dataset):
# #     print(entry)

# # print(dataset)

# #     # features: ['source_file', 'task_id', 'prompt', 'code', 'test_imports', 'test_list'],
# #     # num_rows: 257

# # print(dataset[2])

# # # print(dataset[0]['source_file'])

# # # f = open("../dataset/demofile3.txt", "w")
# # # f.write(dataset[0]['source_file'])
# # # f.close()


from openai import OpenAI
# Set OpenAI's API key and API base to use vLLM's API server.
# openai_api_key = ""
# openai_api_base = "http://0.0.0.0:8000/v1"


# API_MAX_RETRY = 5
# model = "meta-llama/Llama-3.1-8B"




# client = OpenAI(
#     base_url="http://localhost:8000/v1",
#     api_key="",
# )

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=""
)

model_list = ["Qwen/Qwen2.5-7B", "meta-llama/Llama-3.1-8B"]

# completions = client.chat.completions.create(model="Qwen/Qwen2.5-7B",
# stream=False,
# messages=[
#                 {"role": "system", "content": "You are a code developer assistant."},
#                 {"role": "user", "content": "How are you?"},
# ],
# timeout=100)

completions = client.chat.completions.create(model="meta-llama/Llama-3.1-8B",
messages=[
			{"role": "user", "content": "Hello!"}
		 ])

print(completions.choices[0].message.content)


# for _ in range(API_MAX_RETRY):
#     try:
#         completion = client.chat.completions.create(
#             model=model,
#             messages=messages,
#             temperature=temperature,
#             max_tokens=max_tokens,
#             )
#         output = completion.choices[0].message.content
#         break
#     except openai.RateLimitError as e:
#         print(type(e), e)
#         time.sleep(API_RETRY_SLEEP)
#     except openai.BadRequestError as e:
#         print(messages)
#         print(type(e), e)
#     except KeyError:
#         print(type(e), e)
#         break

# return output




# completion = client.chat.completions.create(
#   model="Qwen/Qwen2.5-7B",
#   messages=[
#     {"role": "user", "content": "Hello!"}
#   ]
# )

# print(completion.choices[0].message)




# def chat_completion_openai(model, messages, temperature, max_tokens, api_dict=None):
#     import openai
#     if api_dict:
#         client = openai.OpenAI(
#             base_url=api_dict["api_base"],
#             api_key=api_dict["api_key"],
#         )
#     else:
#         client = openai.OpenAI()
    
#     output = API_ERROR_OUTPUT
#     for _ in range(API_MAX_RETRY):
#         try:
#             completion = client.chat.completions.create(
#                 model=model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 )
#             output = completion.choices[0].message.content
#             break
#         except openai.RateLimitError as e:
#             print(type(e), e)
#             time.sleep(API_RETRY_SLEEP)
#         except openai.BadRequestError as e:
#             print(messages)
#             print(type(e), e)
#         except KeyError:
#             print(type(e), e)
#             break
    
#     return output