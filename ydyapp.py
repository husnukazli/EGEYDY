import streamlit as st
from drive_utils import upload_file_to_drive, list_files_in_folder

# Sayfa ayarları
st.set_page_config(page_title="Materyal Havuzu", page_icon="📚", layout="centered")

st.title("📚 Öğretmen Materyal Havuzu")
st.write("Drive'a gitmeden tüm materyallerinizi buradan yükleyebilir ve görüntüleyebilirsiniz.")

# --- BÖLÜM 1: DOSYA YÜKLEME ---
st.subheader("📤 Yeni Dosya Yükle")
uploaded_file = st.file_uploader("Yüklemek istediğiniz dosyayı seçin", type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "mp3", "mp4"])

if st.button("🚀 Dosyayı Drive'a Yükle"):
    if uploaded_file is not None:
        with st.spinner("Dosya yükleniyor... Lütfen bekleyin."):
            try:
                # DİKKAT: Artık folder_id göndermiyoruz, sistem bunu secrets'tan (hafızadan) otomatik alıyor.
                file_bytes = uploaded_file.getvalue()
                uploaded = upload_file_to_drive(
                    file_bytes=file_bytes,
                    file_name=uploaded_file.name,
                    mime_type=uploaded_file.type
                )
                st.success(f"✅ '{uploaded_file.name}' başarıyla havuzunuza eklendi!")
            except Exception as e:
                st.error(f"Yükleme sırasında bir hata oluştu: {e}")
    else:
        st.warning("Lütfen yükle butonuna basmadan önce bir dosya seçin.")

st.divider()

# --- BÖLÜM 2: DOSYALARI LİSTELEME VE GÖRÜNTÜLEME ---
st.subheader("📂 Havuzdaki Materyaller")

if st.button("🔄 Dosyaları Yenile / Listele"):
    with st.spinner("Drive'daki dosyalar getiriliyor..."):
        try:
            # DİKKAT: folder_id göndermiyoruz, sistem secrets'tan kendi alıyor.
            files = list_files_in_folder()
            
            if not files:
                st.info("Klasörde henüz hiç dosya bulunmuyor. İlk materyali sen yükle!")
            else:
                st.success(f"Toplam {len(files)} adet dosya bulundu.")
                
                # Dosyaları alt alta ve yanlarında link olacak şekilde sıralıyoruz
                for file in files:
                    file_name = file.get('name')
                    file_link = file.get('webViewLink')
                    
                    # Düzenli görünüm için Streamlit kolonları kullanıyoruz
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 **{file_name}**")
                    with col2:
                        # Tıklandığında yeni sekmede dosyayı açan link
                        st.markdown(f"[🔗 Görüntüle]({file_link})", unsafe_allow_html=True)
                        
        except Exception as e:
            st.error(f"Dosyalar listelenirken bir hata oluştu: {e}")
