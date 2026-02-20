    
from graphviz import Digraph
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
class AttackGraphRepair:
    def __init__(self, edges):
        """
        初始化攻击图修复类
        
        Args:
            edges: 边列表，每条边格式为 [subject, predicate, object]
        """
        self.original_edges = edges.copy()
        self.edges = edges.copy()
        
        # 从边中提取所有实体并推断类型
        self.entities = self._extract_entities()
        
        # 按阶段分组边
        self.stage_edges = self._group_edges_by_stage()
        
        # 计算全局出度和入度（在整个图中）
        self.global_out_degree = self._calculate_global_out_degree()
        self.global_in_degree = self._calculate_global_in_degree()
        
    def _extract_entities(self):
        """从边中提取所有实体并推断类型"""
        entities = set()
        for edge in self.edges:
            entities.add(edge[0])  # subject
            entities.add(edge[2])  # object
        return list(entities)
    
    def _get_entity_type(self, entity):
        """根据实体名称推断类型"""
        if entity.startswith('process:'):
            return 'process'
        elif entity.startswith('file:'):
            return 'file'
        elif entity.startswith('socket:'):
            return 'socket'
        elif entity.startswith('reg:'):
            return 'reg'
        return 'unknown'
    
    def _get_stage_from_predicate(self, predicate):
        """从谓词中提取阶段信息"""
        # 格式为 "stage_action"
        if '_' in predicate:
            return predicate.split('_')[0]
        return predicate
    
    def _get_action_from_predicate(self, predicate):
        """从谓词中提取动作信息"""
        # 格式为 "stage_action"
        if '_' in predicate:
            return predicate.split('_')[1]
        return predicate
    
    def _group_edges_by_stage(self):
        """按战术阶段分组边"""
        stage_edges = {}
        
        for edge in self.edges:
            stage = self._get_stage_from_predicate(edge[1])
            if stage not in stage_edges:
                stage_edges[stage] = []
            stage_edges[stage].append(edge)
        
        # 保持阶段顺序（按照输入中的出现顺序）
        ordered_stages = []
        for edge in self.edges:
            stage = self._get_stage_from_predicate(edge[1])
            if stage not in ordered_stages:
                ordered_stages.append(stage)
        
        ordered_stage_edges = {stage: stage_edges[stage] for stage in ordered_stages if stage in stage_edges}
        
        return ordered_stage_edges
    
    def _calculate_global_out_degree(self):
        """计算整个图中每个实体的全局出度"""
        out_degree = {}
        
        for edge in self.edges:
            subject = edge[0]
            out_degree[subject] = out_degree.get(subject, 0) + 1
        
        return out_degree
    
    def _calculate_global_in_degree(self):
        """计算整个图中每个实体的全局入度"""
        in_degree = {}
        
        for edge in self.edges:
            obj = edge[2]
            in_degree[obj] = in_degree.get(obj, 0) + 1
        
        return in_degree
    
    def _calculate_stage_in_degree(self, stage_edges):
        """计算阶段内每个实体的入度（仅用于APPA识别孤儿进程）"""
        in_degree = {}
        
        for edge in stage_edges:
            obj = edge[2]
            in_degree[obj] = in_degree.get(obj, 0) + 1
        
        return in_degree
    
    def _get_process_entities_in_stage(self, stage_edges):
        """获取阶段内的所有进程实体"""
        processes = set()
        for edge in stage_edges:
            # 检查主语
            if self._get_entity_type(edge[0]) == 'process':
                processes.add(edge[0])
            # 检查宾语
            if self._get_entity_type(edge[2]) == 'process':
                processes.add(edge[2])
        return list(processes)
    
    def _get_adjacent_triples(self, entity, stage_edges):
        """获取实体在阶段内的相邻三元组"""
        adjacent = []
        for edge in stage_edges:
            if edge[0] == entity or edge[2] == entity:
                adjacent.append(edge)
        return adjacent
    
    def _get_first_interaction(self, entity, stage_edges):
        """获取实体在阶段内的第一次交互（时间顺序最早）"""
        for i, edge in enumerate(stage_edges):
            if edge[0] == entity or edge[2] == entity:
                return edge, i
        return None, -1
    
    def _get_last_interaction_time(self, entity, stage_edges, time_limit):
        """获取实体在time_limit之前最近一次交互的时间"""
        last_time = -1
        for i, edge in enumerate(stage_edges):
            if i >= time_limit:  # 超过时间限制
                break
            if edge[0] == entity or edge[2] == entity:
                last_time = i
        return last_time
    
    def _update_global_degrees(self, new_edge):
        """更新全局出度和入度"""
        subject = new_edge[0]
        obj = new_edge[2]
        
        # 更新全局出度
        self.global_out_degree[subject] = self.global_out_degree.get(subject, 0) + 1
        
        # 更新全局入度
        self.global_in_degree[obj] = self.global_in_degree.get(obj, 0) + 1
    
    # ========== ISI 算法实现 ==========
    def implicit_spawn_inference(self):
        """Implicit Spawn Inference (ISI) 算法"""
        new_edges = []
        
        for stage, stage_edges in self.stage_edges.items():
            processes = self._get_process_entities_in_stage(stage_edges)
            stage_edges_copy = stage_edges.copy()
            
            i = 0
            while i < len(stage_edges_copy):
                edge = stage_edges_copy[i]
                subject, predicate, obj = edge
                
                # 检查是否是文件执行事件
                action = self._get_action_from_predicate(predicate)
                if action.lower() == "execute" and self._get_entity_type(obj) == "file":
                    # 提取文件名（去掉'file:'前缀）
                    file_name = obj.split(':', 1)[1] if ':' in obj else obj
                    
                    # 寻找同名进程
                    matching_process = None
                    for process in processes:
                        process_name = process.split(':', 1)[1] if ':' in process else process
                        if process_name == file_name:
                            matching_process = process
                            break
                    
                    # 创建新的fork边
                    if matching_process:
                        new_fork_edge = [subject, f"{stage}_Fork", matching_process]
                    else:
                        # 创建新的进程实体
                        new_process = f"process:{file_name}"
                        # 添加到实体集合
                        if new_process not in self.entities:
                            self.entities.append(new_process)
                        processes.append(new_process)
                        # 更新全局出度和入度（新进程初始出度/入度为0）
                        self.global_out_degree[new_process] = 0
                        self.global_in_degree[new_process] = 0
                        new_fork_edge = [subject, f"{stage}_Fork", new_process]
                    
                    # 在当前位置后插入新边
                    stage_edges_copy.insert(i + 1, new_fork_edge)
                    new_edges.append(new_fork_edge)
                    
                    # 更新全局出度和入度
                    self._update_global_degrees(new_fork_edge)
                    
                    i += 1  # 跳过新插入的边
                
                i += 1
            
            # 更新该阶段的边
            self.stage_edges[stage] = stage_edges_copy
        
        # 更新总的边列表
        self._update_all_edges()
        return new_edges
    
    # ========== APPA 算法实现 ==========
    def activity_priority_parent_attribution(self):
        """Activity-Priority Parent Attribution (APPA) 算法"""
        new_edges = []
        
        for stage, stage_edges in self.stage_edges.items():
            processes = self._get_process_entities_in_stage(stage_edges)
            
            # 计算阶段内入度（仅用于识别孤儿进程）
            in_degree = self._calculate_stage_in_degree(stage_edges)
            
            # 获取根实体（第一个三元组的主语）
            if stage_edges:
                root_entity = stage_edges[0][0]
            else:
                continue
            
            # 识别孤儿进程
            orphan_processes = []
            for process in processes:
                # 阶段内入度为0且不是根实体
                if in_degree.get(process, 0) == 0 and process != root_entity:
                    orphan_processes.append(process)
            
            stage_edges_copy = stage_edges.copy()
            
            for orphan in orphan_processes:
                # 获取孤儿的第一次交互
                first_edge, first_idx = self._get_first_interaction(orphan, stage_edges_copy)
                if first_edge is None:
                    continue
                
                # 构建候选父进程池
                candidate_parents = []
                for candidate in processes:
                    if candidate == orphan:
                        continue
                    
                    # 检查候选进程在孤儿第一次交互之前是否有活动（在同一阶段内）
                    has_prior_activity = False
                    for i in range(first_idx):
                        edge = stage_edges_copy[i]
                        if edge[0] == candidate or edge[2] == candidate:
                            has_prior_activity = True
                            break
                    
                    if has_prior_activity:
                        candidate_parents.append(candidate)
                
                if not candidate_parents:
                    continue
                
                # 选择父进程：先按全局出度排序，再按最近活动时间排序
                best_parent = None
                max_global_out_degree = -1
                max_recent_time = -1
                
                for candidate in candidate_parents:
                    cand_global_out_degree = self.global_out_degree.get(candidate, 0)
                    # 获取候选进程在孤儿第一次交互之前的最近活动时间（阶段内）
                    recent_time = self._get_last_interaction_time(candidate, stage_edges_copy, first_idx)
                    
                    # 条件1：全局出度最大
                    # 条件2：在全局出度相同的情况下，最近活动时间最大
                    if (cand_global_out_degree > max_global_out_degree or 
                        (cand_global_out_degree == max_global_out_degree and recent_time > max_recent_time)):
                        max_global_out_degree = cand_global_out_degree
                        max_recent_time = recent_time
                        best_parent = candidate
                
                if best_parent:
                    # 创建新的fork边
                    new_fork_edge = [best_parent, f"{stage}_Fork", orphan]
                    
                    # 在孤儿第一次交互之前插入新边
                    insert_idx = first_idx  # 在第一次交互之前插入
                    stage_edges_copy.insert(insert_idx, new_fork_edge)
                    new_edges.append(new_fork_edge)
                    
                    # 更新全局出度和入度
                    self._update_global_degrees(new_fork_edge)
            
            # 更新该阶段的边
            self.stage_edges[stage] = stage_edges_copy
        
        # 更新总的边列表
        self._update_all_edges()
        return new_edges
    
    # ========== STA 算法实现 ==========
    def sequential_tactical_anchoring(self):
        """Sequential Tactical Anchoring (STA) 算法"""
        new_edges = []
        
        # 获取所有阶段（按顺序）
        stages = list(self.stage_edges.keys())
        
        for i in range(1, len(stages)):
            current_stage = stages[i]
            prev_stage = stages[i-1]
            
            current_edges = self.stage_edges[current_stage]
            prev_edges = self.stage_edges[prev_stage]
            
            if not current_edges or not prev_edges:
                continue
            
            # 当前阶段的根实体
            root_entity = current_edges[0][0]
            
            # 检查根实体是否全局入度为0
            if self.global_in_degree.get(root_entity, 0) == 0:
                # 获取前一阶段的最后一个三元组
                last_edge = prev_edges[-1]
                
                # 确定父进程
                last_object_type = self._get_entity_type(last_edge[2])
                if last_object_type == 'process':
                    parent = last_edge[2]  # 宾语是进程
                else:
                    parent = last_edge[0]  # 主语是进程
                
                # 创建新的fork边
                new_fork_edge = [parent, f"{current_stage}_Fork", root_entity]
                
                # 在当前阶段的开头插入新边
                self.stage_edges[current_stage].insert(0, new_fork_edge)
                new_edges.append(new_fork_edge)
                
                # 更新全局出度和入度
                self._update_global_degrees(new_fork_edge)
        
        # 更新总的边列表
        self._update_all_edges()
        return new_edges
    
    def _update_all_edges(self):
        """更新总的边列表（将所有阶段的边合并）"""
        self.edges = []
        for stage, stage_edges in self.stage_edges.items():
            self.edges.extend(stage_edges)
    
    def repair_all(self):
        """执行完整的修复流程"""
        print("开始路径修复...")
        
        print("\n1. 执行 ISI (Implicit Spawn Inference)...")
        isi_edges = self.implicit_spawn_inference()
        print(f"   ISI新增了 {len(isi_edges)} 条边")
        if isi_edges:
            print("   新增的边:")
            for edge in isi_edges:
                print(f"     {edge[0]} --[{edge[1]}]--> {edge[2]}")
        
        print("\n2. 执行 APPA (Activity-Priority Parent Attribution)...")
        appa_edges = self.activity_priority_parent_attribution()
        print(f"   APPA新增了 {len(appa_edges)} 条边")
        if appa_edges:
            print("   新增的边:")
            for edge in appa_edges:
                print(f"     {edge[0]} --[{edge[1]}]--> {edge[2]}")
        
        print("\n3. 执行 STA (Sequential Tactical Anchoring)...")
        sta_edges = self.sequential_tactical_anchoring()
        print(f"   STA新增了 {len(sta_edges)} 条边")
        if sta_edges:
            print("   新增的边:")
            for edge in sta_edges:
                print(f"     {edge[0]} --[{edge[1]}]--> {edge[2]}")
        
        print(f"\n修复完成！总共新增了 {len(isi_edges) + len(appa_edges) + len(sta_edges)} 条边")
        
        return self.edges
    
    def print_edges(self, edges=None, title="边列表"):
        """打印边列表"""
        if edges is None:
            edges = self.edges
        
        print(f"\n{title} (共{len(edges)}条):")
        print("-" * 80)
        for i, edge in enumerate(edges, 1):
            print(f"{i:2d}. {edge[0]:25s} --[{edge[1]:25s}]--> {edge[2]}")
        print("-" * 80)

