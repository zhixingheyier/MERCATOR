
from selenium import webdriver
from selenium.webdriver.chrome.service import Service  # 新增导入
import time
import random
import tqdm
from bs4 import BeautifulSoup
import glob
import json
import os
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

def parse_blog_content(html):
    article = BeautifulSoup(html, 'html.parser')
    try:
        soup= article.find('article', class_='research-layout--wrapper row')
        header = soup.find('div', class_='col-xs-12 col-md-12 one-column')
        # print(header)
        main_title = header.find('h1',class_="article-details__title").get_text(strip=True)
        body = soup.find('main',class_='main--content col-xs-12 col-lg-8 col-lg-push-2')
    except Exception as e:
        print('处理失败：',e)
        return {}
    result = []
    title_0 = {
        "level": 0,
        "content": main_title
    }
    result.append(title_0)

    texts = body.find_all('div', class_='richText')
    for richText in texts:
        # print('richText',richText)
        for div in richText.find_all('div'):
            for child in div:
                if child.name == 'p':
                    if child.find('span',class_='body-subhead-title'):
                        section = {
                            "level": 2,
                            "content": child.find('span',class_='body-subhead-title').get_text(strip=True)
                        }
                        result.append(section)
                    else:
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
                    try:
                        if child.find('span',class_='body-subhead-title'):
                            section = {
                                "level": 2,
                                "content": child.find('span',class_='body-subhead-title').get_text(strip=True)
                            }
                            result.append(section)
                    except Exception as e:
                        print(child)
                        print('处理未处理的标签时发生错误：', child,': ', e)
                    # print('未处理的标签：', child.name)
    return result
def main():
    with open(r'C:\Users\lesliu\Desktop\selieum\trendmicro\url_name_trandmicro.txt', 'r') as f:
        url_name = f.read().splitlines()
    url_name=[[(item.split(' '))[0],(item.split(' ')[1])] for item in url_name]
    html_path=r'C:\Users\lesliu\Desktop\selieum\trendmicro\blog_html'
    # download_html(url_name,html_path)
    content_dict=get_html(html_path)
    output_json_path=r'C:\Users\lesliu\Desktop\selieum\trendmicro\blog_json'
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


