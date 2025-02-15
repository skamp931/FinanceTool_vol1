import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def get_dividends_from_minkabu(stock_code):
    url = f"https://minkabu.jp/stock/{stock_code}/dividend"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"データ取得に失敗しました。ステータスコード: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 配当金データを取得
    dividend_elements = soup.find("span", class_="dividend-state__amount__integer")
    if dividend_elements:
        dividend = ''.join(dividend_elements.contents).replace('.', '') + "円"
    else:
        dividend = "データが見つかりませんでした"
    
    return dividend

def save_to_google_sheet(data):
    try:
        # Google APIの認証情報を設定
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["web"], scope)
        client = gspread.authorize(creds)
        st.write("Google API認証に成功しました。")
        
        # スプレッドシートを開く
        spreadsheet = client.open_by_key("1CojC1jRmnDuKILj4w7u2JvVoXSwTzJ85EXAOgb0bTiY")
        st.write("スプレッドシートを開きました。")
        
        # 今日の日付と時分秒を含むシートを追加
        sheet_name = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
        st.write(f"新しいシート '{sheet_name}' を追加しました。")
        
        # データを保存
        worksheet.append_row(data)
        st.write("データを保存しました。")
        
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

st.title("財務データ取得ツール (yfinance)")

stock_code = st.text_input("銘柄コードを入力してください")  # 日本の銘柄の場合、".T"を付ける

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
        
        # 配当金の表示
        dividends = get_dividends_from_minkabu(stock_code)
        st.write(f"配当金: {dividends}")
        
        # 保存ボタン
        if st.button("結果を保存"):
            data = [company_name, current_price, per, roa, bps, business_value, asset_value, theoretical_stock_price, dividends]
            save_to_google_sheet(data)
            st.success("データがGoogleスプレッドシートに保存されました。")
        
    except Exception as e:
        st.error(f"データを取得できませんでした: {e}")

if st.button("google確認"):
    save_to_google_sheet("1")
    st.success("データがGoogleスプレッドシートに保存されました。")