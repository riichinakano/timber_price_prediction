import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="栃材原木販売価格予測システム",
    page_icon="🌳",
    layout="wide"
)

# タイトル
st.title("🌳 栃材原木販売価格予測システム")
st.markdown("---")

# 予測モデルの定義
def calculate_price(diameter, length, rank):
    """
    価格予測モデル
    
    Parameters:
    - diameter: 口径 (cm)
    - length: 長さ (m)
    - rank: ランク (A/B/C)
    
    Returns:
    - predicted_price: 予測価格
    - lower_bound: 信頼区間下限
    - upper_bound: 信頼区間上限
    """
    if rank == 'A':
        # Aランク材: 価格 = 18,000円/cm × 口径 + 120,000円/m × 長さ - 850,000円
        predicted_price = 18000 * diameter + 120000 * length - 850000
        confidence_interval = 0.15  # ±15%
    elif rank == 'B':
        # Bランク材: 価格 = 9,000円/cm × 口径 + 80,000円/m × 長さ - 380,000円
        predicted_price = 9000 * diameter + 80000 * length - 380000
        confidence_interval = 0.20  # ±20%
    else:  # rank == 'C'
        # Cランク材: 定額100,000円
        predicted_price = 100000
        confidence_interval = 0.10  # ±10%
    
    lower_bound = predicted_price * (1 - confidence_interval)
    upper_bound = predicted_price * (1 + confidence_interval)
    
    return predicted_price, lower_bound, upper_bound

# サイドバーに説明を表示
with st.sidebar:
    st.header("📊 予測モデル情報")
    st.markdown("""
    ### Aランク材
    ```
    価格 = 18,000円/cm × 口径 
         + 120,000円/m × 長さ 
         - 850,000円
    信頼区間: ±15%
    ```
    
    ### Bランク材
    ```
    価格 = 9,000円/cm × 口径 
         + 80,000円/m × 長さ 
         - 380,000円
    信頼区間: ±20%
    ```
    
    ### Cランク材
    ```
    価格 = 100,000円（定額）
    信頼区間: ±10%
    ```
    """)
    
    st.markdown("---")
    st.markdown("""
    ### ランク付け基準
    - **Aランク**: 口径85cm以上、良好な形状
    - **Bランク**: 口径60-84cm、一般的な形状
    - **Cランク**: 口径60cm未満、形状に難あり
    """)

# メインエリア
st.header("📝 データ入力")

# セッションステートの初期化
if 'timber_data' not in st.session_state:
    st.session_state.timber_data = []

# 入力フォーム
col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2])

with col1:
    no = st.number_input("No.", min_value=1, value=len(st.session_state.timber_data) + 1, step=1)

with col2:
    diameter = st.number_input("口径 (cm)", min_value=1, max_value=200, value=80, step=1)

with col3:
    length = st.number_input("長さ (m)", min_value=0.1, max_value=10.0, value=2.0, step=0.1, format="%.1f")

with col4:
    rank = st.selectbox("ランク", options=['A', 'B', 'C'], index=1)

with col5:
    st.write("")  # スペース調整
    st.write("")  # スペース調整
    add_button = st.button("➕ 追加", use_container_width=True)

# データ追加処理
if add_button:
    predicted_price, lower_bound, upper_bound = calculate_price(diameter, length, rank)

    timber_entry = {
        'No.': no,
        '口径(cm)': diameter,
        '長さ(m)': length,
        'ランク': rank,
        '予測価格(円)': int(predicted_price),
        '下限(円)': int(lower_bound),
        '上限(円)': int(upper_bound)
    }

    st.session_state.timber_data.append(timber_entry)
    st.success(f"No.{no} のデータを追加しました！")
    st.rerun()

# CSVインポート機能
st.markdown("---")
st.subheader("📤 CSV一括インポート")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=['csv'],
        help="No., 口径(cm), 長さ(m), ランク の列を含むCSVファイルをアップロードしてください"
    )

with col2:
    st.write("")
    st.write("")
    import_mode = st.radio(
        "インポートモード",
        options=["追加", "上書き"],
        help="追加: 既存データに追加します\n上書き: 既存データをクリアして新規データのみにします"
    )

