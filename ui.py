import json
import time
import webbrowser
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttks
from read_arxiv import ArxivScraper


class PaperReader:
    def __init__(self):
        
        self.cfg = {
            "area": None,
            "model": None,
            "api_key": None,
            "limit": None,
            "keywords": "",
        }
        self.prompt = """请根据提示词：%s，对以下论文题目进行筛选，挑选出符合提示词方向的论文并返回。
需要注意的是：
1. 论文题目必须严格符合该方向才能入选输出内容。
2. 如果有多篇论文符合条件，请返回所有符合条件的论文。
3. 如果没有符合条件的论文，请返回“今日暂无相关论文推荐”。

返回格式：
1. xxx
2. xxx

以下是论文的名称：
%s

你的返回结果：
"""

        self.paper_raw_info = []

        self.arxiv = ArxivScraper()
        
        self.master = ttks.Window(themename="flatly")
        self.master.title("论文助手")

        # 创建页面的尺寸并固定
        self.master.geometry("1800x920")
        self.master.resizable(False, False)

        # 创建一个分页
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True)

        # 创建一个标签页，用于显示论文内容
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="论文查找")

        self.init_search_tab()

        self.master.mainloop()

    def init_search_tab(self):
        # 创建一个下拉框Combobox，用于选择阅读的分区，包括：人工智能，计算机视觉，自然语言处理
        self.zone_label = tk.Label(self.search_tab, text="阅读分区：", font=("Arial", 10))
        self.zone_label.place(x=10, y=10, width=100, height=20)
        self.zone_list = ttk.Combobox(self.search_tab, values=["cs.CV", "cs.AI", "cs.CL"])
        self.zone_list.place(x=120, y=4, width=250, height=32)

        # 创建一个下拉框Combobox，用于选择阅读论文的大模型：包括：BERT，GPT-3.5，GPT-4
        self.model_label = tk.Label(self.search_tab, text="阅读模型：", font=("Arial", 10))
        self.model_label.place(x=410, y=10, width=100, height=20)
        self.model_list = ttk.Combobox(self.search_tab, values=["qwen-max-longcontext", "qwen-max", "qwen-plus", "qwen-turbo"])
        self.model_list.place(x=520, y=4, width=250, height=32)

        # 创建一个加密的单行文本，用来输入api-key
        self.api_label = tk.Label(self.search_tab, text="API Key: ", font=("Times New Roman", 10))
        self.api_label.place(x=810, y=10, width=100, height=24)
        self.api_entry = tk.Entry(self.search_tab, show="*")
        self.api_entry.place(x=920, y=4, width=250, height=32)

        # 创建一个显示的文本框，用来输入限制查找的论文数量
        self.limit_label = tk.Label(self.search_tab, text="查找数量：", font=("Arial", 10))
        self.limit_label.place(x=1210, y=10, width=100, height=24)
        self.limit_entry = tk.Entry(self.search_tab)
        self.limit_entry.place(x=1320, y=4, width=250, height=32)

        # 设置一个按钮，点击用来获取以上输入的信息
        self.button = tk.Button(self.search_tab, text="确认配置", command=self.get_input_info)
        self.button.place(x=1620, y=4, width=180, height=32)

        # 设置一个单行文本用来记录关键词
        self.keyword_label = tk.Label(self.search_tab, text="关键词：", font=("Arial", 10))
        self.keyword_label.place(x=10, y=50, width=100, height=24)
        self.keyword_entry = tk.Entry(self.search_tab)
        self.keyword_entry.place(x=120, y=44, width=650, height=32)

        # 设置一个按钮用来保存当前的论文题目
        self.save_button = tk.Button(self.search_tab, text="保存论文信息", command=self.save_info)
        self.save_button.place(x=800, y=44, width=120, height=32)

        # 设置一个按钮用来导入论文的题目信息
        self.open_button = tk.Button(self.search_tab, text="导入论文信息", command=self.load_info)
        self.open_button.place(x=930, y=44, width=120, height=32)

        # 设置一个按钮用来爬取论文信息
        self.get_button = tk.Button(self.search_tab, text="网页论文搜索", command=self.get_from_url)
        self.get_button.place(x=1060, y=44, width=120, height=32)

        # 设置一个按钮用来锁定关键词
        self.start_button = tk.Button(self.search_tab, text="锁定关键词", command=self.lock_keyword)
        self.start_button.place(x=1190, y=44, width=120, height=32)

        # 设置一个按钮用来编辑关键词
        self.edit_button = tk.Button(self.search_tab, text="编辑关键词", command=self.unlock_keyword)
        self.edit_button.place(x=1320, y=44, width=120, height=32)

        # 设置一个按钮用来调用大模型
        self.llm_button = tk.Button(self.search_tab, text="筛选论文题目", command=self.screening_papers)
        self.llm_button.place(x=1450, y=44, width=120, height=32)

        # 设置一个按钮用查看论文详情
        self.detail_button = tk.Button(self.search_tab, text="查看论文详情", command=self.get_detail_info)
        self.detail_button.place(x=1620, y=44, width=180, height=32)

        # 设置多行文本，用来获取爬取后的论文信息
        self.paper_text = tk.Text(self.search_tab)
        self.paper_text.place(x=10, y=84, width=780, height=400)

        # 设置一个多行文本，用来显示简单的日志
        self.log_label = tk.Label(self.search_tab, text="简单日志", font=("Arial", 10))
        self.log_label.place(x=10, y=494, width=120, height=24)
        self.log_text = tk.Text(self.search_tab)
        self.log_text.place(x=10, y=524, width=780, height=340)

        # 设计多行文本用来显示大模型筛选后的论文信息
        self.result_text = tk.Listbox(self.search_tab)
        self.result_text.place(x=800, y=84, width=770, height=780)
    
    def get_input_info(self):
        self.cfg["area"] = self.zone_list.get()
        self.cfg["model"] = self.model_list.get()
        self.cfg["api_key"] = self.api_entry.get()
        self.cfg["limit"] = int(self.limit_entry.get())
        self.cfg["keywords"] = self.keyword_entry.get()
        self.edit_logger(str(self.cfg))

    def open_file(self):
        pass
    
    def load_info(self):
        self.cfg = json.load(open("config.json", "r", encoding="utf-8"))
        self.unlock_keyword()
        if self.keyword_entry.get() != "":
            self.keyword_entry.delete(0, tk.END)
        self.keyword_entry.insert(0, self.cfg["keywords"])
        
        self.lock_keyword()
        self.edit_logger("载入配置成功")
        self.edit_logger(str(self.cfg))
        pass
    
    def save_info(self):
        json.dump(self.cfg, open("config.json", "w", encoding="utf-8"))
        self.edit_logger("保存配置成功")
        pass

    def get_from_url(self):
        status_code, self.paper_raw_info = self.arxiv.search_arxiv(self.cfg["limit"], self.cfg["area"])
        # 写入搜索信息
        if self.paper_text.get("0.0", "end") != "":
            self.paper_text.delete(1.0, tk.END)
        for idx, paper in enumerate(self.paper_raw_info):
            self.paper_text.insert(tk.END, f"{idx:>3}: {paper['title']}\n")
        
        self.edit_logger(f"搜索状态：{status_code}")

    def lock_keyword(self):
        self.keyword = self.keyword_entry.get().split(" ")
        self.keyword_entry.config(state=tk.DISABLED)
        self.edit_logger("关键词已锁定")

    def unlock_keyword(self):
        self.keyword_entry.config(state=tk.NORMAL)
        self.edit_logger("关键词已解锁")

    def screening_papers(self):
        prompt = self.arxiv.standardized_input(self.prompt, self.paper_raw_info, self.cfg["keywords"])
        self.edit_logger(f"提示词设计：{prompt}")
        code, result = self.arxiv.get_info(prompt, self.cfg["model"], self.cfg["api_key"])
        self.edit_logger(f"筛选状态：{code}")
        for idx, paper in result:
            self.result_text.insert(tk.END, f"{idx:>3}: {paper}\n")

    def get_detail_info(self):
        pass

    def edit_logger(self, text):
        # 获取时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, timestamp + ": " + text+"\n")


if __name__ == "__main__":
    app = PaperReader()