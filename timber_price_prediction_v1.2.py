import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="栃材原木販売価格予測システム",
    page_icon="🌳",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

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

def validate_data(no, diameter, length, rank):
    """データのバリデーション"""
    errors = []
    
    if no <= 0:
        errors.append("No.は1以上の値を入力してください")
    
    if diameter < 1 or diameter > 200:
        errors.append("口径は1〜200cmの範囲で入力してください")
    
    if length < 0.1 or length > 10.0:
        errors.append("長さは0.1〜10.0mの範囲で入力してください")
    
    if rank not in ['A', 'B', 'C']:
        errors.append("ランクはA、B、Cのいずれかを選択してください")
    
    return errors

# サイドバーに説明を表示
with st.sidebar:
    st.header("📊 予測モデル情報")
    
    # モデル選択タブ
    model_tab = st.radio(
        "表示モード",
        ["モデル式", "ランク基準", "使い方"],
        label_visibility="collapsed"
    )
    
    if model_tab == "モデル式":
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
    
    elif model_tab == "ランク基準":
        st.markdown("""
        ### ランク付け基準
        
        #### 🥇 Aランク
        - 口径85cm以上
        - 良好な形状
        - 予測売上70万円以上
        
        #### 🥈 Bランク
        - 口径60-84cm
        - 一般的な形状
        - 予測売上30-69万円
        
        #### 🥉 Cランク
        - 口径60cm未満
        - 形状に難あり
        - 定額取引が適切
        """)
    
    else:  # 使い方
        st.markdown("""
        ### 使い方
        
        #### 1️⃣ 単体入力
        - フォームに1件ずつ入力
        - 「追加」ボタンで登録
        
        #### 2️⃣ CSV一括入力
        - サンプルをダウンロード
        - データを編集
        - CSVをアップロード
        
        #### 3️⃣ 編集・削除
        - 予測結果一覧から編集
        - 不要な行を削除
        
        #### 4️⃣ 結果確認
        - 統計情報を確認
        - グラフで可視化
        - CSVでダウンロード
        """)
    
    st.markdown("---")
    
    # システム情報
    st.caption("**バージョン:** v1.2")
    st.caption("**最終更新:** 2025-11-10")
    st.caption("**モデル:** 2024年12月版")

# メインエリア
# タブで機能を分ける
tab1, tab2, tab3 = st.tabs(["📝 データ入力", "📊 予測結果", "📈 統計分析"])

