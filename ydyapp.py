import streamlit as st
# Yeni eklediğimiz delete_file_from_drive fonksiyonunu da içeri aktarıyoruz
from drive_utils import upload_file_to_drive, list_files_in_folder, delete_file_from_drive

# Sayfa ayarları
st.set_page_config(page_title="Materyal Havuzu", page_icon="📚", layout="centered")

st.title("📚 Öğretmen Materyal Havuzu")
st.write("Drive'a gitmeden tüm materyallerinizi buradan yükleyebilir, görüntüleyebilir ve silebilirsiniz.")

# --- BÖLÜM 1: DOSYA YÜKLEME ---
st.subheader("📤 Yeni Dosya Yükle")
uploaded_file = st.file_uploader("Yüklemek istediğiniz dosyayı seçin", type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "mp3", "mp4"])

if st.button("🚀 Dosyayı Drive'a Yükle"):
    if uploaded_file is not None:
        with st.spinner("Dosya yükleniyor... Lütfen bekleyin."):
            try:
                file_bytes = uploaded_file.getvalue()
                uploaded = upload_file_to_drive(
                    file_bytes=file_bytes,
                    file_name=uploaded_file.name,
                    mime_type=uploaded_file.type
                )
                st.success(f"✅ '{uploaded_file.name}' başarıyla havuzunuza eklendi!")
                st.rerun() # Yükleme sonrası listeyi güncellemek için sayfayı yeniler
            except Exception as e:
                st.error(f"Yükleme sırasında bir hata oluştu: {e}")
    else:
        st.warning("Lütfen yükle butonuna basmadan önce bir dosya seçin.")

st.divider()

# --- BÖLÜM 2: DOSYALARI LİSTELEME, GÖRÜNTÜLEME VE SİLME ---
st.subheader("📂 Havuzdaki Materyaller")

with st.spinner("Drive'daki dosyalar getiriliyor..."):
    try:
        files = list_files_in_folder()
        
        if not files:
            st.info("Klasörde henüz hiç dosya bulunmuyor. İlk materyali sen yükle!")
        else:
            st.write(f"Toplam **{len(files)}** adet dosya bulundu.")
            st.write("---")
            
            # Dosyaları alt alta sıralıyoruz
            for file in files:
                file_name = file.get('name')
                file_link = file.get('webViewLink')
                file_id = file.get('id') # Silme işlemi için dosyanın kimlik numarasını alıyoruz
                
                # Arayüzü 3 sütuna bölüyoruz: İsim (geniş), Görüntüle Linki (dar), Sil Butonu (dar)
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📄 **{file_name}**")
                
                with col2:
                    st.markdown(f"[🔗 Görüntüle]({file_link})", unsafe_allow_html=True)
                
                with col3:
                    # Her butonun 'key' değeri farklı olmalı, bu yüzden file_id kullanıyoruz
                    if st.button("🗑️ Sil", key=f"del_{file_id}"):
                        with st.spinner("Siliniyor..."):
                            success = delete_file_from_drive(file_id)
                            if success:
                                st.success("Silindi!")
                                st.rerun() # Dosya silindikten sonra listeyi tazelemek için sayfayı yeniler
                            else:
                                st.error("Silinemedi.")
                                
    except Exception as e:
        st.error(f"Dosyalar listelenirken bir hata oluştu: {e}")
