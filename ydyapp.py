import streamlit as st
import hashlib
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Page Config
st.set_page_config(page_title="Material Share", page_icon="📚", layout="wide")

# --- SESSION MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": ""})

# ==========================================
# 1. LOGIN & REGISTER SCREEN
# ==========================================
if not st.session_state["logged_in"]:
    st.title("📚 Material Share")
    st.write("Please log in or register to continue.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Login")
        login_email = st.text_input("Email Address", key="log_email")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Log In", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    ad = users[0].get("ad_soyad", login_email)
                    st.session_state.update({"logged_in": True, "email": login_email, "ad_soyad": ad, "role": users[0]["role"]})
                    st.rerun()
                else:
                    st.error("Invalid email or password!")
            except Exception as e:
                st.error(f"Login error: {e}")

    with col2:
        st.subheader("Register")
        reg_ad_soyad = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email Address", key="reg_email")
        reg_pass = st.text_input("Create Password", type="password", key="reg_pass")
        if st.button("Register", use_container_width=True):
            if reg_email and reg_pass and reg_ad_soyad:
                try:
                    existing = supabase.table("app_users").select("*").eq("email", reg_email).execute()
                    if existing.data:
                        st.warning("This email is already registered!")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": reg_ad_soyad, "email": reg_email, "password": hash_password(reg_pass), "role": "beklemede"
                        }).execute()
                        st.success("Registration successful! You can access the system after admin approval.")
                except Exception as e:
                    st.error(f"Registration error: {e}")
            else:
                st.error("Please fill in all fields.")

    with st.expander("🛡️ Admin Access"):
        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass")
        if st.button("Log In as Admin"):
            if admin_pass == "admin123": 
                st.session_state.update({"logged_in": True, "ad_soyad": "System Admin", "email": "admin", "role": "admin"})
                st.rerun()
            else:
                 st.error("Invalid admin password!")
    st.stop()

# ==========================================
# 2. MAIN APP
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['ad_soyad']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    
    # Rol ismini İngilizce göster
    display_role = "Approved" if st.session_state['role'] == "onaylı" else "Pending" if st.session_state['role'] == "beklemede" else "Admin"
    st.write(f"🔑 Status: {role_color} {display_role.upper()}")
    
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("📚 Material Share")

# Admin Panel
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Admin Approval Panel**")
    res = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
    if res.data:
        for user in res.data:
            col1, col2 = st.columns([4, 1])
            col1.write(f"- 👤 **{user.get('ad_soyad', 'No Name')}** ({user['email']})")
            if col2.button("Approve", key=f"onay_{user['id']}"):
                supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                st.rerun()
    else:
        st.info("No pending users.")
    st.divider()

# TABS
tab_upload, tab_search = st.tabs(["📤 Upload Material", "🔍 Search & Download"])

