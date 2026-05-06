import streamlit as st
import random
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

# フォントの設定
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))

# --- UIの改善：タイトルと余白の調整 ---
st.title("英単語テスト楽々作成ツール")
st.markdown("テスト問題と解答の2枚組をワンクリックで作成！")

# --- ステップ1：設定エリア ---
st.subheader("出題形式とタイトルの設定")

# 【1行目】ラジオボタンとチェックボックスのグループ
col1, col2 = st.columns(2)
with col1:
    mode = st.radio("隠す項目", ["日本語を隠す", "英語を隠す"])
with col2:
    # 以前入れていた高さ調整用の st.write("") は不要になるので削除しています
    is_shuffle = st.checkbox("出題順をランダムにする", value=True)

st.write("") # 1行目と2行目の間に少しだけ余白を作ります

# 【2行目】タイトルと補足のグループ
col3, col4 = st.columns(2)
with col3:
    st.markdown("**テストのタイトル**<br><span style='font-size: 0.85em; color: #666;'>※最大20文字</span>", unsafe_allow_html=True)
    test_title = st.text_input("test_title", value="", placeholder="例：小テスト", max_chars=20, label_visibility="collapsed") 

with col4:
    st.markdown("**補足・指示**<br><span style='font-size: 0.85em; color: #666;'>※最大75文字・3行まで。「/」で改行できます</span>", unsafe_allow_html=True)
    sub_text = st.text_input("sub_text", value="", placeholder="例：合格点は8割です。", max_chars=75, label_visibility="collapsed")

with st.expander("💡 ご利用の注意点"):
    st.markdown("""
    - 英単語と日本語の間は、必ずスペースで区切ってください。
    - 入力された単語が50問を超える場合は、自動的にランダムで50問が抽出されます。
    - 日本語が9文字以上の場合は自動で2行に折り返されます。
    - 日本語の途中に｢/｣を入れると、好きな位置で意図的に2行に改行できます。
    """)

st.divider()

# --- ステップ2：入力エリア ---
st.subheader("単語データの入力")

# ▼単語リストのカスタムラベル（1行目を太字、2行目を小さめの文字に設定）
st.markdown("**単語リスト**<br><span style='font-size: 0.85em; color: #666;'>※英語と日本語をスペースで区切って入力。日本語は「/」で改行できます</span>", unsafe_allow_html=True)

# 入力欄本体（標準のラベルは collapsed で隠す）
raw_text = st.text_area(
    "raw_text",
    "apple りんご", 
    height=200,
    label_visibility="collapsed"
)

st.divider()

