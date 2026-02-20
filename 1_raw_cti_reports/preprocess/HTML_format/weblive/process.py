
from selenium import webdriver
from selenium.webdriver.chrome.service import Service  # 新增导入
import time
import random
import tqdm
from bs4 import BeautifulSoup
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time, random, glob, tqdm

# 创建全局锁（保护文件写入和进度条）
file_lock = threading.Lock()
progress_lock = threading.Lock()

def process_single_item(item, path, file_list, need_code_path):
    """ 处理单个URL的线程任务 """
    content_dict = {}
    service = Service(executable_path=r'C:\Users\28381\Desktop\selieum\chromedriver-win64\chromedriver.exe')
    browser = webdriver.Chrome(service=service)  # 每个线程独立实例
    
    try:
        if item[1]+'.html' not in file_list:
            time.sleep(random.randint(1,3))
            browser.get(item[0])
            html = browser.page_source
            content_dict[item[1]] = html

            if 'Help us in the fight against internet bots' in html:
                with file_lock:  # 加锁写入文件
                    with open(need_code_path, 'a', encoding='utf-8') as f:
                        f.write(item[1]+'\n')
            else:
                with file_lock:
                    with open(f"{path}\\{item[1]}.html", 'w', encoding='utf-8') as f:
                        f.write(html)
    except Exception as e:
        print(f'处理失败：{item[1]}，错误信息：{e}')
    finally:
        browser.quit()

def download_html_multithread(url_name, path):
    """ 多线程版本的主函数 """
    file_list = glob.glob(path + '\\*.html')
    file_list = [file.split('\\')[-1] for file in file_list]
    need_code_path = path + '\\need_code.txt'
    
    # 创建线程池（建议线程数=CPU核心数*2）
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        # 使用线程安全的进度条
        with tqdm.tqdm(total=len(url_name), desc="下载进度") as pbar:
            for item in url_name:
                future = executor.submit(
                    process_single_item, 
                    item, path, file_list, need_code_path
                )
                future.add_done_callback(lambda _: pbar.update(1))
                futures.append(future)
            
            # 等待所有任务完成
            for future in futures:
                future.result()
def download_html(url_name,path):
    file_list = glob.glob(path+'\\*.html')
    file_list = [file.split('\\')[-1] for file in file_list]
# 创建Service对象指定驱动路径
    content_dict={}
    service = Service(executable_path=r'C:\Users\28381\Desktop\selieum\chromedriver-win64\chromedriver.exe')
    browser = webdriver.Chrome(service=service)  # 改为service参数
    for item in tqdm.tqdm(url_name):
        try:
        #随机等待几秒
            if item[1]+'.html' not in file_list:
                time.sleep(random.randint(1,3))
                browser.get(item[0])
                html = browser.page_source
                content_dict[item[1]]=html
                need_code_path= path+'\\need_code.txt'
                if 'Help us in the fight against internet bots' in html:
                    with open(need_code_path,'a',encoding='utf-8') as f:
                        f.write(item[1]+'\n')
                    # print('需要验证码：',item[1])
                else:
                    with open(path+'\\'+item[1]+'.html','w',encoding='utf-8') as f:
                        f.write(html)
        except Exception as e:
            print('处理失败：',item[1],'，错误信息：', e)
    browser.quit()
def get_html(html_path):
    path_list= glob.glob(html_path+'\\*.html')
    content_dict={}
    for path in path_list:
        with open(path,'r',encoding='utf-8') as f:
            html=f.read()
            content_dict[path.split('\\')[-1]]=html
    return content_dict

def parse_blog_content(html):
    # print(html)
    soup= BeautifulSoup(html,'html.parser')
    try:
        header = soup.find('div', class_='article-header')
        # print(header)
        main_title = header.find('h1',class_="page-headline").get_text(strip=True)
        body = soup.find('div',class_='article-body')
        sider= soup.find('div',class_='sidebar col col-lg-4 ps-5 d-none d-lg-block position-sticky')
        sider= sider.find('nav',class_='table-of-contents')
        # flag=False
        sider_head= sider.find('h2',class_='table-of-contents__title')
        sider_content= sider.find_all('li',class_='table-of-contents__item')
        sider_content=[item.get_text(strip=True) for item in sider_content]
        flag=False
        if 'Technical analysis' in sider_content:
            flag=True
        if not flag:
            print('不包含Technical analysis')
            return []

    except Exception as e:
        # print('处理失败：',e)
        return []
    result = []
    
    title_0 = {
        "level": 0,
        "content": main_title
    }

    result.append(title_0)

    # sider_app= {
    #     "level": 1,
    #     "content": sider_content
    # }
    # result.append(sider_app)
    TA_flag= False
    for child in body:
        if child.name == 'h2' and child.get_text(strip=True) == 'Technical analysis':
            section = {
                "level": 1,
                "content": 'Technical analysis Start'
            }
            result.append(section)
            TA_flag=True
        # if child.name == 'h2' and TA_flag:
            section = {
                "level": 2,
                "content": child.get_text(strip=True)
            }
            result.append(section)
        if child.name == 'h2' and child.get_text(strip=True) != 'Technical analysis' and TA_flag:
            section = {
                "level": 1,
                "content": 'Technical analysis Stop'
            }
            result.append(section)
            TA_flag=False
        if child.name == 'h3' and TA_flag:
            section = {
                "level": 3,
                "content": child.get_text(strip=True)
            }
            result.append(section)
        if child.name == 'h4' and TA_flag:
            section = {
                "level": 4,
                "content": child.get_text(strip=True)
            }
            result.append(section)
        elif child.name == 'p' and TA_flag:
            section = {
                "level": 5,
                "content": child.get_text(strip=True)
            }
            result.append(section)
        elif child.name in ['ul', 'ol'] and TA_flag:
            ul_content = [li.get_text(strip=True) for li in child.find_all('li')]
            ol_content = ' \n'.join(ul_content)
            section = {
                "level": 5,
                "content": ol_content
            }
            result.append(section)
        elif child == '\n' and TA_flag:
            continue
        else:
            # print('未处理的标签：', child.name)
            pass
    return result
def main():
    # with open(r'C:\Users\lesliu\Desktop\selieum\weblive\url_name_welivesecurity.txt', 'r') as f:
    #     url_name = f.read().splitlines()
    # url_name=[[(item.split(' '))[0],(item.split(' ')[1])] for item in url_name]
    html_path=r'C:\Users\lesliu\Desktop\selieum\weblive-400+\weblive\blog_html'
    # if not os.path.exists(html_path):
    #     os.makedirs(html_path)
    # download_html_multithread(url_name,html_path)
    content_dict=get_html(html_path)
    output_json_path=r'C:\Users\lesliu\Desktop\selieum\weblive-400+\weblive\blog_json'
    if not os.path.exists(output_json_path):
        os.makedirs(output_json_path)
    for key in content_dict.keys():
        print(key)
        output_json = parse_blog_content(content_dict[key])
        if output_json:
            with open(output_json_path+'\\'+key+'.json', 'w', encoding='utf-8') as f:
                json.dump(output_json, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()
