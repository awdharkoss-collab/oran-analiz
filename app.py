import streamlit as st
import pandas as pd
import kagglehub
import os
import glob
import gc

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
st.caption("Geçmiş Maç & Açılış Oran İstatistik Sistemi")

@st.cache_data(show_spinner="Açılış oranları ve tüm market verileri yükleniyor (~20 sn)...")
def veriyi_yukle_acilis():
    ham_list = []
    for ds in ["adamgbor/club-football-match-data-2000-2025", "ahmadasadi00/football-betting-odds"]:
        try:
            yol = kagglehub.dataset_download(ds)
            for d in glob.glob(os.path.join(yol, "**/*.csv"), recursive=True):
                if os.path.getsize(d) > 30000:
                    try:
                        ham_list.append(pd.read_csv(d, low_memory=False))
                    except:
                        pass
        except:
            pass

    hedef_haritasi = {
        "LigKod": ["Division", "Div", "League", "league", "Country"],
        "Tarih": ["MatchDate", "Date", "date"],
        "EvSahibi": ["HomeTeam", "Home"],
        "Deplasman": ["AwayTeam", "Away"],
        "Ac_MS1": ["OddHome", "B365H", "PSH", "WHH", "AvgH", "MaxH"],
        "Ac_MSX": ["OddDraw", "B365D", "PSD", "WHD", "AvgD", "MaxD"],
        "Ac_MS2": ["OddAway", "B365A", "PSA", "WHA", "AvgA", "MaxA"],
        "Ac_Ust25": ["B365>2.5", "P>2.5", "BbAv>2.5", "Avg>2.5", "Over25", "OddOver25"],
        "Ac_Alt25": ["B365<2.5", "P<2.5", "BbAv<2.5", "Avg<2.5", "Under25", "OddUnder25"],
        "Ac_KgVar": ["B365BTTSY", "BTTSY", "OddBTTSYes", "KGVar"],
        "Ac_KgYok": ["B365BTTSN", "BTTSN", "OddBTTSNo", "KGYok"],
        "Ac_IY15Ust": ["IY15Ust", "HT_Over15"],
        "Ac_IY15Alt": ["IY15Alt", "HT_Under15"],
        "Ac_IY05Ust": ["IY05Ust", "HT_Over05"],
        "Ac_IY05Alt": ["IY05Alt", "HT_Under05"],
        "IY_Ev": ["HTHome", "HTHG"],
        "IY_Dep": ["HTAway", "HTAG"],
        "MS_Ev": ["FTHome", "FTHG", "HG"],
        "MS_Dep": ["FTAway", "FTAG", "AG"]
    }

    parcalar = []
    for temp in ham_list:
        sozluk = {}
        for hedef, adaylar in hedef_haritasi.items():
            for a in adaylar:
                if a in temp.columns:
                    sozluk[hedef] = temp[a]
                    break
        if all(k in sozluk for k in ["EvSahibi", "Deplasman", "Ac_MS1", "MS_Ev", "MS_Dep"]):
            parcalar.append(pd.DataFrame(sozluk))

    del ham_list
    gc.collect()

    temiz = pd.concat(parcalar, ignore_index=True)
    del parcalar
    gc.collect()

    sayisal_kolonlar = [
        "Ac_MS1", "Ac_MSX", "Ac_MS2",
        "Ac_Ust25", "Ac_Alt25", "Ac_KgVar", "Ac_KgYok",
        "Ac_IY15Ust", "Ac_IY15Alt", "Ac_IY05Ust", "Ac_IY05Alt",
        "IY_Ev", "IY_Dep", "MS_Ev", "MS_Dep"
    ]
    for col in sayisal_kolonlar:
        if col not in temiz.columns:
            temiz[col] = pd.NA
        temiz[col] = pd.to_numeric(temiz[col], errors="coerce").astype("float32")

    temiz["LigKod"] = temiz.get("LigKod", pd.Series("Diğer", index=temiz.index)).fillna("Diğer")
    temiz["Tarih"] = temiz.get("Tarih", pd.Series("-", index=temiz.index)).astype(str).str.slice(0, 10)

    temiz = temiz.dropna(subset=["MS_Ev", "MS_Dep", "Ac_MS1", "Ac_MS2"])
    temiz = temiz[(temiz["Ac_MS1"] > 1.0) & (temiz["Ac_MS2"] > 1.0)]
    temiz = temiz.sort_values(by="Ac_Ust25", na_position="first")
    temiz = temiz.drop_duplicates(subset=["EvSahibi", "Deplasman", "MS_Ev", "MS_Dep", "Ac_MS1"], keep="last").copy()

    lig_sozlugu = {
        "E0": "İngiltere Premier Lig", "E1": "İngiltere Championship", "E2": "İngiltere League 1", "E3": "İngiltere League 2", "EC": "İngiltere National League",
        "D1": "Almanya Bundesliga 1", "D2": "Almanya Bundesliga 2", "SP1": "İspanya La Liga", "SP2": "İspanya La Liga 2",
        "I1": "İtalya Serie A", "I2": "İtalya Serie B", "F1": "Fransa Ligue 1", "F2": "Fransa Ligue 2",
        "T1": "Türkiye Süper Lig", "T2": "Türkiye 1. Lig", "N1": "Hollanda Eredivisie", "P1": "Portekiz Premier Lig",
        "B1": "Belçika Pro League", "SC0": "İskoçya Premiership", "SC1": "İskoçya Championship", "G1": "Yunanistan Süper Lig"
    }
    temiz["Lig"] = temiz["LigKod"].astype(str).str.strip().map(lig_sozlugu).fillna(temiz["LigKod"]).astype("category")

    iy_ev = temiz["IY_Ev"].fillna(0).astype("int8")
    iy_dep = temiz["IY_Dep"].fillna(0).astype("int8")
    ms_ev = temiz["MS_Ev"].fillna(0).astype("int8")
    ms_dep = temiz["MS_Dep"].fillna(0).astype("int8")

    iy_s = pd.Series("X", index=temiz.index)
    iy_s[iy_ev > iy_dep] = "1"
    iy_s[iy_ev < iy_dep] = "2"

    ms_s = pd.Series("X", index=temiz.index)
    ms_s[ms_ev > ms_dep] = "1"
    ms_s[ms_ev < ms_dep] = "2"

    son = pd.DataFrame({
        "Lig": temiz["Lig"], "Tarih": temiz["Tarih"],
        "EvSahibi": temiz["EvSahibi"].astype(str), "Deplasman": temiz["Deplasman"].astype(str),
        "Ac_MS1": temiz["Ac_MS1"].round(2), "Ac_MSX": temiz["Ac_MSX"].round(2), "Ac_MS2": temiz["Ac_MS2"].round(2),
        "Ac_Ust25": temiz["Ac_Ust25"].round(2), "Ac_Alt25": temiz["Ac_Alt25"].round(2),
        "Ac_KgVar": temiz["Ac_KgVar"].round(2), "Ac_KgYok": temiz["Ac_KgYok"].round(2),
        "Ac_IY15Ust": temiz["Ac_IY15Ust"].round(2), "Ac_IY15Alt": temiz["Ac_IY15Alt"].round(2),
        "Ac_IY05Ust": temiz["Ac_IY05Ust"].round(2), "Ac_IY05Alt": temiz["Ac_IY05Alt"].round(2),
        "IYSkor": iy_ev.astype(str) + "-" + iy_dep.astype(str),
        "MSSkor": ms_ev.astype(str) + "-" + ms_dep.astype(str),
        "IyMs": (iy_s + "/" + ms_s).astype("category"),
        "Ms": ms_s.astype("category"),
        "MsKg": ((ms_ev > 0) & (ms_dep > 0)).map({True: "VAR", False: "YOK"}).astype("category"),
        "AU25": ((ms_ev + ms_dep) > 2.5).map({True: "ÜST", False: "ALT"}).astype("category"),
        "IY05": ((iy_ev + iy_dep) > 0.5).map({True: "ÜST", False: "ALT"}).astype("category"),
        "IY15": ((iy_ev + iy_dep) > 1.5).map({True: "ÜST", False: "ALT"}).astype("category")
    })
    del temiz
    gc.collect()
    return son

