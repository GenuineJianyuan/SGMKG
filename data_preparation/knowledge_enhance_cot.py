import openai
import os
import json
openai.api_key = 'YOUR_OPENAI_API_KEY'
input_folder = 'YOUR_FUNCTIONAL_STEP_FOLDER_PATH'
output_folder = 'YOUR_WORKFLOW_SAVING_FOLDER_PATH'


STEP_PROMPT='''
Given a structure(target step) that contains descriptions of part of functionality in a geospatial workflow script. 

``` Target step : ```
{}

Here are a list of candidate steps that are performed before the target step. Choose the most appropriate steps that is/are connected to the given structure based on the description of each step choices below.

``` Candidate steps: ```
{}

``` Previous connections: ```
{}

Answer the following question and generate your response:
(1) Think step by step.
(2) What is/are the inputs of the target step?
(3) What are the outputs of in candidate step(s)? List all of them if more than one choice are provided.
(4) Identify which output of the steps in (3) match each input in (2). The match is determined by their natural semantic similarity. 
    - The answer must include each candidate step's output and its match to the input of the target step one by one.
(5) The given structure can not connect to itself. For instance, a given structure "Step1" can not connect to "Step1" itself.
(6) Based on the response for steps in (4), answer which the given step are connected to the target step. A step with output that matches input should be selected.
    - Your answer must cover eact step in (4).
(7) According to the judgement in (6), make decision to which steps are connected. If no connected is found, return "None" instead.
(8) Does all steps include in your judgement? If not, does the left step connect to any candidate steps or target step? 
         If no, keep your judgement, otherwise add the connection you missed.
(9) Give your final decision in the [Decision] block and describe your reason for it.
(10) **Just** response with your reasoning in less than 100 words and your [Decision].
'''

STEP_EXTRACT_PROMPT='''
Based on the given text, extract available step.

``` text info:```
{}

Please just answer the relative steps exactly in the format, e.g., Step 1;Step 2; or response with "None" if there is no step in the given text or "None" exists in the given text.
'''
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


sample_files = set(os.listdir(input_folder))
result_files = set(os.listdir(output_folder))
files_to_process = sample_files-result_files

# 处理这些文件
try:
    for file_name in files_to_process:
        if file_name.endswith('.txt'):
            result_dir = {}
            result_dir[file_name] = []
            file_path = os.path.join(input_folder, file_name)
            with open(file_path, 'r',encoding='utf-8-sig') as f:
                cur_summ = f.read()    
            steps = eval(cur_summ.split("```json")[1].split("```")[0])['Step']
            cur_choices = [steps[0]['Step name']+': '+ steps[0]['Step description']]      
            cur_conn = []
            for step in steps[1:]:
                cur_step = step['Step name']
                cur_step_info = cur_step +': '+ step['Step description']
                conn_info=[]
                for conn in cur_conn:
                    conn_info.append(conn[0]+"->"+conn[1])
                reasoning_prompt = STEP_PROMPT.format(cur_step_info, '\n'.join(str(choice) for choice in cur_choices),'\n'.join(str(conn) for conn in conn_info))
                
                reasoning_response, _ = get_completion(reasoning_prompt,model="gpt-4o-mini",temperature=0.2)
                relation_prompt = STEP_EXTRACT_PROMPT.format(reasoning_response.split("[Decision]")[-1])
                relation_response, _ = get_completion(relation_prompt,model="gpt-4o-mini")
                # print(f'{cur_step} Connection: {relation_response}')
                
                if 'None' not in relation_response:
                    conn_steps = [step_name.strip() for step_name in relation_response.split(';') if step_name.strip()]
                    conn_tuples = []
                    for step_name in conn_steps:
                        if (step_name.strip().replace(' ', '')!=cur_step):
                            conn_tuples.append((step_name, cur_step))
                    cur_conn.extend(conn_tuples)
                
                cur_choices.append(cur_step_info)
            print(f'final step connections for {os.path.join(input_folder,file_name)}:{cur_conn}')
            for conn_tuple in cur_conn:
                if (conn_tuple[0].strip().replace(' ', '')!=conn_tuple[1].strip().replace(' ', '')):
                    result_dir[file_name].append(conn_tuple[0].strip()+";"+conn_tuple[1].strip())
            
            # print(f'Current result: {result_dir}')

            # 将数据写入JSON文件
            with open(output_folder+'\\'+file_name, 'w') as json_file:
                json.dump(result_dir, json_file)
except Exception as e:
    msg=f"{file_name}:{str(e)}"
    print(msg)

