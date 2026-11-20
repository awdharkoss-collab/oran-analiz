import streamlit as st
import pandas as pd
import kagglehub
import urllib.request
import io
import os
import glob
import gc
import shutil

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

@st.cache_data(show_spinner="550.000+ maçlık dev arşiv derleniyor (~35 sn)...")
def veriyi_yukle_550k():
    veri_setleri = [
        "adamgbor/club-football-match-data-2000-2025",
        "ahmadasadi00/football-betting-odds",
        "secareanualin/football-events-database",
        "austro/beat-the-bookie-worldwide-football-dataset",
        "jieyingwu/football-matches-dataset"
    ]

    hedef_haritasi = {
        "LigKod": ["Division", "Div", "League", "league", "country", "Country", "competition"],
        "Tarih": ["MatchDate", "Date", "date", "match_date"],
        "EvSahibi": ["HomeTeam", "Home", "home_team", "HT", "home"],
        "Deplasman": ["AwayTeam", "Away", "away_team", "AT", "away"],
        "Ac_MS1": ["OddHome", "B365H", "PSH", "WHH", "AvgH", "MaxH", "odd_1", "H", "home_odds"],
        "Ac_MSX": ["OddDraw", "B365D", "PSD", "WHD", "AvgD", "MaxD", "odd_x", "D", "draw_odds"],
        "Ac_MS2": ["OddAway", "B365A", "PSA", "WHA", "AvgA", "MaxA", "odd_2", "A", "away_odds"],
        "Kap_MS1": ["B365CH", "PSCH", "AvgCH", "MaxCH", "CloseHome"],
        "Kap_MSX": ["B365CD", "PSCD", "AvgCD", "MaxCD", "CloseDraw"],
        "Kap_MS2": ["B365CA", "PSCA", "AvgCA", "MaxCA", "CloseAway"],
        "IY_Ev": ["HTHome", "HTHG", "ht_home"],
        "IY_Dep": ["HTAway", "HTAG", "ht_away"],
        "MS_Ev": ["FTHome", "FTHG", "home_score", "HG", "ft_home"],
        "MS_Dep": ["FTAway", "FTAG", "away_score", "AG", "ft_away"]
    }
    tum_adaylar = set(sum(hedef_haritasi.values(), []))

    parcalar = []
    for ds in veri_setleri:
        try:
            yol = kagglehub.dataset_download(ds)
            dosyalar = glob.glob(os.path.join(yol, "**/*.csv"), recursive=True)
            for d in dosyalar:
                # 150 MB üzeri devasa ham dosyaları atla ki RAM taşmasın
                if 20000 < os.path.getsize(d) < 150000000:
                    try:
                        basliklar = pd.read_csv(d, nrows=0).columns.tolist()
                        okunacak = [c for c in basliklar if c in tum_adaylar]
                        if len(okunacak) < 5:
                            continue
                        temp = pd.read_csv(d, usecols=okunacak, low_memory=False)
                        sozluk = {}
                        for hedef, adaylar in hedef_haritasi.items():
                            for a in adaylar:
                                if a in temp.columns:
                                    sozluk[hedef] = temp[a]
                                    break
                        if all(k in sozluk for k in ["EvSahibi", "Deplasman", "Ac_MS1", "MS_Ev", "MS_Dep"]):
                            parca = pd.DataFrame(sozluk).dropna(subset=["MS_Ev", "MS_Dep", "Ac_MS1"])
                            parcalar.append(parca)
                        del temp
                        gc.collect()
                    except:
                        pass
            shutil.rmtree(yol, ignore_errors=True)
        except:
            pass

    # Güncel Kapanış Oranlı Sezonlar (2019 - 2026)
    ligler = ["E0", "E1", "E2", "E3", "D1", "D2", "SP1", "SP2", "I1", "I2", "F1", "F2", "T1", "N1", "P1", "B1", "SC0", "G1"]
    sezonlar = ["2526", "2425", "2324", "2223", "2122", "2021", "1920"]
    headers = {"User-Agent": "Mozilla/5.0"}
    for sez in sezonlar:
        for lg in ligler:
            url = f"https://football-data.co.uk{sez}/{lg}.csv"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    t_df = pd.read_csv(io.StringIO(resp.read().decode("latin1")), on_bad_lines="skip")
                    sozluk = {}
                    for hedef, adaylar in hedef_haritasi.items():
                        for a in adaylar:
                            if a in t_df.columns:
                                sozluk[hedef] = t_df[a]
                                break
                    if all(k in sozluk for k in ["EvSahibi", "Deplasman", "Ac_MS1", "MS_Ev", "MS_Dep"]):
                        parcalar.append(pd.DataFrame(sozluk))
            except:
                pass

    temiz = pd.concat(parcalar, ignore_index=True)
    del parcalar
    gc.collect()

    for col in ["Ac_MS1", "Ac_MSX", "Ac_MS2", "Kap_MS1", "Kap_MSX", "Kap_MS2", "IY_Ev", "IY_Dep", "MS_Ev", "MS_Dep"]:
        if col not in temiz.columns:
            temiz[col] = pd.NA
        temiz[col] = pd.to_numeric(temiz[col], errors="coerce").astype("float32")

    temiz["LigKod"] = temiz.get("LigKod", pd.Series("Diğer", index=temiz.index)).fillna("Diğer")
    temiz["Tarih"] = temiz.get("Tarih", pd.Series("-", index=temiz.index)).astype(str).str.slice(0, 10)

    temiz = temiz.dropna(subset=["MS_Ev", "MS_Dep", "Ac_MS1", "Ac_MS2"])
    temiz = temiz[(temiz["Ac_MS1"] > 1.0) & (temiz["Ac_MS2"] > 1.0)]
    temiz = temiz.sort_values(by="Kap_MS1", na_position="first")
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

    son = pd.DataFrame({
        "Lig": temiz["Lig"],
        "Tarih": temiz["Tarih"],
        "EvSahibi": temiz["EvSahibi"].astype(str),
        "Deplasman": temiz["Deplasman"].astype(str),
        "Ac_MS1": temiz["Ac_MS1"].round(2), "Ac_MSX": temiz["Ac_MSX"].round(2), "Ac_MS2": temiz["Ac_MS2"].round(2),
        "Kap_MS1": temiz["Kap_MS1"].round(2), "Kap_MSX": temiz["Kap_MSX"].round(2), "Kap_MS2": temiz["Kap_MS2"].round(2),
        "IYSkor": iy_ev.astype(str) + "-" + iy_dep.astype(str),
        "MSSkor": ms_ev.astype(str) + "-" + ms_dep.astype(str),
        "IyMs": (iy_s + "/" + ms_s).astype("category"),
        "Ms": ms_s.astype("category"),
        "MsKg": ((ms_ev > 0) & (ms_dep > 0)).map({True: "VAR", False: "YOK"}).astype("category"),
        "AU25": ((ms_ev + ms_dep) > 2.5).map({True: "ÜST", False: "ALT"}).astype("category"),
        "AU35": ((ms_ev + ms_dep) > 3.5).map({True: "ÜST", False: "ALT"}).astype("category")
    })
    del temiz
    gc.collect()
    return son

df_maclar = veriyi_yukle_550k()
kapanis_sayisi = df_maclar["Kap_MS1"].notna().sum()
st.caption(f"📊 Açılış Havuzu: {len(df_maclar):,} Maç | Kapanış Havuzu: {kapanis_sayisi:,} Maç")

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
