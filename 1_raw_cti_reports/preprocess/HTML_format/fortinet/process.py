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
        header= article.find('section', class_='b4-hero aem-GridColumn aem-GridColumn--default--12')
        body= article.find('div', class_='responsivegrid aem-GridColumn aem-GridColumn--default--12')
    except Exception as e:
        print('没有找到header or body，处理失败：',e)
        return []
    try:
        #添加主标题
        main_title = header.find('h1').get_text(strip=True)
        result = []
        title_0 = {
            "level": 0,
            "content": main_title
        }
        result.append(title_0)

        #判断文章主体格式
        judge_1 = body.find('div', class_='Table-Content aem-GridColumn aem-GridColumn--default--12')
        judge_2 = body.find('div', class_='cmp cmp-text aem-GridColumn aem-GridColumn--default--12')

        # content_type=[]

        if judge_1 and not judge_2:
            content= judge_1.find('div', class_='aem-GridColumn aem-GridColumn--default--8 b3-blog-list__column-right scrolling-content automatic')
            texts= content.find_all('div', class_='cmp cmp-text')
            for text in texts:
                for child in text:
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
                        # print('未处理的标签：',child.name)
                        continue
            return result
            # pass
        elif judge_2 and not judge_1:
            content=body.find_all('div', class_='cmp cmp-text aem-GridColumn aem-GridColumn--default--12')
            for text in content:
                for child in text:
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
                        # print('未处理的标签：',child.name)
                        continue
            return result


        else:
            print('文章具有另外的行文格式')
            return []

    except Exception as e:
        print('提取文本出现问题：',e)
        return []
def main():
    # with open(r'C:\Users\lesliu\Desktop\selieum\fortinet\url_name.txt', 'r') as f:
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
    for key in content_dict.keys():
        print('正在处理：',key)
        output_json = parse_blog_content(content_dict[key])
        if output_json:
            with open(output_json_path+'\\'+key+'.json', 'w', encoding='utf-8') as f:
                json.dump(output_json, f, ensure_ascii=False, indent=4)
        # break


if __name__ == '__main__':
    main()


