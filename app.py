import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

import requests
from bs4 import BeautifulSoup

def get_dividends_from_minkabu(stock_code):
    url = f"https://minkabu.jp/stock/{stock_code}/dividend"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"データ取得に失敗しました。ステータスコード: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 配当金データを取得
    dividend_elements = soup.find("span", class_="dividend-state__amount__integer")
    st.write(dividend_elements.getText)
    dividend = str(dividend_elements.getText).replace('.', '')+"円"

    return dividend

st.title("財務データ取得ツール (yfinance)")

stock_code = st.text_input("銘柄コードを入力してください", "7203")  # 日本の銘柄の場合、".T"を付ける

financials = None
balance_sheet = None
cashflow = None

if st.button("データ取得"):
    try:
        stock = yf.Ticker(stock_code+".T")
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow

        
        # 会社名と現在の株価を取得
        company_name = stock.info['longName']
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        
        # 必要なデータを取得
        net_income = financials.loc['Net Income'].iloc[0]
        total_assets = balance_sheet.loc['Total Assets'].iloc[0]
        total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0]
        shares_outstanding = stock.info['sharesOutstanding']
        market_price = stock.history(period="1d")['Close'].iloc[-1]
        
        # PER, ROA, BPSの計算
        per = market_price / (net_income / shares_outstanding)
        roa = net_income / total_assets
        bps = total_equity / shares_outstanding
        equity_ratio = total_equity / total_assets
        
        # 事業価値と資産価値の計算
        business_value = per * 15 * roa * 10 * (1 / equity_ratio + 0.33)
        asset_value = bps * equity_ratio
        
        # 理論株価の計算
        theoretical_stock_price = asset_value + business_value
        
        # 結果の表示
        st.write(f"会社名: {company_name}")
        st.write(f"現在の株価: {current_price:.2f} 円")
        st.write(f"PER: {per:.2f}")
        st.write(f"ROA: {roa:.2f}")
        st.write(f"BPS: {bps:.2f}")
        st.write(f"事業価値: {business_value:.2f}")
        st.write(f"資産価値: {asset_value:.2f}")
        st.write(f"理論株価: {theoretical_stock_price:.2f}")
        
        # 3か年の経常利益と株価収益率
        net_income = financials.loc['Net Income'] / 1e8  # 億単位に変換
        pe_ratio = stock.info['trailingPE']
        
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('年')
        ax1.set_ylabel('経常利益 (億円)', color='tab:blue')
        ax1.plot(net_income.index, net_income.values, color='tab:blue', label='経常利益')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('株価収益率 (P/E Ratio)', color='tab:red')
        ax2.plot(net_income.index, [pe_ratio] * len(net_income.index), color='tab:red', linestyle='--', label='P/E Ratio')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        fig.tight_layout()
        st.pyplot(fig)
        
        # 3か年の自己資本率
        equity_ratio = balance_sheet.loc['Total Equity Gross Minority Interest'] / balance_sheet.loc['Total Assets']
        
        plt.figure()
        plt.plot(equity_ratio.index, equity_ratio.values, marker='o')
        plt.title('3か年の自己資本率')
        plt.xlabel('年')
        plt.ylabel('自己資本率')
        st.pyplot(plt)
        
        # 3か年の配当金
        dividends = stock.dividends
        st.write(dividends)

        plt.figure()
        plt.plot(dividends.index, dividends.values, marker='o')
        plt.title('3か年の配当金')
        plt.xlabel('年')
        plt.ylabel('配当金')
        st.pyplot(plt)

        st.write("財務データ (Income Statement)")
        st.write(financials)
        
        st.write("バランスシート (Balance Sheet)")
        st.write(balance_sheet)
        
        st.write("キャッシュフロー (Cash Flow)")
        st.write(cashflow)
        
        # 使用例
        st.write("配当金")

        dividends = get_dividends_from_minkabu(stock_code)
        st.write(dividends)


    except Exception as e:
        st.error(f"データを取得できませんでした: {e}")