# --- ここからがPDFを作る裏側の処理 ---
def create_pdf(word_list, hide_mode, is_shuffle, title, sub):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    valid_lines = [line for line in word_list.split('\n') if line.strip() and len(line.split()) >= 2]

    if len(valid_lines) > 50:
        selected_indices = random.sample(range(len(valid_lines)), 50)
    else:
        selected_indices = list(range(len(valid_lines)))

    if is_shuffle:
        random.shuffle(selected_indices)
    else:
        selected_indices.sort()

    final_lines = [valid_lines[i] for i in selected_indices]
    total_q = len(final_lines)

    # ヘッダーを描画する共通機能
    def draw_header(canvas_obj, is_answer=False):
        actual_title = title if title else "小テスト"
        display_title = f"{actual_title}【解答】" if is_answer else actual_title
        
        title_font_size = 16
        if len(display_title) > 15:
            title_font_size = 12
            
        canvas_obj.setFont('HeiseiKakuGo-W5', title_font_size)
        canvas_obj.drawString(50, 805, display_title)

        sub_lines = []
        if sub:
            parts = sub.split('/')
            for part in parts:
                if not part:
                    continue
                sub_lines.extend([part[i:i+25] for i in range(0, len(part), 25)])
        
        sub_lines = sub_lines[:3]

        canvas_obj.setFont('HeiseiKakuGo-W5', 10)
        sub_y = 780
        for line in sub_lines:
            canvas_obj.drawString(50, sub_y, line)
            sub_y -= 12
            
        # ▼▼▼ 日付・氏名・得点の新しいレイアウト ▼▼▼
        # 日付を右上へ小さく配置します
        canvas_obj.setFont('HeiseiKakuGo-W5', 10)
        canvas_obj.drawString(450, 815, "日付：　　月　　日")
        
        # 氏名と得点を並べて配置します
        canvas_obj.setFont('HeiseiKakuGo-W5', 12)
        canvas_obj.drawString(310, 780, "氏名：")
        canvas_obj.line(350, 780, 460, 780)
        canvas_obj.drawString(470, 780, f"得点：　　/{total_q}点")

        return min(730, sub_y - 20)

    # ==============================
    # 1ページ目：テスト問題の描画
    # ==============================
    start_y = draw_header(c, is_answer=False)
    
    base_x = 50
    y_position = start_y 

    for i, line in enumerate(final_lines):
        if i >= 25:
            base_x = 320
            if i == 25: y_position = start_y

        parts = line.split()
        en = parts[0]
        ja = parts[1]

        if hide_mode == "日本語を隠す":
            c.setFont('Helvetica', 14)
            c.drawString(base_x, y_position, f"Q{i+1}. {en}")
            c.drawString(base_x + 140, y_position, "                   ")
            # カッコを手書きしやすいように幅を調整しました
            c.drawString(base_x + 130, y_position, "(")
            c.drawString(base_x + 240, y_position, ")")
        else:
            c.setFont('Helvetica', 14)
            c.drawString(base_x, y_position, f"Q{i+1}.")
            c.drawString(base_x + 35, y_position, "(")
            c.drawString(base_x + 145, y_position, ")")
            
            if '/' in ja: line1, line2 = ja.split('/', 1)
            elif len(ja) >= 9: line1, line2 = ja[:8], ja[8:]
            else: line1, line2 = ja, ""

            if line2:
                c.setFont('HeiseiKakuGo-W5', 10)
                c.drawString(base_x + 160, y_position + 4, line1)
                c.drawString(base_x + 160, y_position - 8, line2)
            else:
                c.setFont('HeiseiKakuGo-W5', 14)
                c.drawString(base_x + 160, y_position, line1)

        y_position -= 30

    c.showPage() 

    # ==============================
    # 2ページ目：解答プリントの描画
    # ==============================
    start_y = draw_header(c, is_answer=True)
    
    base_x = 50
    y_position = start_y

    for i, line in enumerate(final_lines):
        if i >= 25:
            base_x = 320
            if i == 25: y_position = start_y

        parts = line.split()
        en = parts[0]
        ja = parts[1].replace('/', '') 

        c.setFont('Helvetica', 14)
        c.drawString(base_x, y_position, f"Q{i+1}.")
        
        c.setFillColorRGB(1, 0, 0) 
        if hide_mode == "日本語を隠す":
            c.setFont('HeiseiKakuGo-W5', 14)
            c.drawString(base_x + 45, y_position, ja)
        else:
            c.setFont('Helvetica', 14)
            c.drawString(base_x + 45, y_position, en)
        
        c.setFillColorRGB(0, 0, 0) 
        
        if hide_mode == "日本語を隠す":
            c.setFont('Helvetica', 14)
            c.drawString(base_x + 160, y_position, en)
        else:
            if len(ja) >= 9:
                c.setFont('HeiseiKakuGo-W5', 10)
                c.drawString(base_x + 160, y_position + 4, ja[:8])
                c.drawString(base_x + 160, y_position - 8, ja[8:])
            else:
                c.setFont('HeiseiKakuGo-W5', 14)
                c.drawString(base_x + 160, y_position, ja)

        y_position -= 30

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
# -----------------------------------

# --- ステップ3：出力エリア ---
st.subheader("PDFの出力")
st.info("※ボタンを押すと、1ページ目に問題、2ページ目に赤字の解答が入ったPDFが作成されます。") 

if st.button("PDFプレビューを作成"):
    st.success("PDFの準備ができました。下のボタンからダウンロードしてください。")
    
    pdf_data = create_pdf(raw_text, mode, is_shuffle, test_title, sub_text)
    
    st.download_button(
        label="📥 テストと解答の2ページをまとめて保存", 
        data=pdf_data,
        file_name="english_test_with_answers.pdf",
        mime="application/pdf"
    )