df_maclar = veriyi_yukle_acilis()
st.caption(f"📊 Açılış Oran Havuzu: {len(df_maclar):,} Maç")

c1, c2, c3 = st.columns(3)
ms1 = c1.number_input("MS 1 Açılış", min_value=0.0, value=1.82, step=0.01, format="%.2f")
msx = c2.number_input("MS X Açılış (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")
ms2 = c3.number_input("MS 2 Açılış", min_value=0.0, value=3.90, step=0.01, format="%.2f")

g1, g2, g3, g4 = st.columns(4)
ust25 = g1.number_input("2.5 Üst (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")
alt25 = g2.number_input("2.5 Alt (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")
kgvar = g3.number_input("KG Var (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")
kgyok = g4.number_input("KG Yok (0=Boş)", min_value=0.0, value=0.00, step=0.01, format="%.2f")

iy1, iy2, iy3, iy4 = st.columns(4)
iy05u = iy1.number_input("İY 0.5 Üst", min_value=0.0, value=0.00, step=0.01, format="%.2f")
iy05a = iy2.number_input("İY 0.5 Alt", min_value=0.0, value=0.00, step=0.01, format="%.2f")
iy15u = iy3.number_input("İY 1.5 Üst", min_value=0.0, value=0.00, step=0.01, format="%.2f")
iy15a = iy4.number_input("İY 1.5 Alt", min_value=0.0, value=0.00, step=0.01, format="%.2f")