def judge_format(rel):
    edge_type=['Fork','Inject','Exit','Create','Execute','Read',
               'Write','Delete','Loadlibrary','Modify_Attribute','Send','Receive',
               'Connect','Readkey','Writekey','Createkey','Deletekey']
    subject_type=['process']
    object_type=['process','file','reg','socket']
    if rel[0].split(':',1)[0] not in subject_type or rel[1] not in edge_type or rel[2].split(':',1)[0] not in object_type:
        return True
    else:
        return False

def get_edges_from_file(file_path):
    edges=[]
    with open(file_path, 'r') as f:
        data = json.load(f)
        # print(data)
        data = data[-1]['phase_relationship']
        # print(data)
        edge_list=[(item['phase'],item['semantic_relationship'].split('[System-level Relationships]:')[-1]) for item in data]
    j=0
    for e in edge_list:
        # print(e)
        matches = re.findall(r'<([^>]+)>', e[1])
        # print(matches)
        # for rel in relationship:
            
        relationship=[i.split(',',2) for i in matches]
        # print(relationship,'\n')['process:script', 'Createkey', 'reg:Same path']
        for i in relationship:
            if judge_format(i):
                continue
            else:
                i[1]=e[0]+'_'+i[1].strip()
                i[0]=i[0].strip()
                i[2]=i[2].strip()
                j+=1
                edges.append(i)
    return edges

