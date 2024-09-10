
import os
import openai

STEP_PROMPT='''
Assume that you were a proficient geospatial modeling scientist and you are good at understanding the workflow and modeling process from the given 
semantic description about a geospatial model.

Note that make sure the answers are directly from the model description, rather than based on your assumption:
```model description:
{}
```
Please think step by step.

Follow these instructions and do not forget them:
(1) Understand the given model description and reconstruct it into **JSON** format.
(2) A JSON object **summarization** should be used to store the summarization extracted from the given description.
(3) Create a *Step* JSON object and store all the steps as **JSON array** in the given description.
(4) Each step object in "Step" should be single and does not include any sub step.
(5) According to the purpose, functions, operations, input and output for each step, give a **Step description** to each step.
(6) Each "Step description"  should answer the following question: 1) what is the purpose of this step? 2) how does this step implement? 3)what functions  are called to realize this step? 4) which GEE APIs are called to realize the functions in 3)?  Uses a long article to answer these questions, so that this step can be easily underatood and reproduced.
(7) Use a key "Step name" to give a label to the step with number identifier as "Step1, Step2...".
(8) Give a short name to summary each step based on the Step description using a key **Short Name**...
(9) Use a key "Input" to store the input to each step.
(10) Use a key "Output"  to store the output of each step.
(11) The inputs and outputs must be extracted **exactly** from each step instruction in the model description
(12) Each "Input" and "Output" is presented as JSON array.

'''

STEP_EXAMPLE='''
Please response exactly in the following JSON format:
```json
{
"Code summarization": "the summary of the code",
"Step":[
        {
        "Step name":"Step1", 
        "Short Name":"short name",
        "Step description": "the detailed description and realization of the step;", 
        "Input": ["employed image as input 1","used threshold as input 2; ...(more input)..."], 
        "Output":["expected image as output 1","expected image as output 2; ...(more output)..."]
        },
        ... (more steps...)
       ] 
}
```
'''

# Set OpenAI API key (replace with your environment variable or secure key storage method)
openai.api_key = 'YOUR_OPENAI_API_KEY'

# Define input and output folders (code summarization -> standardized functional step description)
input_folder = r'YOUR_CODE_SUMMARIZATION_FOLDER_PATH'
output_folder = r'YOUR_FUNCTIONAL_STEP_FOLDER_PATH'

# Check if the output folder exists, create it if not
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def get_completion(prompt, model="gpt-3.5-turbo", temperature=0.2, messages=None):
    '''
    Retrieve completions from the OpenAI API, preserving conversation history.
    '''
    if messages is None:
        messages = []

    messages.append({"role": "user", "content": prompt})
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    response_content = response.choices[0].message.content
    messages.append({"role": "system", "content": response_content})
    return response_content, messages

# Get file names from the input and output folders
sample_files = set(os.listdir(input_folder))
result_files = set(os.listdir(output_folder))

# Log file to track any errors
log_file = 'errors.log'

# Identify files present in the input folder but missing from the output folder
files_to_process = sample_files - result_files

# Process each file in the files to process
for file_name in files_to_process:
    if file_name.endswith('.txt'):
        try:
            file_path = os.path.join(input_folder, file_name)
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                cur_summ = f.read()

            # Use STEP_PROMPT and STEP_EXAMPLE to format the prompt (replace with actual values)
            cur_prompt = STEP_PROMPT.format(cur_summ) + "\n" + STEP_EXAMPLE

            # Get the completion from the OpenAI API
            content, _ = get_completion(cur_prompt, model="gpt-3.5-turbo")

            # Write the result to the output file
            output_file_path = os.path.join(output_folder, os.path.basename(file_path))
            print(f"finish generate in: {output_file_path}")
            with open(output_file_path, 'w', encoding='utf-8-sig') as output_file:
                output_file.write(content)

        except Exception as e:
            # Log any errors encountered
            msg = f"{file_name}: {str(e)}"
            print(msg)
            with open(log_file, 'a') as f:
                f.write(msg + '\n')