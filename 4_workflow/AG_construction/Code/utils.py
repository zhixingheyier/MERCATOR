from openai import OpenAI
import json
import os
import glob
import copy
from tqdm import tqdm
import re
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, RegularPolygon, PathPatch
from matplotlib.path import Path
import matplotlib.patches as patches
from matplotlib.patches import Patch
# vLLM服务配置（需先启动vLLM服务）
client = OpenAI(
    api_key = "EMPTY",          # vLLM默认无需认证[1,8](@ref)
    base_url = "http://localhost:8000/v1"  # 默认服务端口
)
class_labels = ['initial access','execution','persistence','privilege escalation',
                'defense evasion','credential access','discovery','lateral movement',
                'collection','command and control','exfiltration','impact','other']

## Step1: stage identification
def get_attack_phase(prompt):
    messages = [
        {"role": "user", "content": prompt}
    ]
    # 发起生成请求
    response = client.chat.completions.create(
        model = "my-sft-model",   # 替换为实际部署的模型名称[1,8](@ref)
        messages = messages,
        temperature = 0.7,        # 控制生成随机性(0-1)[1,3](@ref)
        top_p = 0.9,               # 核采样概率阈值[1,8](@ref)
        max_tokens = 1024,         # 最大生成token数[1,8](@ref)
    )
    return response.choices[0].message.content

def split_attack_phase(raw_data_path, out_data_path):
    instruction_attack_phase="As a cybersecurity threat analyst, map the described attack activity to its corresponding MITRE ATT&CK framework phase. If the activity spans multiple phases, select the most dominant one."
    if not os.path.exists(out_data_path):
        os.makedirs(out_data_path)
    files=glob.glob(raw_data_path+'/*.json')
    for file in files:
        with open(file,'r') as f:
            data=json.load(f)
        split_data=[]
        for item in data:
            prompt = instruction_attack_phase+"\n"+"Described attack activity: "+item['content']
            item['title']=item['title'].strip().lower()
            item['phase']=get_attack_phase(prompt)
            split_data.append(item)
        with open(out_data_path+'/'+os.path.basename(file),'w') as f:
            json.dump(split_data, f, indent=4,ensure_ascii=False)

def split_attack_phase_single_file(file_path, out_data_path):
    instruction_attack_phase="As a cybersecurity threat analyst, map the described attack activity to its corresponding MITRE ATT&CK framework phase. If the activity spans multiple phases, select the most dominant one."
    if not os.path.exists(out_data_path):
        os.makedirs(out_data_path)
    with open(file_path,'r') as f:
        data=json.load(f)
    split_data=[]
    for item in data:
        prompt = instruction_attack_phase+"\n"+"Described attack activity: "+item['content']
        item['title']=item['title'].strip().lower()
        item['phase']=get_attack_phase(prompt)
        split_data.append(item)
    with open(out_data_path+'/'+os.path.basename(file_path),'w') as f:
        json.dump(split_data, f, indent=4,ensure_ascii=False)

def humancheck_splited_phase_data(file_path):
    process_data=[]
    with open(file_path, 'r') as f:
        data= json.load(f)
    for item in data:
        if item['phase'] in class_labels and item['phase'] != 'other':
            process_item={
                'phase': item['phase'],
                'content': item['content']
            }
            process_data.append(process_item)
        print(item['title'],'\n')
        print(item['content'],'\n')
        print(item['phase'])
        print('*'*50)
    return process_data

## Step2: extract element
def get_relationships(prompt):
    messages = [
        # {"role": "system", "content": "你是一个专业的AI助手"},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model = "sft-model",   # 替换为实际部署的模型名称[1,8](@ref)
        messages = messages,
        temperature = 0.7,        # 控制生成随机性(0-1)[1,3](@ref)
        top_p = 0.9,               # 核采样概率阈值[1,8](@ref)
        max_tokens = 1024,         # 最大生成token数[1,8](@ref)
        # repetition_penalty = 1.05  # 重复惩罚系数(>1减少重复)[8](@ref)
    )
    return response.choices[0].message.content

