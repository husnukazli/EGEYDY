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
st.set_page_config(page_title="YDY Materyal Havuzu", page_icon="📚", layout="centered")

# --- OTURUM YÖNETİMİ ---
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False, "email": "", "ad_soyad": "", "role": ""
    })

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANI
# ==========================================
if not st.session_state["logged_in"]:
    st.title("📚 EÜ YDY Materyal Havuzu")
    st.write("Lütfen sisteme giriş yapın veya yeni kayıt oluşturun.")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        login_email = st.text_input("E-posta Adresiniz", key="log_email")
        login_pass = st.text_input("Şifreniz", type="password", key="log_pass")
        if st.button("Giriş Yap", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    ad = users[0].get("ad_soyad", login_email)
                    st.session_state.update({
                        "logged_in": True, 
                        "email": login_email, 
                        "ad_soyad": ad,
                        "role": users[0]["role"]
                    })
                    st.rerun()
                else:
                    st.error("Hatalı e-posta veya şifre!")
            except Exception as e:
                st.error(f"Giriş hatası: {e}")

    with tab2:
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
                            "ad_soyad": reg_ad_soyad,
                            "email": reg_email,
                            "password": hash_password(reg_pass),
                            "role": "beklemede"
                        }).execute()
                        st.success("Kayıt başarılı! Yöneticinin onayından sonra sisteme tam erişim sağlayabilirsiniz.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
            else:
                st.error("Lütfen ad, soyad, e-posta ve şifre alanlarını eksiksiz doldurun.")

    st.divider()
    
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
    try:
        res = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
        bekleyenler = res.data
        
        if bekleyenler:
            st.write("⏳ **Onay Bekleyen Hocalar:**")
            for user in bekleyenler:
                isim = user.get("ad_soyad", "İsimsiz")
                mail = user["email"]
                col1, col2 = st.columns([3, 1])
                col1.write(f"- 👤 **{isim}** ({mail})")
                if col2.button("Yetki Ver", key=f"onay_{user['id']}"):
                    supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                    st.success(f"{isim} başarıyla yetkilendirildi!")
                    st.rerun()
        else:
            st.info("Şu an onay bekleyen kayıt bulunmuyor.")
    except Exception as e:
        st.error(f"Yönetici paneli hatası: {e}")
    st.divider()

# ==========================================
# 3. DOSYA YÜKLEME BÖLÜMÜ
# ==========================================
# Yönetici dosya yüklemesin mantığına göre sadece "onaylı" hocalar yükleyebilir
if st.session_state["role"] == "onaylı":
    st.subheader("📤 Yeni Materyal Yükle")
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
    
    if st.button("🚀 Dosyayı Havuza Yükle"):
        if kur_secimi != "Seçiniz..." and uploaded_file:
            with st.spinner("Dosya yükleniyor..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    file_path = f"{kur_secimi}/{hafta}/{uploaded_file.name}"
                    
                    supabase.storage.from_("materyaller").upload(
                        path=file_path,
                        file=file_bytes,
                        file_options={"content_type": uploaded_file.type, "upsert": "true"}
                    )
                    
                    public_url = supabase.storage.from_("materyaller").get_public_url(file_path)
                    
                    supabase.table("files").insert({
                        "file_name": uploaded_file.name,
                        "file_url": public_url,
                        "kur": kur_secimi,
                        "hafta": hafta,
                        "materyal_turu": materyal_turu,
                        "uploaded_by": st.session_state['ad_soyad']
                    }).execute()
                    
                    st.success(f"✅ '{uploaded_file.name}' başarıyla havuzdaki yerini aldı!")
                except Exception as e:
                    st.error(f"Yükleme sırasında hata oluştu: {e}")
        else:
            st.error("Lütfen bir Kur ve Yüklenecek Dosya seçin.")
    st.divider()
elif st.session_state["role"] == "beklemede":
    st.info("⏳ Dosya yükleme ve görüntüleme yetkiniz yönetici onayından sonra aktif olacaktır.")

# ==========================================
# 4. FİLTRELEME VE GÖRÜNTÜLEME BÖLÜMÜ
# ==========================================
if st.session_state["role"] in ["onaylı", "admin"]:
    st.subheader("📂 Havuzdaki Materyaller ve Filtreleme")

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        filtre_kur = st.selectbox("Filtre - Kur", ["Tümü", "Alpha", "Beta", "Gamma", "Delta", "Yan Destek / Kulüpler"])
    with f_col2:
        filtre_hafta = st.selectbox("Filtre - Hafta", ["Tümü"] + [f"{i}. Hafta" for i in range(1, 15)])

    if st.button("🔄 Dosyaları Listele"):
        with st.spinner("Veritabanı taranıyor..."):
            try:
                query = supabase.table("files").select("*")
                if filtre_kur != "Tümü":
                    query = query.eq("kur", filtre_kur)
                if filtre_hafta != "Tümü":
                    query = query.eq("hafta", filtre_hafta)
                    
                response = query.execute()
                files = response.data
                
                if not files:
                    st.warning("Seçtiğiniz kriterlere uygun materyal bulunamadı.")
                else:
                    st.success(f"Eşleşen toplam {len(files)} adet dosya listeleniyor.")
                    st.write("---")
                    
                    for file in files:
                        file_name = file.get('file_name')
                        file_link = file.get('file_url')
                        uploader = file.get('uploaded_by')
                        kur = file.get('kur')
                        hafta = file.get('hafta')
                        turu = file.get('materyal_turu')
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 **{file_name}**  \n*<small>Kur: {kur} | Hafta: {hafta} | Tür: {turu} | Yükleyen: {uploader}</small>*", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"[🔗 Görüntüle]({file_link})", unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"Dosyalar listelenirken hata oluştu: {e}")