with tab1:
    st.header("データ入力")
    
    # 入力方法の選択
    input_method = st.radio(
        "入力方法を選択",
        ["単体入力", "CSV一括入力"],
        horizontal=True
    )
    
    if input_method == "単体入力":
        st.subheader("🖊️ 単体データ入力")
        
        # セッションステートの初期化
        if 'timber_data' not in st.session_state:
            st.session_state.timber_data = []
        
        # 入力フォーム
        with st.form("input_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                no = st.number_input("No.", min_value=1, value=len(st.session_state.timber_data) + 1, step=1)
            
            with col2:
                diameter = st.number_input("口径 (cm)", min_value=1, max_value=200, value=80, step=1)
            
            with col3:
                length = st.number_input("長さ (m)", min_value=0.1, max_value=10.0, value=2.0, step=0.1, format="%.1f")
            
            with col4:
                rank = st.selectbox("ランク", options=['A', 'B', 'C'], index=1)
            
            submitted = st.form_submit_button("➕ 追加", use_container_width=True, type="primary")
            
            if submitted:
                # バリデーション
                errors = validate_data(no, diameter, length, rank)
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
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
                    st.success(f"✅ No.{no} のデータを追加しました！")
                    st.rerun()
    
    else:  # CSV一括入力
        st.subheader("📤 CSV一括インポート")
        
        # セッションステートの初期化
        if 'timber_data' not in st.session_state:
            st.session_state.timber_data = []
        
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
                help="追加: 既存データに追加\n上書き: 既存データをクリア"
            )
        
        if uploaded_file is not None:
            try:
                # 複数のエンコーディングを試す
                encodings = ['utf-8-sig', 'utf-8', 'shift-jis', 'cp932']
                import_df = None
                
                for encoding in encodings:
                    try:
                        import_df = pd.read_csv(uploaded_file, encoding=encoding)
                        break
                    except:
                        uploaded_file.seek(0)  # ファイルポインタをリセット
                        continue
                
                if import_df is None:
                    st.error("❌ CSVファイルのエンコーディングが不明です")
                else:
                    # 必要な列が存在するかチェック
                    required_columns = ['No.', '口径(cm)', '長さ(m)', 'ランク']
                    missing_columns = [col for col in required_columns if col not in import_df.columns]
                    
                    if missing_columns:
                        st.error(f"❌ 必要な列が不足しています: {', '.join(missing_columns)}")
                        st.info("CSVファイルには以下の列が必要です: No., 口径(cm), 長さ(m), ランク")
                    else:
                        # プレビュー表示
                        st.write("#### 📋 プレビュー")
                        preview_df = import_df[required_columns].head(10)
                        st.dataframe(preview_df, use_container_width=True, hide_index=True)
                        
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
                                        
                                        # バリデーション
                                        errors = validate_data(no_val, diameter_val, length_val, rank_val)
                                        
                                        if errors:
                                            error_rows.append(f"行{idx+2}: {', '.join(errors)}")
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
                                    with st.expander(f"⚠️ {len(error_rows)}件のエラー", expanded=False):
                                        for error in error_rows:
                                            st.write(f"- {error}")
                                
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("❌ キャンセル", use_container_width=True):
                                st.rerun()
            
            except Exception as e:
                st.error(f"❌ CSVファイルの読み込みエラー: {str(e)}")
                st.info("CSVファイルの形式を確認してください。")
        
        # サンプルCSVのダウンロード
        st.markdown("---")
        st.write("#### 📝 サンプルCSVフォーマット")
        sample_data = pd.DataFrame({
            'No.': [1, 2, 3, 4, 5],
            '口径(cm)': [90, 78, 86, 70, 46],
            '長さ(m)': [2.2, 1.9, 2.0, 3.3, 3.0],
            'ランク': ['A', 'B', 'B', 'B', 'C']
        })
        
        col_sample1, col_sample2 = st.columns([3, 1])
        
        with col_sample1:
            st.dataframe(sample_data, use_container_width=True, hide_index=True)
        
        with col_sample2:
            st.write("")
            st.write("")
            sample_csv = sample_data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 サンプルダウンロード",
                data=sample_csv,
                file_name="timber_import_sample.csv",
                mime="text/csv",
                use_container_width=True
            )

with tab2:
    # セッションステートの初期化
    if 'timber_data' not in st.session_state:
        st.session_state.timber_data = []
    
    if st.session_state.timber_data:
        st.header("予測結果一覧")
        
        # データフレーム作成
        df = pd.DataFrame(st.session_state.timber_data)
        
        # データテーブル表示とアクション
        col_table, col_actions = st.columns([4, 1])
        
        with col_table:
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
        
        with col_actions:
            st.write("#### アクション")
            
            # 行削除
            if len(st.session_state.timber_data) > 0:
                with st.expander("➖ 行削除"):
                    row_to_delete = st.selectbox(
                        "削除する行",
                        options=range(len(st.session_state.timber_data)),
                        format_func=lambda x: f"No.{st.session_state.timber_data[x]['No.']}",
                        key="delete_selector"
                    )
                    
                    if st.button("削除実行", use_container_width=True, type="secondary"):
                        deleted_no = st.session_state.timber_data[row_to_delete]['No.']
                        st.session_state.timber_data.pop(row_to_delete)
                        st.success(f"✅ No.{deleted_no} を削除しました")
                        st.rerun()
            
            st.write("")
            
            # データ管理
            with st.expander("🗂️ データ管理"):
                # CSVダウンロード
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 CSVダウンロード",
                    data=csv,
                    file_name=f"timber_prediction_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.write("")
                
                # データクリア
                if st.button("🗑️ 全データクリア", use_container_width=True, type="secondary"):
                    st.session_state.timber_data = []
                    st.success("✅ データをクリアしました")
                    st.rerun()
    
    else:
        st.info("📝 データが登録されていません。「データ入力」タブからデータを追加してください。")

