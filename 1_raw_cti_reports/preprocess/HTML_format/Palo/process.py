
from selenium import webdriver
from selenium.webdriver.chrome.service import Service  # 新增导入
import time
import random
import tqdm
from bs4 import BeautifulSoup
import json
import os
import threading
import glob
from concurrent.futures import ThreadPoolExecutor


# 线程安全的下载函数（每个线程独立实例）
def thread_task(url_pair, path, file_set):
    service = Service(executable_path=r'C:\Users\lesliu\Desktop\selieum\chromedriver-win64\chromedriver.exe')
    try:
        # 每个线程创建独立浏览器实例[7,9](@ref)
        browser = webdriver.Chrome(service=service)
        url, filename = url_pair
        
        if f"{filename}.html" not in file_set:
            # 随机延迟（线程独立）
            time.sleep(random.randint(1,3))
            
            # 执行请求
            browser.get(url)
            html = browser.page_source
            
            # 线程安全写入（通过文件名唯一性保证）[9](@ref)
            with open(f"{path}\\{filename}.html", 'w', encoding='utf-8') as f:
                f.write(html)
                
    except Exception as e:
        print(f"处理失败：{filename}，错误信息：{e}")
    finally:
        browser.quit()

# 主下载函数
def download_html(url_name, path, max_workers=10):
    # 预生成文件集合（避免重复检查）[5,10](@ref)
    file_list = glob.glob(path + '\\*.html')
    file_set = {file.split('\\')[-1].replace('.html', '') for file in file_list}
    
    # 筛选未下载的URL[5](@ref)
    todo_urls = [(url, name) for url, name in url_name if f"{name}.html" not in file_set]
    
    # 创建进度条
    progress = tqdm.tqdm(total=len(todo_urls), desc="下载进度")
    
    # 线程池执行[6,8](@ref)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for url_pair in todo_urls:
            future = executor.submit(
                thread_task,
                url_pair,
                path,
                file_set  # 传递集合避免重复检查
            )
            futures.append(future)
            # 进度更新
            future.add_done_callback(lambda p: progress.update())
        
        # 等待所有任务完成
        for future in futures:
            future.result()
    
    progress.close()
# def download_html(url_name,path):
#     file_list = glob.glob(path+'\\*.html')
#     file_list = [file.split('\\')[-1] for file in file_list]
# # 创建Service对象指定驱动路径
#     # content_dict={}
#     service = Service(executable_path=r'C:\Users\lesliu\Desktop\selieum\chromedriver-win64\chromedriver.exe')
#     browser = webdriver.Chrome(service=service)  # 改为service参数
#     for item in tqdm.tqdm(url_name):
#         try:
#         #随机等待几秒
#             if item[1]+'.html' not in file_list:
#                 time.sleep(random.randint(1,3))
#                 browser.get(item[0])
#                 html = browser.page_source
#                 # content_dict[item[1]]=html
#                 with open(path+'\\'+item[1]+'.html','w',encoding='utf-8') as f:
#                     f.write(html)
#         except Exception as e:
#             print('处理失败：',item[1],'，错误信息：', e)
#     browser.quit()
def get_html(html_path):
    path_list= glob.glob(html_path+'\\*.html')
    content_dict={}
    for path in path_list:
        with open(path,'r',encoding='utf-8') as f:
            html=f.read()
            content_dict[path.split('\\')[-1]]=html
    return content_dict

def parse_blog_content(html):
    article = BeautifulSoup(html, 'html.parser')
    try:
        main=article.find('main',class_='main')
        if not main:
            return []
    except Exception as e:
        print('没有找到main结构：',e)
        return []
    def get_good_structrue(main):
        try:#解析结构体完备的html
            header = main.find('section', class_="section section--article")
            main_title = header.find('h1').get_text(strip=True)
            body = main.find('section',class_='section blog-contents')

            result = []
            title_0 = {
                "level": 0,
                "content": main_title
            }
            result.append(title_0)
            contents = body.find('div', class_='be__contents-wrapper')
            sections = contents.find_all('div', class_='section-wrapper')
            # if not sections:
            #     return {}
            # child_type=[]
            for section in sections:
                for child in section.children:
                    # child_type.append(child.name)
                    if child.name == 'h2':
                        section = {
                            "level": 1,
                            "content": child.get_text(strip=True)
                        }
                        result.append(section)
                    elif child.name == 'h3':
                        section = {
                            "level": 2,
                            "content": child.get_text(strip=True)
                        }
                        result.append(section)
                    elif child.name == 'p':
                        section = {
                            "level": 3,
                            "content": child.get_text(strip=True)
                        }
                        result.append(section)
                    elif child.name in ['ul', 'ol']:
                        ul_content = [li.get_text(strip=True) for li in child.find_all('li')]
                        ol_content = ' \n'.join(ul_content)
                        section = {
                            "level": 3,
                            "content": ol_content
                        }
                        result.append(section)
                    else:
                        # print('未处理的标签：', child.name)
                        continue
            # print('child_type',list(set(child_type)))
            return result
        except Exception as e:
            print('处理失败：',e)
            return []
    def get_bad_structrue(main):
        try:#解析结构体不完整的html
            header = main.find('section', class_="section section--article")
            main_title = header.find('h1').get_text(strip=True)
            body = main.find('section',class_='section blog-contents')
            result = []
            title_0 = {
                "level": 0,
                "content": main_title
            }
            result.append(title_0)
            contents = body.find('div', class_='be__contents-wrapper')
            for child in contents.children:
                if child.name == 'h2':
                    section = {
                        "level": 1,
                        "content": child.get_text(strip=True)
                    }
                    result.append(section)
                elif child.name == 'h3':
                    section = {
                        "level": 2,
                        "content": child.get_text(strip=True)
                    }
                    result.append(section)
                elif child.name == 'p':
                    section = {
                        "level": 3,
                        "content": child.get_text(strip=True)
                    }
                    result.append(section)
                elif child.name in ['ul', 'ol']:
                    ul_content = [li.get_text(strip=True) for li in child.find_all('li')]
                    ol_content = ' \n'.join(ul_content)
                    section = {
                        "level": 3,
                        "content": ol_content
                    }
                    result.append(section)
                elif child == '\n':
                    continue
                else:
                    # print('未处理的标签：', child.name)
                    continue
            return result
        except Exception as e:
            print('处理失败：',e)
            return []
    
    result=get_good_structrue(main)
    if not result or len(result)==1:
        result=get_bad_structrue(main)
        if not result or len(result)==1:
            print('内容提取失败')
    return result
    
def main():
    # with open(r'C:\Users\lesliu\Desktop\selieum\Palo\url_name.txt', 'r') as f:
    #     url_name = f.read().splitlines()
    # url_name=[[(item.split(' '))[0],(item.split(' ')[1])] for item in url_name]
    html_path=r'.\blog_html'
    # html_path_test=r"C:\Users\lesliu\Desktop\selieum\Palo\test"
    # if not os.path.exists(html_path):
    #     os.makedirs(html_path)
    # download_html(url_name,html_path)
    content_dict=get_html(html_path)
    output_json_path=r'.\blog_json'
    if not os.path.exists(output_json_path):
        os.makedirs(output_json_path)
    for key in content_dict.keys():
        print('正在处理：',key)
        output_json = parse_blog_content(content_dict[key])
        if output_json:
            with open(output_json_path+'\\'+key+'.json', 'w', encoding='utf-8') as f:
                json.dump(output_json, f, ensure_ascii=False, indent=4)
        # break


if __name__ == '__main__':
    main()


