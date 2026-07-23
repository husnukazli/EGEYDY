import streamlit as st
import hashlib
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Sayfa Yapılandırması
st.set_page_config(page_title="YDY Materyal Havuzu", page_icon="📚", layout="wide")

# --- OTURUM YÖNETİMİ ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": ""})

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANI
# ==========================================
if not st.session_state["logged_in"]:
    st.title("📚 EÜ YDY Materyal Havuzu")
    st.write("Lütfen sisteme giriş yapın veya kayıt oluşturun.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Giriş Yap")
        login_email = st.text_input("E-posta Adresiniz", key="log_email")
        login_pass = st.text_input("Şifreniz", type="password", key="log_pass")
        if st.button("Giriş Yap", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    ad = users[0].get("ad_soyad", login_email)
                    st.session_state.update({"logged_in": True, "email": login_email, "ad_soyad": ad, "role": users[0]["role"]})
                    st.rerun()
                else:
                    st.error("Hatalı e-posta veya şifre!")
            except Exception as e:
                st.error(f"Giriş hatası: {e}")

    with col2:
        st.subheader("Kayıt Ol")
        reg_ad_soyad = st.text_input("Adınız ve Soyadınız", key="reg_name")
        reg_email = st.text_input("E-posta Adresiniz", key="reg_email")
        reg_pass = st.text_input("Şifre Belirleyin", type="password", key="reg_pass")
        if st.button("Kayıt Ol", use_container_width=True):
            if reg_email and reg_pass and reg_ad_soyad:
                try:
                    existing = supabase.table("app_users").select("*").eq("email", reg_email).execute()
                    if existing.data:
                        st.warning("Bu e-posta zaten kayıtlı!")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": reg_ad_soyad, "email": reg_email, "password": hash_password(reg_pass), "role": "beklemede"
                        }).execute()
                        st.success("Kayıt başarılı! Yönetici onayından sonra giriş yapabilirsiniz.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
            else:
                st.error("Lütfen tüm alanları doldurun.")

    with st.expander("🛡️ Yönetici Girişi"):
        admin_pass = st.text_input("Yönetici Şifresi", type="password", key="admin_pass")
        if st.button("Yönetici Olarak Gir"):
            if admin_pass == "admin123": 
                st.session_state.update({"logged_in": True, "ad_soyad": "Sistem Yöneticisi", "email": "admin", "role": "admin"})
                st.rerun()
            else:
                 st.error("Hatalı yönetici şifresi!")
    st.stop()

# ==========================================
# 2. ANA UYGULAMA (GİRİŞ YAPILDIKTAN SONRA)
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['ad_soyad']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    st.write(f"🔑 Yetki: {role_color} {st.session_state['role'].upper()}")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("📚 EÜ YDY Materyal Havuzu")

# Yönetici Paneli
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Yönetici Onay Paneli**")
    res = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
    if res.data:
        for user in res.data:
            col1, col2 = st.columns([4, 1])
            col1.write(f"- 👤 **{user.get('ad_soyad', 'İsimsiz')}** ({user['email']})")
            if col2.button("Yetki Ver", key=f"onay_{user['id']}"):
                supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                st.rerun()
    else:
        st.info("Onay bekleyen kayıt bulunmuyor.")
    st.divider()

# SEKMELERİ AYIRIYORUZ: YÜKLEME VE ARAMA
tab_yukle, tab_ara = st.tabs(["📤 Materyal Yükle", "🔍 Havuzda Ara ve İndir"])

# ==========================================
# YÜKLEME SEKMESİ
# ==========================================
with tab_yukle:
    if st.session_state["role"] == "onaylı":
        st.markdown("### Yeni Materyal Yükle")
        
        # Filtreleme Ağacı
        kur_secimi = st.selectbox("1. Kur Seçiniz", ["Seçiniz...", "Alpha", "Beta", "Gamma", "Delta", "Yan Destek / Kulüpler"], key="yk_kur")
        omurga = "Belirtilmedi"
        alt_beceri = "Belirtilmedi"
        
        if kur_secimi not in ["Seçiniz...", "Yan Destek / Kulüpler"]:
            omurga = st.selectbox("2. Ders Türü", ["Integrated Skills (Bütünleşik)", "Main Skills (Ana Beceriler)"], key="yk_omurga")
            if omurga == "Integrated Skills (Bütünleşik)":
                alt_beceri = st.selectbox("3. Beceri", ["Grammar", "Vocabulary"], key="yk_beceri_int")
            else:
                alt_beceri = st.selectbox("3. Beceri", ["Reading & Writing", "Listening & Speaking"], key="yk_beceri_main")
        elif kur_secimi == "Yan Destek / Kulüpler":
            omurga = "Kulüp/Destek"
            alt_beceri = st.selectbox("Destek Kanalı", ["Delta A2 & Gamma B1 Remedial", "Translation Workshop", "Speaking / Read, Walk, Speak Club"], key="yk_destek")
            
        hafta = st.selectbox("4. Hafta", [f"{i}. Hafta" for i in range(1, 15)], key="yk_hafta")
        materyal_turu = st.selectbox("5. Materyal Türü", ["Worksheet", "Quiz", "Sınav Örneği", "Answer Key", "Okuma Parçası", "Ses Dosyası (Listening)"], key="yk_turu")
        
        uploaded_file = st.file_uploader("Dosya Seçin", type=["pdf", "docx", "xlsx", "mp3", "jpg", "png"])
        
        if st.button("🚀 Dosyayı Havuza Yükle", use_container_width=True):
            if kur_secimi != "Seçiniz..." and uploaded_file:
                with st.spinner("Dosya yükleniyor..."):
                    try:
                        file_path = f"{kur_secimi}/{hafta}/{uploaded_file.name}"
                        supabase.storage.from_("materyaller").upload(path=file_path, file=uploaded_file.getvalue(), file_options={"content_type": uploaded_file.type, "upsert": "true"})
                        public_url = supabase.storage.from_("materyaller").get_public_url(file_path)
                        
                        supabase.table("files").insert({
                            "file_name": uploaded_file.name, "file_url": public_url, "kur": kur_secimi, 
                            "omurga": omurga, "alt_beceri": alt_beceri, "hafta": hafta, 
                            "materyal_turu": materyal_turu, "uploaded_by": st.session_state['ad_soyad']
                        }).execute()
                        st.success(f"✅ Başarılı!")
                    except Exception as e:
                        st.error(f"Yükleme hatası: {e}")
            else:
                st.error("Kur ve Dosya seçimi zorunludur.")
    elif st.session_state["role"] == "beklemede":
        st.info("⏳ Yükleme yetkiniz onaylandıktan sonra açılacaktır.")
    else:
        st.info("Yöneticiler dosya yüklemez. Kendi hesabınızla giriniz.")

# ==========================================
# ARAMA VE İNDİRME SEKMESİ
# ==========================================
with tab_ara:
    st.markdown("### Materyal Filtrele")
    
    col1, col2 = st.columns(2)
    with col1:
        f_kur = st.selectbox("Kur", ["Tümü", "Alpha", "Beta", "Gamma", "Delta", "Yan Destek / Kulüpler"], key="ara_kur")
        f_omurga = "Tümü"
        f_alt_beceri = "Tümü"
        
        if f_kur not in ["Tümü", "Yan Destek / Kulüpler"]:
            f_omurga = st.selectbox("Ders Türü", ["Tümü", "Integrated Skills (Bütünleşik)", "Main Skills (Ana Beceriler)"], key="ara_omurga")
            if f_omurga == "Integrated Skills (Bütünleşik)":
                f_alt_beceri = st.selectbox("Beceri", ["Tümü", "Grammar", "Vocabulary"], key="ara_beceri_int")
            elif f_omurga == "Main Skills (Ana Beceriler)":
                f_alt_beceri = st.selectbox("Beceri", ["Tümü", "Reading & Writing", "Listening & Speaking"], key="ara_beceri_main")
        elif f_kur == "Yan Destek / Kulüpler":
            f_omurga = "Kulüp/Destek"
            f_alt_beceri = st.selectbox("Destek Kanalı", ["Tümü", "Delta A2 & Gamma B1 Remedial", "Translation Workshop", "Speaking / Read, Walk, Speak Club"], key="ara_destek")
            
    with col2:
        f_hafta = st.selectbox("Hafta", ["Tümü"] + [f"{i}. Hafta" for i in range(1, 15)], key="ara_hafta")
        f_turu = st.selectbox("Materyal Türü", ["Tümü", "Worksheet", "Quiz", "Sınav Örneği", "Answer Key", "Okuma Parçası", "Ses Dosyası (Listening)"], key="ara_turu")

    if st.button("🔄 Dosyaları Listele", use_container_width=True):
        with st.spinner("Aranıyor..."):
            query = supabase.table("files").select("*")
            if f_kur != "Tümü": query = query.eq("kur", f_kur)
            if f_omurga != "Tümü": query = query.eq("omurga", f_omurga)
            if f_alt_beceri != "Tümü": query = query.eq("alt_beceri", f_alt_beceri)
            if f_hafta != "Tümü": query = query.eq("hafta", f_hafta)
            if f_turu != "Tümü": query = query.eq("materyal_turu", f_turu)
            
            files = query.execute().data
            
            if not files:
                st.warning("Bu kriterlere uygun materyal bulunamadı.")
            else:
                st.success(f"{len(files)} adet dosya bulundu.")
                for file in files:
                    with st.container():
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"📄 **{file['file_name']}**<br><small>{file['kur']} | {file.get('alt_beceri','')} | {file['hafta']} | {file['materyal_turu']} | Yükleyen: {file['uploaded_by']}</small>", unsafe_allow_html=True)
                        if st.session_state["role"] == "beklemede":
                            c2.info("🔒 Onay Bekleniyor")
                        else:
                            c2.markdown(f"[👁️ Görüntüle]({file['file_url']}) | [⬇️ İndir]({file['file_url']}?download=)", unsafe_allow_html=True)
                        st.divider()
