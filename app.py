import requests
from bs4 import BeautifulSoup

def get_financial_data(stock_code):
    url = f"https://minkabu.jp/stock/{stock_code}/settlement"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 経常利益を取得
    operating_income = []
    for tag in soup.find_all("td", class_="operating_income"):
        operating_income.append(tag.text.strip())
    
    # 自己資本率を取得
    equity_ratio = []
    for tag in soup.find_all("td", class_="equity_ratio"):
        equity_ratio.append(tag.text.strip())
    
    # PERを取得
    per = []
    for tag in soup.find_all("td", class_="per"):
        per.append(tag.text.strip())
    
    return {
        "operating_income": operating_income,
        "equity_ratio": equity_ratio,
        "per": per
    }

# 使用例
stock_code = "7203"  # トヨタ自動車の例
financial_data = get_financial_data(stock_code)
print(financial_data)