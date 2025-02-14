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
        
        st.write("財務データ")
        st.write(financials)
        
        st.write("バランスシート")
        st.write(balance_sheet)
        
        st.write("キャッシュフロー")
        st.write(cashflow)
        
    except Exception as e:
        st.error(f"データを取得できませんでした: {e}")