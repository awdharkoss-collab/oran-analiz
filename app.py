import streamlit as st
import pandas as pd
import kagglehub
import os
import glob

st.set_page_config(page_title="Futbol Oran İstatistik Pro", page_icon="⚽", layout="centered")

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

st.title("⚽ Futbol Oran İstatistik Pro")

@st.cache_data(show_spinner="2000-2026 arası 600.000+ maçlık dev arşiv derleniyor (İlk açılış ~50 sn)...")
def veriyi_yukle_mega():
    # Kaggle üzerindeki en büyük bahis oranları ve maç arşivleri
    veri_setleri = [
        "adamgbor/club-football-match-data-2000-2025",
        "ahmadasadi00/football-betting-odds",
        "jalalelkhateb/football-odds-and-results-dataset",
        "piterfm/football-matches-dataset",
        "maxhorowitz/nflplaybyplay2009to2016",
        "thedevastator/football-match-results-and-betting-odds",
        "jiezi2004/football-matches-and-betting-odds"
    ]
    
    df_list = []
    for ds in veri_setleri:
        try:
            yol = kagglehub.dataset_download(ds)
            dosyalar = glob.glob(os.path.join(yol, "**/*.csv"), recursive=True)
            for d in dosyalar:
                if os.path.getsize(d) > 15000:
                    try:
                        temp = pd.read_csv(d, low_memory=False)
                        sozluk = {}
                        for hedef, adaylar in {
                            "LigKod": ["Division", "Div", "League", "league", "country", "Country", "tournament"],
                            "Tarih": ["MatchDate", "Date", "date", "match_date"],
                            "EvSahibi": ["HomeTeam", "Home", "home_team", "home", "HT"],
                            "Deplasman": ["AwayTeam", "Away", "away_team", "away", "AT"],
                            "Ac_MS1": ["OddHome", "B365H", "PSH", "WHH", "AvgH", "MaxH", "odd_1", "home_odds", "H"],
                            "Ac_MSX": ["OddDraw", "B365D", "PSD", "WHD", "AvgD", "MaxD", "odd_x", "draw_odds", "D"],
                            "Ac_MS2": ["OddAway", "B365A", "PSA", "WHA", "AvgA", "MaxA", "odd_2", "away_odds", "A"],
                            "Kap_MS1": ["CloseHome", "B365CH", "PSCH", "AvgCH"],
                            "Kap_MSX": ["CloseDraw", "B365CD", "PSCD", "AvgCD"],
                            "Kap_MS2": ["CloseAway", "B365CA", "PSCA", "AvgCA"],
                            "IY_Ev": ["HTHome", "HTHG", "ht_home"],
                            "IY_Dep": ["HTAway", "HTAG", "ht_away"],
                            "MS_Ev": ["FTHome", "FTHG", "home_score", "ft_home", "HG"],
                            "MS_Dep": ["FTAway", "FTAG", "away_score", "ft_away", "AG"]
                        }.items():
                            for a in adaylar:
                                if a in temp.columns:
                                    sozluk[hedef] = temp[a]
                                    break
                        if all(k in sozluk for k in ["EvSahibi", "Deplasman", "Ac_MS1", "MS_Ev", "MS_Dep"]):
                            df_list.append(pd.DataFrame(sozluk))
                    except:
                        pass
        except:
            pass

    temiz = pd.concat(df_list, ignore_index=True)

    # Bellek dostu sayısal dönüşüm (float32)
    for col in ["Ac_MS1", "Ac_MSX", "Ac_MS2", "Kap_MS1", "Kap_MSX", "Kap_MS2", "IY_Ev", "IY_Dep", "MS_Ev", "MS_Dep"]:
        if col not in temiz.columns:
            temiz[col] = pd.NA
        temiz[col] = pd.to_numeric(temiz[col], errors="coerce").astype("float32")

    temiz["Kap_MS1"] = temiz["Kap_MS1"].fillna(temiz["Ac_MS1"])
    temiz["Kap_MSX"] = temiz["Kap_MSX"].fillna(temiz["Ac_MSX"])
    temiz["Kap_MS2"] = temiz["Kap_MS2"].fillna(temiz["Ac_MS2"])
    temiz["LigKod"] = temiz.get("LigKod", pd.Series("Diğer", index=temiz.index)).fillna("Diğer")
    temiz["Tarih"] = pd.to_datetime(temiz.get("Tarih", "-"), errors="coerce", format="mixed").dt.strftime("%Y-%m-%d").fillna("-")

    temiz = temiz.dropna(subset=["MS_Ev", "MS_Dep", "Ac_MS1", "Ac_MS2"])
    temiz = temiz[(temiz["Ac_MS1"] > 1.0) & (temiz["Ac_MS2"] > 1.0)]
    temiz = temiz.drop_duplicates(subset=["Tarih", "EvSahibi", "Deplasman", "Ac_MS1"], keep="last").copy()

    lig_sozlugu = {
        "E0": "İngiltere Premier Lig", "E1": "İngiltere Championship", "E2": "İngiltere League 1", "E3": "İngiltere League 2", "EC": "İngiltere National League",
        "D1": "Almanya Bundesliga 1", "D2": "Almanya Bundesliga 2", "D3": "Almanya 3. Liga",
        "SP1": "İspanya La Liga", "SP2": "İspanya La Liga 2",
        "I1": "İtalya Serie A", "I2": "İtalya Serie B",
        "F1": "Fransa Ligue 1", "F2": "Fransa Ligue 2",
        "T1": "Türkiye Süper Lig", "T2": "Türkiye 1. Lig",
        "N1": "Hollanda Eredivisie", "N2": "Hollanda Eerste Divisie",
        "P1": "Portekiz Premier Lig", "P2": "Portekiz Liga 2",
        "B1": "Belçika Pro League", "B2": "Belçika 2. Lig",
        "SC0": "İskoçya Premiership", "SC1": "İskoçya Championship", "SC2": "İskoçya League One", "SC3": "İskoçya League Two",
        "G1": "Yunanistan Süper Lig", "ARG": "Arjantin Primera", "AUT": "Avusturya Bundesliga",
        "BRA": "Brezilya Serie A", "BRB": "Brezilya Serie B", "CHN": "Çin Süper Ligi",
        "DNK": "Danimarka Superliga", "FIN": "Finlandiya Veikkausliiga", "IRL": "İrlanda Premier",
        "JPN": "Japonya J1 League", "MEX": "Meksika Liga MX", "NOR": "Norveç Eliteserien",
        "POL": "Polonya Ekstraklasa", "ROU": "Romanya Liga 1", "RUS": "Rusya Premier Lig",
        "SWE": "İsveç Allsvenskan", "SWZ": "İsviçre Super League", "USA": "ABD MLS"
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

    return pd.DataFrame({
        "Lig": temiz["Lig"],
        "Tarih": temiz["Tarih"],
        "EvSahibi": temiz["EvSahibi"].astype(str),
        "Deplasman": temiz["Deplasman"].astype(str),
        "Ac_MS1": temiz["Ac_MS1"], "Ac_MSX": temiz["Ac_MSX"], "Ac_MS2": temiz["Ac_MS2"],
        "Kap_MS1": temiz["Kap_MS1"], "Kap_MSX": temiz["Kap_MSX"], "Kap_MS2": temiz["Kap_MS2"],
        "IYSkor": iy_ev.astype(str) + "-" + iy_dep.astype(str),
        "MSSkor": ms_ev.astype(str) + "-" + ms_dep.astype(str),
        "IyMs": (iy_s + "/" + ms_s).astype("category"),
        "Ms": ms_s.astype("category"),
        "MsKg": ((ms_ev > 0) & (ms_dep > 0)).map({True: "VAR", False: "YOK"}).astype("category"),
        "AU25": ((ms_ev + ms_dep) > 2.5).map({True: "ÜST", False: "ALT"}).astype("category"),
        "AU35": ((ms_ev + ms_dep) > 3.5).map({True: "ÜST", False: "ALT"}).astype("category")
    })

df_maclar = veriyi_yukle_mega()
st.caption(f"📊 Aktif Arşiv Kapasitesi: {len(df_maclar):,} Benzersiz Maç (2000 - 2026)")

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
    k1.markdown(f'<div class="metric-card"><div class="metric-title">EŞLEŞEN MAÇ</div><div class="metric-value">{toplam}</div><div class="metric-sub">Havuz: {len(df_maclar):,}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="metric-card"><div class="metric-title">2.5 ÜST</div><div class="metric-value">%{u25/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {u25}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="metric-card"><div class="metric-title">KG VAR</div><div class="metric-value">%{kg/toplam*100:.0f}</div><div class="metric-sub">{toplam} maçta {kg}</div></div>', unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
