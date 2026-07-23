import streamlit as st
import json
import os
import hashlib
from drive_utils import upload_file_to_drive, list_files_in_folder

# --- AYARLAR VE VERİTABANI ---
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {"admin@ydy.com": {"password": hash_password("admin123"), "role": "admin"}}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- SESSION STATE (OTURUM YÖNETİMİ) ---
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False, "email": "", "role": ""
    })

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANLARI (DIŞ KAPI)
# ==========================================
if not st.session_state["logged_in"]:
    st.title("📚 YDY Materyal Havuzu")
    st.write("Lütfen sisteme giriş yapın veya yeni kayıt oluşturun.")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    # --- GİRİŞ YAP ---
    with tab1:
        login_email = st.text_input("E-posta Adresiniz", key="log_email")
        login_pass = st.text_input("Şifreniz", type="password", key="log_pass")
        if st.button("Giriş Yap", use_container_width=True):
            users = load_users()
            if login_email in users and users[login_email]["password"] == hash_password(login_pass):
                st.session_state.update({"logged_in": True, "email": login_email, "role": users[login_email]["role"]})
                st.rerun()
            else:
                st.error("Hatalı e-posta veya şifre!")

    # --- KAYIT OL ---
    with tab2:
        reg_email = st.text_input("E-posta Adresiniz", key="reg_email")
        reg_pass = st.text_input("Şifre Belirleyin", type="password", key="reg_pass")
        
        if st.button("Kayıt Ol", use_container_width=True):
            users = load_users()
            if reg_email in users:
                st.warning("Bu e-posta zaten kayıtlı!")
            elif reg_email and reg_pass:
                users[reg_email] = {
                    "password": hash_password(reg_pass),
                    "role": "beklemede" 
                }
                save_users(users)
                st.success("Kayıt başarılı! Yöneticinin onayından sonra dosya yükleme yetkiniz açılacaktır.")
            else:
                st.error("Lütfen e-posta ve şifre alanlarını doldurun.")

    st.divider()
    
    # --- YÖNETİCİ GİRİŞİ (ŞİFRE İLE) ---
    with st.expander("🛡️ Yönetici Girişi"):
        admin_pass = st.text_input("Yönetici Şifresi", type="password", key="admin_pass")
        if st.button("Yönetici Olarak Gir"):
            users = load_users()
            admin_logged_in = False
            for mail, data in users.items():
                if data["role"] == "admin" and data["password"] == hash_password(admin_pass):
                    st.session_state.update({"logged_in": True, "email": "Yönetici", "role": "admin"})
                    admin_logged_in = True
                    st.rerun()
                    break
            if not admin_logged_in:
                 st.error("Hatalı yönetici şifresi!")
                 
    st.stop()

# ==========================================
# 2. ANA UYGULAMA (GİRİŞ YAPILDIKTAN SONRA)
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['email']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    st.write(f"🔑 Yetki: {role_color} {st.session_state['role'].upper()}")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("📚 YDY Materyal Havuzu")

# ==========================================
# 3. YÖNETİCİ PANELİ
# ==========================================
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Yönetici Paneli**")
    users = load_users()
    bekleyenler = {mail: data for mail, data in users.items() if data["role"] == "beklemede"}
    
    if bekleyenler:
        st.write("⏳ **Onay Bekleyen Kullanıcılar:**")
        for mail in bekleyenler:
            col1, col2 = st.columns([3, 1])
            col1.write(f"- {mail}")
            if col2.button("Yetki Ver (Onayla)", key=f"onay_{mail}"):
                users[mail]["role"] = "onaylı"
                save_users(users)
                st.success(f"{mail} yetkilendirildi!")
                st.rerun()
    else:
        st.info("Onay bekleyen kullanıcı bulunmuyor.")
    st.divider()

# ==========================================
# 4. DOSYA YÜKLEME VE YDY KATEGORİ SİSTEMİ (GERÇEK DRIVE API)
# ==========================================
st.subheader("📤 Yeni Materyal Yükle")

if st.session_state["role"] in ["onaylı", "admin"]:
    kur_secimi = st.selectbox("1. Kur Seçiniz", ["Seçiniz...", "Alpha", "Beta", "Gamma", "Delta", "Yan Destek / Kulüpler"])
    
    alt_beceri = ""
    omurga = ""
    if kur_secimi not in ["Seçiniz...", "Yan Destek / Kulüpler"]:
        omurga = st.selectbox("2. Ders Türü", ["Integrated Skills (Bütünleşik)", "Main Skills (Ana Beceriler)"])
        if omurga == "Integrated Skills (Bütünleşik)":
            alt_beceri = st.selectbox("3. Beceri", ["Grammar", "Vocabulary"])
        else:
            alt_beceri = st.selectbox("3. Beceri", ["Reading & Writing", "Listening & Speaking"])
    elif kur_secimi == "Yan Destek / Kulüpler":
        omurga = "Kulüp/Destek"
        alt_beceri = st.selectbox("Destek Kanalı", ["Delta A2 & Gamma B1 Remedial", "Translation Workshop", "Speaking / Read, Walk, Speak Club"])
        
    hafta = st.selectbox("4. Hafta", [f"{i}. Hafta" for i in range(1, 15)])
    materyal_turu = st.selectbox("5. Materyal Türü", ["Worksheet", "Quiz", "Sınav Örneği", "Answer Key", "Okuma Parçası", "Ses Dosyası (Listening)"])
    
    uploaded_file = st.file_uploader("Dosya Seçin", type=["pdf", "docx", "xlsx", "mp3", "jpg", "png"])
    
    if st.button("🚀 Dosyayı Drive'a Yükle"):
        if kur_secimi != "Seçiniz..." and uploaded_file:
            with st.spinner("Dosya Google Drive'a yükleniyor ve etiketleniyor..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    
                    # Dosya adına ve açıklamasına etiketleri işliyoruz ki Drive'da da net görünsün
                    etiketli_isim = f"[{kur_secimi}] [{hafta}] [{materyal_turu}] {uploaded_file.name}"
                    aciklama = f"Kur: {kur_secimi} | Ders: {omurga} | Alt Beceri: {alt_beceri} | Hafta: {hafta} | Tür: {materyal_turu} | Yükleyen: {st.session_state['email']}"
                    
                    # Gerçek Drive API çağrısı
                    upload_file_to_drive(
                        file_bytes=file_bytes,
                        file_name=etiketli_isim,
                        mime_type=uploaded_file.type
                    )
                    st.success(f"✅ '{uploaded_file.name}' başarıyla havuzdaki yerini aldı!")
                except Exception as e:
                    st.error(f"Yükleme sırasında hata oluştu: {e}")
        else:
            st.error("Lütfen bir Kur ve Yüklenecek Dosya seçin.")
else:
    st.info("⏳ Dosya yükleme yetkiniz yönetici onayından sonra aktif olacaktır.")

st.divider()

# ==========================================
# 5. DOSYALARI LİSTELEME VE GÖRÜNTÜLEME
# ==========================================
st.subheader("📂 Havuzdaki Materyaller")

if st.button("🔄 Dosyaları Listele"):
    with st.spinner("Drive'daki dosyalar getiriliyor..."):
        try:
            files = list_files_in_folder()
            if not files:
                st.info("Klasörde henüz hiç dosya bulunmuyor.")
            else:
                st.success(f"Toplam {len(files)} adet dosya bulundu.")
                for file in files:
                    file_name = file.get('name')
                    file_link = file.get('webViewLink')
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 **{file_name}**")
                    with col2:
                        st.markdown(f"[🔗 Görüntüle]({file_link})", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Dosyalar listelenirken hata oluştu: {e}")