def add_order(edges):
    for index in range(len(edges)):
        edges[index][1]=str(index)+'_'+edges[index][1]
    return edges

def covert_to_G(data_list,name,output_path):
    # 创建有向多重图
    G = nx.MultiDiGraph()

    # 创建节点映射字典和边计数器
    node_mapping = {}  # 映射原始节点名到数字ID
    next_node_id = 1   # 节点ID计数器
    edge_counter = {}  # 边计数器：(源节点, 目标节点) -> 下一个key值

    # 遍历数据，提取节点和边信息
    for item in data_list:
        src_str, dst_str = item[0], item[2]
        
        # 处理源节点（数字ID映射）
        if src_str not in node_mapping:
            src_type, src_value = src_str.split(':', 1)
            node_id = next_node_id
            node_mapping[src_str] = node_id
            G.add_node(node_id, type=src_type, value=src_value)
            next_node_id += 1
        else:
            node_id = node_mapping[src_str]
        
        # 处理目标节点（数字ID映射）
        if dst_str not in node_mapping:
            dst_type, dst_value = dst_str.split(':', 1)
            node_id = next_node_id
            node_mapping[dst_str] = node_id
            G.add_node(node_id, type=dst_type, value=dst_value)
            next_node_id += 1
        else:
            node_id = node_mapping[dst_str]
        
        # 准备边参数
        src_id = node_mapping[src_str]
        dst_id = node_mapping[dst_str]
        edge_type = item[1].split('_')[-1]
        
        # 确定边的数字key（同一节点对间的边使用连续数字）
        edge_key = edge_counter.get((src_id, dst_id), 0)
        edge_counter[(src_id, dst_id)] = edge_key + 1
        
        # 添加带属性的边（使用数字key）
        G.add_edge(src_id, dst_id, key=edge_key, type=edge_type,phase=item[1].split('_')[1],order=item[1].split('_')[0])


    # 转换为JSON格式并保存
    graph_data = json_graph.node_link_data(G)
    with open(f"{output_path}/query_graph_{name}", 'w') as f:
        json.dump(graph_data, f, indent=2)

    # print("="*60)
    # print("节点数字映射关系:")
    # for original, node_id in node_mapping.items():
    #     print(f"  {original} → 节点ID: {node_id}")

    # print("="*60)
    return graph_data

