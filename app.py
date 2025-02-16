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
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CojC1jRmnDuKILj4w7u2JvVoXSwTzJ85EXAOgb0bTiY/edit?gid=0#gid=0")
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

stock_codes = st.text_input("銘柄コードをカンマ区切りで入力してください")  # 日本の銘柄の場合、".T"を付ける

# Initialize session state for data
if 'data' not in st.session_state:
    st.session_state.data = []

if st.button("データ取得"):
    try:
        for stock_code in stock_codes.split(','):
            stock_code = stock_code.strip()  # Remove any leading/trailing whitespace
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
            st.write(f"PER (株価収益率): {per * 100:.2f}%")
            st.write(f"ROA (総資産利益率): {roa * 100:.2f}%")
            st.write(f"BPS (1株当たり純資産): {bps:.2f}")
            st.write(f"事業価値: {business_value:.2f}")
            st.write(f"資産価値: {asset_value:.2f}")
            st.write(f"理論株価: {theoretical_stock_price:.2f}")
            
            # 配当金の表示
            dividends = get_dividends_from_minkabu(stock_code)
            st.write(f"配当金: {dividends}")
            
            # Store data in session state
            st.session_state.data.append([company_name, current_price, per, roa, bps, business_value, asset_value, theoretical_stock_price, dividends])
        
    except Exception as e:
        st.error(f"データを取得できませんでした: {e}")

    # 備考として計算式を表示
    st.write("備考:")
    st.write("事業価値 = PER * 15 * ROA * 10 * (1 / 自己資本比率 + 0.33)")
    st.write("資産価値 = BPS * 自己資本比率")
    st.write("理論株価 = 資産価値 + 事業価値")  

# 保存ボタン
if st.button("結果を保存"):
    if st.session_state.data:
        for data in st.session_state.data:
            st.write(data)
        st.write("保存を開始します。")
        save_to_google_sheet(st.session_state.data)
        st.success("データがGoogleスプレッドシートに保存されました。")
    else:
        st.error("データがありません。最初にデータを取得してください。")
        