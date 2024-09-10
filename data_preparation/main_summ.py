import os
import openai
from data_preparation.Preprocessing import read_and_clean_file, remove_extra_blank_lines

# Retrieve OpenAI API key from environment variables (replace with actual key when deploying)
openai.api_key = 'YOUR_OPENAI_API_KEY'

# Define input and output folder paths for samples and code summarization to save
input_folder = r'YOUR_SAMPLE_FOLDER_PATH' 
output_folder = r'YOUR_CODE_SUMMARIZATION_FOLDER_PATH'


# Define code generation prompt template (customize as needed)
CODE_PROMPT='''
Assume that you were a proficient geospatial modeling scientist and Google Earth Engine developer, you know well about the trick and traps about these GEE workflow scripts using JavaScript. 
The following JavaScript code is a solution for a specific geo-analysis task.

Note that make sure the answers are directly included from the JavaScript code, rather than based on your assumption,here is the code:
```javascript
{}
```

Follow these instructions and do not forget them:
(1) Focus on the code and its annotation (comments) and think step by step.
(2) Give a code summarization of the modeling process of this scripts. 
(3) The code summarization should be **comprehensive**, including details about "what did" (task/application topic),"where" (spatial scope), 
        "when" (time scope), "what data" (data sources), and "what did" (actions and processes described in the script).
        Please use a long article to answer this question as accurately and in detail as possible.
(4) Describe the main steps used to implement this model. Your answer should cover the following question: 
        1) what is the purpose of this step? 
        2) which functions are realized in this step? 
        3) which operations are performed to realize this function? 
        4) how does these operations called in sequence?  
        5) what is/are the input for the step?
        6) what is/are the output from the step?
        Please use a long article to answer these question for each step as accurately and **in detail as possible.**
(5) Each Step must be fine-grained, and cover less input and output.
(6) Only **one** [Summarization] is created.
(7) **Multiple** [Step] can be generated, because you are using these step to specifically depict the modeling process of the given code.

Make sure that the following prohibitions are not violated:
- Never miss any description about the purposes, functions, operations, input, output in the content for each step.
- Never attach raw code in your answer.

Please carefully reason over the code and its annotation (comments), and then response exactly in the following format:
[Summarization]: The summary of the code that satisfies the instructions. 
[Step]: The description of each step with description about the purposes, functions, operations, input, output in the content.  
...... more [Step] elements ......

'''


def get_completion(prompt, model="gpt-3.5-turbo", temperature=0.2, messages=None):
    '''
    Retrieve a completion from the OpenAI API using the given prompt.
    - prompt: The input prompt to send to the OpenAI model.
    - model: The model to be used (default is gpt-3.5-turbo).
    - temperature: Controls the randomness of the output (lower is more deterministic).
    - messages: Optional conversation history (default is None).
    
    Returns:
    - response_content: The generated response content.
    - messages: The updated conversation history.
    '''
    if messages is None:
        messages = []  # Initialize message history if not provided

    messages.append({"role": "user", "content": prompt})
    
    # Make a request to OpenAI to get the response based on the prompt
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    
    # Extract the content from the response
    response_content = response.choices[0].message.content
    
    # Append the response to the conversation history
    messages.append({"role": "system", "content": response_content})
    
    return response_content, messages

# Retrieve list of file names from the input and output folders
input_files = set(os.listdir(input_folder))
output_files = set(os.listdir(output_folder))

# Log file to store errors
log_file = 'errors.log'

# Identify files that are present in the input folder but missing from the output folder
files_to_process = input_files - output_files

# Process each file that needs to be handled
for file_name in files_to_process:
    if file_name.endswith('.txt'):  # Only process text files
        try:
            # Construct the full path of the input file
            input_file_path = os.path.join(input_folder, file_name)
            
            # Read and clean the file content
            with open(input_file_path, 'r', encoding='utf-8') as f:
                cleaned_script = read_and_clean_file(input_file_path)
            
            # Remove extra blank lines from the script
            cleaned_script = remove_extra_blank_lines(cleaned_script)
            
            # Format the prompt with the cleaned script
            current_prompt = CODE_PROMPT.format(cleaned_script)
            
            # Get the completion from OpenAI based on the formatted prompt
            content, _ = get_completion(current_prompt, model="gpt-3.5-turbo")
            
            # Construct the output file path based on the input file name
            output_file_path = os.path.join(output_folder, os.path.basename(input_file_path))
            print(f"Successfully generated content for: {output_file_path}")
            
            # Write the generated content to the output file
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(content)

        except Exception as e:
            # Log any exceptions encountered during file processing
            error_message = f"{file_name}: {str(e)}"
            print(error_message)
            with open(log_file, 'a', encoding='utf-8-sig') as log:
                log.write(error_message + '\n')
