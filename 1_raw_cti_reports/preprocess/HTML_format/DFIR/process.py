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
def download_html_multithread(url_name, path, max_workers=8):
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
def download_html(url_name,path):
    file_list = glob.glob(path+'\\*.html')
    file_list = [file.split('\\')[-1] for file in file_list]
# 创建Service对象指定驱动路径
    # content_dict={}
    service = Service(executable_path=r'C:\Users\lesliu\Desktop\selieum\chromedriver-win64\chromedriver.exe')
    browser = webdriver.Chrome(service=service)  # 改为service参数
    for item in tqdm.tqdm(url_name):
        try:
        #随机等待几秒
            if item[1]+'.html' not in file_list:
                time.sleep(random.randint(1,3))
                browser.get(item[0])
                html = browser.page_source
                # content_dict[item[1]]=html
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

def parse_blog_content(key,html):
    print('正在处理：',key)
    article = BeautifulSoup(html, 'html.parser')
    try:
        main= article.find('div', class_='entry-content-holder')
        header= main.find('header', class_='entry-header')
        body= main.find('div', class_='entry-content')
    except Exception as e:
        print(f'{key}没有找到header or body，处理失败：',e)
        return []
    bad_list=['2024_03_04_threat-brief-wordpress-exploit-leads-to-godzilla-web-shell-discovery-new-cve.pdf.html',
              '2020_05_08_adfind-recon.pdf.html',
              '2020_06_10_lockbit-ransomware-why-you-no-spread.pdf.html',
              '2020_12_13_defender-control.pdf.html',
              '2020_04_04_gogoogle-ransomware.pdf.html',
              '2020_04_14_dharma-ransomware.pdf.html',
              '2020_04_20_sqlserver-or-the-miner-in-the-basement.pdf.html',
              '2020_07_13_ransomware-again-but-we-changed-the-rdp-port.pdf.html',
              '2020_04_30_tricky-pyxie.pdf.html',
              '2022_01_24_cobalt-strike-a-defenders-guide-part-2.pdf.html',
              '2024_08_12_threat-actors-toolkit-leveraging-sliver-poshc2-batch-scripts.pdf.html',
              '2023_01_23_sharefinder-how-threat-actors-discover-file-shares.pdf.html',
              '2022_06_06_will-the-real-msiexec-please-stand-up-exploit-leads-to-data-exfiltration.pdf.html',
              '2022_08_08_bumblebee-roasts-its-way-to-domain-admin.pdf.html',
              '2020_08_31_netwalker-ransomware-in-1-hour.pdf.html'
              ]
    other_writetype_list=[
                '2022_02_07_qbot-likes-to-move-it-move-it.pdf.html',
                '2021_12_13_diavol-ransomware.pdf.html',
                '2021_11_29_continuing-the-bazar-ransomware-story.pdf.html',
                '2021_11_01_from-zero-to-domain-admin.pdf.html',
                '2021_10_18_icedid-to-xinglocker-ransomware-in-24-hours.pdf.html',
                '2021_10_04_bazarloader-and-the-conti-leaks.pdf.html',
                '2021_09_13_bazarloader-to-conti-ransomware-in-32-hours.pdf.html'
                ]
    special_list=['2020_08_03_dridex-from-word-to-domain-dominance.pdf.html',
                  '2021_08_29_cobalt-strike-a-defenders-guide.pdf.html',
                  '2020_06_16_the-little-ransomware-that-couldnt-dharma.pdf.html']
    if key in bad_list:
        print('bad_list, skip!')
        print('='*50)
        return []
    elif key in special_list:
        print('special_list, process latter!')
        print('='*50)
        return[]
        try:
            main_title = header.find('h1').get_text(strip=True)
            result = []
            title_0 = {
                "level": 0,
                "content": main_title
            }
            result.append(title_0)
            for child in body:
                if child.name == 'h2':
                    section = {
                        "level": 2,
                        "content": child.get_text(strip=True).replace(':','')
                    }
                    result.append(section)
                elif child.name == 'h3':
                    section = {
                        "level": 2,
                        "content": child.get_text(strip=True).replace(':','')
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
                    pass
            print('='*50)
            return result
        except Exception as e:
            print('处理失败：',key,'，错误信息：', e)
            return []
    elif key in other_writetype_list:
        # return []
        print('other_list, process now!')
        try:
            main_title = header.find('h1').get_text(strip=True)
            result = []
            title_0 = {
                "level": 0,
                "content": main_title
            }
            result.append(title_0)
            for child in body:
                if child.name == 'h2':
                    section = {
                        "level": 2,
                        "content": child.get_text(strip=True).replace(':','')
                    }
                    result.append(section)
                elif child.name == 'h3':
                    section = {
                        "level": 2,
                        "content": child.get_text(strip=True).replace(':','')
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
                #假如name等于div，类别为markdown，则继续处理
                elif child.name == 'div' and child.get('class') == ['markdown']:
                    for grandchild in child:
                        if grandchild.name == 'h2':
                            section = {
                                "level": 2,
                                "content": grandchild.get_text(strip=True).replace(':','')
                            }
                            result.append(section)
                        elif grandchild.name == 'h3':
                            section = {
                                "level": 2,
                                "content": grandchild.get_text(strip=True).replace(':','')
                            }
                            result.append(section)
                        elif grandchild.name == 'h4':
                            section = {
                                "level": 3,
                                "content": grandchild.get_text(strip=True)
                            }
                            result.append(section)

                        elif grandchild.name == 'p':
                            section = {
                                "level": 3,
                                "content": grandchild.get_text(strip=True)
                            }
                            result.append(section)
                        elif grandchild.name in ['ul', 'ol']:
                            ul_content = [li.get_text(strip=True) for li in grandchild.find_all('li')]
                            ol_content = ' \n'.join(ul_content)
                            section = {
                                "level": 3,
                                "content": ol_content
                            }
                            result.append(section)
                else:
                    # print('未处理的标签：',child.name)
                    continue

            print('='*50)
            return result
        except Exception as e:
            print(f'{key}处理失败：',e)
            return []
    else:
        try:
            # return []
            # 添加主标题
            main_title = header.find('h1').get_text(strip=True)
            result = []
            title_0 = {
                "level": 0,
                "content": main_title
            }
            result.append(title_0)

            h2_content=[]
            h3_content=[]
            h4_content=[]
            h5_content=[]
            for child in body:
                if child.name=='h2':
                    h2_content.append(child.get_text(strip=True).replace(':',''))
                elif child.name=='h3':
                    h3_content.append(child.get_text(strip=True).replace(':',''))
                elif child.name=='h4':
                    h4_content.append(child.get_text(strip=True).replace(':',''))
                elif child.name=='h5':
                    h5_content.append(child.get_text(strip=True).replace(':',''))
            #判断所有h2、h3、h4、h5是否包含Initial Access-->都在h2或者h3中
            # if 'Initial Access' in h2_content or 'Initial Access' in h3_content:
            #     print(f'{key}的h2、h3有Initial Access')
                
            # else:
            #     print(f'{key}的h2、h3没有Initial Access')
            #     print('h2: ',h2_content)
            #     print('h3: ',h3_content)
            #     print('h4: ',h4_content)
            #     print('h5: ',h5_content)

            if 'Initial Access' in h2_content and 'Initial Access' not in h3_content:
                print(f'{key}的h2有Initial Access')
                
                for child in body:
                    if child.name == 'h2':
                        section = {
                            "level": 2,
                            "content": child.get_text(strip=True).replace(':','')
                        }
                        result.append(section)
                    elif child.name == 'h3':
                        section = {
                            "level": 3,
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
                        # print('未处理的标签：',child.name)
                        continue
                print('='*50)
                return result
            elif 'Initial Access' in h3_content and 'Initial Access' not in h2_content:
                print(f'{key}的h3有Initial Access')
                for child in body:
                    if child.name == 'h2':
                        section = {
                            "level": 2,
                            "content": child.get_text(strip=True).replace(':','')
                        }
                        result.append(section)
                    elif child.name == 'h3':
                        section = {
                            "level": 2,
                            "content": child.get_text(strip=True).replace(':','')
                        }
                        result.append(section)
                    elif child.name == 'p':
                        section = {
                            "level": 3,
                            "content": child.get_text(strip=True)
                        }
                        result.append(section)
                    elif child.name == 'h4':
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
                        # print('未处理的标签：',child.name)
                        continue
                print('='*50)
                return result
            else:
                print(f'{key}的h2、h3没有Initial Access')
                return []

        except Exception as e:
            print(f'{key}处理失败：',e)
            return []
        
def main():
    # with open(r'.\url_and_name.txt', 'r') as f:
    #     url_name = f.read().splitlines()
    # url_name=[[(item.split(' '))[0],(item.split(' ')[1])] for item in url_name]
    html_path=r'.\blog_html'
    # if not os.path.exists(html_path):
    #     os.makedirs(html_path)
    # download_html(url_name,html_path)
    content_dict=get_html(html_path)
    output_json_path=r'.\blog_json'
    if not os.path.exists(output_json_path):
        os.makedirs(output_json_path)
    # content_all=[]
    for key in content_dict.keys():
        
        output_json = parse_blog_content(key,content_dict[key])
        if output_json:
            with open(output_json_path+'\\'+key+'.json', 'w', encoding='utf-8') as f:
                json.dump(output_json, f, ensure_ascii=False, indent=4)
        # break
    #     content_all.extend(output_json)
    # print(list(set(content_all)))

if __name__ == '__main__':
    main()
    


