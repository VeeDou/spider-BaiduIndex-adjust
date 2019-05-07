一：相关配置信息
python版本号 3.6.1
1.安装依赖库：pip install -r requirements.txt
2.确保 config.py  template.html  Raphael.js 和 get_index 都在同一目录下
3.安装tesserac-ocr，使用版本是3.05.01。记住安装路径。讲Tesseract-OCR目录路径放到环境变量中。
4.下载chromedriver并将它所在目录放到环境变量中
环境变量可参考： 
1）https://www.cnblogs.com/jianqingwang/p/6978724.html
2）如果python的scripts目录已经在环境变量中了，放到scripts目录下即可。
https://blog.csdn.net/mk_csdn/article/details/79505543 

4.将num.traineddata复制   C:\Program Files (x86)\Tesseract-OCR\tessdata

二:爬虫涉及内容
1.无头浏览器
2.cookie登录
3.js破解
4.图像裁剪
5.图像识别


生成依赖库新方法：
pipreqs
在项目的根目录下使用：pipreqs ./   
使用时，指定编码格式：pipreqs ./ --encoding=utf8