if uploaded_file is not None:
    try:
        # CSVファイルを読み込み
        import_df = pd.read_csv(uploaded_file)

        # 必要な列が存在するかチェック
        required_columns = ['No.', '口径(cm)', '長さ(m)', 'ランク']
        missing_columns = [col for col in required_columns if col not in import_df.columns]

        if missing_columns:
            st.error(f"❌ 必要な列が不足しています: {', '.join(missing_columns)}")
            st.info("CSVファイルには以下の列が必要です: No., 口径(cm), 長さ(m), ランク")
        else:
            # プレビュー表示
            st.write("#### プレビュー")
            st.dataframe(import_df[required_columns].head(10), use_container_width=True)

            if len(import_df) > 10:
                st.info(f"📊 全{len(import_df)}行のうち、最初の10行を表示しています")

            # インポートボタン
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

            with col_btn1:
                if st.button("✅ インポート実行", use_container_width=True, type="primary"):
                    # 上書きモードの場合、既存データをクリア
                    if import_mode == "上書き":
                        st.session_state.timber_data = []

                    # データをインポート
                    imported_count = 0
                    error_rows = []

                    for idx, row in import_df.iterrows():
                        try:
                            no_val = int(row['No.'])
                            diameter_val = float(row['口径(cm)'])
                            length_val = float(row['長さ(m)'])
                            rank_val = str(row['ランク']).strip().upper()

                            # ランクのバリデーション
                            if rank_val not in ['A', 'B', 'C']:
                                error_rows.append(f"行{idx+2}: ランクが無効です（{rank_val}）")
                                continue

                            # 価格計算
                            predicted_price, lower_bound, upper_bound = calculate_price(
                                diameter_val, length_val, rank_val
                            )

                            timber_entry = {
                                'No.': no_val,
                                '口径(cm)': diameter_val,
                                '長さ(m)': length_val,
                                'ランク': rank_val,
                                '予測価格(円)': int(predicted_price),
                                '下限(円)': int(lower_bound),
                                '上限(円)': int(upper_bound)
                            }

                            st.session_state.timber_data.append(timber_entry)
                            imported_count += 1

                        except Exception as e:
                            error_rows.append(f"行{idx+2}: {str(e)}")

                    # 結果表示
                    if imported_count > 0:
                        st.success(f"✅ {imported_count}件のデータをインポートしました！")

                    if error_rows:
                        st.warning(f"⚠️ {len(error_rows)}件のエラーがありました:")
                        for error in error_rows[:5]:  # 最初の5件のみ表示
                            st.write(f"- {error}")
                        if len(error_rows) > 5:
                            st.write(f"... 他{len(error_rows)-5}件")

                    st.rerun()

            with col_btn2:
                if st.button("❌ キャンセル", use_container_width=True):
                    st.rerun()

    except Exception as e:
        st.error(f"❌ CSVファイルの読み込みエラー: {str(e)}")
        st.info("CSVファイルの形式を確認してください。")

# サンプルCSVのダウンロード
st.write("#### サンプルCSVフォーマット")
sample_data = pd.DataFrame({
    'No.': [1, 2, 3],
    '口径(cm)': [90, 78, 70],
    '長さ(m)': [2.2, 1.9, 3.3],
    'ランク': ['A', 'B', 'B']
})

col_sample1, col_sample2, col_sample3 = st.columns([2, 1, 3])

with col_sample1:
    st.dataframe(sample_data, use_container_width=True, hide_index=True)

with col_sample2:
    sample_csv = sample_data.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 サンプルダウンロード",
        data=sample_csv,
        file_name="timber_import_sample.csv",
        mime="text/csv",
        use_container_width=True
    )