with tab3:
    # セッションステートの初期化
    if 'timber_data' not in st.session_state:
        st.session_state.timber_data = []
    
    if st.session_state.timber_data:
        st.header("統計分析")
        
        df = pd.DataFrame(st.session_state.timber_data)
        
        # 統計情報
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
            '予測価格(円)': ['sum', 'mean']
        })
        
        rank_summary.columns = ['本数', '合計金額(円)', '平均価格(円)']
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
                    ),
                    '平均価格(円)': st.column_config.NumberColumn(
                        '平均価格(円)',
                        format="¥%.0f"
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
            
            fig.update_traces(
                textposition='inside',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>金額: ¥%{value:,}<br>割合: %{percent}<extra></extra>'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # グラフ表示
        st.markdown("---")
        st.subheader("📊 価格分布グラフ")
        
        # グラフの種類を選択
        graph_type = st.radio(
            "グラフの種類",
            ["散布図", "ボックスプロット", "ヒストグラム"],
            horizontal=True
        )
        
        if graph_type == "散布図":
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
        
        elif graph_type == "ボックスプロット":
            # ボックスプロット
            fig = px.box(
                df,
                x='ランク',
                y='予測価格(円)',
                color='ランク',
                title='ランク別価格分布',
                color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4', 'C': '#95E1D3'}
            )
            
            fig.update_layout(
                xaxis_title='ランク',
                yaxis_title='予測価格 (円)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:  # ヒストグラム
            # ヒストグラム
            fig = px.histogram(
                df,
                x='予測価格(円)',
                color='ランク',
                title='価格分布ヒストグラム',
                color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4', 'C': '#95E1D3'},
                nbins=20
            )
            
            fig.update_layout(
                xaxis_title='予測価格 (円)',
                yaxis_title='件数',
                barmode='overlay'
            )
            
            fig.update_traces(opacity=0.7)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 詳細統計
        st.markdown("---")
        st.subheader("📊 詳細統計")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**口径の統計**")
            diameter_stats = df['口径(cm)'].describe()
            st.dataframe(
                pd.DataFrame({
                    '統計量': ['件数', '平均', '標準偏差', '最小値', '25%', '中央値', '75%', '最大値'],
                    '値': [
                        f"{diameter_stats['count']:.0f}",
                        f"{diameter_stats['mean']:.1f} cm",
                        f"{diameter_stats['std']:.1f} cm",
                        f"{diameter_stats['min']:.1f} cm",
                        f"{diameter_stats['25%']:.1f} cm",
                        f"{diameter_stats['50%']:.1f} cm",
                        f"{diameter_stats['75%']:.1f} cm",
                        f"{diameter_stats['max']:.1f} cm"
                    ]
                }),
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.write("**長さの統計**")
            length_stats = df['長さ(m)'].describe()
            st.dataframe(
                pd.DataFrame({
                    '統計量': ['件数', '平均', '標準偏差', '最小値', '25%', '中央値', '75%', '最大値'],
                    '値': [
                        f"{length_stats['count']:.0f}",
                        f"{length_stats['mean']:.2f} m",
                        f"{length_stats['std']:.2f} m",
                        f"{length_stats['min']:.2f} m",
                        f"{length_stats['25%']:.2f} m",
                        f"{length_stats['50%']:.2f} m",
                        f"{length_stats['75%']:.2f} m",
                        f"{length_stats['max']:.2f} m"
                    ]
                }),
                hide_index=True,
                use_container_width=True
            )
    
    else:
        st.info("📝 データが登録されていません。「データ入力」タブからデータを追加してください。")

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p><strong>栃材原木販売価格予測システム v1.2</strong></p>
    <p>予測モデル: 重回帰分析（2024年12月版）</p>
    <p style='font-size: 0.8em;'>© 2025 All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