def draw_graph(data,name,output_path):
    # 创建有向图
    G = nx.MultiDiGraph()

    # 添加节点
    node_type_colors = {
        'process': 'skyblue',
        'file': 'lightgreen',
        'socket': 'gold',
        'reg': 'salmon'
    }
    for node in data['nodes']:
        node_type = node['type']
        node_id = node['id']
        node_value = node['value']
        G.add_node(node_id, 
                label=node_value,
                node_type=node_type,
                color=node_type_colors.get(node_type, 'gray'))
    
    # 添加边
    phase_abbr = {
        'initial access': 'IA',
        'execution': 'EX',
        'persistence': 'PER',
        'privilege escalation': 'PE',
        'defense evasion': 'DE',
        'credential access': 'CA',
        'discovery': 'DC',
        'lateral movement': 'LM',
        'collection': 'COL',
        'command and control': 'C&C',
        'exfiltration': 'EXF',
        'impact': 'IM'
    }

    edge_labels = {}
    for link in data['links']:
        phase = link['phase']
        order = link['order']
        edge_type = link['type']
        source = link['source']
        target = link['target']
        key = link['key']
        
        # 创建带order和phase的标签
        label = f"{order}: {phase_abbr.get(phase, phase)}-{edge_type}"
        
        G.add_edge(source, target,
                phase=phase,
                order=order,
                edge_type=edge_type,
                label=label)
        
        # 存储边标签
        edge_labels[(source, target, key)] = label

    # 设置可视化布局
    pos = nx.spring_layout(G, seed=42, k=0.5, iterations=100)

    # 创建图形
    plt.figure(figsize=(20, 16))

    # 绘制节点
    node_colors = [G.nodes[n]['color'] for n in G.nodes]
    node_labels = {n: G.nodes[n]['label'] for n in G.nodes}
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2500, edgecolors='black', linewidths=1.5)

    # 绘制边 - 统一使用灰色箭头
    nx.draw_networkx_edges(G, pos, 
                        edge_color='gray', 
                        arrows=True, 
                        arrowstyle='->', 
                        arrowsize=20, 
                        width=1.8,
                        node_size=2500,
                        connectionstyle='arc3,rad=0.1')

    # 添加节点标签
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=11, font_weight='bold')

    # 添加边标签 - 显示order和phase
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=edge_labels,
        font_size=9,
        font_color='black',
        font_weight='bold',
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.5)
    )

    # 创建图例
    node_legend = [Patch(color=color, label=label) 
                for label, color in node_type_colors.items()]

    # 添加攻击阶段缩写图例
    phase_legend = [Patch(facecolor='white', edgecolor='none', 
                        label=f"{abbr}: {full_name}") 
                for full_name, abbr in phase_abbr.items()]
    plt.legend(handles=node_legend + phase_legend, 
           loc='best', 
           title='Node Types & Attack Phases')

    # 设置标题
    plt.title(f'{name.replace(".json","")} Attack Visualization', fontsize=18, pad=20)

    # 优化显示
    plt.axis('off')
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.05)
    plt.savefig(f"{output_path}/query_graph_{name.replace('.json','')}.png")
    plt.show()
    # 图像保存

