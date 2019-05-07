"""
    author: libra
    date: 2018-09-26
"""
from urllib.parse import urlencode, unquote
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from PIL import Image
from config import COOKIES
import pytesseract
import datetime
import requests
import random
import base64
import json
import time
import re
import os
import io

num =0



headers = {
    'Cookie': COOKIES,
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
}
base_dir = os.path.abspath(os.path.dirname(__file__))

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(chrome_options=chrome_options)

driver.get('file://%s/template.html' % base_dir)

with open('%s/Raphael.js' % base_dir, 'r') as f:
    driver.execute_script(f.read())

js_template = """
document.getElementsByClassName('view-value')[0].innerHTML = '%s'
"""

def get_res1(html):
    """
        get res1, parse html to get res1.
    """
    res = re.search(r'.*PPval\.ppt = \'(.*?)\'', html)
    res = unquote(res[1]) if res else None
    return res


def get_res2(html):
    """
        get res2, parse and get js code in the html,
        then run this js code in the browser, need Raphael.js
    """
    res_script = re.search(r'<script type="text/javascript">\n(T\(function[\d\D]*?)</script>', html)
    res_script = res_script[1] if res_script else None
    res_script_list = res_script.split('\n')
    first_var = re.search(r'(.{15}) = \'.{50}\';', res_script)[1].lstrip(' ')
    all_var = []
    all_var.append(first_var)
    final_script_list = []
    res_var = None
    for line in res_script_list:
        if res_var:
            break
        for var in all_var:
            if var in line:
                temp_var = re.search(r'(.*?) = .*?', line)
                if temp_var:
                    temp_var = temp_var[1].lstrip(' ')
                    all_var.append(temp_var)
                    final_script_list.append(line.strip(' '))
                else:
                    res_var = line.lstrip(' ').rstrip(');').replace('BID.res2(', '')
                break
    final_script = '\n'.join(final_script_list)
    res_script = """
    function %s_func () {
        %s
        return %s
    }
    return %s_func()
    """ % (res_var, final_script, res_var, res_var)
    result = driver.execute_script(res_script)
    return result


def get_res3_datas(res1, res2, startdate, enddate):
    """
        get res3, 
    """
    url_args = {
        'res': res1,
        'res2': res2,
        'startdate': startdate,
        'enddate': enddate,
    }
    url = 'http://index.baidu.com/Interface/Search/getSubIndex/?' + urlencode(url_args)
    html = request(url)
    datas = json.loads(html)
    res3_list = datas['data']['all'][0]['userIndexes_enc'].split(',')
    res3_datas = []
    cur_date = datetime.datetime.strptime(startdate, '%Y-%m-%d')
    for res3 in res3_list:
        res3_datas.append({
            'res3': res3,
            'date': cur_date.strftime('%Y-%m-%d')
        })
        cur_date += datetime.timedelta(days=1)
    return res3_datas


def get_background(url):
    """
        get backgroud-img
    """
    response = requests.get(url, headers=headers)
    img_base64 = base64.b64encode(response.content).decode()
    return img_base64


def get_the_index_html(res1, res2, res3):
    """
        get the BaiduIndex of html
    """
    url_args = {
        'res': res1,
        'res2': res2,
        'res3[]': res3,
    }
    url = 'http://index.baidu.com/Interface/IndexShow/show/?' + urlencode(url_args)
    html = request(url)
    if html:
        datas = json.loads(html)
        html_code = datas['data']['code'][0]
        img_url = re.search(r'url\((".*?")\)}', html_code)[1]
        img_base64 = get_background('http://index.baidu.com' + img_url.replace('"', ''))
        html_code = html_code.replace(img_url, 'data:image/png;base64,%s' % img_base64)
        return html_code


def request(url):
    """
        a simple function of use http/get
    """
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response.encoding = 'gbk'
        result = response.text.replace('\r', '')
    else:
        print('request fail!')
        result = None

    return result


def get_the_index(html):
    """
        get reuslt about index of baidu
        ps: use js to change html and crop image about index of baidu
    """
    js_code = js_template % html
    driver.execute_script(js_code)
    width_list = re.findall(r'style="width:(\d*?)px;"', html)
    # print('width_list:'+str(width_list))
    screen_hot = driver.get_screenshot_as_base64()
    # print('screen_hot:'+str(screen_hot))
    img_byte = base64.b64decode(screen_hot)
    # print('img_byte长度:'+str(len(img_byte)))
    the_index = parse_index_img(img_byte, width_list)
    # print('the_index:'+str(the_index))
    return the_index


def parse_index_img(img_byte, width_list):
    """
        get index by tesseract to parse image
    """
    all_width = 0
    for width in width_list:
        all_width += int(width)

    im = Image.open(io.BytesIO(img_byte)).convert('RGB')
    # im = im.crop((0,8,all_width*2,32))
    im = im.crop((0,4,all_width,16))
    # im2 = im.crop((3,4,all_width,16))
    # im3 = im.crop((4,4,all_width,16))
    # im4 = im.crop((1,3,all_width,16))
    # im5 = im.crop((1,4,all_width,16))
    im = im.resize((im.size[0]*6, im.size[1]*6))
    
    #保存图片
    # global num
    # num +=1
    # im.save("./test%s.png"%num)
    result = pytesseract.image_to_string(im, lang='num',config='digits')
    # print('result_ori:'+str(result))
    result = result.replace(' ', '').replace('.', '').replace(',', '')
    # print('result_rep:'+str(result))
    return result


def sleep_fuc():
    time.sleep(random.randint(1100, 2100)*0.001)


def get_index_one_word(li):
    keyword, startdate, enddate=li
    url_args = {
        'tpl': 'trend',
        'word': keyword.encode('gbk')
    }
    url = 'http://index.baidu.com/?' + urlencode(url_args)
    html = request(url)
    if html:
        res1 = get_res1(html)
        # print('res1：'+str(res1))
        res2 = get_res2(html)
        # print('res2：'+str(res2))
        res3_datas = get_res3_datas(res1, res2, startdate, enddate)
        # print('res3_datas'+str(res3_datas))
        #用来存储一个关键词的内容
        results_one =[]
        for res3_data in res3_datas:
            sleep_fuc()
            res3 = res3_data['res3']
            # print('res3：'+str(res3))
            date = res3_data['date']
            html = get_the_index_html(res1, res2, res3)
            # print('html长度:'+str(len(html)))
            the_index = get_the_index(html)
            # result = {
            #     'keyword': keyword,
            #     'date': date,
            #     'the_index': the_index,
            # }
            result=[keyword,date,the_index]
            results_one.append((result))
        return results_one

def get_all_index(lis):
    results_all=[]
    for li in lis:
        results_one = get_index_one_word(li)
        results_all.extend(results_one)
    return results_all
    

if __name__ == "__main__":
    import datetime
    import pandas as pd 
    time_now= datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    time_now2= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #设置起始日期
    # lis=[['QQ飞车', '2018-10-01', '2018-10-02'],
    # ['QQ', '2018-10-01', '2018-10-02']]
    lis=[['IU', '2018-09-24', '2018-10-23']]
    results_all = get_all_index(lis)
    df = pd.DataFrame(data=results_all,columns=['关键词','日期','指数'])
    df.index=list(range(1,len(df)+1))
    df['抓取时间']= time_now2
    writer = pd.ExcelWriter('百度指数%s.xlsx'%time_now)
    df.to_excel(writer,'百度指数')
    writer.save()

    driver.quit()
