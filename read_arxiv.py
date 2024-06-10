import re
import requests
from http import HTTPStatus
import dashscope


class ArxivScraper:
    def __init__(self):
        self.base_url = "https://arxiv.org/list/%s/recent?skip=0&show=%d"
        self.main_url = "https://arxiv.org/"

        dashscope.api_key = "sk-40ffb98192c74f3f805978bf301b53b2"

    def search_arxiv(self, limit=1000, RD="cs.CV"):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        response = requests.get(self.base_url % (RD, limit), headers=headers)
        return response.status_code, self.parse_arxiv(response.text)
    
    def parse_arxiv(self, text):
        # 获得所有论文的信息
        results = []
        all_info = re.findall(r'<dt>(.*?)</dd>', text, re.S)
        for paper in all_info:
            results.append(self.analytical_paper(paper))
        return results
    
    def analytical_paper(self, paper):
        # 论文标题
        name = re.findall(r"<div class='list-title mathjax'><span class='descriptor'>Title:</span>\n(.*?)\n", paper, re.S)[0].lstrip(" ")
        authors = re.findall(r"<div class='list-authors'>(.*?)</div>", paper, re.S)[0].lstrip(" ")
        author = re.findall(r"<a href=.*?>(.*?)</a>", authors, re.S)
        # 论文链接
        id = re.findall(r'<a href ="(.*?)" title="Abstract" id="(.*?)">', paper, re.S)[0][1]
        url = self.main_url + "abs/" + id
        return {
            "id": id,
            "title": name,
            "url": url,
            "authors": author
        }

    # 找寻研究方向相关的论文
    def get_info(self, prompt: str, model, api: str):
        dashscope.api_key = api
        llm = dashscope.Generation.call(
            model=model,
            prompt=prompt
        )
            # 如果调用成功，则打印模型的输出
        if llm.status_code == HTTPStatus.OK:
            return llm.code, llm["output"]["text"].split("\n")
        # 如果调用失败，则打印出错误码与失败信息
        else:
            return llm.code, [llm.message]

    def standardized_input(self, prompt: str, info, keyword: list):
        keyword = ", ".join(keyword)
        info_str = ""
        try:
            for idx, field in enumerate(info):
                info_str += "%03d: %s\n" % (idx, field["title"])
            return prompt % (keyword, info_str)
        except:
            return "prompt error"


if __name__ == "__main__":
    scraper = ArxivScraper()
    arxiv_text = scraper.search_arxiv()
    
    result = scraper.parse_arxiv(arxiv_text)
    new_prompt = scraper.standardized_input(prompt, result[:64], ["图像压缩算法"])
    print(new_prompt)

    response = scraper.get_info(new_prompt)
    print(response)