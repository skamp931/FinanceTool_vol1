import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_financial_data(stock_code):
    url = f"https://minkabu.jp/stock/{stock_code}/settlement"
    response = requests.get(url)
    
    if response.status_code != 200:
        st.error(f"データ取得に失敗しました。ステータスコード: {response.status_code}")
        return None
    
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

st.title("財務データ取得ツール")

stock_code = st.text_input("銘柄コードを入力してください", "7203")  # デフォルトはトヨタ自動車

if st.button("データ取得"):
    financial_data = get_financial_data(stock_code)
    if financial_data:
        df = pd.DataFrame(financial_data)
        st.write(df)
    else:
        st.error("データを取得できませんでした。")