def relationships_extract_single_file(data,data_name,out_data_path):
    instruction_relationship_extract="As a cybersecurity threat analyst, extract the network security entities and their relationships from the following described attack activity, and output them in a standardized format."
    if not os.path.exists(out_data_path):
        os.makedirs(out_data_path)
    extracted_data=[]
    for item in data:
        prompt = instruction_relationship_extract+"\n"+"Described attack activity: \n"+item['content']
        relationship=get_relationships(prompt)
        data_item={
            'phase': item['phase'],
            'content': item['content'],
            'relationship': relationship
        }
        extracted_data.append(data_item)
    with open(out_data_path+'/'+data_name+'.json','w') as f:
        json.dump(extracted_data, f, indent=4,ensure_ascii=False)

## Step3: semantic alignment
def get_semantic_alignment(prompt):
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model = "sft-model",   # 替换为实际部署的模型名称[1,8](@ref)
        messages = messages,
        temperature = 0.7,        # 控制生成随机性(0-1)[1,3](@ref)
        top_p = 0.9,               # 核采样概率阈值[1,8](@ref)
        max_tokens = 1024,         # 最大生成token数[1,8](@ref)
        # repetition_penalty = 1.05  # 重复惩罚系数(>1减少重复)[8](@ref)
    )
    return response.choices[0].message.content   
def semantic_alignment_single_file(file,output_path,with_CoT=True):
    
    instruction_withcot="As a cybersecurity threat analyst, given an attack description and its corresponding entity relationships. Please convert the original human readable entity relationships into system level entity relationships, and output them in a standardized format."
    instruction_withoutcot="As a cybersecurity threat analyst, given a entity relationships. Please convert the original human readable entity relationships into system level entity relationships, and output them in a standardized format."
    if with_CoT:
        instruction=instruction_withcot
    else:
        instruction=instruction_withoutcot
    with open(file,'r') as f:
        data=json.load(f)
    phase_relationship_one_file=[]
    semantic_alignment_data=[]
    for item in data:
        item_response=[]
        # dict_response={}
        if '[Relationships]: None' in item['relationship'] or len(item['relationship']) < 50:
            item_data={
                'phase':item['phase'],
                'content':item['content'],
                'relationship':item['relationship'],
                'semantic_relationship':'None'
            }
            semantic_alignment_data.append(item_data)
        else:
            relationship_list=item['relationship'].split('\n')
            if with_CoT:
                relationship_list=[i.replace('[CoT]:','[Description]:') for i in relationship_list]
                relationship_list=[i.replace('[Relationships]:','[Original Relationships]:') for i in relationship_list]
                relationship_list=['[Description]:'+i.split('[Description]:')[-1] for i in relationship_list]
            else:
                relationship_list=[i.replace('[Relationships]:','[Original Relationships]:') for i in relationship_list]
                relationship_list=['[Original Relationships]:'+i.split('[Original Relationships]:')[-1] for i in relationship_list]
            for i in relationship_list:
                prompt = instruction+'\n'+i
                response=get_semantic_alignment(prompt)
                item_response.append(response)
                phase_relationship_one_file_data={
                    'phase':item['phase'],
                    'relationship':i,
                    'semantic_relationship':response
                }
                phase_relationship_one_file.append(phase_relationship_one_file_data)

            item_data={
                'phase':item['phase'],
                'content':item['content'],
                'relationship':item['relationship'],
                'semantic_relationship':'\n'.join(item_response)
            }
            semantic_alignment_data.append(item_data)

    dict_phase_relationship_one_file={
        'phase_relationship':phase_relationship_one_file
    }
    semantic_alignment_data.append(dict_phase_relationship_one_file)
    with open(output_path+'/'+file.split('/')[-1],'w') as f:
        json.dump(semantic_alignment_data,f,indent=4)



def main():
    print('test')
    pass
           
if __name__ == '__main__':
    main()