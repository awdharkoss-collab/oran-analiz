import streamlit as st
import pandas as pd
import kagglehub
import os
import glob

st.set_page_config(page_title="Oran Analiz Pro", page_icon="⚽", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    label, .stRadio label, .stSelectbox label, .stNumberInput label, p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .metric-card {
        background-color: #1c222d;
        border: 1px solid #2e3748;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-bottom: 8px;
    }
    .metric-title { font-size: 12px; color: #9aa5b1; font-weight: bold; }
    .metric-value { font-size: 20px; color: #00e676; font-weight: bold; }
    .metric-sub { font-size: 11px; color: #cbd2d9; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Oran Analiz Pro")
st.caption("Geçmiş Maç & Oran İstatistik Sistemi")

@st.cache_data(show_spinner="Açılış ve Gerçek Kapanış oranları derleniyor (~25 sn)...")
def veriyi_yukle_v4():
    df_list = []

    # 1. Kaggle Geniş Açılış Arşivi (2000 - 2025)
    try:
        p1 = kagglehub.dataset_download("adamgbor/club-football-match-data-2000-2025")
        p2 = kagglehub.dataset_download("ahmadasadi00/football-betting-odds")
        dosyalar = glob.glob(os.path.join(p1, "**/*.csv"), recursive=True) + glob.glob(os.path.join(p2, "**/*.csv"), recursive=True)
        for d in dosyalar:
            if os.path.getsize(d) > 50000:
                try:
                    df_list.append(pd.read_csv(d, low_memory=False))
                except:
                    pass
    except:
        pass

    # 2. Resmi Football-Data Gerçek Kapanış Oranlı Sezonlar (2019 - 2026)
    ligler = ["E0", "E1", "E2", "E3", "D1", "D2", "SP1", "SP2", "I1", "I2", "F1", "F2", "T1", "N1", "P1", "B1", "SC0", "G1"]
    sezonlar = ["2526", "2425", "2324", "2223", "2122", "2021", "1920"]
    for sez in sezonlar:
        for lg in ligler:
            url = f"https://football-data.co.uk{sez}/{lg}.csv"
            try:
                t_df = pd.read_csv(url, encoding="latin1", on_bad_lines="skip")
                if "B365CH" in t_df.columns or "PSCH" in t_df.columns:
                    df_list.append(t_df)
            except:
                pass

    df = pd.concat(df_list, ignore_index=True)

    df["LigKod"] = df["Division"].fillna(df["Div"]) if ("Division" in df.columns and "Div" in df.columns) else df.get("Division", df.get("Div", "Diğer"))
    df["Tarih"] = df["MatchDate"].fillna(df["Date"]) if ("MatchDate" in df.columns and "Date" in df.columns) else df.get("MatchDate", df.get("Date", "-"))
    df["EvSahibi"] = df["HomeTeam"].fillna(df["Home"]) if ("HomeTeam" in df.columns and "Home" in df.columns) else df.get("HomeTeam", df.get("Home", "-"))
    df["Deplasman"] = df["AwayTeam"].fillna(df["Away"]) if ("AwayTeam" in df.columns and "Away" in df.columns) else df.get("AwayTeam", df.get("Away", "-"))

    def sutun_birlestir(aday_listesi):
        seri = pd.Series(pd.NA, index=df.index)
        for col in aday_listesi:
            if col in df.columns:
                seri = seri.fillna(df[col])
        return pd.to_numeric(seri, errors="coerce")

    # Açılış Oranları
    df["Ac_MS1"] = sutun_birlestir(["OddHome", "B365H", "PSH", "AvgH"])
    df["Ac_MSX"] = sutun_birlestir(["OddDraw", "B365D", "PSD", "AvgD"])
    df["Ac_MS2"] = sutun_birlestir(["OddAway", "B365A", "PSA", "AvgA"])

    # Gerçek Kapanış Oranları
    df["Kap_MS1"] = sutun_birlestir(["B365CH", "PSCH", "AvgCH", "MaxCH", "CloseHome"])
    df["Kap_MSX"] = sutun_birlestir(["B365CD", "PSCD", "AvgCD", "MaxCD", "CloseDraw"])
    df["Kap_MS2"] = sutun_birlestir(["B365CA", "PSCA", "AvgCA", "MaxCA", "CloseAway"])

    df["IY_Ev"] = sutun_birlestir(["HTHome", "HTHG"])
    df["IY_Dep"] = sutun_birlestir(["HTAway", "HTAG"])
    df["MS_Ev"] = sutun_birlestir(["FTHome", "FTHG"])
    df["MS_Dep"] = sutun_birlestir(["FTAway", "FTAG"])

    df = df.dropna(subset=["MS_Ev", "MS_Dep", "Ac_MS1", "Ac_MS2"]).drop_duplicates(subset=["Tarih", "EvSahibi", "Deplasman"], keep="last").copy()

    lig_sozlugu = {
        "E0": "İngiltere Premier Lig", "E1": "İngiltere Championship", "E2": "İngiltere League 1", "E3": "İngiltere League 2",
        "D1": "Almanya Bundesliga 1", "D2": "Almanya Bundesliga 2", "SP1": "İspanya La Liga", "SP2": "İspanya La Liga 2",
        "I1": "İtalya Serie A", "I2": "İtalya Serie B", "F1": "Fransa Ligue 1", "F2": "Fransa Ligue 2",
        "T1": "Türkiye Süper Lig", "T2": "Türkiye 1. Lig", "N1": "Hollanda Eredivisie", "P1": "Portekiz Premier Lig",
        "B1": "Belçika Pro League", "B2": "Belçika 2. Lig", "SC0": "İskoçya Premiership", "G1": "Yunanistan Süper Lig"
    }
    df["Lig"] = df["LigKod"].astype(str).str.strip().map(lig_sozlugu).fillna(df["LigKod"])

    iy_ev = df["IY_Ev"].fillna(0).astype(int)
    iy_dep = df["IY_Dep"].fillna(0).astype(int)
    ms_ev = df["MS_Ev"].fillna(0).astype(int)
    ms_dep = df["MS_Dep"].fillna(0).astype(int)

    iy_s = pd.Series("X", index=df.index)
    iy_s[iy_ev > iy_dep] = "1"
    iy_s[iy_ev < iy_dep] = "2"

    ms_s = pd.Series("X", index=df.index)
    ms_s[ms_ev > ms_dep] = "1"
    ms_s[ms_ev < ms_dep] = "2"

    return pd.DataFrame({
        "Lig": df["Lig"], "Tarih": df["Tarih"], "EvSahibi": df["EvSahibi"], "Deplasman": df["Deplasman"],
        "Ac_MS1": df["Ac_MS1"], "Ac_MSX": df["Ac_MSX"], "Ac_MS2": df["Ac_MS2"],
        "Kap_MS1": df["Kap_MS1"], "Kap_MSX": df["Kap_MSX"], "Kap_MS2": df["Kap_MS2"],
        "IYSkor": iy_ev.astype(str) + "-" + iy_dep.astype(str),
        "MSSkor": ms_ev.astype(str) + "-" + ms_dep.astype(str),
        "IyMs": iy_s + "/" + ms_s,
        "Ms": ms_s,
        "MsKg": ((ms_ev > 0) & (ms_dep > 0)).map({True: "VAR", False: "YOK"}),
        "AU25": ((ms_ev + ms_dep) > 2.5).map({True: "ÜST", False: "ALT"}),
        "AU35": ((ms_ev + ms_dep) > 3.5).map({True: "ÜST", False: "ALT"})
    })

df_maclar = veriyi_yukle_v4()
kapanis_sayisi = df_maclar["Kap_MS1"].notna().sum()
st.caption(f"📊 Açılış Havuzu: {len(df_maclar):,} Maç | Gerçek Kapanış Havuzu: {kapanis_sayisi:,} Maç")

oran_tipi = st.radio("Oran Türü:", ["Açılış", "Kapanış"], horizontal=True)
c1, c2 = st.columns(2)
ms1 = c1.number_input("MS 1 Oran", min_value=0.0, value=1.82, step=0.01, format="%.2f")
msx = c2.number_input("MS X Oran (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")

c3, c4 = st.columns(2)
ms2 = c3.number_input("MS 2 Oran", min_value=0.0, value=3.90, step=0.01, format="%.2f")
tol = c4.number_input("Tolerans (±)", min_value=0.0, value=0.02, step=0.01, format="%.2f")

lig_listesi = ["Tüm Ligler"] + sorted(df_maclar["Lig"].dropna().unique().tolist())
secilen_lig = st.selectbox("Lig Seçin:", lig_listesi)

col_1 = "Ac_MS1" if oran_tipi == "Açılış" else "Kap_MS1"
col_x = "Ac_MSX" if oran_tipi == "Açılış" else "Kap_MSX"
col_2 = "Ac_MS2" if oran_tipi == "Açılış" else "Kap_MS2"

filtre = pd.Series(True, index=df_maclar.index)
if ms1 > 0: filtre &= df_maclar[col_1].between(ms1 - tol, ms1 + tol)
if msx > 0: filtre &= df_maclar[col_x].between(msx - tol, msx + tol)
if ms2 > 0: filtre &= df_maclar[col_2].between(ms2 - tol, ms2 + tol)
if secilen_lig != "Tüm Ligler": filtre &= (df_maclar["Lig"] == secilen_lig)

sonuc = df_maclar[filtre].copy()
toplam = len(sonuc)

if toplam > 0:
    m1 = (sonuc["Ms"] == "1").sum()
    mx = (sonuc["Ms"] == "X").sum()
    m2 = (sonuc["Ms"] == "2").sum()
    u25 = (sonuc["AU25"] == "ÜST").sum()
    kg = (sonuc["MsKg"] == "VAR").sum()

    k1, k2, k3 = st.columns(3)
    k1.markdown(f'<div class="metric-card"><div class="metric-title">MAÇ</div><div class="metric-value">{toplam}</div><div class="metric-sub">Havuz: {len(df_maclar):,}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-card"><div class="metric-title">2.5 ÜST</div><div class="metric-value">%{u25/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {u25}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-title">KG VAR</div><div class="metric-value">%{kg/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {kg}</div></div>', unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div class="metric-card"><div class="metric-title">MS 1</div><div class="metric-value">%{m1/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {m1}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="metric-card"><div class="metric-title">MS X</div><div class="metric-value">%{mx/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {mx}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="metric-card"><div class="metric-title">MS 2</div><div class="metric-value">%{m2/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {m2}</div></div>', unsafe_allow_html=True)

    st.subheader("🎯 İY / MS Dağılımı")
    iyms_df = sonuc["IyMs"].value_counts().reset_index()
    iyms_df.columns = ["İY/MS", "Adet"]
    iyms_df["Yüzde (%)"] = (iyms_df["Adet"] / toplam * 100).round(1)
    st.dataframe(iyms_df, use_container_width=True, hide_index=True)

    st.subheader("📋 Eşleşen Maçlar")
    def renklendir(val):
        if val in ["ÜST", "VAR"]: return "background-color: #00b050; color: white; font-weight: bold;"
        if val in ["ALT", "YOK"]: return "background-color: #c00000; color: white; font-weight: bold;"
        if val in ["1", "2", "1/1", "2/2", "2/1", "1/2"]: return "background-color: #ed7d31; color: white; font-weight: bold;"
        return ""

    st.dataframe(sonuc.head(150).style.map(renklendir, subset=["Ms", "IyMs", "MsKg", "AU25", "AU35"]), use_container_width=True, hide_index=True)
else:
    st.warning("Bu oranlarda maç bulunamadı. Tolerans değerini artırarak tekrar deneyin.")

st.caption("ℹ️ Bu uygulama yalnızca geçmiş maç verilerine dayalı istatistiksel analiz sunar; bahis oynatmaz.")
