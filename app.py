from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import os
import hashlib

app = Flask(__name__, template_folder='templates')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

# BẮT BUỘC: Thiết lập Secret Key để có thể sử dụng Session (lưu trạng thái đăng nhập)
app.secret_key = 'ueh_secret_key_phong_chong_sql_injection'

# --- CẤU HÌNH SUPABASE ---
SUPABASE_URL = "https://ocateixuzulwmrtxseom.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9jYXRlaXh1enVsd21ydHhzZW9tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYyMTYyMTQsImV4cCI6MjA3MTc5MjIxNH0.w7PLqjLGj4hNNGDh81NwDodEUCCqVSVm_PL0FpYWif8"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- CẤU HÌNH GEMINI API ---
GEMINI_API_KEY = "AIzaSyCt3eljUhGeFX4qWYbHNPGta-f6m7p42oo"
GEMINI_MODEL = "models/gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- 1. TRANG CHỦ & CHI TIẾT ---
@app.route('/')
def home():
    url = f"{SUPABASE_URL}/rest/v1/product1?select=*&order=id.asc"
    try:
        response = requests.get(url, headers=HEADERS)
        products = response.json() if response.status_code == 200 else []
        return render_template('trangchu.html', products=products)
    except:
        return render_template('trangchu.html', products=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    url = f"{SUPABASE_URL}/rest/v1/product1?id=eq.{product_id}&select=*"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if data and len(data) > 0:
            return render_template('product_detail.html', product=data[0])
        return "Không tìm thấy sản phẩm", 404
    except: return "Lỗi hệ thống", 500

# --- 2. TÌM KIẾM (BỔ SUNG ĐỂ SỬA LỖI 404) ---
@app.route('/api/search-unsafe', methods=['POST'])
def search_unsafe():
    keyword = request.json.get('keyword', '')
    url = f"{SUPABASE_URL}/rest/v1/rpc/search_products_unsafe"
    payload = {"search_term": keyword}
    response = requests.post(url, headers=HEADERS, json=payload)
    return jsonify(response.json())

@app.route('/api/search-safe', methods=['POST'])
def search_safe():
    keyword = request.json.get('keyword', '')
    url = f"{SUPABASE_URL}/rest/v1/rpc/search_products_safe"
    payload = {"search_term": keyword}
    response = requests.post(url, headers=HEADERS, json=payload)
    return jsonify(response.json())

# --- 3. ĐĂNG NHẬP / ĐĂNG XUẤT ---
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login-unsafe', methods=['POST'])
def login_unsafe():
    username = request.form.get('username')
    password = request.form.get('password')
    url = f"{SUPABASE_URL}/rest/v1/rpc/login_unsafe_v2"
    payload = {"input_username": username, "input_password": hash_password(password)}
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        data = response.json()
        if data and len(data) > 0:
            session['user'] = data[0]
            return jsonify({'success': True, 'msg': 'SQL Injection thành công!', 'user': data[0]})
        return jsonify({'success': False, 'msg': 'Sai tài khoản'})
    except: return jsonify({'success': False, 'msg': 'Lỗi kết nối'})

@app.route('/api/login-safe', methods=['POST'])
def login_safe():
    username = request.form.get('username')
    password = request.form.get('password')
    params = {"username": f"eq.{username}", "password_hash": f"eq.{hash_password(password)}", "select": "*"}
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/tbl_user", headers=HEADERS, params=params)
        data = response.json()
        if data and len(data) > 0:
            session['user'] = data[0]
            return jsonify({'success': True, 'msg': 'Đăng nhập an toàn thành công!'})
        return jsonify({'success': False, 'msg': 'Sai tài khoản'})
    except: return jsonify({'success': False, 'msg': 'Lỗi hệ thống'})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# --- 4. CHAT AI & GIỎ HÀNG ---
@app.route('/chat')
def chat_page(): return render_template('chat.html')

@app.route('/api/chat-process', methods=['POST'])
def chat_process():
    try:
        user_message = request.json.get('message', '')
        payload = {"contents": [{"parts": [{"text": user_message}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        bot_reply = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '...')
        return jsonify({'reply': bot_reply})
    except: return jsonify({'reply': 'Lỗi hệ thống'}), 500

@app.route('/cart')
def cart(): return render_template('cart.html')

# --- 5. SỬA THÔNG TIN NGƯỜI DÙNG (CÓ CSRF) ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user'):
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')

        user_id = session['user']['id']

        url = f"{SUPABASE_URL}/rest/v1/tbl_user?id=eq.{user_id}"
        payload = {
            "fullname": fullname,
            "email": email
        }

        # ⚠️ KHÔNG CSRF TOKEN → DÍNH CSRF
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code in [200, 204]:
            # cập nhật lại session cho đẹp
            session['user']['fullname'] = fullname
            session['user']['email'] = email
            #return render_template('profile.html', success=True)
            return redirect(url_for('home'))

    return render_template('profile.html', success=False)
# --- 6. GIỮ NGUYÊN TẤT CẢ CÁC TRANG TĨNH KHÁC CỦA ANH ---
@app.route('/gioi-thieu')
def gioi_thieu(): return render_template('gioi_thieu.html')

@app.route('/chuong-trinh-hoc')
def chuong_trinh_hoc(): return render_template('chuong_trinh_hoc.html')

@app.route('/trai-nghiem-sinh-vien')
def trai_nghiem_sinh_vien(): return render_template('trai_nghiem_sinh_vien.html')

@app.route('/goc-truyen-thong')
def goc_truyen_thong(): return render_template('goc_truyen_thong.html')

@app.route('/doanh-nghiep')
def doanh_nghiep(): return render_template('doanh_nghiep.html')

@app.route('/lien-he')
def lien_he(): return render_template('lien_he.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)