# データ表示と計算結果
if st.session_state.timber_data:
    st.markdown("---")
    st.header("📊 予測結果")
    
    # データフレーム作成
    df = pd.DataFrame(st.session_state.timber_data)
    
    # データテーブル表示
    st.subheader("入力データと予測結果")

    # データ編集エリア
    col_table, col_buttons = st.columns([5, 1])

    with col_table:
        # データテーブルのスタイリング
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                '予測価格(円)': st.column_config.NumberColumn(
                    '予測価格(円)',
                    format="¥%d"
                ),
                '下限(円)': st.column_config.NumberColumn(
                    '下限(円)',
                    format="¥%d"
                ),
                '上限(円)': st.column_config.NumberColumn(
                    '上限(円)',
                    format="¥%d"
                )
            }
        )

    with col_buttons:
        st.write("#### 編集")

        # 行番号の選択（削除用）
        if len(st.session_state.timber_data) > 0:
            row_to_delete = st.selectbox(
                "削除する行",
                options=range(len(st.session_state.timber_data)),
                format_func=lambda x: f"No.{st.session_state.timber_data[x]['No.']}"
            )

            if st.button("➖ 削除", use_container_width=True, type="secondary"):
                st.session_state.timber_data.pop(row_to_delete)
                st.success(f"行を削除しました！")
                st.rerun()

        st.write("")

        # 新規行追加
        with st.expander("➕ 行追加"):
            add_no = st.number_input("No.", min_value=1, value=len(st.session_state.timber_data) + 1, step=1, key="edit_no")
            add_diameter = st.number_input("口径(cm)", min_value=1, max_value=200, value=80, step=1, key="edit_diameter")
            add_length = st.number_input("長さ(m)", min_value=0.1, max_value=10.0, value=2.0, step=0.1, format="%.1f", key="edit_length")
            add_rank = st.selectbox("ランク", options=['A', 'B', 'C'], index=1, key="edit_rank")

            if st.button("追加", use_container_width=True, key="add_row_btn"):
                predicted_price, lower_bound, upper_bound = calculate_price(add_diameter, add_length, add_rank)

                timber_entry = {
                    'No.': add_no,
                    '口径(cm)': add_diameter,
                    '長さ(m)': add_length,
                    'ランク': add_rank,
                    '予測価格(円)': int(predicted_price),
                    '下限(円)': int(lower_bound),
                    '上限(円)': int(upper_bound)
                }

                st.session_state.timber_data.append(timber_entry)
                st.success(f"No.{add_no} のデータを追加しました！")
                st.rerun()
    
    # 統計情報
    st.markdown("---")
    st.subheader("📈 統計情報")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総本数", f"{len(df)}本")
    
    with col2:
        total_price = df['予測価格(円)'].sum()
        st.metric("予測合計金額", f"¥{total_price:,}")
    
    with col3:
        total_lower = df['下限(円)'].sum()
        st.metric("合計下限", f"¥{total_lower:,}")
    
    with col4:
        total_upper = df['上限(円)'].sum()
        st.metric("合計上限", f"¥{total_upper:,}")
    
    # ランク別集計
    st.markdown("---")
    st.subheader("🏷️ ランク別集計")
    
    rank_summary = df.groupby('ランク').agg({
        'No.': 'count',
        '予測価格(円)': 'sum'
    }).rename(columns={'No.': '本数', '予測価格(円)': '合計金額(円)'})
    
    rank_summary['割合(%)'] = (rank_summary['合計金額(円)'] / rank_summary['合計金額(円)'].sum() * 100).round(1)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.dataframe(
            rank_summary,
            use_container_width=True,
            column_config={
                '合計金額(円)': st.column_config.NumberColumn(
                    '合計金額(円)',
                    format="¥%d"
                )
            }
        )
    
    with col2:
        # 円グラフ
        fig = px.pie(
            rank_summary.reset_index(),
            values='合計金額(円)',
            names='ランク',
            title='ランク別売上比率',
            color='ランク',
            color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4', 'C': '#95E1D3'}
        )
        
        # グラフのカスタマイズ
        fig.update_traces(
            textposition='inside',
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>金額: ¥%{value:,}<br>割合: %{percent}<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # グラフ表示
    st.markdown("---")
    st.subheader("📊 価格分布グラフ")
    
    # 散布図
    fig = px.scatter(
        df,
        x='口径(cm)',
        y='予測価格(円)',
        color='ランク',
        size='長さ(m)',
        hover_data=['No.', '口径(cm)', '長さ(m)', 'ランク', '予測価格(円)'],
        title='口径と予測価格の関係',
        color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4', 'C': '#95E1D3'}
    )
    
    fig.update_layout(
        xaxis_title='口径 (cm)',
        yaxis_title='予測価格 (円)',
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ボックスプロット
    fig2 = px.box(
        df,
        x='ランク',
        y='予測価格(円)',
        color='ランク',
        title='ランク別価格分布',
        color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4', 'C': '#95E1D3'}
    )
    
    fig2.update_layout(
        xaxis_title='ランク',
        yaxis_title='予測価格 (円)'
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # データクリア・ダウンロードボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("🗑️ データクリア", use_container_width=True):
            st.session_state.timber_data = []
            st.rerun()
    
    with col2:
        # CSVダウンロード
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name="timber_price_prediction.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("👆 上のフォームからデータを入力して「追加」ボタンを押してください。")

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>栃材原木販売価格予測システム v1.0</p>
    <p>予測モデル: 重回帰分析（2024年12月版）</p>
</div>
""", unsafe_allow_html=True)
