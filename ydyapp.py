import streamlit as st
from drive_utils import upload_file_to_drive, list_files_in_folder

st.set_page_config(page_title="Drive Bağlantı Testi", layout="centered")

st.title("🧪 Google Drive Bağlantı & Yükleme Testi")
st.write("Bu ekran sistemin havuzla bağlantısını test etmek için geçici olarak oluşturulmuştur.")

# 1. Drive Klasör ID'sini Alalım
folder_id = st.text_input("Google Drive Klasör ID'sini Buraya Yapıştırın:", value="")

if folder_id:
    st.divider()
    
    # 2. Dosya Yükleme Bölümü
    st.subheader("1. Havuza Dosya Yükle")
    uploaded_file = st.file_uploader("Bir test dosyası seçin (PDF, Word, Görsel vs.):")
    
    if uploaded_file is not None:
        if st.button("Seçili Dosyayı Drive'a Gönder"):
            with st.spinner("Dosya Google Drive havuzuna yükleniyor..."):
                try:
                    file_bytes = uploaded_file.read()
                    res = upload_file_to_drive(file_bytes, uploaded_file.name, folder_id)
                    st.success(f"✅ Dosya başarıyla yüklendi! Dosya Adı: {res.get('name')}")
                    st.markdown(f"[Drive'da Görmek İçin Tıklayın]({res.get('webViewLink')})")
                except Exception as e:
                    st.error(f"Yükleme sırasında hata oluştu: {e}")

    st.divider()

    # 3. Havuzdaki Dosyaları Okuma Bölümü
    st.subheader("2. Havuzdaki Dosyaları Listele")
    if st.button("Havuzu Yenile / Dosyaları Getir"):
        with st.spinner("Drive klasörü taranıyor..."):
            try:
                files = list_files_in_folder(folder_id)
                if not files:
                    st.info("Bu klasörde henüz yüklenmiş bir dosya yok.")
                else:
                    st.write(f"Bulunan Dosya Sayısı: **{len(files)}**")
                    for f in files:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 **{f.get('name')}**")
                        with col2:
                            st.markdown(f"[Aç / İndir]({f.get('webViewLink')})")
            except Exception as e:
                st.error(f"Dosyalar çekilirken hata oluştu: {e}")
else:
    st.warning("Devam etmek için lütfen yukarıdaki kutuya Google Drive Klasör ID'nizi girin.")