# from glob import glob
def draw_dot(file):
# 原始JSON数据
  with open(file, 'r') as f:
    data = json.load(f)
  dot = Digraph(comment='Threat Graph')
  dot.attr(rankdir='LR')  # 从左到右布局

  # 添加节点并设置形状
  for node in data['nodes']:
      node_id = str(node['id'])
      label = node['value']
      
      # 根据类型设置不同形状
      if node['type'] == 'process':
          dot.node(node_id, label, shape='diamond')
      elif node['type'] == 'socket':
          dot.node(node_id, label, shape='ellipse')
      elif node['type'] == 'file':
          dot.node(node_id, label, shape='rectangle')
      elif node['type'] == 'reg':
          dot.node(node_id, label, shape='pentagon')
      else:
          dot.node(node_id, label, shape='circle')

  # 添加边
  for link in data['links']:
      source = str(link['source'])
      target = str(link['target'])
      custom_label = f"{link['order']}. {link['phase']}_{link['type']}"
      dot.edge(source, target, label=custom_label)

  # 保存并渲染
  dot.render(file.replace('json','dot'), view=True)
  # print(file.replace('json','dot'))
def draw_dot_with_color(file):
  PHASE_COLORS = {
        # "reconnaissance": "#FF0000",       # 红色
        # "resource_development": "#FF7F00", # 橙色
        "initial_access": "#FFFF00",       # 黄色
        "execution": "#00FF00",            # 绿色
        "persistence": "#0000FF",          # 蓝色
        "privilege_escalation": "#4B0082", # 靛蓝色
        "defense_evasion": "#9400D3",      # 紫罗兰色
        "credential_access": "#FF1493",    # 深粉色
        "discovery": "#00BFFF",            # 深天蓝
        "lateral_movement": "#7CFC00",     # 黄绿色
        "collection": "#20B2AA",          # 浅海洋绿
        "command_and_control": "#FF6347",  # 番茄红
        "exfiltration": "#8A2BE2",         # 紫罗兰蓝色
        "impact": "#FF69B4",               # 热粉色
        # 默认颜色
        "default": "#A9A9A9"               # 暗灰色
    }
