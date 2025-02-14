import streamlit as st
import yfinance as yf
import pandas as pd

st.title("財務データ取得ツール (yfinance)")

stock_code = st.text_input("銘柄コードを入力してください", "7203.T")  # 日本の銘柄の場合、".T"を付ける

if st.button("データ取得"):
    try:
        stock = yf.Ticker(stock_code)
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        st.write("財務データ (Income Statement)")
        st.write(financials.rename(index={
            'Total Revenue': '総収入',
            'Cost Of Revenue': '売上原価',
            'Gross Profit': '粗利益',
            'Operating Income': '営業利益',
            'Net Income': '純利益'
        }))
        
        st.write("バランスシート (Balance Sheet)")
        st.write(balance_sheet.rename(index={
            'Total Assets': '総資産',
            'Total Liabilities Net Minority Interest': '負債合計',
            'Total Equity Gross Minority Interest': '自己資本合計',
            'Cash And Cash Equivalents': '現金及び現金同等物'
        }))
        
        st.write("キャッシュフロー (Cash Flow)")
        st.write(cashflow.rename(index={
            'Total Cash From Operating Activities': '営業活動によるキャッシュフロー',
            'Total Cashflows From Investing Activities': '投資活動によるキャッシュフロー',
            'Total Cash From Financing Activities': '財務活動によるキャッシュフロー'
        }))
        
    except Exception as e:
        st.error(f"データを取得できませんでした: {e}")