f1, f2 = st.columns(2)
tol = f1.number_input("Tolerans (±)", min_value=0.0, value=0.02, step=0.01, format="%.2f")
lig_listesi = ["Tüm Ligler"] + sorted(df_maclar["Lig"].dropna().unique().tolist())
secilen_lig = f2.selectbox("Lig Seçin:", lig_listesi)

filtre = pd.Series(True, index=df_maclar.index)
if ms1 > 0: filtre &= df_maclar["Ac_MS1"].between(ms1 - tol, ms1 + tol)
if msx > 0: filtre &= df_maclar["Ac_MSX"].between(msx - tol, msx + tol)
if ms2 > 0: filtre &= df_maclar["Ac_MS2"].between(ms2 - tol, ms2 + tol)
if ust25 > 0: filtre &= df_maclar["Ac_Ust25"].between(ust25 - tol, ust25 + tol)
if alt25 > 0: filtre &= df_maclar["Ac_Alt25"].between(alt25 - tol, alt25 + tol)
if kgvar > 0: filtre &= df_maclar["Ac_KgVar"].between(kgvar - tol, kgvar + tol)
if kgyok > 0: filtre &= df_maclar["Ac_KgYok"].between(kgyok - tol, kgyok + tol)
if iy05u > 0: filtre &= df_maclar["Ac_IY05Ust"].between(iy05u - tol, iy05u + tol)
if iy05a > 0: filtre &= df_maclar["Ac_IY05Alt"].between(iy05a - tol, iy05a + tol)
if iy15u > 0: filtre &= df_maclar["Ac_IY15Ust"].between(iy15u - tol, iy15u + tol)
if iy15a > 0: filtre &= df_maclar["Ac_IY15Alt"].between(iy15a - tol, iy15a + tol)
if secilen_lig != "Tüm Ligler": filtre &= (df_maclar["Lig"] == secilen_lig)

sonuc = df_maclar[filtre].copy()
toplam = int(len(sonuc))

if toplam > 0:
    m1 = int((sonuc["Ms"] == "1").sum())
    mx = int((sonuc["Ms"] == "X").sum())
    m2 = int((sonuc["Ms"] == "2").sum())
    u25 = int((sonuc["AU25"] == "ÜST").sum())
    a25 = int((sonuc["AU25"] == "ALT").sum())
    kg = int((sonuc["MsKg"] == "VAR").sum())
    kgy = int((sonuc["MsKg"] == "YOK").sum())
    iy05_ust = int((sonuc["IY05"] == "ÜST").sum())
    iy05_alt = toplam - iy05_ust
    iy15_ust = int((sonuc["IY15"] == "ÜST").sum())
    iy15_alt = toplam - iy15_ust

    k1, k2, k3 = st.columns(3)
    k1.markdown(f'<div class="metric-card"><div class="metric-title">MAÇ</div><div class="metric-value">{toplam}</div><div class="metric-sub">Havuz: {len(df_maclar):,}</div></div>', unsafe_allow_html=True)
