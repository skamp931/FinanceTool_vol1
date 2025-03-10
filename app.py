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
import  time

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
    # Google APIの認証情報を設定
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    st.write("Google API認証に成功しました。")
    
    # スプレッドシートを開く
    spreadsheet = client.open_by_key("1CojC1jRmnDuKILj4w7u2JvVoXSwTzJ85EXAOgb0bTiY")
    st.write("スプレッドシートを開きました。")
    
    # 今日の日付と時分秒を含むシートを追加
    sheet_name = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
    st.write(f"新しいシート '{sheet_name}' を追加しました。")
    
    # ヘッダー行を追加
    header = ["会社名", "現在の株価 (円)", "PER (株価収益率)", "ROA (総資産利益率, %)", "BPS (1株当たり純資産, 円)", 
              "事業価値 (円)", "資産価値 (円)", "理論株価 (円)", "配当金 (円)"]
    worksheet.append_row(header)
    
    # データを文字列に変換し、数値データは整数に変換
    data_as_strings = [
        [str(item) if isinstance(item, str) else str(int(float(item))) for item in row]
        for row in data
    ]
    # データを保存
    worksheet.append_rows(data_as_strings)
    st.write("データを保存しました。")

#main
st.title("財務データ取得ツール")

stock_codes = st.text_input("銘柄コードをカンマ区切りで入力してください")  # 日本の銘柄の場合、".T"を付ける

# Initialize session state for data
if 'data' not in st.session_state:
    st.session_state.data = []

if st.button("データ取得"):

    st.session_state.data = []

    try:
        for stock_code in stock_codes.split(','):
            stock_code = stock_code.strip()  # Remove any leading/trailing whitespace
            stock = yf.Ticker(stock_code+".T")
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow

            # 会社名と現在の株価を取得
            company_name = stock.info.get('longName', '不明な会社名')
            current_price = stock.history(period="1d")['Close'].iloc[-1]

            
            # 必要なデータを取得
            if not financials.empty:
                net_income = financials.loc['Net Income'].iloc[0]
            else:
                st.error("経常利益データが見つかりません。")

            if not balance_sheet.empty:
                total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0]
            else:
                st.error("バランスシートデータが見つかりません。")

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
            st.write(f"銘柄コード: {stock_code}, 会社名: {company_name}")
            st.write(f"現在の株価: {current_price:.2f} 円")
            st.write(f"PER (株価収益率): {per:.2f}")
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

            # グラフの作成
            # 3か年の経常利益

            if len(financials.loc['Net Income']) >= 3:
                net_income_3y = financials.loc['Net Income'].iloc[:3][::-1] / 1e8  # 最新3か年を取得し、億円単位
            else:
                st.error("経常利益データが不足しています。")

            col1, col2, col3 = st.columns(3)

            with col1:
                plt.figure()
                try:
                    net_income_3y = financials.loc['Net Income'].iloc[:3][::-1] / 1e8  # 最新3か年を取得し、億円単位

                    if len(net_income_3y) < 2:
                        st.error("経常利益データが不足しています。")
                    else:
                        net_income_3y.plot(kind='bar', title='3か年の経常利益 (億円)', fontsize=8)
                        plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)  # y=0に水平線を追加
                        plt.xlabel('年度', fontsize=8)
                        plt.ylabel('経常利益 (億円)', fontsize=8)
                        plt.xticks(rotation=0, fontsize=8)
                        plt.yticks(fontsize=8)
                        plt.gca().set_xticklabels([f"{date.year}年{date.month}月" for date in net_income_3y.index])
                        st.pyplot(plt)

                        # 経常利益が前年より増えている場合にマークをつける
                        if net_income_3y.iloc[2] > net_income_3y.iloc[1]:
                            st.write("経常利益が前年より増加✅")
                except IndexError:
                    st.error("経常利益データが不足しています。")
            # 3か年のキャッシュフロー
            with col2:
                try:
                    plt.figure()
                    cashflow_operating = cashflow.loc['Operating Cash Flow'].iloc[:3][::-1] / 1e8
                    cashflow_financing = cashflow.loc['Financing Cash Flow'].iloc[:3][::-1] / 1e8
                    cashflow_investing = cashflow.loc['Investing Cash Flow'].iloc[:3][::-1] / 1e8
                    df_cashflow = pd.DataFrame({
                        '営業キャッシュフロー': cashflow_operating,
                        '財務キャッシュフロー': cashflow_financing,
                        '投資キャッシュフロー': cashflow_investing
                    })
                    df_cashflow.plot(kind='bar', title='3か年のキャッシュフロー (億円)', fontsize=8)
                    plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)  # y=0に水平線を追加
                    plt.xlabel('年度', fontsize=8)
                    plt.ylabel('キャッシュフロー (億円)', fontsize=8)
                    plt.xticks(rotation=0, fontsize=8)
                    plt.yticks(fontsize=8)
                    plt.gca().set_xticklabels([f"{date.year}年{date.month}月" for date in df_cashflow.index])
                    plt.legend(fontsize=8)
                    st.pyplot(plt)
                except KeyError as e:
                    st.error(f"キャッシュフローデータが見つかりません: {e}")

            # 3か年の自己資本比率
            with col3:
                plt.figure()
                equity_ratio_3y = (balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[:3][::-1] / balance_sheet.loc['Total Assets'].iloc[:3][::-1]) * 100
                equity_ratio_3y.plot(kind='bar', title='3か年の自己資本比率 (%)', fontsize=8)
                plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)  # y=0に水平線を追加
                plt.xlabel('年度', fontsize=8)
                plt.ylabel('自己資本比率 (%)', fontsize=8)
                plt.xticks(rotation=0, fontsize=8)
                plt.yticks(fontsize=8)
                plt.ylim(0, 100)  # 最大値を100%に設定
                plt.gca().set_xticklabels([f"{date.year}年{date.month}月" for date in equity_ratio_3y.index])
                st.pyplot(plt)
                        # リクエスト間に1秒待機
        time.sleep(1)

                
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