# 原始JSON数据
  with open(file, 'r') as f:
    data = json.load(f)
  dot = Digraph(comment='Threat Graph')
  dot.attr(rankdir='LR')  # 从左到右布局

  # 添加节点并设置形状
  for node in data['nodes']:
      node_id = str(node['id'])
      label = node['value']
      
      # 根据类型设置不同形状
      if node['type'] == 'process':
          dot.node(node_id, label, shape='diamond')
      elif node['type'] == 'socket':
          dot.node(node_id, label, shape='ellipse')
      elif node['type'] == 'file':
          dot.node(node_id, label, shape='rectangle')
      elif node['type'] == 'reg':
          dot.node(node_id, label, shape='pentagon')
      else:
          dot.node(node_id, label, shape='circle')

  for link in data['links']:
        source = str(link['source'])
        target = str(link['target'])
        
        # 创建自定义标签：order + "_" + phase + "_" + type
        custom_label = f"{link['order']}_{link['phase']}_{link['type']}"
        
        # 获取对应阶段的颜色
        phase_key = link['phase'].replace(' ', '_').lower()  # 标准化阶段名称
        edge_color = PHASE_COLORS.get(phase_key, PHASE_COLORS['default'])
        
        # 设置边的属性：标签、颜色、字体大小
        dot.edge(
            source, 
            target, 
            label=custom_label,
            color=edge_color,
            fontsize='10',
            fontcolor=edge_color
        )
  # 保存并渲染
  dot.render(file.replace('.json','_with_color.dot'), view=True)

if __name__ == '__main__':
    # draw_dot_with_color('test.json')
    pass