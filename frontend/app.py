import streamlit as st
import pandas as pd
import requests
import os

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="VeriTemiz AI", page_icon="🧹", layout="wide")

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🧹 VeriTemiz AI")
    st.markdown("**v1.0.0** | BLM 4121")
    st.divider()
    st.markdown("**Büşra Yavuz**  \n2211502034  \nOcak 2026")

# ── MAIN ──
st.title("🧹 Yapay Zekâ Destekli Veri Temizleme Sistemi")
st.markdown("CSV, TXT, XLSX formatındaki veri setlerinizi yükleyin, analiz edin ve temizleyin.")

# ── ADIM 1: Dosya Yükleme ──
st.header("📂 1. Veri Yükleme")

uploaded_file = st.file_uploader(
    "Dosyanızı seçin",
    type=["csv", "txt", "xlsx"],
    help="Desteklenen formatlar: CSV, TXT, XLSX"
)

if uploaded_file is not None:
    # Backend'e dosya gönder
    with st.spinner("Dosya yükleniyor..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        response = requests.post(f"{API_URL}/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            dataset_id = data["dataset_id"]
            meta = data["meta"]
            
            st.success(f"✅ Dosya başarıyla yüklendi! (Dataset ID: {dataset_id})")
            
            # Meta bilgileri göster
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Dosya Adı", meta["filename"])
            col2.metric("Format", meta["format"])
            col3.metric("Satır Sayısı", f"{meta['row_count']:,}")
            col4.metric("Sütun Sayısı", meta["col_count"])
            
            st.session_state["dataset_id"] = dataset_id
            st.session_state["meta"] = meta
        else:
            st.error("❌ Dosya yüklenemedi.")

# ── ADIM 2: Analiz ──
if "dataset_id" in st.session_state:
    st.divider()
    st.header("🔍 2. Veri Analizi")
    
    if st.button("Analizi Başlat", type="primary"):
        with st.spinner("Analiz yapılıyor..."):
            response = requests.get(f"{API_URL}/analyze/{st.session_state['dataset_id']}")
            
            if response.status_code == 200:
                data = response.json()
                profile = data["profile"]
                recommendations = data["recommendations"]
                
                st.session_state["profile"] = profile
                st.session_state["recommendations"] = recommendations
                st.success("✅ Analiz tamamlandı!")

# ── ADIM 3: Öneriler ──
if "recommendations" in st.session_state:
    st.divider()
    st.header("💡 3. Öneriler ve Seçim")
    
    rec_data = st.session_state["recommendations"]
    
    st.metric("Toplam Problem", rec_data["total"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Eksik Değer", rec_data["missing_count"])
    col2.metric("Aykırı Değer", rec_data["outlier_count"])
    col3.metric("Format Hatası", rec_data["format_count"])
    
    st.divider()
    
    # Her öneri için seçim dropdown'ı
    if "user_selections" not in st.session_state:
        st.session_state["user_selections"] = {}
    
    for rec in rec_data["recommendations"]:
        with st.expander(f"{'🔴' if rec['severity']=='high' else '🟡' if rec['severity']=='medium' else '🟢'} [{rec['category'].upper()}] {rec['summary']}"):
            st.markdown(f"**Sütun:** `{rec['column']}`")
            
            option_names = [opt["name"] for opt in rec["options"]]
            selected = st.selectbox(
                "Yöntem Seçin:",
                option_names,
                key=f"select_{rec['id']}"
            )
            
            # Seçilen yöntemin detaylarını göster
            for opt in rec["options"]:
                if opt["name"] == selected:
                    st.info(opt["desc"])
                    st.session_state["user_selections"][rec['id']] = {
                        "category": rec["category"],
                        "column": rec["column"],
                        "method": opt["id"]
                    }

# ── ADIM 4: Pipeline Uygula ──
if "user_selections" in st.session_state and len(st.session_state["user_selections"]) > 0:
    st.divider()
    st.header("⚡ 4. Temizlik İşlemini Uygula")
    
    st.write(f"**{len(st.session_state['user_selections'])} yöntem seçildi.**")
    
    if st.button("🚀 Tümünü Uygula", type="primary"):
        with st.spinner("Pipeline çalışıyor..."):
            selections = list(st.session_state["user_selections"].values())
            payload = {"selections": selections}
            response = requests.post(
                f"{API_URL}/apply/{st.session_state['dataset_id']}",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ {result['applied_count']} işlem başarıyla uygulandı!")
                
                col1, col2 = st.columns(2)
                col1.metric("Temizlik Öncesi Eksik %", f"%{result['before_missing_pct']}")
                col2.metric("Temizlik Sonrası Eksik %", f"%{result['after_missing_pct']}")
                
                st.info(f"📁 Temizlenmiş dosya: `{result['output_path']}`")
                
                # Temizlenmiş dosyayı indir
                with open(result['output_path'], 'rb') as f:
                    st.download_button(
                        label="⬇️ Temizlenmiş Dosyayı İndir",
                        data=f,
                        file_name=os.path.basename(result['output_path']),
                        mime="text/csv"
                    )
                
                # Logları göster
                with st.expander("📋 İşlem Günlüğü"):
                    for log in result["logs"]:
                        icon = "✅" if log["status"] == "ok" else "❌"
                        st.write(f"{icon} **[{log['timestamp']}]** {log['detail']}")
            else:
                st.error("❌ Pipeline uygulanamadı.")