# ==========================================
# UPLOAD TAB
# ==========================================
with tab_upload:
    if st.session_state["role"] == "onaylı":
        st.markdown("### Share a New Material")
        
        # Form inputs
        f_level = st.selectbox("1. Level", ["Select...", "Alpha", "Beta", "Gamma", "Delta"], key="yk_kur")
        f_class = st.selectbox("2. Class", ["Select...", "Integrated Skills 1", "Integrated Skills 2"], key="yk_omurga")
        f_focus = st.selectbox("3. Focus", ["Speaking", "Reading", "Listening", "Writing", "Vocabulary", "Use of English"], key="yk_beceri")
        f_week = st.selectbox("4. Week", [f"Week {i}" for i in range(1, 15)], key="yk_hafta")
        f_type = st.selectbox("5. Type of Material", ["Link (Kahoot, Bamboozle, etc.)", "Worksheet", "Exam Practice", "Presentation", "Games & Ideas"], key="yk_turu")
        
        # Link mi Dosya mı kontrolü
        is_link = "Link" in f_type
        
        if is_link:
            link_title = st.text_input("Enter Link Title (e.g., Week 2 Kahoot Quiz)")
            link_url = st.text_input("Enter URL (e.g., https://kahoot.it/...)")
            uploaded_file = None
        else:
            # SADECE BURADA İLGİLİ UZANTILARI GÜNCELLEDİM (pdf, ppt, pptx eklendi)
            uploaded_file = st.file_uploader("Select File", type=["pdf", "ppt", "pptx", "docx", "xlsx", "mp3", "jpg", "png", "jpeg"])
            link_title = ""
            link_url = ""
        
        if st.button("🚀 Share to Pool", use_container_width=True):
            if f_level == "Select..." or f_class == "Select...":
                st.error("Level and Class selection is required.")
            else:
                with st.spinner("Uploading..."):
                    try:
                        final_file_url = ""
                        final_file_name = ""
                        
                        if is_link:
                            if not link_title or not link_url:
                                st.error("Please enter both Link Title and URL.")
                                st.stop()
                            final_file_name = link_title
                            final_file_url = link_url if link_url.startswith("http") else f"https://{link_url}"
                        else:
                            if not uploaded_file:
                                st.error("Please select a file to upload.")
                                st.stop()
                                
                            file_path = f"{f_level}/{f_week}/{uploaded_file.name}"
                            
                            # Content type ayarı tarayıcıda direkt açılması için (özellikle pdf ve resimler)
                            content_type = uploaded_file.type if uploaded_file.type else "application/octet-stream"
                            
                            supabase.storage.from_("materyaller").upload(
                                path=file_path, 
                                file=uploaded_file.getvalue(), 
                                file_options={"content_type": content_type, "upsert": "true"}
                            )
                            final_file_url = supabase.storage.from_("materyaller").get_public_url(file_path)
                            final_file_name = uploaded_file.name
                        
                        # Veritabanına kayıt (Schema aynı, sadece menü isimleri İngilizce gitti)
                        supabase.table("files").insert({
                            "file_name": final_file_name, 
                            "file_url": final_file_url, 
                            "kur": f_level, 
                            "omurga": f_class, 
                            "alt_beceri": f_focus, 
                            "hafta": f_week, 
                            "materyal_turu": f_type, 
                            "uploaded_by": st.session_state['ad_soyad']
                        }).execute()
                        
                        st.success(f"✅ Shared successfully!")
                    except Exception as e:
                        st.error(f"Upload error: {e}")
                        
    elif st.session_state["role"] == "beklemede":
        st.info("⏳ Your upload access will be activated after admin approval.")
    else:
        st.info("Admins cannot upload files. Please log in with a teacher account.")

# ==========================================
# SEARCH & DOWNLOAD TAB
# ==========================================
with tab_search:
    st.markdown("### Filter Materials")
    
    col1, col2 = st.columns(2)
    with col1:
        s_level = st.selectbox("Level", ["All", "Alpha", "Beta", "Gamma", "Delta"], key="ara_kur")
        s_class = st.selectbox("Class", ["All", "Integrated Skills 1", "Integrated Skills 2"], key="ara_omurga")
        s_focus = st.selectbox("Focus", ["All", "Speaking", "Reading", "Listening", "Writing", "Vocabulary", "Use of English"], key="ara_beceri")
            
    with col2:
        s_week = st.selectbox("Week", ["All"] + [f"Week {i}" for i in range(1, 15)], key="ara_hafta")
        s_type = st.selectbox("Type of Material", ["All", "Link (Kahoot, Bamboozle, etc.)", "Worksheet", "Exam Practice", "Presentation", "Games & Ideas"], key="ara_turu")

    if st.button("🔄 Search & List", use_container_width=True):
        with st.spinner("Searching..."):
            query = supabase.table("files").select("*")
            if s_level != "All": query = query.eq("kur", s_level)
            if s_class != "All": query = query.eq("omurga", s_class)
            if s_focus != "All": query = query.eq("alt_beceri", s_focus)
            if s_week != "All": query = query.eq("hafta", s_week)
            if s_type != "All": query = query.eq("materyal_turu", s_type)
            
            files = query.execute().data
            
            if not files:
                st.warning("No materials found for these filters.")
            else:
                st.success(f"{len(files)} material(s) found.")
                for file in files:
                    with st.container():
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"📄 **{file['file_name']}**<br><small>{file['kur']} | {file['omurga']} | {file.get('alt_beceri','')} | {file['hafta']} | {file['materyal_turu']} <br> Uploaded by: {file['uploaded_by']}</small>", unsafe_allow_html=True)
                        
                        if st.session_state["role"] == "beklemede":
                            c2.info("🔒 Pending Approval")
                        else:
                            # Link ise direkt git butonu, dosya ise View ve Download butonları
                            if "Link" in file['materyal_turu']:
                                c2.markdown(f"[🔗 Go to Link]({file['file_url']})", unsafe_allow_html=True)
                            else:
                                c2.markdown(f"[👁️ View]({file['file_url']}) | [⬇️ Download]({file['file_url']}?download=)", unsafe_allow_html=True)
                        st.divider()
