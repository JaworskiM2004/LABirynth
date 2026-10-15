# -*- coding: utf-8 -*-
"""
WIĘZIEŃ LABIRYNTU — nieskończone lochy
======================================
Samodzielna gra (roguelite w stylu Brotato + augmenty jak na Arenie w LoL-u).
Cała gra to jeden plik HTML/JS osadzony niżej w stałej GRA_HTML — Streamlit
jest tylko "hostem": rozciąga ją na cały ekran telefonu.

Uruchomienie lokalnie:   pip install streamlit   →   streamlit run app.py
Na Streamlit Cloud:      repozytorium z tym plikiem i requirements.txt

Zapis gry, rekordy i ustawienia trzymane są w przeglądarce (localStorage).

Gra online (do 4 osób w drużynie): połączenie bezpośrednie między przeglądarkami
(WebRTC przez bibliotekę PeerJS, wczytywaną z CDN dopiero po wejściu w tryb online).
Gospodarz liczy całą walkę, pozostali wysyłają tylko swój ruch. Serwer nie jest
potrzebny — wystarczy, że wszyscy otworzą tę samą aplikację i wpiszą kod drużyny
(albo wejdą w link z ?pokoj=KOD).
"""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Więzień Labiryntu",
    page_icon="⛓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Gra ma zajmować cały ekran: chowamy elementy Streamlita, zerujemy marginesy,
# a ramkę z grą rozciągamy na całe okno (gra sama też to robi od środka).
st.markdown(
    """
<style>
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#0b0910 !important; }
  header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], [data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }
  .block-container, [data-testid="stMainBlockContainer"] { padding:0 !important; margin:0 !important; max-width:100% !important; }
  [data-testid="stVerticalBlock"] { gap:0 !important; }
  iframe { position:fixed !important; top:0 !important; left:0 !important; width:100vw !important;
           height:100vh !important; height:100dvh !important; border:0 !important; z-index:999990 !important; }
</style>
<meta name="theme-color" content="#0b0910">
""",
    unsafe_allow_html=True,
)

GRA_HTML = r'''<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="theme-color" content="#0b0910">
<meta name="color-scheme" content="dark">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>Więzień Labiryntu</title>
<style>
  :root {
    --zloto:#e6c15c; --zloto2:#d4af37; --panel:rgba(20,16,28,0.98); --tekst:#f0e8d0; --szary:#a89878;
    --t0:#b8b8b8; --t1:#5aa8e6; --t2:#b06ce8; --t3:#e6b53c; --t4:#ff5a4a;
    --fiz:#f5a25a; --mag:#86b8ff; --praw:#ffffff; --hp:#e74c3c; --dobre:#7ec98a; --zle:#e6543c;
    --wysPaska:168px;
  }
  * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; outline:none;
      -webkit-user-select:none; user-select:none; -webkit-touch-callout:none; }
  html, body { width:100%; height:100%; overflow:hidden; background:#0b0910; color:var(--tekst);
      font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; touch-action:none; overscroll-behavior:none; }
  button { font-family:inherit; color:inherit; cursor:pointer; }
  input, textarea { font-family:inherit; -webkit-user-select:text; user-select:text; }
  textarea.pole { resize:none; letter-spacing:0; font-weight:600; }
  .pole { width:100%; padding:12px 12px; border-radius:12px; border:1.5px solid rgba(230,193,92,0.45); background:rgba(0,0,0,0.35);
      color:#f0e8d0; font-size:17px; font-weight:800; text-align:center; letter-spacing:0.06em; }
  .kod { font-size:44px; font-weight:900; letter-spacing:0.18em; color:#ffe08a; text-align:center; text-shadow:0 2px 14px rgba(230,193,92,0.35); }
  .gracz-lobby { display:flex; align-items:center; gap:10px; padding:9px 11px; border-radius:12px; background:rgba(255,255,255,0.05); margin-bottom:6px; }
  .gracz-lobby .ik { font-size:24px; } .gracz-lobby .n { flex:1; font-weight:800; font-size:14px; } .gracz-lobby .s { font-size:12px; font-weight:800; }
  .mini-klasy { display:grid; grid-template-columns:repeat(6,1fr); gap:5px; }
  .mini-klasy .kafel { padding:6px 2px; } .mini-klasy .kafel .ik { font-size:22px; }
  #gra { position:relative; width:100%; max-width:560px; height:100%; margin:0 auto; overflow:hidden; background:#0a0810; }
  #widok { position:absolute; left:0; top:0; width:100%; display:block; background:#0a0810; }

  /* ---------- HUD ---------- */
  #hud { position:absolute; top:0; left:0; right:0; padding:6px 8px 0; z-index:5; pointer-events:none; }
  .hud-rzad { display:flex; align-items:center; gap:6px; }
  .pasek { position:relative; height:15px; flex:1; background:rgba(0,0,0,0.6); border:1px solid rgba(255,255,255,0.25);
           border-radius:7px; overflow:hidden; }
  .pasek .wyp { position:absolute; left:0; top:0; bottom:0; transition:width .15s ease; }
  #hpWyp { background:linear-gradient(90deg,#b8302a,#e74c3c); }
  #tarczaWyp { background:linear-gradient(90deg,rgba(255,255,255,0.85),rgba(220,230,255,0.75)); }
  #xpWyp { background:linear-gradient(90deg,#3f9a52,#7ee87a); }
  .pasek .napis { position:absolute; inset:0; display:flex; align-items:center; padding-left:6px; font-size:9.5px; font-weight:800;
           color:#fff; text-shadow:0 1px 2px #000,0 0 3px #000; white-space:nowrap; }
  #xpPasek { height:9px; margin-top:3px; }
  #xpPasek .napis { font-size:8px; }
  #falaInfo { flex:0 0 auto; background:rgba(10,8,16,0.82); border:1px solid rgba(230,193,92,0.5); border-radius:10px;
           padding:3px 8px; font-size:12px; font-weight:900; color:#ffe08a; text-align:center; min-width:86px; line-height:1.15; }
  #falaInfo small { display:block; font-size:9px; color:#d8cdb0; font-weight:700; }
  #zlotoInfo { flex:0 0 auto; background:rgba(10,8,16,0.82); border:1px solid rgba(230,193,92,0.35); border-radius:10px;
           padding:3px 8px; font-size:13px; font-weight:900; color:#ffd24a; min-width:58px; text-align:center; }
  #pasekPrzedm { display:flex; gap:4px; margin-top:5px; flex-wrap:wrap; }
  .hud-slot { position:relative; width:27px; height:27px; border-radius:7px; background:rgba(10,8,16,0.8);
           border:1.5px solid var(--t0); display:flex; align-items:center; justify-content:center; font-size:15px; overflow:hidden; }
  .hud-slot .cd { position:absolute; inset:0; background:conic-gradient(rgba(0,0,0,0.72) var(--p,0%), transparent 0); }
  .hud-slot .cdn { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:900;
           color:#fff; text-shadow:0 1px 2px #000; }
  .hud-slot .st { position:absolute; right:1px; bottom:0; font-size:8px; font-weight:900; color:#ffe08a; text-shadow:0 1px 2px #000; }
  .hud-slot.gotowy { box-shadow:0 0 6px rgba(255,224,138,0.8); }

  #dziennik { position:absolute; left:8px; right:8px; top:96px; z-index:5; pointer-events:none; }
  .wpis { font-size:11px; font-weight:700; color:#f0e8d0; text-shadow:0 1px 3px #000; margin-bottom:2px; opacity:0;
          animation:wpis 2.8s ease forwards; }
  @keyframes wpis { 0%{opacity:0;transform:translateY(-4px)} 10%{opacity:1;transform:none} 80%{opacity:1} 100%{opacity:0} }
  #baner { position:absolute; left:0; right:0; top:28%; z-index:6; text-align:center; pointer-events:none; opacity:0;
           transition:opacity .5s; color:#ffe08a; font-weight:900; font-size:26px; text-shadow:0 2px 12px #000,0 0 4px #000; padding:0 14px; }
  #baner small { display:block; font-size:13px; color:#f0e8d0; font-weight:700; margin-top:4px; }

  /* ---------- PAS STEROWANIA ---------- */
  #pasSterowania { position:absolute; left:0; right:0; bottom:0; height:var(--wysPaska); z-index:7;
      background:linear-gradient(180deg,#1a1520,#0e0c14); border-top:2px solid #4a3a2e;
      display:flex; align-items:center; justify-content:space-between; padding:0 14px; touch-action:none; }
  .btn-boczny { position:relative; width:62px; height:62px; border-radius:16px; border:1.5px solid #5a4a2e;
      background:linear-gradient(135deg,#3a3550,#262038); font-size:26px; box-shadow:0 3px 10px rgba(0,0,0,0.45); padding:0; }
  .btn-boczny:active, .btn-boczny.wcisniety { transform:scale(0.94); }
  .kolumna-btn { display:flex; flex-direction:column; gap:9px; }
  .btn-boczny.maly { width:50px; height:50px; border-radius:14px; font-size:22px; }
  .btn-boczny.maly .cdm { border-radius:13px; }
  #btnUmi { width:76px; height:76px; border-radius:22px; font-size:34px; border:2px solid #8a7a4e; background:linear-gradient(135deg,#4a3a6a,#2a2040); }
  #btnUmi .cdm { border-radius:20px; }
  #btnUmi .czas { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:900; color:#fff; text-shadow:0 2px 4px #000; }
  #btnUmi.gotowa { border-color:#ffe08a; box-shadow:0 0 16px rgba(255,224,138,0.55), 0 3px 10px rgba(0,0,0,0.45); animation:umiPuls 1.6s ease-in-out infinite; }
  #btnUmi2 { width:58px; height:58px; border-radius:17px; font-size:26px; border:2px solid #6a7a8e; background:linear-gradient(135deg,#3a4a6a,#20283e); }
  #btnUmi2 .cdm { border-radius:15px; }
  #btnUmi2 .czas { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:18px; font-weight:900; color:#fff; text-shadow:0 2px 4px #000; }
  #btnUmi2.gotowa { border-color:#9fd8ff; box-shadow:0 0 12px rgba(159,216,255,0.5); }
  .btn-boczny.wlaczona { border-color:#7ee87a !important; box-shadow:0 0 16px rgba(126,232,122,0.7) !important; background:linear-gradient(135deg,#2e5a3a,#163a22) !important; }
  #gra.pc #btnUmi2 { width:48px; height:48px; font-size:22px; border-radius:14px; }
  #gra.pc.dotyk #btnUmi2 { width:64px; height:64px; font-size:28px; border-radius:18px; }
  #gra.tryb-pad #btnUmi2 { width:44px; height:44px; font-size:20px; }
  @keyframes umiPuls { 0%,100%{box-shadow:0 0 10px rgba(255,224,138,0.4)} 50%{box-shadow:0 0 22px rgba(255,224,138,0.8)} }
  .btn-boczny .licznik { position:absolute; right:-5px; bottom:-5px; background:#3f8a52; color:#fff; border-radius:9px;
      padding:1px 6px; font-size:11px; font-weight:800; }
  .btn-boczny .cdm { position:absolute; inset:0; border-radius:15px; background:conic-gradient(rgba(0,0,0,0.65) var(--p,0%), transparent 0); }
  #strefaDrazka { position:relative; width:146px; height:146px; touch-action:none; }
  #drazekBaza { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:122px; height:122px; border-radius:50%;
      background:radial-gradient(circle at 40% 35%, rgba(255,255,255,0.07), rgba(0,0,0,0.35)); border:2px solid rgba(230,193,92,0.35); }
  #drazekGalka { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:54px; height:54px; border-radius:50%;
      background:radial-gradient(circle at 38% 32%, #f0dfa8, #d4af37 60%, #8a6a1e); box-shadow:0 3px 10px rgba(0,0,0,0.5); }

  /* ---------- EKRANY (nakladki) ---------- */
  #ekran { position:absolute; inset:0; z-index:30; display:none; overflow-y:auto; -webkit-overflow-scrolling:touch;
      background:radial-gradient(ellipse at 50% 0%, rgba(60,40,90,0.35), transparent 60%), rgba(9,7,13,0.97);
      padding:14px 12px 30px; touch-action:pan-y; }
  #ekran.widoczny { display:block; }
  #ekran.polprzezroczysty { background:rgba(9,7,13,0.86); }
  .tytul { text-align:center; font-size:23px; font-weight:900; color:var(--zloto); letter-spacing:0.02em; margin:4px 0 4px;
      text-shadow:0 2px 10px rgba(0,0,0,0.6); }
  .tytul.duzy { font-size:34px; margin-top:22px; }
  .podtytul { text-align:center; font-size:12.5px; color:#d8cdb0; margin-bottom:12px; line-height:1.5; }
  .sekcja { color:var(--szary); font-size:10.5px; text-transform:uppercase; letter-spacing:0.08em; font-weight:800; margin:14px 2px 6px; }
  .btn { display:block; width:100%; border:none; border-radius:14px; padding:13px 12px; font-weight:900; font-size:15px;
      background:linear-gradient(135deg,#e6c15c,#d4af37); color:#16130a; box-shadow:0 3px 12px rgba(0,0,0,0.45); margin:8px 0; }
  .btn:active { transform:scale(0.98); }
  .btn:disabled { opacity:0.35; }
  .btn.drugi { background:linear-gradient(135deg,#3a3550,#262038); color:var(--tekst); border:1px solid #5a4a2e; }
  .btn.czerw { background:linear-gradient(135deg,#a8402e,#6e2418); color:#fff; }
  .btn.ziel { background:linear-gradient(135deg,#7ec98a,#3f8a52); color:#0d1a0d; }
  .btn-maly { border:1px solid rgba(255,255,255,0.18); background:rgba(255,255,255,0.07); color:var(--tekst); border-radius:10px;
      padding:7px 9px; font-size:12px; font-weight:800; }
  .btn-maly:disabled { opacity:0.3; }
  .btn-maly.zl { background:linear-gradient(135deg,#e6c15c,#d4af37); color:#16130a; border:none; }
  .btn-maly.ziel { background:linear-gradient(135deg,#7ec98a,#3f8a52); color:#0d1a0d; border:none; }
  .btn-maly.czerw { background:rgba(200,70,50,0.25); border-color:rgba(230,84,60,0.6); }
  .rzad-btn { display:flex; gap:8px; }
  .rzad-btn > * { flex:1; }

  .karta { position:relative; background:linear-gradient(180deg,rgba(40,33,52,0.96),rgba(22,18,30,0.98)); border:2px solid var(--t0);
      border-radius:14px; padding:10px 11px; margin-bottom:9px; box-shadow:0 3px 10px rgba(0,0,0,0.35); }
  .karta.wybieralna:active { transform:scale(0.985); }
  .karta.t0 { border-color:var(--t0); }
  .karta.t1 { border-color:var(--t1); box-shadow:0 0 10px rgba(90,168,230,0.25); }
  .karta.t2 { border-color:var(--t2); box-shadow:0 0 12px rgba(176,108,232,0.3); }
  .karta.t3 { border-color:var(--t3); box-shadow:0 0 14px rgba(230,181,60,0.35); }
  .karta.t4 { border-color:var(--t4); box-shadow:0 0 16px rgba(255,90,74,0.45); }
  .karta.glowna { background:linear-gradient(180deg,rgba(58,42,30,0.97),rgba(26,19,16,0.98)); }
  .karta.tp, .karta.ap { border:2px solid transparent;
      background:linear-gradient(180deg,rgba(40,33,52,0.98),rgba(22,18,30,0.99)) padding-box,
                 linear-gradient(120deg,#ff7ae0,#7ae0ff,#ffe07a,#9aff7a,#ff7ae0) border-box;
      background-size:100% 100%, 300% 300%; animation:pryzmat 5s linear infinite; box-shadow:0 0 16px rgba(255,122,224,0.3); }
  @keyframes pryzmat { 0%{background-position:0 0, 0% 50%} 100%{background-position:0 0, 300% 50%} }
  .karta.as { border-color:#a8adb8; box-shadow:0 0 8px rgba(168,173,184,0.2); }
  .karta.az { border-color:#e6c15c; box-shadow:0 0 14px rgba(230,193,92,0.35); }
  .karta.wybrana { outline:3px solid #fff; }
  .karta-gora { display:flex; align-items:center; gap:10px; }
  .karta-ik { flex:0 0 auto; width:44px; height:44px; border-radius:11px; background:rgba(0,0,0,0.35); display:flex;
      align-items:center; justify-content:center; font-size:26px; position:relative; }
  .karta-ik .gw { position:absolute; bottom:-4px; left:50%; transform:translateX(-50%); font-size:9px; color:#ffe08a; white-space:nowrap; text-shadow:0 1px 2px #000; }
  .karta-nazwa { font-size:14.5px; font-weight:900; line-height:1.2; }
  .karta-tier { font-size:10.5px; font-weight:800; opacity:0.9; margin-top:1px; }
  .karta-staty { margin-top:7px; font-size:12px; color:#e8dcc0; line-height:1.55; }
  .karta-staty b { color:#ffe08a; }
  .karta-opis { margin-top:6px; font-size:12px; color:#d8cdb0; line-height:1.5; }
  .karta-opis b { color:#fff; }
  .karta-dol { display:flex; gap:7px; margin-top:9px; align-items:center; }
  .karta-dol .cena { font-weight:900; color:#ffd24a; font-size:14px; margin-right:auto; }
  /* ---------- SKLEP: karty ofert tej samej wielkości, komputer w dwóch kolumnach, telefon w zakładkach ---------- */
  .sp-oferty { display:grid; gap:8px; }
  .sklep-tel .sp-oferty { grid-auto-rows:1fr; gap:10px; }
  .sklep-pc .sp-oferty { grid-auto-rows:var(--hOf, 150px); }
  .oferta-pusta { border:2px dashed rgba(255,255,255,0.14); border-radius:14px; display:flex; align-items:center; justify-content:center; color:#6a6070; font-weight:800; font-size:13px; min-height:64px; }
  .karta.oferta { margin:0; display:grid; grid-template-columns:minmax(0,1fr); grid-template-rows:auto minmax(0,1fr) auto; grid-template-areas:"gora" "srodek" "dol"; overflow:hidden; min-height:0; }
  .karta.oferta > .karta-gora { grid-area:gora; }
  .karta.oferta > .karta-srodek { grid-area:srodek; overflow:hidden; min-height:0; cursor:pointer; }
  .sklep-tel .karta.oferta > .karta-srodek { max-height:6.1em; }
  .karta.oferta > .karta-dol { grid-area:dol; }
  .karta-srodek.ucieta { -webkit-mask-image:linear-gradient(180deg,#000 calc(100% - 20px),transparent); mask-image:linear-gradient(180deg,#000 calc(100% - 20px),transparent); }
  .karta.oferta .tagi { display:none; }
  .karta.oferta.zablok { box-shadow:0 0 0 2px rgba(255,224,138,0.6), 0 0 14px rgba(255,224,138,0.25); }
  .of-btn { display:flex; gap:6px; align-items:center; }
  .btn-maly.info { padding-left:7px; padding-right:7px; }
  .tag.tag-ok { background:rgba(126,201,138,0.2); color:#7ec98a; }
  .onhit { display:inline-block; font-size:0.78em; font-weight:900; text-transform:uppercase; letter-spacing:0.04em; padding:0 5px; border-radius:5px; line-height:1.35;
    background:rgba(255,138,60,0.18); color:#ffb07a; border:1px solid rgba(255,138,60,0.45); vertical-align:0.06em; margin-right:2px; white-space:nowrap; }
  .sklep-pc .karta.oferta { grid-template-columns:minmax(0,1fr) auto; grid-template-rows:auto minmax(0,1fr); grid-template-areas:"gora dol" "srodek dol"; column-gap:12px; padding:9px 12px; }
  .sklep-pc .karta.oferta > .karta-dol { flex-direction:column; align-items:flex-end; justify-content:center; margin:0; gap:7px; border-left:1px solid rgba(255,255,255,0.08); padding-left:12px; }
  .sklep-pc .karta.oferta .karta-dol .cena { margin:0; font-size:16px; }
  .sklep-pc .karta.oferta .karta-ik { width:40px; height:40px; font-size:23px; }
  .sklep-pc .karta.oferta .karta-staty, .sklep-pc .karta.oferta .karta-opis { font-size:11.5px; line-height:1.42; margin-top:3px; }
  #gra.pc .ekran-tresc.sklep-pc { max-width:1560px; }
  .sp-gora { display:flex; align-items:center; gap:14px; margin-bottom:8px; }
  .sp-tytul { font-size:21px; font-weight:900; color:var(--zloto); white-space:nowrap; display:flex; align-items:baseline; gap:8px; }
  .sp-tytul small { font-size:13px; color:#d8cdb0; font-weight:700; }
  .btn.sp-fala { flex:1 1 auto; width:auto; max-width:460px; margin:0 auto; padding:10px 16px; }
  .sp-gora-btn { display:flex; gap:6px; flex:0 0 auto; }
  .sp-uklad { display:grid; grid-template-columns:78px minmax(0,1.08fr) minmax(380px,0.92fr); gap:14px; align-items:start; }
  .sp-aug { display:flex; flex-direction:column; gap:7px; padding:8px 5px; border-radius:14px; background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.08); }
  .sp-aug-tyt { text-align:center; font-size:19px; line-height:1.1; } .sp-aug-tyt b { display:block; font-size:10.5px; color:#d8cdb0; }
  .sp-aug-pusto { text-align:center; font-size:10.5px; color:#6a6070; padding:6px 0; }
  .kfl.kfl-maly { padding:7px 2px 6px; flex-shrink:0; } .kfl.kfl-maly .kfl-ik { width:36px; height:36px; font-size:21px; } .kfl.kfl-maly .kfl-n { font-size:9.5px; }
  .kfl.kfl-maly .kfl-ik::after { width:14px; height:14px; right:-5px; bottom:-5px; }
  .sklep-pc .sekcja { margin:9px 2px 5px; }
  .sklep-pc .sp-build > .chipy:first-child { margin-top:0; }
  .sp-bron-ewo { display:grid; grid-template-columns:1fr; gap:8px; margin-bottom:4px; }
  .sklep-pc .sp-bron-ewo { grid-template-columns:minmax(0,1.3fr) minmax(0,1fr); align-items:stretch; }
  .sp-bron-ewo .kfl.szeroki { margin:0; height:100%; box-sizing:border-box; }
  .sp-bron-ewo .akcja-sklepu.ewo { margin:0; min-height:62px; height:100%; }
  .akcja-sklepu.ewo.gotowa { animation:pulsEwo 1.8s ease-in-out infinite; }
  @keyframes pulsEwo { 0%,100% { box-shadow:0 0 12px rgba(201,168,255,0.3); } 50% { box-shadow:0 0 22px rgba(201,168,255,0.75); } }
  .sklep-pc .sklep-akcje { margin:4px 0 8px; } .sklep-pc .akcja-sklepu { min-height:48px; padding:6px 10px; } .sklep-pc .akcja-sklepu .as-ik { width:26px; height:26px; }
  .sp-oferty.ciasno .karta.oferta { padding:6px 10px; } .sp-oferty.ciasno .karta-ik { width:34px !important; height:34px !important; font-size:20px !important; }
  .sp-oferty.ciasno .karta-nazwa { font-size:13px; } .sp-oferty.ciasno .karta-staty, .sp-oferty.ciasno .karta-opis { font-size:11px !important; line-height:1.35 !important; }
  .sklep-tel .karta.oferta { padding:9px 10px; } .sklep-tel .karta.oferta .karta-staty, .sklep-tel .karta.oferta .karta-opis { font-size:12px; line-height:1.42; margin-top:4px; }
  .sklep-tel .karta.oferta > .karta-dol { margin-top:6px; }
  .sp-zak { margin:10px 0 10px; }
  .sp-tel-tytul { text-align:center; font-size:20px; font-weight:900; color:var(--zloto); margin:0 0 8px; }
  .sp-tel-tytul small { font-size:13px; font-weight:700; color:#d8cdb0; margin-left:4px; }
  #gra.pc .ekran-tresc.sklep-tel { max-width:1100px; }
  #gra.pc .sp-tel-naglowek { display:flex; align-items:center; gap:14px; margin-bottom:8px; } #gra.pc .sp-tel-naglowek .sp-tel-tytul { margin:0; white-space:nowrap; } #gra.pc .sp-tel-naglowek .btn { flex:1; padding:9px 12px; }
  #gra.pc .sp-tel-pasek { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.3fr); gap:10px; align-items:center; margin-bottom:8px; }
  #gra.pc .sp-tel-pasek > * { margin:0; } #gra.pc .sklep-tel .akcja-sklepu { min-height:46px; padding:6px 10px; } #gra.pc .sklep-tel .akcja-sklepu .as-ik { width:24px; height:24px; }
  #gra.pc .sklep-tel .sp-oferty { grid-template-columns:1fr 1fr; }
  #gra.pc .sklep-tel .sp-bron-ewo { grid-template-columns:minmax(0,1.3fr) minmax(0,1fr); }
  .licznik-ul { display:inline-block; background:#7ec98a; color:#0d1a0d; border-radius:8px; padding:0 6px; font-size:11px; font-weight:900; margin-left:3px; line-height:1.5; }
  .kol-t0 { color:var(--t0); } .kol-t1 { color:var(--t1); } .kol-t2 { color:var(--t2); } .kol-t3 { color:var(--t3); } .kol-t4 { color:var(--t4); }
  .kol-p { background:linear-gradient(90deg,#ff7ae0,#7ae0ff,#ffe07a); -webkit-background-clip:text; background-clip:text; color:transparent; }
  /* odznaki tierów (kamienie) - obrazki wstawiane przez przygotujOdznaki() */
  .kol-t0::before, .kol-t1::before, .kol-t2::before, .kol-t3::before, .kol-t4::before, .kol-p::before, .gem-as::before, .gem-az::before, .gem-ap::before {
    content:''; display:inline-block; width:max(1.3em, 15px); height:max(1.3em, 15px); margin:-0.3em 0.15em -0.3em -0.05em; vertical-align:-0.32em; background-position:center; background-size:contain; background-repeat:no-repeat; }
  .kol-t0::before { background-image:var(--gem-t0); } .kol-t1::before { background-image:var(--gem-t1); } .kol-t2::before { background-image:var(--gem-t2); }
  .kol-t3::before { background-image:var(--gem-t3); } .kol-t4::before { background-image:var(--gem-t4); } .kol-p::before { background-image:var(--gem-p); }
  .gem-as::before { background-image:var(--gem-as); } .gem-az::before { background-image:var(--gem-az); } .gem-ap::before { background-image:var(--gem-ap); }
  .karta-ik::after { content:''; position:absolute; right:-7px; top:-7px; width:21px; height:21px; background-position:center; background-size:contain; background-repeat:no-repeat; pointer-events:none; }
  .karta.t0 .karta-ik::after { background-image:var(--gem-t0); } .karta.t1 .karta-ik::after { background-image:var(--gem-t1); } .karta.t2 .karta-ik::after { background-image:var(--gem-t2); }
  .karta.t3 .karta-ik::after { background-image:var(--gem-t3); } .karta.t4 .karta-ik::after { background-image:var(--gem-t4); } .karta.tp .karta-ik::after { background-image:var(--gem-p); }
  .karta.as .karta-ik::after { background-image:var(--gem-as); } .karta.az .karta-ik::after { background-image:var(--gem-az); } .karta.ap .karta-ik::after { background-image:var(--gem-ap); }
  .karta.t1 .karta-ik { background:radial-gradient(circle at 50% 40%, rgba(90,168,230,0.3), rgba(0,0,0,0.35) 72%); box-shadow:inset 0 0 0 1px rgba(90,168,230,0.4); }
  .karta.t2 .karta-ik { background:radial-gradient(circle at 50% 40%, rgba(176,108,232,0.34), rgba(0,0,0,0.35) 72%); box-shadow:inset 0 0 0 1px rgba(176,108,232,0.45); }
  .karta.t3 .karta-ik, .karta.az .karta-ik { background:radial-gradient(circle at 50% 40%, rgba(230,181,60,0.36), rgba(0,0,0,0.35) 72%); box-shadow:inset 0 0 0 1px rgba(230,181,60,0.5); }
  .karta.t4 .karta-ik { background:radial-gradient(circle at 50% 40%, rgba(255,90,74,0.4), rgba(0,0,0,0.35) 72%); box-shadow:inset 0 0 0 1px rgba(255,90,74,0.55); }
  .karta.tp .karta-ik, .karta.ap .karta-ik { background:radial-gradient(circle at 50% 40%, rgba(255,122,224,0.32), rgba(122,224,255,0.12) 55%, rgba(0,0,0,0.35) 75%); box-shadow:inset 0 0 0 1px rgba(255,160,240,0.5); }
  .hud-slot::after { content:''; position:absolute; right:0; top:0; width:10px; height:10px; background-position:center; background-size:contain; background-repeat:no-repeat; pointer-events:none; }
  .hud-slot.t1::after { background-image:var(--gem-t1); } .hud-slot.t2::after { background-image:var(--gem-t2); } .hud-slot.t3::after { background-image:var(--gem-t3); }
  .hud-slot.t4::after { background-image:var(--gem-t4); } .hud-slot.tp::after { background-image:var(--gem-p); }
  .hud-slot .ik { position:relative; line-height:1; }
  .kfl .kfl-ik::after { content:''; position:absolute; right:-6px; bottom:-6px; width:17px; height:17px; background-position:center; background-size:contain; background-repeat:no-repeat; pointer-events:none; }
  .kfl.g-t0 .kfl-ik::after { background-image:var(--gem-t0); } .kfl.g-t1 .kfl-ik::after { background-image:var(--gem-t1); } .kfl.g-t2 .kfl-ik::after { background-image:var(--gem-t2); }
  .kfl.g-t3 .kfl-ik::after { background-image:var(--gem-t3); } .kfl.g-t4 .kfl-ik::after { background-image:var(--gem-t4); } .kfl.g-p .kfl-ik::after { background-image:var(--gem-p); }
  .kfl.g-as .kfl-ik::after { background-image:var(--gem-as); } .kfl.g-az .kfl-ik::after { background-image:var(--gem-az); } .kfl.g-ap .kfl-ik::after { background-image:var(--gem-ap); }
  img.emo { width:1.22em; height:1.22em; margin:-0.11em 0.02em; vertical-align:-0.3em; display:inline-block; object-fit:contain; }
  img.odznaka { width:1.3em; height:1.3em; vertical-align:-0.3em; }
  .fiz { color:var(--fiz); font-weight:800; } .mag { color:var(--mag); font-weight:800; } .praw { color:var(--praw); font-weight:900; }
  .zl { color:#ffd24a; font-weight:800; } .ziel { color:var(--dobre); font-weight:800; } .czer { color:var(--zle); font-weight:800; }
  .cd-tag { display:inline-block; font-size:10px; font-weight:900; padding:1px 6px; border-radius:6px; background:rgba(126,196,255,0.16);
      color:#9fd0ff; margin-left:4px; }
  .tag { display:inline-block; font-size:9.5px; font-weight:800; padding:1px 6px; border-radius:6px; background:rgba(255,255,255,0.08);
      color:#d8cdb0; margin:2px 3px 0 0; }

  .siatka2 { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  .siatka3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; }
  .siatka3 .kafel { padding:8px 4px; } .siatka3 .kafel .ik { font-size:26px; } .siatka3 .kafel .n { font-size:11.5px; line-height:1.2; } .siatka3 .kafel .o { font-size:13px; }
  .kafel { background:linear-gradient(180deg,rgba(40,33,52,0.96),rgba(22,18,30,0.98)); border:2px solid rgba(255,255,255,0.15);
      border-radius:13px; padding:10px 8px; text-align:center; }
  .kafel.wybrany { border-color:#ffe08a; box-shadow:0 0 14px rgba(255,224,138,0.4); }
  .kafel .ik { font-size:30px; }
  .port { position:relative; margin:0 auto; border-radius:50%; flex:0 0 auto; display:flex; align-items:center; justify-content:center;
    background:radial-gradient(circle at 50% 46%, color-mix(in srgb, var(--kp) 55%, transparent) 0%, color-mix(in srgb, var(--kp) 18%, transparent) 48%, transparent 70%); }
  @supports not (background:color-mix(in srgb, red 50%, blue)) { .port { background:radial-gradient(circle at 50% 46%, rgba(255,224,138,0.22), transparent 70%); } }
  .port img.p { width:100%; height:100%; display:block; filter:drop-shadow(0 2px 2px rgba(0,0,0,0.5)); }
  .port .ikk { position:absolute; left:-3px; top:-3px; font-size:15px; filter:drop-shadow(0 1px 1px rgba(0,0,0,0.8)); }
  .mini-klasy .port .ikk { font-size:11px; left:-4px; top:-4px; }
  .kafel .n { font-size:13px; font-weight:900; margin-top:2px; }
  .kafel .o { font-size:10.5px; color:#cfc4a8; margin-top:3px; line-height:1.35; }

  .wiersz-stat { display:flex; align-items:center; gap:8px; padding:6px 8px; background:rgba(255,255,255,0.045); border-radius:9px; margin-bottom:4px; }
  .wiersz-stat .ik { width:22px; text-align:center; font-size:15px; }
  .wiersz-stat .n { flex:1; font-size:12.5px; font-weight:700; }
  .wiersz-stat .v { font-size:14px; font-weight:900; color:#ffe08a; }
  .wiersz-stat .v.zero { color:#6a6070; }
  .gornypasek { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:8px; }
  .zloto-duze { font-size:18px; font-weight:900; color:#ffd24a; }
  .zakladki { display:flex; gap:6px; margin:8px 0 10px; }
  .zakladki button { flex:1; padding:9px 4px; border-radius:10px; border:1px solid #5a4a2e; background:linear-gradient(135deg,#3a3550,#262038);
      font-size:12px; font-weight:800; }
  .zakladki button.akt { background:linear-gradient(135deg,#e6c15c,#d4af37); color:#16130a; }
  .slot-pusty { border:2px dashed rgba(255,255,255,0.14); border-radius:12px; padding:12px; text-align:center; color:#6a6070;
      font-size:12px; margin-bottom:8px; }
  .lista-mini { display:flex; flex-wrap:wrap; gap:6px; }
  .mini { width:44px; height:44px; border-radius:10px; border:2px solid var(--t0); background:rgba(0,0,0,0.35); display:flex;
      align-items:center; justify-content:center; font-size:22px; position:relative; }
  .mini .gw { position:absolute; bottom:-3px; right:1px; font-size:8px; color:#ffe08a; }
  .info-pole { background:rgba(255,255,255,0.05); border:1px solid rgba(230,193,92,0.25); border-radius:12px; padding:10px 12px;
      font-size:12px; line-height:1.6; color:#d8cdb0; margin:8px 0; }
  .info-pole b { color:#ffe08a; }
  .pas-zysk { display:flex; justify-content:space-between; font-size:13px; padding:3px 0; }
  .pas-zysk b { color:#ffe08a; }
  #toast { position:absolute; left:50%; bottom:calc(var(--wysPaska) + 14px); transform:translateX(-50%); z-index:60; background:rgba(14,11,20,0.96);
      border:1px solid rgba(230,193,92,0.5); border-radius:12px; padding:8px 14px; font-size:12.5px; font-weight:800; color:#ffe08a;
      pointer-events:none; opacity:0; transition:opacity .25s; max-width:90%; text-align:center; }
  #modal { position:absolute; inset:0; z-index:50; display:none; background:rgba(0,0,0,0.6); align-items:flex-end; justify-content:center; }
  #modal.widoczny { display:flex; }
  #modalTresc { width:100%; max-height:85%; overflow-y:auto; background:#16121e; border-top:2px solid rgba(230,193,92,0.5);
      border-radius:18px 18px 0 0; padding:14px 12px 22px; touch-action:pan-y; }
  .ikonka-btn { position:absolute; top:10px; width:38px; height:38px; border-radius:11px; border:1px solid rgba(255,255,255,0.25);
      background:rgba(18,16,24,0.85); font-size:17px; z-index:31; }
  #siecInfo { position:absolute; left:50%; top:calc(env(safe-area-inset-top, 0px) + 64px); transform:translateX(-50%); z-index:65; display:none;
      background:rgba(60,14,14,0.95); border:1px solid rgba(255,120,100,0.6); border-radius:12px; padding:7px 14px; font-size:12.5px; font-weight:800;
      color:#ffd0c0; text-align:center; pointer-events:none; white-space:nowrap; }
  .siatka3.trzy, #gra.pc .siatka3.trzy { grid-template-columns:repeat(3, 1fr); }
  #gra.pc .szeroka > .siatka3.trzy { width:min(100%, 760px); justify-self:center; }
  .tagi { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; }
  .tagi .tag { margin:0; font-size:10px; }
  .tag-oh { background:rgba(255,160,90,0.17) !important; color:#ffc29a !important; }
  .tag-oh2 { background:rgba(255,90,90,0.2) !important; color:#ffa0a0 !important; }
  .tag-cd { background:rgba(126,196,255,0.16) !important; color:#9fd0ff !important; }
  .tag-sk { background:rgba(230,193,92,0.16) !important; color:#ffe08a !important; }
  /* ---------- BUILD: kafelki ---------- */
  .kafelki { display:grid; grid-template-columns:repeat(auto-fill, minmax(76px, 1fr)); gap:7px; margin-bottom:4px; }
  .kfl { position:relative; display:flex; flex-direction:column; align-items:center; gap:3px; padding:7px 4px 6px; border-radius:12px;
      background:linear-gradient(180deg,rgba(40,33,52,0.96),rgba(22,18,30,0.98)); border:2px solid var(--kol, rgba(255,255,255,0.15)); min-width:0; }
  .kfl.szeroki { flex-direction:row; gap:10px; padding:8px 10px; margin-bottom:4px; }
  .kfl.pryzm { border-color:transparent; background:linear-gradient(180deg,rgba(40,33,52,0.98),rgba(22,18,30,0.99)) padding-box,
      linear-gradient(120deg,#ff7ae0,#7ae0ff,#ffe07a,#9aff7a,#ff7ae0) border-box; }
  .kfl.pusty { border:2px dashed rgba(255,255,255,0.14); background:none; color:#6a6070; }
  .kfl-ik { position:relative; width:42px; height:42px; border-radius:11px; background:rgba(0,0,0,0.35); display:flex; align-items:center;
      justify-content:center; font-size:25px; flex:0 0 auto; }
  .kfl.pusty .kfl-ik { background:none; font-size:18px; }
  .kfl-n { font-size:10.5px; font-weight:800; text-align:center; line-height:1.2; max-width:100%; overflow:hidden; display:-webkit-box;
      -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .kfl-op { font-size:11px; color:#d8cdb0; line-height:1.45; margin-top:2px; }
  .kfl-znak { position:absolute; bottom:-5px; left:50%; transform:translateX(-50%); font-size:9px; font-weight:900; color:#ffe08a; white-space:nowrap; text-shadow:0 1px 2px #000; }
  .kfl-cd { position:absolute; top:-6px; right:-8px; font-size:8.5px; font-weight:900; padding:0 4px; border-radius:6px; background:rgba(126,196,255,0.25); color:#bfe2ff; }
  .kfl-odz { position:absolute; top:-7px; left:-7px; width:18px; height:18px; border-radius:9px; background:#7ec98a; color:#0d1a0d; font-size:11px;
      font-weight:900; display:flex; align-items:center; justify-content:center; box-shadow:0 1px 4px rgba(0,0,0,0.6); }
  .sekcja .licz { color:#ffe08a; margin-left:4px; }
  .chipy { display:flex; flex-wrap:wrap; gap:5px; margin:4px 0 6px; }
  .chip { font-size:11px; font-weight:700; padding:3px 8px; border-radius:9px; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); color:#d8cdb0; }
  .chip b { color:#ffe08a; }
  #gra.pc .kafelki { grid-template-columns:repeat(auto-fill, minmax(92px, 1fr)); }
  .sklep-akcje { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:6px 0 10px; }
  #gra.pc .szeroka > .sklep-akcje { width:min(100%, 600px); justify-self:center; }
  .akcja-sklepu { display:flex; align-items:center; justify-content:center; gap:10px; padding:11px 10px; border-radius:14px; font:inherit; cursor:pointer; text-align:left; color:#fff; min-height:58px; }
  .akcja-sklepu.przerzut { background:linear-gradient(135deg,#3f78c0,#22457c); border:1.5px solid #8cbcff; box-shadow:0 0 14px rgba(127,178,255,0.35); }
  .akcja-sklepu.staty { background:linear-gradient(135deg,#ecc860,#b38a24); border:1.5px solid #ffe08a; color:#1a1408; box-shadow:0 0 14px rgba(255,224,138,0.3); }
  .akcja-sklepu.ewo { width:100%; margin:0 0 10px; justify-content:flex-start; background:linear-gradient(135deg,#7a4ac4,#3e2470); border:1.5px solid #c9a8ff; box-shadow:0 0 14px rgba(201,168,255,0.3); }
  #gra.pc .szeroka > .akcja-sklepu.ewo { width:min(100%, 600px); justify-self:center; }
  .btn.hazard, .btn-maly.hazard { background:linear-gradient(135deg,#8a2a8a,#4a1050); border:1.5px solid #ff9ae0; color:#fff; }
  .btn.hazard { margin-top:8px; font-size:14px; }
  .hazard-anim { text-align:center; padding:18px 0 8px; }
  .hazard-kostka { font-size:72px; display:inline-block; animation:hazardKrec 0.55s cubic-bezier(.2,.8,.3,1); }
  .hazard-wynik { font-size:22px; font-weight:900; margin-top:8px; opacity:0; animation:hazardWynik 0.2s 0.38s forwards; }
  @keyframes hazardKrec { from { transform:rotate(-720deg) scale(0.3); } to { transform:rotate(0deg) scale(1); } }
  @keyframes hazardWynik { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
  .blok-umi { margin-top:6px; padding:7px 9px; border-radius:9px; background:rgba(255,224,138,0.08); font-size:12.5px; line-height:1.5; }
  .btn-boczny .auto-znak { position:absolute; left:-4px; top:-6px; font-size:9px; font-weight:900; background:#3f8a52; color:#fff; border-radius:6px; padding:1px 4px; display:none; }
  .btn-boczny.auto .auto-znak { display:block; }
  .akcja-sklepu:disabled { opacity:0.38; box-shadow:none; cursor:not-allowed; }
  .akcja-sklepu:not(:disabled):active { transform:scale(0.97); }
  .akcja-sklepu .as-ik { flex:none; width:30px; height:30px; }
  .akcja-sklepu .as-tekst { display:flex; flex-direction:column; line-height:1.15; }
  .akcja-sklepu .as-tekst b { font-size:16px; font-weight:900; }
  .akcja-sklepu .as-tekst span { font-size:13px; font-weight:800; opacity:0.92; white-space:nowrap; }
  .akcja-sklepu.kreci .as-ik { animation:kreci 0.55s cubic-bezier(.3,.7,.4,1); }
  @keyframes kreci { from { transform:rotate(-360deg); } to { transform:rotate(0deg); } }
  /* ---------- PAD ---------- */
  .pad-fokus { outline:3px solid #7ae0ff !important; outline-offset:2px !important;
      box-shadow:0 0 0 6px rgba(122,224,255,0.22), 0 0 20px rgba(122,224,255,0.55) !important; }
  .pad-wcisniety { transform:scale(0.95); }
  .pad-nie { animation:padNie .3s ease; }
  @keyframes padNie { 0%,100%{transform:none} 25%{transform:translateX(-5px)} 75%{transform:translateX(5px)} }
  .pad-kl { display:none; position:absolute; left:-7px; top:-7px; min-width:21px; height:21px; padding:0 5px; border-radius:11px;
      background:#f0e8d0; color:#16130a; font-size:11px; font-weight:900; line-height:21px; text-align:center;
      box-shadow:0 1px 5px rgba(0,0,0,0.7); z-index:2; pointer-events:none; font-family:system-ui,-apple-system,sans-serif; }
  .kl { display:inline-block; min-width:19px; height:19px; padding:0 5px; border-radius:10px; background:#d8cdb0; color:#16130a;
      font-size:10.5px; font-weight:900; line-height:19px; text-align:center; vertical-align:1px; margin:0 1px; }
  #gra.tryb-pad .pad-kl { display:block; }
  #gra.tryb-pad #strefaDrazka { display:none; }
  #gra.tryb-pad #pasSterowania { padding:0 16px; }
  #gra.tryb-pad .kolumna-btn { flex-direction:row; gap:14px; }
  #gra.tryb-pad .btn-boczny.maly { width:44px; height:44px; font-size:20px; }
  #gra.tryb-pad #btnUmi { width:50px; height:50px; font-size:25px; border-radius:15px; }
  #gra.tryb-pad #btnUmi .cdm { border-radius:13px; }
  #gra.tryb-pad #btnUmi .czas { font-size:16px; }
  #padSrodek { display:none; flex:1; text-align:center; font-size:11px; font-weight:800; color:#a89878; line-height:1.9; padding:0 6px; }
  #gra.tryb-pad #padSrodek { display:block; }
  #padPodp { position:absolute; left:0; right:0; bottom:0; z-index:55; display:none; padding:8px 10px calc(8px + env(safe-area-inset-bottom, 0px));
      background:linear-gradient(180deg, rgba(9,7,13,0), rgba(9,7,13,0.94) 35%); font-size:11px; font-weight:800; color:#d8cdb0;
      text-align:center; pointer-events:none; line-height:2; }
  #padPodp.widoczny { display:block; }
  #gra.tryb-pad #ekran { padding-bottom:60px; }
  #gra.tryb-pad #modalTresc { padding-bottom:52px; }
  /* ---------- KOMPUTER (szeroki ekran) ---------- */
  .ekran-tresc, .modal-tresc { zoom:var(--skalaUI, 1); }
  .kb-kl { display:none; position:absolute; left:-7px; top:-7px; min-width:21px; height:19px; padding:0 5px; border-radius:6px;
      background:#2a2238; border:1px solid #8a7a4e; color:#f0e8d0; font-size:10px; font-weight:900; line-height:17px; text-align:center;
      box-shadow:0 1px 5px rgba(0,0,0,0.7); z-index:2; pointer-events:none; font-family:system-ui,-apple-system,sans-serif; }
  #gra.pc:not(.tryb-pad) .kb-kl { display:block; }
  #gra.pc { max-width:none; }
  #gra.pc #hud { zoom:var(--skalaHud, 1); padding:10px 14px 0; }
  #gra.pc .hud-rzad > div:first-child { flex:0 1 430px !important; }
  #gra.pc #falaInfo { position:absolute; left:50%; top:10px; transform:translateX(-50%); min-width:118px; font-size:14px; padding:4px 12px; }
  #gra.pc #falaInfo small { font-size:10.5px; }
  #gra.pc #zlotoInfo { margin-left:auto; font-size:15px; padding:4px 12px; }
  #gra.pc #pasekPrzedm { max-width:430px; }
  #gra.pc .hud-slot { pointer-events:auto; cursor:help; }
  #gra.pc #dziennik { zoom:var(--skalaHud, 1); top:104px; right:auto; width:430px; }
  #gra.pc #baner { zoom:var(--skalaHud, 1); }
  #gra.pc #toast { bottom:calc(96px * var(--skalaHud, 1)); zoom:var(--skalaHud, 1); }
  #gra.pc #pasSterowania { left:50%; right:auto; bottom:12px; transform:translateX(-50%); height:auto; width:auto; zoom:var(--skalaHud, 1);
      padding:9px 16px; gap:16px; justify-content:center; border:1px solid #4a3a2e; border-radius:18px;
      background:rgba(16,13,22,0.84); box-shadow:0 6px 24px rgba(0,0,0,0.5); }
  #gra.pc #strefaDrazka { display:none; }
  #gra.pc .kolumna-btn { flex-direction:row; gap:12px; }
  #gra.pc .btn-boczny.maly { width:48px; height:48px; font-size:21px; }
  #gra.pc #btnUmi { width:56px; height:56px; font-size:27px; border-radius:16px; }
  #gra.pc #btnUmi .cdm { border-radius:14px; }
  #gra.pc #btnUmi .czas { font-size:17px; }
  #gra.pc #padSrodek { flex:0 0 auto; padding:0 4px; }
  #gra.pc #ekran { padding:22px 24px 44px; }
  #gra.pc .ekran-tresc { max-width:720px; margin:0 auto; }
  #gra.pc .ekran-tresc.szeroka { max-width:1200px; display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); column-gap:12px; align-items:start; }
  #gra.pc .szeroka > *:not(.karta):not(.slot-pusty):not(.wiersz-stat) { grid-column:1 / -1; }
  #gra.pc .szeroka > .btn, #gra.pc .szeroka > .rzad-btn { width:min(100%, 600px); justify-self:center; }
  #gra.pc .szeroka > .zakladki { width:min(100%, 900px); justify-self:center; }
  #gra.pc .szeroka > .info-pole { width:min(100%, 900px); justify-self:center; }
  #gra.pc .siatka3 { grid-template-columns:repeat(6, 1fr); }
  #gra.pc .siatka2 { grid-template-columns:repeat(4, 1fr); }
  #gra.pc #modal { align-items:center; }
  #gra.pc #modalTresc { max-width:calc(640px * var(--skalaUI, 1)); max-height:88%; border-radius:18px; border:2px solid rgba(230,193,92,0.5);
      box-shadow:0 20px 60px rgba(0,0,0,0.6); padding:16px 16px 20px; }
  #gra.pc #modal.szeroki #modalTresc { max-width:min(94%, calc(1120px * var(--skalaUI, 1))); }
  #gra.pc .modal-tresc.szeroka { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); column-gap:12px; align-items:start; }
  #gra.pc.tryb-pad #ekran { padding-bottom:64px; }
  @media (hover:hover) and (pointer:fine) {
    [data-a] { cursor:pointer; }
    .btn:not(:disabled):hover, .btn-maly:not(:disabled):hover, .zakladki button:hover, .btn-boczny:hover { filter:brightness(1.12); }
    .kafel[data-a]:hover, .karta[data-a]:hover, .wiersz-stat[data-a]:hover { border-color:rgba(255,224,138,0.75); filter:brightness(1.08); }
    .btn:disabled, .btn-maly:disabled { cursor:not-allowed; }
  }
  .wykres-pas { height:8px; border-radius:4px; background:linear-gradient(90deg,#e6c15c,#d4af37); }

  /* ---------- MARGINESY BEZPIECZNE (wcięcie aparatu, pasek gestów - gra z ekranu początkowego) ---------- */
  #hud { padding-top:calc(6px + env(safe-area-inset-top, 0px)); padding-left:calc(8px + env(safe-area-inset-left, 0px)); padding-right:calc(8px + env(safe-area-inset-right, 0px)); }
  #gra.pc #hud { padding:calc(10px + env(safe-area-inset-top, 0px)) calc(14px + env(safe-area-inset-right, 0px)) 0 calc(14px + env(safe-area-inset-left, 0px)); }
  #gra.pc #falaInfo { top:calc(10px + env(safe-area-inset-top, 0px)); }
  #dziennik { top:calc(96px + env(safe-area-inset-top, 0px)); }
  #pasSterowania { padding-bottom:env(safe-area-inset-bottom, 0px); }
  #ekran { padding-top:calc(14px + env(safe-area-inset-top, 0px)); padding-left:calc(12px + env(safe-area-inset-left, 0px)); padding-right:calc(12px + env(safe-area-inset-right, 0px)); }
  #gra.pc #ekran { padding-top:calc(22px + env(safe-area-inset-top, 0px)); padding-left:calc(24px + env(safe-area-inset-left, 0px)); padding-right:calc(24px + env(safe-area-inset-right, 0px)); }
  #modalTresc { padding-bottom:calc(22px + env(safe-area-inset-bottom, 0px)); }

  /* ---------- TABLET (pionowo) ---------- */
  #gra.tablet { max-width:none; }
  #gra.tablet .ekran-tresc { max-width:640px; margin:0 auto; }
  #gra.tablet #modalTresc { max-width:720px; }
  #gra.tablet #hud, #gra.tablet #dziennik { zoom:var(--skalaHud, 1); }

  /* ---------- POZIOMO NA DOTYKU (telefon / tablet obrócony) ---------- */
  #gra.pc.dotyk .kb-kl { display:none !important; }
  #gra.pc .hud-rzad > div:first-child { max-width:calc(50% - 82px); }
  #gra.pc #pasekPrzedm { max-width:min(430px, calc(50% - 82px)); }
  #gra.pc.dotyk #pasSterowania { left:auto; right:calc(14px + env(safe-area-inset-right, 0px)); bottom:calc(12px + env(safe-area-inset-bottom, 0px)); transform:none;
      background:none; border:0; box-shadow:none; padding:0; gap:12px; align-items:flex-end; }
  #gra.pc.dotyk .kolumna-btn { flex-direction:column; gap:10px; }
  #gra.pc.dotyk .btn-boczny.maly { width:52px; height:52px; font-size:23px; }
  #gra.pc.dotyk #btnUmi { width:84px; height:84px; font-size:37px; border-radius:24px; }
  #gra.pc.dotyk #btnUmi .cdm { border-radius:22px; }
  #gra.pc.dotyk #btnUmi .czas { font-size:23px; }
  #gra.pc.dotyk.tryb-pad #pasSterowania { left:50%; right:auto; transform:translateX(-50%); background:rgba(16,13,22,0.84); border:1px solid #4a3a2e; border-radius:18px; padding:9px 16px; }
  #gra.pc.dotyk.tryb-pad .kolumna-btn { flex-direction:row; }
  #gra.pc.dotyk #toast { bottom:calc(112px * var(--skalaHud, 1)); }
  /* drążek pod kciukiem: pojawia się tam, gdzie dotkniesz planszy (blady podgląd w lewym dolnym rogu) */
  #drazekPlyw { position:absolute; left:calc(100px + env(safe-area-inset-left, 0px)); top:calc(100% - 100px - env(safe-area-inset-bottom, 0px));
      width:124px; height:124px; margin:-62px 0 0 -62px; z-index:6; pointer-events:none; display:none; opacity:0.28; }
  #gra.pc.dotyk:not(.tryb-pad) #drazekPlyw { display:block; }
  #drazekPlyw.aktywny { opacity:0.95; }
  #drazekPlyw .baza { position:absolute; inset:0; border-radius:50%; background:radial-gradient(circle at 40% 35%, rgba(255,255,255,0.08), rgba(0,0,0,0.35));
      border:2px solid rgba(230,193,92,0.45); }
  #drazekPlyw .galka { position:absolute; left:50%; top:50%; width:52px; height:52px; margin:-26px 0 0 -26px; border-radius:50%;
      background:radial-gradient(circle at 38% 32%, #f0dfa8, #d4af37 60%, #8a6a1e); box-shadow:0 3px 10px rgba(0,0,0,0.5); }

  /* niski ekran (telefon poziomo): zwięźlejsze menu */
  @media (max-height:500px) and (orientation:landscape) {
    .menu-klucz { display:none; }
    .tytul.duzy { font-size:27px; margin-top:4px; }
  }
  /* ---------- OBRÓĆ URZĄDZENIE (wybrana orientacja) ---------- */
  #obrocInfo { position:absolute; inset:0; z-index:95; display:none; flex-direction:column; align-items:center; justify-content:center; gap:12px;
      background:rgba(9,7,13,0.97); text-align:center; padding:24px; }
  #obrocInfo.widoczny { display:flex; }
  #obrocInfo .ikona { font-size:64px; animation:obroc 1.8s ease-in-out infinite; }
  #obrocInfo .t { font-size:22px; font-weight:900; color:var(--zloto); }
  #obrocInfo .p { font-size:13px; color:#d8cdb0; max-width:340px; line-height:1.5; }
  #obrocInfo .btn { max-width:320px; }
  @keyframes obroc { 0%,20% { transform:rotate(0deg); } 50%,70% { transform:rotate(-90deg); } 100% { transform:rotate(0deg); } }
  #obrocInfo.pion .ikona { animation-direction:reverse; }
</style>
</head>
<body>
<audio id="odblokowanieDzwiekuIOS" loop playsinline style="display:none;"></audio>
<div id="gra">
  <canvas id="widok"></canvas>
  <div id="hud">
    <div class="hud-rzad">
      <div style="flex:1;min-width:0">
        <div class="pasek" id="hpPasek"><div class="wyp" id="hpWyp" style="width:100%"></div><div class="wyp" id="tarczaWyp" style="width:0%"></div><div class="napis" id="hpNapis">❤️ 100 / 100</div></div>
        <div class="pasek" id="xpPasek"><div class="wyp" id="xpWyp" style="width:0%"></div><div class="napis" id="xpNapis">Poziom 1</div></div>
      </div>
      <div id="falaInfo">🌊 Fala 1<small id="falaCzas">0:20</small></div>
      <div id="zlotoInfo">💰 0</div>
    </div>
    <div id="pasekPrzedm"></div>
  </div>
  <div id="dziennik"></div>
  <div id="baner"></div>
  <div id="pasSterowania">
    <div class="kolumna-btn">
      <button class="btn-boczny maly" id="btnEkw" title="Pauza i build (Esc)">🎒<span class="pad-kl" data-k="Y">Y</span><span class="kb-kl">Esc</span></button>
    </div>
    <div id="strefaDrazka"><div id="drazekBaza"><div id="drazekGalka"></div></div></div>
    <div id="padSrodek"></div>
    <button class="btn-boczny" id="btnUmi2" style="display:none"><span class="auto-znak">AUTO</span><span id="umi2Ik">✨</span><span class="cdm" id="umi2Cd"></span><span class="czas" id="umi2Czas"></span><span class="pad-kl" data-k="RB">RB</span><span class="kb-kl">R</span></button>
    <button class="btn-boczny" id="btnUmi"><span class="auto-znak">AUTO</span><span id="umiIk">✨</span><span class="cdm" id="umiCd"></span><span class="czas" id="umiCzas"></span><span class="pad-kl" data-k="A">A</span><span class="kb-kl">E</span></button>
  </div>
  <div id="ekran"></div>
  <div id="modal"><div id="modalTresc"></div></div>
  <div id="padPodp"></div>
  <div id="toast"></div>
  <div id="siecInfo"></div>
  <div id="drazekPlyw"><div class="baza"></div><div class="galka"></div></div>
  <div id="obrocInfo"><div class="ikona">📱</div><div class="t" id="obrocTytul">Obróć urządzenie</div><div class="p" id="obrocTekst"></div>
    <button class="btn drugi" data-a="obrocAuto">Graj w obu orientacjach</button></div>
</div>
<script>
'use strict';
// atlas fff746044b99 — zapasowe ikony (Noto Color Emoji, licencja SIL OFL 1.1)
const ATLAS_EMOJI = {"kom": 72, "font": 56, "kol": 12, "lista": ["🟠", "🟢", "🟣", "🟧", "🟩", "🥷", "🦣", "🦨", "🦺", "🧉", "🧊", "🧌", "🧑‍🌾", "🩴", "🩸", "🩹", "🩻", "🪃", "🪄", "🪐", "🪓", "🪖", "🪙", "🪚", "🪝", "🪞", "🪢", "🪤", "🪨", "🪬", "🪶", "🪽", "🫀", "🫐", "🫗", "🫥"], "src": "data:image/png;base64,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"};
'use strict';
// =====================================================================
//  WIĘZIEŃ LABIRYNTU — nieskończone lochy
//  Rdzeń: płótno, rozmiary, pomocnicze funkcje, dźwięk
// =====================================================================
const $ = id => document.getElementById(id);
// Stan gry online (uzupełniany w 15_siec.js). var - żeby był dostępny od początku.
var SIEC = { rola: null, mojeId: 0 };
const widok = $('widok'), ctx = widok.getContext('2d');
let DPR = Math.min(2, window.devicePixelRatio || 1);   // rozdzielczość płótna (liczona w dopasujRozmiar)
let WID = 380;                   // logiczna szerokość planszy (na komputerze szersza)
let WYS = 520;                   // logiczna wysokość - zależy od ekranu
const ZOOM = 0.9;
let WID_SW = WID / ZOOM, WYS_SW = WYS / ZOOM;
const KAM_PION = 0.55;
const KAFEL = 44;
const ARENA = 34;                // kafle na bok
const MUR = 2;
const POD_MIN = MUR * KAFEL + 14, POD_MAX = (ARENA - MUR) * KAFEL - 14;
const SRODEK = ARENA * KAFEL / 2;

function losowo(a, b) { return Math.random() * (b - a) + a; }
function losCalk(a, b) { return Math.floor(losowo(a, b + 1)); }
function losZ(t) { return t[Math.floor(Math.random() * t.length)]; }
function szansa(p) { return Math.random() < p; }
function ogr(v, a, b) { return v < a ? a : (v > b ? b : v); }
function odl(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
function tasuj(t) { for (let i = t.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [t[i], t[j]] = [t[j], t[i]]; } return t; }
function losWazony(lista) {           // [[wartosc, waga], ...]
  let s = 0; lista.forEach(e => s += Math.max(0, e[1]));
  let r = Math.random() * s;
  for (const e of lista) { r -= Math.max(0, e[1]); if (r <= 0) return e[0]; }
  return lista[lista.length - 1][0];
}
function okr(v, n) { const p = Math.pow(10, n || 0); return Math.round(v * p) / p; }
function fmt(v) {
  const a = Math.abs(v);
  if (a >= 100) return String(Math.round(v));
  if (a >= 10) return String(Math.round(v * 10) / 10).replace('.', ',');
  return String(Math.round(v * 10) / 10).replace('.', ',');
}
function fmtK(v) { v = Math.round(v); if (v >= 1e6) return (v / 1e6).toFixed(1).replace('.', ',') + ' mln'; if (v >= 10000) return Math.round(v / 1000) + ' tys.'; return String(v); }
function kat(a, b) { return Math.atan2(b.y - a.y, b.x - a.x); }
function roznicaKata(a, b) { return Math.abs(((a - b + Math.PI * 3) % (Math.PI * 2)) - Math.PI); }
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function czas(s) { s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
function lStorGet(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } }
function lStorSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
function lStorDel(k) { try { localStorage.removeItem(k); } catch (e) {} }

// ---------- USTAWIENIA (ekran ⚙️ Ustawienia) ----------
const USTAW = Object.assign({
  uklad: 'auto',          // auto / tel / pc — układ ekranu
  liczby: 'wszystkie',    // wszystkie / wazne / brak — liczby obrażeń nad wrogami
  efekty: 'pelne',        // pelne / oszczedne — iskry i odpryski
  mysz: true,             // komputer: ruch przytrzymanym lewym przyciskiem myszy
  interfejs: 1,           // 0.9 / 1 / 1.15 — wielkość napisów i przycisków
  orientacja: 'auto',     // auto / pion / poziom — telefon i tablet
  ikony: 'auto',          // auto / zawsze / systemowe — zapasowe obrazki emoji, których brakuje na urządzeniu
}, lStorGet('wiezien_ustawienia', {}));
function zapiszUstawienia() { lStorSet('wiezien_ustawienia', USTAW); }
let SKALA_TEKSTU = 1;     // liczby nad wrogami (na komputerze nieco mniejsze, bo plansza jest większa)

// ---------- ROZMIAR: gra zawsze zajmuje cały ekran ----------
const KOLOR_TLA = '#0b0910';
// Ciemne tło i kolor pasków przeglądarki (Safari bierze go z NAJWYŻSZEJ strony -
// na Streamlit Cloud aplikacja siedzi w jeszcze jednej ramce, więc idziemy w górę do samego szczytu)
function przyciemnijDokument(d) {
  try {
    if (!d || !d.documentElement) return;
    if (!d.getElementById('wiezienCiemno')) {
      const st = d.createElement('style'); st.id = 'wiezienCiemno';
      st.textContent = 'html,body{background:' + KOLOR_TLA + ' !important;background-color:' + KOLOR_TLA + ' !important;color-scheme:dark !important;}';
      (d.head || d.documentElement).appendChild(st);
    }
    d.documentElement.style.background = KOLOR_TLA; if (d.body) d.body.style.background = KOLOR_TLA;
    d.documentElement.style.colorScheme = 'dark';
    const metki = d.querySelectorAll('meta[name="theme-color"]');
    if (!metki.length) { const m = d.createElement('meta'); m.name = 'theme-color'; m.content = KOLOR_TLA; (d.head || d.documentElement).appendChild(m); }
    metki.forEach(m => { m.content = KOLOR_TLA; m.removeAttribute('media'); });
    let cs = d.querySelector('meta[name="color-scheme"]');
    if (!cs) { cs = d.createElement('meta'); cs.name = 'color-scheme'; (d.head || d.documentElement).appendChild(cs); }
    cs.content = 'dark';
    let ap = d.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
    if (!ap) { ap = d.createElement('meta'); ap.name = 'apple-mobile-web-app-status-bar-style'; (d.head || d.documentElement).appendChild(ap); }
    ap.content = 'black-translucent';
    // "Dodaj do ekranu początkowego" ma otwierać grę jak aplikację (bez pasków przeglądarki)
    [['apple-mobile-web-app-capable', 'yes'], ['mobile-web-app-capable', 'yes'], ['apple-mobile-web-app-title', 'Więzień']].forEach(([n, v]) => {
      if (!d.querySelector('meta[name="' + n + '"]')) { const m = d.createElement('meta'); m.name = n; m.content = v; (d.head || d.documentElement).appendChild(m); }
    });
  } catch (e) {}
}
function rozciagnijRamke() {
  // Aplikacja Streamlit osadza grę w ramce. Rozciągamy ją na całe okno
  // i chowamy elementy strony - gra ma wyglądać jak osobna aplikacja.
  przyciemnijDokument(document);
  let w = window;
  for (let poziom = 0; poziom < 6; poziom++) {
    let f = null;
    try { f = w.frameElement; } catch (e) { f = null; }
    if (!f) break;
    try {
      f.style.cssText += ';position:fixed !important;top:0 !important;left:0 !important;width:100vw !important;' +
        'height:100vh !important;height:100dvh !important;border:0 !important;margin:0 !important;z-index:999990 !important;max-width:none !important;background:' + KOLOR_TLA + ' !important;';
      const d = f.ownerDocument;
      if (poziom === 0) d.querySelectorAll('header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"]')
        .forEach(e => { e.style.display = 'none'; });
      przyciemnijDokument(d);
      d.documentElement.style.overflow = 'hidden'; if (d.body) d.body.style.overflow = 'hidden';
    } catch (e) { break; }
    try { w = w.parent; void w.document; } catch (e) { break; }
  }
}

// UKŁADY EKRANU
//  - pionowy (telefon, tablet): plansza u góry, na dole pasek z drążkiem i przyciskami;
//  - poziomy (komputer, telefon/tablet obrócony): plansza na cały ekran; z myszką - mały pasek akcji,
//    na dotyku - drążek pod kciukiem w dowolnym miejscu planszy i duże przyciski w prawym dolnym rogu.
function czyDotykowy() {
  try { if (matchMedia('(pointer: coarse)').matches) return true; } catch (e) {}
  let fine = false; try { fine = matchMedia('(any-pointer: fine)').matches; } catch (e) {}
  return (navigator.maxTouchPoints || 0) > 0 && !fine;
}
function czyUkladPC() {
  const w = window.innerWidth, h = window.innerHeight;
  return w > h * 1.05 && w >= 480;
}
function czyUkladDotyk() {
  if (USTAW.uklad === 'pc') return false;
  if (USTAW.uklad === 'tel') return true;
  return czyDotykowy();
}
// marginesy bezpieczne (wcięcie aparatu, pasek gestów) - w aplikacji z ekranu początkowego
let BEZP = { t: 0, b: 0, l: 0, r: 0 };
function zmierzBezpieczne() {
  try {
    let s = document.getElementById('sondaBezp');
    if (!s) { s = document.createElement('div'); s.id = 'sondaBezp'; s.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;visibility:hidden;pointer-events:none;' +
      'padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)'; document.body.appendChild(s); }
    const cs = getComputedStyle(s);
    BEZP = { t: parseFloat(cs.paddingTop) || 0, r: parseFloat(cs.paddingRight) || 0, b: parseFloat(cs.paddingBottom) || 0, l: parseFloat(cs.paddingLeft) || 0 };
  } catch (e) {}
  return BEZP;
}
function dopasujRozmiar() {
  rozciagnijRamke();
  const g = $('gra'), pc = czyUkladPC(), dotyk = pc && czyUkladDotyk();
  const W0 = window.innerWidth, H0 = window.innerHeight, tablet = !pc && Math.min(W0, H0) >= 600;
  g.classList.toggle('pc', pc); g.classList.toggle('dotyk', dotyk); g.classList.toggle('tablet', tablet);
  const B = zmierzBezpieczne();
  const w = g.clientWidth || W0, h = g.clientHeight || H0;
  const pas = pc ? 0 : (typeof PAD !== 'undefined' && PAD.tryb) ? 64 : Math.round(ogr(h * 0.21, 132, 178));   // z padem: wąski pasek bez drążka
  document.documentElement.style.setProperty('--wysPaska', (pas + (pc ? 0 : B.b)) + 'px');
  const hc = Math.max(240, h - (pc ? 0 : pas + B.b));
  widok.style.height = hc + 'px';
  if (pc) {
    // poziomo widać więcej planszy w bok; wysokość widoku zbliżona do telefonu trzymanego pionowo
    WYS = dotyk ? Math.round(ogr(hc * 1.1, 430, 580)) : 500; WID = Math.round(WYS * w / hc);
    if (WID > 1150) { WID = 1150; WYS = Math.round(WID * hc / w); }
    SKALA_TEKSTU = dotyk ? 0.95 : 0.85;
  } else { WID = tablet ? Math.round(ogr(w / 1.3, 380, 680)) : 380; WYS = Math.round(WID * hc / w); SKALA_TEKSTU = tablet ? 1.08 : 1; }
  // płótno w rozdzielczości ekranu (ostre także na dużym monitorze), maks. 2× dla płynności
  DPR = ogr(w * (window.devicePixelRatio || 1) / WID, 1, 2);
  WYS_SW = WYS / ZOOM; WID_SW = WID / ZOOM;
  widok.width = Math.round(WID * DPR); widok.height = Math.round(WYS * DPR);
  // wielkość interfejsu: na komputerze rośnie z wysokością okna, na tablecie z jego wielkością
  const sk = (pc ? (dotyk ? ogr(h / 440, 0.88, 1.4) : ogr(h / 800, 1, 1.45)) : tablet ? ogr(w / 620, 1, 1.35) : 1) * (USTAW.interfejs || 1);
  document.documentElement.style.setProperty('--skalaUI', sk.toFixed(3));
  document.documentElement.style.setProperty('--skalaHud', ((pc ? (dotyk ? ogr(h / 440, 0.9, 1.4) : ogr(h / 760, 1, 1.5)) : tablet ? ogr(w / 620, 1, 1.3) : 1) * (USTAW.interfejs || 1)).toFixed(3));
  if (typeof sprawdzObrot === 'function') sprawdzObrot();
}
// po zmianie okna sklep układa się od nowa (komputer: kolumny, telefon: zakładki)
function poZmianieOkna() { dopasujRozmiar(); try { if (typeof ekranEl !== 'undefined' && stan === 'przerwa' && ekranEl.querySelector('.sp-oferty')) pokazSklep(true); } catch (e) {} }
window.addEventListener('resize', () => setTimeout(poZmianieOkna, 50));
window.addEventListener('orientationchange', () => setTimeout(dopasujRozmiar, 250));

// ---------- DŹWIĘK ----------
let audioCtx = null, glosnik = null;
let dzwiekWlaczony = lStorGet('wiezien_dzwiek', true);
function inicjujDzwiek() {
  try {
    if (!audioCtx || audioCtx.state === 'closed') {
      let okno; try { okno = window.top; void okno.document; } catch (e) { okno = window; }
      if (okno.__wspolnyKontekstAudio && okno.__wspolnyKontekstAudio.state !== 'closed') audioCtx = okno.__wspolnyKontekstAudio;
      else {
        const K = window.AudioContext || window.webkitAudioContext;
        audioCtx = new K();
        try { okno.__wspolnyKontekstAudio = audioCtx; } catch (e2) {}
      }
      glosnik = audioCtx.createGain(); glosnik.gain.value = 0.9; glosnik.connect(audioCtx.destination);
    }
    if (audioCtx.state !== 'running') { try { audioCtx.resume(); } catch (e) {} }
    const el = $('odblokowanieDzwiekuIOS');
    if (el && !el.src) {
      el.src = 'data:audio/wav;base64,UklGRkQDAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YSADAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==';
      el.play().catch(() => {});
    } else if (el && el.paused) el.play().catch(() => {});
  } catch (e) {}
}
['pointerdown', 'touchstart', 'click', 'keydown'].forEach(ev => document.addEventListener(ev, inicjujDzwiek, { passive: true, capture: true }));
document.addEventListener('visibilitychange', () => { if (!document.hidden) setTimeout(inicjujDzwiek, 60); });

const _ostDzwiek = {};
function mozna(klucz, ms) {            // nie dopuszczamy do kakofonii przy 80 wrogach
  const t = performance.now();
  if (_ostDzwiek[klucz] && t - _ostDzwiek[klucz] < ms) return false;
  _ostDzwiek[klucz] = t; return true;
}
function ton(f, dl, typ, gl) {
  if (!audioCtx || !dzwiekWlaczony) return;
  try {
    const t = audioCtx.currentTime, o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = typ || 'square'; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gl || 0.12, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dl);
    o.connect(g); g.connect(glosnik);
    o.start(t); o.stop(t + dl + 0.03);
  } catch (e) {}
}
function tonSlizg(f1, f2, dl, typ, gl) {
  if (!audioCtx || !dzwiekWlaczony) return;
  try {
    const t = audioCtx.currentTime, o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = typ || 'triangle';
    o.frequency.setValueAtTime(f1, t); o.frequency.exponentialRampToValueAtTime(Math.max(20, f2), t + dl);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(gl || 0.06, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dl);
    o.connect(g); g.connect(glosnik); o.start(t); o.stop(t + dl + 0.03);
  } catch (e) {}
}
let buforSzumu = null;
function szum(dl, gl, filtr, czest) {
  if (!audioCtx || !dzwiekWlaczony) return;
  try {
    if (!buforSzumu || buforSzumu.sampleRate !== audioCtx.sampleRate) {
      buforSzumu = audioCtx.createBuffer(1, Math.floor(audioCtx.sampleRate * 0.6), audioCtx.sampleRate);
      const d = buforSzumu.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    const t = audioCtx.currentTime, s = audioCtx.createBufferSource(), f = audioCtx.createBiquadFilter(), g = audioCtx.createGain();
    s.buffer = buforSzumu; f.type = filtr || 'bandpass'; f.frequency.value = czest || 1200;
    g.gain.setValueAtTime(gl, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dl);
    s.connect(f); f.connect(g); g.connect(glosnik); s.start(t); s.stop(t + dl + 0.02);
  } catch (e) {}
}
const DZ = {
  ciecie() { if (mozna('ciecie', 55)) { ton(300, 0.06, 'sawtooth', 0.09); setTimeout(() => ton(170, 0.05, 'sawtooth', 0.06), 35); } },
  magia() { if (mozna('magia', 60)) { ton(560, 0.05, 'sine', 0.08); setTimeout(() => ton(820, 0.07, 'sine', 0.07), 40); } },
  strzal() { if (mozna('strzal', 60)) { tonSlizg(320, 150, 0.07, 'square', 0.05); szum(0.05, 0.04, 'highpass', 2500); } },
  trafienie() { if (mozna('traf', 45)) ton(200, 0.04, 'square', 0.06); },
  kryt() { if (mozna('kryt', 70)) { ton(880, 0.05, 'square', 0.1); setTimeout(() => ton(1180, 0.08, 'square', 0.08), 35); } },
  smiercWroga() { if (mozna('smw', 50)) { ton(160, 0.08, 'sawtooth', 0.08); setTimeout(() => ton(80, 0.13, 'sawtooth', 0.06), 70); } },
  moneta() { if (mozna('mon', 45)) ton(1320 + Math.random() * 200, 0.05, 'triangle', 0.05); },
  kulka() { if (mozna('kul', 40)) ton(760 + Math.random() * 260, 0.045, 'triangle', 0.04); },
  awans() { [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => ton(f, 0.15, 'triangle', 0.12), i * 90)); },
  mikstura() { ton(400, 0.07, 'sine', 0.12); setTimeout(() => ton(700, 0.13, 'sine', 0.11), 70); },
  naladowanie() { if (!mozna('nal', 300)) return; tonSlizg(500, 1300, 0.12, 'triangle', 0.07); },
  obrazenia() { if (mozna('obr', 90)) ton(150, 0.09, 'sawtooth', 0.11); },
  unik() { if (mozna('unik', 120)) tonSlizg(900, 1600, 0.12, 'sine', 0.05); },
  zwyciestwo() { [523, 659, 784, 1046, 1318].forEach((f, i) => setTimeout(() => ton(f, 0.18, 'triangle', 0.13), i * 120)); },
  smierc() { [300, 240, 180, 120].forEach((f, i) => setTimeout(() => ton(f, 0.24, 'sawtooth', 0.12), i * 150)); },
  wybuch() { if (mozna('wyb', 90)) { szum(0.4, 0.2, 'lowpass', 700); tonSlizg(110, 40, 0.35, 'sawtooth', 0.1); } },
  piorun() { if (mozna('pior', 60)) { ton(1200 + Math.random() * 300, 0.05, 'sawtooth', 0.045); szum(0.08, 0.05, 'highpass', 3000); } },
  czar() { if (mozna('czar', 120)) { tonSlizg(380, 1150, 0.25, 'sine', 0.05); } },
  wrogStrzal(t) {
    if (!mozna('ws', 70)) return;
    if (t === 'kusznik' || t === 'lucznik') { tonSlizg(320, 150, 0.06, 'square', 0.035); }
    else if (t === 'boss') tonSlizg(260, 110, 0.18, 'sawtooth', 0.06);
    else tonSlizg(760, 380, 0.08, 'triangle', 0.04);
  },
  zakup() { ton(990, 0.06, 'triangle', 0.1); setTimeout(() => ton(1320, 0.1, 'triangle', 0.1), 60); },
  klik() { ton(700, 0.03, 'triangle', 0.06); },
  wybor() { [660, 880, 1100].forEach((f, i) => setTimeout(() => ton(f, 0.1, 'triangle', 0.1), i * 60)); },
  pryzmat() { [523, 784, 1046, 1318, 1568].forEach((f, i) => setTimeout(() => ton(f, 0.22, 'sine', 0.09), i * 70)); },
  boss() { ton(90, 0.5, 'sawtooth', 0.16); setTimeout(() => ton(60, 0.7, 'sawtooth', 0.14), 400); },
  fala() { [392, 523, 659].forEach((f, i) => setTimeout(() => ton(f, 0.14, 'triangle', 0.1), i * 110)); },
  tarcza() { if (mozna('tar', 150)) tonSlizg(500, 900, 0.15, 'sine', 0.06); },
  skrzynia() { ton(660, 0.07, 'triangle', 0.11); setTimeout(() => ton(990, 0.1, 'triangle', 0.1), 60); },
  blad() { ton(180, 0.12, 'square', 0.08); },
  syk() { if (mozna('syk', 200)) szum(0.4, 0.03, 'highpass', 3200); },
};

// =====================================================================
//  IKONY: emoji rysowane jako gotowe obrazki (dużo szybciej niż tekst),
//  z obrysem / białym błyskiem / szarością, oraz zapasowy atlas dla emoji,
//  których urządzenie nie ma (np. Windows 10, starsze telefony).
//  Atlas: czcionka Noto Color Emoji (SIL Open Font License 1.1).
// =====================================================================
const FONT_EMOJI = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji","Twemoji Mozilla","Segoe UI Symbol",sans-serif';
const IKONY = { brak: new Set(), atlas: null, cache: new Map(), url: {}, regex: null, obserwator: null };
let SKALA_RYS = 1;   // pikseli ekranu na jednostkę planszy - ustawiane przy każdym rysowaniu

(function () {
  if (typeof ATLAS_EMOJI === 'undefined') return;
  const im = new Image();
  im.onload = () => { IKONY.cache.clear(); IKONY.url = {}; if (IKONY.brak.size) wlaczPodmianeEmoji(); };
  im.src = ATLAS_EMOJI.src; IKONY.atlas = im;
})();

// Które emoji z atlasu nie wyświetlą się na tym urządzeniu? Rysujemy je i porównujemy
// z „pustym kwadracikiem” (znak, którego żadna czcionka nie ma) - oraz sprawdzamy,
// czy sekwencja (np. 🧑‍🌾) nie rozpadła się na dwa osobne znaki.
function wykryjBrakiEmoji() {
  IKONY.brak.clear();
  if (typeof ATLAS_EMOJI === 'undefined') return;
  if (USTAW.ikony === 'zawsze') ATLAS_EMOJI.lista.forEach(e => IKONY.brak.add(e));
  else if (USTAW.ikony !== 'systemowe') {
    try {
      const R = 28, c = document.createElement('canvas'); c.width = c.height = R;
      const x = c.getContext('2d', { willReadFrequently: true });
      x.font = '22px ' + FONT_EMOJI; x.textAlign = 'center'; x.textBaseline = 'middle';
      const rys = t => { x.clearRect(0, 0, R, R); x.fillText(t, R / 2, R / 2); return x.getImageData(0, 0, R, R).data; };
      const tofu = rys('\u{10FFFD}'), wzor = x.measureText('😀').width || 22;
      ATLAS_EMOJI.lista.forEach(e => {
        const d = rys(e); let pusty = true, jakTofu = true;
        for (let i = 3; i < d.length; i += 4) if (d[i] > 24) { pusty = false; break; }
        for (let i = 0; i < d.length; i++) if (d[i] !== tofu[i]) { jakTofu = false; break; }
        if (pusty || jakTofu || x.measureText(e).width > wzor * 1.45) IKONY.brak.add(e);
      });
    } catch (e) {}
  }
  IKONY.cache.clear(); IKONY.url = {};
  IKONY.regex = IKONY.brak.size ? new RegExp(Array.from(IKONY.brak).sort((a, b) => b.length - a.length).map(e => e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'g') : null;
  wlaczPodmianeEmoji();
}

function kubelekIkony(px) { return px <= 24 ? Math.max(8, Math.ceil(px / 4) * 4) : px <= 64 ? Math.ceil(px / 8) * 8 : Math.min(224, Math.ceil(px / 16) * 16); }
function rysujGlif(x, ik, cx, cy, px) {
  const A = typeof ATLAS_EMOJI !== 'undefined' ? ATLAS_EMOJI : null;
  if (A && IKONY.brak.has(ik) && IKONY.atlas && IKONY.atlas.complete && IKONY.atlas.naturalWidth) {
    const i = A.lista.indexOf(ik), s = px / A.font * A.kom;
    x.drawImage(IKONY.atlas, (i % A.kol) * A.kom, Math.floor(i / A.kol) * A.kom, A.kom, A.kom, cx - s / 2, cy - s / 2, s, s);
  } else { x.font = px + 'px ' + FONT_EMOJI; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(ik, cx, cy); }
}
// Gotowy obrazek ikony. war: '' zwykła, 'o' z ciemnym obrysem (wrogowie), 'b' biała sylwetka (błysk trafienia),
// 's' szara (można łączyć: 'so' - szara z obrysem)
function obrazIkony(ik, px, war) {
  const k = ik + '|' + px + '|' + (war || '');
  let im = IKONY.cache.get(k);
  if (im) return im;
  if (IKONY.cache.size > 700) IKONY.cache.clear();
  const pad = Math.ceil(px * 0.2) + 3, R = px + pad * 2;
  const c = document.createElement('canvas'); c.width = c.height = R;
  const x = c.getContext('2d');
  rysujGlif(x, ik, R / 2, R / 2, px);
  war = war || '';
  if (war.indexOf('s') >= 0) {
    try { const d = x.getImageData(0, 0, R, R), p = d.data; for (let i = 0; i < p.length; i += 4) { const l = p[i] * 0.3 + p[i + 1] * 0.59 + p[i + 2] * 0.11; p[i] = p[i + 1] = p[i + 2] = l; } x.putImageData(d, 0, 0); } catch (e) {}
  }
  if (war.indexOf('o') >= 0 || war === 'b') {
    const s = document.createElement('canvas'); s.width = s.height = R;
    const y = s.getContext('2d');
    y.drawImage(c, 0, 0); y.globalCompositeOperation = 'source-in'; y.fillStyle = war === 'b' ? '#ffffff' : 'rgba(14,8,20,0.92)'; y.fillRect(0, 0, R, R);
    if (war === 'b') im = s;
    else {
      const g = Math.max(1, px / 24), h = g * 0.72;
      x.globalCompositeOperation = 'destination-over';
      [[g, 0], [-g, 0], [0, g], [0, -g], [h, h], [-h, h], [h, -h], [-h, -h]].forEach(([dx, dy]) => x.drawImage(s, dx, dy));
      x.globalCompositeOperation = 'source-over';
    }
  }
  im = im || c; im.k = R / px;
  IKONY.cache.set(k, im);
  return im;
}
function skalaKontekstu(c) {
  if (c.getTransform) { const t = c.getTransform(); return Math.hypot(t.a, t.b) || 1; }
  return c === ctx ? SKALA_RYS : 2;
}
// Rysuje jedno emoji wyśrodkowane w (x, y); rozm - jak wielkość czcionki w starym fillText
function rysujIk(c, ik, x, y, rozm, war, skala) {
  if (!ik || !(rozm > 0)) return;
  const im = obrazIkony(ik, kubelekIkony(rozm * (skala || skalaKontekstu(c))), war), w = rozm * im.k;
  c.drawImage(im, x - w / 2, y - w / 2, w, w);
}
// Kilka emoji obok siebie (np. ikony afiksów elity)
function podzielIkony(t) {
  const z = Array.from(t || ''), w = [];
  for (let i = 0; i < z.length; i++) {
    const cp = z[i].codePointAt(0), pop = w.length ? w[w.length - 1] : '';
    if (pop && (cp === 0xFE0F || cp === 0x200D || cp === 0x20E3 || (cp >= 0x1F3FB && cp <= 0x1F3FF) || pop.endsWith('‍'))) w[w.length - 1] += z[i];
    else if (z[i].trim()) w.push(z[i]);
  }
  return w;
}
function rysujIki(c, t, x, y, rozm, war) {
  const l = podzielIkony(t), krok = rozm * 1.12;
  l.forEach((ik, i) => rysujIk(c, ik, x + (i - (l.length - 1) / 2) * krok, y, rozm, war));
}
// Tekst z obrysem, w którym mogą być emoji (te, których brakuje, rysujemy z atlasu)
function tekstZObrysem(c, t, x, y) {
  if (!IKONY.regex || !IKONY.regex.test(t)) { if (IKONY.regex) IKONY.regex.lastIndex = 0; c.strokeText(t, x, y); c.fillText(t, x, y); return; }
  IKONY.regex.lastIndex = 0;
  const czesci = [], re = IKONY.regex; let i = 0, m;
  while ((m = re.exec(t))) { if (m.index > i) czesci.push([0, t.slice(i, m.index)]); czesci.push([1, m[0]]); i = m.index + m[0].length; }
  if (i < t.length) czesci.push([0, t.slice(i)]);
  re.lastIndex = 0;
  const rozm = parseFloat((c.font.match(/(\d+(?:\.\d+)?)px/) || [0, 12])[1]);
  const szer = czesci.map(p => p[0] ? rozm * 1.15 : c.measureText(p[1]).width), suma = szer.reduce((a, b) => a + b, 0);
  const wyr = c.textAlign, base = c.textBaseline;
  let px = wyr === 'center' ? x - suma / 2 : (wyr === 'right' || wyr === 'end') ? x - suma : x;
  c.textAlign = 'left';
  const sy = base === 'middle' ? y : base === 'top' ? y + rozm * 0.5 : y - rozm * 0.36;
  czesci.forEach((p, j) => {
    if (p[0]) rysujIk(c, p[1], px + szer[j] / 2, sy, rozm);
    else { c.strokeText(p[1], px, y); c.fillText(p[1], px, y); }
    px += szer[j];
  });
  c.textAlign = wyr;
}

// ---------- strona (HTML): brakujące emoji zamieniamy na obrazki ----------
const POMIN_PODMIANE = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, OPTION: 1, SELECT: 1, INPUT: 1, CANVAS: 1, TITLE: 1 };
function urlIkony(ik) {
  if (!IKONY.url[ik]) {
    const c = document.createElement('canvas'), R = 64; c.width = c.height = R;
    rysujGlif(c.getContext('2d'), ik, R / 2, R / 2, 50);
    IKONY.url[ik] = c.toDataURL('image/png');
  }
  return IKONY.url[ik];
}
function zamienWezelEmoji(n) {
  const t = n.nodeValue, re = IKONY.regex, f = document.createDocumentFragment(); let i = 0, m;
  re.lastIndex = 0;
  while ((m = re.exec(t))) {
    if (m.index > i) f.appendChild(document.createTextNode(t.slice(i, m.index)));
    const im = document.createElement('img'); im.className = 'emo'; im.alt = m[0]; im.draggable = false; im.src = urlIkony(m[0]);
    f.appendChild(im); i = m.index + m[0].length;
  }
  re.lastIndex = 0;
  if (i < t.length) f.appendChild(document.createTextNode(t.slice(i)));
  if (n.parentNode) n.parentNode.replaceChild(f, n);
}
function sprawdzWezel(n) {
  const re = IKONY.regex;
  if (!re || !n.parentNode || POMIN_PODMIANE[n.parentNode.nodeName]) return;
  const jest = re.test(n.nodeValue || ''); re.lastIndex = 0;
  if (jest) zamienWezelEmoji(n);
}
function podmienEmojiW(el) {
  if (!IKONY.regex || !el) return;
  if (el.nodeType === 3) { sprawdzWezel(el); return; }
  if (el.nodeType !== 1 || POMIN_PODMIANE[el.nodeName]) return;
  const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), lista = [];
  let n; while ((n = tw.nextNode())) lista.push(n);
  lista.forEach(sprawdzWezel);
}
function wlaczPodmianeEmoji() {
  if (IKONY.obserwator) { IKONY.obserwator.disconnect(); IKONY.obserwator = null; }
  if (!IKONY.regex || typeof MutationObserver === 'undefined' || !document.body) return;
  podmienEmojiW(document.body);
  IKONY.obserwator = new MutationObserver(lista => {
    for (const m of lista) {
      if (m.type === 'characterData') sprawdzWezel(m.target);
      else m.addedNodes.forEach(podmienEmojiW);
    }
  });
  IKONY.obserwator.observe(document.body, { childList: true, subtree: true, characterData: true });
}

// =====================================================================
//  STATYSTYKI, TIERY, OPISY
// =====================================================================
const TIERY = [
  { nazwa: 'Zwykły',     nazwaZ: 'Zwykła',     kolor: '#b8b8b8', rz: 'I' },
  { nazwa: 'Rzadki',     nazwaZ: 'Rzadka',     kolor: '#5aa8e6', rz: 'II' },
  { nazwa: 'Epicki',     nazwaZ: 'Epicka',     kolor: '#b06ce8', rz: 'III' },
  { nazwa: 'Legendarny', nazwaZ: 'Legendarna', kolor: '#e6b53c', rz: 'IV' },
  { nazwa: 'Mityczny',   nazwaZ: 'Mityczna',   kolor: '#ff5a4a', rz: 'V' },
];
const KOLOR_PRYZMAT = '#ff7ae0';
const TIERY_AUG = {
  s: { nazwa: 'Szary augment', kolor: '#a8adb8', klasa: 'as' },
  z: { nazwa: 'Złoty augment', kolor: '#e6c15c', klasa: 'az' },
  p: { nazwa: 'Pryzmatyczny augment', kolor: '#ff7ae0', klasa: 'ap' },
};

// k - klucz, n - nazwa, i - ikona, j - jednostka, o - objaśnienie, g - grupa
const DEF_STATOW = [
  { k: 'hpMax', n: 'Maks. zdrowie', i: '❤️', g: 'obrona', o: 'Ile obrażeń zniesiesz. Leczenie nie przekroczy tej wartości.' },
  { k: 'pancerz', n: 'Pancerz', i: '🛡️', g: 'obrona', o: 'Zmniejsza obrażenia fizyczne: 100 pancerza = −50%.' },
  { k: 'odpMag', n: 'Odporność na magię', i: '🔰', g: 'obrona', o: 'Zmniejsza obrażenia magiczne: 100 = −50%.' },
  { k: 'unik', n: 'Unik', i: '💨', j: '%', g: 'obrona', o: 'Szansa, że trafienie Cię ominie (maks. 80%, ze Skrzydlatymi Sandałami 95%). Nie działa na wybuchy.' },
  { k: 'redukcja', n: 'Redukcja obrażeń', i: '🪨', j: '%', g: 'obrona', o: 'Zmniejsza KAŻDE otrzymane obrażenia (maks. 75%, z Tytanowym Kręgosłupem 90%).' },
  { k: 'wytrwalosc', n: 'Nieustępliwość', i: '🧱', j: '%', g: 'obrona', o: 'Skraca spowolnienia i ogłuszenia nałożone na Ciebie.' },
  { k: 'ad', n: 'Obrażenia od ataku', i: '⚔️', g: 'atak', o: 'Dodawane do broni fizycznych (wg ich przelicznika) i wielu przedmiotów.' },
  { k: 'ap', n: 'Moc umiejętności', i: '✨', g: 'atak', o: 'Wzmacnia bronie magiczne i większość efektów przedmiotów.' },
  { k: 'as', n: 'Prędkość ataku', i: '⚡', j: '%', g: 'atak', o: 'Premia do tempa ataków wszystkich broni.' },
  { k: 'kryt', n: 'Szansa na kryt', i: '🎯', j: '%', g: 'atak', o: 'Szansa, że atak zada obrażenia krytyczne.' },
  { k: 'krytObr', n: 'Obrażenia krytyczne', i: '💥', j: '%', g: 'atak', baza: 175, o: 'Mnożnik obrażeń trafienia krytycznego.' },
  { k: 'obrBonus', n: 'Obrażenia', i: '🔥', j: '%', g: 'atak', o: 'Mnoży WSZYSTKIE zadawane obrażenia.' },
  { k: 'lethality', n: 'Przebicie pancerza', i: '🗡️', g: 'atak', o: 'Płaskie przebicie: ignoruje tyle pancerza wroga.' },
  { k: 'przebPancP', n: '% przebicia pancerza', i: '🪓', j: '%', g: 'atak', o: 'Ignoruje taki procent pancerza wroga.' },
  { k: 'przebMag', n: 'Przebicie magii', i: '🌀', g: 'atak', o: 'Płaskie przebicie odporności na magię.' },
  { k: 'przebMagP', n: '% przebicia magii', i: '🕳️', j: '%', g: 'atak', o: 'Ignoruje taki procent odporności na magię.' },
  { k: 'omni', n: 'Wampiryzm', i: '🦇', j: '%', g: 'atak', o: 'Leczy o procent WSZYSTKICH zadanych obrażeń (obszarowe i rozłożone w czasie: 1/3). Limit: 1% maks. zdrowia na sekundę + 0,12% za każdy punkt (maks. 5%/s). Rzadki — w wyborze statystyk dopiero od fioletowego tieru.' },
  { k: 'zasieg', n: 'Zasięg', i: '🏹', j: '%', g: 'atak', o: 'Zasięg broni dystansowych (wręcz: połowa premii).' },
  { k: 'pociski', n: 'Dodatkowe pociski', i: '➶', g: 'atak', o: 'Bronie strzelające wypuszczają więcej pocisków (każdy dodatkowy: 60% obrażeń).' },
  { k: 'przebicie', n: 'Przebicie pocisków', i: '📌', g: 'atak', o: 'Pociski przelatują przez tylu dodatkowych wrogów.' },
  { k: 'obszar', n: 'Wielkość obszarów', i: '⭕', j: '%', g: 'atak', o: 'Większe wybuchy, aury i pola.' },
  { k: 'haste', n: 'Przyspieszenie', i: '⏱️', g: 'uzyt', o: 'Skraca odnowienia broni, przedmiotów i umiejętności: 100 = 2× częściej.' },
  { k: 'ms', n: 'Prędkość ruchu', i: '👟', g: 'uzyt', o: 'Jak szybko się poruszasz.' },
  { k: 'leczenie', n: 'Moc leczenia i tarcz', i: '💞', j: '%', g: 'uzyt', o: 'Wzmacnia każde leczenie i każdą tarczę.' },
  { k: 'szczescie', n: 'Szczęście', i: '🍀', g: 'uzyt', o: 'Lepsze przedmioty w sklepie i skrzyniach, częstsze skrzynie, lepsze augmenty i statystyki.' },
  { k: 'zbieranie', n: 'Zasięg zbierania', i: '🧲', g: 'uzyt', o: 'Z jakiej odległości przyciągasz złoto i doświadczenie.' },
  { k: 'chciwosc', n: 'Zysk złota', i: '💰', j: '%', g: 'uzyt', o: 'Więcej złota z każdego źródła.' },
  { k: 'xpBonus', n: 'Doświadczenie', i: '📘', j: '%', g: 'uzyt', o: 'Więcej doświadczenia z kulek.' },
  { k: 'obrElity', n: 'Obrażenia vs elity i bossowie', i: '👑', j: '%', g: 'atak', o: 'Dodatkowe obrażenia przeciw elitom i bossom.' },
  { k: 'onHitFiz', n: 'On-hit (fizyczne)', i: '🟠', g: 'onhit', o: 'On-hit: każde trafienie atakiem zadaje dodatkowo tyle obrażeń fizycznych.' },
  { k: 'onHitMag', n: 'On-hit (magiczne)', i: '🔵', g: 'onhit', o: 'On-hit: każde trafienie atakiem zadaje dodatkowo tyle obrażeń magicznych.' },
  { k: 'onHitPraw', n: 'On-hit (prawdziwe)', i: '⚪', g: 'onhit', o: 'On-hit: każde trafienie atakiem zadaje dodatkowo tyle obrażeń prawdziwych (ignorują pancerz).' },
];
const STAT = {}; DEF_STATOW.forEach(d => STAT[d.k] = d);
// znacznik efektów przy trafieniu (on-hit) w opisach
const OH = '<span class="onhit">on-hit</span> ';
const BAZA_STATOW = {
  hpMax: 120, pancerz: 0, odpMag: 0, unik: 0, redukcja: 0, wytrwalosc: 0,
  ad: 0, ap: 0, as: 0, kryt: 5, krytObr: 0, obrBonus: 0, lethality: 0, przebPancP: 0, przebMag: 0, przebMagP: 0,
  omni: 0, zasieg: 0, pociski: 0, przebicie: 0, obszar: 0, haste: 0, ms: 140, leczenie: 0, szczescie: 0,
  zbieranie: 85, chciwosc: 0, xpBonus: 0, obrElity: 0, onHitFiz: 0, onHitMag: 0, onHitPraw: 0,
};
function pusteStaty() { const s = {}; for (const k in BAZA_STATOW) s[k] = 0; return s; }

function wartoscStatuTekst(k, v) {
  const d = STAT[k];
  if (k === 'krytObr') return Math.round(175 + v) + '%';
  if (d && d.j === '%') return fmt(v) + '%';
  if (d && d.j === '/s') return fmt(v) + '/s';
  return fmt(v);
}
// "+25 ⚔️ Obrażeń od ataku" - linijki statów przedmiotu
const NAZWY_W_OPISIE = {
  hpMax: 'zdrowia', pancerz: 'pancerza', odpMag: 'odp. na magię', unik: 'uniku', redukcja: 'redukcji obrażeń',
  wytrwalosc: 'nieustępliwości', ad: 'obrażeń od ataku', ap: 'mocy umiejętności', as: 'prędkości ataku', kryt: 'szansy na kryt',
  krytObr: 'obrażeń krytycznych', obrBonus: 'obrażeń', lethality: 'przebicia pancerza', przebPancP: 'przebicia pancerza',
  przebMag: 'przebicia magii', przebMagP: 'przebicia magii', omni: 'wampiryzmu', zasieg: 'zasięgu',
  pociski: 'pocisków', przebicie: 'przebicia pocisków', obszar: 'wielkości obszarów', haste: 'przyspieszenia', ms: 'prędkości ruchu',
  leczenie: 'mocy leczenia i tarcz', szczescie: 'szczęścia', zbieranie: 'zasięgu zbierania', chciwosc: 'zysku złota', xpBonus: 'doświadczenia',
  obrElity: 'obrażeń vs elity i bossowie', onHitFiz: 'fiz. obrażeń on-hit', onHitMag: 'mag. obrażeń on-hit', onHitPraw: 'prawdziwych obr. on-hit',
};
function liniaStatu(k, v) {
  const d = STAT[k] || { i: '•' };
  const proc = d.j === '%' ? '%' : '';
  const znak = v >= 0 ? '+' : '−';
  return '<span>' + d.i + ' <b>' + znak + fmt(Math.abs(v)) + proc + '</b> ' + (NAZWY_W_OPISIE[k] || k) + '</span>';
}
function opisStatow(staty, mn) {
  if (!staty) return '';
  const cz = [];
  for (const k in staty) { const v = staty[k] * (mn || 1); if (Math.abs(v) > 0.0001) cz.push(liniaStatu(k, v)); }
  return cz.join('<br>');
}

// ---------- ULEPSZENIA STATYSTYK (wybór przy awansie) ----------
// cztery tiery: wartość rośnie, a lepsze tiery częściej dzięki szczęściu i poziomowi
const ULEPSZENIA_STATOW = [
  { k: 'hpMax', w: [15, 28, 46, 72] },
  { k: 'pancerz', w: [5, 9, 15, 23] },
  { k: 'odpMag', w: [5, 9, 15, 23] },
  { k: 'ad', w: [6, 10, 16, 24] },
  { k: 'ap', w: [9, 15, 24, 36] },
  { k: 'as', w: [5, 9, 14, 21] },
  { k: 'kryt', w: [4, 7, 10, 15] },
  { k: 'krytObr', w: [5, 9, 14, 20] },
  { k: 'obrBonus', w: [3, 5, 8, 12] },
  { k: 'omni', w: [0, 0, 2.5, 4], odTieru: 2 },   // wampiryzm: rzadki, dopiero od fioletowego
  { k: 'ms', w: [6, 10, 15, 22] },
  { k: 'zasieg', w: [6, 10, 15, 22] },
  { k: 'unik', w: [2, 3.5, 5, 7] },
  { k: 'szczescie', w: [6, 11, 18, 28] },
  { k: 'haste', w: [5, 9, 14, 21] },
  { k: 'lethality', w: [2, 4, 6, 9] },
  { k: 'przebMag', w: [3, 5, 8, 12] },
  { k: 'chciwosc', w: [3, 5, 8, 12] },
  { k: 'xpBonus', w: [4, 6, 9, 13] },
  { k: 'zbieranie', w: [20, 35, 55, 80] },
  { k: 'leczenie', w: [5, 8, 12, 18] },
  { k: 'onHitFiz', w: [5, 8, 13, 20] },
  { k: 'onHitMag', w: [5, 8, 13, 20] },
];

// =====================================================================
//  BROŃ GŁÓWNA — każda postać ma swoją (zależnie od klasy), to ona atakuje.
//  Ulepszana w sklepie tierami I–V. Skaluje się od kilku statystyk naraz.
//  Bronie dodatkowe ("oręż", 03b_oreze.js) dają do niej statystyki.
// =====================================================================
const MN_BRONI = [1, 1.55, 2.3, 3.3, 4.6];
const MAKS_TIER_BRONI = 4;
const CENA_ULEPSZ_BRONI = [55, 125, 240, 400];   // z tieru t na t+1

// Rodziny broni: główna + bronie dodatkowe tej samej rodziny dają premię zestawu
const RODZINY = {
  biala:      { n: 'Broń biała', ik: '⚔️', staty: n => ({ ad: [5, 10, 16, 24, 34][n], pancerz: [8, 14, 22, 32, 44][n] }), opis: 'obrażeń od ataku i pancerza' },
  strzelecka: { n: 'Broń strzelecka', ik: '🏹', staty: n => ({ as: [8, 14, 20, 28, 38][n], kryt: [4, 7, 10, 14, 18][n] }), opis: 'prędkości ataku i szansy na kryt' },
  magiczna:   { n: 'Broń magiczna', ik: '🪄', staty: n => ({ ap: [12, 22, 34, 50, 70][n], haste: [8, 14, 20, 28, 36][n] }), opis: 'mocy umiejętności i przyspieszenia' },
  alchemia:   { n: 'Alchemia', ik: '💣', staty: n => ({ obszar: [10, 16, 24, 32, 42][n], obrBonus: [4, 7, 10, 14, 18][n] }), opis: 'wielkości obszarów i obrażeń' },
};
const KLUCZE_RODZIN = Object.keys(RODZINY);
const PROGI_RODZIN = [2, 3, 4, 5, 6];
const IKONY_SKAL = { ad: '⚔️', ap: '✨', hpMax: '❤️ maks. zdrowia', pancerz: '🛡️ pancerza', odpMag: '🔰 odporności', ms: '👟 prędkości ruchu', szczescie: '🍀 szczęścia', as: '⚡ prędkości ataku', zloto: '💰 złota', kryt: '🎯 szansy na kryt', haste: '⏱️ przyspieszenia' };

const BRONIE = {
  // ======================= BROŃ BIAŁA =======================
  miecz: {
    nazwa: 'Miecz', ikona: '🗡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.8, zasieg: 76, obr: 24, skal: { ad: 1.18 }, luk: 2.0,
    opisEf: t => 'Leczy o <b>' + (4 + 2 * t) + '%</b> zadanych obrażeń.',
    naTrafienie(w, b, k) { if (k.zadane > 0) leczWampirem(k.zadane * (0.04 + 0.02 * b.tier), 'Miecz'); },
  },
  mieczTarcza: {
    nazwa: 'Miecz i Tarcza', ikona: '🛡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.95, zasieg: 72, obr: 31, skal: { ad: 1.26, pancerz: 0.49 }, luk: 2.2,
    opisEf: t => 'Co 4. cios: tarcza <b>' + (25 + 15 * t) + ' + 20% pancerza</b> na 3 s i odrzut wrogów wokół.',
    naTrafienie(w, b, k) { if (!k.glowny || k.echo) return; b.licznik = (b.licznik || 0) + 1; if (b.licznik % 4) return; dajTarcze(25 + 15 * b.tier + 0.2 * D.pancerz, 3); obszarowe(gracz.x, gracz.y, 80, '#e8e8f0', o => odrzuc(o, 30), true); },
  },
  topor: {
    nazwa: 'Topór', ikona: '🪓', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.05, zasieg: 70, obr: 33, skal: { ad: 1.21, hpMax: 0.022 }, luk: 2.1,
    opisEf: t => 'Krwawienie: <b>' + (40 + 10 * t) + '%</b> obrażeń przez 2,5 s · krwawienie leczy Cię o 20% swoich obrażeń.',
    naTrafienie(w, b, k) { krwawienie(w, k.bazowe * (0.40 + 0.10 * b.tier) / 2.5, 2.5, true); },
  },
  mlot: {
    nazwa: 'Młot', ikona: '🔨', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.45, zasieg: 70, obr: 54, skal: { ad: 1.416, hpMax: 0.047 }, luk: 2.6,
    opisEf: t => 'Szeroki zamach · ogłusza na <b>' + fmt(0.35 + 0.1 * t) + ' s</b> i odrzuca.',
    naTrafienie(w, b, k) { oglusz(w, 0.35 + 0.1 * b.tier, { zrodlo: 'Młot' }); odrzuc(w, 34); },
  },
  sztylety: {
    nazwa: 'Sztylety', ikona: '⚔️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.48, zasieg: 56, obr: 11, skal: { ad: 0.7, ms: 0.05 }, luk: 1.5, kryt: 12,
    opisEf: t => '+12% szansy na kryt · rozpędzają się: każdy cios +8% prędkości ataku, do <b>+' + (40 + 10 * t) + '%</b> (reset po 2 s przerwy).',
    przyAtaku(b) { b.rozped = Math.min(0.40 + 0.10 * b.tier, (b.rozped || 0) + 0.08); b.odCiosu = 0; },
    tempo(b) { return 1 + (b.rozped || 0); },
  },
  wlocznia: {
    nazwa: 'Włócznia', ikona: '🔱', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 0.9, zasieg: 112, obr: 19, skal: { ad: 0.817, ms: 0.069 }, rzut: true,
    opisEf: t => 'Pchnięcie trafia wszystkich w linii · co <b>' + (t >= 2 ? 3 : 4) + '.</b> atak rzut przebijającą włócznią (150% obrażeń).',
  },
  kastety: {
    nazwa: 'Kastety', ikona: '🥊', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.4, zasieg: 52, obr: 14, skal: { ad: 0.878, pancerz: 0.162, hpMax: 0.011 }, luk: 1.4,
    opisEf: t => 'Bardzo szybkie · co 4. cios ogłusza na <b>' + fmt(0.5 + 0.1 * t) + ' s</b>.',
    naTrafienie(w, b, k) { b.licznik = (b.licznik || 0) + (k.glowny ? 1 : 0); if (k.glowny && b.licznik % 4 === 0) oglusz(w, 0.5 + 0.1 * b.tier, { zrodlo: 'Kastety' }); odrzuc(w, 8); },
  },
  kosa: {
    nazwa: 'Kosa', ikona: '🌙', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.25, zasieg: 86, obr: 31, skal: { ad: 1.088, ap: 0.448 }, luk: Math.PI * 2,
    opisEf: t => 'Obrót o 360° · każdy trafiony wróg leczy Cię o <b>' + fmt(0.6 + 0.2 * t) + '%</b> maks. zdrowia (do 5 naraz).',
    naTrafienie(w, b, k) { if ((k.licznikCiosu || 0) <= 5) leczWampirem(D.hpMax * (0.003 + 0.001 * b.tier), 'Kosa'); },
  },
  lancuch: {
    nazwa: 'Łańcuch Więźnia', ikona: '⛓️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.0, zasieg: 98, obr: 24, skal: { ad: 0.9, ms: 0.1, hpMax: 0.01 }, luk: 2.6,
    opisEf: t => 'Długi zamach kulą na łańcuchu · trafieni są spowolnieni o <b>' + (20 + 5 * t) + '%</b>, a cel główny przyciągnięty bliżej.',
    naTrafienie(w, b, k) { spowolnij(w, 0.2 + 0.05 * b.tier, 1.2); if (k.glowny && !w.ciezki && !w.boss) { const kk = kat(w, gracz); w.kbx += Math.cos(kk) * 120; w.kby += Math.sin(kk) * 120; } },
  },

  // ======================= BROŃ STRZELECKA =======================
  luk: {
    nazwa: 'Łuk', ikona: '🎯', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.72, zasieg: 300, obr: 27, skal: { ad: 1.44, as: 0.24 }, dystans: true,
    predkosc: 590, ksztalt: 'strzala', kolor: '#e8d8b0', kryt: 10, krytObr: 25,
    opisEf: t => '+10% szansy na kryt, +25% obr. krytycznych' + (t >= 3 ? ' · <b>2 strzały</b> naraz' : ''),
  },
  kusza: {
    nazwa: 'Kusza', ikona: '🏹', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 1.5, zasieg: 330, obr: 52, skal: { ad: 1.296 }, dystans: true,
    predkosc: 680, ksztalt: 'belt', kolor: '#d8d0b0', przebija: 2, przebPanc: 25,
    opisEf: t => 'Bełt przebija <b>' + (2 + t) + '</b> wrogów · ignoruje 25% pancerza.',
  },
  bumerang: {
    nazwa: 'Bumerang', ikona: '🪃', rodz: 'strzelecka', atak: 'bumerang', obrTyp: 'fiz', cd: 1.2, zasieg: 215, obr: 19, skal: { ad: 0.722, ms: 0.085 }, dystans: true,
    opisEf: t => 'Leci i wraca, raniąc w obie strony' + (t >= 3 ? ' · rzuca <b>2</b> bumerangi' : '') + '.',
  },
  pistolet: {
    nazwa: 'Pistolet', ikona: '🔫', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.5, zasieg: 270, obr: 15, skal: { ad: 0.889, szczescie: 0.191 }, dystans: true,
    predkosc: 820, ksztalt: 'kula', kolor: '#ffe08a', kryt: 8,
    opisEf: t => 'Szybkie strzały · co <b>6.</b> strzał to <b>salwa ' + (3 + Math.floor(t / 2)) + ' kul</b> (każda 70% obrażeń).',
    przyAtaku(b) { b.licznikP = (b.licznikP || 0) + 1; },
  },
  muszkiet: {
    nazwa: 'Muszkiet Snajpera', ikona: '🎖️', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 2.2, zasieg: 455, obr: 88, skal: { ad: 1.488 }, dystans: true,
    predkosc: 1100, ksztalt: 'belt', kolor: '#fff0c0', przebija: 4, krytObr: 50, celDaleki: true,
    opisEf: t => 'Bardzo wolny, ogromne obrażenia · celuje w <b>najdalszego</b> wroga w zasięgu · przebija ' + (4 + t) + ' wrogów · +50% obr. krytycznych.',
  },
  gwozdziarka: {
    nazwa: 'Gwoździarka', ikona: '🔩', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.3, zasieg: 250, obr: 10, skal: { ad: 0.621, pancerz: 0.083 }, dystans: true,
    predkosc: 640, ksztalt: 'belt', kolor: '#c0c8d0', przebija: 1,
    opisEf: t => 'Seria gwoździ · każdy przebija 1 wroga · trafienia kruszą pancerz o <b>' + (3 + t) + '%</b> (do 30%).',
    naTrafienie(w, b) { w.krusz = Math.min(0.3, (w.krusz || 0) + 0.03 + 0.01 * b.tier); },
  },

  // ======================= BROŃ MAGICZNA =======================
  rozdzka: {
    nazwa: 'Różdżka', ikona: '🪄', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.8, zasieg: 290, obr: 24, skal: { ap: 1.152, ad: 0.192 }, dystans: true,
    predkosc: 410, ksztalt: 'kula', kolor: '#c58ae6', naprowadza: 3.5,
    opisEf: t => 'Lekko naprowadzany pocisk' + (t >= 1 ? ' · odbija się do <b>' + (t >= 3 ? 2 : 1) + '</b> kolejnych wrogów' : '') + '.',
    odbicia: t => (t >= 3 ? 2 : (t >= 1 ? 1 : 0)),
  },
  rozdzkaOgnia: {
    nazwa: 'Różdżka Ognia', ikona: '🔥', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.1, zasieg: 265, obr: 20, skal: { ap: 0.8 }, dystans: true,
    predkosc: 380, ksztalt: 'kula', kolor: '#ff7a3c',
    opisEf: t => 'Wybucha (r 58): <b>50%</b> obrażeń wokół i podpala na 3 s (<b>' + (25 + 5 * t) + '%</b> obr./s).',
    naTrafienie(w, b, k) {
      if (!k.glowny) return;
      const dps = k.bazowe * (0.25 + 0.05 * b.tier);
      podpal(w, dps, 3, 'mag', 'Różdżka Ognia');
      obszarowe(w.x, w.y, 58, '#ff8a3a', o => { if (o !== w) { zadaj(o, k.bazowe * 0.5, 'mag', { obszar: true, zr: 'Różdżka Ognia' }); podpal(o, dps, 3, 'mag', 'Różdżka Ognia'); } });
    },
  },
  rozdzkaPior: {
    nazwa: 'Różdżka Piorunów', ikona: '⚡', rodz: 'magiczna', atak: 'piorun', obrTyp: 'mag', cd: 0.72, zasieg: 220, obr: 18, skal: { ap: 0.9, as: 0.15 }, dystans: true,
    opisEf: t => 'Natychmiastowa błyskawica · przeskakuje na <b>' + (3 + t) + '</b> kolejnych wrogów (−25% za skok).',
  },
  rozdzkaZimy: {
    nazwa: 'Różdżka Zimy', ikona: '❄️', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.0, zasieg: 265, obr: 15, skal: { ap: 0.72, odpMag: 0.18 }, dystans: true,
    predkosc: 380, ksztalt: 'kula', kolor: '#a8e0f5',
    opisEf: t => 'Wybuch mrozu (r 60): <b>60%</b> obrażeń wokół i spowolnienie <b>' + (30 + 5 * t) + '%</b> · zostawia lodowe pole.',
    naTrafienie(w, b, k) {
      if (!k.glowny) return;
      const sp = 0.30 + 0.05 * b.tier;
      spowolnij(w, sp, 2);
      obszarowe(w.x, w.y, 60, '#8fd0ff', o => { if (o !== w) { zadaj(o, k.bazowe * 0.6, 'mag', { obszar: true, zr: 'Różdżka Zimy' }); spowolnij(o, sp, 2); } });
      polaEfektow.push({ wl: gracz, x: w.x, y: w.y, r: 70 * mnObszaru(), czas: 2.5, max: 2.5, tyk: 0.5, rodzaj: 'mroz', obr: k.bazowe * 0.12, zr: 'Różdżka Zimy' });
    },
  },
  kosturPustki: {
    nazwa: 'Kostur Pustki', ikona: '🔮', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.3, zasieg: 280, obr: 26, skal: { ap: 0.9 }, dystans: true,
    predkosc: 330, ksztalt: 'pustka', kolor: '#9a6aff', przebija: 99,
    opisEf: t => 'Kula przelatuje przez wszystkich · dodatkowo <b>' + (20 + 5 * t) + '%</b> obrażeń jako prawdziwe.',
    naTrafienie(w, b, k) { zadaj(w, k.bazowe * (0.20 + 0.05 * b.tier), 'praw', { zr: 'Kostur Pustki' }); },
  },
  kosturKosci: {
    nazwa: 'Kostur Kości', ikona: '🦴', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.95, zasieg: 275, obr: 32, skal: { ap: 1.2, hpMax: 0.024 }, dystans: true,
    predkosc: 420, ksztalt: 'kosc', kolor: '#e8f0ff',
    opisEf: t => 'Zabici tym kosturem wrogowie mają <b>' + (10 + 4 * t) + '%</b> szansy powstać jako Twój szkielet na 8 s.',
    naZabicie(w, b) { if (!w.boss && !w.sojusznik && Math.random() < 0.10 + 0.04 * b.tier) wskrzesSojusznika(w); },
  },
  kosturNatury: {
    nazwa: 'Kostur Natury', ikona: '🌿', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.9, zasieg: 275, obr: 31, skal: { ap: 1.19, hpMax: 0.035 }, dystans: true,
    predkosc: 430, ksztalt: 'kolec', kolor: '#7ee87a',
    opisEf: t => 'Ciernie oplątują (spowolnienie 40% na 0,8 s) · co 5. trafienie leczy Cię o <b>' + (2 + t) + '%</b> maks. zdrowia.',
    naTrafienie(w, b, k) { spowolnij(w, 0.4, 0.8); if (!k.glowny) return; b.licznik = (b.licznik || 0) + 1; if (b.licznik % 5 === 0) leczGracza(D.hpMax * (0.02 + 0.01 * b.tier), 'Kostur Natury'); },
  },

  // ======================= ALCHEMIA =======================
  granatnik: {
    nazwa: 'Granatnik', ikona: '🧨', rodz: 'alchemia', atak: 'granat', obrTyp: 'fiz', cd: 1.35, zasieg: 245, obr: 26, skal: { ad: 0.602, ap: 0.43 }, dystans: true,
    promien: 68, kolor: '#ffb070',
    opisEf: t => 'Granat wybucha w miejscu celu (r <b>' + (68 + 6 * t) + '</b>) i rani wszystkich w zasięgu wybuchu.',
  },
  // ---- nowe bronie ----
  kosci: {
    nazwa: 'Kości do gry', ikona: '🎲', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.6, zasieg: 275, obr: 25, skal: { ad: 1.012, szczescie: 0.562 }, dystans: true,
    predkosc: 520, ksztalt: 'kula', kolor: '#f0f0f0',
    opisEf: t => 'Słabe, ale losowe: każdy rzut to <b>1–6</b> oczek (obrażenia ×oczka/3,5). Szóstka trafia za <b>×' + fmt(2.4 + 0.2 * t) + '</b>.',
    mnTrafienia(b, w, o) { if (!o.glowny) return 1; const r = 1 + Math.floor(Math.random() * 6); if (r === 6) { tekstSwiat(w.x, w.y - w.r - 14, '🎲 6!', '#ffe08a', 0.6, 12); return 2.4 + 0.2 * b.tier; } return r / 3.5; },
  },
  katana: {
    nazwa: 'Katana', ikona: '🗡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.75, zasieg: 72, obr: 23, skal: { ad: 1.035, kryt: 0.46 }, luk: 1.9, kryt: 15, krytObr: 25,
    opisEf: t => '+15% szansy na kryt, krytyki +25% · <b>trafienie krytyczne nakłada efekty <span class="onhit">on-hit</span> ' + (t >= 3 ? '3 razy' : '2 razy') + '</b>.',
    naTrafienie(w, b, k) { if (k.kryt && k.glowny && !w.martwy) zastosujOnHit(w, b, { razy: b.tier >= 3 ? 2 : 1 }); },
  },
  halabarda: {
    nazwa: 'Halabarda', ikona: '⚜️', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 1.15, zasieg: 140, obr: 34, skal: { ad: 1.0, pancerz: 0.25 }, przebPanc: 30,
    opisEf: t => 'Długie pchnięcie przez całą linię · ignoruje 30% pancerza · skaluje się z Twoim pancerzem · wrogowie dostają <b>' + (10 + 3 * t) + '%</b> więcej obrażeń przez 3 s.',
    naTrafienie(w, b, k) { w.naznaczony = Math.max(w.naznaczony || 0, 3); w.mnNazn = Math.max(w.mnNazn || 0, 0.10 + 0.03 * b.tier); },
  },
  buzdygan: {
    nazwa: 'Buzdygan', ikona: '🏏', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.1, zasieg: 64, obr: 40, skal: { ad: 1.12, hpMax: 0.022 }, luk: 1.6,
    opisEf: t => 'Ciężkie uderzenia: <b>' + (15 + 5 * t) + '%</b> szansy na ogłuszenie (0,8 s) · <b>+' + (30 + 10 * t) + '%</b> obrażeń elitom i bossom.',
    mnTrafienia(b, w) { return (w.elita || w.boss) ? 1.3 + 0.1 * b.tier : 1; },
    naTrafienie(w, b, k) { if (k.glowny && Math.random() < 0.15 + 0.05 * b.tier) oglusz(w, 0.8, { zrodlo: 'Buzdygan' }); },
  },
  lukDlugi: {
    nazwa: 'Łuk Długi', ikona: '🎯', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 1.7, zasieg: 410, obr: 58, skal: { ad: 1.35 }, dystans: true, celDaleki: true,
    predkosc: 900, ksztalt: 'strzala', kolor: '#f0e0b0', przebija: 3, kryt: 10, krytObr: 40,
    opisEf: t => 'Snajperski: celuje w <b>najdalszego</b> wroga, przebija ' + (3 + t) + ' wrogów, krytyki +40% · im dalej leci, tym mocniej (do +' + (30 + 10 * t) + '%).',
    mnTrafienia(b, w) { const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); return 1 + Math.min(1, d / 340) * (0.3 + 0.1 * b.tier); },
  },
  ksiegaZaklec: {
    nazwa: 'Księga Zaklęć', ikona: '📕', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.1, zasieg: 300, obr: 11, skal: { ap: 0.504, haste: 0.252 }, dystans: true,
    predkosc: 360, ksztalt: 'kula', kolor: '#ff8ab0', naprowadza: 6, dodPociski: 2, rozrzut: 0.5,
    opisEf: t => 'Wystrzeliwuje <b>' + (3 + Math.floor(t / 2)) + '</b> naprowadzanych pocisków naraz (każdy 100% obrażeń) · skaluje się z ⏱️ przyspieszeniem.',
    dodPociskiT: t => 2 + Math.floor(t / 2), pelnePociski: true,
  },
  berloSlonca: {
    nazwa: 'Berło Słońca', ikona: '☀️', rodz: 'magiczna', atak: 'granat', obrTyp: 'mag', cd: 1.45, zasieg: 250, obr: 21, skal: { ap: 0.7 }, dystans: true,
    promien: 72, kolor: '#ffd24a',
    opisEf: t => 'Słoneczny wybuch w miejscu celu (r <b>' + (72 + 6 * t) + '</b>) · podpala trafionych na 2 s (<b>' + (20 + 6 * t) + '%</b> obr./s).',
    naTrafienie(w, b, k) { podpal(w, k.bazowe * (0.2 + 0.06 * b.tier), 2, 'mag', 'Berło Słońca'); },
  },
  kwasomiot: {
    nazwa: 'Kwasomiot', ikona: '🧪', rodz: 'alchemia', atak: 'stozek', obrTyp: 'fiz', cd: 0.4, zasieg: 115, obr: 7, skal: { ad: 0.315, ap: 0.225 }, dystans: false,
    pol: 0.38, kolor: '#9aff5a',
    opisEf: t => 'Strumień kwasu w stożku · <b>rozpuszcza pancerz</b>: każde trafienie −4% pancerza i odporności celu (do −' + (40 + 5 * t) + '%).',
    naTrafienie(w, b, k) { w.krusz = Math.min(0.40 + 0.05 * b.tier, (w.krusz || 0) + 0.04); },
  },
  miotaczOgnia: {
    nazwa: 'Miotacz Ognia', ikona: '🌋', rodz: 'alchemia', atak: 'stozek', obrTyp: 'mag', cd: 0.35, zasieg: 125, obr: 6, skal: { ap: 0.252, ad: 0.18 }, dystans: false,
    pol: 0.42, kolor: '#ff8a3a',
    opisEf: t => 'Strumień ognia w stożku · podpala na 2 s (<b>' + (30 + 8 * t) + '%</b> obr./s).',
    naTrafienie(w, b, k) { podpal(w, k.bazowe * (0.30 + 0.08 * b.tier), 2, 'mag', 'Miotacz Ognia'); },
  },
  // ======================= NOWE BRONIE =======================
  glewia: {
    nazwa: 'Glewia Piorunów', ikona: '⚡', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.0, zasieg: 92, obr: 24, skal: { ad: 0.85, ap: 0.35 }, luk: 2.4, energia: true,
    opisEf: t => 'Szeroki zamach · ⚡ <b>naładowany cios</b> (energia z biegania i ciosów) puszcza łańcuch piorunów na <b>' + (3 + t) + '</b> wrogów: 70% obrażeń ciosu (magiczne).',
    naNaladowanym(b, cel) { if (cel.wirtualny || cel.martwy) return; lancuch(gracz, cel, obrBroni(b) * 0.7, 'mag', 3 + b.tier, 170, 1, 'Glewia Piorunów'); },
  },
  batPogromcy: {
    nazwa: 'Bat Pogromcy', ikona: '🪢', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 0.85, zasieg: 165, obr: 24, skal: { ad: 1.125, as: 0.15 }, szer: 14,
    opisEf: t => 'Długie smagnięcie przez linię · wrogowie na <b>końcu bata</b> (ostatnia 1/3 zasięgu) dostają <b>+' + (40 + 10 * t) + '%</b> obrażeń.',
    mnTrafienia(b, w) { const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); return d > zasiegAtaku(b) * 0.66 ? 1.4 + 0.1 * b.tier : 1; },
  },
  szpada: {
    nazwa: 'Szpada', ikona: '🤺', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 0.6, zasieg: 96, obr: 14, skal: { ad: 0.8, kryt: 0.3 }, kryt: 20, szer: 12,
    opisEf: t => 'Bardzo szybkie pchnięcia · +20% szansy na kryt · co <b>4.</b> pchnięcie trafia w punkt witalny: <b>pewny kryt</b> i dodatkowo <b>' + (40 + 10 * t) + '%</b> tego trafienia jako obrażenia prawdziwe.',
    przyAtaku(b) { b.licznikW = (b.licznikW || 0) + 1; b._wital = b.licznikW % 4 === 0; if (b._wital) gracz.stanKlasy.pewnyKryt = true; },
    naTrafienie(w, b, k) { if (!k.glowny || !b._wital || w.martwy) return; b._wital = false; zadaj(w, k.zadaneSurowe * (0.4 + 0.1 * b.tier), 'praw', { zr: 'Szpada' }); efektBlysk(w.x, w.y, '#fff6c0'); },
  },
  puklerz: {
    nazwa: 'Puklerz', ikona: '🛡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.1, zasieg: 62, obr: 37, skal: { ad: 0.85, pancerz: 0.85, hpMax: 0.043 }, luk: 1.8,
    opisEf: t => 'Uderzenie tarczą: odrzuca i ogłusza cel na 0,3 s · każde uderzenie daje tarczę <b>' + fmt(1.5 + 0.5 * t) + '%</b> maks. zdrowia (2 s, najwyżej 4 naraz) · skaluje się z pancerzem i zdrowiem.',
    naTrafienie(w, b, k) { if (!k.glowny) return; oglusz(w, 0.3, { zrodlo: 'Puklerz' }); odrzuc(w, 24);
      if (gracz.tarcze.filter(x => x.puklerz).length < 4) { dajTarcze(D.hpMax * (0.015 + 0.005 * b.tier), 2); gracz.tarcze[gracz.tarcze.length - 1].puklerz = 1; } },
  },
  czakram: {
    nazwa: 'Czakram', ikona: '🥏', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.95, zasieg: 260, obr: 25, skal: { ad: 1.163, kryt: 0.775 }, dystans: true,
    predkosc: 560, ksztalt: 'czakram', kolor: '#e0e8f0', kryt: 10, odbicia: t => 2 + t, bezSpadku: true, zasiegOdbicia: 200,
    opisEf: t => 'Odbija się między <b>' + (3 + t) + '</b> wrogami <b>bez utraty siły</b> · +10% szansy na kryt · skaluje się z szansą na kryt.',
  },
  noze: {
    nazwa: 'Noże do Rzucania', ikona: '🔪', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.85, zasieg: 235, obr: 12, skal: { ad: 0.7, kryt: 0.25 }, dystans: true,
    predkosc: 640, ksztalt: 'noz', kolor: '#d8d8e4', kryt: 10, krytObr: 20, rozrzut: 0.22, dodPociskiT: t => 2 + Math.floor(t / 2),
    opisEf: t => 'Wachlarz <b>' + (3 + Math.floor(t / 2)) + '</b> noży (każdy kolejny 60% obrażeń) · +10% szansy na kryt, krytyki +20%.',
  },
  kosturGromu: {
    nazwa: 'Kostur Gromu', ikona: '🌩️', rodz: 'magiczna', atak: 'grom', obrTyp: 'mag', cd: 1.25, zasieg: 280, obr: 26, skal: { ap: 0.828 }, dystans: true, promien: 55, energia: true,
    opisEf: t => 'Piorun z nieba w miejsce celu (r <b>' + (55 + 5 * t) + '</b>) · ⚡ <b>naładowany</b>: dodatkowo <b>' + (2 + Math.floor(t / 2)) + '</b> pioruny w pobliskich wrogów (60% obrażeń).',
    naNaladowanym(b, cel) { const ile = 2 + Math.floor(b.tier / 2); najblizsi(cel.x, cel.y, 220, ile, [cel]).forEach((w, n) => opoznione(0.08 * (n + 1), () => { if (stan === 'walka' && !w.martwy) uderzGromem(b, w.x, w.y, w, 0.6); })); },
  },
  widly: {
    nazwa: 'Widły', ikona: '🔱', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 0.95, zasieg: 104, obr: 17, skal: { ad: 0.85, hpMax: 0.012 }, szer: 22,
    opisEf: t => 'Szerokie pchnięcie trzema zębami · zabici widłami wrogowie zostawiają <b>+' + (30 + 10 * t) + '%</b> doświadczenia więcej.',
    naZabicie(w, b) { if (!w.bezLupu && !w.sojusznik) rozsypKulki(w.x, w.y, w.xp * (0.3 + 0.1 * b.tier)); },
  },
  kule: {
    nazwa: 'Krążące Kule', ikona: '🪐', rodz: 'magiczna', atak: 'orbita', obrTyp: 'mag', cd: 0.5, zasieg: 72, obr: 15, skal: { ap: 0.56, hpMax: 0.011 },
    opisEf: t => '<b>' + (2 + t) + '</b> kule krążą wokół Ciebie i ranią każdego, kogo dotkną (ten sam wróg co 0,5 s — szybciej z prędkością ataku) · zasięg = promień orbity · dobre do walki wręcz.',
  },
};
const KLUCZE_BRONI = Object.keys(BRONIE);

function nowaBron(rodzaj, tier) { return { rodzaj: rodzaj, tier: tier || 0, cd: Math.random() * 0.4, licznik: 0 }; }
function nazwaBroni(b) { return BRONIE[b.rodzaj].nazwa + ' ' + TIERY[b.tier].rz; }
function obrBroni(b) {
  const B = BRONIE[b.rodzaj];
  let v = B.obr * MN_BRONI[b.tier];
  for (const k in B.skal) v += B.skal[k] * (k === 'zloto' ? gracz.zloto : (k === 'ad' && FLAGI.wszystkoMag) ? D.ap : (D[k] || 0));   // Kostur Arcymaga: przelicznik ⚔️ liczy się od ✨
  const kl = KLASY[gracz.klasa];
  if (kl && kl.mnBroni) v *= kl.mnBroni(B, b);
  v *= (FLAGI.mnGlownej || 1) * (1 + (FLAGI.mnGlownejAug || 0)) * ((b.ewo || 0) >= 1 ? 1.2 : 1) * (1 + 0.15 * (b.mistrz || 0));
  return Math.max(1, v);
}
// faktyczny odstęp między atakami (z prędkością ataku)
function odstepAtaku(b) { const B = BRONIE[b.rodzaj]; const t = ogr((1 + D.as / 100) * (B.tempo ? B.tempo(b) : 1), 0.2, B.cd / 0.1); return B.cd / t; }
function zasiegBroni(b) {
  const B = BRONIE[b.rodzaj];
  const premia = D.zasieg / 100 * (B.dystans ? 1 : 0.5);
  return B.zasieg * Math.max(0.4, 1 + premia) * ((b.ewo || 0) >= 2 ? 1.15 : 1);
}
function opisSkalowania(B) {
  return Object.keys(B.skal).map(k => {
    const v = B.skal[k];
    if (k === 'hpMax') return fmt(v * 100) + '% ' + IKONY_SKAL[k];
    return Math.round(v * 100) + '% ' + (IKONY_SKAL[k] || k);
  }).join(' + ');
}
function opisBroni(b, krotki) {
  const B = BRONIE[b.rodzaj];
  const typ = B.obrTyp === 'mag' ? '<span class="mag">magiczne</span>' : '<span class="fiz">fizyczne</span>';
  let s = '<b>' + Math.round(B.obr * MN_BRONI[b.tier]) + '</b> ' + typ + ' + ' + opisSkalowania(B) + ' · co <b>' + fmt(B.cd) + ' s</b> · zasięg ' + B.zasieg;
  if (!krotki && typeof D !== 'undefined' && D && gracz) s += '<br>Teraz: <b>' + Math.round(obrBroni(b)) + '</b> obrażeń na trafienie';
  s += '<br>' + B.opisEf(b.tier);
  s += '<br><span class="tag">' + RODZINY[B.rodz].ik + ' ' + RODZINY[B.rodz].n + '</span>';
  return s;
}
function cenaUlepszeniaGlownej(b) { const K = KLASY[gracz.klasa]; return Math.round(CENA_ULEPSZ_BRONI[b.tier] * mnCeny() * (1 - (K.rabatBroni || 0))); }

// ---------- rysowanie broni (wektorowo, ostrze w prawo) ----------
function rysujKsztaltBroni(c, b) {
  if (!b) return;
  const kol = TIERY[b.tier].kolor, drewno = '#6b4a2a', metal = '#d8d8e4', ciemny = '#3a3a46';
  function ostrze(dl, szer, k) {
    c.fillStyle = k; c.beginPath(); c.moveTo(0, -szer / 2); c.lineTo(dl - szer * 0.9, -szer / 2); c.lineTo(dl, 0);
    c.lineTo(dl - szer * 0.9, szer / 2); c.lineTo(0, szer / 2); c.closePath(); c.fill();
  }
  function rozdzkaZKrysztalem(kk, okragly) {
    c.fillStyle = drewno; c.fillRect(-9, -1.5, 20, 3);
    c.save(); c.translate(15, 0); c.fillStyle = kk; c.globalAlpha = 0.35; c.beginPath(); c.arc(0, 0, 8, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1; c.beginPath();
    if (okragly) c.arc(0, 0, 5.5, 0, Math.PI * 2); else { c.moveTo(0, -5.5); c.lineTo(5, 0); c.lineTo(0, 5.5); c.lineTo(-5, 0); c.closePath(); }
    c.fill(); c.restore(); c.fillStyle = kol; c.fillRect(8, -2.2, 3, 4.4);
  }
  switch (b.rodzaj) {
    case 'miecz':
      c.fillStyle = drewno; c.fillRect(-8, -1.6, 7, 3.2); c.fillStyle = kol; c.fillRect(-1.5, -5, 3, 10);
      ostrze(20, 5, metal); c.fillStyle = kol; c.fillRect(2, -0.7, 15, 1.4); break;
    case 'mieczTarcza':
      c.fillStyle = drewno; c.fillRect(-8, -1.6, 7, 3.2); c.fillStyle = kol; c.fillRect(-1.5, -5, 3, 10); ostrze(18, 4.6, metal);
      c.fillStyle = '#5a4a8a'; c.beginPath(); c.moveTo(-6, -12); c.lineTo(2, -12); c.lineTo(2, -4); c.quadraticCurveTo(-2, 1, -6, -4); c.closePath(); c.fill();
      c.fillStyle = kol; c.fillRect(-3, -10, 2, 5); break;
    case 'topor':
      c.fillStyle = drewno; c.fillRect(-9, -1.8, 20, 3.6); c.fillStyle = metal; c.beginPath();
      c.moveTo(7, -2); c.lineTo(17, -10); c.lineTo(21, -1); c.lineTo(21, 1); c.lineTo(17, 10); c.lineTo(7, 2); c.closePath(); c.fill();
      c.fillStyle = kol; c.fillRect(6, -3, 3, 6); break;
    case 'mlot':
      c.fillStyle = drewno; c.fillRect(-9, -2, 19, 4); c.fillStyle = ciemny; c.fillRect(9, -9, 11, 18); c.fillStyle = kol; c.fillRect(17, -9, 3, 18); break;
    case 'sztylety':
      c.fillStyle = drewno; c.fillRect(-6, -3.6, 5, 2.4); c.fillRect(-6, 1.2, 5, 2.4);
      c.save(); c.translate(0, -2.4); ostrze(12, 3.4, metal); c.restore(); c.save(); c.translate(0, 2.4); ostrze(12, 3.4, metal); c.restore(); break;
    case 'wlocznia':
      c.fillStyle = drewno; c.fillRect(-12, -1.7, 30, 3.4); c.fillStyle = kol; c.fillRect(15, -2.6, 3, 5.2);
      c.save(); c.translate(18, 0); ostrze(11, 5.6, metal); c.restore(); break;
    case 'lancuch':
      c.strokeStyle = '#9a9aa8'; c.lineWidth = 1.6; for (let i = 0; i < 4; i++) { c.beginPath(); c.ellipse(-4 + i * 5, 0, 3, 1.8, 0, 0, Math.PI * 2); c.stroke(); }
      c.fillStyle = ciemny; c.beginPath(); c.arc(19, 0, 6, 0, Math.PI * 2); c.fill(); c.fillStyle = kol; c.beginPath(); c.arc(17.5, -1.5, 1.8, 0, Math.PI * 2); c.fill(); break;
    case 'kusza':
      c.fillStyle = drewno; c.fillRect(-10, -2, 22, 4); c.strokeStyle = ciemny; c.lineWidth = 2.4;
      c.beginPath(); c.moveTo(8, -11); c.lineTo(13, 0); c.lineTo(8, 11); c.stroke();
      c.strokeStyle = '#e8e0c8'; c.lineWidth = 1; c.beginPath(); c.moveTo(8, -11); c.lineTo(2, 0); c.lineTo(8, 11); c.stroke();
      c.fillStyle = kol; c.fillRect(-10, -2, 5, 4); break;
    case 'luk':
      c.strokeStyle = drewno; c.lineWidth = 3; c.beginPath(); c.arc(-2, 0, 13, -1.25, 1.25); c.stroke();
      c.strokeStyle = '#e8e0c8'; c.lineWidth = 1; c.beginPath(); c.moveTo(2.1, -12.3); c.lineTo(2.1, 12.3); c.stroke();
      c.fillStyle = kol; c.fillRect(8, -2, 3, 4); break;
    case 'bumerang':
      c.strokeStyle = kol; c.lineWidth = 4.5; c.lineCap = 'round'; c.beginPath(); c.moveTo(-6, -9); c.lineTo(6, 0); c.lineTo(-6, 9); c.stroke(); c.lineCap = 'butt'; break;
    case 'pistolet':
      c.fillStyle = drewno; c.beginPath(); c.moveTo(-6, -1); c.lineTo(-2, -1); c.lineTo(-1, 7); c.lineTo(-6, 7); c.closePath(); c.fill();
      c.fillStyle = ciemny; c.fillRect(-6, -4, 20, 4.5); c.fillStyle = kol; c.fillRect(10, -4, 4, 2); break;
    case 'muszkiet':
      c.fillStyle = drewno; c.fillRect(-12, -2, 16, 4); c.beginPath(); c.moveTo(-12, -2); c.lineTo(-16, 4); c.lineTo(-10, 2); c.closePath(); c.fill();
      c.fillStyle = ciemny; c.fillRect(2, -1.6, 22, 2.6); c.fillStyle = kol; c.fillRect(-2, -4, 6, 2); break;
    case 'gwozdziarka':
      c.fillStyle = '#e6a03c'; c.fillRect(-6, -5, 14, 9); c.fillStyle = ciemny; c.fillRect(8, -2, 8, 4); c.fillRect(-4, 4, 4, 6); c.fillStyle = kol; c.fillRect(-6, -5, 3, 9); break;
    case 'kastety':
      c.fillStyle = metal; c.fillRect(-4, -7, 9, 14); c.fillStyle = kol;
      for (let i = 0; i < 4; i++) { c.beginPath(); c.arc(6, -5.2 + i * 3.5, 1.8, 0, Math.PI * 2); c.fill(); } break;
    case 'kosa':
      c.fillStyle = drewno; c.fillRect(-12, -1.6, 28, 3.2); c.fillStyle = metal; c.beginPath();
      c.moveTo(14, -1.6); c.quadraticCurveTo(10, -16, -4, -17); c.quadraticCurveTo(6, -11, 10, -1.6); c.closePath(); c.fill();
      c.fillStyle = kol; c.fillRect(12, -2.5, 3, 5); break;
    case 'granatnik':
      c.fillStyle = drewno; c.fillRect(-10, -2.5, 12, 5); c.fillStyle = '#4a5a3a'; c.fillRect(0, -4.5, 16, 9); c.fillStyle = '#2a2a2a'; c.beginPath(); c.arc(16, 0, 4.5, 0, Math.PI * 2); c.fill();
      c.fillStyle = kol; c.fillRect(4, -4.5, 3, 9); break;
    case 'miotaczOgnia':
      c.fillStyle = '#8a3a2a'; c.fillRect(-10, -4, 10, 8); c.fillStyle = ciemny; c.fillRect(0, -2, 16, 4); c.fillStyle = '#ff8a3a'; c.beginPath(); c.arc(18, 0, 2.5 + Math.random() * 1.5, 0, Math.PI * 2); c.fill();
      c.fillStyle = kol; c.fillRect(-10, -4, 3, 8); break;
    case 'kosturKosci':
      c.fillStyle = '#d8d0c0'; c.fillRect(-10, -1.5, 22, 3); rysujIk(c, '💀', 16, 0, 11); break;
    case 'kosturNatury':
      c.fillStyle = '#5a3a1a'; c.fillRect(-10, -1.6, 22, 3.2); c.fillStyle = '#5ac46a'; c.beginPath(); c.ellipse(15, -4, 5, 2.5, -0.6, 0, Math.PI * 2); c.ellipse(16, 3, 4.5, 2.2, 0.6, 0, Math.PI * 2); c.fill();
      c.fillStyle = kol; c.fillRect(8, -2.2, 3, 4.4); break;
    case 'rozdzkaOgnia': rozdzkaZKrysztalem('#ff7a3c'); break;
    case 'rozdzkaZimy': rozdzkaZKrysztalem('#7ec4e8'); break;
    case 'rozdzkaPior': rozdzkaZKrysztalem('#ffe066'); break;
    case 'kosturPustki': rozdzkaZKrysztalem('#9a6aff', true); break;
    case 'katana':
      c.fillStyle = '#2a2230'; c.fillRect(-11, -1.7, 9, 3.4); c.fillStyle = '#c8b070'; for (let i = 0; i < 3; i++) c.fillRect(-10 + i * 3, -1.7, 1.2, 3.4);
      c.fillStyle = kol; c.beginPath(); c.ellipse(-1.5, 0, 1.6, 4.4, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = metal; c.beginPath(); c.moveTo(0, -1.6); c.quadraticCurveTo(13, -3.6, 26, -5.4); c.lineTo(23.5, -1.2); c.quadraticCurveTo(12, 0.6, 0, 1.6); c.closePath(); c.fill();
      c.strokeStyle = 'rgba(255,255,255,0.7)'; c.lineWidth = 0.7; c.beginPath(); c.moveTo(1, -1.1); c.quadraticCurveTo(13, -3, 24, -4.8); c.stroke(); break;
    case 'halabarda':
      c.fillStyle = drewno; c.fillRect(-14, -1.6, 34, 3.2); c.fillStyle = metal;
      c.beginPath(); c.moveTo(14, -1.6); c.lineTo(15, -10); c.quadraticCurveTo(22, -8, 23, -1.6); c.closePath(); c.fill();
      c.beginPath(); c.moveTo(20, -1.4); c.lineTo(30, 0); c.lineTo(20, 1.4); c.closePath(); c.fill();
      c.beginPath(); c.moveTo(16, 1.6); c.lineTo(18, 6); c.lineTo(20, 1.6); c.closePath(); c.fill(); c.fillStyle = kol; c.fillRect(12, -2.4, 2.5, 4.8); break;
    case 'buzdygan':
      c.fillStyle = drewno; c.fillRect(-9, -1.8, 18, 3.6); c.fillStyle = kol; c.fillRect(-9, -2.4, 3, 4.8);
      c.fillStyle = ciemny; c.beginPath(); c.arc(14, 0, 6, 0, Math.PI * 2); c.fill(); c.fillStyle = metal;
      for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; c.beginPath(); c.moveTo(14 + Math.cos(a - 0.35) * 5, Math.sin(a - 0.35) * 5); c.lineTo(14 + Math.cos(a) * 9.5, Math.sin(a) * 9.5); c.lineTo(14 + Math.cos(a + 0.35) * 5, Math.sin(a + 0.35) * 5); c.closePath(); c.fill(); } break;
    case 'lukDlugi':
      c.strokeStyle = '#5a3a1a'; c.lineWidth = 3.4; c.beginPath(); c.arc(-6, 0, 18, -1.2, 1.2); c.stroke();
      c.strokeStyle = '#e8e0c8'; c.lineWidth = 1; c.beginPath(); c.moveTo(0.5, -16.8); c.lineTo(0.5, 16.8); c.stroke();
      c.fillStyle = kol; c.fillRect(10, -2, 3, 4); break;
    case 'kosci':
      [[2, -5, 0.3], [10, 3, -0.4]].forEach(([x, y, a]) => { c.save(); c.translate(x, y); c.rotate(a); c.fillStyle = '#f4f4f4'; c.fillRect(-4.5, -4.5, 9, 9); c.strokeStyle = kol; c.lineWidth = 1; c.strokeRect(-4.5, -4.5, 9, 9);
        c.fillStyle = '#c0392b'; [[-2, -2], [2, 2], [0, 0]].forEach(([dx, dy]) => { c.beginPath(); c.arc(dx, dy, 1.1, 0, Math.PI * 2); c.fill(); }); c.restore(); }); break;
    case 'ksiegaZaklec':
      c.fillStyle = '#7a2a4a'; c.fillRect(-2, -8, 16, 16); c.fillStyle = '#f4ead8'; c.fillRect(0, -7, 13, 14); c.fillStyle = '#ff8ab0'; c.fillRect(-2, -8, 3, 16);
      c.strokeStyle = '#c06090'; c.lineWidth = 0.8; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(3, -4 + i * 3); c.lineTo(11, -4 + i * 3); c.stroke(); } c.fillStyle = kol; c.fillRect(11, -8, 3, 3); break;
    case 'berloSlonca':
      c.fillStyle = '#c8a040'; c.fillRect(-10, -1.6, 22, 3.2); c.save(); c.translate(16, 0); c.fillStyle = '#ffd24a'; c.globalAlpha = 0.35; c.beginPath(); c.arc(0, 0, 9, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1;
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; c.beginPath(); c.moveTo(Math.cos(a) * 4, Math.sin(a) * 4); c.lineTo(Math.cos(a) * 8, Math.sin(a) * 8); c.strokeStyle = '#ffb030'; c.lineWidth = 1.6; c.stroke(); }
      c.beginPath(); c.arc(0, 0, 4.5, 0, Math.PI * 2); c.fill(); c.restore(); c.fillStyle = kol; c.fillRect(8, -2.2, 3, 4.4); break;
    case 'kwasomiot':
      c.fillStyle = '#4a6a2a'; c.beginPath(); c.arc(-6, 0, 6.5, 0, Math.PI * 2); c.fill(); c.fillStyle = '#9aff5a'; c.beginPath(); c.arc(-6, 0, 3.5, 0, Math.PI * 2); c.fill();
      c.fillStyle = ciemny; c.fillRect(0, -2, 15, 4); c.fillStyle = '#9aff5a'; c.globalAlpha = 0.8; c.beginPath(); c.arc(17, 0, 2 + Math.random() * 1.2, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1;
      c.fillStyle = kol; c.fillRect(4, -2.6, 2.5, 5.2); break;
    case 'glewia':
      c.fillStyle = drewno; c.fillRect(-13, -1.6, 30, 3.2); c.fillStyle = metal;
      c.beginPath(); c.moveTo(15, -2); c.quadraticCurveTo(25, -9, 31, -2); c.quadraticCurveTo(26, 1, 15, 2); c.closePath(); c.fill();
      c.strokeStyle = '#9fe8ff'; c.lineWidth = 1.2; c.shadowColor = '#7ae0ff'; c.shadowBlur = 6; c.beginPath(); c.moveTo(18, -4); c.lineTo(22, -1); c.lineTo(20, 0); c.lineTo(26, 3); c.stroke(); c.shadowBlur = 0;
      c.fillStyle = kol; c.fillRect(13, -2.6, 2.5, 5.2); break;
    case 'batPogromcy':
      c.fillStyle = '#4a2a1a'; c.fillRect(-9, -1.8, 9, 3.6); c.fillStyle = kol; c.fillRect(-1, -2.2, 2, 4.4);
      c.strokeStyle = '#7a4a2a'; c.lineWidth = 1.8; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.bezierCurveTo(8, -9, 14, 8, 22, -2); c.quadraticCurveTo(26, -6, 29, -3); c.stroke(); c.lineCap = 'butt'; break;
    case 'szpada':
      c.fillStyle = drewno; c.fillRect(-9, -1.4, 7, 2.8); c.fillStyle = kol; c.beginPath(); c.arc(-1, 0, 4.4, -Math.PI / 2, Math.PI / 2); c.fill();
      c.fillStyle = metal; c.beginPath(); c.moveTo(0, -0.9); c.lineTo(26, -0.3); c.lineTo(27, 0); c.lineTo(26, 0.3); c.lineTo(0, 0.9); c.closePath(); c.fill(); break;
    case 'puklerz':
      c.fillStyle = '#6a5a3a'; c.beginPath(); c.arc(6, 0, 10, 0, Math.PI * 2); c.fill(); c.strokeStyle = kol; c.lineWidth = 2; c.stroke();
      c.fillStyle = metal; c.beginPath(); c.arc(6, 0, 3.4, 0, Math.PI * 2); c.fill(); break;
    case 'czakram':
      c.save(); c.translate(8, 0); c.rotate(Date.now() / 160); c.strokeStyle = metal; c.lineWidth = 2.6; c.beginPath(); c.arc(0, 0, 7.5, 0, Math.PI * 2); c.stroke();
      c.fillStyle = kol; for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2; c.beginPath(); c.moveTo(Math.cos(a) * 7, Math.sin(a) * 7); c.lineTo(Math.cos(a + 0.4) * 11, Math.sin(a + 0.4) * 11); c.lineTo(Math.cos(a + 0.5) * 7, Math.sin(a + 0.5) * 7); c.closePath(); c.fill(); } c.restore(); break;
    case 'noze':
      [-0.45, 0, 0.45].forEach(a => { c.save(); c.rotate(a); c.fillStyle = '#3a2a2a'; c.fillRect(-2, -1, 5, 2); ostrze(13, 3, metal); c.restore(); }); c.fillStyle = kol; c.fillRect(-3, -1.5, 2, 3); break;
    case 'kosturGromu':
      c.fillStyle = '#4a3a5a'; c.fillRect(-10, -1.6, 22, 3.2); c.save(); c.translate(16, 0); c.fillStyle = '#8a8aa0'; c.beginPath(); c.arc(-2, -1, 4.5, 0, Math.PI * 2); c.arc(2.5, -2, 4, 0, Math.PI * 2); c.arc(2, 2, 3.6, 0, Math.PI * 2); c.fill();
      c.strokeStyle = '#ffe066'; c.lineWidth = 1.5; c.shadowColor = '#ffe066'; c.shadowBlur = 6; c.beginPath(); c.moveTo(0, 2); c.lineTo(-2, 6); c.lineTo(1, 6); c.lineTo(-1, 10); c.stroke(); c.restore(); c.fillStyle = kol; c.fillRect(8, -2.2, 3, 4.4); break;
    case 'widly':
      c.fillStyle = drewno; c.fillRect(-12, -1.5, 26, 3); c.fillStyle = metal; c.fillRect(13, -6.5, 2.4, 13);
      [-5.5, 0, 5.5].forEach(y => { c.fillRect(14, y - 0.9, 10, 1.8); c.beginPath(); c.moveTo(24, y - 0.9); c.lineTo(27, y); c.lineTo(24, y + 0.9); c.fill(); }); c.fillStyle = kol; c.fillRect(10, -2, 2.5, 4); break;
    case 'kule':
      c.fillStyle = '#b48aff'; c.globalAlpha = 0.35; c.beginPath(); c.arc(6, 0, 8, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1; c.beginPath(); c.arc(6, 0, 4.6, 0, Math.PI * 2); c.fill();
      c.strokeStyle = kol; c.lineWidth = 1.4; c.beginPath(); c.ellipse(6, 0, 9, 3, -0.4, 0, Math.PI * 2); c.stroke(); break;
    default: rozdzkaZKrysztalem('#c58ae6');
  }
}

// =====================================================================
//  BRONIE DODATKOWE ("oręż") — jak przedmioty w LoL-u:
//  dają STATYSTYKI broni głównej i same od czasu do czasu coś odpalają:
//  co kilka sekund (skraca to Przyspieszenie) albo co N-ty atak broni głównej.
//  Tier I–IV: dwie takie same o tym samym tierze łączą się w wyższy.
// =====================================================================
const MS_ORE = [0.75, 1.2, 1.72, 2.3];    // mnożnik statystyk
const MO_ORE = [1, 1.6, 2.4, 3.4];        // mnożnik efektu
const CENA_ORE = [28, 62, 125, 215];
const MO = i => MO_ORE[i.tier || 0] * (1 + (FLAGI.mnOreza || 0));
function kryt2() { return 1.75 + D.krytObr / 100; }

const OREZE = [
  // ======================= MAGICZNE =======================
  { id: 'iskry', rodz: 'magiczna', ik: '✨', n: 'Różdżka Iskier', s: { ap: 14, as: 6 }, cd: 3,
    opis: i => 'Co <b>3 s</b> iskra przeskakuje po 3 wrogach: <span class="mag">' + f0((18 + 0.25 * D.ap) * MO(i)) + '</span> (18 + 25% ✨).',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 230); if (!c) return; cdUstaw(i, 3); lancuch(gracz, c, (18 + 0.25 * D.ap) * MO(i), 'mag', 3, 150, 0.9, 'Różdżka Iskier'); } },
  { id: 'kulaOgnia', rodz: 'magiczna', ik: '🔥', n: 'Kula Ognia', s: { ap: 16 }, cd: 4,
    opis: i => 'Co <b>4 s</b> kula ognia wybucha na wrogu (r 60): <span class="mag">' + f0((30 + 0.4 * D.ap) * MO(i)) + '</span> (30 + 40% ✨) i podpala.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 250); if (!c) return; cdUstaw(i, 4); const v = (30 + 0.4 * D.ap) * MO(i);
      wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 360, obr: v, typ: 'mag', kolor: '#ff7a3c', ksztalt: 'kula', zr: 'Kula Ognia', zycie: 1.2, naprowadza: 5, wybuch: { r: 60, obr: v * 0.7, podpal: v * 0.15 } }); DZ.magia(); } },
  { id: 'lodowaGwiazda', rodz: 'magiczna', ik: '❄️', n: 'Lodowa Gwiazda', s: { ap: 12, odpMag: 10 }, cd: 5,
    opis: i => 'Co <b>5 s</b> nowa mrozu wokół Ciebie (r 110): <span class="mag">' + f0((22 + 0.3 * D.ap) * MO(i)) + '</span> (22 + 30% ✨) i spowolnienie 35% na 2 s.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 110) === 0) return; cdUstaw(i, 5); aura(110, '#9fd8ff', w => { zadaj(w, (22 + 0.3 * D.ap) * MO(i), 'mag', { obszar: true, zr: 'Lodowa Gwiazda' }); spowolnij(w, 0.35, 2); }, true); } },
  { id: 'berloArkan', rodz: 'magiczna', ik: '🔮', n: 'Berło Arkan', s: { ap: 18, haste: 6 }, co: 5,
    opis: i => 'Co <b>5.</b> atak broni głównej: 3 naprowadzane pociski po <span class="mag">' + f0((12 + 0.15 * D.ap) * MO(i)) + '</span> (12 + 15% ✨).',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 5) return; for (let n = 0; n < 3; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, cel) + (n - 1) * 0.6, predkosc: 380, naprowadza: 7, cel: cel, obr: (12 + 0.15 * D.ap) * MO(i), typ: 'mag', kolor: '#c9a8ff', ksztalt: 'kula', zr: 'Berło Arkan', zycie: 1.5 }); } },
  { id: 'ksiegaMeteorow', rodz: 'magiczna', ik: '☄️', n: 'Księga Meteorów', s: { ap: 22 }, cd: 8,
    opis: i => 'Co <b>8 s</b> meteor spada na największe skupisko wrogów (r 85): <span class="mag">' + f0((60 + 0.7 * D.ap) * MO(i)) + '</span> (60 + 70% ✨).',
    tik(i) { if (!cdGotowe(i)) return; const c = skupisko(gracz.x, gracz.y, 320, 85); if (!c) return; cdUstaw(i, 8); meteoryt(c.x, c.y, 0.7, 85, (60 + 0.7 * D.ap) * MO(i), 'Księga Meteorów'); } },
  { id: 'krysztalowaKula', rodz: 'magiczna', ik: '🔵', n: 'Kryształowa Kula', s: { ap: 10, hpMax: 40 },
    opis: i => (i.tier >= 2 ? '2 kule krążą' : 'Kula krąży') + ' wokół Ciebie (r 70): <span class="mag">' + f0((12 + 0.22 * D.ap) * MO(i)) + '</span> (12 + 22% ✨) przy dotknięciu.',
    tik(i, dt) { orbitujace(i, dt, i.tier >= 2 ? 2 : 1, 70, '#7ac8ff', () => (12 + 0.22 * D.ap) * MO(i), 'mag', 'Kryształowa Kula'); } },
  { id: 'rozdzkaTrucizny', rodz: 'magiczna', ik: '🧪', n: 'Różdżka Trucizny', s: { ap: 12, przebMag: 5 }, cd: 4,
    opis: i => 'Co <b>4 s</b> trująca chmura na wrogu (r 65, 3 s): <span class="mag">' + f0((8 + 0.12 * D.ap) * MO(i)) + '</span> (8 + 12% ✨) co 0,5 s.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 240); if (!c) return; cdUstaw(i, 4); polaEfektow.push({ wl: gracz, x: c.x, y: c.y, r: 65 * mnObszaru(), czas: 3, max: 3, tyk: 0, rodzaj: 'trucizna', obr: (8 + 0.12 * D.ap) * MO(i), zr: 'Różdżka Trucizny' }); } },
  { id: 'kosturBurzy', rodz: 'magiczna', ik: '⛈️', n: 'Kostur Burzy', s: { ap: 16, as: 8 }, cd: 0.6,
    opis: i => 'Trafienia <b>krytyczne</b> przywołują piorun w cel i 2 sąsiadów: <span class="mag">' + f0((25 + 0.3 * D.ap) * MO(i)) + '</span> (25 + 30% ✨).',
    naKryt(i, w) { if (!cdGotowe(i)) return; cdUstaw(i, 0.6); lancuch({ x: w.x, y: w.y - 150 }, w, (25 + 0.3 * D.ap) * MO(i), 'mag', 3, 150, 1, 'Kostur Burzy'); } },
  { id: 'lampaDusz', rodz: 'magiczna', ik: '🏮', n: 'Lampa Dusz', s: { ap: 15, omni: 1 },
    opis: i => 'Zabity wróg ma 30% szansy uwolnić duszę: leci w najbliższego wroga, <span class="mag">' + f0((20 + 0.3 * D.ap) * MO(i)) + '</span> (20 + 30% ✨), a Ty leczysz się o ' + f0(4 * MO(i)) + '.',
    naZabicie(i, w) { if (Math.random() > 0.3) return; const c = najblizszyWrog(w.x, w.y, 260, [w]); leczGracza(4 * MO(i), 'Lampa Dusz', true); if (!c) return;
      wystrzel({ x: w.x, y: w.y, cel: c, predkosc: 330, naprowadza: 9, obr: (20 + 0.3 * D.ap) * MO(i), typ: 'mag', kolor: '#bff0ff', ksztalt: 'kula', zr: 'Lampa Dusz', zycie: 1.6 }); } },
  { id: 'pierscienPustki', rodz: 'magiczna', ik: '🌀', n: 'Pierścień Pustki', s: { ap: 20, przebMagP: 8 }, cd: 7,
    opis: i => 'Co <b>7 s</b> czarna dziura (r 130, 2 s) wciąga wrogów i co 0,5 s zadaje <span class="mag">' + f0((10 + 0.14 * D.ap) * MO(i)) + '</span> (10 + 14% ✨).',
    tik(i) { if (!cdGotowe(i)) return; const c = skupisko(gracz.x, gracz.y, 280, 120); if (!c) return; cdUstaw(i, 7); dodajStwora('dziura', c.x, c.y, 2, { obr: (10 + 0.14 * D.ap) * MO(i), zr: 'Pierścień Pustki', r: 130 * mnObszaru() }); } },

  // ======================= STRZELECKIE =======================
  { id: 'lukEcha', rodz: 'strzelecka', ik: '🎯', n: 'Łuk Echa', s: { ad: 10, kryt: 6 }, co: 4,
    opis: i => 'Co <b>4.</b> atak broni głównej: strzała przebijająca wszystkich na linii: <span class="fiz">' + f0((20 + 0.6 * D.ad) * MO(i)) + '</span> (20 + 60% ⚔️).',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 4) return; wystrzel({ x: gracz.x, y: gracz.y, cel: cel, predkosc: 640, obr: (20 + 0.6 * D.ad) * MO(i), typ: 'fiz', kolor: '#e8d8b0', ksztalt: 'strzala', zr: 'Łuk Echa', przebija: 99, zycie: 0.8 }); } },
  { id: 'kuszaObl', rodz: 'strzelecka', ik: '🏹', n: 'Kusza Oblężnicza', s: { ad: 14, lethality: 3 }, cd: 5,
    opis: i => 'Co <b>5 s</b> ciężki bełt w wroga z największym zdrowiem: <span class="fiz">' + f0((50 + 0.9 * D.ad) * MO(i)) + '</span> (50 + 90% ⚔️), przebija.',
    tik(i) { if (!cdGotowe(i)) return; const c = najsilniejszyWrog(gracz.x, gracz.y, 320); if (!c) return; cdUstaw(i, 5); wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 760, obr: (50 + 0.9 * D.ad) * MO(i), typ: 'fiz', kolor: '#d8d0b0', ksztalt: 'belt', zr: 'Kusza Oblężnicza', przebija: 5, zycie: 0.8 }); DZ.strzal(); } },
  { id: 'pistoletSk', rodz: 'strzelecka', ik: '🔫', n: 'Pistolet Skałkowy', s: { ad: 8, as: 10 }, cd: 2.5,
    opis: i => 'Co <b>2,5 s</b> strzał w najbliższego wroga — zawsze <b>krytyczny</b>: <span class="fiz">' + f0((15 + 0.5 * D.ad) * MO(i) * kryt2()) + '</span> ((15 + 50% ⚔️) × obr. krytyczne).',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 240); if (!c) return; cdUstaw(i, 2.5); wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 850, obr: (15 + 0.5 * D.ad) * MO(i) * kryt2(), typ: 'fiz', kolor: '#ffe08a', ksztalt: 'kula', zr: 'Pistolet Skałkowy', zycie: 0.6 }); DZ.strzal(); } },
  { id: 'garlacz', rodz: 'strzelecka', ik: '💥', n: 'Garłacz', s: { ad: 12, hpMax: 30 }, cd: 6,
    opis: i => 'Co <b>6 s</b> śrut w stożku: 7 pocisków po <span class="fiz">' + f0((10 + 0.25 * D.ad) * MO(i)) + '</span> (10 + 25% ⚔️).',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 200); if (!c) return; cdUstaw(i, 6); const k0 = kat(gracz, c);
      for (let n = 0; n < 7; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: k0 + (n - 3) * 0.11, predkosc: 600, obr: (10 + 0.25 * D.ad) * MO(i), typ: 'fiz', kolor: '#d8c890', ksztalt: 'kula', zr: 'Garłacz', zycie: 0.42 }); DZ.wybuch(); } },
  { id: 'rewolwer', rodz: 'strzelecka', ik: '🤠', n: 'Rewolwer', s: { ad: 10, kryt: 8 }, co: 6,
    opis: i => 'Co <b>6.</b> atak broni głównej: 6 szybkich strzałów w losowych wrogów po <span class="fiz">' + f0((8 + 0.25 * D.ad) * MO(i)) + '</span> (8 + 25% ⚔️).',
    naAtak(i) { i.licz = (i.licz || 0) + 1; if (i.licz % 6) return; for (let n = 0; n < 6; n++) opoznione(n * 0.07, () => { const c = losowyWrog(gracz.x, gracz.y, 260); if (c) wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 800, obr: (8 + 0.25 * D.ad) * MO(i), typ: 'fiz', kolor: '#ffe08a', ksztalt: 'kula', zr: 'Rewolwer', zycie: 0.6 }); }); DZ.strzal(); } },
  { id: 'kuszaPowt', rodz: 'strzelecka', ik: '🪃', n: 'Kusza Powtarzalna', s: { as: 14, ad: 6 }, cd: 1.5,
    opis: i => 'Co <b>1,5 s</b> mały bełt w losowego wroga: <span class="fiz">' + f0((8 + 0.3 * D.ad) * MO(i)) + '</span> (8 + 30% ⚔️).',
    tik(i) { if (!cdGotowe(i)) return; const c = losowyWrog(gracz.x, gracz.y, 240); if (!c) return; cdUstaw(i, 1.5); wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 640, obr: (8 + 0.3 * D.ad) * MO(i), typ: 'fiz', kolor: '#c9b890', ksztalt: 'belt', zr: 'Kusza Powtarzalna', zycie: 0.6 }); } },
  { id: 'bumerangLowcy', rodz: 'strzelecka', ik: '🥏', n: 'Bumerang Łowcy', s: { ad: 10, ms: 10 }, cd: 4,
    opis: i => 'Co <b>4 s</b> bumerang leci i wraca, raniąc w obie strony: <span class="fiz">' + f0((18 + 0.45 * D.ad) * MO(i)) + '</span> (18 + 45% ⚔️).',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 220); if (!c) return; cdUstaw(i, 4); const k = kat(gracz, c);
      pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * 380, vy: Math.sin(k) * 380, zycie: 4, r: 9, obr: (18 + 0.45 * D.ad) * MO(i), typ: 'fiz', zr: 'Bumerang Łowcy', przedmiot: true,
        przebija: 99, trafieni: [], kolor: '#e6b53c', ksztalt: 'bumerang', bumerang: true, droga: 0, maxDroga: 220, wraca: false, obrot: 0 }); } },
  { id: 'proca', rodz: 'strzelecka', ik: '🪨', n: 'Proca', s: { as: 8, szczescie: 10 }, co: 3,
    opis: i => 'Co <b>3.</b> atak broni głównej: kamień w cel — <span class="fiz">' + f0((10 + 0.3 * D.ad) * MO(i)) + '</span> (10 + 30% ⚔️) i ogłuszenie 0,6 s.',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 3) return; wystrzel({ x: gracz.x, y: gracz.y, cel: cel, predkosc: 560, obr: (10 + 0.3 * D.ad) * MO(i), typ: 'fiz', kolor: '#8a8a9a', ksztalt: 'kula', zr: 'Proca', zycie: 0.8, ogluszy: 0.6 }); } },
  { id: 'lukBurzy', rodz: 'strzelecka', ik: '🌩️', n: 'Łuk Burzy', s: { ad: 10, as: 10 }, cd: 0.5,
    opis: i => 'Trafienia <b>krytyczne</b>: piorunowa strzała przeskakuje na 3 cele: <span class="mag">' + f0((20 + 0.4 * D.ad) * MO(i)) + '</span> (20 + 40% ⚔️).',
    naKryt(i, w) { if (!cdGotowe(i)) return; cdUstaw(i, 0.5); lancuch(gracz, w, (20 + 0.4 * D.ad) * MO(i), 'mag', 3, 160, 1, 'Łuk Burzy'); } },
  { id: 'harpun', rodz: 'strzelecka', ik: '🪝', n: 'Harpun', s: { ad: 12, zasieg: 10 }, cd: 6,
    opis: i => 'Co <b>6 s</b> harpun w najdalszego wroga w zasięgu: przyciąga go i zadaje <span class="fiz">' + f0((30 + 0.6 * D.ad) * MO(i)) + '</span> (30 + 60% ⚔️).',
    tik(i) { if (!cdGotowe(i)) return; const c = najdalszyWrog(gracz.x, gracz.y, 300); if (!c) return; cdUstaw(i, 6); dodajBlyskawice(gracz.x, gracz.y, c.x, c.y, '#c8b890');
      zadaj(c, (30 + 0.6 * D.ad) * MO(i), 'fiz', { zr: 'Harpun' }); if (!c.ciezki && !c.boss) { const k = kat(c, gracz); c.kbx += Math.cos(k) * 240; c.kby += Math.sin(k) * 240; } } },

  // ======================= BIAŁA =======================
  { id: 'dwureczny', rodz: 'biala', ik: '⚔️', n: 'Miecz Dwuręczny', s: { ad: 16, hpMax: 40 }, cd: 5,
    opis: i => 'Co <b>5 s</b> piruet wokół Ciebie (r 100): <span class="fiz">' + f0((30 + 0.7 * D.ad) * MO(i)) + '</span> (30 + 70% ⚔️).',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 100) === 0) return; cdUstaw(i, 5); ciecia.push({ x: gracz.x, y: gracz.y, kat: 0, luk: Math.PI * 2, r: 100 * mnObszaru(), czas: 0.25, max: 0.25, kolor: '#e8e8f0' });
      aura(100, '#e8e8f0', w => zadaj(w, (30 + 0.7 * D.ad) * MO(i), 'fiz', { obszar: true, zr: 'Miecz Dwuręczny' }), true); DZ.ciecie(); } },
  { id: 'toporRzeznika', rodz: 'biala', ik: '🪓', n: 'Topór Rzeźnika', s: { ad: 15, hpMax: 25 }, co: 4,
    opis: i => 'Co <b>4.</b> atak broni głównej: rozszczepienie — krwawienie na celu i wrogach obok (r 75): <span class="fiz">' + f0((25 + 0.5 * D.ad) * MO(i)) + '</span> (25 + 50% ⚔️) przez 3 s.',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 4) return; obszarowe(cel.x, cel.y, 75, '#c0392b', w => krwawienie(w, (25 + 0.5 * D.ad) * MO(i) / 3, 3, true), false); } },
  { id: 'wloczniaStraz', rodz: 'biala', ik: '🔱', n: 'Włócznia Strażnika', s: { ad: 10, pancerz: 12 }, cd: 3,
    opis: i => 'Co <b>3 s</b> pchnięcie w linii (zasięg 170): <span class="fiz">' + f0((18 + 0.45 * D.ad) * MO(i)) + '</span> (18 + 45% ⚔️) wszystkim na drodze.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 170); if (!c) return; cdUstaw(i, 3); liniowe(kat(gracz, c), 170, 20, w => zadaj(w, (18 + 0.45 * D.ad) * MO(i), 'fiz', { zr: 'Włócznia Strażnika' })); } },
  { id: 'sztyletSkryt', rodz: 'biala', ik: '🔪', n: 'Sztylet Skrytobójcy', s: { kryt: 10, lethality: 5 }, co: 3,
    opis: i => 'Co <b>3.</b> atak broni głównej: dodatkowe pchnięcie <span class="fiz">' + f0((15 + 0.4 * D.ad) * MO(i)) + '</span> (15 + 40% ⚔️) — podwójne, gdy cel ma mniej niż 50% zdrowia.',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 3) return; opoznione(0.08, () => { if (!cel.martwy) { zadaj(cel, (15 + 0.4 * D.ad) * MO(i) * (cel.hp < cel.hpMax * 0.5 ? 2 : 1), 'fiz', { zr: 'Sztylet Skrytobójcy' }); efektBlysk(cel.x, cel.y, '#c0c0d0'); } }); } },
  { id: 'mlotBojowy', rodz: 'biala', ik: '🔨', n: 'Młot Bojowy', s: { hpMax: 60, pancerz: 8 }, cd: 6,
    opis: i => 'Co <b>6 s</b> fala uderzeniowa (r 120): <span class="fiz">' + f0((25 + 0.5 * D.ad + 0.03 * D.hpMax) * MO(i)) + '</span> (25 + 50% ⚔️ + 3% maks. zdrowia) i ogłuszenie 0,6 s.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 120) === 0) return; cdUstaw(i, 6); aura(120, '#c0a080', w => { zadaj(w, (25 + 0.5 * D.ad + 0.03 * D.hpMax) * MO(i), 'fiz', { obszar: true, zr: 'Młot Bojowy' }); oglusz(w, 0.6, { zrodlo: 'Młot Bojowy' }); }, true); DZ.wybuch(); } },
  { id: 'kosaZniwiarza', rodz: 'biala', ik: '🌙', n: 'Kosa Żniwiarza', s: { ad: 11, omni: 1 },
    opis: i => 'Każde zabójstwo: 25% szansy na wirujące cięcie (r 95): <span class="fiz">' + f0((20 + 0.5 * D.ad) * MO(i)) + '</span> (20 + 50% ⚔️).',
    naZabicie(i, w) { if (Math.random() > 0.25 || i._t > czasGry - 0.3) return; i._t = czasGry; ciecia.push({ x: gracz.x, y: gracz.y, kat: 0, luk: Math.PI * 2, r: 95 * mnObszaru(), czas: 0.22, max: 0.22, kolor: '#c9a8ff' });
      aura(95, '#c9a8ff', o => zadaj(o, (20 + 0.5 * D.ad) * MO(i), 'fiz', { obszar: true, zr: 'Kosa Żniwiarza' }), true); } },
  { id: 'rapier', rodz: 'biala', ik: '🤺', n: 'Rapier', s: { as: 12, kryt: 8 }, co: 5,
    opis: i => 'Co <b>5.</b> atak broni głównej: pchnięcie egzekucyjne — <span class="fiz">' + f0(20 * MO(i)) + ' + ' + fmt(8 * MO(i)) + '% brakującego zdrowia celu</span> (bossowie: 1/3).',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 5) return; opoznione(0.06, () => { if (cel.martwy) return; zadaj(cel, 20 * MO(i) + (cel.hpMax - cel.hp) * 0.08 * MO(i) * (cel.boss ? 0.33 : 1), 'fiz', { zr: 'Rapier' }); efektBlysk(cel.x, cel.y, '#ffe08a'); }); } },
  { id: 'tarczaBojowa', rodz: 'biala', ik: '🛡️', n: 'Tarcza Bojowa', s: { pancerz: 18, hpMax: 50 }, cd: 7,
    opis: i => 'Co <b>7 s</b> uderzenie tarczą w stożku: <span class="fiz">' + f0((20 + 0.3 * D.pancerz) * MO(i)) + '</span> (20 + 30% pancerza), ogłusza 0,5 s i daje tarczę ' + f0((30 + 0.1 * D.pancerz) * MO(i)) + '.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 130); if (!c) return; cdUstaw(i, 7); dajTarcze((30 + 0.1 * D.pancerz) * MO(i), 3);
      stozek(kat(gracz, c), 130, 0.7, '#d8d8e4', w => { zadaj(w, (20 + 0.3 * D.pancerz) * MO(i), 'fiz', { zr: 'Tarcza Bojowa' }); oglusz(w, 0.5, { zrodlo: 'Tarcza Bojowa' }); }); } },
  { id: 'bicz', rodz: 'biala', ik: '🐍', n: 'Bicz', s: { as: 10, zasieg: 8 }, cd: 2.5,
    opis: i => 'Co <b>2,5 s</b> smagnięcie łukiem (zasięg 150): <span class="fiz">' + f0((14 + 0.4 * D.ad) * MO(i)) + '</span> (14 + 40% ⚔️) i spowolnienie 30%.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 150); if (!c) return; cdUstaw(i, 2.5); stozek(kat(gracz, c), 150, 0.55, '#c8a070', w => { zadaj(w, (14 + 0.4 * D.ad) * MO(i), 'fiz', { zr: 'Bicz' }); spowolnij(w, 0.3, 1.2); }); } },
  { id: 'kastetTytana', rodz: 'biala', ik: '🥊', n: 'Kastet Tytana', s: { hpMax: 50, ad: 8 }, co: 4,
    opis: i => 'Co <b>4.</b> atak broni głównej: potężny cios — <span class="fiz">' + f0((10 + 0.02 * D.hpMax) * MO(i)) + '</span> (10 + 2% maks. zdrowia), odrzut i ogłuszenie 0,4 s.',
    naAtak(i, b, cel) { i.licz = (i.licz || 0) + 1; if (i.licz % 4) return; opoznione(0.05, () => { if (cel.martwy) return; zadaj(cel, (10 + 0.02 * D.hpMax) * MO(i), 'fiz', { zr: 'Kastet Tytana' }); odrzuc(cel, 40); oglusz(cel, 0.4, { zrodlo: 'Kastet Tytana' }); }); } },

  // ======================= ALCHEMIA =======================
  { id: 'granaty', rodz: 'alchemia', ik: '💣', n: 'Granaty', s: { obszar: 8, ad: 8 }, cd: 5,
    opis: i => 'Co <b>5 s</b> granat w losowego wroga (r 75): <span class="fiz">' + f0((30 + 0.5 * D.ad + 0.3 * D.ap) * MO(i)) + '</span> (30 + 50% ⚔️ + 30% ✨).',
    tik(i) { if (!cdGotowe(i)) return; const c = losowyWrog(gracz.x, gracz.y, 250); if (!c) return; cdUstaw(i, 5); granat(gracz.x, gracz.y, c.x, c.y, 75, (30 + 0.5 * D.ad + 0.3 * D.ap) * MO(i), 'fiz', 'Granaty'); } },
  { id: 'fiolkaKwasu', rodz: 'alchemia', ik: '⚗️', n: 'Fiolka Kwasu', s: { ap: 10, przebPancP: 6 }, cd: 6,
    opis: i => 'Co <b>6 s</b> kałuża kwasu (r 70, 4 s): <span class="mag">' + f0((8 + 0.12 * D.ap) * MO(i)) + '</span> (8 + 12% ✨) co 0,5 s i kruszy pancerz o 15%.',
    tik(i) { if (!cdGotowe(i)) return; const c = skupisko(gracz.x, gracz.y, 240, 70); if (!c) return; cdUstaw(i, 6); polaEfektow.push({ wl: gracz, x: c.x, y: c.y, r: 70 * mnObszaru(), czas: 4, max: 4, tyk: 0, rodzaj: 'kwas', obr: (8 + 0.12 * D.ap) * MO(i), zr: 'Fiolka Kwasu' }); } },
  { id: 'dynamit', rodz: 'alchemia', ik: '🧨', n: 'Dynamit', s: { obrBonus: 4, hpMax: 30 }, cd: 10,
    opis: i => 'Co <b>10 s</b> laska dynamitu na skupisko wrogów (r 130): <span class="fiz">' + f0((80 + 1.0 * D.ad + 0.8 * D.ap) * MO(i)) + '</span> (80 + 100% ⚔️ + 80% ✨).',
    tik(i) { if (!cdGotowe(i)) return; const c = skupisko(gracz.x, gracz.y, 260, 130); if (!c) return; cdUstaw(i, 10); granat(gracz.x, gracz.y, c.x, c.y, 130, (80 + D.ad + 0.8 * D.ap) * MO(i), 'fiz', 'Dynamit', 1.0); } },
  { id: 'molotow', rodz: 'alchemia', ik: '🍾', n: 'Koktajl Mołotowa', s: { ap: 10, ad: 6 }, cd: 5,
    opis: i => 'Co <b>5 s</b> płonąca kałuża (r 65, 3 s) podpala wrogów: <span class="mag">' + f0((10 + 0.2 * D.ad + 0.2 * D.ap) * MO(i)) + '</span> (10 + 20% ⚔️ + 20% ✨) na sekundę.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 230); if (!c) return; cdUstaw(i, 5); polaEfektow.push({ wl: gracz, x: c.x, y: c.y, r: 65 * mnObszaru(), czas: 3, max: 3, tyk: 0, rodzaj: 'ogien', obr: (10 + 0.2 * D.ad + 0.2 * D.ap) * MO(i), zr: 'Koktajl Mołotowa' }); } },
  { id: 'bombaDymna', rodz: 'alchemia', ik: '💨', n: 'Bomba Dymna', s: { unik: 4, ms: 12 }, cd: 9,
    opis: i => 'Co <b>9 s</b>, gdy wróg jest blisko: chmura dymu — <b>+' + Math.round(20 * Math.min(2, MO(i))) + '% uniku</b> na 3 s, wrogowie wokół spowolnieni o 40%.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 90) === 0) return; cdUstaw(i, 9); dodajBuff('dym', { unik: 20 * Math.min(2, MO(i)) }, 3); aura(140, '#a0a0b0', w => spowolnij(w, 0.4, 2), true); } },
  { id: 'minaPulapka', rodz: 'alchemia', ik: '⚙️', n: 'Mina Pułapka', s: { pancerz: 6, obszar: 6 }, cd: 4,
    opis: i => 'Co <b>4 s</b> zostawia minę (20 s). Wybucha, gdy wróg na nią wejdzie (r 70): <span class="fiz">' + f0((40 + 0.6 * D.ad) * MO(i)) + '</span> (40 + 60% ⚔️).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 4); dodajStwora('mina', gracz.x, gracz.y, 20, { obr: (40 + 0.6 * D.ad) * MO(i), zr: 'Mina Pułapka', r: 70 * mnObszaru() }); } },
  { id: 'butlaGazu', rodz: 'alchemia', ik: '☁️', n: 'Butla Gazu', s: { hpMax: 50, leczenie: 5 },
    opis: i => 'Trujący opar wokół Ciebie (r 85): co 0,5 s <span class="mag">' + f0((6 + 0.08 * D.ap + 0.005 * D.hpMax) * MO(i)) + '</span> (6 + 8% ✨ + 0,5% maks. zdrowia).',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t < 0.5) return; i.t = 0; aura(85, '#9ae05a', w => zadaj(w, (6 + 0.08 * D.ap + 0.005 * D.hpMax) * MO(i), 'mag', { dot: true, obszar: true, zr: 'Butla Gazu' })); } },
  { id: 'rakietnica', rodz: 'alchemia', ik: '🚀', n: 'Rakietnica', s: { ad: 10, ap: 10 }, cd: 7,
    opis: i => 'Co <b>7 s</b> 4 rakiety w różnych wrogów (wybuch r 50): <span class="fiz">' + f0((25 + 0.35 * D.ad + 0.35 * D.ap) * MO(i)) + '</span> (25 + 35% ⚔️ + 35% ✨) każda.',
    tik(i) { if (!cdGotowe(i)) return; const cele = najblizsi(gracz.x, gracz.y, 280, 4); if (!cele.length) return; cdUstaw(i, 7); const v = (25 + 0.35 * D.ad + 0.35 * D.ap) * MO(i);
      cele.forEach((c, n) => wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, c) + (n - 1.5) * 0.4, cel: c, naprowadza: 6, predkosc: 420, obr: v * 0.5, typ: 'fiz', kolor: '#ffb04a', ksztalt: 'rakieta', zr: 'Rakietnica', zycie: 1.4, wybuch: { r: 50, obr: v } })); } },
  // ---- nowe: naładowanie, cięcie wokół celu, odbijające się czakramy ----
  { id: 'kosaStatikka', rodz: 'biala', ik: '⚡', n: 'Kosa Statikka', s: { as: 10, ms: 8 }, energia: true,
    opis: i => '⚡ <b>Naładowany atak</b> broni głównej puszcza łańcuch piorunów na 4 wrogów: <span class="mag">' + f0((25 + 0.3 * D.ad + 0.2 * D.ap) * MO(i)) + '</span> (25 + 30% ⚔️ + 20% ✨) każdemu. Energia ładuje się z biegania i ataków.',
    naNaladowanym(i, b, cel) { lancuch(gracz, cel, (25 + 0.3 * D.ad + 0.2 * D.ap) * MO(i), 'mag', 4, 170, 1, 'Kosa Statikka'); } },
  { id: 'tiamat', rodz: 'biala', ik: '🌊', n: 'Tiamat', s: { ad: 12, hpMax: 30 }, co: 1,
    opis: i => OH + '(raz na atak) każdy atak broni głównej tnie wrogów wokół celu (r 70): <span class="fiz">' + f0(12 * MO(i)) + '%</span> obrażeń ataku (fizyczne).',
    naTrafienie(i, w, k) { if (!k.glowny || k.zadaneSurowe <= 0) return; const v = k.zadaneSurowe * 0.12 * MO(i); obszarowe(w.x, w.y, 70, '#7ab8e8', o => { if (o !== w) zadaj(o, v, 'fiz', { obszar: true, zr: 'Tiamat' }); }, true); } },
  { id: 'szybkostrzal', rodz: 'strzelecka', ik: '🎆', n: 'Działo Szybkostrzelne', s: { as: 10, zasieg: 10 }, energia: true,
    opis: i => '⚡ <b>Naładowany atak</b> wystrzeliwuje dodatkowy ognisty pocisk w <b>najdalszego</b> wroga do 480: <span class="fiz">' + f0((40 + 0.5 * D.ad) * MO(i)) + '</span> (40 + 50% ⚔️), przebija 2 wrogów.',
    naNaladowanym(i, b, cel) { const c = najdalszyWrog(gracz.x, gracz.y, 480) || cel; if (!c || c.wirtualny) return; wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 760, obr: (40 + 0.5 * D.ad) * MO(i), typ: 'fiz', kolor: '#ffb04a', ksztalt: 'rakieta', zr: 'Działo Szybkostrzelne', zycie: 0.9, przebija: 2, naprowadza: 4 }); } },
  { id: 'czakram', rodz: 'strzelecka', ik: '🥏', n: 'Mały Czakram', s: { ad: 10, kryt: 6 }, cd: 3,
    opis: i => 'Co <b>3 s</b> rzuca czakram, który odbija się między <b>4</b> wrogami bez utraty siły: <span class="fiz">' + f0((20 + 0.5 * D.ad) * MO(i)) + '</span> (20 + 50% ⚔️), może trafić krytycznie.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 260); if (!c) return; cdUstaw(i, 3);
      wystrzel({ x: gracz.x, y: gracz.y, cel: c, predkosc: 560, obr: (20 + 0.5 * D.ad) * MO(i), typ: 'fiz', kolor: '#e8e8f0', ksztalt: 'czakram', zr: 'Mały Czakram', zycie: 1.2, naprowadza: 8, odbicia: 3, mozeKryt: true, bezSpadku: true, zasiegOdbicia: 200 }); } },
  { id: 'grimuar', rodz: 'magiczna', ik: '📓', n: 'Grimuar Cieni', s: { ap: 16, haste: 8 }, energia: true,
    opis: i => '⚡ <b>Naładowany atak</b>: cień celu wybucha (r 85): <span class="mag">' + f0((35 + 0.5 * D.ap) * MO(i)) + '</span> (35 + 50% ✨) i ogłusza trafionych na 0,6 s.',
    naNaladowanym(i, b, cel) { if (cel.wirtualny) return; const v = (35 + 0.5 * D.ap) * MO(i); fale.push({ x: cel.x, y: cel.y, czas: 0.4, max: 0.4, r: 85 * mnObszaru(), kolor: '#7a4ac4' });
      obszarowe(cel.x, cel.y, 85, '#7a4ac4', o => { zadaj(o, v, 'mag', { obszar: true, zr: 'Grimuar Cieni' }); oglusz(o, 0.6, { zrodlo: 'Grimuar Cieni' }); }, true); } },
  { id: 'zatruteStrzalki', rodz: 'alchemia', ik: '🎋', n: 'Zatrute Strzałki', s: { as: 8, ap: 8 }, co: 2,
    opis: i => OH + 'co <b>2.</b> atak broni głównej (raz na atak) zatruwa cel na 3 s: <span class="mag">' + f0((8 + 0.15 * D.ap) * MO(i)) + ' + 25% obrażeń ataku</span> na sekundę (magiczne).',
    naTrafienie(i, w, k) { if (!k.glowny) return; i.licz = (i.licz || 0) + 1; if (i.licz % 2) return; podpal(w, (8 + 0.15 * D.ap) * MO(i) + k.bazowe * 0.25, 3, 'mag', 'Zatrute Strzałki'); } },
];
const DEF_ORE = {}; OREZE.forEach(o => { o.oreze = true; DEF_ORE[o.id] = o; });
function nowyOrez(id, tier) { return { id: id, tier: tier || 0, cd: 0, licz: 0, ore: 1 }; }
function nazwaOreza(o) { return DEF_ORE[o.id].n + ' ' + TIERY[o.tier].rz; }
function cenaOreza(tier) { return Math.round(CENA_ORE[tier] * mnCeny()); }
function cenaUlepszeniaOreza(o) { return Math.round(CENA_ORE[o.tier + 1] * 0.75 * mnCeny()); }
function wartoscSprzedazyOreza(o) { return Math.round(CENA_ORE[o.tier] * 0.4 * mnCeny()); }
function statyOreza(o) { const d = DEF_ORE[o.id], s = {}; for (const k in d.s) s[k] = d.s[k] * MS_ORE[o.tier]; return s; }
function opisOreza(o) {
  const d = DEF_ORE[o.id];
  let s = '<div class="karta-staty">' + opisStatow(statyOreza(o), 1 + (FLAGI.mnPrzedmiotow || 0)) + '</div>';
  s += '<div class="karta-opis">' + d.opis(o) + '</div>';
  return s;
}

// =====================================================================
//  PANCERZ (ze skrzyń i czasem ze sklepu) i PRZEDMIOTY (ze sklepu)
//  Przedmioty NIE dają statystyk — mają same pasywki: stawiają działka,
//  sadzą krzaki z leczącymi owocami, co N-ty atak puszczają coś innego...
// =====================================================================
const MN_PANCERZA = [0.8, 1.36, 2.05, 3.0];
const SLOTY_PANCERZA = ['helm', 'zbroja', 'buty', 'amulet'];
const NAZWY_SLOTOW = { helm: 'Głowa', zbroja: 'Korpus', buty: 'Stopy', amulet: 'Szyja' };
const IKONY_SLOTOW = { helm: '🪖', zbroja: '🛡️', buty: '👢', amulet: '📿' };
const PANCERZE = [
  { id: 'helmPlyt', slot: 'helm', n: 'Hełm płytowy', ik: '🪖', s: { pancerz: 14, hpMax: 25 } },
  { id: 'kapturUcz', slot: 'helm', n: 'Kaptur Uczonego', ik: '🎓', s: { xpBonus: 10, ap: 10 } },
  { id: 'helmWoj', slot: 'helm', n: 'Hełm Wojownika', ik: '⛑️', s: { pancerz: 7, ad: 5 } },
  { id: 'opaska', slot: 'helm', n: 'Opaska Łowcy', ik: '🎀', s: { kryt: 5, zasieg: 8 } },
  { id: 'koronaMaga', slot: 'helm', n: 'Diadem Maga', ik: '👑', s: { ap: 15, odpMag: 8 } },
  { id: 'helmBerserka', slot: 'helm', n: 'Rogaty Hełm', ik: '🐂', s: { hpMax: 35, as: 5 } },
  { id: 'zbrPlyt', slot: 'zbroja', n: 'Zbroja płytowa', ik: '🛡️', s: { pancerz: 22, hpMax: 30 } },
  { id: 'zbrBers', slot: 'zbroja', n: 'Napierśnik Berserkera', ik: '🥋', s: { ad: 7, as: 7, hpMax: 15 } },
  { id: 'zbrStraz', slot: 'zbroja', n: 'Zbroja Strażnika', ik: '🦺', s: { pancerz: 10, hpMax: 65 } },
  { id: 'szata', slot: 'zbroja', n: 'Szata Maga', ik: '👘', s: { ap: 16, odpMag: 14, hpMax: 15 } },
  { id: 'zbrKata', slot: 'zbroja', n: 'Kolczuga Kata', ik: '☠️', s: { pancerz: 12, lethality: 4 } },
  { id: 'plaszczCienia', slot: 'zbroja', n: 'Płaszcz Cienia', ik: '🧥', s: { unik: 5, ms: 8, hpMax: 15 } },
  { id: 'zbrSmocza', slot: 'zbroja', n: 'Smocza Łuska', ik: '🐲', s: { pancerz: 12, odpMag: 12, hpMax: 25 } },
  { id: 'butWichr', slot: 'buty', n: 'Buty Wichru', ik: '👟', s: { ms: 22 } },
  { id: 'butOkute', slot: 'buty', n: 'Buty okute', ik: '🥾', s: { pancerz: 10, ms: 8, hpMax: 15 } },
  { id: 'butWedr', slot: 'buty', n: 'Buty Wędrowca', ik: '🧦', s: { ms: 12, hpMax: 20 } },
  { id: 'butMaga', slot: 'buty', n: 'Buty Maga', ik: '🩴', s: { przebMag: 6, ms: 10 } },
  { id: 'butBers', slot: 'buty', n: 'Buty Berserkera', ik: '🥿', s: { as: 10, ms: 10 } },
  { id: 'butMerk', slot: 'buty', n: 'Buty Merkurego', ik: '👞', s: { odpMag: 12, wytrwalosc: 15, ms: 10 } },
  { id: 'amMocy', slot: 'amulet', n: 'Amulet Mocy', ik: '📿', s: { ad: 9 } },
  { id: 'amZycia', slot: 'amulet', n: 'Amulet Życia', ik: '💠', s: { hpMax: 75 } },
  { id: 'amLowcy', slot: 'amulet', n: 'Amulet Łowcy', ik: '🔮', s: { ad: 5, xpBonus: 8 } },
  { id: 'amWiedzy', slot: 'amulet', n: 'Amulet Wiedzy', ik: '📖', s: { xpBonus: 18 } },
  { id: 'amZrodla', slot: 'amulet', n: 'Amulet Źródła', ik: '💧', s: { leczenie: 8 } },
  { id: 'amKrwi', slot: 'amulet', n: 'Amulet Krwi', ik: '🩸', s: { omni: 1 } },
  { id: 'amSzczescia', slot: 'amulet', n: 'Amulet Szczęścia', ik: '🧿', s: { szczescie: 14 } },
  { id: 'amChciwosci', slot: 'amulet', n: 'Amulet Chciwości', ik: '🪙', s: { chciwosc: 14 } },
  { id: 'amCzasu', slot: 'amulet', n: 'Amulet Czasu', ik: '⌚', s: { haste: 12 } },
  { id: 'amArkan', slot: 'amulet', n: 'Amulet Arkan', ik: '🔯', s: { ap: 12, przebMagP: 4 } },
];
const DEF_PANC = {}; PANCERZE.forEach(p => DEF_PANC[p.id] = p);
function nowyPancerz(id, tier) { return { id: id, tier: tier }; }
function statyPancerza(p) { const d = DEF_PANC[p.id], s = {}; for (const k in d.s) { const v = d.s[k] * MN_PANCERZA[p.tier]; s[k] = (k === 'omni') ? Math.round(v * 10) / 10 : Math.round(v); } return s; }
function cenaPancerza(p) { return Math.round([22, 50, 100, 170][p.tier] * mnCeny()); }

// ---------------------------------------------------------------------
//  Pomocnicze dla przedmiotów
// ---------------------------------------------------------------------
const M = i => 1 + 0.25 * (i.gw || 0);         // gwiazdki ulepszenia: +25% za każdą (pryzmaty nie mają gwiazdek)
function cdGotowe(i) { return !(i.cd > 0); }
function cdUstaw(i, sek) { if (i.ore && FLAGI.cdOreza) sek *= 1 - FLAGI.cdOreza; i.cdMax = sek * 100 / (100 + Math.max(0, D.haste)); i.cd = i.cdMax; hak('naAktywacji', i); }
const CENY_TIERU = [26, 58, 115, 195];
const MAKS_GWIAZDEK = 3;
function f0(v) { return Math.round(v); }

// t: tier 0-3, unik: unikalny (domyślnie dla efektów), cd: odnowienie dla paska HUD
const PRZEDMIOTY = [
  // ======================= ZWYKŁE (T1) =======================
  { id: 'przepaska', t: 0, ik: '🌵', n: 'Kolczasta Przepaska',
    opis: i => 'Gdy wróg trafi Cię <b>wręcz</b>, otrzymuje <span class="mag">' + f0((10 + 0.35 * D.pancerz) * M(i)) + '</span> (10 + 35% pancerza) obrażeń magicznych.',
    naOtrzymanie(i, v, typ, o) { if (o.wrog && o.wrecz) zadaj(o.wrog, (10 + 0.35 * D.pancerz) * M(i), 'mag', { zr: 'Kolczasta Przepaska', odbicie: true }); } },
  { id: 'wiezyczka', t: 0, ik: '🗼', n: 'Mała Wieżyczka', cd: 10, wielokrotny: true,
    opis: i => 'Co <b>10 s</b> stawia wieżyczkę na 8 s. Strzela co 0,8 s: <span class="fiz">' + f0((8 + 0.2 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (8 + 20% ⚔️ + 20% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 10); postawDzialko('wiezyczka', 8, { obr: (8 + 0.2 * D.ad + 0.2 * D.ap) * M(i), co: 0.8, zr: 'Mała Wieżyczka' }); } },
  { id: 'krzakJagod', t: 0, ik: '🫐', n: 'Krzak Jagód', cd: 16, wielokrotny: true,
    opis: i => 'Co <b>16 s</b> sadzi krzak (12 s), który co 3 s zrzuca jagodę. Jagoda leczy tego, kto ją zbierze, o <b>' + fmt(5 * M(i)) + '%</b> maks. zdrowia (działa też na kolegów).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 16); dodajStwora('krzak', gracz.x + losowo(-40, 40), gracz.y + losowo(-40, 40), 12, { co: 3, lecz: 0.05 * M(i), ikOwocu: '🫐' }); } },
  { id: 'swieca', t: 0, ik: '🕯️', n: 'Świeca Mędrca',
    opis: i => 'Każdy nowy poziom leczy Cię o <b>' + Math.round(15 * M(i)) + '%</b> maks. zdrowia i daje tarczę ' + Math.round(10 * M(i)) + '% maks. zdrowia na 3 s.',
    naAwans(i) { leczGracza(D.hpMax * 0.15 * M(i), 'Świeca Mędrca'); dajTarcze(D.hpMax * 0.1 * M(i), 3); } },
  { id: 'sakiewka', t: 0, ik: '👛', n: 'Sakiewka Złodzieja', wielokrotny: true,
    opis: i => 'Zabici wrogowie mają <b>12%</b> szansy upuścić dodatkowe <b>' + f0(2.5 * M(i)) + '</b> złota (ponad zwykłe złoto z fali).',
    naZabicie(i, w) { if (!w.bezLupu && !w.sojusznik && Math.random() < 0.12) rozsypMonety(w.x, w.y, 2.5 * M(i) / 1.3, true); } },
  { id: 'koniczyna', t: 0, ik: '🍀', n: 'Czterolistna Koniczyna',
    opis: i => 'Skrzynie wypadają z wrogów o <b>' + Math.round(30 * M(i)) + '%</b> częściej.',
    mnSkrzyn(i) { return 1 + 0.3 * M(i); } },
  { id: 'lusterko', t: 0, ik: '🪞', n: 'Lusterko',
    opis: i => 'Pociski wrogów mają <b>' + Math.round(Math.min(50, 15 * M(i))) + '%</b> szansy odbić się od Ciebie i polecieć z powrotem (bez obrażeń dla Ciebie).',
    odbijPocisk(i) { return Math.random() < Math.min(0.5, 0.15 * M(i)); } },
  { id: 'oselka', t: 0, ik: '🪨', n: 'Osełka',
    opis: i => 'Co <b>5.</b> atak broni głównej zadaje <b>+' + Math.round(50 * M(i)) + '%</b> obrażeń.',
    naAtak(i) { i.licz = (i.licz || 0) + 1; i.gotowy = i.licz % 5 === 0; },
    modZadanych(i, w, typ, o) { return o.atak && i.gotowy ? 1 + 0.5 * M(i) : 1; } },
  { id: 'pochodnia', t: 0, ik: '🔦', n: 'Pochodnia',
    opis: i => OH + '(raz na atak) <b>25%</b> szansy podpalić cel: <span class="mag">' + f0((5 + 0.15 * D.ad + 0.1 * D.ap) * M(i)) + '</span> (5 + 15% ⚔️ + 10% ✨) na sekundę przez 3 s.',
    naTrafienie(i, w, k) { if (k.glowny && Math.random() < 0.25) podpal(w, (5 + 0.15 * D.ad + 0.1 * D.ap) * M(i), 3, 'mag', 'Pochodnia'); } },
  { id: 'magnes', t: 0, ik: '🧲', n: 'Magnes', cd: 12,
    opis: i => 'Co <b>' + fmt(12 / M(i)) + ' s</b> przyciąga do Ciebie wszystkie kulki doświadczenia i monety z całej areny.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna || (kulki.length + monety.length) < 4) return; cdUstaw(i, 12 / M(i)); przyciagnijLupy(); fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 160, kolor: '#7ee87a', odwrot: true }); } },
  { id: 'kamienOdnowy', t: 0, ik: '💠', n: 'Kamień Odnowy',
    opis: i => 'Co 15 zabójstw i za każdą zabitą elitę leczysz się o <b>' + Math.round(12 * M(i)) + '%</b> maks. zdrowia.',
    naZabicie(i, w) { i.zab = (i.zab || 0) + 1; if (w.elita || w.boss || i.zab % 15 === 0) leczGracza(D.hpMax * 0.12 * M(i), 'Kamień Odnowy'); } },
  { id: 'talizmanUniku', t: 0, ik: '🍃', n: 'Talizman Wiatru',
    opis: i => 'Po <b>uniku</b> następny atak zadaje <b>+' + Math.round(60 * M(i)) + '%</b> obrażeń, a Ty zyskujesz +40 prędkości ruchu na 1 s.',
    naUniku(i) { i.gotowy = 1; dodajBuff('wiatr', { ms: 40 }, 1); },
    modZadanych(i, w, typ, o) { if (o.atak && i.gotowy) { i.gotowy = 0; return 1 + 0.6 * M(i); } return 1; } },
  { id: 'rog', t: 0, ik: '📯', n: 'Róg Bojowy',
    opis: i => 'Na początku każdej fali: <b>+' + Math.round(35 * M(i)) + '%</b> prędkości ataku i +20 prędkości ruchu na 8 s.',
    naStartFali(i) { dodajBuff('rog', { as: 35 * M(i), ms: 20 }, 8); } },
  { id: 'pulapka', t: 0, ik: '🪤', n: 'Wnyki', cd: 7, wielokrotny: true,
    opis: i => 'Co <b>7 s</b> zostawia wnyki (20 s). Pierwszy wróg, który w nie wejdzie, jest unieruchomiony na 1,5 s i dostaje <span class="fiz">' + f0((20 + 0.3 * D.ad) * M(i)) + '</span> (20 + 30% ⚔️).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 7); dodajStwora('wnyki', gracz.x, gracz.y, 20, { obr: (20 + 0.3 * D.ad) * M(i), zr: 'Wnyki' }); } },
  { id: 'ksiazkaKucharska', t: 0, ik: '🍳', n: 'Książka Kucharska', cd: 12,
    opis: i => 'Co <b>12 s</b> w walce zjadasz przekąskę: leczysz się o <b>' + fmt(6 * M(i)) + '%</b> maks. zdrowia i dostajesz tarczę ' + fmt(8 * M(i)) + '% maks. zdrowia na 3 s.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 12); leczGracza(D.hpMax * 0.06 * M(i), 'Książka Kucharska'); dajTarcze(D.hpMax * 0.08 * M(i), 3); } },

  // ======================= RZADKIE (T2) =======================
  { id: 'dzialko', t: 1, ik: '🔫', n: 'Działko Strażnicze', cd: 12, wielokrotny: true,
    opis: i => 'Co <b>12 s</b> stawia działko na 12 s. Strzela co 0,6 s: <span class="fiz">' + f0((12 + 0.3 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (12 + 30% ⚔️ + 20% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 12); postawDzialko('dzialko', 12, { obr: (12 + 0.3 * D.ad + 0.2 * D.ap) * M(i), co: 0.6, zr: 'Działko Strażnicze' }); } },
  { id: 'wiezaMrozu', t: 1, ik: '❄️', n: 'Wieża Mrozu', cd: 15, wielokrotny: true,
    opis: i => 'Co <b>15 s</b> stawia wieżę mrozu (10 s). Co 1,5 s fala zimna (r 120): spowolnienie 45% i <span class="mag">' + f0((10 + 0.2 * D.ap) * M(i)) + '</span> (10 + 20% ✨). Co trzecia fala zamraża na 0,8 s.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 15); postawDzialko('wiezaMrozu', 10, { obr: (10 + 0.2 * D.ap) * M(i), co: 1.5, zr: 'Wieża Mrozu', aura: 120 * mnObszaru() }); } },
  { id: 'mozdzierz', t: 1, ik: '🧨', n: 'Moździerz', cd: 14, wielokrotny: true,
    opis: i => 'Co <b>14 s</b> stawia moździerz (12 s). Co 2 s pocisk spada na <b>największą grupę</b> wrogów w zasięgu 380 (r 75): <span class="fiz">' + f0((25 + 0.45 * D.ad + 0.25 * D.ap) * M(i)) + '</span> (25 + 45% ⚔️ + 25% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 14); postawDzialko('mozdzierz', 12, { obr: (25 + 0.45 * D.ad + 0.25 * D.ap) * M(i), co: 2, zr: 'Moździerz' }); } },
  { id: 'zrodlo', t: 1, ik: '⛲', n: 'Źródło Życia', cd: 20, wielokrotny: true,
    opis: i => 'Co <b>20 s</b> stawia źródło (10 s): drużyna w promieniu 130 odzyskuje <b>' + fmt(2.5 * M(i)) + '%</b> maks. zdrowia na sekundę.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 20); postawDzialko('zrodlo', 10, { lecz: 0.025 * M(i), co: 0.5, zr: 'Źródło Życia', aura: 130 }); } },
  { id: 'krzakZycia', t: 1, ik: '🌳', n: 'Krzak Życia', cd: 18, wielokrotny: true,
    opis: i => 'Co <b>18 s</b> sadzi krzak (16 s), który co 2,5 s zrzuca owoc. Owoc leczy o <b>' + fmt(6 * M(i)) + '%</b> maks. zdrowia tego, kto go podniesie.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 18); dodajStwora('krzak', gracz.x + losowo(-40, 40), gracz.y + losowo(-40, 40), 16, { co: 2.5, lecz: 0.06 * M(i), ikOwocu: '🍎', ik: '🌳' }); } },
  { id: 'tesla', t: 1, ik: '⚡', n: 'Wieża Tesli', cd: 14, wielokrotny: true,
    opis: i => 'Co <b>14 s</b> stawia wieżę (10 s). Co sekundę razi łańcuchem 3 wrogów: <span class="mag">' + f0((15 + 0.3 * D.ap) * M(i)) + '</span> (15 + 30% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 14); postawDzialko('tesla', 10, { obr: (15 + 0.3 * D.ap) * M(i), co: 1, zr: 'Wieża Tesli' }); } },
  { id: 'ul', t: 1, ik: '🐝', n: 'Ul', cd: 9, wielokrotny: true,
    opis: i => 'Co <b>9 s</b> wypuszcza 3 pszczoły (6 s). Każda żądli co 0,6 s: <span class="fiz">' + f0((6 + 0.15 * D.ad + 0.15 * D.ap) * M(i)) + '</span> (6 + 15% ⚔️ + 15% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 9); for (let n = 0; n < 3; n++) dodajStwora('pszczola', gracz.x, gracz.y, 6, { obr: (6 + 0.15 * D.ad + 0.15 * D.ap) * M(i), zr: 'Ul', ruchomy: true }); } },
  { id: 'totemOgnia', t: 1, ik: '🗿', n: 'Totem Ognia', cd: 15, wielokrotny: true,
    opis: i => 'Co <b>15 s</b> stawia totem (10 s): wrogowie w promieniu 100 płoną — <span class="mag">' + f0((10 + 0.2 * D.ap) * M(i)) + '</span> (10 + 20% ✨) co 0,5 s.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 15); dodajStwora('totem', gracz.x, gracz.y, 10, { obr: (10 + 0.2 * D.ap) * M(i), zr: 'Totem Ognia', aura: 100 * mnObszaru() }); } },
  { id: 'echoOstrza', t: 1, ik: '🔁', n: 'Echo Ostrza',
    opis: i => 'Co <b>' + Math.max(3, 7 - (i.gw || 0)) + '.</b> atak broni głównej powtarza się po chwili (echo pełnej mocy).',
    naAtak(i, b, cel, o) { if (o && o.echo) return; i.licz = (i.licz || 0) + 1; if (i.licz % Math.max(3, 7 - (i.gw || 0))) return; opoznione(0.15, () => echoAtaku(b, cel)); } },
  { id: 'iskrownik', t: 1, ik: '🔋', n: 'Iskrownik', cd: 4,
    opis: i => OH + 'co 4 s (⏱️ przyspieszenie skraca) następny atak razi piorunem do 4 wrogów: <span class="mag">' + f0((30 + 0.3 * D.ap + 0.2 * D.ad) * M(i)) + '</span> (30 + 30% ✨ + 20% ⚔️).',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 4); lancuch(gracz, w, (30 + 0.3 * D.ap + 0.2 * D.ad) * M(i), 'mag', 4, 160, 1, 'Iskrownik'); } },
  { id: 'ostrzeBurzy', t: 1, ik: '⛈️', n: 'Ostrze Burzy', energia: true,
    opis: i => '⚡ <b>Naładowany atak</b> zadaje dodatkowo <span class="mag">' + f0((50 + 0.6 * D.ad) * M(i)) + '</span> (50 + 60% ⚔️), spowalnia cel o 50% na 1,5 s i daje Ci +40 prędkości ruchu na 1,5 s.',
    naNaladowanym(i, b, cel) { if (cel.martwy) return; zadaj(cel, (50 + 0.6 * D.ad) * M(i), 'mag', { zr: 'Ostrze Burzy' }); spowolnij(cel, 0.5, 1.5); efektBlysk(cel.x, cel.y, '#9fd8ff'); dodajBuff('burza', { ms: 40 }, 1.5); } },
  { id: 'kordelas', t: 1, ik: '🗡️', n: 'Ząbkowany Kordelas',
    opis: i => 'Po zabiciu wroga następny atak zadaje <b>+' + Math.round(45 * M(i)) + '%</b> obrażeń.',
    naZabicie(i) { i.gotowy = 1; },
    modZadanych(i, w, typ, o) { if (o.atak && i.gotowy) { i.gotowy = 0; return 1 + 0.45 * M(i); } return 1; } },
  { id: 'zaslona', t: 1, ik: '🧕', n: 'Zasłona Wiedźmy', cd: 14,
    opis: i => 'Całkowicie blokuje następne trafienie. Odnawia się co <b>' + fmt(14 / M(i)) + ' s</b>.',
    modOtrzymanych(i, v, typ, o) { if (cdGotowe(i) && v > 0 && !o.dot) { cdUstaw(i, 14 / M(i)); tekstSwiat(gracz.x, gracz.y - 26, 'Zablokowano!', '#c9a8ff'); DZ.tarcza(); return 0; } return 1; } },
  { id: 'rekawicaMrozu', t: 1, ik: '🧊', n: 'Mroźna Rękawica',
    opis: i => 'Wrogowie w promieniu 150 są spowolnieni o <b>' + Math.round(Math.min(45, 18 * M(i))) + '%</b>.',
    tik(i) { const r = 150 * mnObszaru(); wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < r + w.r) spowolnij(w, Math.min(0.45, 0.18 * M(i)), 0.2); }); } },
  { id: 'kolczuga', t: 1, ik: '🌹', n: 'Kolczuga Cierni',
    opis: i => 'Trafiona wręcz odbijasz <span class="mag">' + f0((15 + 0.3 * D.pancerz) * M(i)) + '</span> (15 + 30% pancerza) obrażeń magicznych i nakładasz <b>Rany</b> (wróg leczy się o 60% słabiej).',
    naOtrzymanie(i, v, typ, o) { if (o.wrog && o.wrecz) { zadaj(o.wrog, (15 + 0.3 * D.pancerz) * M(i), 'mag', { zr: 'Kolczuga Cierni', odbicie: true }); o.wrog.rany = 3; } } },
  { id: 'krazace', t: 1, ik: '🌀', n: 'Krążące Ostrza',
    opis: i => '2 ostrza krążą wokół Ciebie (r 62) i tną wrogów: <span class="fiz">' + f0((12 + 0.35 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (12 + 35% ⚔️ + 20% ✨).',
    tik(i, dt) { orbitujace(i, dt, 2, 62, '#d8d8e4', () => (12 + 0.35 * D.ad + 0.2 * D.ap) * M(i), 'fiz', 'Krążące Ostrza'); } },
  { id: 'pochlaniacz', t: 1, ik: '🍶', n: 'Pochłaniacz Magii', cd: 45,
    opis: i => 'Gdy zdrowie spadnie poniżej 35%: tarcza <b>' + f0((90 + 12 * gracz.poziom) * M(i)) + '</b> (90 + 12 × poziom) na 4 s. Odnowienie 45 s.',
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp < D.hpMax * 0.35 && gracz.hp > 0) { cdUstaw(i, 45); dajTarcze((90 + 12 * gracz.poziom) * M(i), 4); } } },
  { id: 'skarbiec', t: 1, ik: '💼', n: 'Skarbiec Kupca',
    opis: i => 'Na koniec fali odsetki: <b>' + Math.round(10 * M(i)) + '%</b> posiadanego złota (maks. ' + f0(30 * M(i)) + ').',
    naKoniecFali(i) { const z = Math.min(30 * M(i), gracz.zloto * 0.1 * M(i)); if (z >= 1) dodajZloto(Math.floor(z), true, 'Odsetki'); } },
  { id: 'tarczaStraz', t: 1, ik: '🔰', n: 'Tarcza Strażnika', cd: 10,
    opis: i => 'Co 10 s dostajesz tarczę <b>' + f0((40 + 0.06 * D.hpMax) * M(i)) + '</b> (40 + 6% maks. zdrowia) na 4 s.',
    tik(i) { if (cdGotowe(i) && fala.aktywna) { cdUstaw(i, 10); dajTarcze((40 + 0.06 * D.hpMax) * M(i), 4); } } },
  { id: 'pazur', t: 1, ik: '🐾', n: 'Pazur Łowcy',
    opis: i => 'Zadajesz <b>+' + Math.round(30 * M(i)) + '%</b> obrażeń wrogom, którzy mają ponad 80% zdrowia.',
    modZadanych(i, w) { return w.hp > w.hpMax * 0.8 ? 1 + 0.3 * M(i) : 1; } },
  { id: 'siekacz', t: 1, ik: '🪚', n: 'Siekacz',
    opis: i => OH + '(raz na atak) ataki <b>wręcz</b> rozcinają też wrogów wokół celu (r 65): <span class="fiz">' + Math.round(50 * M(i)) + '%</span> obrażeń.',
    naTrafienie(i, w, k) { if (!k.glowny || !k.bron || BRONIE[k.bron.rodzaj].dystans) return;
      obszarowe(w.x, w.y, 65, '#d8c0a0', o => { if (o !== w) zadaj(o, k.zadaneSurowe * 0.5 * M(i), 'fiz', { obszar: true, zr: 'Siekacz' }); }, true); } },
  { id: 'ogniste', t: 1, ik: '🧤', n: 'Ogniste Rękawice',
    opis: i => 'Trafienia krytyczne podpalają: <span class="mag">' + Math.round(35 * M(i)) + '%</span> obrażeń krytyku w ciągu 3 s.',
    naKryt(i, w, k) { podpal(w, k.zadane * 0.35 * M(i) / 3, 3, 'mag', 'Ogniste Rękawice'); } },
  { id: 'plyta', t: 1, ik: '🧱', n: 'Kamienna Płyta',
    opis: i => 'Gdy w pobliżu (150) są co najmniej 3 wrogie istoty, otrzymujesz <b>' + Math.round(Math.min(30, 15 * M(i))) + '%</b> mniej obrażeń.',
    modOtrzymanych(i) { return policzWrogow(gracz.x, gracz.y, 150) >= 3 ? 1 - Math.min(0.3, 0.15 * M(i)) : 1; } },
  { id: 'strach', t: 1, ik: '🎃', n: 'Strach na Wróble', cd: 13,
    opis: i => 'Co <b>13 s</b> stawia wabik (5 s): wrogowie w promieniu 200 idą do niego zamiast do Ciebie. Na koniec wybucha (r 110): <span class="mag">' + f0((30 + 0.4 * D.ap + 0.02 * D.hpMax) * M(i)) + '</span>.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 180) < 3) return; cdUstaw(i, 13); dodajStwora('wabik', gracz.x + losowo(-30, 30), gracz.y + losowo(-30, 30), 5, { obr: (30 + 0.4 * D.ap + 0.02 * D.hpMax) * M(i), zr: 'Strach na Wróble', aura: 200 }); } },
  { id: 'stalowe', t: 1, ik: '🫀', n: 'Stalowe Serce', cd: 8,
    opis: i => OH + 'co 8 s trafienie <b>elity lub bossa</b> zadaje <span class="fiz">' + f0((60 + 0.06 * D.hpMax) * M(i)) + '</span> (60 + 6% maks. zdrowia) i daje <b>na stałe +8</b> maks. zdrowia. Zebrane: <b>' + (i.stos || 0) + '</b>.',
    naTrafienie(i, w, k) { if (!(w.elita || w.boss) || !cdGotowe(i)) return; cdUstaw(i, 8); zadaj(w, (60 + 0.06 * D.hpMax) * M(i), 'fiz', { zr: 'Stalowe Serce' }); i.stos = (i.stos || 0) + 1; przeliczStaty(); efektBlysk(w.x, w.y, '#ff6a6a'); },
    statyFlat(i, s) { s.hpMax += 8 * (i.stos || 0); } },
  { id: 'rozlupywacz', t: 1, ik: '⚒️', n: 'Czarny Rozłupywacz',
    opis: i => 'Obrażenia <span class="fiz">fizyczne</span> kruszą pancerz i odporność celu o ' + Math.round(8 * M(i)) + '% (do 45%). Wrogowie skruszeni o ponad 30% dostają od Ciebie <b>+10%</b> obrażeń.',
    naObrazenia(i, w, v, typ) { if (typ === 'fiz') w.krusz = Math.min(0.45, (w.krusz || 0) + 0.08 * M(i)); },
    modZadanych(i, w) { return w && (w.krusz || 0) > 0.3 ? 1.1 : 1; } },

  // ======================= EPICKIE (T3) =======================
  { id: 'dzialoGromu', t: 2, ik: '💥', n: 'Działo Gromu', cd: 14, wielokrotny: true,
    opis: i => 'Co <b>14 s</b> stawia ciężkie działo (12 s). Co 1,2 s strzela pociskiem wybuchowym (r 60): <span class="fiz">' + f0((30 + 0.5 * D.ad + 0.3 * D.ap) * M(i)) + '</span> (30 + 50% ⚔️ + 30% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 14); postawDzialko('dzialoGromu', 12, { obr: (30 + 0.5 * D.ad + 0.3 * D.ap) * M(i), co: 1.2, zr: 'Działo Gromu' }); } },
  { id: 'snajper', t: 2, ik: '🎯', n: 'Wieża Snajperska', cd: 16, wielokrotny: true,
    opis: i => 'Co <b>16 s</b> stawia wieżę snajperską (12 s). Co 2,5 s strzela w <b>najgroźniejszego</b> wroga w zasięgu 420 (elity i bossowie najpierw): <span class="fiz">' + f0((60 + 1.0 * D.ad + 0.4 * D.ap) * M(i)) + '</span> (60 + 100% ⚔️ + 40% ✨), przebija wszystkich na linii.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 16); postawDzialko('snajper', 12, { obr: (60 + 1.0 * D.ad + 0.4 * D.ap) * M(i), co: 2.5, zr: 'Wieża Snajperska' }); } },
  { id: 'drzewoZycia', t: 2, ik: '🌲', n: 'Drzewo Życia', cd: 25, wielokrotny: true,
    opis: i => 'Co <b>25 s</b> wyrasta drzewo (24 s): co 3 s zrzuca 2 owoce (leczą ' + fmt(7 * M(i)) + '% maks. zdrowia), a drużyna w promieniu 120 regeneruje 1,5% maks. zdrowia na sekundę.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 25); dodajStwora('krzak', gracz.x + losowo(-30, 30), gracz.y + losowo(-30, 30), 24, { co: 3, lecz: 0.07 * M(i), ikOwocu: '🍐', ik: '🌲', owoce: 2, regen: 0.015 * M(i), aura: 120 }); } },
  { id: 'chowaniec', t: 2, ik: '🐺', n: 'Wilczy Chowaniec', wielokrotny: true,
    opis: i => 'Wilk biegnie przy Tobie i gryzie co 0,8 s: <span class="fiz">' + f0((15 + 0.4 * D.ad + 0.01 * D.hpMax) * M(i)) + '</span> (15 + 40% ⚔️ + 1% maks. zdrowia). Jest niezniszczalny.',
    tik(i) { if (!fala.aktywna) return; if (!i._s || i._s.czas <= 0 || stwory.indexOf(i._s) < 0) i._s = dodajStwora('wilk', gracz.x + 20, gracz.y, 9999, { ruchomy: true, zr: 'Wilczy Chowaniec', zrodlo: i });
      i._s.obr = (15 + 0.4 * D.ad + 0.01 * D.hpMax) * M(i); } },
  { id: 'botrk', t: 2, ik: '👑', n: 'Ostrze Zniszczonego Króla',
    opis: i => OH + '<span class="fiz">' + fmt(6 * M(i)) + '%</span> AKTUALNEGO zdrowia celu jako obrażenia fizyczne (bossowie: połowa). Pełna wartość na pierwszym trafionym wrogu ataku, <b>1/3</b> na pozostałych trafionych tym samym atakiem. Leczy o 10% tej wartości (w limicie wampiryzmu).',
    naTrafienie(i, w, k) { if (w.hp > 0) { const v = zadaj(w, w.hp * 0.06 * M(i) * (w.boss ? 0.5 : 1) * (k.glowny ? 1 : 1 / 3), 'fiz', { onhit: true, zr: 'Ostrze Zniszczonego Króla' }); if (v > 0) leczWampirem(v * 0.1, 'BotRK'); } } },
  { id: 'huragan', t: 2, ik: '🌪️', n: 'Huragan Runaana',
    opis: i => 'Ataki <b>dystansowe</b> wystrzeliwują 2 dodatkowe pociski w pobliskich wrogów (<span class="fiz">' + Math.round(40 * M(i)) + '%</span> obrażeń, nakładają efekty <span class="onhit">on-hit</span>).',
    naAtak(i, b, cel) { const B = BRONIE[b.rodzaj]; if (!B.dystans) return; najblizsi(cel.x, cel.y, 260, 2, [cel]).forEach(w => strzalPomocniczy(b, w, 0.4 * M(i))); } },
  { id: 'guinsoo', t: 2, ik: '🟧', n: 'Ostrze Furii Guinsoo',
    opis: i => 'Każdy atak daje ładunek Furii: <b>+' + fmt(5 * M(i)) + '%</b> prędkości ataku na 4 s (maks. 10 ładunków, nowy atak odnawia czas). Przy 10 ładunkach co <b>2.</b> atak nakłada efekty <span class="onhit">on-hit</span> <b>dwukrotnie</b>.' + (i.st ? ' Teraz: <b>' + i.st + '</b>.' : ''),
    naAtak(i, b, cel, o) { if (o && o.echo) return; if (czasGry - (i.t || -99) > 4) i.st = 0; i.st = Math.min(10, (i.st || 0) + 1); i.t = czasGry; oznaczStaty();
      if (i.st >= 10) { i.licz = (i.licz || 0) + 1; if (i.licz % 2 === 0) b._podwojnyOnHit = true; } },
    statyDyn(i, s) { if (czasGry - (i.t || -99) > 4) i.st = 0; s.as += 5 * (i.st || 0) * M(i); } },
  { id: 'trojca', t: 2, ik: '🔺', n: 'Trójca', cd: 4,
    opis: i => OH + '<b>Czaroostrze:</b> co 4 s (⏱️ przyspieszenie skraca) następny atak zadaje dodatkowo <span class="fiz">' + f0((30 + 1.0 * D.ad) * M(i)) + '</span> (30 + 100% ⚔️) i daje +25 prędkości ruchu na 2 s.',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 4); zadaj(w, (30 + D.ad) * M(i), 'fiz', { zr: 'Trójca' }); efektBlysk(w.x, w.y, '#ffd24a'); dodajBuff('trojca', { ms: 25 }, 2); } },
  { id: 'krwiopijca', t: 2, ik: '🩸', n: 'Krwiopijca',
    opis: i => 'Nadmiar leczenia zamienia się w tarczę (do <b>' + f0((60 + 0.12 * D.hpMax) * M(i)) + '</b>).',
    naNadleczenie(i, v) { const max = (60 + 0.12 * D.hpMax) * M(i); const ob = tarczaSuma(); if (ob < max) dajTarcze(Math.min(v, max - ob), 6, true); } },
  { id: 'rabadon', t: 2, ik: '🎩', n: 'Kapelusz Rabadona',
    opis: i => 'Zwiększa Twoją moc umiejętności o <b>' + Math.round(30 * M(i)) + '%</b>.',
    statyMnoz(i, s) { s.ap *= 1 + 0.3 * M(i); } },
  { id: 'liandry', t: 2, ik: '🕯️', n: 'Udręka Liandry',
    opis: i => 'Obrażenia <span class="mag">magiczne</span> podpalają: <span class="mag">' + fmt(2.5 * M(i)) + '%</span> maks. zdrowia celu na sekundę przez 3 s (bossowie: 0,8%). Płonący zadajesz <b>+15%</b> obrażeń, a gdy płonący wróg zginie, ogień <b>przeskakuje na 2 najbliższych</b>.',
    naObrazenia(i, w, v, typ, o) { if (typ === 'mag' && !o.dot && w.hp > 0) { podpal(w, w.hpMax * (w.boss ? 0.008 : 0.025) * M(i), 3, 'mag', 'Udręka Liandry'); w._liandry = czasGry + 3; } },
    modZadanych(i, w) { return w && w._liandry > czasGry ? 1.15 : 1; },
    naZabicie(i, w) { if (!(w._liandry > czasGry)) return;
      najblizsi(w.x, w.y, 150, 2, [w]).forEach(c => { podpal(c, c.hpMax * (c.boss ? 0.008 : 0.025) * M(i), 3, 'mag', 'Udręka Liandry'); c._liandry = czasGry + 3; dodajBlyskawice(w.x, w.y, c.x, c.y, '#ff8a3c'); }); } },
  { id: 'zhonya', t: 2, ik: '⏳', n: 'Klepsydra Zhonyi', cd: 45,
    opis: i => 'Gdy zdrowie spadnie poniżej <b>30%</b>: 2,5 s zastoju — jesteś <b>niewrażliwy</b> (nie ruszasz się) i odzyskujesz <b>' + Math.round(25 * M(i)) + '%</b> maks. zdrowia. Na koniec złota fala (r 170): <span class="mag">' + f0((60 + 0.8 * D.ap + 0.08 * D.hpMax) * M(i)) + '</span> (60 + 80% ✨ + 8% maks. zdrowia) i ogłuszenie 1,2 s. Odnowienie 45 s.',
    naOtrzymanie(i) {
      if (!cdGotowe(i) || gracz.hp <= 0 || gracz.hp >= D.hpMax * 0.3) return;
      cdUstaw(i, 45); gracz.zastoj = 2.5; gracz.niewr = Math.max(gracz.niewr, 2.5); tekstSwiat(gracz.x, gracz.y - 28, '⏳ Zastój!', '#ffe08a'); DZ.tarcza();
      const ja = gracz, m = M(i), obr = (60 + 0.8 * D.ap + 0.08 * D.hpMax) * m;
      for (let n = 1; n <= 5; n++) opoznione(0.5 * n, () => { if (gracz === ja) leczGracza(D.hpMax * 0.05 * m, 'Klepsydra Zhonyi'); });
      opoznione(2.5, () => { if (gracz !== ja || stan !== 'walka') return; DZ.wybuch();
        aura(170, '#ffd24a', w => { zadaj(w, obr, 'mag', { obszar: true, zr: 'Klepsydra Zhonyi' }); oglusz(w, 1.2, { zrodlo: 'Klepsydra Zhonyi' }); }, true); });
    } },
  { id: 'aniol', t: 2, ik: '😇', n: 'Anioł Stróż',
    opis: i => 'Gdy zginiesz, wracasz z 50% zdrowia. Ładuje się raz na 3 fale. ' + ((i.ladowanie || 0) > 0 ? '<b class="czer">Ładuje się: jeszcze ' + i.ladowanie + ' fal(e)</b>' : '<b class="ziel">Gotowy</b>'),
    naSmierc(i) { if ((i.ladowanie || 0) > 0) return false; i.ladowanie = 3; gracz.hp = D.hpMax * 0.5; gracz.niewr = 2; tekstSwiat(gracz.x, gracz.y - 30, '😇 Wskrzeszenie!', '#fff6c0'); DZ.pryzmat(); return true; },
    naKoniecFali(i) { if (i.ladowanie > 0) i.ladowanie--; } },
  { id: 'kolekcjoner', t: 2, ik: '💀', n: 'Kolekcjoner',
    opis: () => 'Dobija wrogów (nie bossów) poniżej <b>7%</b> zdrowia. Każde zabójstwo daje +1 złota.',
    naObrazenia(i, w) { if (!w.boss && w.hp > 0 && w.hp < w.hpMax * 0.07) { w.hp = 0; tekstSwiat(w.x, w.y - w.r - 10, '☠️', '#e6543c'); zabij(w, { zr: 'Kolekcjoner' }); } },
    naZabicie(i, w) { dodajZloto(1, false); } },
  { id: 'egida', t: 2, ik: '☀️', n: 'Płonąca Egida',
    opis: i => '<b>Pożoga:</b> co sekundę <span class="mag">' + f0((15 + 0.02 * D.hpMax) * M(i)) + '</span> (15 + 2% maks. zdrowia) obrażeń magicznych w promieniu 115.',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t >= 1) { i.t = 0; aura(115, '#ffb03c', w => zadaj(w, (15 + 0.02 * D.hpMax) * M(i), 'mag', { obszar: true, zr: 'Płonąca Egida' })); } } },
  { id: 'ciernie', t: 2, ik: '🦔', n: 'Kolczasta Zbroja',
    opis: i => 'Każde trafienie przez wroga odbija mu <span class="mag">' + f0((25 + 0.3 * D.pancerz) * M(i)) + '</span> (25 + 30% pancerza) obrażeń magicznych i nakłada <b>Rany</b>.',
    naOtrzymanie(i, v, typ, o) { if (o.wrog) { zadaj(o.wrog, (25 + 0.3 * D.pancerz) * M(i), 'mag', { zr: 'Kolczasta Zbroja', odbicie: true }); o.wrog.rany = 3; } } },
  { id: 'luden', t: 2, ik: '🔊', n: 'Echo Ludena', cd: 4,
    opis: i => 'Co 4 s następne obrażenia magiczne wywołują echo: <span class="mag">' + f0((90 + 0.4 * D.ap) * M(i)) + '</span> (90 + 40% ✨) w cel i 4 pobliskich wrogów.',
    naObrazenia(i, w, v, typ, o) { if (typ !== 'mag' || o.zr === 'Echo Ludena' || !cdGotowe(i)) return; cdUstaw(i, 4); const obr = (90 + 0.4 * D.ap) * M(i);
      [w].concat(najblizsi(w.x, w.y, 200, 4, [w])).forEach(c => { dodajBlyskawice(w.x, w.y, c.x, c.y, '#c9a8ff'); zadaj(c, obr, 'mag', { zr: 'Echo Ludena' }); }); } },
  { id: 'shiv', t: 2, ik: '🗡️', n: 'Nóż Statikka', energia: true,
    opis: i => '⚡ <b>Naładowany atak</b> puszcza łańcuch piorunów na <b>6</b> wrogów: <span class="mag">' + f0((45 + 0.4 * D.ad + 0.25 * D.ap) * M(i)) + '</span> (45 + 40% ⚔️ + 25% ✨) każdemu.',
    naNaladowanym(i, b, cel) { lancuch(gracz, cel, (45 + 0.4 * D.ad + 0.25 * D.ap) * M(i), 'mag', 6, 180, 1, 'Nóż Statikka'); } },
  { id: 'kraken', t: 2, ik: '🦑', n: 'Pogromca Krakena',
    opis: i => OH + 'co 3. atak (raz na atak) zadaje dodatkowo <span class="praw">' + f0((50 + 0.5 * D.ad) * M(i)) + '</span> (50 + 50% ⚔️) obrażeń prawdziwych.',
    naTrafienie(i, w, k) { if (!k.glowny) return; i.licz = (i.licz || 0) + 1; if (i.licz % 3 === 0) { zadaj(w, (50 + 0.5 * D.ad) * M(i), 'praw', { zr: 'Pogromca Krakena' }); efektBlysk(w.x, w.y, '#7ae0ff'); } } },
  { id: 'hydra', t: 2, ik: '🐉', n: 'Tytaniczna Hydra',
    opis: i => OH + 'ataki zadają dodatkowo <span class="fiz">' + fmt(1.5 * M(i)) + '%</span> Twojego maks. zdrowia, a (raz na atak) wrogowie wokół celu (r 70) dostają <span class="fiz">' + fmt(2.5 * M(i)) + '%</span> maks. zdrowia.',
    statyPost(i, s) { s.onHitFiz += s.hpMax * 0.015 * M(i); },
    naTrafienie(i, w, k) { if (!k.glowny) return; const v = D.hpMax * 0.025 * M(i); obszarowe(w.x, w.y, 70, '#c0a080', o => { if (o !== w) zadaj(o, v, 'fiz', { obszar: true, zr: 'Tytaniczna Hydra' }); }, true); } },
  { id: 'navori', t: 2, ik: '🔵', n: 'Ostrze Navori',
    opis: i => OH + '(raz na atak) każdy atak, który trafi, skraca <b>pozostałe</b> odnowienie Twoich umiejętności o <b>' + fmt(6 * M(i)) + '%</b> (krytyczne: ' + fmt(12 * M(i)) + '%).',
    naTrafienie(i, w, k) { if (!k.glowny) return; const p = Math.min(0.3, (k.kryt ? 0.12 : 0.06) * M(i)); [gracz.umi, gracz.umi2].forEach(u => { if (u && u.cd > 0) u.cd *= 1 - p; }); } },
  { id: 'czarnyOgien', t: 2, ik: '🏮', n: 'Pochodnia Czarnego Ognia',
    opis: i => 'Obrażenia magiczne podpalają: <span class="mag">' + f0((30 + 0.12 * D.ap) * M(i)) + '</span> (30 + 12% ✨) przez 3 s. +3% obrażeń za każdego płonącego wroga w pobliżu (maks. 30%).',
    naObrazenia(i, w, v, typ, o) { if (typ === 'mag' && !o.dot && w.hp > 0) podpal(w, (30 + 0.12 * D.ap) * M(i) / 3, 3, 'mag', 'Pochodnia Czarnego Ognia'); },
    modZadanych(i) { if (!i._t || czasGry - i._t > 0.3) { i._t = czasGry; i._n = wrogowie.filter(w => !w.martwy && w.ogien && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 300).length; } return 1 + Math.min(0.3, 0.03 * (i._n || 0)); } },
  { id: 'zmarzlina', t: 2, ik: '🧊', n: 'Wieczna Zmarzlina', cd: 10,
    opis: i => 'Co 10 s lodowy stożek w najbliższego wroga: <span class="mag">' + f0((100 + 0.5 * D.ap) * M(i)) + '</span> (100 + 50% ✨) i unieruchomienie na 1 s.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 230); if (!c) return; cdUstaw(i, 10);
      stozek(kat(gracz, c), 240, 0.6, '#cfefff', w => { zadaj(w, (100 + 0.5 * D.ap) * M(i), 'mag', { zr: 'Wieczna Zmarzlina' }); oglusz(w, 1, { zrodlo: 'Zmarzlina' }); }); } },
  { id: 'pasRakietowy', t: 2, ik: '🎇', n: 'Pas Rakietowy Hextech', cd: 9,
    opis: i => 'Co 9 s wystrzeliwuje 7 pocisków w stożku: <span class="mag">' + f0((60 + 0.25 * D.ap) * M(i)) + '</span> (60 + 25% ✨) każdy.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 260); if (!c) return; cdUstaw(i, 9); const k0 = kat(gracz, c);
      for (let n = 0; n < 7; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: k0 + (n - 3) * 0.13, predkosc: 520, obr: (60 + 0.25 * D.ap) * M(i), typ: 'mag', kolor: '#ffb04a', ksztalt: 'kula', zr: 'Pas Rakietowy', zycie: 0.7 }); DZ.magia(); } },
  { id: 'pijawka', t: 2, ik: '🧛', n: 'Pijawka Krwi', cd: 9,
    opis: i => 'Co 9 s wir: <span class="fiz">' + f0((80 + 1.0 * D.ad) * M(i)) + '</span> (80 + 100% ⚔️) w promieniu 130; leczy 8% brakującego zdrowia + 2% za każdego trafionego.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 130) === 0) return; cdUstaw(i, 9); let n = 0;
      aura(130, '#c0392b', w => { n++; zadaj(w, (80 + D.ad) * M(i), 'fiz', { obszar: true, zr: 'Pijawka Krwi' }); }, true);
      leczGracza((D.hpMax - gracz.hp) * 0.08 + D.hpMax * 0.02 * Math.min(n, 8), 'Pijawka Krwi'); } },
  { id: 'midas', t: 2, ik: '🪙', n: 'Monety Midasa',
    opis: i => '<b>' + Math.round(7 * M(i)) + '%</b> szansy, że podniesiona moneta jest warta 5×.',
    mnozMonety(i) { return Math.random() < 0.07 * M(i) ? 5 : 1; } },
  { id: 'mejai', t: 2, ik: '📗', n: 'Księga Mejai', wielokrotny: true,
    opis: i => 'Co 8 zabójstw (i za każdą elitę) +1 ładunek, maks. 60: każdy daje <b>+' + fmt(3 * M(i)) + ' ✨</b> i <b>+' + fmt(1.2 * M(i)) + ' ⚔️</b>. Przy 30 ładunkach +8% obrażeń. Ładunki: <b>' + Math.min(60, i.lad || 0) + '/60</b>.',
    naZabicie(i, w) { i.zab = (i.zab || 0) + 1; if ((i.lad || 0) < 60 && (w.elita || w.boss || i.zab % 8 === 0)) { i.lad = (i.lad || 0) + 1; przeliczStaty(); } },
    statyFlat(i, s) { const n = Math.min(60, i.lad || 0); s.ap += 3 * n * M(i); s.ad += 1.2 * n * M(i); if (n >= 30) s.obrBonus += 8; } },

  // ======================= LEGENDARNE (T4) =======================
  { id: 'korona', t: 3, ik: '👸', n: 'Korona Królowej', cd: 10,
    opis: i => 'Osłona: następne obrażenia są mniejsze o <b>' + Math.round(Math.min(90, 75 * M(i))) + '%</b>. Po zużyciu odnawia się po 10 s.',
    modOtrzymanych(i, v, typ, o) { if (cdGotowe(i) && v > 0 && !o.dot) { cdUstaw(i, 10); efektBlysk(gracz.x, gracz.y, '#ffe08a'); return 1 - Math.min(0.9, 0.75 * M(i)); } return 1; } },
  { id: 'wichura', t: 3, ik: '🌬️', n: 'Wichura', cd: 7,
    opis: i => 'Co 7 s 3 naprowadzane pociski w najsłabszego wroga w pobliżu: <span class="fiz">' + f0((50 + 0.2 * D.ad) * M(i)) + '</span> (50 + 20% ⚔️) każdy, do +50% przeciw rannym.',
    tik(i) { if (!cdGotowe(i)) return; const c = najslabszyWrog(gracz.x, gracz.y, 280); if (!c) return; cdUstaw(i, 7);
      for (let n = 0; n < 3; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, c) + (n - 1) * 0.5, predkosc: 430, naprowadza: 8, cel: c, obr: (50 + 0.2 * D.ad) * M(i) * (1 + 0.5 * (1 - c.hp / c.hpMax)), typ: 'fiz', kolor: '#bff0ff', ksztalt: 'strzala', zr: 'Wichura', zycie: 1.4 }); } },
  { id: 'sunderer', t: 3, ik: '⚜️', n: 'Boski Rozłamywacz', cd: 3,
    opis: i => OH + 'co 3 s (⏱️ przyspieszenie skraca) następny atak zadaje <span class="fiz">' + fmt(8 * M(i)) + '%</span> maks. zdrowia celu (bossowie: 3%) i leczy Cię o 30% tej wartości (maks. 4% Twojego zdrowia).',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 3); const v = zadaj(w, w.hpMax * (w.boss ? 0.03 : 0.08) * M(i), 'fiz', { zr: 'Boski Rozłamywacz' }); leczGracza(Math.min(v * 0.3, D.hpMax * 0.04), 'Boski Rozłamywacz'); efektBlysk(w.x, w.y, '#ffe08a'); } },
  { id: 'zacmienie', t: 3, ik: '🌘', n: 'Zaćmienie', cd: 6,
    opis: i => OH + 'dwa ataki w tego samego wroga w 1,5 s: <span class="fiz">' + fmt(6 * M(i)) + '%</span> jego maks. zdrowia (bossowie 2,5%) i tarcza <b>' + f0((40 + 0.35 * D.ad) * M(i)) + '</b>. Odnowienie 6 s.',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; if (i.cel === w && czasGry - i.czas < 1.5) { cdUstaw(i, 6); i.cel = null; zadaj(w, w.hpMax * (w.boss ? 0.025 : 0.06) * M(i), 'fiz', { zr: 'Zaćmienie' }); dajTarcze((40 + 0.35 * D.ad) * M(i), 2); efektBlysk(w.x, w.y, '#c9a8ff'); } else { i.cel = w; i.czas = czasGry; } } },
  { id: 'shieldbow', t: 3, ik: '🏹', n: 'Nieśmiertelny Łuk', cd: 55,
    opis: i => 'Gdy zdrowie spadnie poniżej 30%: tarcza <b>' + f0((250 + 0.2 * D.hpMax) * M(i)) + '</b> (250 + 20% maks. zdrowia) na 3 s i +6% wampiryzmu na 6 s. Odnowienie 55 s.',
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp > 0 && gracz.hp < D.hpMax * 0.3) { cdUstaw(i, 55); dajTarcze((250 + 0.2 * D.hpMax) * M(i), 3); dodajBuff('shieldbow', { omni: 6 }, 6); } } },
  { id: 'zniwiarz', t: 3, ik: '🌑', n: 'Żniwiarz Nocy',
    opis: i => 'Pierwsze trafienie każdego wroga zadaje dodatkowo <span class="mag">' + f0((100 + 0.2 * D.ap) * M(i)) + '</span> (100 + 20% ✨) obrażeń magicznych.',
    naObrazenia(i, w, v, typ, o) { if (w._zniw || o.zr === 'Żniwiarz Nocy') return; w._zniw = 1; zadaj(w, (100 + 0.2 * D.ap) * M(i), 'mag', { zr: 'Żniwiarz Nocy' }); } },
  { id: 'warmog', t: 3, ik: '🟩', n: 'Kirys Warmoga',
    opis: i => '+20% maks. zdrowia. <b>Zawsze</b> odzyskujesz <b>' + fmt(1.2 * M(i)) + '%</b> maks. zdrowia na sekundę, a gdy przez 2 s nikt Cię nie trafi — <b>3×</b> tyle. Nie słabnie od zmęczenia.',
    statyMnoz(i, s) { s.hpMax *= 1.2; },
    tik(i, dt) { if (!fala.aktywna || gracz.hp >= D.hpMax) return; const spokoj = czasGry - (gracz.ostTrafienie || -99) > 2; leczGracza(D.hpMax * 0.012 * M(i) * (spokoj ? 3 : 1) * dt, 'Kirys Warmoga', true); } },
  { id: 'lodoweSerce', t: 3, ik: '❄️', n: 'Lodowe Serce',
    opis: i => 'Wrogowie w promieniu 220 atakują o <b>' + Math.round(Math.min(60, 25 * M(i))) + '%</b> wolniej i poruszają się o 15% wolniej.',
    tik(i) { const r = 220 * mnObszaru(); wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < r + w.r) { spowolnij(w, 0.15, 0.2); w.zamarzniecieAtaku = Math.max(w.zamarzniecieAtaku || 0, Math.min(0.6, 0.25 * M(i))); w._zaT = 0.2; } }); } },
  { id: 'esencja', t: 3, ik: '🔷', n: 'Złodziej Esencji',
    opis: i => 'Trafienia krytyczne skracają odnowienia o 0,3 s. Gdy coś się odnowi i aktywuje, ' + OH + 'następny atak zadaje dodatkowo <span class="fiz">' + f0((40 + 0.9 * D.ad) * M(i)) + '</span> (40 + 90% ⚔️) i daje +15% prędkości ataku na 3 s (do 3 razy).',
    naKryt(i) { skrocCd(0.3); },
    naAktywacji(i, zrodlo) { if (zrodlo !== i) i.gotowy = 1; },
    naTrafienie(i, w, k) { if (k.glowny && i.gotowy) { i.gotowy = 0; zadaj(w, (40 + 0.9 * D.ad) * M(i), 'fiz', { zr: 'Złodziej Esencji' });
      i.st = Math.min(3, (i.st > 0 && czasGry < i.tSt ? i.st : 0) + 1); i.tSt = czasGry + 3; dodajBuff('esencja', { as: 0 }, 3); gracz.buffy.esencja.staty = { as: 15 * i.st }; oznaczStaty(); } } },
  { id: 'fabryka', t: 3, ik: '🏭', n: 'Fabryka Wieżyczek', cd: 16,
    opis: i => 'Twoje działka i wieże stoją <b>2× dłużej</b> i strzelają o 30% szybciej. Co <b>16 s</b> stawia darmowe działko: <span class="fiz">' + f0((20 + 0.4 * D.ad + 0.3 * D.ap) * M(i)) + '</span> co 0,5 s.',
    fabryka: true,
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 16); postawDzialko('dzialko', 12, { obr: (20 + 0.4 * D.ad + 0.3 * D.ap) * M(i), co: 0.5, zr: 'Fabryka Wieżyczek' }); } },
  { id: 'gaj', t: 3, ik: '🏞️', n: 'Gaj Driady', cd: 18,
    opis: i => 'Co <b>18 s</b> sadzi 3 krzaki (14 s) wokół Ciebie. Ich owoce leczą o ' + fmt(6 * M(i)) + '% maks. zdrowia i dają tarczę o tej samej wartości (także kolegom).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 18); for (let n = 0; n < 3; n++) { const k = n * 2.09; dodajStwora('krzak', gracz.x + Math.cos(k) * 70, gracz.y + Math.sin(k) * 70, 14, { co: 3, lecz: 0.06 * M(i), tarcza: true, ikOwocu: '🍇', ik: '🌿' }); } } },
  { id: 'smoczeJajo', t: 3, ik: '🥚', n: 'Smocze Jajo',
    opis: i => 'Wykluwa się smoczek, który leci przy Tobie i co 2 s zieje ogniem w stożku: <span class="mag">' + f0((30 + 0.6 * D.ap + 2 * nrFali()) * M(i)) + '</span> (30 + 60% ✨ + 2 × numer fali) i podpala.',
    tik(i) { if (!fala.aktywna) return; if (!i._s || i._s.czas <= 0 || stwory.indexOf(i._s) < 0) i._s = dodajStwora('smok', gracz.x - 20, gracz.y, 9999, { ruchomy: true, zr: 'Smocze Jajo', zrodlo: i });
      i._s.obr = (30 + 0.6 * D.ap + 2 * nrFali()) * M(i); } },
  // ======================= LECZENIE BEZ WAMPIRYZMU =======================
  { id: 'ziola', t: 0, ik: '🌿', n: 'Woreczek Ziół', wielokrotny: true,
    opis: i => 'Zabici wrogowie mają <b>' + Math.round(Math.min(25, 7 * M(i))) + '%</b> szansy upuścić zioło (elity zawsze). Zioło leczy tego, kto je podniesie, o <b>4%</b> maks. zdrowia (działa też na kolegów).',
    naZabicie(i, w) { if (w.sojusznik || (!w.elita && !w.boss && Math.random() > Math.min(0.25, 0.07 * M(i)))) return; dodajStwora('owoc', w.x, w.y, 10, { lecz: 0.04, ik: '🌿' }); } },
  { id: 'opatrunek', t: 1, ik: '🩹', n: 'Opatrunek Polowy',
    opis: i => 'Odzyskujesz <b>' + Math.round(Math.min(60, 30 * M(i))) + '%</b> każdych otrzymanych obrażeń, rozłożone na 4 s (rana się goi). Teraz do odzyskania: <b>' + f0(i.pula || 0) + '</b>.',
    naOtrzymanie(i, v, typ, o) { if (v > 0 && !o.odbicie) i.pula = Math.min(D.hpMax, (i.pula || 0) + v * Math.min(0.6, 0.3 * M(i))); },
    tik(i, dt) { if (!(i.pula > 0.5) || !fala.aktywna) return; const x = Math.max(i.pula * dt / 4, Math.min(i.pula, 2 * dt)); i.pula -= x; leczGracza(x, 'Opatrunek Polowy', true); } },
  // ======================= NOWE: naładowanie, przy trafieniu, uniwersalne =======================
  { id: 'kolczan', t: 0, ik: '🪶', n: 'Kołczan Lekkości',
    opis: i => OH + 'ataki zadają <span class="fiz">' + f0((8 + 0.06 * Math.max(0, D.as)) * M(i)) + '</span> (8 + 6% Twojej prędkości ataku) obrażeń fizycznych.',
    statyPost(i, s) { s.onHitFiz += (8 + 0.06 * Math.max(0, s.as)) * M(i); } },
  { id: 'iskrzaceButy', t: 0, ik: '👢', n: 'Iskrzące Buty', energia: true,
    opis: i => '⚡ <b>Naładowany atak</b>: +' + f0(30 * M(i)) + ' prędkości ruchu na 2 s i odnowienie umiejętności krótsze o <b>' + fmt(1 * M(i)) + ' s</b>. (Energia ładuje się z biegania i ataków.)',
    naNaladowanym(i) { dodajBuff('iskrzaceButy', { ms: 30 * M(i) }, 2); [gracz.umi, gracz.umi2].forEach(u => { if (u && u.cd > 0) u.cd = Math.max(0, u.cd - M(i)); }); } },
  { id: 'pierscienDoliny', t: 0, ik: '💍', n: 'Pierścień Doliny',
    opis: i => 'Na początku każdej fali dostajesz tarczę <b>' + f0(15 * M(i)) + '%</b> maks. zdrowia na 8 s, a co 20 s w walce kolejną na ' + f0(6 * M(i)) + '% (4 s).', cd: 20,
    naStartFali(i) { i._start = true; },
    tik(i) { if (!fala.aktywna) return; if (i._start) { i._start = false; dajTarcze(D.hpMax * 0.15 * M(i), 8); cdUstaw(i, 20); return; } if (!cdGotowe(i)) return; cdUstaw(i, 20); dajTarcze(D.hpMax * 0.06 * M(i), 4); } },
  { id: 'luneta', t: 0, ik: '🔭', n: 'Luneta',
    opis: i => '+' + f0(15 * M(i)) + '% zasięgu broni (wręcz: połowa). Trafienia z odległości ponad 220 zadają <b>' + f0(12 * M(i)) + '%</b> więcej obrażeń.',
    statyFlat(i, s) { s.zasieg += 15 * M(i); },
    modZadanych(i, w) { return w && Math.hypot(w.x - gracz.x, w.y - gracz.y) > 220 ? 1 + 0.12 * M(i) : 1; } },
  { id: 'kondensator', t: 1, ik: '🔌', n: 'Kondensator', energia: true, energiaTempo: i => 0.4 * M(i),
    opis: i => 'Energia ładuje się o <b>' + f0(40 * M(i)) + '%</b> szybciej. ⚡ <b>Naładowany atak</b> daje tarczę ' + fmt(8 * M(i)) + '% maks. zdrowia i +' + f0(20 * M(i)) + '% prędkości ataku na 3 s.',
    naNaladowanym(i) { dajTarcze(D.hpMax * 0.08 * M(i), 3); dodajBuff('kondensator', { as: 20 * M(i) }, 3); } },
  { id: 'zegarBitewny', t: 1, ik: '⏱️', n: 'Zegar Bitewny',
    opis: i => OH + '(raz na atak) każdy atak, który trafi, skraca odnowienia Twoich <b>przedmiotów i broni dodatkowych</b> o ' + fmt(0.15 * M(i)) + ' s (krytyczne: ' + fmt(0.3 * M(i)) + ' s).',
    naTrafienie(i, w, k) { if (!k.glowny) return; const s = (k.kryt ? 0.3 : 0.15) * M(i);
      gracz.przedmioty.forEach(p => { if (p && p !== i && p.cd > 0) p.cd = Math.max(0, p.cd - s); }); gracz.oreze.forEach(o => { if (o.cd > 0) o.cd = Math.max(0, o.cd - s); }); } },
  { id: 'zabNashora', t: 1, ik: '🦷', n: 'Ząb Nashora',
    opis: i => OH + 'ataki zadają <span class="mag">' + f0((12 + 0.2 * Math.max(0, D.ap)) * M(i)) + '</span> (12 + 20% ✨) obrażeń magicznych.',
    statyKonc(i, s) { s.onHitMag += (12 + 0.2 * Math.max(0, s.ap)) * M(i); } },
  { id: 'koniecRozumu', t: 1, ik: '🧿', n: 'Koniec Rozumu',
    opis: i => OH + '<span class="mag">' + f0((15 + 0.15 * Math.max(0, D.odpMag)) * M(i)) + '</span> (15 + 15% odporności na magię) obrażeń magicznych. Leczy o 10% tej wartości (w limicie wampiryzmu).',
    naTrafienie(i, w) { if (w.martwy) return; const v = zadaj(w, (15 + 0.15 * Math.max(0, D.odpMag)) * M(i), 'mag', { onhit: true, zr: 'Koniec Rozumu' }); if (v > 0) leczWampirem(v * 0.1, 'Koniec Rozumu'); } },
  { id: 'medalion', t: 1, ik: '🏅', n: 'Medalion Odwagi',
    opis: i => 'Gdy masz mniej niż <b>40% zdrowia</b>: otrzymujesz <b>' + f0(Math.min(40, 25 * M(i))) + '%</b> mniej obrażeń i masz +' + f0(25 * M(i)) + ' prędkości ruchu.',
    modOtrzymanych(i) { return gracz.hp < D.hpMax * 0.4 ? 1 - Math.min(0.4, 0.25 * M(i)) : 1; },
    statyDyn(i, s) { if (gracz.hp < s.hpMax * 0.4) s.ms += 25 * M(i); } },
  { id: 'krwiozerczaHydra', t: 2, ik: '🐲', n: 'Krwiożercza Hydra',
    opis: i => OH + '(raz na atak) ataki tną wszystkich wrogów wokół celu (r 80): <span class="fiz">' + f0(25 * M(i)) + '%</span> obrażeń ataku. Leczysz się o 8% obrażeń cięcia (w limicie wampiryzmu).',
    naTrafienie(i, w, k) { if (!k.glowny || k.zadaneSurowe <= 0) return; const v = k.zadaneSurowe * 0.25 * M(i); let suma = 0;
      obszarowe(w.x, w.y, 80, '#c0392b', o => { if (o !== w) suma += zadaj(o, v, 'fiz', { obszar: true, zr: 'Krwiożercza Hydra' }); }, true); if (suma > 0) leczWampirem(suma * 0.08, 'Krwiożercza Hydra'); } },
  { id: 'zegarek', t: 2, ik: '⌚', n: 'Zegarek Kieszonkowy', cd: 30,
    opis: i => 'Co <b>' + f0(30 / M(i)) + ' s</b> (⏱️ przyspieszenie skraca) <b>zeruje odnowienie</b> Twoich umiejętności, jeśli zostało im więcej niż 2 s.',
    tik(i) { if (!fala.aktywna || !cdGotowe(i)) return; const u = [gracz.umi, gracz.umi2].filter(x => x && x.cd > 2); if (!u.length) return; u.forEach(x => x.cd = 0); cdUstaw(i, 30 / M(i)); tekstSwiat(gracz.x, gracz.y - 30, '⌚ Gotowe!', '#ffe08a', 0.8, 13); } },
  { id: 'kamienFilozoficzny', t: 2, ik: '🔶', n: 'Kamień Filozoficzny',
    opis: i => 'Na koniec każdej fali losowa statystyka rośnie <b>na stałe</b> (jak zwykły wybór przy awansie' + (i.gw ? ', ×' + fmt(M(i)) : '') + '). Zostaje nawet po sprzedaży. Dotąd: ' + (i.licz || 0) + '.',
    naKoniecFali(i) { const u = losUlepszeniaStatu(0); const v = u.w[0] * M(i); gracz.stale[u.k] = (gracz.stale[u.k] || 0) + v; i.licz = (i.licz || 0) + 1; oznaczStaty();
      dziennik('🔶 Kamień Filozoficzny: ' + STAT[u.k].i + ' ' + STAT[u.k].n + ' +' + fmt(v) + (STAT[u.k].j === '%' ? '%' : '')); } },
];
// unikalne: tylko jeden egzemplarz; wielokrotne (działka, stworzenia, Mejai...) można kupić kilka razy - każdy działa osobno
const DEF_PRZ = {}; PRZEDMIOTY.forEach(p => { DEF_PRZ[p.id] = p; if (p.unik === undefined) p.unik = !p.wielokrotny; });

function cenaPrzedmiotu(d) { return Math.round((d.cena || CENY_TIERU[d.t]) * mnCeny()); }
function cenaUlepszenia(inst) { const d = DEF_PRZ[inst.id]; const baza = d.t === 'p' ? 170 * (gracz && KLASY[gracz.klasa].ulepszaPryzmaty && ewo('pas') >= 1 ? 0.75 : 1) : (d.cena || CENY_TIERU[d.t]); return Math.round(baza * (0.55 + 0.35 * (inst.gw || 0)) * mnCeny()); }
function wartoscSprzedazy(inst) { const d = DEF_PRZ[inst.id]; const baza = d.t === 'p' ? 120 : (d.cena || CENY_TIERU[d.t]); return Math.round(baza * mnCeny() * (0.4 + 0.15 * (inst.gw || 0))); }
function nowyPrzedmiot(id) { return { id: id, gw: 0, cd: 0 }; }
function gwiazdki(n) { return n ? '★'.repeat(n) : ''; }

// =====================================================================
//  PRZEDMIOTY PRYZMATYCZNE — tylko z Pryzmatycznego Kowadła
// =====================================================================
const PRYZMATY = [
  { id: 'poglos', ik: '🔔', n: 'Pogłos', s: { pancerz: 40, odpMag: 40, as: 30 },
    opis: i => 'Zyskujesz <b>' + fmt(2 * M(i)) + ' maks. zdrowia</b> za każdy 1% premii do prędkości ataku. '
      + OH + 'ataki zadają dodatkowo <span class="mag">' + fmt(2 * M(i)) + '% Twojego maks. zdrowia</span> obrażeń magicznych i (raz na atak) mają 12% szansy ogłuszyć na 0,5 s. '
      + '<b>Twoje ogłuszenia nakładają efekty <span class="onhit">on-hit</span> 3 razy.</b>',
    statyPost(i, s) { s.hpMax += 2 * Math.max(0, s.as) * M(i); s.onHitMag += s.hpMax * 0.02 * M(i); },
    naTrafienie(i, w, k) { if (k.glowny && !k.zOgluszenia && Math.random() < 0.12) oglusz(w, 0.5, { zrodlo: 'Pogłos' }); },
    naOgluszenie(i, w) { if (glebokoscOnHit > 0 || w.martwy) return; zastosujOnHit(w, null, { razy: 3, zOgluszenia: true }); efektBlysk(w.x, w.y, '#ffe08a'); } },
  { id: 'fulminacja', ik: '🌩️', n: 'Fulminacja', s: { ap: 50, haste: 20 },
    opis: i => 'Każde obrażenia nakładają ładunek Fulminacji. Przy <b>6</b> ładunkach piorun: <span class="mag">' + f0((60 + 0.4 * D.ap) * M(i)) + ' + 4% maks. zdrowia celu</span> (bossowie 1,5%) obrażeń magicznych, przeskakuje na 2 wrogów i daje im po 3 ładunki.',
    naObrazenia(i, w, v, typ, o) {
      if (o.zr === 'Fulminacja' || w.hp <= 0) return;
      w.fulm = (w.fulm || 0) + (o.dot ? 0.34 : 1);
      if (w.fulm >= 6) { w.fulm = 0; fulminuj(i, w); }
    } },
  { id: 'runy', ik: '🪬', n: 'Rzeźbiarz Run', s: { ad: 40, ap: 40 }, cd: 2.5,
    opis: i => OH + 'co 2,5 s (⏱️ przyspieszenie skraca) trafienie przywołuje 3 runiczne ostrza wokół celu. Po 0,8 s tną wszystkich w promieniu 85: <span class="mag">3 × ' + f0((25 + 0.25 * D.ad + 0.25 * D.ap) * M(i)) + '</span> (25 + 25% ⚔️ + 25% ✨) obrażeń magicznych.',
    naTrafienie(i, w) { if (!cdGotowe(i)) return; cdUstaw(i, 2.5); runyWokol(w, (25 + 0.25 * D.ad + 0.25 * D.ap) * M(i)); } },
  { id: 'hazard', ik: '🎲', n: 'Ostrze Hazardzisty', s: { as: 40, kryt: 10 },
    opis: i => OH + 'ataki zadają dodatkowo <span class="mag">' + f0((4 + 0.03 * gracz.zloto) * M(i)) + '</span> (4 + 3% Twojego złota, bez limitu) obrażeń magicznych. '
      + 'Po każdej fali <b>rzut monetą</b>: orzeł — +50% złota zdobytego w fali, reszka — tracisz 20% tego złota. Szczęście zwiększa szansę na orła.',
    statyDyn(i, s) { s.onHitMag += (4 + 0.03 * gracz.zloto) * M(i); },
    naKoniecFali(i) {
      const zysk = run.zlotoFali || 0; if (zysk <= 0) return;
      const p = Math.min(0.75, 0.5 + D.szczescie * 0.0015);
      if (Math.random() < p) { const z = Math.round(zysk * 0.5); dodajZloto(z, true, '🎲 Orzeł!'); toast('🎲 Orzeł! +' + z + ' 💰'); }
      else { const z = Math.round(zysk * 0.2); gracz.zloto = Math.max(0, gracz.zloto - z); toast('🎲 Reszka… −' + z + ' 💰'); }
    } },
  { id: 'koronaDemona', ik: '😈', n: 'Korona Króla Demonów', s: { hpMax: 350, ap: 40 },
    opis: i => 'Każda sekunda fali: <b>+1%</b> zadawanych obrażeń i <b>−0,5%</b> otrzymywanych (maks. ' + Math.round(20 * M(i)) + ' sekund). Teraz: <b>' + (i.stos || 0) + '</b>.',
    naStartFali(i) { i.stos = 0; i.t = 0; },
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t >= 1) { i.t = 0; i.stos = Math.min(Math.round(20 * M(i)), (i.stos || 0) + 1); } },
    modZadanych(i) { return 1 + 0.01 * (i.stos || 0); },
    modOtrzymanych(i) { return 1 - 0.005 * (i.stos || 0); } },
  { id: 'kulaDetonacji', ik: '💣', n: 'Kula Detonacji', s: { ap: 70, hpMax: 150 },
    opis: i => OH + 'co <b>3.</b> atak (raz na atak) przykleja do celu kulę detonacji. Po 1,2 s wybucha (r 100): <span class="mag">' + f0(40 + 0.4 * D.ap) + ' + 6% maks. zdrowia celu</span> (40 + 40% ✨; bossowie 1,5%) obrażeń magicznych wszystkim wokół. Wróg zabity wybuchem <b>też wybucha</b> (połowa siły) — reakcja łańcuchowa.',
    naTrafienie(i, w, k) { if (!k.glowny || k.zOgluszenia) return; i.licz = (i.licz || 0) + 1; if (i.licz % 3) return; przyklejKule(w); },
    naZabicie(i, w, o) { if (!o || o.zr !== 'Kula Detonacji' || (o.glKuli || 0) >= 3) return; const x = w.x, y = w.y, hm = w.hpMax, b = w.boss, g = (o.glKuli || 0) + 1;
      opoznione(0.15, () => wybuchKuli(x, y, hm, b, Math.pow(0.5, g), g)); } },
  { id: 'podcinacz', ik: '🦵', n: 'Podcinacz Ścięgien', s: { ad: 35, as: 30 },
    opis: i => OH + 'co <b>4.</b> atak (raz na atak) podcina cel: ogłusza go na 0,75 s, a wrogów wokół (r 90) spowalnia o 40% na 1,5 s i nacina — <b>krwawią</b> 3% maks. zdrowia na sekundę przez 3 s (bossowie 0,6%). Twoje ataki zadają <b>+20%</b> obrażeń ogłuszonym i spowolnionym wrogom.',
    naTrafienie(i, w, k) { if (!k.glowny || k.zOgluszenia) return; i.licz = (i.licz || 0) + 1; if (i.licz % 4) return;
      oglusz(w, 0.75, { zrodlo: 'Podcinacz' }); rozbryzg(w.x, w.y, '#c0392b', 8);
      obszarowe(w.x, w.y, 90, '#9fd8ff', o => { spowolnij(o, 0.4, 1.5); krwawienie(o, o.hpMax * (o.boss ? 0.006 : 0.03), 3); }, true); },
    modZadanych(i, w, typ, o) { return o && o.atak && w && (w.ogl > 0 || (w.spow > 0 && w.spowCzas > 0)) ? 1.2 : 1; } },
  { id: 'gromochron', ik: '⚡', n: 'Gromochron', s: { hpMax: 300, ap: 50 }, cd: 1,
    opis: i => 'Co <b>1 s</b> (⏱️ przyspieszenie skraca) <b>2 pioruny</b> uderzają w różnych wrogów w pobliżu (260): <span class="mag">' + f0((35 + 0.2 * D.ap + 0.02 * D.hpMax) * M(i)) + '</span> (35 + 20% ✨ + 2% maks. zdrowia) obrażeń magicznych każdy. Im więcej przyspieszenia, tym częściej (teraz co ' + fmt(100 / (100 + Math.max(0, D.haste))) + ' s).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; const cele = tasuj(wrogowie.filter(x => !x.martwy && !(x.zauroczony > 0) && !x.sojusznik && Math.hypot(x.x - gracz.x, x.y - gracz.y) < 260)).slice(0, 2); if (!cele.length) return; cdUstaw(i, 1);
      DZ.piorun(); cele.forEach(c => { dodajBlyskawice(c.x, c.y - 140, c.x, c.y, '#ffe066'); zadaj(c, (35 + 0.2 * D.ap + 0.02 * D.hpMax) * M(i), 'mag', { zr: 'Gromochron' }); }); } },
  { id: 'piekielnyTopor', ik: '🪓', n: 'Topór Piekielnego Ognia', s: { ad: 60, as: 15 },
    opis: i => OH + '(raz na atak) wokół trafionego wroga wybucha piekielny ogień (r 70): <span class="fiz">45% obrażeń ataku</span> wszystkim wrogom obok, a na ziemi zostaje <b>płonąca plama</b> (2 s), która pali i podpala. Co <b>4.</b> wybuch to <b>Erupcja</b>: słup ognia (r 120) za <span class="fiz">120% obrażeń ataku</span>, ogłuszenie na 0,4 s i większa plama ognia.',
    naTrafienie(i, w, k) { if (!k.glowny || !k.bron || k.zOgluszenia) return; i.licz = (i.licz || 0) + 1; piekielnyOgien(w, k.zadaneSurowe || 0, i.licz % 4 === 0); } },
  { id: 'atma', ik: '⚖️', n: 'Rachunek Atmy', s: { hpMax: 600, pancerz: 30, kryt: 15 },
    opis: i => 'Zyskujesz obrażenia od ataku równe <b>' + fmt(2.5 * M(i)) + '%</b> dodatkowego zdrowia (teraz +' + f0(Math.max(0, D.hpMax - 100) * 0.025 * M(i)) + ' ⚔️).',
    statyPost(i, s) { s.ad += Math.max(0, s.hpMax - 100) * 0.025 * M(i); } },
  { id: 'kostucha', ik: '⚰️', n: 'Żniwo Kostuchy', s: { ad: 45, kryt: 25, krytObr: 20 },
    opis: i => 'Trafienia krytyczne zadają dodatkowo <span class="praw">' + Math.round(40 * M(i)) + '%</span> swoich obrażeń jako obrażenia prawdziwe. Każde zabójstwo skraca odnowienia przedmiotów o 0,3 s.',
    naKryt(i, w, k) { zadaj(w, k.zadane * 0.4 * M(i), 'praw', { zr: 'Żniwo Kostuchy' }); },
    naZabicie() { skrocCd(0.3); } },
  { id: 'jaksho', ik: '🐚', n: "Jak'Sho Zmiennokształtny", s: { hpMax: 300, pancerz: 20, odpMag: 20 },
    opis: i => 'Każda sekunda fali: +6% pancerza i odporności (maks. 8). Przy 8 ładunkach rośniesz i zadajesz <b>+' + Math.round(15 * M(i)) + '%</b> obrażeń. Teraz: <b>' + (i.stos || 0) + '</b>.',
    naStartFali(i) { i.stos = 0; i.t = 0; oznaczStaty(); },
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t >= 1 && (i.stos || 0) < 8) { i.t = 0; i.stos = (i.stos || 0) + 1; oznaczStaty(); } },
    statyMnoz(i, s) { s.pancerz *= 1 + 0.06 * (i.stos || 0); s.odpMag *= 1 + 0.06 * (i.stos || 0); },
    modZadanych(i) { return (i.stos || 0) >= 8 ? 1 + 0.15 * M(i) : 1; },
    rozmiar(i) { return (i.stos || 0) >= 8 ? 1.25 : 1; } },
  { id: 'okrucienstwo', ik: '🩻', n: 'Okrucieństwo', s: { ad: 50, lethality: 12 },
    opis: i => 'Każde zabójstwo daje ładunek <b>Okrucieństwa</b> na 4 s (kolejne zabójstwo odnawia czas, maks. 12): <b>+4% obrażeń</b> i <b>+4% prędkości ataku</b> za ładunek. Przy 12 ładunkach ' + OH + 'ścinasz wrogów (nie bossów) poniżej <b>12%</b> zdrowia, a ścięty wybucha krwią (r 80) za 15% swojego maks. zdrowia. Teraz: <b>' + (czasGry < (i.do || 0) ? (i.st || 0) : 0) + '</b>.',
    naZabicie(i) { i.st = Math.min(12, (czasGry < (i.do || 0) ? (i.st || 0) : 0) + 1); i.do = czasGry + 4; oznaczStaty(); },
    statyDyn(i, s) { if (czasGry >= (i.do || 0)) i.st = 0; s.as += 4 * (i.st || 0); },
    modZadanych(i) { return czasGry < (i.do || 0) ? 1 + 0.04 * (i.st || 0) : 1; },
    naTrafienie(i, w) { if ((i.st || 0) < 12 || czasGry >= (i.do || 0) || w.boss || w.martwy || w.hp > w.hpMax * 0.12) return;
      const x = w.x, y = w.y, v = w.hpMax * 0.15; w.hp = 0; zabij(w, { zr: 'Okrucieństwo' }); tekstSwiat(x, y - 20, '🩸', '#ff4a4a', 0.6, 14);
      opoznione(0.05, () => { rozbryzg(x, y, '#c0392b', 12); obszarowe(x, y, 80, '#c0392b', o => zadaj(o, v, 'fiz', { obszar: true, zr: 'Okrucieństwo' })); }); } },
  { id: 'pozeracz', ik: '🍖', n: 'Pożeracz Ciał', s: { ad: 40, hpMax: 200 },
    opis: i => 'Każde zabójstwo daje <b>na stałe</b> +0,25 ⚔️ i +1 maks. zdrowia (elita ×3, boss ×10; maks. 5000 ładunków). Zjedzone: <b>' + (i.stos || 0) + '</b>.',
    naZabicie(i, w) { if ((i.stos || 0) >= 5000) return; i.stos = Math.min(5000, (i.stos || 0) + (w.boss ? 10 : (w.elita ? 3 : 1))); if (w.elita || w.boss || i.stos % 5 === 0) oznaczStaty(); },
    statyFlat(i, s) { s.ad += 0.25 * (i.stos || 0) * M(i); s.hpMax += (i.stos || 0) * M(i); } },
  { id: 'hemomanta', ik: '🩸', n: 'Hełm Hemomanty', s: { hpMax: 650 }, cd: 3,
    opis: i => 'Co <b>3 s</b> (⏱️ przyspieszenie skraca) krwawa fala (r 120): <span class="mag">' + f0(D.hpMax * 0.04 * M(i)) + '</span> (4% maks. zdrowia) obrażeń magicznych. Leczysz się o 30% zadanych (maks. 6% zdrowia).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna || policzWrogow(gracz.x, gracz.y, 140) === 0) return; cdUstaw(i, 3); let suma = 0;
      aura(120, '#c0392b', w => { suma += zadaj(w, D.hpMax * 0.04 * M(i), 'mag', { obszar: true, zr: 'Hełm Hemomanty' }); }, true);
      if (suma > 0) leczGracza(Math.min(suma * 0.3, D.hpMax * 0.06), 'Hełm Hemomanty'); } },
  { id: 'zefir', ik: '🕊️', n: 'Zefir', s: { as: 50, ms: 30, unik: 12, pociski: 1 },
    opis: () => 'Broń główna strzelająca wypuszcza <b>dodatkowy pocisk</b>.' },
  { id: 'lalkarz', ik: '🎭', n: 'Lalkarz', s: { ap: 40, as: 30 },
    opis: i => OH + '(raz na atak) trafienia oplatają wroga nićmi. Przy <b>4</b> niciach wróg (nie boss) zostaje przejęty na <b>' + fmt(4 * M(i)) + ' s</b> — walczy po Twojej stronie, zadając <span class="mag">3× swój atak + 30% ✨</span> innym wrogom. Bossowie są tylko ogłuszani.',
    naTrafienie(i, w, k) { if (!k.glowny || w.zauroczony > 0) return; w.nici = (w.nici || 0) + 1; if (w.nici < 4) return; w.nici = 0;
      if (w.boss) { oglusz(w, 0.6, { zrodlo: 'Lalkarz' }); return; }
      w.zauroczony = 4 * M(i); w.wlasciciel = gracz; tekstSwiat(w.x, w.y - w.r - 10, '🎭', '#ff9ae0'); } },
  { id: 'maska', ik: '🎎', n: 'Bliźniacza Maska', s: { ad: 20, ap: 20, as: 20 },
    opis: i => 'Każdy atak ma <b>' + Math.round(Math.min(60, 35 * M(i))) + '%</b> szansy powtórzyć się po chwili (echo, pełne obrażenia i efekty).',
    naAtak(i, b, cel, o) { if (o && o.echo) return; if (Math.random() < Math.min(0.6, 0.35 * M(i))) opoznione(0.14, () => echoAtaku(b, cel)); } },
  { id: 'helia', ik: '🌸', n: 'Echo Helii', s: { ap: 60, hpMax: 300, leczenie: 25 },
    opis: i => 'Zadawanie obrażeń tworzy odłamki duszy (najwyżej 4/s). Przy 5 odłamkach: leczysz się o <b>' + f0((50 + 0.1 * D.ap) * M(i)) + '</b> i zadajesz tyle samo <span class="mag">obrażeń magicznych</span> najbliższemu wrogowi.',
    naObrazenia(i, w, v, typ, o) { if (o.zr === 'Echo Helii') return; if (czasGry - (i.ost || 0) < 0.25) return; i.ost = czasGry; i.odl = (i.odl || 0) + 1;
      if (i.odl >= 5) { i.odl = 0; const val = (50 + 0.1 * D.ap) * M(i); leczGracza(val, 'Echo Helii'); const c = najblizszyWrog(gracz.x, gracz.y, 300); if (c) { dodajBlyskawice(gracz.x, gracz.y, c.x, c.y, '#ffb0e0'); zadaj(c, val, 'mag', { zr: 'Echo Helii' }); } } } },
  { id: 'ksiezyc', ik: '🌙', n: 'Kamień Księżycowy', s: { hpMax: 300, ap: 40, haste: 30 }, cd: 4,
    opis: i => 'Co 4 s tarcza <b>' + f0((40 + 0.05 * D.hpMax) * M(i)) + '</b> (40 + 5% maks. zdrowia) na 4 s.',
    tik(i) { if (cdGotowe(i) && fala.aktywna) { cdUstaw(i, 4); dajTarcze((40 + 0.05 * D.hpMax) * M(i), 4); } } },
  { id: 'lopatka', ik: '🥄', n: 'Złota Łopatka', s: { ad: 30, ap: 50, as: 30, kryt: 20, hpMax: 250, pancerz: 30, odpMag: 30, haste: 20, ms: 15,
      krytObr: 15, obrBonus: 8, lethality: 8, przebPancP: 8, przebMag: 8, przebMagP: 8, unik: 5, redukcja: 5, wytrwalosc: 15, omni: 2, zasieg: 10, przebicie: 1, obszar: 10,
      leczenie: 10, szczescie: 20, zbieranie: 30, chciwosc: 10, xpBonus: 10, obrElity: 10, onHitFiz: 6, onHitMag: 6, onHitPraw: 3 },
    opis: () => 'Trochę wszystkiego. Naprawdę <b>wszystkiego</b> — każda statystyka w grze.' },
  { id: 'wooglet', ik: '🧙', n: 'Kapelusz Wiedźmy Wooglet', s: { ap: 100, pancerz: 30 }, cd: 60,
    opis: i => 'Moc umiejętności <b>+' + Math.round(40 * M(i)) + '%</b>. Gdy zdrowie spadnie poniżej 25%: zastój na 2,5 s. Odnowienie 60 s.',
    statyMnoz(i, s) { s.ap *= 1 + 0.4 * M(i); },
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp > 0 && gracz.hp < D.hpMax * 0.25) { cdUstaw(i, 60); gracz.zastoj = 2.5; gracz.niewr = Math.max(gracz.niewr, 2.5); tekstSwiat(gracz.x, gracz.y - 28, '⏳ Zastój!', '#ffe08a'); } } },
  { id: 'gwiazda', ik: '🌟', n: 'Gwiazda Neutronowa', s: { ap: 60, obszar: 40 },
    opis: i => 'Obrażenia <b>obszarowe</b> zadają <b>+5%</b> i dodatkowo <b>+1% za każde 10 ✨</b> (przy 1000 ✨: +105%). Teraz: <b>+' + f0(5 + Math.max(0, D.ap) / 10) + '%</b>.',
    modZadanych(i, w, typ, o) { return o.obszar ? 1 + 0.05 + Math.max(0, D.ap) / 1000 : 1; } },
  { id: 'paktKrwi', ik: '🫀', n: 'Pakt Krwi', s: { hpMax: 600, omni: 3 },
    opis: i => 'Co 5 s tracisz 3% aktualnego zdrowia. Zadajesz obrażenia większe o <b>' + Math.round(60 * M(i)) + '%</b> brakującego zdrowia (przy 50% zdrowia: +' + Math.round(30 * M(i)) + '%).',
    tik(i, dt) { if (!fala.aktywna) return; i.t = (i.t || 0) + dt; if (i.t >= 5) { i.t = 0; gracz.hp = Math.max(1, gracz.hp * 0.97); } },
    modZadanych(i) { return 1 + 0.6 * M(i) * (1 - gracz.hp / D.hpMax); } },
  { id: 'lustro', ik: '🪞', n: 'Lustro Odbicia', s: { pancerz: 40, odpMag: 40, hpMax: 200 },
    opis: i => 'Odbijasz <span class="praw">' + Math.round(Math.min(150, 60 * M(i))) + '%</span> otrzymanych obrażeń jako obrażenia prawdziwe w napastnika.',
    naOtrzymanie(i, v, typ, o) { if (o.wrog && v > 0) zadaj(o.wrog, (o.przed || v) * Math.min(1.5, 0.6 * M(i)), 'praw', { zr: 'Lustro Odbicia', odbicie: true }); } },
  { id: 'kornukopia', ik: '🌽', n: 'Róg Obfitości', s: { hpMax: 200, szczescie: 30 },
    opis: i => 'Po każdej fali dostajesz <b>2</b> darmowe wybory statystyk (zawsze co najmniej rzadkie).',
    naKoniecFali(i) { gracz.darmoweWybory = (gracz.darmoweWybory || 0) + 2; } },
  { id: 'dziedzictwo', ik: '🏺', n: 'Dziedzictwo Kowala', s: { ad: 20, ap: 30, pancerz: 20 },
    opis: () => 'Przy każdej wizycie w sklepie losowy z Twoich zwykłych przedmiotów zyskuje <b>★</b>, a losowa broń dodatkowa <b>+1 tier</b> (jeśli może).',
    naSklep(i) { const kand = gracz.przedmioty.filter(p => p && DEF_PRZ[p.id].t !== 'p' && (p.gw || 0) < MAKS_GWIAZDEK); if (kand.length) { const p = losZ(kand); p.gw = (p.gw || 0) + 1; toast('🏺 ' + DEF_PRZ[p.id].n + ' zyskuje ★'); }
      const ko = gracz.oreze.filter(o => o.tier < 3); if (ko.length) { const o = losZ(ko); o.tier++; toast('🏺 ' + nazwaOreza(o)); } oznaczStaty(); } },
  // ---------------- dziwne skalowania ----------------
  { id: 'blizniaczeOstrze', ik: '🗡️', n: 'Bliźniacze Ostrze', s: { as: 25, ad: 15 },
    opis: () => 'Twoje ataki nakładają efekty ' + OH + '<b>dwukrotnie</b>.', podwojnyOnHit: true },
  { id: 'klingaRezonansu', ik: '🎼', n: 'Klinga Rezonansu', s: { kryt: 20, krytObr: 20 },
    opis: () => 'Trafienia <b>krytyczne</b> nakładają efekty ' + OH + 'jeszcze <b>2 razy</b>.', onHitKryt: 2 },
  { id: 'serceGolema', ik: '🗿', n: 'Serce Golema', s: { pancerz: 40 },
    opis: () => 'Każdy punkt pancerza daje <b>3 maks. zdrowia</b>, a ' + OH + 'ataki zadają <span class="fiz">15% pancerza</span> jako obrażenia fizyczne (teraz +' + f0(D.pancerz * 3) + ' ❤️, +' + f0(D.pancerz * 0.15) + ' przy trafieniu).',
    statyPost(i, s) { s.hpMax += 3 * Math.max(0, s.pancerz); s.onHitFiz += 0.15 * Math.max(0, s.pancerz); } },
  { id: 'odwroconaKlepsydra', ik: '⌛', n: 'Odwrócona Klepsydra', s: { haste: 30 },
    opis: () => 'Przyspieszenie zwiększa też <b>prędkość ataku</b> 1:1 (teraz +' + f0(D.haste) + '%).',
    statyPost(i, s) { s.as += Math.max(0, s.haste); } },
  { id: 'zlotyZab', ik: '🦷', n: 'Złoty Ząb', s: { chciwosc: 25 },
    opis: () => '+1 obrażeń od ataku ⚔️ i +1 mocy umiejętności ✨ za każde 12 posiadanego złota (bez limitu). Teraz: +' + f0(gracz.zloto / 12) + '.',
    statyDyn(i, s) { s.ad += gracz.zloto / 12; s.ap += gracz.zloto / 12; } },
  { id: 'mrowczaSila', ik: '🐜', n: 'Mrówcza Siła', s: { ms: 30 },
    opis: () => 'Prędkość ruchu powyżej 140 daje <b>25%</b> swojej wartości jako ⚔️ i <b>40%</b> jako ✨ (teraz +' + f0(Math.max(0, D.ms - 140) * 0.25) + ' ⚔️, +' + f0(Math.max(0, D.ms - 140) * 0.4) + ' ✨).',
    statyPost(i, s) { const n = Math.max(0, s.ms - 140); s.ad += n * 0.25; s.ap += n * 0.4; } },
  { id: 'ksiegaUmarlych', ik: '📕', n: 'Księga Umarłych', s: { ap: 30 },
    opis: () => 'Każde 10 zabójstw w tej grze: <b>+1 ✨</b> i +1 maks. zdrowia, bez limitu. Teraz: +' + Math.floor((run.zabici || 0) / 10) + '.',
    statyDyn(i, s) { const n = Math.floor((run.zabici || 0) / 10); s.ap += n; s.hpMax += n; } },
  { id: 'gwiazdaZaranna', ik: '🌠', n: 'Gwiazda Zaranna', s: { szczescie: 40 },
    opis: () => 'Każdy punkt szczęścia daje <b>0,2%</b> szansy na kryt i <b>0,4%</b> obrażeń krytycznych (teraz +' + fmt(D.szczescie * 0.2) + '% / +' + fmt(D.szczescie * 0.4) + '%).',
    statyPost(i, s) { s.kryt += Math.max(0, s.szczescie) * 0.2; s.krytObr += Math.max(0, s.szczescie) * 0.4; } },
  { id: 'kosturArcymaga', ik: '🧙', n: 'Kostur Arcymaga', s: { ap: 60 },
    opis: () => 'Całe Twoje ⚔️ zamienia się w ✨ (<b>1 ⚔️ → 2 ✨</b>). Ataki bronią zadają obrażenia <span class="mag">magiczne</span>, a przelicznik ⚔️ broni liczy się od ✨ (np. miecz 100% ⚔️ → 100% ✨). Działa po Harmonii i Wadze Sprawiedliwości.',
    wszystkoMag: true, statyKonw3(i, s) { s.ap += 2 * Math.max(0, s.ad); s.ad = 0; } },
  { id: 'zelaznaDziewica', ik: '⚙️', n: 'Żelazna Dziewica', s: { pancerz: 30, odpMag: 30, hpMax: 150 },
    opis: () => 'Otrzymujesz <b>15% więcej</b> obrażeń, ale każde trafienie odbija <span class="praw">100%</span> obrażeń (przed obroną) jako prawdziwe w napastnika i wrogów w promieniu 80.',
    modOtrzymanych() { return 1.15; },
    naOtrzymanie(i, v, typ, o) { if (!o.wrog || o.dot) return; const x = o.wrog.x, y = o.wrog.y, ob = o.przed || v; obszarowe(x, y, 80, '#d8d8e4', w => zadaj(w, ob, 'praw', { zr: 'Żelazna Dziewica', odbicie: true, obszar: true }), true); } },
  { id: 'rytualKrwi', ik: '🔪', n: 'Rytuał Krwi', s: { hpMax: 400 },
    opis: () => 'Tracisz 1,5% aktualnego zdrowia co sekundę. Każdy 1% brakującego zdrowia daje <b>+1,2%</b> obrażeń i <b>+0,25%</b> wampiryzmu.',
    tik(i, dt) { if (fala.aktywna) gracz.hp = Math.max(1, gracz.hp - gracz.hp * 0.015 * dt); },
    statyDyn(i, s) { s.omni += 25 * Math.max(0, 1 - gracz.hp / Math.max(1, s.hpMax)); },
    modZadanych() { return 1 + 1.2 * Math.max(0, 1 - gracz.hp / D.hpMax); } },
  { id: 'wagaSprawiedliwosci', ik: '⚖️', n: 'Waga Sprawiedliwości', s: { ad: 20, ap: 20 },
    opis: () => 'Twoje ⚔️ i ✨ wyrównują się do <b>wyższej</b> z nich (po Harmonii, przed Kosturem Arcymaga).',
    statyKonw2(i, s) { const m = Math.max(s.ad, s.ap); s.ad = m; s.ap = m; } },
  { id: 'grubyPortfel', ik: '💰', n: 'Gruby Portfel', s: { chciwosc: 30 },
    opis: () => '+1% obrażeń za każde 10 posiadanego złota (bez limitu). Teraz: +' + Math.round(gracz.zloto / 10) + '%.',
    modZadanych() { return 1 + gracz.zloto / 1000; } },
  { id: 'wiecznaZima', ik: '☃️', n: 'Wieczna Zima', s: { ap: 40, odpMag: 30 },
    opis: () => 'Spowolnieni wrogowie otrzymują <b>+25%</b> obrażeń. Co trzecie spowolnienie tego samego wroga <b>zamraża</b> go na 1 s.',
    naSpowolnieniu(i, w) { if (czasGry - (w._zima || 0) < 0.4) return; w._zima = czasGry; w._zimaN = (w._zimaN || 0) + 1; if (w._zimaN % 3 === 0) oglusz(w, 1, { zrodlo: 'Wieczna Zima' }); },
    modZadanych(i, w) { return w.spow > 0 && w.spowCzas > 0 ? 1.25 : 1; } },
  { id: 'pierscienSalw', ik: '💍', n: 'Pierścień Salw', s: { as: 30 },
    opis: () => '+1 pocisk broni głównej za każde 60% premii do prędkości ataku (teraz +' + Math.floor(Math.max(0, D.as) / 60) + ').',
    statyPost(i, s) { s.pociski += Math.floor(Math.max(0, s.as) / 60); } },
  { id: 'lodowyKolec', ik: '🧊', n: 'Lodowy Kolec', s: { pancerz: 30, kryt: 15 },
    opis: () => 'Obrażenia krytyczne <b>+1%</b> za każde 3 pancerza (teraz +' + f0(Math.max(0, D.pancerz) / 3) + '%).',
    statyPost(i, s) { s.krytObr += Math.max(0, s.pancerz) / 3; } },
  { id: 'astrolabium', ik: '🔭', n: 'Astrolabium', s: { xpBonus: 40 },
    opis: () => 'Każdy poziom postaci daje <b>+2 ✨</b>, <b>+1 ⚔️</b> i +4 maks. zdrowia.',
    statyFlat(i, s) { const p = gracz.poziom; s.ap += 2 * p; s.ad += p; s.hpMax += 4 * p; } },
  { id: 'mapaSkarbow', ik: '🗺️', n: 'Mapa Skarbów', s: { szczescie: 30 },
    opis: () => 'Po każdej fali dostajesz <b>skrzynię</b> (lepszą przy dużym szczęściu). Elity zostawiają 2 skrzynie.',
    naKoniecFali() { const t = D.szczescie > 120 ? 3 : D.szczescie > 70 ? 2 : D.szczescie > 30 ? 1 : 0; gracz.skrzynie.push({ tier: Math.min(3, t + (Math.random() < 0.25 ? 1 : 0)) }); },
    naZabicie(i, w) { if (w.elita && !w.bezLupu) skrzynieNaZiemi.push({ x: w.x + 12, y: w.y, tier: tierSkrzyni(w), faza: 0 }); } },
  { id: 'krysztalCzasu', ik: '💎', n: 'Kryształ Czasu', s: { haste: 40, hpMax: 150 },
    opis: () => 'Poniżej 50% zdrowia wszystkie odnowienia (broni, przedmiotów, umiejętności) płyną <b>2× szybciej</b>.', krysztalCzasu: true },
  { id: 'tarczaTytana', ik: '🛡️', n: 'Tarcza Tytana', s: { hpMax: 300, leczenie: 20 }, cd: 5,
    opis: () => 'Co 5 s tarcza <b>5% maks. zdrowia</b>. Gdy masz tarczę, ' + OH + '(raz na atak) ataki zadają dodatkowo <span class="fiz">12% jej wartości</span>.',
    tik(i) { if (cdGotowe(i) && fala.aktywna) { cdUstaw(i, 5); dajTarcze(D.hpMax * 0.05, 5); } },
    naTrafienie(i, w, k) { const t = tarczaSuma(); if (k.glowny && t > 0) zadaj(w, t * 0.12, 'fiz', { zr: 'Tarcza Tytana' }); } },
  { id: 'czerwonyKsiezyc', ik: '🌕', n: 'Czerwony Księżyc', s: { omni: 4, leczenie: 15 },
    opis: i => 'Nadmiarowe leczenie daje <b>na stałe</b> +1 ⚔️ i +1 ✨ za każde 60 punktów (bez limitu). Teraz: +' + Math.floor((i.nadmiar || 0) / 60) + '.',
    naNadleczenie(i, v) { const przed = Math.floor((i.nadmiar || 0) / 60); i.nadmiar = (i.nadmiar || 0) + v; if (Math.floor(i.nadmiar / 60) !== przed) oznaczStaty(); },
    statyFlat(i, s) { const n = Math.floor((i.nadmiar || 0) / 60); s.ad += n; s.ap += n; } },
  { id: 'lustrzaneOdbicie', ik: '🫥', n: 'Lustrzane Odbicie', s: { ad: 30, ap: 30 },
    opis: () => 'Broń główna atakuje też <b>za Tobą</b>: najbliższy wróg z drugiej strony dostaje lustrzany atak (70% obrażeń, z efektami).',
    naAtak(i, b, cel, o) { if (o && (o.echo || o.lustro)) return; const k0 = kat(gracz, cel) + Math.PI; let naj = null, nd = zasiegAtaku(b) + 30;
      for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0) continue; const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); if (d < nd && roznicaKata(Math.atan2(w.y - gracz.y, w.x - gracz.x), k0) < 1.2) { nd = d; naj = w; } }
      if (naj) { dodajBlyskawice(gracz.x, gracz.y, naj.x, naj.y, '#e6dcff'); trafienieAtakiem(naj, b, { mn: 0.7, glowny: false }); } } },
  { id: 'koronaWielu', ik: '🎭', n: 'Korona Wielu Rodzin', s: { hpMax: 150 },
    opis: () => '+8% obrażeń i +5% prędkości ataku za każdą <b>różną rodzinę broni</b>, którą nosisz (teraz: ' + liczbaRodzin() + ').',
    statyFlat(i, s) { s.as += 5 * liczbaRodzin(); }, modZadanych() { return 1 + 0.08 * liczbaRodzin(); } },
  { id: 'matkaRoju', ik: '🐝', n: 'Matka Roju', s: { ap: 30, hpMax: 150 },
    opis: () => 'Każde zabójstwo wypuszcza <b>pszczołę</b> (6 s, maks. 12 naraz). Żądli za <span class="fiz">' + f0(10 + 0.2 * D.ap) + '</span> (10 + 20% ✨).',
    naZabicie(i) { if (stwory.filter(s => s.typ === 'pszczola' && s.wl === gracz).length >= 12) return; dodajStwora('pszczola', gracz.x, gracz.y, 6, { obr: 10 + 0.2 * D.ap, zr: 'Matka Roju', ruchomy: true }); } },
  { id: 'sakwaAlchemika', ik: '🧉', n: 'Sakwa Alchemika', s: { hpMax: 200 }, cd: 12,
    opis: () => 'Gdy spadniesz poniżej <b>50% zdrowia</b>, sam wypijasz eliksir (odnowienie 12 s): leczysz się o <b>25% maks. zdrowia</b>, wrogowie w promieniu 180 dostają tyle <span class="mag">obrażeń magicznych</span>, a koledzy w tym promieniu leczą się o połowę.',
    tik(i) { if (!fala.aktywna || !cdGotowe(i) || gracz.hp >= D.hpMax * 0.5 || fala.bezLeczenia) return; cdUstaw(i, 12); const v = D.hpMax * 0.25;
      leczGracza(v, 'Sakwa Alchemika'); aura(180, '#7ee87a', w => zadaj(w, v, 'mag', { obszar: true, zr: 'Sakwa Alchemika' }), true); leczDruzyne(gracz.x, gracz.y, 180, v * 0.5, true); DZ.mikstura(); } },
  { id: 'bezdennaPaszcza', ik: '👄', n: 'Bezdenna Paszcza', s: { hpMax: 250 },
    opis: i => 'Zabicie wroga leczy o 1% jego maks. zdrowia (maks. 1% Twojego, w limicie wampiryzmu) i daje <b>na stałe</b> 0,5% tej wartości do maks. zdrowia — najwyżej +1 za zwykłego wroga, +4 za elitę, +15 za bossa, łącznie do +6000 (teraz +' + f0(i.stos || 0) + ').',
    naZabicie(i, w) { leczWampirem(Math.min(w.hpMax * 0.01, D.hpMax * 0.01), 'Bezdenna Paszcza'); if ((i.stos || 0) >= 6000) return; i.stos = Math.min(6000, (i.stos || 0) + Math.min(w.boss ? 15 : w.elita ? 4 : 1, w.hpMax * 0.005)); if (w.elita || w.boss || Math.random() < 0.1) oznaczStaty(); },
    statyFlat(i, s) { s.hpMax += i.stos || 0; } },
  { id: 'zegarZaglady', ik: '⏰', n: 'Zegar Zagłady', s: { ad: 40, ap: 40 }, cd: 10,
    opis: () => OH + 'co 10 s (⏱️ przyspieszenie skraca) następny atak zadaje <span class="praw">20% obrażeń</span> zadanych przez Ciebie w ostatnich 10 s (bossom maks. 12% ich maks. zdrowia).',
    tik(i) { if (i.start === undefined) i.start = run.zadane; },
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 10); let v = Math.max(0, run.zadane - (i.start || 0)) * 0.2; i.start = run.zadane; if (w.boss) v = Math.min(v, w.hpMax * 0.12); if (v > 1) { zadaj(w, v, 'praw', { zr: 'Zegar Zagłady' }); efektBlysk(w.x, w.y, '#ffffff'); DZ.wybuch(); } } },
  { id: 'ognistyOgon', ik: '☄️', n: 'Ognisty Ogon', s: { ms: 25 },
    opis: () => 'Zostawiasz za sobą ognisty ślad: <span class="mag">' + f0(8 + 0.12 * D.ap + 0.1 * D.ms) + '</span> (8 + 12% ✨ + 10% prędkości ruchu) co 0,5 s.',
    tik(i, dt) { if (!gracz.wRuchu || !fala.aktywna) return; i.t = (i.t || 0) + dt; if (i.t < 0.3) return; i.t = 0; polaEfektow.push({ wl: gracz, x: gracz.x, y: gracz.y, r: 30, czas: 1.6, max: 1.6, tyk: 0, rodzaj: 'ogien', obr: 8 + 0.12 * D.ap + 0.1 * D.ms, zr: 'Ognisty Ogon' }); } },
  { id: 'okoOtchlani', ik: '👁️', n: 'Oko Otchłani', s: { przebMagP: 20, przebPancP: 20 },
    opis: () => 'Wszystkie Twoje obrażenia zadają dodatkowo <span class="praw">12%</span> jako obrażenia prawdziwe.',
    naObrazenia(i, w, v, typ, o) { if (typ === 'praw' && o.zr === 'Oko Otchłani') return; if (w.hp > 0) zadaj(w, v * 0.12, 'praw', { zr: 'Oko Otchłani', bezHakow: true }); } },
  { id: 'kulaPiorunow', ik: '🔮', n: 'Kula Piorunów', s: { ap: 40, as: 20 },
    opis: i => 'Zadawane obrażenia ładują kulę (' + Math.round(Math.min(100, (i.lad || 0) / progKuli() * 100)) + '%). Pełna kula wystrzeliwuje <b>5 piorunów</b>: <span class="mag">' + f0(40 + 0.4 * D.ap + 3 * nrFali()) + '</span> każdy.',
    naObrazenia(i, w, v, typ, o) { if (o.zr === 'Kula Piorunów') return; i.lad = (i.lad || 0) + v; if (i.lad < progKuli()) return; i.lad = 0;
      tasuj(wrogowie.filter(x => !x.martwy && !(x.zauroczony > 0) && Math.hypot(x.x - gracz.x, x.y - gracz.y) < 320)).slice(0, 5).forEach(c => { dodajBlyskawice(c.x, c.y - 160, c.x, c.y, '#c9a8ff'); zadaj(c, 40 + 0.4 * D.ap + 3 * nrFali(), 'mag', { zr: 'Kula Piorunów' }); }); DZ.piorun(); } },
  { id: 'dzwonPogrzebowy', ik: '🔕', n: 'Dzwon Pogrzebowy', s: { hpMax: 200, ap: 30 }, cd: 6,
    opis: () => 'Co 6 s dzwon ogłusza wrogów w promieniu 150 na 0,8 s i zadaje im <span class="mag">3% ich maks. zdrowia</span> (bossom 1%).',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 150) === 0) return; cdUstaw(i, 6); aura(150, '#c9c0a0', w => { zadaj(w, w.hpMax * (w.boss ? 0.01 : 0.03), 'mag', { obszar: true, zr: 'Dzwon Pogrzebowy' }); oglusz(w, 0.8, { zrodlo: 'Dzwon' }); }, true); tonSlizg(220, 110, 0.6, 'sine', 0.1); } },
  { id: 'puszkaPandory', ik: '🎁', n: 'Puszka Pandory', s: { szczescie: 30, hpMax: 150 },
    opis: () => 'Po każdej fali otwierasz puszkę: <b>2 losowe nagrody</b> spośród: przedmiot (do epickiego, od 15. fali też legendarny; bez miejsca — ★ dla losowego przedmiotu), +1 tier losowej broni dodatkowej, skrzynia, 2 darmowe wybory statystyk, złoto (60 + 8 × numer fali).',
    naKoniecFali() { for (let n = 0; n < 2; n++) nagrodaPandory(); } },
  { id: 'sandaly', ik: '🪽', n: 'Skrzydlate Sandały', s: { ms: 40, unik: 10 },
    opis: i => 'Unik może przekroczyć 80% (do <b>95%</b>). Każdy unik daje <b>+10% obrażeń</b> na 5 s (do 5 razy). Teraz: ' + (i.stos || 0) + '.',
    unikMax: 95, naUniku(i) { i.stos = Math.min(5, (i.stos || 0) + 1); i.t = 5; },
    tik(i, dt) { if (i.t > 0) { i.t -= dt; if (i.t <= 0) i.stos = 0; } }, modZadanych(i) { return 1 + 0.1 * (i.stos || 0); } },
  { id: 'kregoslup', ik: '🦴', n: 'Tytanowy Kręgosłup', s: { hpMax: 300, wytrwalosc: 40 },
    opis: () => 'Jesteś odporny na <b>spowolnienia</b>. Redukcja obrażeń +12% i jej limit rośnie z 75% do 90%.',
    odpornyNaSpow: true, redukcjaMax: 90, statyFlat(i, s) { s.redukcja += 12; } },
  { id: 'ruchomyArsenal', ik: '🗃️', n: 'Ruchomy Arsenał', s: { as: 15 },
    opis: () => '<b>+2 miejsca</b> na bronie dodatkowe, ale broń główna zadaje 15% mniej obrażeń.',
    natychmiast() { gracz.slotyOreza += 2; }, mnGlownej: 0.85,
    cofnij() { gracz.slotyOreza = Math.max(0, gracz.slotyOreza - 2); while (gracz.oreze.length > gracz.slotyOreza) { const o = gracz.oreze.pop(); gracz.zloto += wartoscSprzedazyOreza(o); } } },
  { id: 'kielich', ik: '🍷', n: 'Kielich Nadmiaru', s: { omni: 9 }, kielich: true,
    opis: i => 'Limit wampiryzmu rośnie o <b>2%</b> zdrowia na sekundę, a wampiryzm <b>ponad limit nie przepada</b>: najpierw zamienia się w tarczę (do 25% maks. zdrowia), a gdy tarcza jest pełna — co sekundę wybucha wokół Ciebie (r 140) jako obrażenia magiczne. Zebrane: <b>' + f0(i.pula || 0) + '</b>.',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t < 1) return; i.t = 0; const v = Math.min(i.pula || 0, D.hpMax * 0.2); if (v < 5 || !fala.aktywna) return; i.pula -= v;
      aura(140, '#c0392b', w => zadaj(w, v, 'mag', { obszar: true, zr: 'Kielich Nadmiaru' }), true); } },
  // ---- nowe ----
  { id: 'kondensatorBurzy', ik: '⚡', n: 'Kondensator Burzy', s: { as: 30, ms: 15 }, energia: true, energiaTempo: 1, naladowanyKryt: true, naladowanyOnHit: 2,
    opis: () => 'Energia ładuje się <b>2× szybciej</b>. ⚡ <b>Naładowany atak</b> zawsze trafia krytycznie i nakłada efekty <span class="onhit">on-hit</span> <b>3 razy</b>. (Energia: bieganie i ataki.)' },
  { id: 'sercHydry', ik: '💢', n: 'Serce Hydry', s: { ad: 35, hpMax: 250 },
    opis: () => OH + '(raz na atak) każdy atak broni głównej tnie <b>wszystkich wrogów wokół Ciebie</b> (r 120): <span class="fiz">55% obrażeń ataku + 2,5% maks. zdrowia</span> obrażeń fizycznych' + (D && gracz && gracz.bronie[0] ? ' (teraz ok. ' + f0(obrBroni(gracz.bronie[0]) * 0.55 + D.hpMax * 0.025) + ')' : '') + '. Bez odnowienia — im szybciej atakujesz, tym częściej.',
    naTrafienie(i, w, k) { if (!k.glowny || !k.bron || k.zOgluszenia || i._tA === czasGry) return; i._tA = czasGry; const v = (k.zadaneSurowe || 0) * 0.55 + D.hpMax * 0.025;
      aura(120, '#c0392b', o => zadaj(o, v, 'fiz', { obszar: true, zr: 'Serce Hydry' }), true); } },
  { id: 'wiecznyMechanizm', ik: '🕰️', n: 'Wieczny Mechanizm', s: { haste: 30 },
    opis: () => OH + 'każde trafienie (każdy trafiony wróg) skraca odnowienia <b>przedmiotów, broni dodatkowych i umiejętności</b> o 0,1 s (krytyk: 0,2 s) — najwyżej o 0,5 s na jeden atak.',
    naTrafienie(i, w, k) { if (i._tA !== czasGry) { i._tA = czasGry; i._s = 0; } if (i._s >= 0.5) return; const s = Math.min(0.5 - i._s, k.kryt ? 0.2 : 0.1); i._s += s;
      [gracz.umi, gracz.umi2].forEach(u => { if (u && u.cd > 0) u.cd = Math.max(0, u.cd - s); });
      gracz.przedmioty.forEach(p => { if (p && p.cd > 0) p.cd = Math.max(0, p.cd - s); }); gracz.oreze.forEach(o => { if (o.cd > 0) o.cd = Math.max(0, o.cd - s); }); } },
  { id: 'gwiazdaNeutronowa', ik: '🔆', n: 'Pryzmat Rozproszenia', s: { ap: 40, ad: 20 }, wszyscyGlowni: true,
    opis: () => 'Efekty ' + OH + 'oznaczone „raz na atak” działają na <b>każdego</b> trafionego wroga — w łuku ciosu, przebitych pociskiem i w wybuchu (efekty z odnowieniem nadal raz).' },
];
PRYZMATY.forEach(p => { p.t = 'p'; p.unik = true; DEF_PRZ[p.id] = p; });
// ---- Kula Detonacji: kula przyklejona do wroga, wybuch po 1,2 s, reakcja łańcuchowa ----
function przyklejKule(w) {
  const hm = w.hpMax, b = w.boss;
  efektyCzasowe.push({ wl: gracz, rodzaj: 'detonacja', cel: w, x: w.x, y: w.y, r: 100, czas: 1.2, max: 1.2, koniec(e) { wybuchKuli(e.x, e.y, hm, b, 1, 0); } });
}
function wybuchKuli(x, y, hpMaxCelu, boss, sila, gl) {
  if (stan !== 'walka') return;
  DZ.wybuch(); rozbryzg(x, y, '#ff9a3c', 12);
  const v = (40 + 0.4 * D.ap + hpMaxCelu * (boss ? 0.015 : 0.06)) * sila;
  obszarowe(x, y, 100, '#ff7a2a', o => zadaj(o, v, 'mag', { obszar: true, zr: 'Kula Detonacji', glKuli: gl }));
}
// ---- Topór Piekielnego Ognia: wybuch ognia wokół celu, płonąca plama, co 4. raz Erupcja ----
function piekielnyOgien(w, sur, erupcja) {
  const x = w.x, y = w.y;
  if (erupcja) {
    efektyCzasowe.push({ wl: gracz, rodzaj: 'slupOgnia', x: x, y: y, r: 120 * mnObszaru(), czas: 0.55, max: 0.55 }); DZ.wybuch(); rozbryzg(x, y, '#ff8a2a', 16);
    obszarowe(x, y, 120, '#ff6a2a', o => { zadaj(o, sur * 1.2, 'fiz', { obszar: true, zr: 'Topór Piekielnego Ognia' }); oglusz(o, 0.4, { zrodlo: 'Erupcja' }); });
  } else obszarowe(x, y, 70, '#ff6a2a', o => { if (o !== w) zadaj(o, sur * 0.45, 'fiz', { obszar: true, zr: 'Topór Piekielnego Ognia' }); });
  if (polaEfektow.filter(p => p.zr === 'Topór Piekielnego Ognia').length < 10)
    polaEfektow.push({ wl: gracz, x: x, y: y, r: (erupcja ? 70 : 42) * mnObszaru(), czas: 2, max: 2, tyk: 0.25, rodzaj: 'ogien', obr: Math.max(4, sur * 0.12), zr: 'Topór Piekielnego Ognia' });
}
// ---- Puszka Pandory: jedna losowa nagroda ----
function nagrodaPandory() {
  const r = losZ(['przedmiot', 'przedmiot', 'oreze', 'skrzynia', 'staty', 'zloto']);
  if (r === 'przedmiot') {
    if (wolneSlotyPrzedm(false) > 0) {
      const maxT = fala.nr >= 15 ? 3 : 2, pula = PRZEDMIOTY.filter(p => p.t <= maxT && (!p.unik || !maPrzedmiot(p.id)));
      if (pula.length) { const d = losWazony(pula.map(p => [p, [6, 4, 2, 1][p.t]])); const inst = nowyPrzedmiot(d.id); gracz.przedmioty.push(inst); if (d.natychmiast) d.natychmiast(inst);
        dziennik('🎁 Puszka Pandory: ' + d.ik + ' ' + d.n); przebudujHaki(); oznaczStaty(); return; }
    }
    const kand = gracz.przedmioty.filter(p => p && DEF_PRZ[p.id].t !== 'p' && (p.gw || 0) < MAKS_GWIAZDEK);
    if (kand.length) { const p = losZ(kand); p.gw = (p.gw || 0) + 1; dziennik('🎁 Puszka Pandory: ' + DEF_PRZ[p.id].ik + ' ' + DEF_PRZ[p.id].n + ' zyskuje ★'); oznaczStaty(); return; }
  }
  if (r === 'oreze') { const ko = gracz.oreze.filter(o => o.tier < 3); if (ko.length) { const o = losZ(ko); o.tier++; dziennik('🎁 Puszka Pandory: ' + nazwaOreza(o)); oznaczStaty(); return; } }
  if (r === 'skrzynia') { gracz.skrzynie.push({ tier: Math.min(3, tierSkrzyni(null)) }); dziennik('🎁 Puszka Pandory: 📦 skrzynia'); return; }
  if (r === 'staty') { gracz.darmoweWybory = (gracz.darmoweWybory || 0) + 2; dziennik('🎁 Puszka Pandory: 2 darmowe wybory statystyk'); return; }
  const z = Math.round(60 + 8 * fala.nr); dodajZloto(z, true, 'Puszka Pandory'); dziennik('🎁 Puszka Pandory: +' + z + ' 💰');
}
function progKuli() { return 300 + 60 * nrFali(); }
function liczbaRodzin() { const r = {}; gracz.bronie.forEach(b => r[BRONIE[b.rodzaj].rodz] = 1); gracz.oreze.forEach(o => r[DEF_ORE[o.id].rodz] = 1); return Object.keys(r).length; }

function fulminuj(i, w) {
  const obr = (60 + 0.4 * D.ap + w.hpMax * (w.boss ? 0.015 : 0.04)) * M(i);
  dodajBlyskawice(w.x, w.y - 160, w.x, w.y, '#c9a8ff'); DZ.piorun();
  zadaj(w, obr, 'mag', { zr: 'Fulminacja' });
  najblizsi(w.x, w.y, 180, 2, [w]).forEach(o => { dodajBlyskawice(w.x, w.y, o.x, o.y, '#c9a8ff'); o.fulm = (o.fulm || 0) + 3; });
}

// =====================================================================
//  AUGMENTY (jak na Arenie): szare, złote i pryzmatyczne.
//  Każdy augment można ulepszyć w sklepie do poziomu III.
// =====================================================================
const MN_AUG = [1, 1.6, 2.3];
const MAKS_POZ_AUG = 3;
const MA = a => MN_AUG[Math.max(0, Math.min(2, ((a && a.poz) || 1) - 1))];
const CENY_ULEPSZ_AUG = { s: [80, 150], z: [140, 260], p: [220, 400] };
function cenaUlepszeniaAug(a) { const d = DEF_AUG[a.id]; return Math.round(CENY_ULEPSZ_AUG[d.r][(a.poz || 1) - 1] * mnCeny()); }
function rzymska(n) { return ['I', 'II', 'III'][(n || 1) - 1]; }

const AUGMENTY = [
  // ---------------- SZARE ----------------
  { id: 'grubeKosci', r: 's', ik: '🦴', n: 'Grube kości', opis: a => '+' + Math.round(20 * MA(a)) + '% maks. zdrowia.', statyMnoz(a, s) { s.hpMax *= 1 + 0.2 * MA(a); } },
  { id: 'szybkiePalce', r: 's', ik: '⚡', n: 'Szybkie palce', s: { as: 28 } },
  { id: 'skupienie', r: 's', ik: '🎯', n: 'Skupienie', s: { kryt: 14, krytObr: 20 } },
  { id: 'luski', r: 's', ik: '🐉', n: 'Smocze łuski', s: { pancerz: 35, odpMag: 35 } },
  { id: 'lekkieButy', r: 's', ik: '🪶', n: 'Lekkie stopy', s: { ms: 30, unik: 7 } },
  { id: 'zbieraczka', r: 's', ik: '🧲', n: 'Zbieracz', s: { zbieranie: 90, xpBonus: 20 } },
  { id: 'chciwosc', r: 's', ik: '💰', n: 'Chciwość', s: { chciwosc: 35 } },
  { id: 'pijawka', r: 's', ik: '🦇', n: 'Pijawka', s: { omni: 1.5 } },
  { id: 'ostrzeIKostur', r: 's', ik: '⚔️', n: 'Ostrze i kostur', s: { ad: 20, ap: 35 } },
  { id: 'szczesciara', r: 's', ik: '🍀', n: 'Szczęściarz', s: { szczescie: 35 } },
  { id: 'dlugieRece', r: 's', ik: '🏹', n: 'Długie ręce', s: { zasieg: 28 } },
  { id: 'regeneracja', r: 's', ik: '💗', n: 'Regeneracja', opis: a => 'Twoja regeneracja (każda postać trochę się regeneruje) jest <b>' + fmt(1 + 3 * MA(a)) + '×</b> silniejsza.' + (D && gracz ? ' Teraz: ' + fmt(regenNaSekunde()) + ' zdrowia/s.' : ''),
    mnRegen(a) { return 1 + 3 * MA(a); } },
  { id: 'przyspieszenie', r: 's', ik: '⏱️', n: 'Przyspieszenie', s: { haste: 35 } },
  { id: 'ciezkaReka', r: 's', ik: '👑', n: 'Ciężka ręka', s: { obrElity: 35 } },
  { id: 'precyzja', r: 's', ik: '🔍', n: 'Precyzja', s: { przebPancP: 15, przebMagP: 15 } },
  { id: 'kamiennaSkora', r: 's', ik: '🪨', n: 'Kamienna skóra', s: { redukcja: 8, hpMax: 40 } },
  { id: 'kolce', r: 's', ik: '🌵', n: 'Kolce', opis: a => 'Odbijasz <span class="mag">' + Math.round(50 * MA(a)) + '%</span> obrażeń otrzymanych wręcz jako obrażenia magiczne.',
    naOtrzymanie(a, v, typ, o) { if (o.wrog && o.wrecz) zadaj(o.wrog, (o.przed || v) * 0.5 * MA(a), 'mag', { zr: 'Kolce', odbicie: true }); } },
  { id: 'pierwszaKrew', r: 's', ik: '🩸', n: 'Pierwsza krew', opis: a => 'Pierwsze trafienie każdego wroga zadaje <b>+' + Math.round(70 * MA(a)) + '%</b> obrażeń.',
    modZadanych(a, w) { if (!w._pk) { w._pk = 1; return 1 + 0.7 * MA(a); } return 1; } },
  { id: 'ladunekStatyczny', r: 's', ik: '🔋', n: 'Ładunek statyczny', opis: a => 'Co 8. atak razi piorunem 3 wrogów: <span class="mag">' + f0((60 + 0.4 * D.ad + 0.4 * D.ap) * MA(a)) + '</span> (60 + 40% ⚔️ + 40% ✨).',
    naAtak(a, b, cel) { a.licz = (a.licz || 0) + 1; if (a.licz % 8 === 0) lancuch(gracz, cel, (60 + 0.4 * D.ad + 0.4 * D.ap) * MA(a), 'mag', 3, 170, 1, 'Ładunek statyczny'); } },
  { id: 'egzekutorka', r: 's', ik: '🪓', n: 'Egzekutor', opis: a => 'Dobija zwykłych wrogów (nie elity, nie bossów) poniżej <b>' + Math.round(10 + 4 * (MA(a) - 1) * 2) + '%</b> zdrowia.',
    naObrazenia(a, w) { const p = 0.10 + 0.08 * (MA(a) - 1); if (!w.boss && !w.elita && w.hp > 0 && w.hp < w.hpMax * p) { w.hp = 0; zabij(w, { zr: 'Egzekutor' }); } } },
  { id: 'zapasMikstur', r: 's', ik: '💨', n: 'Drugi oddech', opis: a => 'Gdy spadniesz poniżej <b>35% zdrowia</b>: leczysz się o <b>35% maks. zdrowia</b> i masz 1 s niewrażliwości. Działa <b>' + ((a && a.poz) || 1) + '×</b> na falę (ulepszenie: +1 raz).',
    naStartFali(a) { a.uzyte = 0; },
    tik(a) { if (!fala.aktywna || gracz.hp >= D.hpMax * 0.35 || gracz.hp <= 0 || (a.uzyte || 0) >= ((a.poz) || 1) || fala.bezLeczenia) return; a.uzyte = (a.uzyte || 0) + 1;
      leczGracza(D.hpMax * 0.35, 'Drugi oddech'); gracz.niewr = Math.max(gracz.niewr || 0, 1); tekstSwiat(gracz.x, gracz.y - 30, '💨 Drugi oddech', '#9fe8ff', 1, 14); DZ.mikstura(); } },
  { id: 'lodoweDotkniecie', r: 's', ik: '🧊', n: 'Lodowe dotknięcie', opis: a => OH + 'ataki spowalniają o <b>' + Math.round(Math.min(50, 25 * MA(a))) + '%</b> na 1 s.',
    naTrafienie(a, w) { spowolnij(w, Math.min(0.5, 0.25 * MA(a)), 1); } },
  { id: 'podpalaczka', r: 's', ik: '🔥', n: 'Podpalacz', opis: a => OH + 'ataki podpalają: <span class="mag">' + f0((14 + 0.15 * D.ad + 0.15 * D.ap) * MA(a)) + '</span> (14 + 15% ⚔️ + 15% ✨) na sekundę przez 3 s.',
    naTrafienie(a, w) { podpal(w, (14 + 0.15 * D.ad + 0.15 * D.ap) * MA(a), 3, 'mag', 'Podpalacz'); } },
  { id: 'wytrwalosc', r: 's', ik: '🧱', n: 'Wytrwałość', s: { wytrwalosc: 35 }, opis: a => 'Bossowie zadają Ci <b>' + Math.round(Math.min(45, 20 * MA(a))) + '%</b> mniej obrażeń.',
    modOtrzymanych(a, v, typ, o) { return o.wrog && o.wrog.boss ? 1 - Math.min(0.45, 0.2 * MA(a)) : 1; } },
  { id: 'kupiecki', r: 's', ik: '🏪', n: 'Kupiecki zmysł', opis: () => 'Ceny w sklepie −12%, a pierwszy przerzut w każdym sklepie jest darmowy. Ulepszenie: kolejne −12% i +1 darmowy przerzut.',
    natychmiast() { gracz.rabat += 12; gracz.darmowePrzerzuty += 1; }, naUlepszenie() { gracz.rabat += 12; gracz.darmowePrzerzuty += 1; } },
  { id: 'weteran', r: 's', ik: '🎖️', n: 'Weteran', opis: () => 'Natychmiast <b>4</b> darmowe wybory statystyk. Ulepszenie: kolejne 4.',
    natychmiast() { gracz.darmoweWybory = (gracz.darmoweWybory || 0) + 4; }, naUlepszenie() { gracz.darmoweWybory = (gracz.darmoweWybory || 0) + 4; } },
  { id: 'zwinnosc', r: 's', ik: '💨', n: 'Zwinność', opis: a => 'Po otrzymaniu obrażeń +' + f0(55 * MA(a)) + ' prędkości ruchu na 1,5 s.',
    naOtrzymanie(a) { dodajBuff('zwinnosc', { ms: 55 * MA(a) }, 1.5); } },
  { id: 'tarczaStartowa', r: 's', ik: '🔰', n: 'Bariera', opis: a => 'Na początku każdej fali tarcza <b>' + Math.round(40 * MA(a)) + '% maks. zdrowia</b> na 12 s.',
    naStartFali(a) { dajTarcze(D.hpMax * 0.4 * MA(a), 12); } },
  { id: 'oszczedny', r: 's', ik: '🧾', n: 'Oszczędny', opis: a => 'Przerzuty sklepu są o <b>' + Math.round(Math.min(80, 35 * MA(a))) + '%</b> tańsze, a ulepszanie broni głównej o ' + Math.round(Math.min(50, 15 * MA(a))) + '%.', oszczedny: a => MA(a) },
  { id: 'adrenalina', r: 's', ik: '💉', n: 'Adrenalina', opis: a => 'Poniżej 40% zdrowia: <b>+' + Math.round(35 * MA(a)) + '%</b> prędkości ataku i +30 prędkości ruchu.',
    statyDyn(a, s) { if (gracz.hp < s.hpMax * 0.4) { s.as += 35 * MA(a); s.ms += 30; } } },

  // ---------------- ZŁOTE ----------------
  { id: 'kieszen', r: 'z', ik: '👜', n: 'Dodatkowa kieszeń', opis: () => '<b>+1 miejsce</b> na przedmiot. Ulepszenie: kolejne miejsce.', natychmiast() { gracz.slotyPrzedm++; }, naUlepszenie() { gracz.slotyPrzedm++; } },
  { id: 'zbrojmistrz', r: 'z', ik: '🗡️', n: 'Zbrojmistrz', opis: () => '<b>+1 miejsce</b> na broń dodatkową. Ulepszenie: kolejne miejsce.', natychmiast() { gracz.slotyOreza++; }, naUlepszenie() { gracz.slotyOreza++; } },
  { id: 'mocOgnia', r: 'z', ik: '➶', n: 'Siła ognia', s: { pociski: 1 }, opis: () => 'Broń główna strzelająca wypuszcza dodatkowy pocisk (za każdy poziom).' },
  { id: 'wampiryzm', r: 'z', ik: '🧛', n: 'Wampiryzm', s: { omni: 3 }, opis: a => 'Nadmiar leczenia zamienia się w tarczę (do ' + Math.round(18 * MA(a)) + '% maks. zdrowia).',
    naNadleczenie(a, v) { const max = D.hpMax * 0.18 * MA(a), ob = tarczaSuma(); if (ob < max) dajTarcze(Math.min(v, max - ob), 6, true); } },
  { id: 'szklaneDzialo', r: 'z', ik: '🔭', n: 'Szklane działo', s: { obrBonus: 45 }, opis: () => '−20% maks. zdrowia.', statyMnoz(a, s) { s.hpMax *= 0.8; } },
  { id: 'ostatniaKropla', r: 'z', ik: '🩸', n: 'Ostatnia kropla', opis: a => 'Zadajesz +' + fmt(0.7 * MA(a)) + '% obrażeń za każdy 1% brakującego zdrowia.',
    modZadanych(a) { return 1 + 0.7 * MA(a) * (1 - gracz.hp / D.hpMax); } },
  { id: 'mistrzOstrzy', r: 'z', ik: '🌟', n: 'Mistrz ostrzy', s: { kryt: 18 }, opis: a => 'Trafienia krytyczne skracają odnowienia o ' + fmt(0.35 * MA(a)) + ' s.',
    naKryt(a) { skrocCd(0.35 * MA(a)); } },
  { id: 'burzaOstrzy', r: 'z', ik: '🌀', n: 'Burza ostrzy', opis: a => '3 ostrza krążą wokół Ciebie (r 80): <span class="fiz">' + f0((35 + 0.5 * D.ad + 0.35 * D.ap) * MA(a)) + '</span> (35 + 50% ⚔️ + 35% ✨).',
    tik(a, dt) { orbitujace(a, dt, 3, 80, '#ffe08a', () => (35 + 0.5 * D.ad + 0.35 * D.ap) * MA(a), 'fiz', 'Burza ostrzy'); } },
  { id: 'piromanka', r: 'z', ik: '🎆', n: 'Piroman', opis: a => 'Płonący wrogowie wybuchają po śmierci (r 80): <span class="mag">' + f0((50 + 0.4 * D.ap) * MA(a)) + '</span> i podpalają sąsiadów.',
    naZabicie(a, w) { if (!w.ogien || !w.ognie || !Object.keys(w.ognie).some(k => k !== 'Piroman')) return; const x = w.x, y = w.y, dps = (dpsOgnia(w) || 10) * 0.5, v = (50 + 0.4 * D.ap) * MA(a);
      opoznione(0.05, () => obszarowe(x, y, 80, '#ff7a3c', o => { zadaj(o, v, 'mag', { obszar: true, zr: 'Piroman' }); podpal(o, dps, 3, 'mag', 'Piroman'); })); } },
  { id: 'mroznaAura', r: 'z', ik: '❄️', n: 'Mroźna aura', opis: a => 'Wrogowie w promieniu 150 są spowolnieni o ' + Math.round(Math.min(55, 30 * MA(a))) + '%.',
    tik(a) { const r = 150 * mnObszaru(), p = Math.min(0.55, 0.3 * MA(a)); wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < r + w.r) spowolnij(w, p, 0.2); }); } },
  { id: 'echo', r: 'z', ik: '🔁', n: 'Echo', opis: a => Math.round(Math.min(60, 25 * MA(a))) + '% szansy, że atak broni głównej się powtórzy.',
    naAtak(a, b, cel, o) { if (o && o.echo) return; if (Math.random() < Math.min(0.6, 0.25 * MA(a))) opoznione(0.16, () => echoAtaku(b, cel)); } },
  { id: 'lancuchBlyskawic', r: 'z', ik: '⛓️', n: 'Łańcuch błyskawic', opis: a => 'Trafienia krytyczne wywołują łańcuch piorunów (4 cele): <span class="mag">' + Math.round(70 * MA(a)) + '%</span> obrażeń krytyku.',
    naKryt(a, w, k) { lancuch(gracz, w, k.zadane * 0.7 * MA(a), 'mag', 4, 170, 0.9, 'Łańcuch błyskawic', true); } },
  { id: 'gruboskorna', r: 'z', ik: '🦏', n: 'Gruboskórny', s: { hpMax: 150, redukcja: 15 } },
  { id: 'tytan', r: 'z', ik: '🗿', n: 'Tytan', opis: a => '+' + Math.round(25 * MA(a)) + '% maks. zdrowia, ' + OH + 'ataki zadają <span class="fiz">' + fmt(2.5 * MA(a)) + '% Twojego maks. zdrowia</span>. Jesteś większy.',
    statyMnoz(a, s) { s.hpMax *= 1 + 0.25 * MA(a); }, statyPost(a, s) { s.onHitFiz += s.hpMax * 0.025 * MA(a); }, rozmiar() { return 1.15; } },
  { id: 'alchemiczka', r: 'z', ik: '⚗️', n: 'Alchemik', opis: a => 'Co <b>10 s</b> w walce rozbijasz eliksir: Ty i koledzy w promieniu 150 leczycie się o <b>' + fmt(8 * MA(a)) + '%</b> maks. zdrowia, a Ty dostajesz +' + Math.round(35 * MA(a)) + '% prędkości ataku na 5 s.',
    tik(a) { if (!fala.aktywna || a.cd > 0) return; a.cd = 10 * 100 / (100 + Math.max(0, D.haste)); leczDruzyne(gracz.x, gracz.y, 150, 0, true, 0.08 * MA(a)); dodajBuff('alchemia', { as: 35 * MA(a) }, 5); fale.push({ x: gracz.x, y: gracz.y, czas: 0.4, max: 0.4, r: 150, kolor: '#7ee87a' }); } },
  { id: 'inwestorka', r: 'z', ik: '📈', n: 'Inwestor', opis: a => 'Na koniec fali odsetki: ' + Math.round(15 * MA(a)) + '% posiadanego złota (maks. ' + f0(45 * MA(a)) + ').',
    naKoniecFali(a) { const z = Math.min(45 * MA(a), gracz.zloto * 0.15 * MA(a)); if (z >= 1) dodajZloto(Math.floor(z), true, 'Odsetki'); } },
  { id: 'kowal', r: 'z', ik: '⚒️', n: 'Kowal', opis: a => 'Przy każdej wizycie w sklepie ' + (MA(a) > 1.5 ? '2 losowe przedmioty zyskują' : 'losowy przedmiot zyskuje') + ' ★ za darmo.',
    naSklep(a) { for (let n = 0; n < (MA(a) > 1.5 ? 2 : 1); n++) { const kand = gracz.przedmioty.filter(p => p && DEF_PRZ[p.id].t !== 'p' && (p.gw || 0) < MAKS_GWIAZDEK); if (!kand.length) return; const p = losZ(kand); p.gw = (p.gw || 0) + 1; toast('⚒️ ' + DEF_PRZ[p.id].n + ' zyskuje ★'); } oznaczStaty(); } },
  { id: 'ogluszacz', r: 'z', ik: '💫', n: 'Ogłuszacz', opis: a => OH + 'ataki mają ' + Math.round(Math.min(30, 12 * MA(a))) + '% szansy ogłuszyć na 0,6 s.',
    naTrafienie(a, w, k) { if (!k.zOgluszenia && Math.random() < Math.min(0.3, 0.12 * MA(a))) oglusz(w, 0.6, { zrodlo: 'Ogłuszacz' }); } },
  { id: 'krysztalowaSkora', r: 'z', ik: '💎', n: 'Kryształowa skóra', cd: 7, opis: a => 'Co ' + fmt(7 / MA(a)) + ' s blokuje jedno trafienie.',
    modOtrzymanych(a, v, typ, o) { if (cdGotowe(a) && v > 0 && !o.dot) { cdUstaw(a, 7 / MA(a)); tekstSwiat(gracz.x, gracz.y - 26, '💎', '#bff0ff'); return 0; } return 1; } },
  { id: 'olowiane', r: 'z', ik: '📌', n: 'Ołowiane pociski', s: { przebicie: 2 }, opis: a => 'Pociski zadają +' + Math.round(15 * MA(a)) + '% obrażeń.',
    modZadanych(a, w, typ, o) { return o.pocisk ? 1 + 0.15 * MA(a) : 1; } },
  { id: 'magiczneOstrze', r: 'z', ik: '🔮', n: 'Magiczne ostrze', opis: a => OH + 'ataki zadają dodatkowo <span class="mag">' + f0((15 + 0.3 * D.ap) * MA(a)) + '</span> (15 + 30% ✨) obrażeń magicznych.',
    statyKonc(a, s) { s.onHitMag += (15 + 0.3 * s.ap) * MA(a); } },
  { id: 'rozblysk', r: 'z', ik: '💥', n: 'Rozbłysk', cd: 5, opis: a => 'Co 5 s wybuch wokół Ciebie (r 120): <span class="mag">' + f0((55 + 0.7 * D.ap + 0.4 * D.ad) * MA(a)) + '</span> (55 + 70% ✨ + 40% ⚔️).',
    tik(a) { if (!cdGotowe(a) || policzWrogow(gracz.x, gracz.y, 120) === 0) return; cdUstaw(a, 5); aura(120, '#ffd24a', w => zadaj(w, (55 + 0.7 * D.ap + 0.4 * D.ad) * MA(a), 'mag', { obszar: true, zr: 'Rozbłysk' }), true); } },
  { id: 'glod', r: 'z', ik: '🍗', n: 'Wieczny głód', opis: a => 'Każde zabójstwo daje na stałe +' + fmt(0.7 * MA(a)) + ' maks. zdrowia (maks. +' + f0(400 * MA(a)) + '). Teraz: +' + fmt(Math.min(400 * MA(a), (a.stos || 0) * 0.7 * MA(a))) + '.',
    naZabicie(a) { if ((a.stos || 0) < 2000) { a.stos = (a.stos || 0) + 1; if (a.stos % 4 === 0) oznaczStaty(); } },
    statyFlat(a, s) { s.hpMax += Math.min(400 * MA(a), (a.stos || 0) * 0.7 * MA(a)); } },
  { id: 'wszechstronnosc', r: 'z', ik: '⚖️', n: 'Wszechstronność', opis: a => 'Za każdą różną rodzinę broni (główna + dodatkowe): +' + Math.round(7 * MA(a)) + '% obrażeń i +' + Math.round(5 * MA(a)) + '% prędkości ataku.',
    statyFlat(a, s) { s.as += 5 * MA(a) * liczbaRodzin(); }, modZadanych(a) { return 1 + 0.07 * MA(a) * liczbaRodzin(); } },
  { id: 'nekromantka', r: 'z', ik: '💀', n: 'Nekromanta', opis: a => 'Zabici wrogowie mają ' + Math.round(10 * MA(a)) + '% szansy powstać jako Twój sojusznik na 8 s.',
    naZabicie(a, w) { if (!w.boss && !w.sojusznik && Math.random() < 0.1 * MA(a)) wskrzesSojusznika(w); } },
  { id: 'lowczyniGlow', r: 'z', ik: '🏆', n: 'Łowca głów', opis: a => 'Każda zabita elita daje darmowy wybór statystyk (najwyżej ' + (MA(a) > 1.5 ? 4 : 2) + ' na falę), a boss — ' + (MA(a) > 1.5 ? 4 : 2) + ' dodatkowe.',
    naStartFali(a) { a.wFali = 0; },
    naZabicie(a, w) { const lim = MA(a) > 1.5 ? 4 : 2; if (w.boss) gracz.darmoweWybory = (gracz.darmoweWybory || 0) + lim; else if (w.elita && (a.wFali || 0) < lim) { a.wFali = (a.wFali || 0) + 1; gracz.darmoweWybory = (gracz.darmoweWybory || 0) + 1; } } },
  { id: 'ped', r: 'z', ik: '🐎', n: 'Pęd', opis: a => 'Ruch buduje ładunki (do 100). Przy 100 ' + OH + 'następny atak zadaje dodatkowo <span class="fiz">' + f0((80 + 1.2 * D.ad) * MA(a)) + '</span> (80 + 120% ⚔️) i spowalnia o 50%.',
    tik(a, dt) { if (gracz.wRuchu) a.lad = Math.min(100, (a.lad || 0) + dt * 45); },
    naTrafienie(a, w, k) { if (k.glowny && (a.lad || 0) >= 100) { a.lad = 0; zadaj(w, (80 + 1.2 * D.ad) * MA(a), 'fiz', { zr: 'Pęd' }); spowolnij(w, 0.5, 1.5); efektBlysk(w.x, w.y, '#ffd24a'); } } },
  { id: 'krytycznyRytm', r: 'z', ik: '🥁', n: 'Krytyczny rytm', opis: a => 'Trafienia <b>krytyczne</b> nakładają efekty <span class="onhit">on-hit</span> jeszcze <b>' + ((a && a.poz) || 1) + '×</b>.', onHitKryt: a => (a.poz || 1) },
  { id: 'mistrzWiezyczek', r: 'z', ik: '🛠️', n: 'Mistrz wieżyczek', opis: a => 'Twoje działka, wieże, krzaki, pszczoły i inne stworzenia zadają <b>+' + Math.round(40 * MA(a)) + '%</b> obrażeń i leczą o tyle mocniej.',
    mnStworow: a => 0.4 * MA(a) },
  { id: 'kaskada', r: 'z', ik: '🌊', n: 'Kaskada broni', opis: a => 'Efekty broni dodatkowych są o <b>' + Math.round(25 * MA(a)) + '%</b> silniejsze, a ich odnowienia o ' + Math.round(Math.min(40, 15 * MA(a))) + '% krótsze.',
    mnOreza: a => 0.25 * MA(a), cdOreza: a => Math.min(0.4, 0.15 * MA(a)) },
  { id: 'skupienieMocy', r: 'z', ik: '🌀', n: 'Skupienie mocy', opis: a => 'Umiejętność postaci odnawia się o <b>' + Math.round(Math.min(50, 20 * MA(a))) + '%</b> szybciej i jest o ' + Math.round(25 * MA(a)) + '% silniejsza.',
    cdUmi: a => Math.min(0.5, 0.2 * MA(a)), mnUmi: a => 0.25 * MA(a) },

  // ---------------- PRYZMATYCZNE ----------------
  { id: 'kowadloAug', r: 'p', ik: '🔨', n: 'Pryzmatyczne kowadło', opis: () => 'Natychmiast wybierz <b>przedmiot pryzmatyczny</b>. Ulepszenie: kolejne kowadło.',
    natychmiast() { gracz.kowadla = (gracz.kowadla || 0) + 1; }, naUlepszenie() { gracz.kowadla = (gracz.kowadla || 0) + 1; } },
  { id: 'wielorekaAug', r: 'p', ik: '🦑', n: 'Wieloręki', opis: a => '<b>+2 miejsca</b> na bronie dodatkowe. Każda broń dodatkowa daje +' + Math.round(6 * MA(a)) + '% prędkości ataku.',
    natychmiast() { gracz.slotyOreza += 2; }, statyFlat(a, s) { s.as += 6 * MA(a) * gracz.oreze.length; } },
  { id: 'kwintesencja', r: 'p', ik: '💠', n: 'Kwintesencja', opis: a => 'Statystyki z broni dodatkowych i pancerza są większe o ' + Math.round(35 * MA(a)) + '%.', mnPrzedmiotow: a => 0.35 * MA(a) },
  { id: 'zamiana', r: 'p', ik: '☯️', n: 'Harmonia', opis: a => 'Twoje ⚔️ zwiększają ✨ o ' + Math.round(60 * MA(a)) + '% swojej wartości — i odwrotnie. Działa przed Wagą Sprawiedliwości i Kosturem Arcymaga.',
    statyKonw1(a, s) { const ad = s.ad, ap = s.ap, m = 0.6 * MA(a); s.ad += ap * m; s.ap += ad * m; } },
  { id: 'bogini', r: 'p', ik: '👼', n: 'Bogini', opis: a => 'Gdy zginiesz, odradzasz się z PEŁNYM zdrowiem. Ładuje się raz na ' + Math.max(1, 3 - ((a && a.poz) || 1)) + ' fal(e). ' + ((a.lad || 0) > 0 ? '<b class="czer">Ładuje się</b>' : '<b class="ziel">Gotowa</b>'),
    naSmierc(a) { if ((a.lad || 0) > 0) return false; a.lad = Math.max(1, 3 - (a.poz || 1)); gracz.hp = D.hpMax; gracz.niewr = 2.5; tekstSwiat(gracz.x, gracz.y - 30, '👼 Odrodzenie!', '#fff6c0'); DZ.pryzmat(); return true; },
    naKoniecFali(a) { if (a.lad > 0) a.lad--; } },
  { id: 'grawitacja', r: 'p', ik: '🕳️', n: 'Grawitacja', cd: 6, opis: a => 'Co 6 s wciągasz wrogów z promienia ' + f0(230 * Math.sqrt(MA(a))) + ' do siebie, ogłuszasz ich na 0,6 s i zadajesz <span class="mag">' + f0((30 + 0.3 * D.ap) * MA(a)) + '</span>.',
    tik(a) { if (!cdGotowe(a) || policzWrogow(gracz.x, gracz.y, 230) < 2) return; cdUstaw(a, 6); const r = 230 * Math.sqrt(MA(a)) * mnObszaru();
      fale.push({ x: gracz.x, y: gracz.y, czas: 0.45, max: 0.45, r: r, kolor: '#9a6aff', odwrot: true });
      wrogowie.forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - gracz.x, w.y - gracz.y) > r) return; const k = kat(w, gracz), d = Math.hypot(w.x - gracz.x, w.y - gracz.y); const o = Math.max(0, d - 40) * (w.boss ? 0.25 : 0.85);
        w.x += Math.cos(k) * o; w.y += Math.sin(k) * o; oglusz(w, 0.6, { zrodlo: 'Grawitacja' }); zadaj(w, (30 + 0.3 * D.ap) * MA(a), 'mag', { obszar: true, zr: 'Grawitacja' }); }); tonSlizg(300, 60, 0.4, 'sine', 0.12); } },
  { id: 'wiecznyOgien', r: 'p', ik: '🔥', n: 'Wieczny ogień', opis: a => 'Wszystkie Twoje obrażenia podpalają: <span class="mag">' + fmt(1.5 * MA(a)) + '% maks. zdrowia celu</span>/s przez 3 s (bossowie 1/3). Płonący wrogowie otrzymują +' + Math.round(15 * MA(a)) + '% obrażeń.',
    naObrazenia(a, w, v, typ, o) { if (!o.dot && w.hp > 0) podpal(w, w.hpMax * (w.boss ? 0.005 : 0.015) * MA(a), 3, 'mag', 'Wieczny ogień'); },
    modZadanych(a, w) { return w.ogien ? 1 + 0.15 * MA(a) : 1; } },
  { id: 'krytycznaMasa', r: 'p', ik: '☢️', n: 'Krytyczna masa', s: { kryt: 30 }, opis: () => 'Szansa na kryt może przekroczyć 100% — nadmiar to szansa na <b>superkryt</b> (podwójne obrażenia krytyczne).', superkryt: true },
  { id: 'szybkostrzelnosc', r: 'p', ik: '🔫', n: 'Szybkostrzelność', s: { as: 80, obrBonus: -10 } },
  { id: 'tytaniczna', r: 'p', ik: '🏔️', n: 'Tytaniczna moc', opis: a => '+' + Math.round(45 * MA(a)) + '% maks. zdrowia. +1% obrażeń za każde 100 maks. zdrowia.',
    statyMnoz(a, s) { s.hpMax *= 1 + 0.45 * MA(a); }, modZadanych() { return 1 + D.hpMax / 10000; } },
  { id: 'zloteRuno', r: 'p', ik: '🐏', n: 'Złote runo', opis: a => 'Złoto to siła: +1 ⚔️ za każde ' + f0(15 / MA(a)) + ' złota i +1 ✨ za każde ' + f0(10 / MA(a)) + ' złota (bez limitu).',
    statyDyn(a, s) { s.ad += gracz.zloto / 15 * MA(a); s.ap += gracz.zloto / 10 * MA(a); } },
  { id: 'klonowanie', r: 'p', ik: '🧬', n: 'Klonowanie', opis: () => 'Dostajesz <b>dodatkowe miejsce</b> i kopię losowego posiadanego przedmiotu (także pryzmatycznego). Ulepszenie: kolejny klon.',
    natychmiast() { klonujPrzedmiot(); }, naUlepszenie() { klonujPrzedmiot(); } },
  { id: 'paktDemona', r: 'p', ik: '👹', n: 'Pakt z demonem', opis: () => '<b>+2 miejsca</b> na przedmioty, ale −25% maks. zdrowia. Ulepszenie: kolejne miejsce.',
    natychmiast() { gracz.slotyPrzedm += 2; }, naUlepszenie() { gracz.slotyPrzedm += 1; }, statyMnoz(a, s) { s.hpMax *= 0.75; } },
  { id: 'burza', r: 'p', ik: '⛈️', n: 'Burza', opis: a => 'Co ' + fmt(0.5 / MA(a)) + ' s piorun w losowego wroga (r 280): <span class="mag">' + f0(40 + 0.25 * D.ap + 0.25 * D.ad) + '</span> (40 + 25% ✨ + 25% ⚔️).',
    tik(a, dt) { a.t = (a.t || 0) + dt; if (a.t < 0.5 / MA(a)) return; a.t = 0; const c = losowyWrog(gracz.x, gracz.y, 280); if (!c) return;
      dodajBlyskawice(c.x + losowo(-30, 30), c.y - 150, c.x, c.y, '#bfe0ff'); DZ.piorun(); zadaj(c, 40 + 0.25 * D.ap + 0.25 * D.ad, 'mag', { zr: 'Burza' }); } },
  { id: 'mistrzyniCzasu', r: 'p', ik: '⌛', n: 'Mistrz czasu', s: { haste: 100 } },
  { id: 'wampirzyLord', r: 'p', ik: '🧛', n: 'Wampirzy władca', s: { omni: 4, leczenie: 25 } },
  { id: 'armagedon', r: 'p', ik: '☄️', n: 'Armagedon', cd: 8, opis: a => 'Co 8 s meteory spadają na ' + f0(5 * MA(a)) + ' losowych wrogów (r 70): <span class="mag">' + f0(120 + 0.7 * D.ap + 0.7 * D.ad) + '</span> (120 + 70% ✨ + 70% ⚔️).',
    tik(a) { if (!cdGotowe(a)) return; const cele = tasuj(wrogowie.filter(w => !w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 360)).slice(0, Math.round(5 * MA(a))); if (!cele.length) return; cdUstaw(a, 8);
      cele.forEach((c, n) => { meteoryt(c.x, c.y, 0.6 + n * 0.1, 70, 120 + 0.7 * D.ap + 0.7 * D.ad, 'Armagedon'); }); } },
  { id: 'olbrzymka', r: 'p', ik: '🦣', n: 'Olbrzym', s: { obszar: 35, ms: -15 }, opis: a => '+' + Math.round(60 * MA(a)) + '% maks. zdrowia, broń wręcz ma +40% zasięgu. Jesteś ogromny.',
    statyMnoz(a, s) { s.hpMax *= 1 + 0.6 * MA(a); }, rozmiar() { return 1.35; }, zasiegWrecz: 0.4 },
  { id: 'hazardAug', r: 'p', ik: '🎰', n: 'Va banque', opis: () => 'Tracisz CAŁE złoto, ale dostajesz 2 losowe przedmioty legendarne (gdy brak miejsca — dodatkowe miejsca). Ulepszenie: znowu.',
    natychmiast() { vaBanque(); }, naUlepszenie() { vaBanque(); } },
  { id: 'gwiezdnyPyl', r: 'p', ik: '✨', n: 'Gwiezdny pył', s: { szczescie: 70 }, opis: () => 'Kolejne augmenty są zawsze co najmniej złote.', lepszeAugmenty: true },
  { id: 'burzaCiosow', r: 'p', ik: '🥊', n: 'Burza ciosów', s: { as: 25 }, opis: () => 'Twoje ataki nakładają efekty <span class="onhit">on-hit</span> <b>dwukrotnie</b>.', podwojnyOnHit: true },
  { id: 'arsenalGlowny', r: 'p', ik: '⚜️', n: 'Mistrzostwo broni', opis: a => 'Broń główna natychmiast zyskuje <b>+1 tier</b> i zadaje <b>+' + Math.round(25 * MA(a)) + '%</b> obrażeń.',
    natychmiast() { gracz.bronie.forEach(b => { if (b.tier < MAKS_TIER_BRONI) b.tier++; }); }, mnGlownejAug: a => 0.25 * MA(a) },
  { id: 'perpetuum', r: 'p', ik: '♾️', n: 'Perpetuum mobile', opis: a => 'Każde zabójstwo skraca odnowienia broni, przedmiotów i umiejętności o <b>' + fmt(0.15 * MA(a)) + ' s</b>.',
    naZabicie(a) { skrocCd(0.15 * MA(a)); } },
  { id: 'nadczlowiek', r: 'p', ik: '🦸', n: 'Nadczłowiek', opis: a => 'Umiejętność postaci odnawia się <b>2× szybciej</b>, a po jej użyciu przez 4 s zadajesz +' + Math.round(30 * MA(a)) + '% obrażeń.',
    cdUmi: () => 0.5, naUmiejetnosci(a) { dodajBuff('nadczl', { obrBonus: 30 * MA(a) }, 4); } },
  { id: 'echoBroni', r: 'p', ik: '🔂', n: 'Echo arsenału', opis: a => 'Efekty broni dodatkowych mają <b>' + Math.round(Math.min(60, 30 * MA(a))) + '%</b> szansy odpalić się drugi raz.', echoOreza: a => Math.min(0.6, 0.3 * MA(a)) },
  { id: 'przelew', r: 'p', ik: '🫗', n: 'Przelew', przelew: a => MA(a),
    opis: a => 'To, co przekracza limity, <b>nie przepada</b>: szansa na kryt ponad 100% → +' + fmt(1.5 * MA(a)) + '% obrażeń krytycznych za 1%; unik ponad limit → +' + fmt(1.5 * MA(a)) + '% obrażeń za 1%; redukcja obrażeń ponad limit → +' + fmt(2 * MA(a)) + '% maks. zdrowia za 1%; wampiryzm ponad 33 → +' + fmt(0.6 * MA(a)) + '% obrażeń za 1; prędkość ataku ponad 300% → +' + fmt(0.15 * MA(a)) + '% obrażeń za 1%.' },
  // ---- nowe: naładowanie i przy trafieniu ----
  { id: 'iskrzenie', r: 's', ik: '⚡', n: 'Iskrzenie', energia: true, energiaTempo: a => 0.3 * MA(a), naladowanyObr: a => 0.25 * MA(a),
    opis: a => 'Energia ładuje się o <b>' + Math.round(30 * MA(a)) + '%</b> szybciej, a ⚡ naładowane ataki zadają <b>+' + Math.round(25 * MA(a)) + '%</b> obrażeń. (Energia: bieganie i ataki; przy 100 następny atak jest naładowany.)' },
  { id: 'jadSkorpiona', r: 's', ik: '🦂', n: 'Jad Skorpiona', opis: a => OH + 'ataki zadają <span class="fiz">' + f0((10 + 0.1 * Math.max(0, D.ad)) * MA(a)) + '</span> (10 + 10% ⚔️) obrażeń fizycznych.',
    statyKonc(a, s) { s.onHitFiz += (10 + 0.1 * Math.max(0, s.ad)) * MA(a); } },
  { id: 'burzowyPed', r: 'z', ik: '🌩️', n: 'Burzowy Pęd', energia: true,
    opis: a => '⚡ <b>Naładowany atak</b> przywołuje 3 pioruny w pobliskich wrogów: <span class="mag">' + f0((40 + 0.4 * D.ad + 0.4 * D.ap) * MA(a)) + '</span> (40 + 40% ⚔️ + 40% ✨) każdy.',
    naNaladowanym(a, b, cel) { const v = (40 + 0.4 * D.ad + 0.4 * D.ap) * MA(a); najblizsi(cel.x, cel.y, 220, 3).forEach((w, n) => opoznione(n * 0.07, () => { if (w.martwy) return; dodajBlyskawice(w.x + losowo(-20, 20), w.y - 140, w.x, w.y, '#ffe066'); zadaj(w, v, 'mag', { zr: 'Burzowy Pęd' }); efektBlysk(w.x, w.y, '#ffe066'); })); DZ.piorun(); } },
  { id: 'pospiech', r: 'z', ik: '⏩', n: 'Pośpiech', opis: a => OH + '(raz na atak) każdy atak, który trafi, skraca pozostałe odnowienie Twoich umiejętności o <b>' + fmt(0.15 * MA(a)) + ' s</b>.',
    naTrafienie(a, w, k) { if (!k.glowny) return; const s = 0.15 * MA(a); [gracz.umi, gracz.umi2].forEach(u => { if (u && u.cd > 0) u.cd = Math.max(0, u.cd - s); }); } },
  { id: 'wiecznaBurza', r: 'p', ik: '♾️', n: 'Wieczna Burza', energia: true, coTrzeciNaladowany: true, naladowanyObr: a => 0.15 * MA(a),
    opis: a => 'Co <b>3.</b> atak jest ⚡ naładowany bez względu na energię (energia nadal ładuje kolejne). Naładowane ataki zadają +' + Math.round(15 * MA(a)) + '% obrażeń.' },
];
const DEF_AUG = {}; AUGMENTY.forEach(a => DEF_AUG[a.id] = a);
function klonujPrzedmiot() { const kand = gracz.przedmioty.filter(p => p && gracz.przedmioty.filter(q => q && q.id === p.id).length < 2); if (!kand.length) { gracz.slotyPrzedm++; return; } const p = losZ(kand); if (czyPryzmat(p)) gracz.slotyPryzm = (gracz.slotyPryzm || 2) + 1; else gracz.slotyPrzedm++; gracz.przedmioty.push({ id: p.id, gw: p.gw || 0, cd: 0 }); toast('🧬 Sklonowano: ' + DEF_PRZ[p.id].n); }
function vaBanque() { gracz.zloto = 0; const pula = PRZEDMIOTY.filter(p => p.t === 3 && !maPrzedmiot(p.id)); for (let n = 0; n < 2 && pula.length; n++) { const d = pula.splice(Math.floor(Math.random() * pula.length), 1)[0]; if (wolneSlotyPrzedm() <= 0) gracz.slotyPrzedm++; gracz.przedmioty.push(nowyPrzedmiot(d.id)); toast('🎰 ' + d.n); } }
function statyAugmentu(a) { const d = DEF_AUG[a.id]; if (!d.s) return null; const s = {}; for (const k in d.s) s[k] = d.s[k] * MA(a); return s; }

// =====================================================================
//  POSTACIE (klasy): broń startowa, statystyki bazowe, pasywka, umiejętności
//  i DRZEWKO EWOLUCJI (3 gałęzie × 3 rangi, kupowane w sklepie, rangi odblokowują poziomy 3/10/20).
// =====================================================================
// rodziny: tylko podpowiedź, z jakimi rodzinami broni postać dobrze się łączy (premia zestawu).
// Szanse w sklepie, skrzyniach, augmentach i kowadłach są takie same dla każdej postaci.
// staty: różnice względem bazy (120 zdrowia, 140 prędkości ruchu).
const EWO_BRONI = ['+20% obrażeń tej broni', '+15% zasięgu, bronie strzelające: +1 pocisk', 'efekty <span class="onhit">on-hit</span> tej broni działają <b>2 razy</b>'];
const KLASY = {
  // ------------------------------------------------------------------ WIĘZIEŃ
  wiezniarka: {
    wyglad: { czapka: 'kajdany', broda: true },
    n: 'Więzień', ik: '⛓️', rola: 'wręcz · rośnie z poziomem', slotyOreza: 4, slotyPrzedm: 4, start: 'lancuch', rodziny: null, hpZaPoziom: 7,
    staty: { hpMax: 10, ms: 5, xpBonus: 25 },
    opis: 'Rośnie z każdym poziomem: <b>+1,5% obrażeń za poziom</b> (bez limitu), +25% doświadczenia, co 5 poziomów darmowy wybór statystyk. Na start +1 przerzut augmentów.',
    dar() { gracz.przerzutyAug += 1; },
    wyborCo: () => ewo('pas') >= 2 ? 4 : 5,
    modZadanych() { return 1 + (ewo('pas') >= 1 ? 0.02 : 0.015) * gracz.poziom; },
    statyMnoz(st, s) { if (ewo('pas') >= 3) s.hpMax *= 1 + 0.01 * gracz.poziom; },
    naZabicie(st) { if (ewo('u2') >= 3 && gracz.buffy.kajdany && (st.przedl || 0) < 4) { gracz.buffy.kajdany.czas += 0.5; st.przedl = (st.przedl || 0) + 0.5; } },
    tik(st, dt) {
      tikWiruKajdan(st, dt);
      if (!gracz.buffy.kajdany) return; st.tKaj = (st.tKaj || 0) - dt; if (st.tKaj > 0) return; st.tKaj = 0.5;
      const r = 150 + (ewo('u2') >= 2 ? 40 : 0);
      aura(r, '#ffd24a', w => { zadaj(w, (25 + 0.6 * D.ad + 0.3 * D.ap) * mnUmi(), 'fiz', { obszar: true, zr: 'Zerwane kajdany' }); if (ewo('u2') >= 2) spowolnij(w, 0.25, 0.6); });
    },
    umi: { n: 'Wir kajdan', ik: '🌀', cd: 14,
      opis: m => '<b>Zatrzymujesz się</b> na ' + fmt(2.5 + (ewo('u1') >= 1 ? 0.5 : 0)) + ' s i <b>nie otrzymujesz obrażeń</b>. Łańcuchy smagają najbliższego wroga (do 170) — tym częściej, im większa prędkość ataku (teraz co ' + fmt(odstepWiru()) + ' s): <span class="fiz">' + f0((15 + 0.45 * D.ad + 0.15 * D.ap) * m) + '</span> (15 + 45% ⚔️ + 15% ✨), mogą trafić krytycznie i <b>nakładają efekty <span class="onhit">on-hit</span></b>. Leczysz się o 15% zadanych (w limicie wampiryzmu).',
      uzyj(m) { const t = 2.5 + (ewo('u1') >= 1 ? 0.5 : 0); gracz.stanKlasy.wir = { t: t, tL: 0, m: m, suma: 0 }; gracz.niewr = Math.max(gracz.niewr, t); gracz.korzen = t;
        if (gracz.zdalny) siecZdarzenieGracza(gracz, ['korzen', Math.round(t * 10)]); fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 120, kolor: '#c8c8d8' }); DZ.ciecie(); return true; } },
    umi2: { n: 'Zerwane kajdany', ik: '⛓️', cd: 16,
      opis: m => 'Przez ' + fmt(6 + (ewo('u2') >= 1 ? 2 : 0)) + ' s: <b>+' + f0(70 * m) + '%</b> prędkości ataku, +' + f0(40 * m) + ' prędkości ruchu, a łańcuchy co 0,5 s smagają wszystkich w promieniu ' + (150 + (ewo('u2') >= 2 ? 40 : 0)) + ': <span class="fiz">' + f0((25 + 0.6 * D.ad + 0.3 * D.ap) * m) + '</span> (25 + 60% ⚔️ + 30% ✨).',
      uzyj(m) { dodajBuff('kajdany', { as: 70 * m, ms: 40 * m }, 6 + (ewo('u2') >= 1 ? 2 : 0)); gracz.stanKlasy.tKaj = 0; gracz.stanKlasy.przedl = 0; fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 150, kolor: '#ffd24a' }); DZ.awans(); return true; } },
    ewo: [
      { id: 'u1', ik: '🌀', n: 'Wir kajdan', r: ['+0,5 s trwania', 'każde smagnięcie przeskakuje na drugiego wroga (50%)', 'na koniec wybuch łańcuchów (r 160): 40 + 150% ⚔️ i +40% prędkości ruchu na 2 s'] },
      { id: 'u2', ik: '⛓️', n: 'Zerwane kajdany', r: ['+2 s trwania', 'promień +40 i spowolnienie 25%', 'każde zabójstwo przedłuża efekt o 0,5 s (do +4 s)'] },
      { id: 'pas', ik: '📈', n: 'Więzienna krzepa', r: ['+2% obrażeń za poziom (zamiast 1,5%)', 'darmowy wybór statystyk co 4 poziomy', 'każdy poziom: +1% maks. zdrowia'] },
    ],
    kolory: { plaszcz: ['#b3263a', '#6e1424'], tunika: ['#41b097', '#21645a'], wlosy: '#5a3420' },
  },
  // ------------------------------------------------------------------ RYCERZ
  rycerz: {
    wyglad: { czapka: 'helm' },
    n: 'Rycerz', ik: '🛡️', rola: 'wręcz · tank, pancerz to siła', slotyOreza: 4, slotyPrzedm: 4, start: 'mieczTarcza', rodziny: ['biala'], hpZaPoziom: 8,
    staty: { hpMax: 60, pancerz: 30, ms: -5 },
    opis: 'Pancerz to siła: <b>+1% obrażeń za każde 3 pancerza</b> (bez limitu) i <b>pancerz ×1,25</b>. Otrzymuje 15% mniej obrażeń, tarcze +30%.',
    statyMnoz(st, s) { s.pancerz *= ewo('pas') >= 1 ? 1.35 : 1.25; }, statyPost(st, s) { s.obrBonus += Math.max(0, s.pancerz) / (ewo('pas') >= 2 ? 2.5 : 3); },
    modOtrzymanych(st) { return (ewo('pas') >= 3 ? 0.75 : 0.85) * (st.wyzwanie > czasGry ? 0.6 : 1); }, mnTarcz: 0.3,
    naOtrzymanie(st, v, typ, o) { if (!(st.wyzwanie > czasGry) || !o.wrog || o.dot) return; zadaj(o.wrog, (o.przed || v) * (ewo('u2') >= 2 ? 1 : 0.5), 'praw', { zr: 'Wyzwanie', odbicie: true });
      if (ewo('u2') >= 3) leczGracza(D.hpMax * 0.03, 'Wyzwanie'); },
    umi: { n: 'Szarża', ik: '🐎', cd: () => ewo('u1') >= 2 ? 6 : 8,
      opis: m => 'Szarżuje ' + (200 + (ewo('u1') >= 1 ? 80 : 0)) + ' px w kierunku ruchu: wrogowie na drodze dostają <span class="fiz">' + f0((60 + 1.5 * D.ad + 1.0 * D.pancerz) * m) + '</span> (60 + 150% ⚔️ + 100% 🛡️) i są ogłuszeni na 1,2 s. Dostajesz tarczę ' + f0((40 + 0.8 * D.pancerz) * m) + ' (40 + 80% 🛡️).',
      uzyj(m) { szarza(200 + (ewo('u1') >= 1 ? 80 : 0), (60 + 1.5 * D.ad + 1.0 * D.pancerz) * m, 1.2, 'Szarża'); dajTarcze((40 + 0.8 * D.pancerz) * m, 3);
        if (ewo('u1') >= 3) { const ja = gracz; opoznione(0.25, () => { if (gracz !== ja || stan !== 'walka') return; fale.push({ x: gracz.x, y: gracz.y, czas: 0.4, max: 0.4, r: 120, kolor: '#e8e8f0' });
          aura(120, '#e8e8f0', w => { zadaj(w, (30 + 1.0 * D.pancerz) * m, 'fiz', { obszar: true, zr: 'Szarża' }); oglusz(w, 0.8, { zrodlo: 'Szarża' }); }, true); }); }
        return true; } },
    umi2: { n: 'Wyzwanie', ik: '📯', cd: 16,
      opis: m => 'Wyzywasz wrogów w promieniu 260 — przez ' + fmt(3 + (ewo('u2') >= 1 ? 1 : 0)) + ' s atakują tylko Ciebie. Otrzymujesz <b>40% mniej obrażeń</b>, a każdy cios w Ciebie odbija <span class="praw">' + (ewo('u2') >= 2 ? 100 : 50) + '%</span> obrażeń (przed obroną) jako prawdziwe.',
      uzyj(m) { const t = 3 + (ewo('u2') >= 1 ? 1 : 0); gracz.stanKlasy.wyzwanie = czasGry + t; wrogowie.forEach(w => { if (!w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 260) { w.cel = gracz; w.tCelu = t; } });
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#ffe08a', odwrot: true }); DZ.boss(); return true; } },
    ewo: [
      { id: 'u1', ik: '🐎', n: 'Szarża', r: ['+80 długości', 'odnowienie 6 s (zamiast 8)', 'na końcu fala uderzeniowa (r 120): 30 + 100% 🛡️ i ogłuszenie 0,8 s'] },
      { id: 'u2', ik: '📯', n: 'Wyzwanie', r: ['+1 s trwania', 'odbija 100% obrażeń', 'każdy cios w Ciebie podczas Wyzwania leczy 3% maks. zdrowia'] },
      { id: 'pas', ik: '🛡️', n: 'Bastion', r: ['pancerz ×1,35', '+1% obrażeń za każde 2,5 pancerza', 'otrzymujesz 25% mniej obrażeń (zamiast 15%)'] },
    ],
    kolory: { plaszcz: ['#3a4a8a', '#1a2450'], tunika: ['#c8ccd8', '#7a7e8c'], wlosy: '#c8a060' },
  },
  // ------------------------------------------------------------------ LEPRIKON
  szczesciara: {
    wyglad: { czapka: 'melonik' },
    n: 'Leprikon', ik: '🍀', rola: 'dystans · szczęście i kryty', slotyOreza: 4, slotyPrzedm: 4, start: 'pistolet', rodziny: null,
    staty: { hpMax: -10, ms: 10, kryt: 15, krytObr: 15, unik: 8 },
    opis: 'Fart w walce: +15% kryta, +8% uniku. <b>Po każdym uniku następny atak jest pewnym krytem.</b> Każde 5 🍀 daje +1% kryta, a każdy kryt ma 6% szans upuścić <b>monetę</b>.',
    statyPost(st, s) { s.kryt += Math.max(0, s.szczescie) / 5; if (ewo('pas') >= 1) { s.kryt += 5; s.krytObr += 10; } },
    statyDyn(st, s) { if (st.zryw > czasGry) s.as += 20; },
    modZadanych(st) { return ewo('pas') >= 3 ? 1 + Math.max(0, D.szczescie) / 1000 : 1; },
    naUniku(st) { st.pewnyKryt = true; if (ewo('pas') >= 2) { st.zryw = czasGry + 2; oznaczStaty(); } },
    naKryt(st, w) { if (Math.random() < 0.06) rozsypMonety(w.x, w.y, 1 + fala.nr * 0.1, true); if (gracz.buffy.fart) { st.fartObr = (st.fartObr || 0); if (ewo('u1') >= 2) leczWampirem(D.hpMax * 0.01, 'Fart'); } },
    naObrazenia(st, w, v) { if (gracz.buffy.fart) st.fartObr = (st.fartObr || 0) + v; },
    umi: { n: 'Fart', ik: '🌈', cd: 15,
      opis: m => 'Przez ' + fmt((5 + (ewo('u1') >= 1 ? 1 : 0)) * Math.min(1.5, m)) + ' s <b>każdy atak jest krytyczny</b>, krytyki zadają +50% więcej i masz +40% uniku.',
      uzyj(m) { const t = (5 + (ewo('u1') >= 1 ? 1 : 0)) * Math.min(1.5, m); dodajBuff('fart', { kryt: 300, krytObr: 50, unik: 40 }, t); gracz.stanKlasy.fartObr = 0; DZ.pryzmat();
        if (ewo('u1') >= 3) { const ja = gracz; opoznione(t, () => { if (gracz !== ja || stan !== 'walka') return; const v = (gracz.stanKlasy.fartObr || 0) * 0.1; if (v < 1) return;
          aura(200, '#ffd24a', w => zadaj(w, v / Math.max(1, policzWrogow(gracz.x, gracz.y, 200)), 'praw', { obszar: true, zr: 'Garniec złota' }), true); DZ.moneta(); }); }
        return true; } },
    umi2: { n: 'Tęcza', ik: '🌈', cd: () => ewo('u2') >= 3 ? 8 : 12,
      opis: m => 'Przemykasz po tęczy ' + (180 + (ewo('u2') >= 1 ? 60 : 0)) + ' px w kierunku ruchu: wrogowie na drodze dostają <span class="fiz">' + f0((40 + 1.0 * D.ad + 0.2 * D.szczescie) * m) + '</span> (40 + 100% ⚔️ + 20% 🍀), a zabici upuszczają monety.' + (ewo('u2') >= 2 ? ' Trafieni są spowolnieni o 40%, a Ty masz +30% prędkości ruchu na 3 s.' : ''),
      uzyj(m) { const dl = 180 + (ewo('u2') >= 1 ? 60 : 0), v = (40 + 1.0 * D.ad + 0.2 * D.szczescie) * m;
        let mx = gracz.kierRX || gracz.kierX || 1, my = gracz.kierRY || 0; if (gracz.zdalny && gracz.umiKier) { mx = gracz.umiKier[0] || mx; my = gracz.umiKier[1] || my; }
        liniowe(Math.atan2(my, mx), dl, 30, w => { zadaj(w, v, 'fiz', { zr: 'Tęcza' }); if (w.martwy) rozsypMonety(w.x, w.y, 2, true); if (ewo('u2') >= 2) spowolnij(w, 0.4, 2); });
        if (ewo('u2') >= 2) dodajBuff('tecza', { ms: 0.3 * D.ms }, 3);
        for (let n = 0; n < 7; n++) czastki.push({ x: gracz.x + mx * n * dl / 7, y: gracz.y + my * n * dl / 7, vx: 0, vy: -20, czas: 0.6, max: 0.6, kolor: ['#ff5a5a', '#ffb04a', '#ffe066', '#7ee87a', '#5aa8e6', '#9a6ae0', '#ff7ae0'][n] });
        mrugnij(dl); DZ.czar(); return true; } },
    ewo: [
      { id: 'u1', ik: '🌈', n: 'Fart', r: ['+1 s trwania', 'podczas Fartu każdy kryt leczy 1% maks. zdrowia', 'na koniec Garniec złota: 10% obrażeń zadanych w czasie Fartu wybucha wokół (prawdziwe)'] },
      { id: 'u2', ik: '🌈', n: 'Tęcza', r: ['+60 długości', 'spowalnia trafionych o 40%, +30% prędkości ruchu na 3 s', 'odnowienie 8 s (zamiast 12)'] },
      { id: 'pas', ik: '🍀', n: 'Fart w genach', r: ['+5% kryta i +10% obrażeń krytycznych', 'unik daje +20% prędkości ataku na 2 s', 'każde 10 🍀 = +1% wszystkich obrażeń'] },
    ],
    kolory: { plaszcz: ['#2e8a3a', '#14501e'], tunika: ['#e6c15c', '#a07a1e'], wlosy: '#c8742a' },
  },
  // ------------------------------------------------------------------ AKIMBO
  wieloreka: {
    wyglad: { czapka: 'opaska' },
    n: 'Akimbo', ik: '👐', rola: 'dwie bronie główne · prędkość ataku', slotyOreza: 2, slotyPrzedm: 4, start: 'wybor2', rodziny: null, hpZaPoziom: 6,
    staty: { hpMax: -5, ms: 5, as: 10 },
    opis: '<b>Dwie bronie główne</b> naraz (wybierasz obie, każda ×0,75 obrażeń), 2 miejsca na broń dodatkową, <b>bez umiejętności</b>. <b>Krzyżowy ogień:</b> gdy wroga trafi jedna broń, a zaraz potem druga (do 2 s), druga zadaje +30% i dostajesz ładunek +4% prędkości ataku do końca fali (maks. 25). Zabójstwo jedną bronią „podaje” krzyżowe trafienie drugiej.',
    mnBroni: () => 0.75,
    naStartFali(st) { st.stosy = 0; st.podanie = null; },
    statyDyn(st, s) { s.as += 4 * (st.stosy || 0); },
    naTrafienie(st, w, k) {
      if (!k.glowny || gracz.bronie.length < 2 || w.martwy && !k.zadane) return;
      const i = gracz.bronie.indexOf(k.bron); if (i < 0) return;
      const p = w._akimbo, pd = st.podanie;
      const krzyz = (p && p.g === gracz.id && p.i !== i && czasGry - p.t < 2) || (pd && pd.i !== i && czasGry - pd.t < 1.5);
      w._akimbo = { i: i, t: czasGry, g: gracz.id };
      if (!krzyz) return;
      st.podanie = null;
      if (!w.martwy) zadaj(w, k.zadaneSurowe * (ewo('pas') >= 2 ? 0.6 : 0.3), BRONIE[k.bron.rodzaj].obrTyp, { zr: 'Krzyżowy ogień' });
      if (ewo('pas') >= 3) obszarowe(w.x, w.y, 60, '#ffb04a', o => { if (o !== w) zadaj(o, k.zadaneSurowe * 0.4, 'fiz', { obszar: true, zr: 'Krzyżowy ogień' }); }, true);
      const maks = ewo('pas') >= 1 ? 35 : 25; if ((st.stosy || 0) < maks) { st.stosy = (st.stosy || 0) + 1; oznaczStaty(); }
      efektBlysk(w.x, w.y, '#ffb04a');
    },
    naZabicie(st, w, o) { if (o && o.bron) { const i = gracz.bronie.indexOf(o.bron); if (i >= 0) st.podanie = { i: i, t: czasGry }; } },
    ewo: [
      { id: 'b1', ik: '🤛', n: 'Lewa ręka (1. broń)', bron: 0, r: EWO_BRONI },
      { id: 'b2', ik: '🤜', n: 'Prawa ręka (2. broń)', bron: 1, r: EWO_BRONI },
      { id: 'pas', ik: '✖️', n: 'Krzyżowy ogień', r: ['maks. 35 ładunków', 'krzyżowe trafienie +60% (zamiast 30%)', 'krzyżowe trafienie wybucha wokół celu (r 60, 40%)'] },
    ],
    kolory: { plaszcz: ['#4a5ac4', '#24306e'], tunika: ['#9a6ae0', '#5a3a8a'], wlosy: '#2a2030' },
  },
  // ------------------------------------------------------------------ ONE-HANDED
  jedynaczka: {
    wyglad: { czapka: 'opaska' },
    n: 'One-handed', ik: '🗡️', rola: 'jedna broń · bez umiejętności', slotyOreza: 0, slotyPrzedm: 5, slotyPryzm: 3, start: 'wybor', rodziny: null, hpZaPoziom: 6,
    staty: { hpMax: 5, ms: 5, as: 20 },
    opis: 'Jedna broń na całe życie: zadaje <b>2× obrażeń</b>, zaczyna na II tierze (do wyboru), ulepszanie −50%, a po V tierze rośnie dalej — <b>Mistrzostwo I–V</b> (każde: +15% obrażeń i wybór jednej z 3 cech broni). <b>Nie nosi broni dodatkowych</b> i nie ma umiejętności. <b>3 miejsca na pryzmaty</b> — każdy pryzmat <b>nasyca broń</b>: +15% jej obrażeń.',
    mnBroni: () => 2 * (1 + (ewo('pryzm') >= 2 ? 0.3 : 0.15) * liczPrzedm(true)), rabatBroni: 0.5, mistrzostwo: true,
    kowadloWybor: () => ewo('pryzm') >= 1 ? 4 : 3,
    statyFlat(st, s) { if (ewo('tech') >= 1) { s.as += 10; s.kryt += 5; } if (ewo('tech') >= 2) { s.krytObr += 15; s.obrBonus += 5; }
      const b = gracz.bronie[0]; if (b && b.perki) b.perki.forEach(p => { const P = PERKI_MISTRZA[p]; if (P && P.s) dodajStaty(s, P.s); }); },
    naAtak(st, b, cel, o) { if (ewo('tech') < 3 || (o && o.echo)) return; st.licz = (st.licz || 0) + 1; if (st.licz % 5 === 0) opoznione(0.12, () => echoAtaku(b, cel)); },
    ewo: [
      { id: 'ostrze', ik: '🗡️', n: 'Ostrze', bron: 0, r: EWO_BRONI },
      { id: 'pryzm', ik: '🔨', n: 'Nasycenie pryzmatami', r: ['Pryzmatyczne Kowadło: wybór z 4 zamiast 3', 'każdy pryzmat +30% obrażeń broni (zamiast 15%)', '+1 miejsce na pryzmat (4)'], naZakup: r => { if (r === 3) gracz.slotyPryzm++; } },
      { id: 'tech', ik: '🥋', n: 'Technika', r: ['+10% prędkości ataku i +5% kryta', '+15% obrażeń krytycznych i +5% obrażeń', 'co 5. atak powtarza się (echo)'] },
    ],
    kolory: { plaszcz: ['#2a2a2a', '#0e0e0e'], tunika: ['#c0c0d0', '#6a6a7a'], wlosy: '#e8e0d0' },
  },
  // ------------------------------------------------------------------ MAG
  czarodziejka: {
    wyglad: { czapka: 'kapeluszMaga', kol: '#4a2a9a', broda: '#e8e0ff' },
    n: 'Mag', ik: '🧙', rola: 'dystans · umiejętności', slotyOreza: 4, slotyPrzedm: 4, start: 'rozdzka', rodziny: ['magiczna'], hpZaPoziom: 4,
    staty: { hpMax: -25, ap: 25, haste: 25 },
    opis: 'Gra się <b>umiejętnościami</b>: obie o 25% mocniejsze, <b>moc umiejętności ×1,4</b> i +25 przyspieszenia. Różdżka jest słaba (obrażenia broni ×0,6).',
    statyMnoz(st, s) { s.ap *= ewo('pas') >= 2 ? 1.5 : 1.4; }, mnBroni: () => ewo('pas') >= 1 ? 0.75 : 0.6, mnUmi: 0.25,
    naUmiejetnosci(st) { if (ewo('pas') >= 3) st.czaroostrze = 3; },
    modZadanych(st, w, typ, o) { if (o && o.atak && st.czaroostrze > 0) { st.czaroostrze--; return 1.5; } return 1; },
    umi2: { n: 'Mrugnięcie', ik: '💫', cd: () => ewo('u2') >= 2 ? 4.5 : 7,
      opis: m => 'Teleport o ' + (170 + (ewo('u2') >= 1 ? 60 : 0)) + ' w kierunku ruchu. W miejscu startu wybucha lodowa nowa (r 130): <span class="mag">' + f0((50 + 0.8 * D.ap) * m) + '</span> (50 + 80% ✨) i zamrożenie wrogów na 1,2 s.' + (ewo('u2') >= 3 ? ' Zamrożeni dostają +30% obrażeń przez 3 s.' : ''),
      uzyj(m) { const x0 = gracz.x, y0 = gracz.y, r = 130 * mnObszaru(); fale.push({ x: x0, y: y0, czas: 0.45, max: 0.45, r: r, kolor: '#9fd8ff' });
        wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - x0, w.y - y0) > r + w.r * 0.5) return; zadaj(w, (50 + 0.8 * D.ap) * m, 'mag', { obszar: true, zr: 'Mrugnięcie' }); oglusz(w, 1.2, { zrodlo: 'Mrugnięcie' });
          if (ewo('u2') >= 3) { w.naznaczony = Math.max(w.naznaczony || 0, 3); w.mnNazn = Math.max(w.mnNazn || 0, 0.3); } });
        for (let n = 0; n < 10; n++) czastki.push({ x: x0 + losowo(-20, 20), y: y0 + losowo(-20, 20), vx: losowo(-60, 60), vy: losowo(-60, 60), czas: 0.5, max: 0.5, kolor: '#cfefff' });
        mrugnij(170 + (ewo('u2') >= 1 ? 60 : 0)); DZ.czar(); return true; } },
    umi: { n: 'Meteor', ik: '☄️', cd: 10,
      opis: m => 'Wielki meteor spada na największe skupisko wrogów (r 130): <span class="mag">' + f0((150 + 1.6 * D.ap) * m) + '</span> (150 + 160% ✨), a za nim ' + (3 + (ewo('u1') >= 1 ? 2 : 0)) + ' mniejsze po ' + f0((50 + 0.5 * D.ap) * m) + ' (50 + 50% ✨).' + (ewo('u1') >= 2 ? ' Zostawia płonącą ziemię (3 s).' : '') + (ewo('u1') >= 3 ? ' Co 3. meteor jest olbrzymi (r 200, ×2).' : ''),
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 360, 130) || najblizszyWrog(gracz.x, gracz.y, 360); if (!c) return false; const st = gracz.stanKlasy;
        st.meteory = (st.meteory || 0) + 1; const olb = ewo('u1') >= 3 && st.meteory % 3 === 0;
        meteoryt(c.x, c.y, 0.7, olb ? 200 : 130, (150 + 1.6 * D.ap) * m * (olb ? 2 : 1), 'Meteor');
        if (ewo('u1') >= 2) { const ja = gracz; opoznione(0.7, () => { if (gracz !== ja) return; polaEfektow.push({ wl: gracz, x: c.x, y: c.y, r: 110 * mnObszaru(), czas: 3, max: 3, tyk: 0.5, rodzaj: 'ogien', obr: (0.3 * D.ap) * m / 2, zr: 'Meteor' }); }); }
        for (let n = 0; n < 3 + (ewo('u1') >= 1 ? 2 : 0); n++) meteoryt(c.x + losowo(-110, 110), c.y + losowo(-110, 110), 1 + n * 0.2, 70, (50 + 0.5 * D.ap) * m, 'Meteor'); return true; } },
    ewo: [
      { id: 'u1', ik: '☄️', n: 'Meteor', r: ['+2 małe meteory', 'zostawia płonącą ziemię na 3 s (30% ✨/s)', 'co 3. meteor jest olbrzymi (r 200, ×2 obrażeń)'] },
      { id: 'u2', ik: '💫', n: 'Mrugnięcie', r: ['+60 odległości', 'odnowienie 4,5 s (zamiast 7)', 'zamrożeni dostają +30% obrażeń przez 3 s'] },
      { id: 'pas', ik: '📜', n: 'Arkana', r: ['broń ×0,75 (zamiast ×0,6)', 'moc umiejętności ×1,5', 'po umiejętności 3 następne ataki bronią: +50% obrażeń'] },
    ],
    kolory: { plaszcz: ['#6a3ac4', '#341a6e'], tunika: ['#3a7ae0', '#1a3a8a'], wlosy: '#e8e0ff' },
  },
  // ------------------------------------------------------------------ BERSERKER
  berserkerka: {
    wyglad: { czapka: 'rogi', broda: true },
    n: 'Berserker', ik: '🪓', rola: 'wręcz · im mniej zdrowia, tym groźniej', slotyOreza: 4, slotyPrzedm: 4, start: 'topor', rodziny: ['biala'], hpZaPoziom: 7,
    staty: { hpMax: 35, ms: 10, as: 15 },
    opis: 'Im mniej zdrowia, tym groźniejszy: <b>+1% prędkości ataku i +0,6% obrażeń za każdy 1% brakującego zdrowia</b>. <b>Rozpęd:</b> każde zabójstwo daje ładunek (+2% prędkości ataku, +3 prędkości ruchu, 4 s, maks. 10); przy pełnych ładunkach ciosy tną wszystkich wokół (40%). Regeneracja o połowę słabsza.',
    mnRegen: () => 0.5,
    statyDyn(st, s) { const b = Math.max(0, 1 - gracz.hp / Math.max(1, s.hpMax)) * 100; s.as += b; s.obrBonus += b * 0.6;
      if (czasGry > (st.tRozp || 0)) st.rozped = 0; const r = st.rozped || 0; s.as += 2 * r; s.ms += 3 * r; if (st.szalDo > czasGry) { s.as += 60; s.omni += 8; } },
    modOtrzymanych(st) { return ewo('pas') >= 2 && gracz.hp < D.hpMax * 0.3 ? 0.8 : 1; },
    limitWampF: st => st.szalDo > czasGry && ewo('u1') >= 2 ? 0.04 : 0,
    naZabicie(st, w, o) { const maks = ewo('pas') >= 1 ? 15 : 10; st.rozped = Math.min(maks, (st.rozped || 0) + 1); st.tRozp = czasGry + 4; oznaczStaty();
      if (o && o.zr === 'Skok Rzeźnika' && ewo('u2') >= 3) gracz.umi2.cd = 0; },
    naTrafienie(st, w, k) { const prog = ewo('pas') >= 3 ? 6 : (ewo('pas') >= 1 ? 15 : 10); if (!k.glowny || (st.rozped || 0) < prog || czasGry - (st.tCiecia || -9) < 0.5) return; st.tCiecia = czasGry;
      aura(95, '#c0392b', o => { if (o !== w) zadaj(o, k.zadaneSurowe * 0.4, 'fiz', { obszar: true, zr: 'Rozpęd' }); }, false); },
    naOtrzymanie(st, v) { if (st.szalDo > czasGry) st.przyjeteSzal = (st.przyjeteSzal || 0) + v; },
    naSmierc(st) { if (st.szalDo > czasGry) { gracz.hp = 1; return true; } return false; },
    umi: { n: 'Szał', ik: '😡', cd: 16,
      opis: m => 'Przez ' + fmt(6 + (ewo('u1') >= 1 ? 1.5 : 0)) + ' s <b>nie możesz zginąć</b> (zdrowie nie spadnie poniżej 1), +60% prędkości ataku, +8% wampiryzmu, +30 prędkości ruchu.' + (ewo('u1') >= 3 ? ' Na koniec wybuchasz za 30% obrażeń przyjętych w Szale (r 180).' : ''),
      uzyj(m) { const st = gracz.stanKlasy, t = 6 + (ewo('u1') >= 1 ? 1.5 : 0); st.szalDo = czasGry + t; st.przyjeteSzal = 0; dodajBuff('szal', { ms: 30 }, t); rozbryzg(gracz.x, gracz.y, '#c0392b', 16); DZ.boss(); oznaczStaty();
        if (ewo('u1') >= 3) { const ja = gracz; opoznione(t, () => { if (gracz !== ja || stan !== 'walka') return; const v = (st.przyjeteSzal || 0) * 0.3; if (v < 1) return; fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 180, kolor: '#c0392b' });
          aura(180, '#c0392b', w => zadaj(w, v, 'fiz', { obszar: true, zr: 'Szał' }), true); DZ.wybuch(); }); }
        return true; } },
    umi2: { n: 'Skok Rzeźnika', ik: '🦘', cd: () => ewo('u2') >= 1 ? 8 : 10,
      opis: m => 'Skaczesz na skupisko wrogów (do 240) i uderzasz o ziemię (r 120): <span class="fiz">' + f0((40 + 1.2 * D.ad + 0.04 * D.hpMax) * m) + '</span> (40 + 120% ⚔️ + 4% maks. zdrowia), ogłuszenie 0,5 s.' + (ewo('u2') >= 2 ? ' Trafieni krwawią 3 s.' : '') + (ewo('u2') >= 3 ? ' Zabójstwo skokiem odnawia go.' : ''),
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 240, 120) || najblizszyWrog(gracz.x, gracz.y, 240); if (!c) return false; skokDo(c.x, c.y, 240);
        const ja = gracz; opoznione(0.2, () => { if (gracz !== ja || stan !== 'walka') return; const v = (40 + 1.2 * D.ad + 0.04 * D.hpMax) * m; fale.push({ x: gracz.x, y: gracz.y, czas: 0.4, max: 0.4, r: 120, kolor: '#c0392b' }); rozbryzg(gracz.x, gracz.y, '#8a5a3a', 14);
          aura(120, '#c0392b', w => { zadaj(w, v, 'fiz', { obszar: true, zr: 'Skok Rzeźnika' }); oglusz(w, 0.5, { zrodlo: 'Skok Rzeźnika' }); if (ewo('u2') >= 2) krwawienie(w, v * 0.3, 3, true); }, true); DZ.wybuch(); });
        return true; } },
    ewo: [
      { id: 'u1', ik: '😡', n: 'Szał', r: ['+1,5 s trwania', 'limit wampiryzmu +4%/s w czasie Szału', 'na koniec wybuch: 30% przyjętych obrażeń (r 180)'] },
      { id: 'u2', ik: '🦘', n: 'Skok Rzeźnika', r: ['odnowienie 8 s', 'trafieni krwawią (30%/s przez 3 s)', 'zabójstwo skokiem odnawia go'] },
      { id: 'pas', ik: '🩸', n: 'Rozpęd', r: ['maks. 15 ładunków', 'poniżej 30% zdrowia: −20% otrzymywanych obrażeń', 'cięcie wokół już od 6 ładunków'] },
    ],
    kolory: { plaszcz: ['#8a2a1a', '#4a1008'], tunika: ['#7a5a3a', '#4a3020'], wlosy: '#d04020' },
  },
  // ------------------------------------------------------------------ WAMPIR
  wampirzyca: {
    wyglad: { czapka: 'wampir' },
    n: 'Wampir', ik: '🧛', rola: 'wręcz/magia · prawdziwy wampiryzm', slotyOreza: 4, slotyPrzedm: 4, start: 'kosa', rodziny: ['biala', 'magiczna'], hpZaPoziom: 6,
    staty: { hpMax: -5, ms: 10, omni: 6, leczenie: 25 },
    opis: '<b>Prawdziwy wampiryzm</b>: limit wampiryzmu wyższy o 4% zdrowia/s, +6% wampiryzmu, leczenie +25%, zabójstwo leczy 0,5% maks. zdrowia. Nie regeneruje się sam. <b>Pula krwi:</b> nadmiar leczenia zbiera się (do 40% maks. zdrowia) i wzmacnia Ucztę krwi.',
    mnRegen: () => 0,
    naZabicie() { leczWampirem(D.hpMax * (ewo('pas') >= 1 ? 0.01 : 0.005), 'Wampir'); },
    limitWampF: () => 0.04 + (ewo('pas') >= 3 ? 0.02 : 0),
    naNadleczenie(st, v) { st.pula = Math.min(D.hpMax * (ewo('pas') >= 2 ? 0.6 : 0.4), (st.pula || 0) + v); },
    naObrazenia(st, w, v) { if (w.krwawyZnak > czasGry && v > 0) leczWampirem(v * 0.04, 'Znak krwi'); },
    naTrafienie(st, w, k) { if (!k.glowny || !(st.ukaszenia > 0)) return; st.ukaszenia--; leczGracza(D.hpMax * 0.05, 'Ukąszenie'); },
    tik(st, dt) {
      if (!(gracz.forma === 'nietoperz')) return;
      wrogowie.forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - gracz.x, w.y - gracz.y) > 34 + w.r) return; const kl = '_mgla' + gracz.id; if (w[kl] && czasGry - w[kl] < 0.5) return; w[kl] = czasGry;
        const v = zadaj(w, (30 + 0.5 * D.ap) * (st.mMgly || 1), 'mag', { zr: 'Mgła nietoperzy' }); leczWampirem(v * 0.3, 'Mgła nietoperzy'); if (ewo('u2') >= 2) spowolnij(w, 0.4, 1.5); });
    },
    umi: { n: 'Uczta krwi', ik: '🩸', cd: () => ewo('u1') >= 3 ? 8 : 12,
      opis: m => 'Wysysa krew z wrogów w promieniu ' + (190 + (ewo('u1') >= 1 ? 50 : 0)) + ': <span class="mag">' + f0((60 + 0.08 * D.hpMax + 0.7 * D.ap) * m) + '</span> (60 + 8% maks. zdrowia + 70% ✨) każdemu, plus <b>cała Pula krwi</b> (' + f0(gracz.stanKlasy.pula || 0) + ') rozdzielona między nich. Leczysz się o 50% zadanych (maks. 30% zdrowia).' + (ewo('u1') >= 2 ? ' Naznacza: przez 5 s Twoje obrażenia im leczą Cię o 4%.' : ''),
      uzyj(m) { const r = 190 + (ewo('u1') >= 1 ? 50 : 0), n = policzWrogow(gracz.x, gracz.y, r); if (!n) return false; const st = gracz.stanKlasy, dod = (st.pula || 0) / n; st.pula = 0; let suma = 0;
        aura(r, '#c0392b', w => { suma += zadaj(w, (60 + 0.08 * D.hpMax + 0.7 * D.ap) * m + dod, 'mag', { obszar: true, zr: 'Uczta krwi' }); dodajBlyskawice(w.x, w.y, gracz.x, gracz.y, '#e04050'); if (ewo('u1') >= 2) w.krwawyZnak = czasGry + 5; }, true);
        leczGracza(Math.min(suma * 0.5, D.hpMax * 0.3), 'Uczta krwi'); return true; } },
    umi2: { n: 'Mgła nietoperzy', ik: '🦇', cd: 14,
      opis: m => 'Zamieniasz się w rój nietoperzy na ' + fmt(2 + (ewo('u2') >= 1 ? 1 : 0)) + ' s: <b>niewrażliwość</b>, +60% prędkości ruchu, a każdy wróg, przez którego przelatujesz, dostaje <span class="mag">' + f0((30 + 0.5 * D.ap) * m) + '</span> (30 + 50% ✨) co 0,5 s i leczy Cię o 30%.' + (ewo('u2') >= 3 ? ' Potem 3 ataki leczą po 5% maks. zdrowia.' : ''),
      uzyj(m) { const t = 2 + (ewo('u2') >= 1 ? 1 : 0), st = gracz.stanKlasy; st.mMgly = m; gracz.forma = 'nietoperz'; gracz.formaDo = czasGry + t; gracz.niewr = Math.max(gracz.niewr, t); dodajBuff('mgla', { ms: 0.6 * D.ms }, t);
        if (ewo('u2') >= 3) { const ja = gracz; opoznione(t, () => { if (gracz === ja) st.ukaszenia = 3; }); } rozbryzg(gracz.x, gracz.y, '#3a0a1a', 14); DZ.czar(); return true; } },
    ewo: [
      { id: 'u1', ik: '🩸', n: 'Uczta krwi', r: ['promień +50', 'naznacza: przez 5 s Twoje obrażenia im leczą Cię o 4%', 'odnowienie 8 s (zamiast 12)'] },
      { id: 'u2', ik: '🦇', n: 'Mgła nietoperzy', r: ['+1 s trwania', 'spowalnia przelatywanych o 40%', 'potem 3 ataki leczą po 5% maks. zdrowia'] },
      { id: 'pas', ik: '🧛', n: 'Pradawna krew', r: ['zabójstwo leczy 1% maks. zdrowia', 'Pula krwi do 60% maks. zdrowia', 'limit wampiryzmu jeszcze +2%/s'] },
    ],
    kolory: { plaszcz: ['#3a0a1a', '#1a0008'], tunika: ['#6a0a2a', '#3a0418'], wlosy: '#101010' },
  },
  // ------------------------------------------------------------------ SIGMA
  kolos: {
    wyglad: { lysy: true, broda: true },
    n: 'Sigma', ik: '🗿', rola: 'wręcz · ogromne zdrowie', slotyOreza: 4, slotyPrzedm: 5, start: 'kastety', rodziny: ['biala'], hpZaPoziom: 10,
    staty: { hpMax: 80, pancerz: 25, odpMag: 15, ms: -15, as: -10, wytrwalosc: 30 },
    opis: 'Nie przejmuje się niczym: <b>maks. zdrowie ×1,3</b>, ataki zadają <span class="onhit">on-hit</span> <span class="fiz">3% maks. zdrowia</span>, <b>nie da się go spowolnić</b>, +30% nieustępliwości. Wolniejszy, większy. +1 miejsce na przedmiot.',
    odpornyNaSpow: true,
    statyMnoz(st, s) { s.hpMax *= ewo('pas') >= 1 ? 1.4 : 1.3; }, statyPost(st, s) { s.onHitFiz += s.hpMax * (ewo('pas') >= 2 ? 0.04 : 0.03); if (ewo('pas') >= 3) s.redukcja += Math.min(25, s.hpMax / 100); }, rozmiar() { return 1.2; },
    umi: { n: 'Kamienna skóra', ik: '🪨', cd: 18,
      opis: m => '<b>' + fmt((3.5 + (ewo('u1') >= 1 ? 1 : 0)) * Math.min(1.6, m)) + ' s niewrażliwości</b>, wrogowie w promieniu 260 rzucają się na Ciebie' + (ewo('u1') >= 2 ? ' i dostają +20% obrażeń' : '') + '. Na koniec fala uderzeniowa (r ' + (ewo('u1') >= 3 ? 300 : 200) + '): <span class="fiz">' + f0((ewo('u1') >= 3 ? 0.2 : 0.12) * D.hpMax * m) + '</span> (' + (ewo('u1') >= 3 ? 20 : 12) + '% maks. zdrowia).',
      uzyj(m) { const t = (3.5 + (ewo('u1') >= 1 ? 1 : 0)) * Math.min(1.6, m); gracz.niewr = Math.max(gracz.niewr, t);
        wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 260) { w.cel = gracz; w.tCelu = t; if (ewo('u1') >= 2) { w.naznaczony = Math.max(w.naznaczony || 0, t); w.mnNazn = Math.max(w.mnNazn || 0, 0.2); } } });
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#c0b8a0', odwrot: true }); DZ.tarcza();
        const ja = gracz, r = ewo('u1') >= 3 ? 300 : 200, p = ewo('u1') >= 3 ? 0.2 : 0.12;
        opoznione(t, () => { if (gracz !== ja || stan !== 'walka') return; aura(r, '#c0b8a0', w => { zadaj(w, p * D.hpMax * m, 'fiz', { obszar: true, zr: 'Kamienna skóra' }); oglusz(w, 0.8, { zrodlo: 'Kamienna skóra' }); }, true); DZ.wybuch(); }); return true; } },
    umi2: { n: 'Trzęsienie', ik: '🌋', cd: () => ewo('u2') >= 2 ? 8 : 11,
      opis: m => 'Tupnięcie (r 170): <span class="fiz">' + f0((20 + 0.06 * D.hpMax) * m) + '</span> (20 + 6% maks. zdrowia) i podrzucenie wrogów (0,7 s ogłuszenia).' + (ewo('u2') >= 1 ? ' Po 0,8 s wstrząs wtórny (50%).' : '') + (ewo('u2') >= 3 ? ' Zostawia szczelinę spowalniającą o 50% (3 s).' : ''),
      uzyj(m) { const v = (20 + 0.06 * D.hpMax) * m, x = gracz.x, y = gracz.y; const tup = (mn) => { fale.push({ x: x, y: y, czas: 0.45, max: 0.45, r: 170 * mnObszaru(), kolor: '#a08a6a' }); rozbryzg(x, y, '#8a7a5a', 12);
          obszarowe(x, y, 170, '#a08a6a', w => { zadaj(w, v * mn, 'fiz', { obszar: true, zr: 'Trzęsienie' }); oglusz(w, 0.7 * mn, { zrodlo: 'Trzęsienie' }); }, true); DZ.wybuch(); };
        tup(1); if (ewo('u2') >= 1) { const ja = gracz; opoznione(0.8, () => { if (gracz === ja && stan === 'walka') tup(0.5); }); }
        if (ewo('u2') >= 3) polaEfektow.push({ wl: gracz, x: x, y: y, r: 140 * mnObszaru(), czas: 3, max: 3, tyk: 0.5, rodzaj: 'kwas', spow: 0.5, obr: v * 0.05, zr: 'Trzęsienie' });
        return true; } },
    ewo: [
      { id: 'u1', ik: '🪨', n: 'Kamienna skóra', r: ['+1 s niewrażliwości', 'przyciągnięci wrogowie dostają +20% obrażeń', 'fala końcowa r 300 i 20% maks. zdrowia'] },
      { id: 'u2', ik: '🌋', n: 'Trzęsienie', r: ['wstrząs wtórny po 0,8 s (50%)', 'odnowienie 8 s (zamiast 11)', 'szczelina spowalnia o 50% przez 3 s'] },
      { id: 'pas', ik: '🗿', n: 'Sigma grindset', r: ['maks. zdrowie ×1,4', '<span class="onhit">on-hit</span> 4% maks. zdrowia', 'każde 100 maks. zdrowia: +1% redukcji obrażeń (do 25%)'] },
    ],
    kolory: { plaszcz: ['#5a5a6a', '#2a2a34'], tunika: ['#8a7a6a', '#4a4034'], wlosy: '#3a3030' },
  },
  // ------------------------------------------------------------------ ELF
  elf: {
    wyglad: { czapka: 'kaptur', kol: '#2e7a3a', uszy: true },
    n: 'Elf', ik: '🧝', rola: 'dystans · naładowane salwy', slotyOreza: 4, slotyPrzedm: 4, start: 'luk', rodziny: ['strzelecka'], hpZaPoziom: 4,
    staty: { hpMax: -35, ms: 20, zasieg: 15, kryt: 10 },
    opis: 'Szybki łucznik z małą ilością zdrowia. Bieganie i strzały ładują <b>⚡ energię</b> (szybciej niż innym). Pełna energia <b>sama odpala Salwę</b>: większe, przebijające strzały, kilka naraz, dużo prędkości ataku i obrażeń. Pierwsza strzała Salwy jest naładowana (działa z przedmiotami „naładowany atak”).',
    energia: true, mnEnergii: 1.8,
    blokujEnergie: st => st.salwa > czasGry,
    naPelnaEnergie(st) { st.salwa = czasGry + 3 + (ewo('u1') >= 1 ? 1 : 0); oznaczStaty(); if (gracz === lokalny || !druzyna()) DZ.pryzmat(); fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 90, kolor: '#9fe8ff' }); },
    statyDyn(st, s) { if (!(st.salwa > czasGry)) return; s.as += 60 + (ewo('u1') >= 2 ? 20 : 0); s.obrBonus += 30; s.przebicie += 99; const b = gracz.bronie[0];
      s.pociski += 2 + Math.floor(((b && b.tier) || 0) / 2) + (ewo('u1') >= 2 ? 1 : 0); },
    modZadanych(st, w, typ, o) { if (o && o.atak && st.mocna) { st.mocna = false; spowolnij(w, 0.5, 1.5); efektBlysk(w.x, w.y, '#9fe8ff'); return 2; } return 1; },
    naTrafienie(st, w, k) { if (ewo('u1') >= 3 && st.salwa > czasGry && k.glowny && !w._wybSalwy) { w._wybSalwy = 1; obszarowe(w.x, w.y, 50, '#9fe8ff', o => { if (o !== w) zadaj(o, k.zadaneSurowe * 0.5, 'fiz', { obszar: true, zr: 'Salwa' }); }, true); } },
    umi: { n: 'Salwa', ik: '🏹', pasywna: true, podpowiedz: 'Salwa odpala się sama przy pełnej ⚡ energii (bieganie i strzały)',
      opis: m => '<b>Odpala się sama</b> przy pełnej ⚡ energii. Przez ' + fmt(3 + (ewo('u1') >= 1 ? 1 : 0)) + ' s: +' + (60 + (ewo('u1') >= 2 ? 20 : 0)) + '% prędkości ataku, +30% obrażeń, strzały są większe i <b>przebijają wszystkich</b>, a łuk wypuszcza <b>' + (3 + Math.floor(((gracz.bronie[0] && gracz.bronie[0].tier) || 0) / 2) + (ewo('u1') >= 2 ? 1 : 0)) + '</b> strzały naraz (więcej z tierem łuku).',
      uzyj() { return false; } },
    umi2: { n: 'Odskok', ik: '🍃', cd: () => ewo('u2') >= 1 ? 5 : 7,
      opis: m => 'Odskakujesz 150 px od najbliższego wroga. Następna strzała zadaje <b>2× obrażeń</b> i spowalnia o 50%, a Ty dostajesz +' + (ewo('u2') >= 2 ? 50 : 30) + ' ⚡ energii.' + (ewo('u2') >= 3 ? ' Zostawiasz wabik, który przyciąga wrogów na 2 s.' : ''),
      uzyj(m) { const c = najblizszyWrog(gracz.x, gracz.y, 400); let kx = -(gracz.kierX || 1), ky = 0; if (c) { const d = Math.hypot(gracz.x - c.x, gracz.y - c.y) || 1; kx = (gracz.x - c.x) / d; ky = (gracz.y - c.y) / d; }
        if (ewo('u2') >= 3) dodajStwora('wabik', gracz.x, gracz.y, 2, { aura: 160, obr: 0, zr: 'Odskok' });
        gracz.kierRX = kx; gracz.kierRY = ky; if (gracz.zdalny) gracz.umiKier = [kx, ky]; mrugnij(150); gracz.stanKlasy.mocna = true; dodajEnergie(ewo('u2') >= 2 ? 50 : 30); DZ.czar(); return true; } },
    ewo: [
      { id: 'u1', ik: '🏹', n: 'Salwa', r: ['+1 s trwania', '+1 strzała i +20% prędkości ataku', 'pierwsze trafienie każdego wroga wybucha (r 50, 50%)'] },
      { id: 'u2', ik: '🍃', n: 'Odskok', r: ['odnowienie 5 s (zamiast 7)', '+50 energii (zamiast 30)', 'zostawia wabik na 2 s'] },
      { id: 'luk', ik: '🎯', n: 'Łuk', bron: 0, r: EWO_BRONI },
    ],
    kolory: { plaszcz: ['#3a8a3a', '#1a4a1a'], tunika: ['#c0d890', '#6a8a3a'], wlosy: '#f0e0a0' },
  },
  // ------------------------------------------------------------------ ASSASSIN
  assassin: {
    wyglad: { czapka: 'maska' },
    n: 'Assassin', ik: '🥷', rola: 'wręcz · kryty, shurikeny', slotyOreza: 4, slotyPrzedm: 4, start: 'sztylety', rodziny: ['biala', 'strzelecka'], hpZaPoziom: 5,
    staty: { hpMax: -30, ms: 15, kryt: 15, lethality: 8 },
    opis: 'Mało zdrowia, dużo krytów. <b>Shurikeny (pasywka):</b> co ' + '1,6 s (⏱️ przyspieszenie skraca) rzuca 2 shurikeny w najbliższych wrogów; każdy odbija się 2 razy bez utraty siły, może trafić krytycznie i rośnie z ⚔️ i szansą na kryt.',
    tik(st, dt) { tikShurikenow(st, dt); },
    naZabicie(st, w, o) { if (o && o.zr === 'Cięcie cienia' && ewo('u1') >= 2 && gracz.umi.cd > 0) gracz.umi.cd *= 0.5; },
    naAtak(st) { if (st.zCienia > 0) { st.zCienia--; st.pewnyKryt = true; } },
    umi: { n: 'Cięcie cienia', ik: '🗡️', cd: 8,
      opis: m => 'Wirujące cięcie wszystkich wrogów wokół Ciebie (r ' + f0(Math.max(140, zasiegAtakuGl() * 2.2)) + '): <b>' + f0(320 * m) + '%</b> obrażeń broni (nakłada efekty <span class="onhit">on-hit</span>). Dobija zwykłych wrogów i elity poniżej <b>' + (ewo('u1') >= 1 ? 18 : 12) + '%</b> zdrowia.' + (ewo('u1') >= 3 ? ' Po 0,5 s cień powtarza cięcie (50%).' : ''),
      uzyj(m) { const b = gracz.bronie[0]; if (!b) return false; const ja = gracz;
        const tnij = (mn) => { if (gracz !== ja || stan !== 'walka') return; const zas = Math.max(140, zasiegAtaku(b) * 2.2), prog = ewo('u1') >= 1 ? 0.18 : 0.12;
          ciecia.push({ x: gracz.x, y: gracz.y, kat: 0, luk: Math.PI * 2, r: zas, czas: 0.3, max: 0.3, kolor: '#9a6ae0' });
          wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - gracz.x, w.y - gracz.y) > zas + w.r) return; trafienieAtakiem(w, b, { mn: 3.2 * m * mn, glowny: true });
            if (!w.martwy && !w.boss && w.hp < w.hpMax * prog) { w.hp = 0; zabij(w, { zr: 'Cięcie cienia' }); tekstSwiat(w.x, w.y - w.r - 12, '✂️', '#e0c8ff', 0.6, 13); } }); DZ.kryt(); };
        tnij(1); if (ewo('u1') >= 3) opoznione(0.5, () => tnij(0.5)); return true; } },
    umi2: { n: 'Zasłona dymna', ik: '💨', cd: 13,
      opis: m => 'Doskok o 220 w kierunku ruchu i chmura dymu: znikasz na ' + fmt(2.5 + (ewo('u2') >= 1 ? 1 : 0)) + ' s — wrogowie Cię nie widzą i nie atakują, +30% prędkości ruchu' + (ewo('u2') >= 2 ? ', shurikeny lecą 2× częściej' : '') + '. ' + (ewo('u2') >= 3 ? '3 pierwsze ataki' : 'Pierwszy atak') + ' po wyjściu z cienia to <b>pewny kryt</b>.',
      uzyj(m) { const t = 2.5 + (ewo('u2') >= 1 ? 1 : 0), x0 = gracz.x, y0 = gracz.y;
        for (let n = 0; n < 18; n++) czastki.push({ x: x0 + losowo(-34, 34), y: y0 + losowo(-34, 34), vx: losowo(-40, 40), vy: losowo(-60, 0), czas: 0.9, max: 0.9, kolor: n % 3 ? '#8a8a9a' : '#5a5a6a' });
        fale.push({ x: x0, y: y0, czas: 0.45, max: 0.45, r: 70, kolor: '#9a9aaa' });
        mrugnij(220); gracz.niewidzialny = t; dodajBuff('dym', { ms: 0.3 * D.ms }, t); gracz.stanKlasy.zCienia = ewo('u2') >= 3 ? 3 : 1;
        wrogowie.forEach(w => { if (w.cel === gracz) { w.cel = null; w.tCelu = 0; w.zamach = 0; } });
        DZ.czar(); return true; } },
    ewo: [
      { id: 'sh', ik: '✴️', n: 'Shurikeny', r: ['+1 shuriken', '+2 odbicia', '+1 shuriken i shurikeny nakładają efekty <span class="onhit">on-hit</span>'] },
      { id: 'u1', ik: '🗡️', n: 'Cięcie cienia', r: ['dobija poniżej 18%', 'zabójstwo skraca odnowienie o połowę', 'cień powtarza cięcie po 0,5 s (50%)'] },
      { id: 'u2', ik: '💨', n: 'Zasłona dymna', r: ['+1 s niewidzialności', 'w cieniu shurikeny lecą 2× częściej', '3 pewne kryty po wyjściu z cienia'] },
    ],
    kolory: { plaszcz: ['#2a2a3a', '#101018'], tunika: ['#4a3a6a', '#24183a'], wlosy: '#1a1a1a' },
  },
  // ------------------------------------------------------------------ BOMBA
  bombardierka: {
    wyglad: { czapka: 'gogle' },
    n: 'Bomba', ik: '💣', rola: 'dystans · wybuchy', slotyOreza: 4, slotyPrzedm: 4, start: 'granatnik', rodziny: ['alchemia'],
    staty: { hpMax: 5, obszar: 30 },
    opis: 'Wybuchy i obszar zadają <b>+40%</b> obrażeń, +30% wielkości obszarów. <b>Reakcja łańcuchowa:</b> wrogowie zabici obrażeniami obszarowymi mają 25% szans wybuchnąć (r 60): 20 + 30% ⚔️ + 30% ✨.',
    statyFlat(st, s) { if (ewo('pas') >= 2) s.obszar += 20; },
    modZadanych(st, w, typ, o) { return o.obszar ? (ewo('pas') >= 3 ? 1.65 : 1.4) : 1; },
    naZabicie(st, w, o) { if (!o || !o.obszar || Math.random() > (ewo('pas') >= 1 ? 0.4 : 0.25)) return; const v = (20 + 0.3 * D.ad + 0.3 * D.ap) * mnUmi();
      opoznione(0.08, () => { if (stan !== 'walka') return; fale.push({ x: w.x, y: w.y, czas: 0.3, max: 0.3, r: 60 * mnObszaru(), kolor: '#ffb070' }); rozbryzg(w.x, w.y, '#ffb070', 8);
        obszarowe(w.x, w.y, 60, '#ffb070', o2 => zadaj(o2, v, 'fiz', { obszar: true, zr: 'Reakcja łańcuchowa' }), true); }); },
    umi: { n: 'Wielka bomba', ik: '💥', cd: () => ewo('u1') >= 3 ? 8 : 12,
      opis: m => 'Rzuca wielką bombę na skupisko wrogów (r ' + (200 + (ewo('u1') >= 1 ? 40 : 0)) + ', po 1,1 s): <span class="fiz">' + f0((200 + 2 * D.ad + 1.5 * D.ap) * m) + '</span> (200 + 200% ⚔️ + 150% ✨) i ogłuszenie 1,5 s.' + (ewo('u1') >= 2 ? ' Rozpada się na 4 bomby kasetowe (40%).' : ''),
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 320, 160) || najblizszyWrog(gracz.x, gracz.y, 320); if (!c) return false; const v = (200 + 2 * D.ad + 1.5 * D.ap) * m;
        granat(gracz.x, gracz.y, c.x, c.y, 200 + (ewo('u1') >= 1 ? 40 : 0), v, 'fiz', 'Wielka bomba', 1.1, 1.5);
        if (ewo('u1') >= 2) for (let n = 0; n < 4; n++) { const k = n * Math.PI / 2 + 0.6; granat(c.x, c.y, c.x + Math.cos(k) * 120, c.y + Math.sin(k) * 120, 80, v * 0.4, 'fiz', 'Wielka bomba', 1.6, 0.4); }
        return true; } },
    umi2: { n: 'Miny', ik: '⚙️', cd: 10,
      opis: m => 'Rozrzuca ' + (5 + (ewo('u2') >= 1 ? 3 : 0)) + ' min wokół siebie (15 s). Wróg, który wejdzie, wysadza minę (r 70): <span class="fiz">' + f0((40 + 0.6 * D.ad + 0.4 * D.ap) * m) + '</span> (40 + 60% ⚔️ + 40% ✨).' + (ewo('u2') >= 2 ? ' Wybuch spowalnia o 40%.' : '') + (ewo('u2') >= 3 ? ' Miny przyciągają wrogów.' : ''),
      uzyj(m) { const n = 5 + (ewo('u2') >= 1 ? 3 : 0), v = (40 + 0.6 * D.ad + 0.4 * D.ap) * m;
        for (let i = 0; i < n; i++) { const k = i / n * Math.PI * 2, r = losowo(50, 110); const s = dodajStwora('mina', gracz.x + Math.cos(k) * r, gracz.y + Math.sin(k) * r, 15, { obr: v / mnStw(), r: 70 * mnObszaru(), zr: 'Miny', spow: ewo('u2') >= 2 ? 0.4 : 0 });
          if (ewo('u2') >= 3) s.wabi = 1; } DZ.klik(); return true; } },
    ewo: [
      { id: 'u1', ik: '💥', n: 'Wielka bomba', r: ['promień +40', 'rozpada się na 4 bomby kasetowe (40%)', 'odnowienie 8 s (zamiast 12)'] },
      { id: 'u2', ik: '⚙️', n: 'Miny', r: ['+3 miny', 'wybuch spowalnia o 40%', 'miny przyciągają wrogów'] },
      { id: 'pas', ik: '🔥', n: 'Reakcja łańcuchowa', r: ['szansa na wybuch 40%', '+20% wielkości obszarów', 'obrażenia obszarowe +65% (zamiast 40%)'] },
    ],
    kolory: { plaszcz: ['#e6743c', '#8a3a14'], tunika: ['#2a2a2a', '#101010'], wlosy: '#ffb050' },
  },
  // ------------------------------------------------------------------ INŻYNIER
  inzynierka: {
    wyglad: { czapka: 'kask' },
    n: 'Inżynier', ik: '🔧', rola: 'dystans · działka', slotyOreza: 4, slotyPrzedm: 4, start: 'gwozdziarka', rodziny: ['strzelecka', 'alchemia'],
    staty: { hpMax: 5, haste: 15, pancerz: 10 },
    opis: 'Działka, wieże i inne stworzenia zadają <b>2× obrażeń</b>. Zaczyna z <b>Małą Wieżyczką</b>. Gwoździarka jest słabsza (obrażenia broni ×0,7).',
    mnStworow: () => 1 + (ewo('pas') >= 1 ? 0.4 : 0) + (ewo('pas') >= 3 ? 0.3 : 0), mnBroni: () => 0.7, dar() { gracz.przedmioty.push(nowyPrzedmiot('wiezyczka')); },
    naStartFali() { if (ewo('pas') >= 2) opoznione(0.5, () => postawDzialko('dzialko', 12, { obr: (30 + 0.7 * D.ad + 0.5 * D.ap) * mnUmi() * 0.6, co: 0.4, zr: 'Wieżyczka bojowa' })); },
    naObrazenia(st, w, v, typ, o) { if (ewo('u2') >= 3 && gracz.buffy.przeladowanie && o && (o.zr === 'Wieżyczka bojowa' || o.zr === 'Mała Wieżyczka')) leczWampirem(v * 0.05, 'Przeładowanie'); },
    umi2: { n: 'Przeładowanie', ik: '🔩', cd: 14,
      opis: m => 'Przez <b>' + (5 + (ewo('u2') >= 1 ? 2 : 0)) + ' s</b> wszystkie Twoje działka, wieże i stworzenia działają <b>2× szybciej</b>, a postawione stoją o 3 s dłużej. Tarcza ' + f0(15 * m) + '% maks. zdrowia.' + (ewo('u2') >= 2 ? ' +40% prędkości ataku.' : '') + (ewo('u2') >= 3 ? ' Działka leczą Cię o 5% swoich obrażeń.' : ''),
      uzyj(m) { const t = 5 + (ewo('u2') >= 1 ? 2 : 0); dodajBuff('przeladowanie', ewo('u2') >= 2 ? { as: 40 } : {}, t); stwory.forEach(s => { if (s.wl === gracz && s.max < 9000) s.czas += 3; }); dajTarcze(D.hpMax * 0.15 * m, 5);
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 120, kolor: '#e6c15c' }); DZ.awans(); return true; } },
    umi: { n: 'Wieżyczka bojowa', ik: '🏗️', cd: 14,
      opis: m => 'Stawia ' + (ewo('u1') >= 3 ? '<b>2</b> ciężkie wieżyczki' : 'ciężką wieżyczkę') + ' na ' + (12 + (ewo('u1') >= 1 ? 4 : 0)) + ' s: co ' + (ewo('u1') >= 2 ? '0,2' : '0,3') + ' s <span class="fiz">' + f0((30 + 0.7 * D.ad + 0.5 * D.ap) * m) + '</span> (30 + 70% ⚔️ + 50% ✨).',
      uzyj(m) { const n = ewo('u1') >= 3 ? 2 : 1; for (let i = 0; i < n; i++) postawDzialko('dzialko', 12 + (ewo('u1') >= 1 ? 4 : 0), { obr: (30 + 0.7 * D.ad + 0.5 * D.ap) * m, co: ewo('u1') >= 2 ? 0.2 : 0.3, zr: 'Wieżyczka bojowa' }); return true; } },
    ewo: [
      { id: 'u1', ik: '🏗️', n: 'Wieżyczka bojowa', r: ['+4 s trwania', 'strzela co 0,2 s', 'stawia 2 wieżyczki'] },
      { id: 'u2', ik: '🔩', n: 'Przeładowanie', r: ['+2 s trwania', '+40% prędkości ataku', 'działka leczą Cię o 5% swoich obrażeń'] },
      { id: 'pas', ik: '🔧', n: 'Warsztat', r: ['stworzenia ×2,4 obrażeń', 'na start fali darmowa wieżyczka (12 s)', 'stworzenia jeszcze +30% obrażeń'] },
    ],
    kolory: { plaszcz: ['#e6c15c', '#a07a1e'], tunika: ['#3a6ac4', '#1a3a7a'], wlosy: '#8a4a2a' },
  },
  // ------------------------------------------------------------------ NEKROMANTA
  nekromantka: {
    wyglad: { czapka: 'czaszka' },
    n: 'Nekromanta', ik: '💀', rola: 'dystans · armia sojuszników', slotyOreza: 4, slotyPrzedm: 4, start: 'kosturKosci', rodziny: ['magiczna'], hpZaPoziom: 4,
    staty: { hpMax: -15, ap: 20 },
    opis: 'Dowodzi armią: sojusznicy zadają <b>3× obrażeń</b> i żyją 3× dłużej, każdy zabity wróg ma 8% szans wstać po Twojej stronie. Kostur jest słaby (obrażenia broni ×0,6).',
    mnSojusznikow: () => 2 + (ewo('pas') >= 2 ? 0.5 : 0) + (ewo('pas') >= 3 ? 0.5 : 0), mnBroni: () => 0.6,
    umi2: { n: 'Detonacja', ik: '💥', cd: 8, brak: 'Nie masz sojuszników do wysadzenia',
      opis: m => 'Twoi sojusznicy wybuchają (r ' + (90 + (ewo('u2') >= 1 ? 40 : 0)) + '): <span class="mag">' + f0((50 + 0.7 * D.ap) * m) + '</span> (50 + 70% ✨) każdy. Za każdego leczysz się o ' + (ewo('u2') >= 2 ? 4 : 2) + '% maks. zdrowia.' + (ewo('u2') >= 3 ? ' Połowa wysadzonych wstaje ponownie.' : ''),
      uzyj(m) { const moi = wrogowie.filter(w => !w.martwy && w.sojusznik && w.zauroczony > 0 && w.wlasciciel === gracz); if (!moi.length) return false; const r = 90 + (ewo('u2') >= 1 ? 40 : 0);
        moi.forEach((s, n) => { s.martwy = true; s.bezLupu = true; rozbryzg(s.x, s.y, '#9ae07a', 10);
          obszarowe(s.x, s.y, r, '#9ae07a', w => zadaj(w, (50 + 0.7 * D.ap) * m, 'mag', { obszar: true, zr: 'Detonacja' }));
          if (ewo('u2') >= 3 && n % 2 === 0) { const ja = gracz; opoznione(0.6, () => { if (gracz === ja && stan === 'walka') wskrzesSojusznika({ typ: s.typ, x: s.x, y: s.y }, 8); }); } });
        leczGracza(D.hpMax * (ewo('u2') >= 2 ? 0.04 : 0.02) * moi.length, 'Detonacja'); DZ.wybuch(); return true; } },
    naZabicie(st, w) { if (!w.boss && !w.sojusznik && Math.random() < (ewo('pas') >= 1 ? 0.12 : 0.08)) wskrzesSojusznika(w, 8); },
    umi: { n: 'Armia ciemności', ik: '☠️', cd: 16,
      opis: m => 'Przywołuje ' + f0((7 + (ewo('u1') >= 1 ? 3 : 0)) * m) + ' szkieletów' + (ewo('u1') >= 2 ? ' (w tym kuszników)' : '') + ', które walczą po Twojej stronie przez ' + (ewo('u1') >= 3 ? 20 : 12) + ' s' + (ewo('u1') >= 3 ? ' (+50% zdrowia)' : '') + '.',
      uzyj(m) { const n0 = Math.round((7 + (ewo('u1') >= 1 ? 3 : 0)) * m), t = ewo('u1') >= 3 ? 20 : 12;
        for (let n = 0; n < n0; n++) { const k = n / n0 * Math.PI * 2; wskrzesSojusznika({ typ: ewo('u1') >= 2 && n % 3 === 0 ? 'kusznik' : 'szkielet', x: gracz.x + Math.cos(k) * 55, y: gracz.y + Math.sin(k) * 55 }, t);
          const s = wrogowie[wrogowie.length - 1]; if (ewo('u1') >= 3 && s && s.sojusznik) { s.hp *= 1.5; s.hpMax = s.hp; } } DZ.czar(); return true; } },
    ewo: [
      { id: 'u1', ik: '☠️', n: 'Armia ciemności', r: ['+3 szkielety', 'co trzeci to kusznik', 'żyją 20 s i mają +50% zdrowia'] },
      { id: 'u2', ik: '💥', n: 'Detonacja', r: ['promień +40', 'leczy 4% za sojusznika', 'połowa wysadzonych wstaje ponownie'] },
      { id: 'pas', ik: '💀', n: 'Mroczny pakt', r: ['12% szans na wskrzeszenie', 'sojusznicy +50% obrażeń', 'sojusznicy jeszcze +50% obrażeń i dłuższe życie'] },
    ],
    kolory: { plaszcz: ['#1a3a2a', '#0a1a10'], tunika: ['#4a4a5a', '#24242e'], wlosy: '#d8e8d0' },
  },
  // ------------------------------------------------------------------ DRUID
  druidka: {
    wyglad: { czapka: 'wieniec', broda: true },
    n: 'Druid', ik: '🌿', rola: 'dystans/wręcz · natura i trucizny', slotyOreza: 4, slotyPrzedm: 4, start: 'kosturNatury', rodziny: ['magiczna', 'alchemia'],
    staty: { hpMax: -5, leczenie: 30 },
    opis: 'Natura: <b>regeneracja ×3</b>, leczenie +30%, owoce i stworzenia +50%, zmęczenie słabsze o połowę. Druga umiejętność to <b>trujące zarodniki</b> zostawiane za sobą, które kosztują zdrowie. Kostur słabszy (×0,7). Zaczyna z <b>Krzakiem Jagód</b>.',
    mnRegen: () => ewo('pas') >= 1 ? 4.5 : 3,
    statyMnoz(st, s) { if (st.niedzwiedz > czasGry) { s.pancerz += 50; s.odpMag += 50; s.obrBonus += 30; } },
    mnStworow: () => ewo('pas') >= 2 ? 1 : 0.5, polZmeczenia: true, mnBroni: () => 0.7, dar() { gracz.przedmioty.push(nowyPrzedmiot('krzakJagod')); },
    naStartFali(st) { st.niedzwUzyty = false; },
    tik(st, dt) {
      if (ewo('pas') >= 3 && !st.niedzwUzyty && fala.aktywna && gracz.hp < D.hpMax * 0.3) { st.niedzwUzyty = true; st.niedzwiedz = czasGry + 6; leczGracza(D.hpMax * 0.4, 'Niedźwiedź'); oznaczStaty(); tekstSwiat(gracz.x, gracz.y - 34, '🐻 Niedźwiedź!', '#c8a070', 1.2, 15); DZ.boss(); }
      if (st.niedzwiedz > czasGry) { st.tN = (st.tN || 0) - dt; if (st.tN <= 0) { st.tN = 0.5; aura(80, '#8a6a4a', w => zadaj(w, (20 + 0.5 * D.ap + 0.02 * D.hpMax) * mnUmi(), 'fiz', { obszar: true, zr: 'Niedźwiedź' })); } }
      if (!st.zarodniki) return;
      if (!fala.aktywna || gracz.powalony) { st.zarodniki = false; return; }
      // koszt: 1% maks. zdrowia na sekundę (nie schodzi poniżej 10%)
      if (gracz.hp > D.hpMax * 0.1) gracz.hp = Math.max(D.hpMax * 0.1, gracz.hp - D.hpMax * 0.01 * dt);
      st.tZ = (st.tZ || 0) - dt; if (st.tZ > 0) return; st.tZ = 0.35;
      polaEfektow.push({ wl: gracz, x: gracz.x + losowo(-6, 6), y: gracz.y + losowo(-6, 6), r: 48 * mnObszaru(), czas: 4, max: 4, tyk: 0.2, rodzaj: 'trucizna', spow: 0.2,
        obr: (12 + 0.25 * D.ap + 0.01 * D.hpMax) * mnUmi() * 0.5 * (ewo('u2') >= 1 ? 1.4 : 1), zr: 'Zarodniki', lecz: ewo('u2') >= 2 ? 0.01 : 0, krusz: ewo('u2') >= 3 ? 0.2 : 0 });
    },
    umi2: { n: 'Zarodniki', ik: '🍄', cd: 0, przelacz: true, aktywna: st => !!st.zarodniki,
      opis: m => 'Przełącznik. <b>Włączone:</b> zostawiasz za sobą trujące chmury (4 s, r 48): <span class="mag">' + f0((12 + 0.25 * D.ap + 0.01 * D.hpMax) * m * (ewo('u2') >= 1 ? 1.4 : 1)) + '</span>/s (12 + 25% ✨ + 1% maks. zdrowia) i spowolnienie 20%. Chmury się nakładają.' + (ewo('u2') >= 2 ? ' Leczą kolegów w środku (1%/s).' : '') + (ewo('u2') >= 3 ? ' Kruszą pancerz i odporność o 20%.' : '') + ' Kosztuje <b>1% maks. zdrowia na sekundę</b> (nie zejdziesz poniżej 10%).',
      uzyj() { const st = gracz.stanKlasy; st.zarodniki = !st.zarodniki; st.tZ = 0; tekstSwiat(gracz.x, gracz.y - 34, st.zarodniki ? '🍄 Zarodniki: wł.' : '🍄 Zarodniki: wył.', '#9ae07a', 0.9, 12); return true; } },
    umi: { n: 'Zarośla', ik: '🌱', cd: 13,
      opis: m => 'Korzenie unieruchamiają wrogów w promieniu ' + (180 + (ewo('u1') >= 1 ? 60 : 0)) + ' na ' + fmt(1.6 * m) + ' s i zadają <span class="mag">' + f0((60 + 0.9 * D.ap) * m) + '</span> (60 + 90% ✨)' + (ewo('u1') >= 2 ? ', a przez 3 s dostają +25% obrażeń' : '') + '. Drużyna w promieniu 240 leczy się o ' + f0(20 * m) + '% maks. zdrowia.' + (ewo('u1') >= 3 ? ' Wyrastają 2 lecznicze drzewa.' : ''),
      uzyj(m) { aura(180 + (ewo('u1') >= 1 ? 60 : 0), '#5ac46a', w => { zadaj(w, (60 + 0.9 * D.ap) * m, 'mag', { obszar: true, zr: 'Zarośla' }); oglusz(w, 1.6 * m, { zrodlo: 'Zarośla' }); if (ewo('u1') >= 2) { w.naznaczony = Math.max(w.naznaczony || 0, 3); w.mnNazn = Math.max(w.mnNazn || 0, 0.25); } }, true);
        leczDruzyne(gracz.x, gracz.y, 240, 0, true, 0.2 * m);
        if (ewo('u1') >= 3) for (let n = 0; n < 2; n++) dodajStwora('krzak', gracz.x + (n ? 50 : -50), gracz.y, 10, { co: 3, lecz: 0.04, ikOwocu: '🍎', ik: '🌳', owoce: 1, regen: 0.01, aura: 110 });
        return true; } },
    ewo: [
      { id: 'u1', ik: '🌱', n: 'Zarośla', r: ['promień +60', 'unieruchomieni dostają +25% obrażeń przez 3 s', 'wyrastają 2 lecznicze drzewa (10 s)'] },
      { id: 'u2', ik: '🍄', n: 'Zarodniki', r: ['chmury +40% obrażeń', 'chmury leczą kolegów w środku', 'chmury kruszą pancerz i odporność o 20%'] },
      { id: 'pas', ik: '🐻', n: 'Dzika natura', r: ['regeneracja ×4,5', 'owoce i stworzenia ×2', 'raz na falę przy <30% zdrowia: Niedźwiedź (leczenie 40%, 6 s: +50 pancerza i odporności, +30% obrażeń, cios wokół)'] },
    ],
    kolory: { plaszcz: ['#3a7a2a', '#1a4a10'], tunika: ['#8a6a3a', '#5a4020'], wlosy: '#c87a2a' },
  },
  // ------------------------------------------------------------------ HAZARDZISTA
  hazardzistka: {
    wyglad: { czapka: 'fedora' },
    n: 'Hazardzista', ik: '🎲', rola: 'ryzyko na każdym kroku', slotyOreza: 4, slotyPrzedm: 4, start: 'kosci', rodziny: null,
    staty: { hpMax: -5, kryt: 10, ms: 10 },
    opis: 'Rzuca kośćmi (losowe obrażenia). <b>Ryzyko:</b> przy każdym wyborze (augment, statystyki, skrzynia, oferta w sklepie) może raz za darmo <b>zaryzykować 🎲</b>: 1/3 — przepada, 1/3 — zostaje, 1/3 — <b>ulepsza się</b> (wyższy tier). Co falę losuje dużą premię. +3 przerzuty augmentów.',
    hazard: true,
    dar() { gracz.przerzutyAug += 3; },
    naStartFali(st) {
      const opcje = [['as', 60, '⚡ +60% prędkości ataku'], ['ad', 50, '⚔️ +50 obrażeń od ataku'], ['ap', 90, '✨ +90 mocy umiejętności'], ['kryt', 40, '🎯 +40% szansy na kryt'],
        ['ms', 60, '👟 +60 prędkości ruchu'], ['pancerz', 80, '🛡️ +80 pancerza'], ['obrBonus', 30, '💥 +30% obrażeń'], ['chciwosc', 100, '💰 +100% złota'], ['haste', 50, '⏱️ +50 przyspieszenia']];
      const o = losZ(opcje); st.premia = { k: o[0], v: o[1] }; st.kary = []; st.bonusy = []; oznaczStaty(); dziennik('🎲 Premia fali: ' + o[2]);
    },
    naKoniecFali(st) { st.kary = []; st.bonusy = []; },
    statyFlat(st, s) { if (st.premia && fala && fala.aktywna) s[st.premia.k] += st.premia.v; },
    statyDyn(st, s) { if (st.jackpot > czasGry) { s.obrBonus += 150; s.kryt += 100; }
      const ak = (st.kary || []).filter(k => !k.do || k.do > czasGry); ak.forEach(k => { if (k.id === 'ciezki') s.ms -= 0.3 * s.ms; if (k.id === 'oslabiony') s.as -= 30; });
      if ((st.kary || []).some(k => k.id === 'kruchy' && (!k.do || k.do > czasGry))) { s.hpMax *= 0.7; } },
    modZadanych(st) { return (st.kary || []).some(k => k.id === 'slaby' && (!k.do || k.do > czasGry)) ? 0.75 : 1; },
    modOtrzymanych(st) { return (st.kary || []).some(k => k.id === 'odsloniety' && (!k.do || k.do > czasGry)) ? 1.25 : 1; },
    mnXp(st) { return 1 + 0.5 * (st.bonusy || []).filter(b => b === 'xp').length * (ewo('u1') >= 2 ? 1.5 : 1); },
    mnZlota(st) { return 1 + 0.5 * (st.bonusy || []).filter(b => b === 'zloto').length * (ewo('u1') >= 2 ? 1.5 : 1); },
    umi: { n: 'Ruletka', ik: '🎰', cd: 20,
      opis: m => 'Zakręć: <b>' + (ewo('u1') >= 1 ? 55 : 50) + '%</b> szans na nagrodę: ×1,5 złota albo +50% doświadczenia do końca fali, skrzynia, stała statystyka albo jackpot (6 s: +150% obrażeń, każdy atak krytyczny). W przeciwnym razie <b>kara do końca fali</b>' + (ewo('u1') >= 3 ? ' (tylko 15 s)' : '') + ': −25% obrażeń, −30% maks. zdrowia, −30% prędkości ruchu, −30% prędkości ataku albo +25% otrzymywanych obrażeń. Nagrody się kumulują, różne kary też (ta sama kara drugi raz się nie dokłada).',
      uzyj(m) { ruletka(); return true; } },
    umi2: { n: 'Koło fortuny', ik: '🎡', cd: () => ewo('u2') >= 3 ? 6 : 9,
      opis: () => 'Kręci kołem: <b>jackpot</b> (6 s: +150% obrażeń i każdy atak krytyczny), <b>joker</b> (umiejętność losowej innej postaci), salwa wybuchów, wir, niewrażliwość, szał, leczenie, złoto…' + (ewo('u2') >= 2 ? '' : ' albo <b>pech</b> (tracisz 15% zdrowia, ale następny rzut to pewny jackpot)') + '.',
      uzyj(m) { koloFortuny(m); return true; } },
    ewo: [
      { id: 'u1', ik: '🎰', n: 'Ruletka', r: ['55% szans na nagrodę', 'nagrody ×1,5', 'kary trwają tylko 15 s'] },
      { id: 'u2', ik: '🎡', n: 'Koło fortuny', r: ['jackpot 2× częściej', 'bez pecha', 'odnowienie 6 s (zamiast 9)'] },
      { id: 'pas', ik: '🎲', n: 'Ryzyko', r: ['przepada tylko 1/4, ulepsza ~42%', 'możesz ryzykować 2 razy przy każdym wyborze', 'gdy przepadnie — dostajesz 30% jego wartości w złocie'] },
    ],
    kolory: { plaszcz: ['#6a1a6a', '#3a0a3a'], tunika: ['#e0e0e0', '#9a9a9a'], wlosy: '#1a1a1a' },
  },
  // ------------------------------------------------------------------ KAPŁAN PRYZMATU
  kaplanka: {
    wyglad: { czapka: 'aureola' },
    n: 'Kapłan Pryzmatu', ik: '🔮', rola: 'wsparcie · pryzmaty', slotyOreza: 4, slotyPrzedm: 3, slotyPryzm: 4, start: 'kosturPustki', rodziny: ['magiczna'], hpZaPoziom: 4,
    staty: { hpMax: -15 },
    opis: 'Mistrz pryzmatów: <b>4 miejsca na pryzmaty</b> (za to 3 zwykłe przedmioty). Darmowe Pryzmatyczne Kowadło na start i drugie po 3. fali. <b>Tylko on ulepsza pryzmaty gwiazdkami ★</b> (+25% za każdą). Tarcze i leczenie dla drużyny +50%.',
    dar() { gracz.kowadla = (gracz.kowadla || 0) + 1; }, mnTarcz: 0.5, ulepszaPryzmaty: true,
    kowadloWybor: () => 3 + (ewo('pryzm') >= 1 ? 1 : 0) + (ewo('pryzm') >= 2 ? 1 : 0),
    kowadloPo: 3,   // darmowe kowadło, które inni dostają po 1. fali, Kapłan dostaje dopiero po 3.
    naKoniecFali(st) { if (ewo('pas') >= 3 && fala.nr % 5 === 0) { gracz.kowadla = (gracz.kowadla || 0) + 1; dziennik('🔨 Kapłan: darmowe Pryzmatyczne Kowadło'); } },
    modZadanych() { return ewo('pas') >= 2 ? 1 + 0.05 * liczPrzedm(true) : 1; },
    umi: { n: 'Pryzmatyczna tarcza', ik: '💠', cd: () => ewo('u1') >= 3 ? 10 : 13,
      opis: m => 'Ty i koledzy w promieniu 260 dostajecie tarczę <b>' + f0((35 + (ewo('u1') >= 1 ? 10 : 0)) * m) + '% maks. zdrowia</b> na 4 s, leczenie ' + f0(15 * m) + '% i +30% obrażeń na 5 s.' + (ewo('u1') >= 2 ? ' Tarcza, która przetrwa, na koniec wybucha (obrażenia = jej reszta).' : ''),
      uzyj(m) { leczDruzyne(gracz.x, gracz.y, 260, 0, true, 0.15 * m, (0.35 + (ewo('u1') >= 1 ? 0.1 : 0)) * m); const z0 = gracz, wyb = ewo('u1') >= 2;
        gracze.forEach(p => { if (p.powalony || Math.hypot(p.x - z0.x, p.y - z0.y) > 260) return; kontekst(p); dodajBuff('pryzmat', { obrBonus: 30 }, 5); if (wyb && p.tarcze.length) p.tarcze[p.tarcze.length - 1].wybuch = true; }); kontekst(z0);
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#ff9ae0' }); DZ.pryzmat(); return true; } },
    ewo: [
      { id: 'u1', ik: '💠', n: 'Pryzmatyczna tarcza', r: ['tarcza +10% maks. zdrowia', 'tarcza, która przetrwa, wybucha', 'odnowienie 10 s (zamiast 13)'] },
      { id: 'pryzm', ik: '🔨', n: 'Kowadło', r: ['Pryzmatyczne Kowadło: wybór z 4', 'wybór z 5', '+1 miejsce na pryzmat (5)'], naZakup: r => { if (r === 3) gracz.slotyPryzm++; } },
      { id: 'pas', ik: '🔮', n: 'Objawienie', r: ['ulepszanie pryzmatów 25% taniej', 'każdy pryzmat: +5% wszystkich obrażeń', 'darmowe Pryzmatyczne Kowadło co 5 fal'] },
    ],
    kolory: { plaszcz: ['#e07ac0', '#7a3a8a'], tunika: ['#7ae0ff', '#3a8aa0'], wlosy: '#ffffff' },
  },
  // ------------------------------------------------------------------ FARMER
  farmer: {
    wyglad: { czapka: 'slomkowy', broda: true },
    n: 'Farmer', ik: '🧑‍🌾', rola: 'farmienie złota i doświadczenia · rośnie bez końca', slotyOreza: 4, slotyPrzedm: 4, start: 'widly', rodziny: ['biala'], hpZaPoziom: 5,
    staty: { hpMax: -20, xpBonus: 20, chciwosc: 15 },
    opis: 'Na początku słaby, ale <b>rośnie bez końca</b>. <b>Gospodarstwo:</b> co 100 zabitych potworów (cała gra) zbiera <b>Urodzaj</b>: +2% obrażeń, +1% maks. zdrowia, +1% doświadczenia i złota — bez limitu. Na koniec fali zbiera plony (złoto i doświadczenie, więcej z każdym Urodzajem). <b>Sam sadzi</b> plony, które co sekundę dają złoto i doświadczenie.',
    urodzaj(st) { return Math.floor((st.zabite || 0) / (ewo('pas') >= 1 ? 75 : 100)); },
    naZabicie(st, w) { if (w.sojusznik) return; const przed = KLASY.farmer.urodzaj(st); st.zabite = (st.zabite || 0) + 1; if (KLASY.farmer.urodzaj(st) > przed) { oznaczStaty(); tekstSwiat(gracz.x, gracz.y - 34, '🌾 Urodzaj ' + KLASY.farmer.urodzaj(st) + '!', '#ffe08a', 1.2, 14); DZ.awans(); } },
    statyFlat(st, s) { const u = KLASY.farmer.urodzaj(st); s.xpBonus += u; s.chciwosc += u; },
    statyMnoz(st, s) { s.hpMax *= 1 + 0.01 * KLASY.farmer.urodzaj(st); },
    modZadanych(st) { return 1 + 0.02 * KLASY.farmer.urodzaj(st); },
    naKoniecFali(st) { const u = KLASY.farmer.urodzaj(st), mn = (1 + 0.1 * u) * (ewo('pas') >= 2 ? 1.5 : 1);
      dodajZloto((4 + 1.5 * fala.nr) * mn, false, '🌾 Zbiory'); dodajXp((5 + 2 * fala.nr) * mn);
      if (ewo('pas') >= 3) { const z = Math.min(100, gracz.zloto * 0.05); if (z >= 1) dodajZloto(Math.floor(z), true, '🏦 Odsetki'); } },
    plonuj(s) { const mn = (ewo('u1') >= 2 ? 1.5 : 1) * mnUmi(); dodajZloto(0.25 * (1 + fala.nr * 0.08) * mn); dodajXp(0.4 * (1 + fala.nr * 0.1) * mn);
      if (ewo('u1') >= 3 && Math.hypot(gracz.x - s.x, gracz.y - s.y) < 100) leczGracza(D.hpMax * 0.005, 'Złote kłosy', true); },
    umi: { n: 'Sadzenie', ik: '🌱', cd: 6, auto: true,
      opis: m => '<b>Sadzi się samo</b> co ' + fmt(cdUmiTeraz(KLASY.farmer.umi)) + ' s (do ' + (5 + (ewo('u1') >= 1 ? 3 : 0)) + ' plonów naraz, do końca fali). Każdy plon co sekundę daje <b>' + fmt(0.25 * (1 + nrFali() * 0.08) * m * (ewo('u1') >= 2 ? 1.5 : 1)) + ' złota</b> i ' + fmt(0.4 * (1 + nrFali() * 0.1) * m * (ewo('u1') >= 2 ? 1.5 : 1)) + ' doświadczenia — nie trzeba zbierać.' + (ewo('u1') >= 3 ? ' Stojąc przy plonach leczysz się o 0,5% maks. zdrowia/s.' : ''),
      uzyj(m) { const moje = stwory.filter(s => s.typ === 'plon' && s.wl === gracz); if (moje.length >= 5 + (ewo('u1') >= 1 ? 3 : 0)) { moje[0].czas = 0; }
        dodajStwora('plon', gracz.x + losowo(-12, 12), gracz.y + losowo(-12, 12), 9999, { ik: '🌱' }); return true; } },
    ewo: [
      { id: 'u1', ik: '🌱', n: 'Sadzenie', r: ['+3 plony naraz', 'plony dają +50%', 'Złote kłosy: przy plonach leczysz się 0,5%/s'] },
      { id: 'widly', ik: '🔱', n: 'Widły', bron: 0, r: EWO_BRONI },
      { id: 'pas', ik: '🌾', n: 'Gospodarstwo', r: ['Urodzaj co 75 zabitych (zamiast 100)', 'zbiory na koniec fali ×1,5', 'odsetki: 5% złota na koniec fali (maks. 100)'] },
    ],
    kolory: { plaszcz: ['#8a6a2a', '#4a3a14'], tunika: ['#3a6ac4', '#1a3a7a'], wlosy: '#c8a060' },
  },
};
const KLUCZE_KLAS = Object.keys(KLASY);
function opisRodzinKlasy(K) { return K.rodziny ? K.rodziny.map(r => RODZINY[r].ik + ' ' + RODZINY[r].n).join(', ') : 'wszystkie po równo'; }
function opisBroniStartowej(K) { return K.start === 'losowa' ? '🎲 losowa' : K.start === 'wybor' ? '✋ do wyboru (II tier)' : K.start === 'wybor2' ? '✋✋ dwie do wyboru' : BRONIE[K.start].ikona + ' ' + BRONIE[K.start].nazwa; }
function zasiegAtakuGl() { return gracz && gracz.bronie[0] && D ? zasiegAtaku(gracz.bronie[0]) : 70; }

// ---------------------------------------------------------------------
//  Cechy broni z Mistrzostwa (One-handed): po V tierze każdy poziom Mistrzostwa = wybór 1 z 3
// ---------------------------------------------------------------------
const PERKI_MISTRZA = {
  szybkosc: { ik: '⚡', n: 'Błyskawiczne ręce', o: '+20% prędkości ataku', s: { as: 20 } },
  kryt: { ik: '🎯', n: 'Precyzja', o: '+12% szansy na kryt', s: { kryt: 12 } },
  krytObr: { ik: '💥', n: 'Zabójczy cios', o: '+30% obrażeń krytycznych', s: { krytObr: 30 } },
  zasieg: { ik: '🏹', n: 'Długie ramię', o: '+20% zasięgu', s: { zasieg: 20 } },
  pociski: { ik: '➶', n: 'Wielokrotność', o: '+1 pocisk (bronie strzelające)', s: { pociski: 1 } },
  obszar: { ik: '⭕', n: 'Szeroki zamach', o: '+25% wielkości obszarów', s: { obszar: 25 } },
  wampir: { ik: '🩸', n: 'Krwawe ostrze', o: '+4% wampiryzmu', s: { omni: 4 } },
  onhit: { ik: '🟠', n: 'Ciężka ręka', o: '+25 obrażeń fizycznych on-hit', s: { onHitFiz: 25 } },
  onhitMag: { ik: '🔵', n: 'Runy', o: '+25 obrażeń magicznych on-hit', s: { onHitMag: 25 } },
  przebicie: { ik: '🗡️', n: 'Przeszywanie', o: '+12 przebicia pancerza', s: { lethality: 12 } },
};
const CENY_MISTRZOSTWA = [500, 700, 900, 1150, 1400];
const MAKS_MISTRZOSTWA = 5;

// ---------------------------------------------------------------------
//  Mechaniki postaci
// ---------------------------------------------------------------------
// Więzień: Wir kajdan — smagnięcia co (0,32 s / prędkość ataku)
function odstepWiru() { return Math.max(0.07, 0.32 / (1 + Math.max(0, D ? D.as : 0) / 100)); }
function tikWiruKajdan(st, dt) {
  const wr = st.wir; if (!wr) return;
  wr.t -= dt; wr.tL -= dt;
  if (wr.tL <= 0 && fala.aktywna) {
    wr.tL = odstepWiru();
    const b = gracz.bronie[0], cele = najblizsi(gracz.x, gracz.y, 170, ewo('u1') >= 2 ? 2 : 1);
    cele.forEach((w, n) => {
      const kr = Math.random() * 100 < D.kryt, v = (15 + 0.45 * D.ad + 0.15 * D.ap) * wr.m * (kr ? 1.75 + D.krytObr / 100 : 1) * (n ? 0.5 : 1);
      const z = zadaj(w, v, 'fiz', { zr: 'Wir kajdan', kryt: kr, atak: true }); wr.suma += z;
      dodajBlyskawice(gracz.x, gracz.y - 4, w.x, w.y, '#c8c8d8');
      if (b && !w.martwy && n === 0) zastosujOnHit(w, b, { k: { bron: b, kryt: kr, glowny: true, zadane: z, zadaneSurowe: v, bazowe: v, licznikCiosu: 1, zOgluszenia: false } });
      if (z > 0) leczWampirem(z * 0.15, 'Wir kajdan');
    });
  }
  if (wr.t <= 0) {
    st.wir = null; gracz.korzen = 0;
    if (ewo('u1') >= 3) { fale.push({ x: gracz.x, y: gracz.y, czas: 0.45, max: 0.45, r: 160 * mnObszaru(), kolor: '#c8c8d8' }); aura(160, '#c8c8d8', w => zadaj(w, (40 + 1.5 * D.ad) * wr.m, 'fiz', { obszar: true, zr: 'Wir kajdan' }), true); dodajBuff('wirKoniec', { ms: 0.4 * D.ms }, 2); DZ.wybuch(); }
  }
}
// Assassin: shurikeny co 1,6 s (przyspieszenie skraca), odbijają się bez utraty siły
function tikShurikenow(st, dt) {
  if (!fala.aktywna) return;
  st.tS = (st.tS || 0) - dt * (ewo('u2') >= 2 && gracz.niewidzialny > 0 ? 2 : 1);
  if (st.tS > 0) return;
  const ile = 2 + (ewo('sh') >= 1 ? 1 : 0) + (ewo('sh') >= 3 ? 1 : 0), cele = najblizsi(gracz.x, gracz.y, 320, ile);
  if (!cele.length) { st.tS = 0.2; return; }
  st.tS = 1.6 * 100 / (100 + Math.max(0, D.haste));
  const v = (10 + 0.45 * D.ad + 0.5 * Math.max(0, D.kryt)) * mnUmi();
  for (let n = 0; n < ile; n++) { const c = cele[n % cele.length];
    wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, c) + (n - (ile - 1) / 2) * 0.25, cel: c, predkosc: 600, obr: v, typ: 'fiz', kolor: '#d8d8e8', ksztalt: 'shuriken', zr: 'Shurikeny', zycie: 1.1, naprowadza: 7,
      odbicia: 2 + (ewo('sh') >= 2 ? 2 : 0), mozeKryt: true, bezSpadku: true, zasiegOdbicia: 190, onHit: ewo('sh') >= 3 }); }
  if (mozna('shuriken', 120)) ton(900, 0.04, 'triangle', 0.04);
}
// skok w miejsce (Berserker): jak mignięcie, ale do punktu
function skokDo(tx, ty, maks) {
  const dx = tx - gracz.x, dy = ty - gracz.y, d = Math.hypot(dx, dy) || 1, dl = Math.min(maks, d);
  gracz.kierRX = dx / d; gracz.kierRY = dy / d; if (gracz.zdalny) gracz.umiKier = [dx / d, dy / d];
  mrugnij(dl);
}
// Hazardzista: Ruletka 50/50
const KARY_RULETKI = { slaby: '−25% obrażeń', kruchy: '−30% maks. zdrowia', ciezki: '−30% prędkości ruchu', oslabiony: '−30% prędkości ataku', odsloniety: '+25% otrzymywanych obrażeń' };
function ruletka() {
  const st = gracz.stanKlasy; st.kary = st.kary || []; st.bonusy = st.bonusy || [];
  const wygrana = Math.random() < (ewo('u1') >= 1 ? 0.55 : 0.5), mn = ewo('u1') >= 2 ? 1.5 : 1;
  const T = (t, k) => { tekstSwiat(gracz.x, gracz.y - 40, t, k, 1.3, 15); if (!gracz.zdalny) toast(t); };
  if (wygrana) {
    const r = losWazony([['zloto', 22], ['xp', 22], ['skrzynia', 20], ['stat', 22], ['jackpot', 14]]);
    if (r === 'zloto') { st.bonusy.push('zloto'); T('🎰 Złoto ×' + fmt(1 + 0.5 * mn) + ' do końca fali!', '#ffd24a'); }
    else if (r === 'xp') { st.bonusy.push('xp'); T('🎰 Doświadczenie +' + Math.round(50 * mn) + '% do końca fali!', '#9fd8ff'); }
    else if (r === 'skrzynia') { const t = Math.min(3, tierSkrzyni(null) + (Math.random() * 100 < D.szczescie * mn ? 1 : 0)); gracz.skrzynie.push({ tier: t }); T('🎰 Skrzynia (' + TIERY[t].nazwaZ.toLowerCase() + ')!', TIERY[t].kolor); }
    else if (r === 'stat') { const u = losUlepszeniaStatu(1); const v = u.w[1] * mn; gracz.stale[u.k] = (gracz.stale[u.k] || 0) + v; oznaczStaty(); T('🎰 Na stałe: ' + STAT[u.k].i + ' +' + fmt(v) + (STAT[u.k].j === '%' ? '%' : ''), '#7ee87a'); }
    else { st.jackpot = czasGry + 6 * mn; oznaczStaty(); T('🎰 JACKPOT!', '#ffd24a'); fale.push({ x: gracz.x, y: gracz.y, czas: 0.7, max: 0.7, r: 200, kolor: '#ffd24a' }); }
    DZ.pryzmat();
  } else {
    // każda kara działa najwyżej raz naraz (ta sama wylosowana drugi raz tylko się odnawia)
    const id = losZ(Object.keys(KARY_RULETKI)), ist = st.kary.find(k => k.id === id && (!k.do || k.do > czasGry));
    if (ist) ist.do = ewo('u1') >= 3 ? czasGry + 15 : 0; else st.kary.push({ id: id, do: ewo('u1') >= 3 ? czasGry + 15 : 0 }); oznaczStaty();
    if (id === 'kruchy') zastosujStaty();
    T('🎰 Pech: ' + KARY_RULETKI[id] + (ewo('u1') >= 3 ? ' (15 s)' : ' do końca fali'), '#ff6a5a'); DZ.obrazenia();
  }
}
// Hazardzista: Koło fortuny (druga umiejętność)
function koloFortuny(m) {
  const st = gracz.stanKlasy;
  const r = st.pewnyJackpot ? 0 : losWazony([[0, ewo('u2') >= 1 ? 14 : 7], [1, 14], [2, 13], [3, 11], [4, 9], [5, 10], [6, 9], [7, 8], [8, 9], [ewo('u2') >= 2 ? 7 : 9, 10]]);
  st.pewnyJackpot = false;
  const T = (t) => { if (!gracz.zdalny) toast('🎡 ' + t); tekstSwiat(gracz.x, gracz.y - 40, '🎡 ' + t, '#ffe08a', 1.2, 15); };
  if (r === 0) { st.jackpot = czasGry + 6; oznaczStaty(); DZ.pryzmat(); T('JACKPOT!'); fale.push({ x: gracz.x, y: gracz.y, czas: 0.7, max: 0.7, r: 200, kolor: '#ffd24a' }); }
  else if (r === 1) { const inne = KLUCZE_KLAS.filter(k => k !== 'hazardzistka' && KLASY[k].umi && !KLASY[k].umi.pasywna && !KLASY[k].umi.auto); let ok = false;
    for (let p = 0; p < 4 && !ok; p++) { const k = losZ(inne); try { ok = KLASY[k].umi.uzyj(m) !== false; } catch (e) { ok = false; } if (ok) T('Joker: ' + KLASY[k].umi.ik + ' ' + KLASY[k].umi.n); }
    if (!ok) { gracz.niewr = Math.max(gracz.niewr, 2); T('Joker: unik losu'); } }
  else if (r === 2) { for (let n = 0; n < 10; n++) opoznione(0.06 * n, () => { const x = gracz.x + losowo(-220, 220), y = gracz.y + losowo(-220, 220); obszarowe(x, y, 70, '#ffb070', w => zadaj(w, (80 + 0.8 * D.ad + 0.8 * D.ap) * m, 'mag', { obszar: true, zr: 'Koło fortuny' })); rozbryzg(x, y, '#ffb070', 8); }); DZ.wybuch(); T('Salwa wybuchów!'); }
  else if (r === 3) { wrogowie.forEach(w => { if (w.martwy || w.boss || w.zauroczony > 0) return; const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); if (d < 260 && d > 1) { w.x += (gracz.x - w.x) / d * Math.min(d - 30, 140); w.y += (gracz.y - w.y) / d * Math.min(d - 30, 140); oglusz(w, 1.5, { zrodlo: 'Koło fortuny' }); } }); fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#9a6ae0', odwrot: true }); T('Wir!'); }
  else if (r === 4) { gracz.niewr = Math.max(gracz.niewr, 4); T('4 s niewrażliwości!'); }
  else if (r === 5) { dodajBuff('kolo', { as: 100 * m, ms: 40 }, 6); T('Szał!'); }
  else if (r === 6) { leczGracza(D.hpMax * 0.5, 'Koło fortuny'); T('Leczenie!'); }
  else if (r === 7) { dodajZloto(Math.round((10 + 4 * fala.nr) * m), true, '🎡 Koło fortuny'); T('Złoto!'); }
  else if (r === 8) { st.natychmiast = 2; T('Kręć jeszcze raz!'); }
  else { gracz.hp = Math.max(1, gracz.hp - D.hpMax * 0.15); st.pewnyJackpot = true; T('Pech… następny rzut to JACKPOT'); }
}

// =====================================================================
//  WROGOWIE, ELITY, BOSSOWIE i ich zachowanie
// =====================================================================
const TYPY_WROGOW = {
  szczur:   { n: 'Szczur', ik: '🐀', hp: 20, atak: 6, panc: 0, odp: 0, ms: 95, xp: 2, zl: 1, r: 13, kolor: '#8a6a4a' },
  goblin:   { n: 'Goblin', ik: '👺', hp: 28, atak: 8, panc: 6, odp: 0, ms: 110, xp: 2, zl: 1, r: 15, kolor: '#5a9a4a' },
  szkielet: { n: 'Szkielet', ik: '💀', hp: 42, atak: 10, panc: 18, odp: 5, ms: 80, xp: 3, zl: 1, r: 16, kolor: '#d8d0c0' },
  pajak:    { n: 'Pająk', ik: '🕷️', hp: 14, atak: 5, panc: 0, odp: 0, ms: 150, xp: 1, zl: 1, r: 12, kolor: '#4a3a5a' },
  okrazacz: { n: 'Nietoperz', ik: '🦇', hp: 26, atak: 7, panc: 4, odp: 6, ms: 125, xp: 3, zl: 2, r: 15, kolor: '#6a5a8a', dyst: 230, typObr: 'mag', zach: 'okrazajacy' },
  bombiarz: { n: 'Bombiarz', ik: '💣', hp: 34, atak: 16, panc: 3, odp: 0, ms: 160, xp: 3, zl: 2, r: 15, kolor: '#e6743c', wybuchowy: true },
  kusznik:  { n: 'Kusznik', ik: '🏹', hp: 30, atak: 12, panc: 6, odp: 0, ms: 68, xp: 3, zl: 2, r: 15, kolor: '#7a6a4a', dyst: 320, typObr: 'fiz' },
  trujacy:  { n: 'Skunks', ik: '🦨', hp: 55, atak: 9, panc: 6, odp: 6, ms: 105, xp: 4, zl: 2, r: 16, kolor: '#6a9a4a', zach: 'uciekajacy', typObr: 'mag' },
  mag:      { n: 'Mroczny mag', ik: '🧙', hp: 32, atak: 12, panc: 4, odp: 15, ms: 64, xp: 4, zl: 2, r: 16, kolor: '#8a5ac4', dyst: 260, typObr: 'mag', czary: true },
  jezdziec: { n: 'Jeździec', ik: '🐗', hp: 52, atak: 12, panc: 10, odp: 0, ms: 128, xp: 4, zl: 2, r: 17, kolor: '#8a5a3a', zach: 'szarzaBoki' },
  lucznik:  { n: 'Łucznik', ik: '🎯', hp: 28, atak: 11, panc: 5, odp: 0, ms: 78, xp: 3, zl: 2, r: 15, kolor: '#9a7a4a', dyst: 280, typObr: 'fiz', zach: 'okrazajacy' },
  czarodziej:{ n: 'Czarodziej', ik: '🔮', hp: 36, atak: 11, panc: 5, odp: 15, ms: 66, xp: 4, zl: 2, r: 16, kolor: '#4a9ad4', dyst: 290, typObr: 'mag', teleportuje: true, czary: true },
  ogr:      { n: 'Ogr', ik: '👹', hp: 120, atak: 18, panc: 28, odp: 10, ms: 58, xp: 7, zl: 4, r: 22, kolor: '#a04a3a' },
  szaman:   { n: 'Szaman', ik: '🧌', hp: 40, atak: 6, panc: 5, odp: 20, ms: 74, xp: 5, zl: 3, r: 16, kolor: '#4aa080', dyst: 200, typObr: 'mag', zach: 'okrazajacy', leczy: true },
  golem:    { n: 'Golem', ik: '🗿', hp: 150, atak: 20, panc: 40, odp: 20, ms: 50, xp: 8, zl: 5, r: 24, kolor: '#7a7a8a', rozpada: true },
  kamyk:    { n: 'Odłamek', ik: '🪨', hp: 45, atak: 10, panc: 20, odp: 10, ms: 88, xp: 2, zl: 1, r: 14, kolor: '#8a8a9a' },
  duch:     { n: 'Duch', ik: '👻', hp: 30, atak: 9, panc: 0, odp: 30, ms: 100, xp: 3, zl: 2, r: 15, kolor: '#c0d0ff', typObr: 'mag', duch: true },
  // ---- nowi wrogowie: wytrzymali, z własnymi sztuczkami (nie szybsi) ----
  szlam:    { n: 'Szlam', ik: '🟢', hp: 70, atak: 9, panc: 4, odp: 4, ms: 70, xp: 3, zl: 2, r: 18, kolor: '#5ac46a', dzieli: 'szlamMaly', opis: 'Po śmierci dzieli się na 2 małe szlamy' },
  szlamMaly:{ n: 'Mały szlam', ik: '🟢', hp: 26, atak: 6, panc: 2, odp: 2, ms: 88, xp: 1, zl: 0.5, r: 11, kolor: '#7ae08a' },
  krwiopijca:{ n: 'Krwiopijca', ik: '🦟', hp: 34, atak: 7, panc: 0, odp: 0, ms: 112, xp: 3, zl: 2, r: 13, kolor: '#c0392b', wysysa: true, opis: 'Leczy się o potrójne zadane obrażenia' },
  tarczownik:{ n: 'Tarczownik', ik: '🛡️', hp: 95, atak: 13, panc: 30, odp: 10, ms: 60, xp: 6, zl: 3, r: 19, kolor: '#7a8aa0', tarczaPrzod: true, opis: 'Z przodu blokuje 65% obrażeń — zajdź go z boku' },
  zombie:   { n: 'Zombie', ik: '🧟', hp: 120, atak: 14, panc: 8, odp: 0, ms: 52, xp: 5, zl: 3, r: 18, kolor: '#6a8a5a', wstaje: true, opis: 'Połowa wstaje raz po śmierci' },
  kultysta: { n: 'Kultysta', ik: '🕯️', hp: 55, atak: 8, panc: 6, odp: 25, ms: 70, xp: 6, zl: 3, r: 16, kolor: '#a04ad0', dyst: 220, typObr: 'mag', zach: 'okrazajacy', wzmacnia: true, opis: 'Wzmacnia wrogów obok: +30% obrażeń i −25% otrzymywanych' },
  jez:      { n: 'Kolczak', ik: '🦔', hp: 85, atak: 12, panc: 35, odp: 10, ms: 62, xp: 5, zl: 3, r: 18, kolor: '#8a6a4a', kolce: true, opis: 'Co chwilę strzela kolcami we wszystkie strony' },
  mozdzierz:{ n: 'Moździerzysta', ik: '🧨', hp: 48, atak: 15, panc: 8, odp: 5, ms: 60, xp: 6, zl: 3, r: 16, kolor: '#7a6a5a', dyst: 380, zach: 'okrazajacy', artyleria: true, opis: 'Ostrzeliwuje miejsce, w którym stoisz (czerwony krąg)' },
  upiorny:  { n: 'Upiorny rycerz', ik: '🤺', hp: 210, atak: 20, panc: 32, odp: 32, ms: 58, xp: 10, zl: 5, r: 21, kolor: '#5a6a9a', szarzuje: true, opis: 'Po chwili namierzania szarżuje prosto na Ciebie' },
};
// [od fali, typ, waga]
const PULA_WROGOW = [
  [1, 'szczur', 10], [1, 'goblin', 8], [2, 'szkielet', 7], [3, 'okrazacz', 4], [3, 'pajak', 4], [4, 'bombiarz', 3],
  [5, 'kusznik', 4], [6, 'trujacy', 3], [7, 'mag', 3], [7, 'jezdziec', 4], [8, 'lucznik', 3], [9, 'ogr', 3],
  [9, 'szaman', 2], [11, 'golem', 2], [11, 'czarodziej', 2], [12, 'duch', 3],
  [4, 'szlam', 4], [6, 'krwiopijca', 3], [8, 'tarczownik', 3], [10, 'zombie', 4], [12, 'kultysta', 2], [13, 'jez', 3], [14, 'mozdzierz', 2], [17, 'upiorny', 2],
];
const AFIKSY = {
  olbrzym:     { n: 'Olbrzym', ik: '⛰️' },
  szybki:      { n: 'Szybki', ik: '💨' },
  tarczownik:  { n: 'Tarczownik', ik: '🛡️' },
  wampir:      { n: 'Wampir', ik: '🧛' },
  ognisty:     { n: 'Ognisty', ik: '🔥' },
  lodowy:      { n: 'Lodowy', ik: '❄️' },
  wybuchowy:   { n: 'Wybuchowy', ik: '💥' },
  skoczek:     { n: 'Skoczek', ik: '🌀' },
  regenerujacy:{ n: 'Regenerujący', ik: '💚' },
  przywolywacz:{ n: 'Przywoływacz', ik: '🐀' },
  lustrzany:   { n: 'Lustrzany', ik: '🪞' },
  wsciekly:    { n: 'Wściekły', ik: '💢' },
};
const KLUCZE_AFIKSOW = Object.keys(AFIKSY);

const BOSSOWIE = [
  { id: 'wladca', n: 'Władca Labiryntu', ik: '😈', kolor: '#c0392b', hp: 1300, atak: 22, panc: 40, odp: 30, ms: 92, r: 34 },
  { id: 'wiedzma', n: 'Wiedźma Otchłani', ik: '🧝', kolor: '#8a5ac4', hp: 1550, atak: 17, panc: 30, odp: 60, ms: 60, r: 34 },
  { id: 'tytan', n: 'Tytan Popiołów', ik: '👺', kolor: '#e6743c', hp: 2100, atak: 25, panc: 70, odp: 40, ms: 64, r: 40 },
  { id: 'krolowa', n: 'Królowa Pająków', ik: '🕷️', kolor: '#6a3a8a', hp: 1900, atak: 21, panc: 40, odp: 40, ms: 84, r: 36 },
  { id: 'lisz', n: 'Lisz', ik: '☠️', kolor: '#7ec4e8', hp: 2200, atak: 21, panc: 30, odp: 80, ms: 62, r: 34 },
];

// ---------- skalowanie z falą i trudnością ----------
// Na początku wrogowie rosną umiarkowanie, od 8. fali coraz szybciej,
// a od 18. i 28. fali — wykładniczo (każda kolejna fala wyraźnie mocniejsza).
function skalaFali(nr) {
  const T = TRUDNOSCI[run.trudnosc];
  const x = Math.max(0, (nr - 1) * T.tempo);
  const p8 = Math.max(0, nr - 8), p18 = Math.max(0, nr - 18), p28 = Math.max(0, nr - 28);
  return {
    hp: 2.0 * (1 + 0.32 * x + 0.04 * x * x) * Math.pow(1.09, p8) * Math.pow(1.09, p18) * Math.pow(1.08, p28) * T.hp,
    atak: 1.35 * (1 + 0.14 * x + 0.011 * x * x) * Math.pow(1.06, p8) * Math.pow(1.06, p18) * Math.pow(1.05, p28) * T.atak,
    panc: 1 + 0.05 * x,
    ms: Math.min(1.22, 1 + 0.007 * Math.max(0, nr - 1)) * T.ms,   // prędkość rośnie tak samo na każdej trudności (tylko mnożnik T.ms)
    zl: 1 + 0.04 * x,
    xp: 1 + 0.07 * x,
  };
}

let licznikWrogow = 0;
function stworzWroga(typ, x, y, opcje) {
  opcje = opcje || {};
  const t = TYPY_WROGOW[typ], S = skalaFali(fala.nr);
  const w = {
    id: ++licznikWrogow, typ: typ, n: t.n, ik: t.ik, obraz: t.obraz, x: x, y: y, r: t.r, kolor: t.kolor,
    hp: t.hp * S.hp, hpMax: t.hp * S.hp, atak: t.atak * S.atak, panc: t.panc * S.panc, odp: t.odp * S.panc,
    ms: t.ms * S.ms * losowo(0.92, 1.08), xp: t.xp * S.xp, zl: t.zl * S.zl * 0.85,
    dyst: t.dyst || 0, typObr: t.typObr || 'fiz', zach: t.zach || 'goniacy',
    cd: losowo(0.3, 1.2), kierKraz: Math.random() < 0.5 ? 1 : -1, cdBoczny: losowo(0.6, 1.6), cdGazu: losowo(0.4, 1.2),
    spow: 0, spowCzas: 0, ogl: 0, ogien: null, krew: null, krusz: 0, naznaczony: 0, zauroczony: 0, trafiony: 0,
    kbx: 0, kby: 0, afiksy: [], elita: false, boss: false, martwy: false, wiek: 0,
  };
  if (opcje.elita) zrobElite(w, opcje.afiksy);
  if (TRUDNOSCI[run.trudnosc].msWrogow) w.ms *= TRUDNOSCI[run.trudnosc].msWrogow;
  if (fala.mnHpWrogow) { w.hp *= fala.mnHpWrogow; w.hpMax = w.hp; }
  if (liczbaGraczy() > 1) { w.hp *= mnDruzyny(); w.hpMax = w.hp; }
  if (fala.mnMsWrogow) w.ms *= fala.mnMsWrogow;
  return w;
}

function zrobElite(w, ile) {
  w.elita = true;
  w.hp *= 3.2; w.hpMax = w.hp; w.atak *= 1.45; w.panc *= 1.3; w.odp *= 1.3; w.r *= 1.18; w.xp *= 4; w.zl *= 6;
  if (ile === undefined) { const nr = fala.nr; ile = (nr < 10 ? 1 : nr < 20 ? 2 : 3) + (TRUDNOSCI[run.trudnosc].afiksy || 0); }
  const pula = tasuj(KLUCZE_AFIKSOW.slice());
  for (let i = 0; i < ile && i < pula.length; i++) dodajAfiks(w, pula[i]);
}
function dodajAfiks(w, a) {
  w.afiksy.push(a);
  if (a === 'olbrzym') { w.hp *= 1.8; w.hpMax = w.hp; w.r *= 1.25; w.ciezki = true; }
  if (a === 'szybki') { w.ms *= 1.4; w.mnCd = 0.7; }
  if (a === 'tarczownik') { w.tarczaMax = w.hpMax * 0.4; w.tarcza = w.tarczaMax; w.odTrafienia = 0; }
  if (a === 'przywolywacz') w.cdPrzyw = 4;
  if (a === 'skoczek') w.cdSkoku = 3;
}

function stworzBossa(idx, x, y) {
  const B = BOSSOWIE[idx % BOSSOWIE.length], S = skalaFali(fala.nr), T = TRUDNOSCI[run.trudnosc];
  const cykl = Math.floor(idx / BOSSOWIE.length);
  const w = stworzWroga('szczur', x, y);
  Object.assign(w, {
    typ: 'boss', bossId: B.id, n: B.n + (cykl ? ' ' + 'I'.repeat(cykl + 1) : ''), ik: B.ik, kolor: B.kolor, r: B.r, obraz: null,
    hp: B.hp * S.hp * 0.85 * (T.hpBoss || 1), atak: B.atak * S.atak * (fala.nr <= 10 ? 0.7 : 0.8), panc: B.panc * S.panc, odp: B.odp * S.panc, ms: B.ms * Math.min(1.25, S.ms),
    xp: 60 * S.xp, zl: 60 * S.zl, boss: true, elita: false, ciezki: true, dyst: 0, zach: 'boss', typObr: 'fiz',
    t1: 2.5, t2: 4.5, t3: 7, t4: 9, faza: 0, mnCdBossa: Math.pow(0.85, cykl), wzmocniony: cykl,
  });
  if (liczbaGraczy() > 1) w.hp *= 1 + 0.85 * (liczbaGraczy() - 1);
  w.hpMax = w.hp;
  return w;
}

// ---------- AKTUALIZACJA ----------
function aktualizujWrogow(dt) {
  const z0 = gracz;
  if (!zywiGracze().length) return;
  for (let i = 0; i < wrogowie.length; i++) {
    const w = wrogowie[i];
    if (w.martwy) continue;
    // cel: najbliższa żywa postać (co pół sekundy, żeby nie skakali między graczami)
    w.tCelu = (w.tCelu || 0) - dt;
    if (!w.cel || w.cel.powalony || w.cel.niewidzialny > 0 || w.tCelu <= 0 || gracze.indexOf(w.cel) < 0) { w.cel = najblizszyGracz(w.x, w.y); w.tCelu = 0.5; }
    w.wiek += dt;
    if (w.trafiony > 0) w.trafiony -= dt;
    if (w.naznaczony > 0) w.naznaczony -= dt;
    if (w.rany > 0) w.rany -= dt;
    if (w.wzm > 0) { w.wzm -= dt; if (w.wzm <= 0) w.atak /= 1.3; }
    if (w._zaT > 0) { w._zaT -= dt; if (w._zaT <= 0) w.zamarzniecieAtaku = 0; }
    // efekty rozłożone w czasie
    tikEfektowWroga(w, dt); if (w.martwy) continue;
    // nikogo nie widać (np. wszyscy niewidzialni): wróg się rozgląda i nie atakuje
    if (!w.cel) { w.zamach = 0; if (w.ogl > 0) w.ogl -= dt; if (w.spowCzas > 0) { w.spowCzas -= dt; if (w.spowCzas <= 0) w.spow = 0; } ogranicz(w); continue; }
    // afiksy pasywne
    kontekst(w.cel);
    if (w.afiksy.length) aktualizujAfiksy(w, dt);
    if (w.martwy) continue;
    if (w.spowCzas > 0) { w.spowCzas -= dt; if (w.spowCzas <= 0) w.spow = 0; }
    // odrzut
    if (w.kbx || w.kby) { w.x += w.kbx * dt; w.y += w.kby * dt; w.kbx *= Math.pow(0.002, dt); w.kby *= Math.pow(0.002, dt); if (Math.abs(w.kbx) + Math.abs(w.kby) < 5) { w.kbx = 0; w.kby = 0; } }
    if (w.ogl > 0) { w.ogl -= dt; w.zamach = 0; ogranicz(w); continue; }
    if (w.zauroczony > 0) { w.zauroczony -= dt; if (w.wlasciciel && gracze.indexOf(w.wlasciciel) >= 0) kontekst(w.wlasciciel); aiSojusznika(w, dt); ogranicz(w); continue; }
    // wabik (Strach na Wróble): idą do niego zamiast do gracza
    if (w.tWabik > 0) { w.tWabik -= dt; if (w.wabik && stwory.indexOf(w.wabik) >= 0) { const d = Math.hypot(w.wabik.x - w.x, w.wabik.y - w.y); if (d > 18) { w.x += (w.wabik.x - w.x) / d * w.ms * dt; w.y += (w.wabik.y - w.y) / d * w.ms * dt; } ogranicz(w); continue; } }
    kontekst(w.cel);
    const msMn = (1 - Math.min(0.85, w.spow)) * (w.afiksy.indexOf('wsciekly') >= 0 && w.hp < w.hpMax * 0.5 ? 1.35 : 1);
    if (w.boss) aiBossa(w, dt, msMn); else aiWroga(w, dt, msMn);
    ogranicz(w);
  }
  kontekst(z0);
  // rozpychanie - wrogowie nie wchodzą na siebie
  rozepchnij();
}

function ogranicz(w) { w.x = ogr(w.x, POD_MIN, POD_MAX); w.y = ogr(w.y, POD_MIN, POD_MAX); }

function rozepchnij() {
  const n = wrogowie.length; if (n < 2) return;
  const siatka = new Map(), K = 48;
  for (let i = 0; i < n; i++) { const w = wrogowie[i]; if (w.martwy || w.duch) continue; const k = ((w.x / K) | 0) * 1000 + ((w.y / K) | 0); let l = siatka.get(k); if (!l) siatka.set(k, l = []); l.push(w); }
  for (let i = 0; i < n; i++) {
    const a = wrogowie[i]; if (a.martwy || a.duch) continue;
    const cx = (a.x / K) | 0, cy = (a.y / K) | 0;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const l = siatka.get((cx + dx) * 1000 + (cy + dy)); if (!l) continue;
      for (let j = 0; j < l.length; j++) { const b = l[j]; if (b === a) continue;
        const ddx = a.x - b.x, ddy = a.y - b.y, d = Math.hypot(ddx, ddy), min = (a.r + b.r) * 0.82;
        if (d < min && d > 0.01) { const p = (min - d) * 0.25 / d; const wa = a.boss ? 0.1 : 1, wb = b.boss ? 0.1 : 1; a.x += ddx * p * wa; a.y += ddy * p * wa; b.x -= ddx * p * wb; b.y -= ddy * p * wb; } }
    }
  }
}

function strzalWroga(w, k, predkosc, obr, opcje) {
  opcje = opcje || {};
  pociskiWrogow.push(Object.assign({ x: w.x, y: w.y, vx: Math.cos(k) * predkosc, vy: Math.sin(k) * predkosc, obr: obr, typ: w.typObr || 'fiz', zycie: 2.4, kolor: '#c46ce8', wrog: w, r: 5, kto: w.n }, opcje));
}

// ZAMACH: wróg wręcz najpierw się zamachuje (czerwony łuk rośnie), a cios pada dopiero po chwili.
// Kto w tym czasie odskoczy albo przebiegnie obok, nie oberwie; ogłuszenie przerywa zamach.
const ZASIEG_ZAMACHU = 10;                       // o tyle dalej sięga cios niż odległość, z której zaczyna zamach
function czasZamachu(w) { return (w.boss ? 0.46 : w.elita ? 0.31 : 0.36) * (TRUDNOSCI[run.trudnosc].zamach || 1); }
function zacznijZamach(w, kat) { w.zamach = w.zamachMax = czasZamachu(w); w.zamKat = kat; }
function wyprowadzCios(w, dAtak, mn) {
  const T = TYPY_WROGOW[w.typ] || {};
  const zas = w.r + gracz.r * rozmiarGracza() + (w.boss ? 8 : 6) - (gracz.zdalny ? 5 : 0) + ZASIEG_ZAMACHU;
  const kat = Math.atan2(gracz.y - w.y, gracz.x - w.x);
  ciecia.push({ x: w.x, y: w.y, kat: kat, luk: 1.7, r: w.r + 22, czas: 0.16, max: 0.16, kolor: '#ff6a5a' });
  if (dAtak > zas) return false;                 // chybił - gracz zdążył uskoczyć
  const zad = zranGracza(w.atak * (mn || 1), w.typObr || 'fiz', { wrog: w, wrecz: true });
  if (T.wysysa && zad > 0) { w.hp = Math.min(w.hpMax, w.hp + zad * 3); czastkiLeczenia(w.x, w.y); }
  if (w.afiksy.indexOf('lodowy') >= 0) spowolnijGracza(0.35, 1.5);
  return true;
}
function odlegloscDoCiosu(w, d) {
  if (!gracz.zdalny || gracz.netX === undefined) return d;
  return Math.max(d, Math.hypot(gracz.netX - w.x, gracz.netY - w.y));
}
function aiWroga(w, dt, msMn) {
  const dx = gracz.x - w.x, dy = gracz.y - w.y, d = Math.hypot(dx, dy) || 1, kg = Math.atan2(dy, dx);
  // gracz online: cios liczy się dopiero, gdy wróg sięga go i w ostatniej zgłoszonej pozycji, i w przewidywanej
  // (gdy gracz nagle zawróci, przewidywanie nie dorzuci mu ciosu "z powietrza"); do tego odrobina luzu
  const luz = gracz.zdalny ? 5 : 0, dAtak = odlegloscDoCiosu(w, d);
  const T = TYPY_WROGOW[w.typ] || {};
  w.kier = kg;
  // trwa zamach: stoi w miejscu, a na końcu wyprowadza cios (trafia tylko, jeśli gracz nadal jest blisko)
  if (w.zamach > 0) { w.zamach -= dt; if (w.zamach <= 0) { w.zamach = 0; wyprowadzCios(w, dAtak); } return; }
  // Upiorny rycerz: namierza (stoi 0,7 s) i szarżuje
  if (T.szarzuje) {
    if (w.dashT > 0) { w.dashT -= dt; w.x += w.dVX * dt; w.y += w.dVY * dt; if (!w.trafilDash && dAtak < w.r + gracz.r * rozmiarGracza() + 6 - luz) { w.trafilDash = true; zranGracza(w.atak * 1.6, 'fiz', { wrog: w, wrecz: true }); } return; }
    if (w.dashZa > 0) { w.dashZa -= dt; if (w.dashZa <= 0) { const v = 470; w.dVX = Math.cos(kg) * v; w.dVY = Math.sin(kg) * v; w.dashT = Math.min(0.9, (d + 80) / v); w.trafilDash = false; } return; }
    w.cdDash = (w.cdDash === undefined ? 3 : w.cdDash) - dt;
    if (w.cdDash <= 0 && d < 330 && d > 80) { w.cdDash = 5.5; w.dashZa = 0.7; tekstSwiat(w.x, w.y - w.r - 12, '❗', '#ff6a5a', 0.7, 16); return; }
  }
  // Kolczak: kolce we wszystkie strony
  if (T.kolce) { w.cdKolcow = (w.cdKolcow === undefined ? 2 : w.cdKolcow) - dt; if (w.cdKolcow <= 0 && d < 320) { w.cdKolcow = 2.8; for (let s = 0; s < 8; s++) strzalWroga(w, s * Math.PI / 4 + (w.wiek % 1), 190, w.atak * 0.8, { kolor: '#d8c8a0', zycie: 1.5, ksztalt: 'belt' }); DZ.wrogStrzal(w.typ); } }
  // Kultysta: wzmacnia wrogów obok
  if (T.wzmacnia) { w.cdWzm = (w.cdWzm === undefined ? 1.5 : w.cdWzm) - dt; if (w.cdWzm <= 0) { w.cdWzm = 3.5; let n = 0;
    wrogowie.forEach(o => { if (o === w || o.martwy || o.boss || o.zauroczony > 0 || Math.hypot(o.x - w.x, o.y - w.y) > 180) return; if (!(o.wzm > 0)) o.atak *= 1.3; o.wzm = 3.6; n++; });
    if (n) fale.push({ x: w.x, y: w.y, czas: 0.5, max: 0.5, r: 180, kolor: '#c06ae0' }); } }
  let rx = 0, ry = 0;
  const zasieg = w.dyst || (w.r + gracz.r * rozmiarGracza() + 6 - luz);
  if (w.zach === 'okrazajacy') {
    const DOBRY = w.leczy ? 180 : 150;
    if (d > DOBRY + 40) { rx = Math.cos(kg); ry = Math.sin(kg); }
    else if (d < DOBRY - 40) { rx = -Math.cos(kg); ry = -Math.sin(kg); }
    else { rx = -Math.sin(kg) * w.kierKraz; ry = Math.cos(kg) * w.kierKraz; }
  } else if (w.zach === 'uciekajacy') {
    if (d < 210) {
      const od = kg + Math.PI; let k = od;
      // od ścian areny odbija się w bok, żeby nie utknąć w rogu
      const nx = w.x + Math.cos(od) * 60, ny = w.y + Math.sin(od) * 60;
      if (nx < POD_MIN + 20 || nx > POD_MAX - 20 || ny < POD_MIN + 20 || ny > POD_MAX - 20) k = od + w.kierKraz * Math.PI / 2;
      rx = Math.cos(k) * (d < 80 ? 1.4 : 1); ry = Math.sin(k) * (d < 80 ? 1.4 : 1);
    } else { rx = -Math.sin(kg) * w.kierKraz; ry = Math.cos(kg) * w.kierKraz; }
    w.cdGazu -= dt;
    if (w.zloty) { w.znika -= dt; if (w.znika <= 0) { w.martwy = true; w.bezLupu = true; rozbryzg(w.x, w.y, '#ffd24a', 14); tekstSwiat(w.x, w.y - 20, 'uciekł!', '#ffd24a'); } }
    else if (w.cdGazu <= 0) { w.cdGazu = 0.6; kaluze.push({ x: w.x, y: w.y, r: 28, czas: 5, max: 5, tyk: 0, obr: Math.max(2, w.atak * 0.45), typ: 'mag', rodzaj: 'gaz', wrog: w }); DZ.syk(); }
  } else if (w.zach === 'szarzaBoki') {
    if (d > zasieg * 0.9) { rx = Math.cos(kg); ry = Math.sin(kg); }
    w.cdBoczny -= dt;
    if (w.cdBoczny <= 0 && d < 260) {
      w.cdBoczny = 1.9;
      [Math.PI / 2, -Math.PI / 2].forEach(o => strzalWroga(w, kg + o, 195, w.atak * 0.7, { kolor: '#e8a05a', zycie: 2.2 }));
      DZ.wrogStrzal(w.typ);
    }
  } else if (d > zasieg * 0.9) { rx = Math.cos(kg); ry = Math.sin(kg); }

  const dl = Math.hypot(rx, ry);
  if (dl > 0.001) { w.x += rx / dl * Math.min(1.45, dl) * w.ms * msMn * dt; w.y += ry / dl * Math.min(1.45, dl) * w.ms * msMn * dt; }

  // Szaman: leczy rannych sojuszników
  if (w.leczy) {
    w.cdLecz = (w.cdLecz || 2) - dt;
    if (w.cdLecz <= 0) { w.cdLecz = 2.4;
      wrogowie.forEach(o => { if (!o.martwy && o !== w && !o.zauroczony && Math.hypot(o.x - w.x, o.y - w.y) < 170 && o.hp < o.hpMax) {
        o.hp = Math.min(o.hpMax, o.hp + o.hpMax * 0.08 * (o.rany > 0 ? 0.4 : 1)); czastkiLeczenia(o.x, o.y); } });
      fale.push({ x: w.x, y: w.y, czas: 0.4, max: 0.4, r: 170, kolor: '#5ae0a0' });
    }
  }
  // Bombiarz: dopada i zostawia bombę z lontem
  if (TYPY_WROGOW[w.typ] && TYPY_WROGOW[w.typ].wybuchowy && d < w.r + gracz.r + 14) {
    postawBombe(w.x, w.y, w.atak, 0.75); w.martwy = true; w.bezLupu = true; ton(880, 0.08, 'square', 0.07); return;
  }
  const mnAt = (w.mnCd || 1) * (1 + (w.zamarzniecieAtaku || 0));
  w.cd -= dt / mnAt;
  if (w.zach === 'uciekajacy' || w.cd > 0) return;
  if ((w.dyst ? d : dAtak) > zasieg) return;
  w.cd = 1.25;
  if (w.dyst) {
    if (TYPY_WROGOW[w.typ].czary) {
      w.licz = (w.licz || 0) + 1;
      if (w.licz % 3 === 0) {
        const c = (w.licz / 3) % 3;
        if (c === 1) { [-0.3, 0, 0.3].forEach(o => strzalWroga(w, kg + o, 210, w.atak * 0.8, { kolor: '#e0458a', zycie: 1.8 })); tekstSwiat(w.x, w.y - w.r - 10, '✨ Salwa!', '#ff9fd0'); }
        else if (c === 2) postawSciane(w, kg);
        else rzucWir(w);
        DZ.czar(); return;
      }
    }
    if (w.leczy) { strzalWroga(w, kg, 200, w.atak, { kolor: '#5ae0a0' }); DZ.wrogStrzal(w.typ); return; }
    if (T.artyleria) { w.cd = 2.8; uderzeniaBossa.push({ x: gracz.x + losowo(-25, 25), y: gracz.y + losowo(-25, 25), r: 62, czas: 0, zapowiedz: 1.3, obr: w.atak * 1.3, typ: 'fiz', zadane: false, kto: w.n }); DZ.wrogStrzal(w.typ); return; }
    const belt = w.typ === 'kusznik' || w.typ === 'lucznik';
    strzalWroga(w, kg, belt ? 320 : 230, w.atak, { kolor: belt ? '#c9a36b' : '#c46ce8', ksztalt: belt ? 'belt' : null, zycie: 1.8 });
    DZ.wrogStrzal(w.typ);
  } else { zacznijZamach(w, kg); w.cd = Math.max(0.3, w.cd - w.zamach); }    // rytm ciosów jak dawniej (zamach liczy się do odnowienia)
}

function aktualizujAfiksy(w, dt) {
  const a = w.afiksy;
  if (a.indexOf('regenerujacy') >= 0 && w.hp < w.hpMax) w.hp = Math.min(w.hpMax, w.hp + w.hpMax * 0.025 * dt * (w.rany > 0 ? 0.4 : 1));
  if (a.indexOf('tarczownik') >= 0) { w.odTrafienia = (w.odTrafienia || 0) + dt; if (w.odTrafienia > 4 && w.tarcza < w.tarczaMax) w.tarcza = Math.min(w.tarczaMax, w.tarcza + w.tarczaMax * 0.25 * dt); }
  if (a.indexOf('ognisty') >= 0) { w.cdOgnia = (w.cdOgnia || 0) - dt; if (w.cdOgnia <= 0) { w.cdOgnia = 0.7; kaluze.push({ x: w.x, y: w.y, r: 24, czas: 3, max: 3, tyk: 0, obr: w.atak * 0.35, typ: 'mag', rodzaj: 'ogien', wrog: w }); } }
  if (a.indexOf('przywolywacz') >= 0) { w.cdPrzyw -= dt; if (w.cdPrzyw <= 0) { w.cdPrzyw = 7; if (wrogowie.length < limitWrogow()) for (let i = 0; i < 2; i++) { const s = stworzWroga('szczur', w.x + losowo(-30, 30), w.y + losowo(-30, 30)); s.bezLupu = true; s.xp *= 0.3; wrogowie.push(s); } } }
  if (a.indexOf('skoczek') >= 0 && w.ogl <= 0) { w.cdSkoku -= dt; if (w.cdSkoku <= 0) { w.cdSkoku = 5; const k = Math.random() * Math.PI * 2; rozbryzg(w.x, w.y, '#9fd8ff', 10); w.x = ogr(gracz.x + Math.cos(k) * 120, POD_MIN, POD_MAX); w.y = ogr(gracz.y + Math.sin(k) * 120, POD_MIN, POD_MAX); rozbryzg(w.x, w.y, '#9fd8ff', 10); tonSlizg(700, 1500, 0.18, 'sine', 0.05); } }
}

// Wróg przejęty przez Lalkarza / wskrzeszony: walczy po stronie gracza
function aiSojusznika(w, dt) {
  let cel = null, najD = 420;
  for (const o of wrogowie) { if (o === w || o.martwy || o.zauroczony > 0) continue; const d = Math.hypot(o.x - w.x, o.y - w.y); if (d < najD) { najD = d; cel = o; } }
  w.cd -= dt;
  if (!cel) { const d = Math.hypot(gracz.x - w.x, gracz.y - w.y); if (d > 60) { w.x += (gracz.x - w.x) / d * w.ms * dt; w.y += (gracz.y - w.y) / d * w.ms * dt; } }
  else {
    if (najD > w.r + cel.r + 4) { w.x += (cel.x - w.x) / najD * w.ms * 1.1 * dt; w.y += (cel.y - w.y) / najD * w.ms * 1.1 * dt; }
    else if (w.cd <= 0) { w.cd = 0.9; zadaj(cel, (w.atak * 3 + 0.3 * D.ap) * (1 + (FLAGI.mnSojusznikow || 0)), 'mag', { zr: w.sojusznik ? 'Sojusznicy' : 'Lalkarz' }); rozbryzg(cel.x, cel.y, '#ff9ae0', 5); }
  }
  if (w.zauroczony <= 0 && w.sojusznik) { w.martwy = true; w.bezLupu = true; rozbryzg(w.x, w.y, '#9a9aaa', 10); }
}

// ---------- CZARY ZWYKŁYCH WROGÓW (z dawnego labiryntu) ----------
function postawSciane(w, k) {
  const cx = w.x + Math.cos(k) * 62, cy = w.y + Math.sin(k) * 62, px = -Math.sin(k) * 75, py = Math.cos(k) * 75;
  scianyMagiczne.push({ x1: cx - px, y1: cy - py, x2: cx + px, y2: cy + py, grubosc: 14, czas: 4, max: 4 });
  tekstSwiat(w.x, w.y - w.r - 10, '🔮 Ściana!', '#9fd8ff');
}
function rzucWir(w) {
  wiry.push({ x: gracz.x, y: gracz.y, r: 95, czas: 4.2, max: 4.2, rozruch: 0.7, faza: 0, tyk: 0, atak: w.atak });
  tekstSwiat(w.x, w.y - w.r - 10, '🌀 Wir!', '#c9a8ff');
}
function postawBombe(x, y, atak, lont) { bomby.push({ x: x, y: y, lont: lont || 0.8, max: lont || 0.8, atak: atak, r: 120 }); }
function wybuchBomby(b) {
  DZ.wybuch(); rozbryzg(b.x, b.y, '#ffd24a', 30); rozbryzg(b.x, b.y, '#e6743c', 24);
  fale.push({ x: b.x, y: b.y, czas: 0.45, max: 0.45, r: b.r, kolor: '#ffd24a' });
  dlaKazdego(g => { if (!g.powalony && g._D && Math.hypot(g.x - b.x, g.y - b.y) <= b.r) zranGracza(b.atak * 1.4 + D.hpMax * 0.05, 'fiz', { wybuch: true, bezUniku: true, kto: 'Bomba' }); });
  wrogowie.forEach(o => { if (!o.martwy && !o.boss && Math.hypot(o.x - b.x, o.y - b.y) <= b.r) { o.hp -= b.atak * 2; o.trafiony = 0.12; if (o.hp <= 0) zabij(o, { zr: 'Bomba' }); } });
}

// ---------- BOSSOWIE ----------
function aiBossa(w, dt, msMn) {
  const dx = gracz.x - w.x, dy = gracz.y - w.y, d = Math.hypot(dx, dy) || 1, kg = Math.atan2(dy, dx);
  const mc = w.mnCdBossa || 1, proc = w.hp / w.hpMax, luz = gracz.zdalny ? 5 : 0, dAtak = odlegloscDoCiosu(w, d);
  w.t1 -= dt; w.t2 -= dt; w.t3 -= dt; w.t4 -= dt;
  // szarża w toku
  if (w.szarza > 0) {
    w.szarza -= dt; w.x += w.szVX * dt; w.y += w.szVY * dt;
    w.cd -= dt; if (dAtak < w.r + gracz.r + 8 - luz && w.cd <= 0) { w.cd = 0.6; zranGracza(w.atak * 1.4, 'fiz', { wrog: w, wrecz: true }); }
    return;
  }
  if (w.przygotowanie > 0) { w.przygotowanie -= dt; if (w.przygotowanie <= 0) { w.szarza = w.dlSzarzy || 0.85; const k = Math.atan2(gracz.y - w.y, gracz.x - w.x); w.szVX = Math.cos(k) * (w.vSzarzy || 520); w.szVY = Math.sin(k) * (w.vSzarzy || 520); DZ.boss(); } return; }
  let rx = 0, ry = 0;
  switch (w.bossId) {
    case 'wladca': {
      rx = Math.cos(kg); ry = Math.sin(kg);
      if (w.t1 <= 0 && d < 160) { w.t1 = 4.2 * mc; uderzeniaBossa.push({ x: w.x, y: w.y, r: 125, czas: 0, zapowiedz: 0.8, obr: w.atak * 0.9, typ: 'fiz', zadane: false }); tonSlizg(320, 90, 0.7, 'sawtooth', 0.07); }
      if (w.t2 <= 0 && d > 110) { w.t2 = 5 * mc; w.przygotowanie = 0.55; w.dlSzarzy = 0.85; w.vSzarzy = 470; tekstSwiat(w.x, w.y - w.r - 14, '⚠️ Szarża!', '#ffd24a'); return; }
      if (!w.wezwal && proc < 0.5) { w.wezwal = true; w.ms *= 1.2; for (let i = 0; i < 6; i++) { const s = stworzWroga('szczur', w.x + losowo(-90, 90), w.y + losowo(-90, 90)); s.bezLupu = true; wrogowie.push(s); } baner('😈 Władca wpada w szał!', 'Przywołuje szczury i przyspiesza'); }
      break;
    }
    case 'wiedzma': {
      if (d > 260) { rx = Math.cos(kg); ry = Math.sin(kg); } else if (d < 180) { rx = -Math.cos(kg); ry = -Math.sin(kg); } else { rx = -Math.sin(kg); ry = Math.cos(kg); }
      if (w.t1 <= 0) { w.t1 = 2.2 * mc; for (let s = 0; s < 11; s++) strzalWroga(w, kg + (s - 5) * 0.22, 225, w.atak * 0.9, { typ: 'mag', kolor: '#e86ca0', zycie: 3 }); DZ.wrogStrzal('boss'); }
      if (w.t3 <= 0) { w.t3 = 11 * mc; if (wrogowie.length < limitWrogow()) for (let p = 0; p < 3; p++) { const s = stworzWroga(Math.random() < 0.5 ? 'ogr' : 'mag', w.x + losowo(-80, 80), w.y + losowo(-80, 80)); s.bezLupu = true; s.hp *= 0.6; s.hpMax = s.hp; wrogowie.push(s); } tekstSwiat(w.x, w.y - w.r - 14, '💀 Przywołanie!', '#e86ca0'); }
      if (w.t2 <= 0 && w.hp < (w.hpTele || w.hpMax) - w.hpMax * 0.12) { w.t2 = 6 * mc; w.hpTele = w.hp; rozbryzg(w.x, w.y, '#c9a8ff', 16); const k = Math.random() * Math.PI * 2; w.x = ogr(gracz.x + Math.cos(k) * 240, POD_MIN, POD_MAX); w.y = ogr(gracz.y + Math.sin(k) * 240, POD_MIN, POD_MAX); rozbryzg(w.x, w.y, '#c9a8ff', 16); tonSlizg(700, 1600, 0.2, 'sine', 0.06); }
      break;
    }
    case 'tytan': {
      rx = Math.cos(kg); ry = Math.sin(kg);
      if (w.faza < 1 && proc <= 0.75) { w.faza = 1; w.poswiata = '#a855f7'; baner('🟣 Tytan wpada w furię', 'Więcej pocisków'); }
      if (w.faza < 2 && proc <= 0.5) { w.faza = 2; w.poswiata = '#e6543c'; w.pole = true; baner('🔴 Pole spowolnienia!', 'Nie stój blisko Tytana'); }
      if (w.faza < 3 && proc <= 0.25) { w.faza = 3; w.poswiata = '#ffd24a'; w.ms *= 1.3; baner('💛 Ostatnia faza', 'Tytan zostawia ogień'); }
      if (w.pole && d < 190) spowolnijGracza(0.4, 0.2);
      if (w.faza >= 3) { w.cdOgnia = (w.cdOgnia || 0) - dt; if (w.cdOgnia <= 0) { w.cdOgnia = 0.4; kaluze.push({ x: w.x, y: w.y, r: 34, czas: 4, max: 4, tyk: 0, obr: w.atak * 0.3, typ: 'mag', rodzaj: 'ogien', wrog: w }); } }
      if (w.t1 <= 0) { w.t1 = 2.3 * mc / (1 + w.faza * 0.35); const ile = 9 + w.faza * 3; for (let s = 0; s < ile; s++) strzalWroga(w, kg + (s - (ile - 1) / 2) * 0.24, 235, w.atak * 0.7, { kolor: w.poswiata || '#e86ca0', zycie: 3 }); DZ.wrogStrzal('boss'); }
      if (w.t2 <= 0 && d > 90) { w.t2 = 7.5 * mc; w.przygotowanie = 1.0; w.dlSzarzy = 1.0; w.vSzarzy = 600; tekstSwiat(w.x, w.y - w.r - 14, '⚠️ Szarża!', '#ffd24a'); return; }
      break;
    }
    case 'krolowa': {
      if (d > 140) { rx = Math.cos(kg); ry = Math.sin(kg); } else { rx = -Math.sin(kg); ry = Math.cos(kg); }
      if (w.t1 <= 0) { w.t1 = 3 * mc; [-0.35, 0, 0.35].forEach(o => strzalWroga(w, kg + o, 250, w.atak * 0.6, { kolor: '#e8e8f0', zycie: 2.5, siec: true, r: 7 })); DZ.wrogStrzal('boss'); }
      if (w.t2 <= 0) { w.t2 = 4.5 * mc; const cx = gracz.x, cy = gracz.y; w.skok = { x: cx, y: cy, czas: 0.95, sx: w.x, sy: w.y };
        uderzeniaBossa.push({ x: cx, y: cy, r: 95, czas: 0, zapowiedz: 0.95, obr: w.atak * 1.2, typ: 'fiz', zadane: false }); }
      if (w.t3 <= 0) { w.t3 = 7 * mc; if (wrogowie.length < limitWrogow()) for (let p = 0; p < 4; p++) { const s = stworzWroga('pajak', w.x + losowo(-60, 60), w.y + losowo(-60, 60)); s.bezLupu = true; wrogowie.push(s); } }
      if (w.skok) { w.skok.czas -= dt; const t = 1 - Math.max(0, w.skok.czas) / 0.95; w.x = w.skok.sx + (w.skok.x - w.skok.sx) * t; w.y = w.skok.sy + (w.skok.y - w.skok.sy) * t; w.wysokosc = Math.sin(t * Math.PI) * 40; if (w.skok.czas <= 0) { w.skok = null; w.wysokosc = 0; } return; }
      break;
    }
    case 'lisz': {
      if (d > 230) { rx = Math.cos(kg); ry = Math.sin(kg); } else if (d < 150) { rx = -Math.cos(kg); ry = -Math.sin(kg); } else { rx = -Math.sin(kg); ry = Math.cos(kg); }
      if (w.t1 <= 0) { w.t1 = 3 * mc; w.obrotPierscienia = (w.obrotPierscienia || 0) + 0.2; for (let s = 0; s < 16; s++) strzalWroga(w, w.obrotPierscienia + s * Math.PI / 8, 190, w.atak * 0.7, { typ: 'mag', kolor: '#bfe8ff', zycie: 3.2, ksztalt: 'kosc' }); DZ.wrogStrzal('boss'); }
      if (w.t2 <= 0) { w.t2 = 6 * mc; uderzeniaBossa.push({ x: w.x, y: w.y, r: 160, czas: 0, zapowiedz: 1.0, obr: w.atak * 1.0, typ: 'mag', zadane: false, mroz: true, sledz: w }); }
      if (w.t3 <= 0) { w.t3 = 10 * mc; if (wrogowie.length < limitWrogow()) for (let p = 0; p < 4; p++) { const s = stworzWroga('szkielet', w.x + losowo(-100, 100), w.y + losowo(-100, 100)); s.bezLupu = true; wrogowie.push(s); } tekstSwiat(w.x, w.y - w.r - 14, '💀 Powstańcie!', '#bfe8ff'); }
      if (w.t4 <= 0) { w.t4 = 8 * mc; rozbryzg(w.x, w.y, '#bfe8ff', 14); const k = Math.random() * Math.PI * 2; w.x = ogr(gracz.x + Math.cos(k) * 210, POD_MIN, POD_MAX); w.y = ogr(gracz.y + Math.sin(k) * 210, POD_MIN, POD_MAX); rozbryzg(w.x, w.y, '#bfe8ff', 14); }
      break;
    }
  }
  const dl = Math.hypot(rx, ry), mnZam = w.zamach > 0 ? 0.2 : 1;
  if (dl > 0.001) { w.x += rx / dl * w.ms * msMn * mnZam * dt; w.y += ry / dl * w.ms * msMn * mnZam * dt; }
  w.cd -= dt;
  if (w.zamach > 0) { w.zamach -= dt; if (w.zamach <= 0) { w.zamach = 0; wyprowadzCios(w, odlegloscDoCiosu(w, Math.hypot(gracz.x - w.x, gracz.y - w.y))); } }
  else if (dAtak < w.r + gracz.r * rozmiarGracza() + 8 - luz && w.cd <= 0) { w.cd = 1.05; zacznijZamach(w, kg); }
}

function wskrzesSojusznika(w, czas) {
  if (wrogowie.filter(o => o.sojusznik && !o.martwy).length > 24) return;
  const s = stworzWroga(TYPY_WROGOW[w.typ] ? w.typ : 'szkielet', w.x, w.y);
  s.sojusznik = true; s.zauroczony = (czas || 8) * (1 + (FLAGI.mnSojusznikow || 0)); s.bezLupu = true; s.wlasciciel = gracz; s.hp = s.hpMax = s.hpMax * 1.5; s.kolor = '#9a9aaa';
  wrogowie.push(s); rozbryzg(w.x, w.y, '#9a9aaa', 12);
}
function limitWrogow() { return Math.min(120 + 20 * (liczbaGraczy() - 1), (42 + fala.nr * 3.4) * (1 + 0.3 * (liczbaGraczy() - 1))); }

// =====================================================================
//  STAN GRY, STATYSTYKI, EFEKTY I WALKA
// =====================================================================
let gracz = null, D = null, run = null;
let fala = { nr: 0, aktywna: false };
let stan = 'menu';                 // menu | walka | przerwa | smierc
let wrogowie = [], pociski = [], pociskiWrogow = [], kulki = [], monety = [], skrzynieNaZiemi = [];
let czastki = [], teksty = [], fale = [], blyskawice = [], ciecia = [], kaluze = [], polaEfektow = [], wiry = [], scianyMagiczne = [];
let bomby = [], uderzeniaBossa = [], zapowiedzi = [], opoznioneLista = [], efektyCzasowe = [], stozki = [], orbyRys = [];
let czasGry = 0, glebokoscOnHit = 0;
// ---- DRUŻYNA: kilku graczy w jednej symulacji ----
// Każdy gracz ma własne staty (D), haki, flagi i "run" (statystyki, przerwa).
// Funkcje gry działają na globalnych zmiennych - przełączamy je kontekst(p).
let gracze = [], lokalny = null;
function kontekst(p) {
  if (!p || p === gracz) return;
  gracz = p; D = p._D; HAKI = p._HAKI || HAKI; FLAGI = p._FLAGI || FLAGI; run = p._run || run;
}
function zywiGracze() { return gracze.filter(p => !p.powalony && !p.martwy); }
function liczbaGraczy() { return Math.max(1, gracze.length); }
// Drużyna: więcej wrogów (×mnDruzyny), a łupy z nich są dzielone tak, by każdy dostawał mniej więcej tyle, co w pojedynkę
function mnDruzyny() { return 1 + 0.5 * (liczbaGraczy() - 1); }
function mnLupuDruzyny() { return 1 / mnDruzyny(); }
function najblizszyGracz(x, y) { let naj = null, nd = Infinity; for (const p of gracze) { if (p.powalony || p.martwy || p.niewidzialny > 0) continue; const d = Math.hypot(p.x - x, p.y - y); if (d < nd) { nd = d; naj = p; } } return naj; }
function dlaKazdego(fn) { const z = gracz; for (const p of gracze.slice()) { kontekst(p); fn(p); } kontekst(z); }

// ---------------------------------------------------------------------
//  NOWA POSTAĆ
// ---------------------------------------------------------------------
function xpDoPoziomu(L) { return Math.round(18 + 10 * L + 2.2 * L * L); }
function nowyGracz(klasa) {
  const K = KLASY[klasa];
  return {
    klasa: klasa, x: SRODEK, y: SRODEK, r: 13, hp: 100, poziom: 1, xp: 0, xpNast: xpDoPoziomu(1),
    zloto: 0,
    bronie: [], oreze: [], pancerz: { helm: null, zbroja: null, buty: null, amulet: null }, przedmioty: [], augmenty: [],
    ulepszenia: {}, stale: {}, slotyOreza: K.slotyOreza !== undefined ? K.slotyOreza : 4, slotyPrzedm: K.slotyPrzedm, slotyPryzm: K.slotyPryzm || 2, umi: { cd: 0, cdMax: 0 }, umi2: { cd: 0, cdMax: 0 },
    rabat: 0, darmowePrzerzuty: 0, przerzutyAug: 2, darmoweWybory: 0, kowadla: 0, doWyboru: 0, skrzynie: [],
    tarcze: [], buffy: {}, niewr: 0, zastoj: 0, spowG: 0, spowGCzas: 0, migotanie: 0, stanKlasy: {}, kierX: 1, kierY: 0,
    ostTrafienie: -99, wRuchu: false, faza: 0, augmentyDoWyboru: [], blysk: 0, _brudne: true, _ostDyn: 0, id: 0, nick: '',
  };
}

// ---------------------------------------------------------------------
//  HAKI - wszystkie źródła efektów (klasa, przedmioty, augmenty)
// ---------------------------------------------------------------------
const HAKI_NAZWY = ['statyFlat', 'statyDyn', 'statyMnoz', 'statyPost', 'naTrafienie', 'naAtak', 'naObrazenia', 'naZabicie', 'naOtrzymanie',
  'modOtrzymanych', 'modZadanych', 'naKryt', 'naOgluszenie', 'naSpowolnieniu', 'tik', 'naStartFali', 'naKoniecFali', 'naSmierc',
  'naNadleczenie', 'naAktywacji', 'naSklep', 'mnozMonety', 'rozmiar', 'naAwans', 'naUniku', 'mnSkrzyn', 'odbijPocisk', 'naUmiejetnosci', 'statyKonw1', 'statyKonw2', 'statyKonw3', 'statyKonc', 'naNaladowanym', 'mnXp', 'mnZlota', 'mnRegen'];
// flagi sumowane ze wszystkich źródeł (liczba albo funkcja od instancji, np. poziomu augmentu)
const FLAGI_SUMA = ['energiaTempo', 'naladowanyOnHit', 'naladowanyObr', 'przelew', 'mnPrzedmiotow', 'zasiegWrecz', 'onHitKryt', 'oszczedny', 'mnStworow', 'mnOreza', 'cdOreza', 'cdUmi', 'mnUmi', 'mnGlownejAug', 'echoOreza', 'mnTarcz', 'mnSojusznikow'];
const FLAGI_LOG = ['energia', 'naladowanyKryt', 'wszyscyGlowni', 'coTrzeciNaladowany', 'kielich', 'bezKryt', 'superkryt', 'podwojnyOnHit', 'lepszeAugmenty', 'wszystkoMag', 'krysztalCzasu', 'odpornyNaSpow', 'fabryka'];
let HAKI = {}, FLAGI = {};
function zrodlaEfektow() {
  const z = [[KLASY[gracz.klasa], gracz.stanKlasy]];
  gracz.oreze.forEach(o => { if (o) z.push([DEF_ORE[o.id], o]); });
  gracz.przedmioty.forEach(p => { if (p) z.push([DEF_PRZ[p.id], p]); });
  gracz.augmenty.forEach(a => z.push([DEF_AUG[a.id], a]));
  return z;
}
function przebudujHaki() {
  HAKI = {}; HAKI_NAZWY.forEach(n => HAKI[n] = []);
  { const K = KLASY[gracz.klasa]; (K.ewo || []).forEach(e => { if (e.bron !== undefined && gracz.bronie[e.bron]) gracz.bronie[e.bron].ewo = ewo(e.id); }); }
  FLAGI = { unikMax: 80, redukcjaMax: 75, mnGlownej: 1 };
  FLAGI_SUMA.forEach(f => FLAGI[f] = 0); FLAGI_LOG.forEach(f => FLAGI[f] = false);
  zrodlaEfektow().forEach(([d, i]) => {
    if (!d) return;
    HAKI_NAZWY.forEach(n => { if (typeof d[n] === 'function' && !(n === 'tik' && d.oreze)) HAKI[n].push([d, i]); });
    FLAGI_SUMA.forEach(f => { if (d[f]) FLAGI[f] += typeof d[f] === 'function' ? d[f](i) : d[f]; });
    FLAGI_LOG.forEach(f => { if (d[f]) FLAGI[f] = true; });
    if (d.unikMax) FLAGI.unikMax = Math.max(FLAGI.unikMax, d.unikMax);
    if (d.redukcjaMax) FLAGI.redukcjaMax = Math.max(FLAGI.redukcjaMax, d.redukcjaMax);
    if (d.mnGlownej && typeof d.mnGlownej === 'number') FLAGI.mnGlownej *= d.mnGlownej;
  });
  gracz.bronie.forEach(b => { const B = BRONIE[b.rodzaj]; if (B && B.energia) FLAGI.energia = true; });
  gracz.maEnergie = !!FLAGI.energia;
  gracz._HAKI = HAKI; gracz._FLAGI = FLAGI;
}

// ---------------------------------------------------------------------
//  NAŁADOWANIE (jak „energized” w LoL-u): energia 0–100 ładuje się z ruchu (1 na 5 px) i z ataków (+7).
//  Przy 100 następny atak bronią główną jest NAŁADOWANY i odpala efekty przedmiotów/augmentów/broni „naładowany atak”.
// ---------------------------------------------------------------------
const ENERGIA_ZA_ATAK = 7, PX_NA_ENERGIE = 5;
function dodajEnergie(v) {
  if (!FLAGI.energia || !(v > 0)) return;
  const K = KLASY[gracz.klasa];
  if (K && K.blokujEnergie && K.blokujEnergie(gracz.stanKlasy)) return;
  const przed = gracz.energia || 0;
  gracz.energia = Math.min(100, przed + v * (1 + (FLAGI.energiaTempo || 0)) * (K && K.mnEnergii ? K.mnEnergii : 1));
  if (przed < 100 && gracz.energia >= 100) { if (K && K.naPelnaEnergie) { try { K.naPelnaEnergie(gracz.stanKlasy); } catch (e) { zglosBlad(e, 'naPelnaEnergie'); } } if (gracz === lokalny || !druzyna()) DZ.naladowanie(); }
}
function energiaZRuchu() {
  if (!FLAGI.energia) { gracz._ex = gracz.x; gracz._ey = gracz.y; return; }
  if (gracz._ex !== undefined) { const d = Math.hypot(gracz.x - gracz._ex, gracz.y - gracz._ey); if (d > 0.2 && d < 60) dodajEnergie(d / PX_NA_ENERGIE); }
  gracz._ex = gracz.x; gracz._ey = gracz.y;
}
// wywoływane przy każdym prawdziwym ataku bronią główną; zwraca true, gdy ten atak jest naładowany
function zuzyjEnergie(b, cel, o) {
  if (!FLAGI.energia || o.echo || cel.wirtualny) return false;
  const wymuszony = (FLAGI.coTrzeciNaladowany && ((gracz._licznikNal = (gracz._licznikNal || 0) + 1) % 3 === 0));
  if ((gracz.energia || 0) >= 100 || wymuszony) {
    if (!wymuszony) gracz.energia = 0;
    gracz.naladowanyBlysk = 0.35;
    efektBlysk(cel.x, cel.y, '#7ae0ff'); dodajBlyskawice(gracz.x, gracz.y - 6, cel.x, cel.y, '#9fe8ff');
    return true;
  }
  dodajEnergie(ENERGIA_ZA_ATAK);
  return false;
}
function sumaHakow(n, a) {
  const l = HAKI[n]; if (!l || !l.length) return 0;
  let s = 0; for (let j = 0; j < l.length; j++) { try { const v = l[j][0][n](l[j][1], a); if (typeof v === 'number' && isFinite(v)) s += v; } catch (er) { zglosBlad(er, n); } }
  return s;
}
function ktorysHak(n, a) {
  const l = HAKI[n]; if (!l || !l.length) return false;
  for (let j = 0; j < l.length; j++) { try { if (l[j][0][n](l[j][1], a)) return true; } catch (er) { zglosBlad(er, n); } }
  return false;
}
function hak(n, a, b, c, d, e) {
  const l = HAKI[n]; if (!l || !l.length) return;
  for (let j = 0; j < l.length; j++) { try { l[j][0][n](l[j][1], a, b, c, d, e); } catch (er) { zglosBlad(er, n + ':' + (l[j][0].id || l[j][0].n)); } }
}
function mnoznikHakow(n, a, b, c) {
  const l = HAKI[n]; if (!l || !l.length) return 1;
  let m = 1;
  for (let j = 0; j < l.length; j++) { try { const v = l[j][0][n](l[j][1], a, b, c); if (typeof v === 'number' && isFinite(v)) m *= v; } catch (er) { zglosBlad(er, n); } }
  return m;
}
function rozmiarGracza() { return mnoznikHakow('rozmiar'); }
const BLEDY = [];
function zglosBlad(er, gdzie) { if (BLEDY.length < 50) BLEDY.push(gdzie + ': ' + (er && er.message)); if (window.__test) console.error(gdzie, er); }

// ---------------------------------------------------------------------
//  STATYSTYKI
// ---------------------------------------------------------------------
function oznaczStaty() { if (gracz) gracz._brudne = true; }
function przeliczStaty() { if (gracz) gracz._brudne = true; }
function dodajStaty(s, z, mn) { if (!z) return; mn = mn === undefined ? 1 : mn; for (const k in z) if (k in s) s[k] += z[k] * mn; }
function policzZestawy() {
  const licz = {};
  gracz.bronie.forEach(b => { const r = BRONIE[b.rodzaj].rodz; licz[r] = (licz[r] || 0) + 1; });
  gracz.oreze.forEach(o => { const r = DEF_ORE[o.id].rodz; licz[r] = (licz[r] || 0) + 1; });
  return licz;
}
function poziomZestawu(n) { let p = -1; PROGI_RODZIN.forEach((pr, i) => { if (n >= pr) p = i; }); return p; }
function obliczStaty() {
  const s = Object.assign({}, BAZA_STATOW);
  const K = KLASY[gracz.klasa];
  dodajStaty(s, K.staty);
  s.hpMax += (K.hpZaPoziom || 5) * (gracz.poziom - 1);
  dodajStaty(s, gracz.ulepszenia);
  dodajStaty(s, gracz.stale);
  const mnP = 1 + FLAGI.mnPrzedmiotow;
  SLOTY_PANCERZA.forEach(sl => { const p = gracz.pancerz[sl]; if (p) dodajStaty(s, statyPancerza(p), mnP); });
  gracz.oreze.forEach(o => { if (o) dodajStaty(s, statyOreza(o), mnP); });
  gracz.przedmioty.forEach(p => { if (p && DEF_PRZ[p.id].s) dodajStaty(s, DEF_PRZ[p.id].s, M(p)); });   // tylko pryzmaty mają staty (gwiazdki: Kapłan Pryzmatu)
  gracz.augmenty.forEach(a => { const st = statyAugmentu(a); if (st) dodajStaty(s, st); });
  const z = policzZestawy();
  for (const t in z) { const n = poziomZestawu(z[t]); if (n >= 0 && RODZINY[t]) dodajStaty(s, RODZINY[t].staty(n)); }
  for (const id in gracz.buffy) dodajStaty(s, gracz.buffy[id].staty);
  hak('statyFlat', s);
  hak('statyDyn', s);
  if (gracz.stale.hpProc) s.hpMax *= 1 + gracz.stale.hpProc / 100;
  hak('statyMnoz', s);
  hak('statyPost', s);
  // zamiany ⚔️/✨ zawsze w tej kolejności: Harmonia (dodaje) → Waga Sprawiedliwości (wyrównuje w górę) → Kostur Arcymaga (⚔️ → ✨)
  hak('statyKonw1', s); hak('statyKonw2', s); hak('statyKonw3', s);
  hak('statyKonc', s);   // to, co liczy się od gotowych ⚔️/✨
  if (FLAGI.przelew) przelejNadmiar(s, FLAGI.przelew);
  s.hpMax = Math.max(1, Math.round(s.hpMax));
  s.ms = Math.max(40, s.ms);
  return s;
}
// PRZELEW (augment): to, co przekracza limity, nie przepada, tylko zamienia się w coś innego
function przelejNadmiar(s, m) {
  if (s.kryt > 100) { s.krytObr += (s.kryt - 100) * 1.5 * m; s.kryt = 100; }
  const lu = FLAGI.unikMax || 80; if (s.unik > lu) { s.obrBonus += (s.unik - lu) * 1.5 * m; s.unik = lu; }
  const lr = FLAGI.redukcjaMax || 75; if (s.redukcja > lr) { s.hpMax *= 1 + (s.redukcja - lr) * 0.02 * m; s.redukcja = lr; }
  const wamp = Math.max(0, s.omni);           // powyżej 33 limit leczenia już nie rośnie
  if (wamp > 33) s.obrBonus += (wamp - 33) * 0.6 * m;
  const sp = s.as - 300; if (sp > 0) s.obrBonus += sp * 0.15 * m;      // bardzo szybkie ataki i tak tracą sens
}
function zastosujStaty() {
  const stareMax = D ? D.hpMax : null;
  D = obliczStaty(); gracz._D = D;
  // korekta aktualnego zdrowia
  if (stareMax !== null && D.hpMax !== stareMax) {
    if (D.hpMax > stareMax) gracz.hp += D.hpMax - stareMax;
    gracz.hp = Math.min(gracz.hp, D.hpMax);
  }
  gracz._brudne = false;
}
function odswiezStatyJesliTrzeba() {
  if (gracz._brudne || !D) { zastosujStaty(); gracz._ostDyn = czasGry; return; }
  if (HAKI.statyDyn.length && czasGry - (gracz._ostDyn || 0) > 0.25) { zastosujStaty(); gracz._ostDyn = czasGry; }
}
function mnObszaru() { return 1 + D.obszar / 100; }
function nrFali() { return fala ? Math.max(1, fala.nr) : 1; }
function mnCeny() { const nr = Math.max(1, fala.nr || 1); return (1 + 0.075 * (nr - 1)) * Math.max(0.4, 1 - (gracz ? gracz.rabat : 0) / 100); }
function maPrzedmiot(id) { return gracz.przedmioty.some(p => p && p.id === id); }
// Przedmioty zwykłe i pryzmatyczne mają OSOBNE miejsca (np. 4 zwykłe + 2 pryzmatyczne).
function czyPryzmat(p) { const d = p && DEF_PRZ[p.id || p]; return !!d && d.t === 'p'; }
function liczPrzedm(pryzm) { return gracz.przedmioty.filter(p => p && czyPryzmat(p) === !!pryzm).length; }
function slotyTypu(pryzm) { return pryzm ? (gracz.slotyPryzm || 2) : gracz.slotyPrzedm; }
function wolneSlotyPrzedm(pryzm) { return slotyTypu(pryzm) - liczPrzedm(pryzm); }

// ---------------------------------------------------------------------
//  ZADAWANIE OBRAŻEŃ
// ---------------------------------------------------------------------
function zadaj(w, ilosc, typ, o) {
  if (!w || w.martwy || !(ilosc > 0)) return 0;
  o = o || {};
  if (w.zauroczony > 0 && w.sojusznik) return 0;
  let mn = 1 + D.obrBonus / 100;
  if (w.boss || w.elita) mn += D.obrElity / 100;
  if (w.naznaczony > 0 && w.mnNazn) mn *= 1 + w.mnNazn;      // Halabarda
  if (w.wzm > 0) mn *= 0.75;                                  // wróg wzmocniony przez Kultystę
  mn *= mnoznikHakow('modZadanych', w, typ, o);
  let v = ilosc * Math.max(0, mn);
  if (typ === 'fiz') {
    const p = w.panc * (1 - (w.krusz || 0)) * (1 - Math.min(100, D.przebPancP + (o.przebPanc || 0)) / 100) - D.lethality;
    v *= p >= 0 ? 100 / (100 + p) : 2 - 100 / (100 - p);
  } else if (typ === 'mag') {
    const p = w.odp * (1 - (w.krusz || 0)) * (1 - Math.min(100, D.przebMagP) / 100) - D.przebMag;
    v *= p >= 0 ? 100 / (100 + p) : 2 - 100 / (100 - p);
  }
  if (w.duch && o.pocisk && Math.random() < 0.3) { tekstSwiat(w.x, w.y - w.r - 6, 'pudło', '#c0d0ff', 0.6); return 0; }
  if (w.tarczaPrzod === undefined) w.tarczaPrzod = !!(TYPY_WROGOW[w.typ] && TYPY_WROGOW[w.typ].tarczaPrzod);
  if (w.tarczaPrzod && w.kier !== undefined && w.ogl <= 0 && roznicaKata(Math.atan2(gracz.y - w.y, gracz.x - w.x), w.kier) < 1.0) { v *= 0.35; if (Math.random() < 0.15) tekstSwiat(w.x, w.y - w.r - 8, '🛡 blok', '#c8d0e0', 0.5, 10); }
  if (w.tarcza > 0) { const pochl = Math.min(w.tarcza, v); w.tarcza -= pochl; w.odTrafienia = 0; v -= pochl; if (v <= 0) { w.trafiony = 0.08; return 0; } }
  w.hp -= v; w.trafiony = 0.1;
  // liczby obrażeń - sumowane, żeby nie zasypać ekranu
  const t = w.txt || (w.txt = { v: 0, typ: typ, kryt: false, t0: czasGry });
  t.v += v; if (o.kryt) t.kryt = true; if (typ === 'praw' || (typ === 'mag' && t.typ === 'fiz')) t.typ = typ;
  run.zadane += v;
  const zr = o.zr || 'Inne'; run.zrodla[zr] = (run.zrodla[zr] || 0) + v;
  let lecz = 0;
  if (D.omni > 0) lecz += v * D.omni / 100 * ((o.dot || o.obszar) ? 0.33 : 1);
  if (lecz > 0) leczWampirem(lecz, 'Wampiryzm');
  if (w.afiksy.length && w.afiksy.indexOf('lustrzany') >= 0 && !o.odbicie && czasGry - (w._ostOdb || 0) > 0.4) {
    w._ostOdb = czasGry; zranGracza(Math.min(v * 0.08, D.hpMax * 0.015), 'praw', { bezUniku: true, odbicie: true, kto: 'Lustrzana elita' });
  }
  if (!o.bezHakow) hak('naObrazenia', w, v, typ, o);
  if (w.hp <= 0 && !w.martwy) zabij(w, o);
  return v;
}

function zabij(w, o) {
  if (w.martwy) return;
  w.martwy = true; o = o || {};
  if (w.txt) wypiszObrazenia(w);
  run.zabici++;
  rozbryzg(w.x, w.y, w.kolor || '#c0392b', w.boss ? 40 : 12);
  DZ.smiercWroga();
  if (!w.bezLupu && !w.sojusznik) {
    const mL = w.boss ? 1 : mnLupuDruzyny();
    rozsypKulki(w.x, w.y, w.xp * mL);
    rozsypMonety(w.x, w.y, w.zl * mL, !!w.zloty);
    const mnS = (1 + D.szczescie / 100) * mnoznikHakow('mnSkrzyn') * (TRUDNOSCI[run.trudnosc].skrzynie || 1);
    let pSk = w.boss ? 1 : (w.elita ? 0.12 : 0.005) * mnS * mL;
    if (!w.boss && (fala.skrzynie || 0) >= zakresSkrzyn(fala.nr)[1]) pSk = 0;
    if (Math.random() < pSk) { skrzynieNaZiemi.push({ x: w.x, y: w.y, tier: tierSkrzyni(w), faza: Math.random() * 6, boss: !!w.boss }); if (!w.boss) fala.skrzynie = (fala.skrzynie || 0) + 1; }
  }
  const T = TYPY_WROGOW[w.typ];
  if (T && T.dzieli && !w.sojusznik) {
    for (let i = 0; i < 2; i++) { const s = stworzWroga(T.dzieli, w.x + losowo(-16, 16), w.y + losowo(-16, 16)); if (w.elita) { s.hp *= 2; s.hpMax = s.hp; } wrogowie.push(s); }
  }
  if (T && T.wstaje && !w.wstal && !w.sojusznik && Math.random() < 0.5) {
    const s = stworzWroga(w.typ, w.x, w.y); s.wstal = true; s.hp = s.hpMax = s.hpMax * 0.5; s.ogl = 0.9; wrogowie.push(s); tekstSwiat(w.x, w.y - w.r - 10, '🧟 wstaje!', '#9ae07a', 0.9, 12);
  }
  if (T && T.rozpada && !w.sojusznik) {
    for (let i = 0; i < 2; i++) { const s = stworzWroga('kamyk', w.x + losowo(-14, 14), w.y + losowo(-14, 14)); if (w.elita) { s.hp *= 2; s.hpMax = s.hp; } wrogowie.push(s); }
  }
  if (w.afiksy.indexOf('wybuchowy') >= 0) postawBombe(w.x, w.y, w.atak, 0.9);
  if (w.afiksy.indexOf('lodowy') >= 0) { fale.push({ x: w.x, y: w.y, czas: 0.4, max: 0.4, r: 120, kolor: '#9fd8ff' }); dlaKazdego(p => { if (!p.powalony && Math.hypot(p.x - w.x, p.y - w.y) < 120) spowolnijGracza(0.5, 2); }); }
  if (w.czempion) fala.czempionZabity = true;
  if (w.boss) bossPokonany(w);
  if (o.bron && BRONIE[o.bron.rodzaj] && BRONIE[o.bron.rodzaj].naZabicie) { try { BRONIE[o.bron.rodzaj].naZabicie(w, o.bron); } catch (e) { zglosBlad(e, 'naZabicie broni'); } }
  if (!o.bezHakow) hak('naZabicie', w, o);
}

function wypiszObrazenia(w) {
  const t = w.txt; w.txt = null;
  if (!t || t.v < 0.5) return;
  if (teksty.length > 36 && !t.kryt) return;
  const kol = t.typ === 'mag' ? '#86b8ff' : (t.typ === 'praw' ? '#ffffff' : '#f5c58a');
  // o: 1 = zwykła liczba obrażeń, 2 = ważna (kryt, elita, boss) — ustawienie „Liczby obrażeń” filtruje je przy rysowaniu
  tekstSwiat(w.x + losowo(-6, 6), w.y - w.r - 2, fmtK(t.v) + (t.kryt ? '!' : ''), t.kryt ? '#ffd24a' : kol, t.kryt ? 0.9 : 0.7, t.kryt ? 15 : 12, (t.kryt || w.elita || w.boss) ? 2 : 1);
}

// ---------------------------------------------------------------------
//  ATAK BRONIĄ
// ---------------------------------------------------------------------
function trafienieAtakiem(w, b, o) {
  if (!w || w.martwy) return;
  o = o || {};
  const B = BRONIE[b.rodzaj];
  const glowny = o.glowny !== false, nal = (o.naladowany !== undefined ? o.naladowany : !!b._naladowany) && glowny;
  const baz = obrBroni(b) * (o.mn || 1) * (B.mnTrafienia ? B.mnTrafienia(b, w, o) : 1) * (nal ? 1 + (FLAGI.naladowanyObr || 0) : 1);
  const sz = FLAGI.bezKryt ? 0 : D.kryt + (B.kryt || 0);
  let kryt = Math.random() * 100 < sz || (!!o.pewnyKryt && !FLAGI.bezKryt), mnK = 1;
  if (kryt) {
    mnK = 1.75 + (D.krytObr + (B.krytObr || 0)) / 100;
    if (FLAGI.superkryt && sz > 100 && Math.random() * 100 < sz - 100) { mnK *= 2; tekstSwiat(w.x, w.y - w.r - 16, 'SUPERKRYT', '#ff7ae0', 0.8, 14); }
  }
  const surowe = baz * mnK;
  const zad = zadaj(w, surowe, FLAGI.wszystkoMag ? 'mag' : B.obrTyp, { atak: true, kryt: kryt, bron: b, zr: B.nazwa, pocisk: o.pocisk, przebPanc: B.przebPanc, obszar: o.obszar });
  const k = { bron: b, kryt: kryt, glowny: glowny || !!FLAGI.wszyscyGlowni, zadane: zad, zadaneSurowe: surowe, bazowe: baz, licznikCiosu: o.licznikCiosu || 1, zOgluszenia: false, naladowany: nal };
  if (B.naTrafienie) { try { B.naTrafienie(w, b, k); } catch (e) { zglosBlad(e, 'bron ' + b.rodzaj); } }
  if (kryt) { hak('naKryt', w, k); DZ.kryt(); }
  let razy = 1; if (b._podwojnyOnHit) razy++; if (FLAGI.podwojnyOnHit) razy *= 2;
  if (kryt && FLAGI.onHitKryt) razy += Math.round(FLAGI.onHitKryt);
  if (nal && FLAGI.naladowanyOnHit) razy += Math.round(FLAGI.naladowanyOnHit);
  zastosujOnHit(w, b, { k: k, razy: Math.min(8, razy) });
}
function zastosujOnHit(w, b, o) {
  glebokoscOnHit++;
  try {
    const razy = o.razy || 1;
    const k = o.k || { bron: b, kryt: false, glowny: false, zadane: 0, zadaneSurowe: 0, bazowe: 0, zOgluszenia: !!o.zOgluszenia };
    if (o.zOgluszenia) k.zOgluszenia = true;
    for (let r = 0; r < razy; r++) {
      if (w.martwy) break;
      if (D.onHitFiz > 0) zadaj(w, D.onHitFiz, 'fiz', { onhit: true, zr: 'On-hit' });
      if (D.onHitMag > 0) zadaj(w, D.onHitMag, 'mag', { onhit: true, zr: 'On-hit' });
      if (D.onHitPraw > 0) zadaj(w, D.onHitPraw, 'praw', { onhit: true, zr: 'On-hit' });
      if (w.martwy) break;
      hak('naTrafienie', w, k);
    }
  } finally { glebokoscOnHit--; }
}

function celBroni(b, zas) {
  // celowanie (trzymana prawa gałka pada): atak ZAWSZE leci w tę stronę — w wroga w tym kierunku (±~22°),
  // a gdy nikogo tam nie ma, w pusty punkt na końcu zasięgu. Puszczona gałka = zwykłe namierzanie.
  const ck = gracz.celKat;
  if (ck !== null && ck !== undefined) {
    let naj = null, najW = Infinity;
    for (let i = 0; i < wrogowie.length; i++) {
      const w = wrogowie[i]; if (w.martwy || w.zauroczony > 0) continue;
      const d = Math.hypot(w.x - gracz.x, w.y - gracz.y) - w.r; if (d >= zas) continue;
      const dk = roznicaKata(Math.atan2(w.y - gracz.y, w.x - gracz.x), ck);
      if (dk > 0.38 + Math.atan2(w.r, Math.max(1, d + w.r))) continue;
      const wyn = dk * 230 + d * 0.3;
      if (wyn < najW) { najW = wyn; naj = w; }
    }
    if (naj) return naj;
    return { x: gracz.x + Math.cos(ck) * zas, y: gracz.y + Math.sin(ck) * zas, r: 0, martwy: true, wirtualny: true, hp: 0, hpMax: 1, afiksy: [] };
  }
  const daleki = BRONIE[b.rodzaj].celDaleki;
  let naj = null, najD = daleki ? -1 : Infinity;
  for (let i = 0; i < wrogowie.length; i++) {
    const w = wrogowie[i]; if (w.martwy || w.zauroczony > 0) continue;
    const d = Math.hypot(w.x - gracz.x, w.y - gracz.y) - w.r;
    if (d < zas && (daleki ? d > najD : d < najD)) { najD = d; naj = w; }
  }
  return naj;
}
function zasiegAtaku(b) { const B = BRONIE[b.rodzaj]; return zasiegBroni(b) * (B.dystans ? 1 : (1 + FLAGI.zasiegWrecz) * Math.sqrt(rozmiarGracza())); }

function aktualizujBronie(dt) {
  if (gracz.zastoj > 0) return;
  for (let idx = 0; idx < gracz.bronie.length; idx++) {
    const b = gracz.bronie[idx], B = BRONIE[b.rodzaj];
    if (b.anim > 0) b.anim -= dt;
    if (B.przyAtaku && b.odCiosu !== undefined) { b.odCiosu += dt; if (b.odCiosu > 2) b.rozped = 0; }
    if (fala.rozbrojenie && idx > 0) continue;
    if (B.atak === 'orbita') { orbitaBroni(b, dt); continue; }
    let tempo = (1 + D.as / 100) * (B.tempo ? B.tempo(b) : 1);
    tempo = ogr(tempo, 0.2, B.cd / 0.1);
    if (b.cd > 0) b.cd -= dt * tempo;
    if (b.cd > 0) continue;
    const cel = celBroni(b, zasiegAtaku(b));
    if (!cel) { b.cd = 0; continue; }
    b.cd += B.cd;
    if (b.cd < 0) b.cd = 0;
    atakujBronia(b, cel, {});
  }
}

function atakujBronia(b, cel, o) {
  const B = BRONIE[b.rodzaj];
  b.kat = kat(gracz, cel); b.anim = 0.16;
  gracz.kierX = Math.cos(b.kat); gracz.kierY = Math.sin(b.kat);
  if (B.przyAtaku) B.przyAtaku(b);
  b._podwojnyOnHit = (b.ewo || 0) >= 3;
  b._naladowany = zuzyjEnergie(b, cel, o);
  if (!cel.wirtualny) hak('naAtak', b, cel, o);   // atak w pustkę (celowanie gałką) nie liczy się do efektów „co N-ty atak”
  if (b._naladowany) { if (B.naNaladowanym) { try { B.naNaladowanym(b, cel); } catch (e) { zglosBlad(e, 'naładowany ' + b.rodzaj); } } hak('naNaladowanym', b, cel); }
  b._pewnyKryt = !!gracz.stanKlasy.pewnyKryt || (b._naladowany && FLAGI.naladowanyKryt); gracz.stanKlasy.pewnyKryt = false;
  run.ataki++;
  switch (B.atak) {
    case 'wrecz': cios(b, cel); DZ.ciecie(); break;
    case 'pchniecie': pchniecie(b, cel); DZ.ciecie(); break;
    case 'pocisk': strzal(b, cel); if (B.obrTyp === 'mag') DZ.magia(); else DZ.strzal(); break;
    case 'piorun': piorunBroni(b, cel); break;
    case 'bumerang': rzutBumerangiem(b, cel); DZ.strzal(); break;
    case 'granat': rzutGranatu(b, cel); DZ.strzal(); break;
    case 'stozek': strumien(b, cel); break;
    case 'orbita': trafienieAtakiem(cel, b, { glowny: true }); break;
    case 'grom': uderzGromem(b, cel.x, cel.y, cel.wirtualny ? null : cel, 1); DZ.piorun(); break;
  }
  b._pewnyKryt = false; b._naladowany = false;
}
// Kostur Gromu: piorun z nieba w miejsce celu, rani wszystkich w promieniu
function uderzGromem(b, x, y, cel, mn) {
  const B = BRONIE[b.rodzaj], r = (B.promien + 5 * b.tier) * mnObszaru();
  dodajBlyskawice(x + losowo(-24, 24), y - 170, x, y, '#ffe066'); fale.push({ x: x, y: y, czas: 0.3, max: 0.3, r: r, kolor: '#ffe066' });
  let pierwszy = true;
  wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - x, w.y - y) > r + w.r * 0.5) return;
    const gl = cel ? w === cel : pierwszy; pierwszy = false; trafienieAtakiem(w, b, { mn: mn, glowny: gl, obszar: !gl, pewnyKryt: gl && b._pewnyKryt }); });
}
// Krążące Kule: ciągła orbita, każdy dotknięty wróg dostaje trafienie (ten sam co B.cd s / prędkość ataku)
function orbitaBroni(b, dt) {
  const B = BRONIE[b.rodzaj];
  let tempo = ogr((1 + D.as / 100) * (B.tempo ? B.tempo(b) : 1), 0.2, 6);
  b.faza = (b.faza || 0) + dt * 2.6 * Math.sqrt(tempo);
  const n = 2 + b.tier, rr = zasiegAtaku(b), odstep = B.cd / tempo, klucz = '_orbB' + gracz.id;
  if (b.cdAtk > 0) b.cdAtk -= dt;
  for (let j = 0; j < n; j++) {
    const k = b.faza + j * Math.PI * 2 / n, x = gracz.x + Math.cos(k) * rr, y = gracz.y + Math.sin(k) * rr;
    orbyRys.push({ x: x, y: y, kolor: '#b48aff', kat: k });
    for (let i = 0; i < wrogowie.length; i++) {
      const w = wrogowie[i]; if (w.martwy || w.zauroczony > 0) continue;
      if (Math.abs(w.x - x) > 16 + w.r || Math.abs(w.y - y) > 16 + w.r || Math.hypot(w.x - x, w.y - y) > 16 + w.r) continue;
      if (w[klucz] && czasGry - w[klucz] < odstep) continue;
      w[klucz] = czasGry;
      // co odstęp liczy się jak „atak” (efekty co N-ty atak, naładowanie)
      if (!(b.cdAtk > 0)) { b.cdAtk = odstep; b.kat = k; b.anim = 0.12; atakujBronia(b, w, { orbita: true }); }
      else trafienieAtakiem(w, b, { glowny: true });
    }
  }
}
// granatnik: pocisk leci łukiem w miejsce celu i wybucha
function rzutGranatu(b, cel) {
  const B = BRONIE[b.rodzaj], ile = 1 + Math.max(0, Math.round(D.pociski));
  for (let n = 0; n < ile; n++) {
    const tx = cel.x + (n ? losowo(-60, 60) : 0), ty = cel.y + (n ? losowo(-60, 60) : 0);
    const d = Math.hypot(tx - gracz.x, ty - gracz.y), v = 340, k = Math.atan2(ty - gracz.y, tx - gracz.x);
    pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, zycie: Math.max(0.12, d / v), maxZycie: Math.max(0.12, d / v), r: 7, bron: b, mn: n ? 0.6 : 1,
      granat: { r: (B.promien + 6 * b.tier) * mnObszaru() }, trafieni: [], kolor: B.kolor, ksztalt: 'granat', przebija: 0, pewnyKryt: !n && b._pewnyKryt, naladowany: !n && !!b._naladowany });
  }
}
function wybuchGranatu(p) {
  const r = p.granat.r;
  fale.push({ x: p.x, y: p.y, czas: 0.35, max: 0.35, r: r, kolor: '#ffb070' }); rozbryzg(p.x, p.y, '#ffb070', 14); DZ.wybuch();
  let glowny = true;
  wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - p.x, w.y - p.y) > r + w.r * 0.5) return; trafienieAtakiem(w, p.bron, { mn: p.mn, glowny: glowny, obszar: true, pewnyKryt: p.pewnyKryt && glowny, naladowany: !!p.naladowany && glowny }); glowny = false; });
}
// miotacz: stożek ognia
function strumien(b, cel) {
  const B = BRONIE[b.rodzaj], zas = zasiegAtaku(b), k0 = b.kat;
  stozki.push({ x: gracz.x, y: gracz.y, kat: k0, r: zas, pol: B.pol, czas: 0.18, max: 0.18, kolor: B.kolor });
  if (mozna('plomien', 140)) szum(0.12, 0.05, 'bandpass', 600);
  let jest = false;
  wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0) return; const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); if (d > zas + w.r) return;
    if (roznicaKata(Math.atan2(w.y - gracz.y, w.x - gracz.x), k0) > B.pol + Math.atan2(w.r, Math.max(1, d))) return; jest = jest || w === cel; trafienieAtakiem(w, b, { glowny: w === cel, pewnyKryt: b._pewnyKryt && w === cel }); });
  if (!jest && !cel.martwy) trafienieAtakiem(cel, b, { glowny: true });
}
function echoAtaku(b, cel) {
  if (stan !== 'walka' || gracz.bronie.indexOf(b) < 0) return;
  if (!cel || cel.martwy) cel = celBroni(b, zasiegAtaku(b));
  if (cel) atakujBronia(b, cel, { echo: true });
}

function cios(b, cel) {
  const B = BRONIE[b.rodzaj], zas = zasiegAtaku(b), k0 = b.kat, luk = B.luk;
  ciecia.push({ x: gracz.x, y: gracz.y, kat: k0, luk: luk, r: zas, czas: 0.16, max: 0.16, kolor: TIERY[b.tier].kolor });
  let n = 0;
  const lista = wrogowie.slice();
  for (const w of lista) {
    if (w.martwy || w.zauroczony > 0) continue;
    const d = Math.hypot(w.x - gracz.x, w.y - gracz.y);
    if (d > zas + w.r) continue;
    if (luk < 6 && roznicaKata(Math.atan2(w.y - gracz.y, w.x - gracz.x), k0) > luk / 2 + Math.atan2(w.r, Math.max(1, d))) continue;
    n++;
    trafienieAtakiem(w, b, { glowny: w === cel, licznikCiosu: n, pewnyKryt: b._pewnyKryt && w === cel });
  }
  if (cel.martwy === false && n === 0) trafienieAtakiem(cel, b, { glowny: true, licznikCiosu: 1, pewnyKryt: b._pewnyKryt });
}
function pchniecie(b, cel) {
  const zas = zasiegAtaku(b), k0 = b.kat, cx = Math.cos(k0), cy = Math.sin(k0);
  ciecia.push({ x: gracz.x, y: gracz.y, kat: k0, luk: 0, r: zas, czas: 0.14, max: 0.14, kolor: TIERY[b.tier].kolor, linia: true });
  const lista = wrogowie.slice();
  let trafionyCel = false;
  for (const w of lista) {
    if (w.martwy || w.zauroczony > 0) continue;
    const rx = w.x - gracz.x, ry = w.y - gracz.y, wzd = rx * cx + ry * cy, pop = Math.abs(rx * cy - ry * cx);
    if (wzd < -w.r || wzd > zas + w.r || pop > (BRONIE[b.rodzaj].szer || 18) + w.r) continue;
    if (w === cel) trafionyCel = true;
    trafienieAtakiem(w, b, { glowny: w === cel, pewnyKryt: b._pewnyKryt && w === cel });
  }
  if (!trafionyCel && !cel.martwy) trafienieAtakiem(cel, b, { glowny: true, pewnyKryt: b._pewnyKryt });
  if (!BRONIE[b.rodzaj].rzut) return;
  b.licznik = (b.licznik || 0) + 1;
  if (b.licznik % (b.tier >= 2 ? 3 : 4) === 0) {
    pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: cx * 470, vy: cy * 470, zycie: 0.9, r: 7, bron: b, mn: 1.5, przebija: 99, trafieni: [], kolor: '#d8d0b0', ksztalt: 'wlocznia' });
    ton(300, 0.08, 'triangle', 0.1);
  }
}
function strzal(b, cel) {
  const B = BRONIE[b.rodzaj];
  let ile = 1 + Math.max(0, Math.round(D.pociski)) + (b.rodzaj === 'luk' && b.tier >= 3 ? 1 : 0) + (B.dodPociskiT ? B.dodPociskiT(b.tier) : 0) + ((b.ewo || 0) >= 2 ? 1 : 0);
  let rozrzut = B.rozrzut || 0.16;
  if (b.rodzaj === 'pistolet' && b.licznikP % 6 === 0) { ile += 2 + Math.floor(b.tier / 2); rozrzut = 0.1; }
  const zas = zasiegAtaku(b);
  const przebija = (B.przebija || 0) + ((b.rodzaj === 'kusza' || b.rodzaj === 'muszkiet') ? b.tier : 0) + Math.max(0, Math.round(D.przebicie));
  for (let n = 0; n < ile; n++) {
    const off = ile === 1 ? 0 : (n - (ile - 1) / 2) * rozrzut;
    const k = b.kat + off;
    pociski.push({
      wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * B.predkosc, vy: Math.sin(k) * B.predkosc, zycie: zas * 1.05 / B.predkosc, r: gracz.stanKlasy.salwa > czasGry ? 10 : 6, duza: gracz.stanKlasy.salwa > czasGry,
      bron: b, mn: n === 0 || B.pelnePociski ? 1 : (b.rodzaj === 'pistolet' ? 0.7 : 0.6), glowny: n === 0, przebija: przebija, trafieni: [], kolor: B.kolor, ksztalt: B.ksztalt,
      naprowadza: B.naprowadza || 0, cel: cel, odbicia: B.odbicia ? B.odbicia(b.tier) : 0, pewnyKryt: n === 0 && b._pewnyKryt, naladowany: n === 0 && !!b._naladowany, bezSpadku: !!B.bezSpadku, zasiegOdbicia: B.zasiegOdbicia || 0,
    });
  }
}
function strzalPomocniczy(b, w, mn) {
  const B = BRONIE[b.rodzaj], k = kat(gracz, w), v = B.predkosc || 500;
  pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, zycie: 1, r: 6, bron: b, mn: mn, glowny: false, przebija: 0, trafieni: [],
    kolor: B.kolor || '#e8d8b0', ksztalt: B.ksztalt || 'strzala', naprowadza: 6, cel: w });
}
function piorunBroni(b, cel) {
  if (cel.wirtualny) { const w = najblizsi(cel.x, cel.y, 140, 1)[0]; if (!w) { dodajBlyskawice(gracz.x, gracz.y - 8, cel.x, cel.y, '#ffe066'); return; } cel = w; }
  const ile = 3 + b.tier + Math.max(0, Math.round(D.pociski));
  dodajBlyskawice(gracz.x, gracz.y - 8, cel.x, cel.y, '#ffe066'); DZ.piorun();
  trafienieAtakiem(cel, b, { glowny: true });
  let ogniwo = cel, trafieni = [cel], sila = 0.75;
  for (let s = 0; s < ile; s++) {
    let nast = null, najD = 150 * mnObszaru();
    for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || trafieni.indexOf(w) >= 0) continue; const d = Math.hypot(w.x - ogniwo.x, w.y - ogniwo.y); if (d < najD) { najD = d; nast = w; } }
    if (!nast) break;
    dodajBlyskawice(ogniwo.x, ogniwo.y, nast.x, nast.y, '#ffe066');
    trafienieAtakiem(nast, b, { glowny: false, mn: sila });
    trafieni.push(nast); ogniwo = nast; sila *= 0.75;
  }
}
function rzutBumerangiem(b, cel) {
  const ile = (b.tier >= 3 ? 2 : 1) + Math.max(0, Math.round(D.pociski));
  const zas = zasiegAtaku(b);
  for (let n = 0; n < ile; n++) {
    const k = b.kat + (ile === 1 ? 0 : (n - (ile - 1) / 2) * 0.35);
    pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * 380, vy: Math.sin(k) * 380, zycie: 4, r: 9, bron: b, mn: n === 0 ? 1 : 0.6, glowny: n === 0,
      przebija: 99, trafieni: [], kolor: TIERY[b.tier].kolor, ksztalt: 'bumerang', bumerang: true, droga: 0, maxDroga: zas, wraca: false, obrot: 0 });
  }
}

// ---------------------------------------------------------------------
//  EFEKTY STATUSU NA WROGACH
// ---------------------------------------------------------------------
function oglusz(w, czas, o) {
  if (!w || w.martwy) return;
  if (w.boss) czas *= 0.3; else if (w.ciezki) czas *= 0.7;
  w.ogl = Math.max(w.ogl || 0, czas);
  hak('naOgluszenie', w, czas, o || {});
}
function spowolnij(w, proc, czas) {
  if (!w || w.martwy) return;
  if (w.boss) proc *= 0.5;
  if (proc >= (w.spow || 0)) w.spow = proc;
  w.spowCzas = Math.max(w.spowCzas || 0, czas);
  if (HAKI.naSpowolnieniu.length) hak('naSpowolnieniu', w);
}
function podpal(w, dps, czas, typ, zr) {
  if (!w || w.martwy || !(dps > 0)) return;
  const kl = zr || 'Podpalenie';
  if (!w.ognie) w.ognie = {};
  const o = w.ognie[kl];
  if (o) { o.dps = Math.max(o.dps, dps); o.czas = Math.max(o.czas, czas); o.wl = gracz; }
  else w.ognie[kl] = { dps: dps, czas: czas, tyk: 0.5, typ: typ || 'mag', wl: gracz };
  w.ogien = true;
}
function dpsOgnia(w) { let s = 0; if (w.ognie) for (const k in w.ognie) s += w.ognie[k].dps; return s; }
function krwawienie(w, dps, czas, leczy) {
  if (!w || w.martwy || !(dps > 0)) return;
  if (w.krew) { w.krew.dps = Math.max(w.krew.dps, dps); w.krew.czas = Math.max(w.krew.czas, czas); w.krew.leczy = w.krew.leczy || leczy; w.krew.wl = gracz; }
  else w.krew = { dps: dps, czas: czas, tyk: 0.5, leczy: !!leczy, wl: gracz };
}
function tikEfektowWroga(w, dt) {
  if (w.ognie) {
    let jest = false;
    for (const kl in w.ognie) {
      const o = w.ognie[kl]; o.czas -= dt; o.tyk -= dt;
      if (o.tyk <= 0) { o.tyk += 0.5; kontekst(o.wl); zadaj(w, o.dps * 0.5, o.typ, { dot: true, zr: kl }); if (w.martwy) return; }
      if (o.czas <= 0) delete w.ognie[kl]; else jest = true;
    }
    w.ogien = jest; if (!jest) w.ognie = null;
  }
  if (w.krew) {
    w.krew.czas -= dt; w.krew.tyk -= dt;
    if (w.krew.tyk <= 0) { w.krew.tyk += 0.5; kontekst(w.krew.wl); const v = zadaj(w, w.krew.dps * 0.5, 'fiz', { dot: true, zr: 'Krwawienie' }); if (w.krew && w.krew.leczy && v > 0) leczWampirem(v * 0.2, 'Krwawienie'); if (w.martwy) return; }
    if (w.krew && w.krew.czas <= 0) w.krew = null;
  }
}
function odrzuc(w, sila) {
  if (!w || w.martwy || w.ciezki || w.boss) return;
  const k = kat(gracz, w); w.kbx += Math.cos(k) * sila * 7; w.kby += Math.sin(k) * sila * 7;
}

// ---------------------------------------------------------------------
//  POMOCNICZE DLA PRZEDMIOTÓW
// ---------------------------------------------------------------------
function zywi() { return wrogowie.filter(w => !w.martwy && !(w.zauroczony > 0)); }
function najblizszyWrog(x, y, r, wyklucz) {
  let naj = null, najD = r;
  for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || (wyklucz && wyklucz.indexOf(w) >= 0)) continue; const d = Math.hypot(w.x - x, w.y - y); if (d < najD) { najD = d; naj = w; } }
  return naj;
}
function najblizsi(x, y, r, n, wyklucz) {
  return wrogowie.filter(w => !w.martwy && !(w.zauroczony > 0) && (!wyklucz || wyklucz.indexOf(w) < 0) && Math.hypot(w.x - x, w.y - y) < r)
    .sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y)).slice(0, n);
}
function losowyWrog(x, y, r) { const l = wrogowie.filter(w => !w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - x, w.y - y) < r); return l.length ? losZ(l) : null; }
function najslabszyWrog(x, y, r) { let naj = null; for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - x, w.y - y) > r) continue; if (!naj || w.hp < naj.hp) naj = w; } return naj; }
function policzWrogow(x, y, r) { let n = 0; for (const w of wrogowie) if (!w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - x, w.y - y) < r + w.r) n++; return n; }

function obszarowe(x, y, r, kolor, fn, cichy) {
  r *= mnObszaru();
  if (!cichy) fale.push({ x: x, y: y, czas: 0.3, max: 0.3, r: r, kolor: kolor || '#ffd24a' });
  const n = wrogowie.length;
  for (let i = 0; i < n; i++) { const w = wrogowie[i]; if (!w || w.martwy || w.zauroczony > 0) continue; if (Math.hypot(w.x - x, w.y - y) <= r + w.r * 0.5) fn(w); }
}
function aura(r, kolor, fn, wyrazna) {
  const rr = r * mnObszaru();
  fale.push({ x: gracz.x, y: gracz.y, czas: wyrazna ? 0.35 : 0.5, max: wyrazna ? 0.35 : 0.5, r: rr, kolor: kolor, slaba: !wyrazna, zaGraczem: true });
  const n = wrogowie.length;
  for (let i = 0; i < n; i++) { const w = wrogowie[i]; if (!w || w.martwy || w.zauroczony > 0) continue; if (Math.hypot(w.x - gracz.x, w.y - gracz.y) <= rr + w.r * 0.5) fn(w); }
}
function stozek(k0, zas, pol, kolor, fn) {
  zas *= mnObszaru();
  stozki.push({ x: gracz.x, y: gracz.y, kat: k0, r: zas, pol: pol, czas: 0.4, max: 0.4, kolor: kolor });
  const n = wrogowie.length;
  for (let i = 0; i < n; i++) { const w = wrogowie[i]; if (!w || w.martwy || w.zauroczony > 0) continue; const d = Math.hypot(w.x - gracz.x, w.y - gracz.y);
    if (d <= zas + w.r && roznicaKata(Math.atan2(w.y - gracz.y, w.x - gracz.x), k0) <= pol) fn(w); }
}
function lancuch(zrodlo, cel, obr, typ, ile, zasieg, spadek, zr, bezPierwszego) {
  if (!cel || cel.martwy) return;
  dodajBlyskawice(zrodlo.x, zrodlo.y - 6, cel.x, cel.y, '#9fd8ff'); DZ.piorun();
  if (!bezPierwszego) zadaj(cel, obr, typ, { zr: zr });
  let ogniwo = cel, trafieni = [cel], sila = spadek || 1;
  for (let s = 0; s < ile - 1; s++) {
    let nast = null, najD = zasieg * mnObszaru();
    for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || trafieni.indexOf(w) >= 0) continue; const d = Math.hypot(w.x - ogniwo.x, w.y - ogniwo.y); if (d < najD) { najD = d; nast = w; } }
    if (!nast) break;
    dodajBlyskawice(ogniwo.x, ogniwo.y, nast.x, nast.y, '#9fd8ff');
    zadaj(nast, obr * sila, typ, { zr: zr });
    trafieni.push(nast); ogniwo = nast; sila *= (spadek || 1);
  }
}
function orbitujace(inst, dt, n, r, kolor, obrFn, typ, zr) {
  inst.faza = (inst.faza || 0) + dt * 3.2;
  const rr = r * Math.sqrt(mnObszaru());
  for (let j = 0; j < n; j++) {
    const k = inst.faza + j * Math.PI * 2 / n, x = gracz.x + Math.cos(k) * rr, y = gracz.y + Math.sin(k) * rr;
    orbyRys.push({ x: x, y: y, kolor: kolor, kat: k });
    for (const w of wrogowie) {
      if (w.martwy || w.zauroczony > 0) continue;
      if (Math.hypot(w.x - x, w.y - y) > 14 + w.r) continue;
      const klucz = '_orb' + zr;
      if (w[klucz] && czasGry - w[klucz] < 0.5) continue;
      w[klucz] = czasGry;
      zadaj(w, obrFn(), typ, { zr: zr });
    }
  }
}
function runyWokol(w, obr) {
  efektyCzasowe.push({ wl: gracz, rodzaj: 'runy', cel: w, x: w.x, y: w.y, czas: 0.8, max: 0.8,
    koniec(e) { const x = e.cel && !e.cel.martwy ? e.cel.x : e.x, y = e.cel && !e.cel.martwy ? e.cel.y : e.y;
      for (let n = 0; n < 3; n++) obszarowe(x, y, 85, '#c9a8ff', o => zadaj(o, obr, 'mag', { obszar: true, zr: 'Rzeźbiarz Run' }), n > 0);
      tonSlizg(900, 300, 0.2, 'sawtooth', 0.05); } });
}
function meteoryt(x, y, opozn, r, obr, zr) {
  efektyCzasowe.push({ wl: gracz, rodzaj: 'meteor', x: x, y: y, r: r * mnObszaru(), czas: opozn, max: opozn,
    koniec(e) { DZ.wybuch(); rozbryzg(e.x, e.y, '#ff9a3c', 18); obszarowe(e.x, e.y, r, '#ff7a3c', o => zadaj(o, obr, 'mag', { obszar: true, zr: zr })); } });
}
function opoznione(t, fn) { opoznioneLista.push({ t: t, fn: fn, wl: gracz }); }
function dodajBuff(id, staty, czas) { const b = gracz.buffy[id]; if (b) b.czas = Math.max(b.czas, czas); else { gracz.buffy[id] = { staty: staty, czas: czas }; oznaczStaty(); } }
function skrocCd(sek) {
  gracz.przedmioty.forEach(p => { if (p && p.cd > 0) p.cd = Math.max(0, p.cd - sek); }); gracz.augmenty.forEach(a => { if (a.cd > 0) a.cd = Math.max(0, a.cd - sek); });
  gracz.oreze.forEach(o => { if (o.cd > 0) o.cd = Math.max(0, o.cd - sek); }); if (gracz.umi && gracz.umi.cd > 0) gracz.umi.cd = Math.max(0, gracz.umi.cd - sek * 0.5); if (gracz.umi2 && gracz.umi2.cd > 0) gracz.umi2.cd = Math.max(0, gracz.umi2.cd - sek * 0.5);
}
function wystrzel(o) {
  const k = o.kat !== undefined ? o.kat : kat({ x: o.x, y: o.y }, o.cel);
  pociski.push({ wl: gracz, x: o.x, y: o.y, vx: Math.cos(k) * o.predkosc, vy: Math.sin(k) * o.predkosc, zycie: o.zycie || 1.2, r: o.r || 6, obr: o.obr, typ: o.typ,
    kolor: o.kolor, ksztalt: o.ksztalt || 'kula', zr: o.zr, przebija: o.przebija || 0, trafieni: [], naprowadza: o.naprowadza || 0, cel: o.cel, przedmiot: true,
    wybuch: o.wybuch || null, ogluszy: o.ogluszy || 0, odbicia: o.odbicia || 0, onHit: !!o.onHit, mozeKryt: !!o.mozeKryt, bezSpadku: !!o.bezSpadku, zasiegOdbicia: o.zasiegOdbicia || 0 });
  if (pociski.length > 260) pociski.splice(0, pociski.length - 260);
}
// ---- dodatkowe pomocnicze: cele i obszary ----
function najsilniejszyWrog(x, y, r) { let naj = null; for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - x, w.y - y) > r) continue; if (!naj || w.hp > naj.hp) naj = w; } return naj; }
function najdalszyWrog(x, y, r) { let naj = null, nd = -1; for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0) continue; const d = Math.hypot(w.x - x, w.y - y); if (d < r && d > nd) { nd = d; naj = w; } } return naj; }
// wróg, wokół którego (w promieniu pr) stoi najwięcej innych - dobre miejsce na wybuch
function skupisko(x, y, r, pr) {
  let naj = null, najN = -1;
  const lista = wrogowie.filter(w => !w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - x, w.y - y) < r);
  const probki = lista.length > 24 ? tasuj(lista.slice()).slice(0, 24) : lista;
  for (const a of probki) { let n = 0; for (const b of lista) if (Math.hypot(a.x - b.x, a.y - b.y) < pr) n += b.elita || b.boss ? 3 : 1; if (n > najN) { najN = n; naj = a; } }
  return naj;
}
function liniowe(k0, zas, szer, fn) {
  const cx = Math.cos(k0), cy = Math.sin(k0);
  ciecia.push({ x: gracz.x, y: gracz.y, kat: k0, luk: 0, r: zas, czas: 0.16, max: 0.16, kolor: '#e8e0c8', linia: true });
  wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0) return; const rx = w.x - gracz.x, ry = w.y - gracz.y, wzd = rx * cx + ry * cy, pop = Math.abs(rx * cy - ry * cx);
    if (wzd < -w.r || wzd > zas + w.r || pop > szer + w.r) return; fn(w); });
}
// granat/bomba rzucona przez gracza: leci łukiem i wybucha w punkcie
function granat(x0, y0, x1, y1, r, obr, typ, zr, opozn, ogl) {
  const d = Math.hypot(x1 - x0, y1 - y0), lot = opozn || Math.max(0.25, d / 380);
  efektyCzasowe.push({ wl: gracz, rodzaj: 'granat', x: x1, y: y1, sx: x0, sy: y0, r: r * mnObszaru(), czas: lot, max: lot,
    koniec(e) { DZ.wybuch(); rozbryzg(e.x, e.y, '#ffb070', 20); fale.push({ x: e.x, y: e.y, czas: 0.4, max: 0.4, r: e.r, kolor: '#ffb070' });
      obszarowe(e.x, e.y, r, '#ff9a3c', o => { zadaj(o, obr, typ, { obszar: true, zr: zr }); if (ogl) oglusz(o, ogl, { zrodlo: zr }); }, true); } });
}
// leczenie (i tarcza) dla całej drużyny w promieniu - także dla gracza, który to robi
function leczDruzyne(x, y, r, ile, zSoba, procHp, procTarczy) {
  const z0 = gracz;
  gracze.forEach(p => {
    if (p.powalony || p.martwy || !p._D || (!zSoba && p === z0) || Math.hypot(p.x - x, p.y - y) > r) return;
    kontekst(p);
    const v = (ile || 0) + (procHp || 0) * D.hpMax;
    if (v > 0) { leczGracza(v, 'Leczenie drużyny'); czastkiLeczenia(p.x, p.y); }
    if (procTarczy) dajTarcze(D.hpMax * procTarczy, 4);
  });
  kontekst(z0);
}

// ---------------------------------------------------------------------
//  LECZENIE, TARCZE, OBRAŻENIA GRACZA
// ---------------------------------------------------------------------
function druzyna() { return gracze.length > 1 || (typeof SIEC !== 'undefined' && !!SIEC.rola); }
// Limit wampiryzmu: ułamek maks. zdrowia na sekundę (1% + 0,12% za punkt, maks. 5%; klasa i Kielich podnoszą)
function limitWampiryzmu() { const K = KLASY[gracz.klasa], k = (K.limitWampF ? K.limitWampF(gracz.stanKlasy || {}) : (K.limitWamp || 0)) + (FLAGI.kielich ? 0.02 : 0); return Math.min(0.05 + k, 0.01 + k + 0.0012 * Math.max(0, D.omni)); }
// Każde leczenie zależne od zadanych obrażeń / zabójstw idzie przez ten sam limit
// (zapas = 1 sekunda limitu, odnawia się na bieżąco) — inaczej przy ogromnych obrażeniach nie dało się umrzeć.
function leczWampirem(v, zr) {
  if (!(v > 0) || !gracz || !D) return 0;
  const b = gracz._wampB === undefined ? limitWampiryzmu() * D.hpMax : gracz._wampB;
  const x = Math.min(v, b); gracz._wampB = b - x;
  if (v > x && FLAGI.kielich) nadmiarKielicha(v - x);
  return x > 0 ? leczGracza(x, zr, true) : 0;
}
// Kielich Nadmiaru: wampiryzm ponad limit -> tarcza, a gdy tarcza pełna -> pula wybuchająca co sekundę
function nadmiarKielicha(v) {
  if (fala.bezLeczenia) return;
  const i = gracz.przedmioty.find(p => p && p.id === 'kielich'); if (!i) return;
  const max = D.hpMax * 0.25, ob = tarczaSuma();
  if (ob < max) { const t = Math.min(v, max - ob); dajTarcze(t, 5, true); v -= t; }
  if (v > 0) i.pula = Math.min(D.hpMax * 0.5, (i.pula || 0) + v);
}
// Zmęczenie: od 11. fali każde leczenie słabnie o 2,5% na falę, maks. o połowę (regeneracji nie dotyczy)
function zmeczenie(nr) { return Math.min(0.5, Math.max(0, ((nr || 0) - 10) * 0.025)); }
const BEZ_ZMECZENIA = { 'Regeneracja': 1, 'Kirys Warmoga': 1 };
// Regeneracja bazowa: każda postać sama odzyskuje trochę zdrowia (0,6 + 0,3% maks. zdrowia na sekundę).
// Nie ma już statystyki regeneracji - mnożą ją tylko klasa (Druid więcej, Wampir wcale) i augment Regeneracja.
function regenNaSekunde(hpMax) {
  hpMax = hpMax === undefined ? D.hpMax : hpMax;
  return (0.6 + 0.003 * hpMax) * Math.max(0, mnoznikHakow('mnRegen'));
}
function leczGracza(v, zr, cichy) {
  if (!gracz || gracz.martwy || gracz.powalony || !(v > 0) || stan !== 'walka') return 0;
  if (fala.bezLeczenia) return 0;
  v *= 1 + D.leczenie / 100;
  if (!BEZ_ZMECZENIA[zr]) v *= 1 - zmeczenie(fala.nr) * (KLASY[gracz.klasa].polZmeczenia ? 0.5 : 1);
  const brak = D.hpMax - gracz.hp, real = Math.min(brak, v);
  if (real > 0) { gracz.hp += real; run.leczenie += real; gracz._lecz = (gracz._lecz || 0) + real; const lz = run.leczenieZr || (run.leczenieZr = {}); lz[zr || '?'] = (lz[zr || '?'] || 0) + real; }
  if (v > real + 0.01 && HAKI.naNadleczenie.length) hak('naNadleczenie', v - real);
  return real;
}
function dajTarcze(v, czas, bezMn) {
  if (!(v > 0)) return;
  if (!bezMn) v *= (1 + D.leczenie / 100) * (1 + (FLAGI.mnTarcz || 0));
  gracz.tarcze.push({ v: v, czas: czas, max: czas });
  if (gracz.tarcze.length > 12) gracz.tarcze.shift();
  DZ.tarcza();
}
function tarczaSuma() { let s = 0; gracz.tarcze.forEach(t => s += t.v); return s; }
function pochlonTarcze(v) {
  while (v > 0 && gracz.tarcze.length) { const t = gracz.tarcze[0], p = Math.min(t.v, v); t.v -= p; v -= p; if (t.v <= 0.01) gracz.tarcze.shift(); }
  return v;
}
function spowolnijGracza(proc, czas) {
  if (FLAGI.odpornyNaSpow) return;
  const tw = Math.min(0.8, D.wytrwalosc / 100);
  proc *= 1 - tw; czas *= 1 - tw;
  if (proc >= gracz.spowG) gracz.spowG = proc;
  gracz.spowGCzas = Math.max(gracz.spowGCzas, czas);
}
function zranGracza(v, typ, o) {
  if (!gracz || gracz.martwy || gracz.powalony || stan !== 'walka' || !(v > 0)) return 0;
  o = o || {};
  if (gracz.niewr > 0) return 0;
  if (!o.bezUniku && !o.dot && Math.random() * 100 < Math.min(FLAGI.unikMax || 80, D.unik)) { tekstSwiat(gracz.x, gracz.y - 24, 'unik', '#bfe8ff', 0.6); DZ.unik(); hak('naUniku'); return 0; }
  const przed = v;
  let m = 1;
  if (typ === 'fiz') m *= D.pancerz >= 0 ? 100 / (100 + D.pancerz) : 2 - 100 / (100 - D.pancerz);
  else if (typ === 'mag') m *= D.odpMag >= 0 ? 100 / (100 + D.odpMag) : 2 - 100 / (100 - D.odpMag);
  m *= 1 - Math.min(FLAGI.redukcjaMax || 75, Math.max(0, D.redukcja)) / 100;
  m *= mnoznikHakow('modOtrzymanych', v, typ, o);
  if (fala.mnOtrzymanych) m *= fala.mnOtrzymanych;
  v *= m;
  if (v <= 0) return 0;
  v = pochlonTarcze(v);
  if (v <= 0) { tekstSwiat(gracz.x, gracz.y - 24, '🛡', '#e8f0ff', 0.4); return 0; }
  gracz.hp -= v; gracz.ostTrafienie = czasGry; gracz.migotanie = 0.15;
  const kto = o.kto || (o.wrog ? o.wrog.n + (o.wrog.elita ? ' (elita)' : '') : (o.wybuch ? 'Wybuch' : (o.odbicie ? 'Odbicie' : '?')));
  (run.ostTrafienia || (run.ostTrafienia = [])).push(kto + ' ' + Math.round(v)); if (run.ostTrafienia.length > 10) run.ostTrafienia.shift();
  run.otrzymaneOd = run.otrzymaneOd || {}; run.otrzymaneOd[kto.replace(' (elita)', '')] = (run.otrzymaneOd[kto.replace(' (elita)', '')] || 0) + v;
  run.przyjete += v; run.trafienia++; run.trafFali = (run.trafFali || 0) + 1; fala.trafienia = (fala.trafienia || 0) + 1;
  gracz._obr = (gracz._obr || 0) + v;
  if (o.wrog && o.wrog.afiksy && o.wrog.afiksy.indexOf('wampir') >= 0) o.wrog.hp = Math.min(o.wrog.hpMax, o.wrog.hp + v * 0.4 * (o.wrog.rany > 0 ? 0.4 : 1));
  DZ.obrazenia();
  o.przed = przed;
  if (!o.odbicie) hak('naOtrzymanie', v, typ, o);
  if (fala.proba && fala.proba.id === 'taniec' && !o.dot) { const z = Math.floor(gracz.zloto * 0.05); gracz.zloto -= z; }
  if (gracz.hp <= 0) {
    let uratowana = false;
    for (const h of HAKI.naSmierc) { try { if (h[0].naSmierc(h[1])) { uratowana = true; break; } } catch (e) { zglosBlad(e, 'naSmierc'); } }
    if (!uratowana) { if (druzyna()) powalGracza(); else smiercGracza(); }
  }
  return v;
}
// ---- DRUŻYNA: powalenie i podnoszenie ----
function powalGracza() {
  gracz.powalony = true; gracz.hp = 0; gracz.reanim = 0; gracz.tarcze = [];
  rozbryzg(gracz.x, gracz.y, '#c0392b', 24); DZ.smierc();
  const imie = gracz.nick || KLASY[gracz.klasa].n;
  baner('💀 ' + imie + ' pada!', zywiGracze().length ? 'Stań obok przez 3 s, żeby podnieść' : '');
  if (!zywiGracze().length) koniecDruzyny();
}
const CZAS_PODNOSZENIA = 3;
function aktualizujPodnoszenie(dt) {
  for (const p of gracze) {
    if (!p.powalony) continue;
    let ilu = 0;
    for (const q of gracze) if (q !== p && !q.powalony && Math.hypot(q.x - p.x, q.y - p.y) < 52) ilu++;
    if (ilu) p.reanim = (p.reanim || 0) + dt * (1 + 0.5 * (ilu - 1));
    else p.reanim = Math.max(0, (p.reanim || 0) - dt * 0.5);
    if (p.reanim >= CZAS_PODNOSZENIA) {
      const z = gracz; kontekst(p);
      p.powalony = false; p.reanim = 0; p.hp = D.hpMax * 0.35; p.niewr = 1.5;
      tekstSwiat(p.x, p.y - 30, '💚 Wstaje!', '#7ee87a', 1.2, 15); DZ.mikstura();
      kontekst(z);
    }
  }
}

// ---------------------------------------------------------------------
//  ŁUPY: doświadczenie, złoto, skrzynie
// ---------------------------------------------------------------------
let NR_LUPU = 0;     // każda kulka i moneta ma swój numer (gra online: klient zgłasza, co zebrał)
function rozsypKulki(x, y, xp) {
  const n = ogr(Math.round(xp / 1.5), 1, 8), na = xp / n;
  for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), v = losowo(40, 140); kulki.push({ id: ++NR_LUPU, x: x, y: y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, xp: na, faza: losowo(0, 6), opozn: 0.25 }); }
  while (kulki.length > 160) { const a = kulki.shift(), b = kulki[0]; b.xp += a.xp; }
}
// ---- ZŁOTO I SKRZYNIE NA FALĘ ----
// Złoto nie zależy od liczby wrogów: na każdą falę jest PULA złota z wrogów (70%) i stała nagroda
// za przetrwanie (30%). Po wyczerpaniu puli wrogowie sypią już tylko okruchy (10% wartości).
function zlotoNaFale(nr) { return (25 + 20 * Math.max(1, nr || 1)) * (TRUDNOSCI[run.trudnosc].zloto || 1); }
function pulaZlotaFali(nr) { return 0.7 * zlotoNaFale(nr); }
// Skrzynie: na falę od–do (minimum dostajesz po fali, nawet jeśli nic nie wypadło; więcej niż maksimum nie wypadnie)
function zakresSkrzyn(nr) { return [nr >= 3 && !czyFalaBossa(nr) ? 1 : 0, 2 + Math.floor(nr / 12)]; }
function rozsypMonety(x, y, v, pozaPula) {
  const T = TRUDNOSCI[run.trudnosc];
  v *= (T.zloto || 1) * 1.3;
  if (!pozaPula && fala && fala.aktywna) {
    const B = pulaZlotaFali(fala.nr), juz = fala.zlotoZWrogow || 0;
    const wPuli = Math.max(0, Math.min(v, B - juz));
    fala.zlotoZWrogow = juz + wPuli;
    v = wPuli + (v - wPuli) * 0.1;
  }
  if (!(v > 0.05)) return;
  let n = ogr(Math.round(v), 1, 6);
  const na = v / n;
  for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), s = losowo(30, 120); monety.push({ id: ++NR_LUPU, x: x, y: y, vx: Math.cos(k) * s, vy: Math.sin(k) * s, v: na, faza: losowo(0, 6), opozn: 0.3 }); }
  while (monety.length > 140) { const a = monety.shift(), b = monety[0]; b.v += a.v; }
}
function dodajXp(v) {
  v *= (1 + D.xpBonus / 100) * (fala.mnXp || 1) * (HAKI.mnXp.length ? mnoznikHakow('mnXp') : 1);
  gracz.xp += v; run.xp += v;
  while (gracz.xp >= gracz.xpNast) {
    gracz.xp -= gracz.xpNast; gracz.poziom++; gracz.doWyboru++;
    gracz.xpNast = xpDoPoziomu(gracz.poziom);
    { const K = KLASY[gracz.klasa]; if (K.wyborCo && gracz.poziom % K.wyborCo() === 0) gracz.darmoweWybory++; }
    gracz.blysk = 1.2; DZ.awans(); oznaczStaty();
    dziennik('⭐ Poziom ' + gracz.poziom + '! Wybierzesz ulepszenie po fali.');
    if (HAKI.naAwans.length) { zastosujStaty(); hak('naAwans'); }
  }
}
function dodajZloto(v, bezMn, opis) {
  if (!(v > 0)) return;
  if (!bezMn) v *= (1 + D.chciwosc / 100) * (fala.mnZlota || 1) * (HAKI.mnZlota.length ? mnoznikHakow('mnZlota') : 1);
  gracz.zloto += v; run.zloto += v; run.zlotoFali = (run.zlotoFali || 0) + v;
  if (opis) dziennik('💰 ' + opis + ': +' + Math.floor(v));
}
// zebranie łupu (wspólne dla drużyny). Klient online zgłasza zebrane kulki/monety po numerze.
function zbierzKulke(i) { const k = kulki[i]; if (!k) return; kulki.splice(i, 1); const xp = k.xp; dlaKazdego(() => dodajXp(xp)); DZ.kulka(); }
function zbierzMonete(i) {
  const m = monety[i]; if (!m) return; monety.splice(i, 1);
  // złoto jest wspólne: każdy dostaje pełną wartość monety razy SWOJE premie (zysk złota, Midas…)
  const v = m.v; dlaKazdego(q => { const mn = mnoznikHakow('mnozMonety'); if (mn > 1) tekstSwiat(q.x, q.y - 28, '🪙 ×' + mn, '#ffd24a', 0.8); dodajZloto(v * mn); });
  DZ.moneta();
}
function zbierzLupPoId(id) {
  let i = kulki.findIndex(k => k.id === id); if (i >= 0) { zbierzKulke(i); return; }
  i = monety.findIndex(m => m.id === id); if (i >= 0) zbierzMonete(i);
}
function przyciagnijLupy() {
  kulki.forEach(k => k.ssij = true); monety.forEach(m => m.ssij = true);
  if (typeof SIEC !== 'undefined' && SIEC.rola === 'host') siecZdarzenie(['ssij']);
}
function tierSkrzyni(w) {
  if (w && w.boss) return fala.nr < 10 ? 2 : 3;
  const L = 1 + D.szczescie / 100, nr = fala.nr;
  const p3 = Math.min(0.12, Math.max(0, (nr - 8) * 0.008)) * L, p2 = Math.min(0.3, Math.max(0, (nr - 3) * 0.02)) * L, p1 = Math.min(0.55, 0.15 + nr * 0.025) * L;
  const r = Math.random() * (w && w.elita ? 0.7 : 1);
  if (r < p3) return 3; if (r < p3 + p2) return 2; if (r < p3 + p2 + p1) return 1; return 0;
}
// Łupy są wspólne: to, co ktoś podniesie, dostaje każdy z drużyny (każdy z własnymi premiami).
function zbieracz(x, y, dt, l) {
  let naj = null, nd = Infinity;
  for (const p of gracze) { if (p.powalony || p.martwy || !p._D) continue; const d = Math.hypot(p.x - x, p.y - y); if (d < nd) { nd = d; naj = p; } }
  return [naj, nd];
}
function aktualizujLupy(dt) {
  if (!zywiGracze().length) return;
  const z0 = gracz;
  for (let i = kulki.length - 1; i >= 0; i--) {
    const k = kulki[i]; k.faza += dt * 6; if (k.opozn > 0) k.opozn -= dt;
    const [p, d] = zbieracz(k.x, k.y); if (!p) break;
    const zb = p._D.zbieranie, dx = p.x - k.x, dy = p.y - k.y, dd = d || 1;
    if (k.opozn <= 0 && (d < zb || k.ssij)) { const s = 140 + Math.max(0, zb - d) * 6 + (k.ssij ? 600 : 0); k.vx += dx / dd * s * dt; k.vy += dy / dd * s * dt; }
    k.vx *= 0.92; k.vy *= 0.92; k.x += k.vx * dt; k.y += k.vy * dt;
    if (d < 16) zbierzKulke(i);
  }
  for (let i = monety.length - 1; i >= 0; i--) {
    const m = monety[i]; m.faza += dt * 5; if (m.opozn > 0) m.opozn -= dt;
    const [p, d] = zbieracz(m.x, m.y); if (!p) break;
    const zb = p._D.zbieranie, dx = p.x - m.x, dy = p.y - m.y, dd = d || 1;
    if (m.opozn <= 0 && (d < zb || m.ssij)) { const s = 140 + Math.max(0, zb - d) * 6 + (m.ssij ? 600 : 0); m.vx += dx / dd * s * dt; m.vy += dy / dd * s * dt; }
    m.vx *= 0.92; m.vy *= 0.92; m.x += m.vx * dt; m.y += m.vy * dt;
    if (d < 16) zbierzMonete(i);
  }
  for (let i = skrzynieNaZiemi.length - 1; i >= 0; i--) {
    const s = skrzynieNaZiemi[i]; s.faza += dt;
    const [p, d] = zbieracz(s.x, s.y);
    if (p && d < 30 + p.r) {
      dlaKazdego(q => {
        q.skrzynie.push({ tier: s.tier, boss: s.boss }); run.skrzynieLacznie = (run.skrzynieLacznie || 0) + 1;
        dziennik('📦 Skrzynia (' + TIERY[s.tier].nazwaZ.toLowerCase() + ') — otworzysz ją po fali');
      });
      DZ.skrzynia(); skrzynieNaZiemi.splice(i, 1);
    }
  }
  kontekst(z0);
}

// ---------------------------------------------------------------------
//  RUCH I AKTUALIZACJA GRACZA
// ---------------------------------------------------------------------
let joy = { aktywny: false, x: 0, y: 0 }, klawisze = {};
function scianaBlokuje(x0, y0, x1, y1, r) {
  for (const sc of scianyMagiczne) { const d1 = odlDoOdcinka(x1, y1, sc); if (d1 < r + sc.grubosc / 2 && d1 < odlDoOdcinka(x0, y0, sc)) return true; }
  return false;
}
function odlDoOdcinka(px, py, sc) {
  const dx = sc.x2 - sc.x1, dy = sc.y2 - sc.y1, l2 = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((px - sc.x1) * dx + (py - sc.y1) * dy) / l2));
  return Math.hypot(px - (sc.x1 + t * dx), py - (sc.y1 + t * dy));
}
// Kierunek ruchu z drążka/klawiatury (lub bota w testach)
function wejscieRuchu() {
  let mx = 0, my = 0;
  if (joy.aktywny) { const dl = Math.hypot(joy.x, joy.y); if (dl > 7) { const s = Math.min(1, dl / 52); mx = joy.x / dl * s; my = joy.y / dl * s; } }
  if (klawisze.l) mx -= 1; if (klawisze.p) mx += 1; if (klawisze.g) my -= 1; if (klawisze.d) my += 1;
  if (PAD.mx || PAD.my) { mx += PAD.mx; my += PAD.my; }   // pad (src/14_pad.js)
  if (MYSZ.aktywna) { const k = kierunekMyszy(); if (k) { const s = Math.min(1, k[2] / 36); mx += k[0] * s; my += k[1] * s; } }   // komputer: lewy przycisk myszy
  if (gracz.botFn) { const b = gracz.botFn(); mx = b.x; my = b.y; }
  else if (window.__bot) { const b = window.__bot(); mx = b.x; my = b.y; }
  const dl = Math.hypot(mx, my); if (dl > 1) { mx /= dl; my /= dl; }
  return [mx, my];
}
// Ruch postaci (używany też przez klienta gry online - sam rusza swoją postacią)
function ruszGracza(dt, ms, roz) {
  if (gracz.dash && gracz.dash.t > 0) {
    const d = gracz.dash, k = Math.min(dt, d.t); d.t -= dt;
    gracz.x = ogr(gracz.x + d.vx * k, POD_MIN, POD_MAX); gracz.y = ogr(gracz.y + d.vy * k, POD_MIN, POD_MAX); gracz.wRuchu = true;
    if (d.t <= 0) gracz.dash = null;
    return;
  }
  const [mx, my] = wejscieRuchu();
  gracz.wRuchu = false;
  if (gracz.zastoj <= 0 && !(gracz.korzen > 0) && (mx || my)) {
    const v = ms * (1 - Math.min(0.8, gracz.spowG)) * dt;
    const nx = ogr(gracz.x + mx * v, POD_MIN, POD_MAX), ny = ogr(gracz.y + my * v, POD_MIN, POD_MAX);
    const r = gracz.r * roz;
    if (!scianaBlokuje(gracz.x, gracz.y, nx, gracz.y, r)) gracz.x = nx;
    if (!scianaBlokuje(gracz.x, gracz.y, gracz.x, ny, r)) gracz.y = ny;
    gracz.wRuchu = true;
    if (Math.abs(mx) > 0.2) gracz.kierX = mx;
    gracz.kierRX = mx; gracz.kierRY = my;
  }
  // wiry przyciągają
  for (const wr of wiry) {
    if (wr.rozruch > 0) continue;
    const dx = wr.x - gracz.x, dy = wr.y - gracz.y, d = Math.hypot(dx, dy);
    if (d < wr.r && d > 2) { const c = (30 + (1 - d / wr.r) * 40) * dt; gracz.x += dx / d * c; gracz.y += dy / d * c; }
  }
}
function aktualizujGracza(dt) {
  if (gracz.niewr > 0) gracz.niewr -= dt;
  { const lim = limitWampiryzmu() * D.hpMax; gracz._wampB = Math.min(lim, (gracz._wampB === undefined ? lim : gracz._wampB) + lim * dt); }
  if (gracz.zastoj > 0) gracz.zastoj -= dt;
  if (gracz.migotanie > 0) gracz.migotanie -= dt;
  if (gracz.blysk > 0) gracz.blysk -= dt;
  if (gracz.naladowanyBlysk > 0) gracz.naladowanyBlysk -= dt;
  if (gracz.korzen > 0) gracz.korzen -= dt;
  if (gracz.niewidzialny > 0) gracz.niewidzialny -= dt;
  if (gracz.forma && gracz.formaDo <= czasGry) gracz.forma = null;
  for (const id in gracz.buffy) { const b = gracz.buffy[id]; b.czas -= dt; if (b.czas <= 0) { delete gracz.buffy[id]; oznaczStaty(); } }
  for (let i = gracz.tarcze.length - 1; i >= 0; i--) { const t = gracz.tarcze[i]; t.czas -= dt; if (t.czas <= 0) { gracz.tarcze.splice(i, 1); if (t.wybuch && t.v > 1) { const v = t.v; aura(150, '#ff9ae0', w => zadaj(w, v, 'mag', { obszar: true, zr: 'Pryzmatyczna tarcza' }), true); } } }
  if (gracz.spowGCzas > 0) { gracz.spowGCzas -= dt; if (gracz.spowGCzas <= 0) gracz.spowG = 0; }
  if (gracz.hp < D.hpMax) { const reg = regenNaSekunde(); if (reg > 0) leczGracza(reg * dt, 'Regeneracja', true); }
  // ruch: lokalny gracz steruje sam, zdalnego ustawia sieć
  if (gracz.zdalny) {
    if (gracz.netX !== undefined) {
      const nx = ogr(gracz.netX, POD_MIN, POD_MAX), ny = ogr(gracz.netY, POD_MIN, POD_MAX);
      const wiek = Math.min(0.12, Math.max(0, (performance.now() - (gracz.netT || 0)) / 1000) + (gracz.opoz || 0));
      let tx = ogr(nx + (gracz.netVX || 0) * wiek, POD_MIN, POD_MAX), ty = ogr(ny + (gracz.netVY || 0) * wiek, POD_MIN, POD_MAX);
      if ((tx !== nx || ty !== ny) && scianaBlokuje(nx, ny, tx, ty, gracz.r)) { tx = nx; ty = ny; }
      gracz.wRuchu = Math.hypot(gracz.netVX || 0, gracz.netVY || 0) > 8;
      gracz.x = tx; gracz.y = ty;
      if (gracz.netKX) gracz.kierX = gracz.netKX;
    }
  } else ruszGracza(dt, D.ms, rozmiarGracza());
  energiaZRuchu();
  // wiry ranią
  for (const wr of wiry) {
    if (wr.rozruch > 0) continue;
    const d = Math.hypot(wr.x - gracz.x, wr.y - gracz.y);
    wr.tyki = wr.tyki || {};
    const kl = gracz.id || 0;
    wr.tyki[kl] = (wr.tyki[kl] || 0) - dt;
    if (d < 26 && wr.tyki[kl] <= 0) { wr.tyki[kl] = 0.6; zranGracza(wr.atak * 0.5, 'mag', { dot: true, kto: 'Wir' }); }
  }
  aktualizujBronie(dt);
  // odnowienia (Kryształ Czasu: 2× szybciej poniżej połowy zdrowia)
  const dtCd = dt * (FLAGI.krysztalCzasu && gracz.hp < D.hpMax * 0.5 ? 2 : 1);
  gracz.przedmioty.forEach(p => { if (p && p.cd > 0) p.cd -= dtCd; });
  gracz.augmenty.forEach(a => { if (a.cd > 0) a.cd -= dtCd; });
  if (gracz.umi.cd > 0) gracz.umi.cd -= dtCd; if (gracz.umi2 && gracz.umi2.cd > 0) gracz.umi2.cd -= dtCd;
  aktualizujOreze(dt, dtCd);
  hak('tik', dt);
  // zbiorcze liczby leczenia i obrażeń nad postacią
  gracz._tTxt = (gracz._tTxt || 0) + dt;
  if (gracz._tTxt > 0.45) {
    gracz._tTxt = 0;
    if (gracz._lecz >= 1) tekstSwiat(gracz.x + 14, gracz.y - 30, '+' + Math.round(gracz._lecz), '#7ec98a', 0.7, 12);
    if (gracz._obr >= 1) tekstSwiat(gracz.x - 14, gracz.y - 30, '−' + Math.round(gracz._obr), '#ff6a5a', 0.7, 13);
    gracz._lecz = 0; gracz._obr = 0;
  }
}

// Bronie dodatkowe: odnowienia i ich efekty (osobno, żeby działało "Echo arsenału")
function aktualizujOreze(dt, dtCd) {
  for (const o of gracz.oreze) {
    if (o.cd > 0) o.cd -= dtCd;
    const d = DEF_ORE[o.id]; if (!d || !d.tik) continue;
    const gotowa = !(o.cd > 0);
    try { d.tik(o, dt); } catch (e) { zglosBlad(e, 'oreze ' + o.id); }
    if (gotowa && o.cd > 0 && FLAGI.echoOreza && d.cd && Math.random() < FLAGI.echoOreza) {
      opoznione(0.3, () => { if (stan !== 'walka') return; const c = o.cd, cm = o.cdMax; o.cd = 0; try { d.tik(o, 0); } catch (e) {} o.cd = c; o.cdMax = cm; });
    }
  }
}
// ---- UMIEJĘTNOŚĆ AKTYWNA postaci ----
// moc umiejętności: premia klasy/przedmiotów + co 3 poziomy postaci +4% (bez limitu)
function premiaPoziomuUmi(p) { return 0.04 * Math.floor(((p || gracz).poziom || 1) / 3); }
function mnUmi() { return 1 + (FLAGI.mnUmi || 0) + premiaPoziomuUmi(); }
// odnowienie umiejętności: bazowe (może zależeć od ewolucji) i po przyspieszeniu
function cdBazoweUmi(U) { return typeof U.cd === 'function' ? U.cd() : (U.cd || 0); }
function cdUmiTeraz(U) { return cdBazoweUmi(U) * Math.max(0.25, 1 - (FLAGI.cdUmi || 0)) * 100 / (100 + Math.max(0, D ? D.haste : 0)); }
// ranga ewolucji (0–3) gałęzi bieżącej postaci
function ewo(id) { return (gracz && gracz.ewo && gracz.ewo[id]) || 0; }
// Umiejętności postaci: nr 1 (każda postać) i nr 2 (tylko niektóre). Przełącznik (przelacz) włącza/wyłącza efekt.
function umiPostaci(nr) { const K = KLASY[gracz.klasa]; return nr === 2 ? K.umi2 : K.umi; }
function czyUmiAktywna(nr) {
  if (typeof SIEC !== 'undefined' && SIEC.rola === 'klient' && !gracz.zdalny) return !!(SIEC.umiAkt && SIEC.umiAkt[nr - 1]);
  const U = umiPostaci(nr); return !!(U && U.aktywna && U.aktywna(gracz.stanKlasy || {}));
}
function stanUmi(nr) { if (nr === 2) return gracz.umi2 || (gracz.umi2 = { cd: 0, cdMax: 0 }); return gracz.umi; }
// Auto-użycie: umiejętności z „auto” (Farmer) zawsze, a pozostałe, gdy gracz włączył 🤖 (tylko na swoim urządzeniu)
function autoUmiejetnosci(p, lokalnie) {
  if (!p || p.powalony || p.martwy || stan !== 'walka' || !fala.aktywna) return;
  for (const nr of [1, 2]) {
    const U = umiPostaci(nr); if (!U || U.pasywna || U.przelacz) continue;
    const st = stanUmi(nr); if (st.cd > 0) continue;
    const chce = U.auto ? SIEC.rola !== 'klient' : !!(lokalnie && p.autoUmi && p.autoUmi[nr]);   // „auto” u klienta robi gospodarz
    if (!chce || (p._autoT && czasGry - p._autoT < 0.25)) continue;                                // przy braku celu nie co klatkę
    if (!uzyjUmiejetnosci(nr, true)) p._autoT = czasGry;
  }
}
function uzyjUmiejetnosci(nr, cicho) {
  nr = nr === 2 ? 2 : 1;
  if (stan !== 'walka' || !gracz || gracz.martwy || gracz.powalony || gracz.zastoj > 0) return false;
  const U = umiPostaci(nr), st = stanUmi(nr); if (!U) return false;
  if (U.pasywna) { if (!gracz.zdalny && U.podpowiedz && !cicho) toast(U.ik + ' ' + U.podpowiedz); return false; }
  if (SIEC.rola === 'klient') { if (st.cd > 0) return false; siecWyslijHost({ t: 'umi', n: nr, k: [Math.round((gracz.kierRX || gracz.kierX || 1) * 100) / 100, Math.round((gracz.kierRY || 0) * 100) / 100] }); st.cd = 0.5; return true; }
  if (st.cd > 0) return false;
  let ok = false;
  try { ok = U.uzyj(mnUmi()) !== false; } catch (e) { zglosBlad(e, 'umiejetnosc ' + gracz.klasa + ' ' + nr); }
  if (!ok) { if (!gracz.zdalny && !U.przelacz && !cicho) toast(U.ik + ' ' + (U.brak || 'Brak celu w pobliżu')); return false; }
  st.cdMax = U.przelacz ? 0.6 : cdUmiTeraz(U);
  st.cd = st.cdMax;
  if (gracz.stanKlasy.natychmiast === nr) { gracz.stanKlasy.natychmiast = 0; st.cd = 0.4; }
  if (!U.przelacz) tekstSwiat(gracz.x, gracz.y - 34, U.ik + ' ' + U.n, '#ffe08a', 1, 13);
  hak('naUmiejetnosci');
  return true;
}
// mignięcie (np. Mag): szybki doskok w kierunku ruchu (u gracza online - przez zdarzenie u niego)
function mrugnij(dl) {
  let mx = gracz.kierRX || gracz.kierX || 1, my = gracz.kierRY || 0;
  if (gracz.zdalny && gracz.umiKier) { mx = gracz.umiKier[0] || mx; my = gracz.umiKier[1] || my; }
  const n = Math.hypot(mx, my) || 1; mx /= n; my /= n;
  gracz.niewr = Math.max(gracz.niewr, 0.3);
  if (gracz.zdalny) siecZdarzenieGracza(gracz, ['dash', Math.round(mx * 100), Math.round(my * 100), dl]);
  else gracz.dash = { vx: mx * dl / 0.12, vy: my * dl / 0.12, t: 0.12 };
}
// Szarża (Rycerz): obrażenia od razu na linii, ruch postaci rozłożony na chwilę
function szarza(dl, obr, ogl, zr) {
  let mx = gracz.kierRX || gracz.kierX || 1, my = gracz.kierRY || 0;
  if (gracz.zdalny && gracz.umiKier) { mx = gracz.umiKier[0] || mx; my = gracz.umiKier[1] || my; }
  const n = Math.hypot(mx, my) || 1; mx /= n; my /= n;
  const k0 = Math.atan2(my, mx);
  liniowe(k0, dl, 26, w => { zadaj(w, obr, 'fiz', { zr: zr }); oglusz(w, ogl, { zrodlo: zr }); odrzuc(w, 25); });
  gracz.niewr = Math.max(gracz.niewr, 0.35);
  if (gracz.zdalny) siecZdarzenieGracza(gracz, ['dash', Math.round(mx * 100), Math.round(my * 100), dl]);
  else gracz.dash = { vx: mx * dl / 0.2, vy: my * dl / 0.2, t: 0.2 };
  DZ.ciecie();
}

function aktualizujPociski(dt) {
  const z0 = gracz;
  // pociski graczy
  for (let i = pociski.length - 1; i >= 0; i--) {
    const p = pociski[i];
    if (p.wl) kontekst(p.wl);
    if (p.naprowadza && p.cel && !p.cel.martwy) {
      const kk = Math.atan2(p.cel.y - p.y, p.cel.x - p.x), v = Math.hypot(p.vx, p.vy); let ka = Math.atan2(p.vy, p.vx);
      let r = ((kk - ka + Math.PI * 3) % (Math.PI * 2)) - Math.PI; ka += ogr(r, -p.naprowadza * dt, p.naprowadza * dt);
      p.vx = Math.cos(ka) * v; p.vy = Math.sin(ka) * v;
    }
    if (p.bumerang) {
      p.obrot += dt * 18;
      if (!p.wraca) { p.droga += Math.hypot(p.vx, p.vy) * dt; if (p.droga >= p.maxDroga) { p.wraca = true; p.trafieni = []; } }
      else { const k = Math.atan2(gracz.y - p.y, gracz.x - p.x); p.vx = Math.cos(k) * 440; p.vy = Math.sin(k) * 440; if (Math.hypot(gracz.x - p.x, gracz.y - p.y) < 18) { pociski.splice(i, 1); continue; } }
    }
    p.x += p.vx * dt; p.y += p.vy * dt; p.zycie -= dt;
    if (p.granat) { if (p.zycie <= 0) { pociski.splice(i, 1); wybuchGranatu(p); } continue; }   // granat leci nad wrogami
    if (p.zycie <= 0 || p.x < MUR * KAFEL - 20 || p.y < MUR * KAFEL - 20 || p.x > (ARENA - MUR) * KAFEL + 20 || p.y > (ARENA - MUR) * KAFEL + 20) { pociski.splice(i, 1); continue; }
    if (scianyMagiczne.length && scianyMagiczne.some(sc => odlDoOdcinka(p.x, p.y, sc) < sc.grubosc / 2 + 3)) { pociski.splice(i, 1); continue; }
    let usun = false;
    for (let j = 0; j < wrogowie.length; j++) {
      const w = wrogowie[j];
      if (w.martwy || w.zauroczony > 0 || p.trafieni.indexOf(w) >= 0) continue;
      if (Math.abs(w.x - p.x) > w.r + p.r + 4 || Math.abs(w.y - p.y) > w.r + p.r + 4) continue;
      if (Math.hypot(w.x - p.x, w.y - p.y) > w.r + p.r) continue;
      p.trafieni.push(w);
      if (p.przedmiot) { const kr = p.mozeKryt && Math.random() * 100 < D.kryt; const z = zadaj(w, p.obr * (kr ? kryt2() : 1), p.typ, { zr: p.zr, pocisk: true, kryt: kr }); if (p.ogluszy) oglusz(w, p.ogluszy, { zrodlo: p.zr });
        if (p.onHit && gracz.bronie[0] && !w.martwy) zastosujOnHit(w, gracz.bronie[0], { k: { bron: gracz.bronie[0], kryt: kr, glowny: false, zadane: z, zadaneSurowe: p.obr, bazowe: p.obr, licznikCiosu: 1 } }); }
      else trafienieAtakiem(w, p.bron, { mn: p.mn, glowny: p.glowny !== false, pocisk: true, pewnyKryt: p.pewnyKryt, naladowany: !!p.naladowany && p.trafieni.length === 1 });
      if (p.wl) kontekst(p.wl);
      if (p.wybuch) { const wb = p.wybuch, zr = p.zr; fale.push({ x: p.x, y: p.y, czas: 0.3, max: 0.3, r: wb.r * mnObszaru(), kolor: p.kolor }); obszarowe(p.x, p.y, wb.r, p.kolor, o => { if (o !== w) zadaj(o, wb.obr, p.typ, { obszar: true, zr: zr }); if (wb.podpal) podpal(o, wb.podpal, 3, 'mag', zr); }, true); if (wb.podpal) podpal(w, wb.podpal, 3, 'mag', zr); pociski.splice(i, 1); usun = false; break; }
      if (p.bumerang) continue;
      if (p.odbicia > 0) {
        p.odbicia--; const nast = najblizszyWrog(p.x, p.y, p.zasiegOdbicia || 220, p.trafieni);
        if (nast) { const k = Math.atan2(nast.y - p.y, nast.x - p.x), v = Math.hypot(p.vx, p.vy); p.vx = Math.cos(k) * v; p.vy = Math.sin(k) * v; p.cel = nast; p.naprowadza = Math.max(p.naprowadza || 0, 8); p.zycie = Math.max(p.zycie, 0.8); if (!p.bezSpadku) p.mn = (p.mn || 1) * 0.8; continue; }
      }
      if (p.przebija > 0) { p.przebija--; continue; }
      usun = true; break;
    }
    if (usun) pociski.splice(i, 1);
  }
  // pociski wrogów - trafiają pierwszego gracza na drodze
  for (let i = pociskiWrogow.length - 1; i >= 0; i--) {
    const p = pociskiWrogow[i];
    p.x += p.vx * dt; p.y += p.vy * dt; p.zycie -= dt;
    if (p.zycie <= 0 || p.x < MUR * KAFEL - 30 || p.y < MUR * KAFEL - 30 || p.x > (ARENA - MUR) * KAFEL + 30 || p.y > (ARENA - MUR) * KAFEL + 30) { pociskiWrogow.splice(i, 1); continue; }
    for (const g of gracze) {
      if (g.powalony || g.martwy || !g._D) continue;
      kontekst(g);
      if (Math.hypot(p.x - g.x, p.y - g.y) < g.r * rozmiarGracza() * (g.zdalny ? 0.7 : 1) + (p.r || 5)) {
        if (HAKI.odbijPocisk.length && ktorysHak('odbijPocisk')) {
          // Lusterko: pocisk wraca do strzelca jako nasz
          pociskiWrogow.splice(i, 1); tekstSwiat(g.x, g.y - 24, '🪞', '#bfe8ff', 0.5);
          wystrzel({ x: p.x, y: p.y, kat: Math.atan2(-p.vy, -p.vx), predkosc: Math.hypot(p.vx, p.vy) * 1.2, obr: p.obr * 2, typ: p.typ || 'fiz', kolor: '#bfe8ff', ksztalt: 'kula', zr: 'Lusterko', zycie: 1.5, cel: p.wrog && !p.wrog.martwy ? p.wrog : null, naprowadza: p.wrog ? 6 : 0 });
          break;
        }
        zranGracza(p.obr, p.typ || 'fiz', { wrog: p.wrog && !p.wrog.martwy ? p.wrog : null, pocisk: true, kto: p.kto });
        if (p.siec) spowolnijGracza(0.45, 1.2);
        pociskiWrogow.splice(i, 1); break;
      }
    }
  }
  kontekst(z0);
}

function aktualizujPlansze(dt) {
  const z0 = gracz;
  for (let i = kaluze.length - 1; i >= 0; i--) {
    const k = kaluze[i]; k.czas -= dt; k.tyk -= dt;
    if (k.tyk <= 0) {
      let ktos = false;
      for (const g of gracze) {
        if (g.powalony || g.martwy || !g._D) continue;
        if (Math.hypot(g.x - k.x, g.y - k.y) < k.r + g.r * 0.6) { kontekst(g); zranGracza(k.obr, k.typ, { dot: true, bezUniku: true, kto: k.rodzaj === 'gaz' ? 'Gaz' : 'Ogień na ziemi' }); ktos = true; }
      }
      if (ktos) k.tyk = 0.5;
    }
    if (k.czas <= 0) kaluze.splice(i, 1);
  }
  for (let i = polaEfektow.length - 1; i >= 0; i--) {
    const p = polaEfektow[i]; p.czas -= dt; p.tyk -= dt;
    if (p.wl) kontekst(p.wl);
    const rani = p.tyk <= 0; if (rani) p.tyk = 0.5;
    const n = wrogowie.length;
    for (let j = 0; j < n; j++) { const w = wrogowie[j]; if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - p.x, w.y - p.y) > p.r + w.r * 0.5) continue; if (p.rodzaj === 'mroz') spowolnij(w, 0.3, 0.4); if (p.spow) spowolnij(w, p.spow, 0.4); if (p.krusz) w.krusz = Math.max(w.krusz || 0, p.krusz);
      if (rani) { zadaj(w, p.obr, 'mag', { dot: true, obszar: true, zr: p.zr }); if (p.rodzaj === 'kwas') w.krusz = Math.max(w.krusz || 0, 0.15); else if (p.rodzaj === 'ogien') podpal(w, p.obr * 0.3, 1.5, 'mag', p.zr); } }
    if (rani && p.lecz) leczDruzyne(p.x, p.y, p.r, 0, true, p.lecz * 0.5);
    if (p.czas <= 0) polaEfektow.splice(i, 1);
  }
  for (let i = wiry.length - 1; i >= 0; i--) { const wr = wiry[i]; wr.czas -= dt; wr.faza += dt * 5; if (wr.rozruch > 0) wr.rozruch -= dt; if (wr.czas <= 0) wiry.splice(i, 1); }
  for (let i = scianyMagiczne.length - 1; i >= 0; i--) { scianyMagiczne[i].czas -= dt; if (scianyMagiczne[i].czas <= 0) scianyMagiczne.splice(i, 1); }
  for (let i = bomby.length - 1; i >= 0; i--) { bomby[i].lont -= dt; if (bomby[i].lont <= 0) wybuchBomby(bomby.splice(i, 1)[0]); }
  for (let i = uderzeniaBossa.length - 1; i >= 0; i--) {
    const u = uderzeniaBossa[i]; u.czas += dt;
    if (u.sledz && !u.sledz.martwy && !u.zadane) { u.x = u.sledz.x; u.y = u.sledz.y; }
    if (!u.zadane && u.czas >= u.zapowiedz) {
      u.zadane = true; fale.push({ x: u.x, y: u.y, czas: 0.4, max: 0.4, r: u.r, kolor: u.mroz ? '#9fd8ff' : '#ff5a3a' }); DZ.wybuch(); rozbryzg(u.x, u.y, u.mroz ? '#bfe8ff' : '#8a4a2a', 20);
      for (const g of gracze) {
        if (g.powalony || g.martwy || !g._D) continue;
        if (Math.hypot(g.x - u.x, g.y - u.y) <= u.r - (g.zdalny ? 6 : 0)) { kontekst(g); zranGracza(u.obr, u.typ || 'fiz', { bezUniku: true, wybuch: true, kto: u.kto || 'Uderzenie bossa' }); if (u.mroz) spowolnijGracza(0.5, 2); }
      }
    }
    if (u.czas > u.zapowiedz + 0.3) uderzeniaBossa.splice(i, 1);
  }
  for (let i = opoznioneLista.length - 1; i >= 0; i--) { const o = opoznioneLista[i]; o.t -= dt; if (o.t <= 0) { opoznioneLista.splice(i, 1); if (o.wl) kontekst(o.wl); try { o.fn(); } catch (e) { zglosBlad(e, 'opoznione'); } } }
  for (let i = efektyCzasowe.length - 1; i >= 0; i--) { const e = efektyCzasowe[i]; e.czas -= dt; if (e.cel && !e.cel.martwy) { e.x = e.cel.x; e.y = e.cel.y; } if (e.czas <= 0) { efektyCzasowe.splice(i, 1); if (e.wl) kontekst(e.wl); try { e.koniec && e.koniec(e); } catch (er) { zglosBlad(er, 'efekt'); } } }
  kontekst(z0);
  aktualizujWizualne(dt);
  // sumy obrażeń na wrogach
  for (const w of wrogowie) if (w.txt && czasGry - w.txt.t0 > 0.12) wypiszObrazenia(w);
}
function aktualizujWizualne(dt) {
  [czastki, teksty, fale, blyskawice, ciecia, stozki].forEach(l => { for (let i = l.length - 1; i >= 0; i--) { l[i].czas -= dt; if (l[i].czas <= 0) l.splice(i, 1); } });
  czastki.forEach(c => { c.x += c.vx * dt; c.y += c.vy * dt; c.vx *= 0.94; c.vy *= 0.94; });
  teksty.forEach(t => { t.y -= 26 * dt; });
}

// ---------------------------------------------------------------------
//  EFEKTY WIZUALNE (dane)
// ---------------------------------------------------------------------
function tekstSwiat(x, y, t, kolor, czas, rozm, o) { if (teksty.length > 55) teksty.shift(); teksty.push({ x: x, y: y, t: t, kolor: kolor, czas: czas || 0.9, max: czas || 0.9, rozm: rozm || 13, o: o || 0 }); }
function rozbryzg(x, y, kolor, n) { if (SIEC.rola === 'host') siecZdarzenie(['r', x | 0, y | 0, kolor, n]); const q = poziomEfektow(); if (q === 2) n = Math.min(4, Math.ceil(n * 0.3)); else if (q === 1) n = Math.ceil(n * 0.6); for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), v = losowo(40, 140); czastki.push({ x: x, y: y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, czas: 0.45, max: 0.45, kolor: kolor }); } if (czastki.length > 400) czastki.splice(0, czastki.length - 400); }
function czastkiLeczenia(x, y) { if (SIEC.rola === 'host') siecZdarzenie(['l', x | 0, y | 0]); for (let i = 0; i < 4; i++) czastki.push({ x: x + losowo(-8, 8), y: y, vx: 0, vy: -50, czas: 0.5, max: 0.5, kolor: '#5ae0a0' }); }
function efektBlysk(x, y, kolor) { fale.push({ x: x, y: y, czas: 0.25, max: 0.25, r: 26, kolor: kolor }); }
function dodajBlyskawice(x1, y1, x2, y2, kolor) {
  const dl = Math.hypot(x2 - x1, y2 - y1), ile = Math.max(4, Math.round(dl / 16));
  const nx = -(y2 - y1) / (dl || 1), ny = (x2 - x1) / (dl || 1), pkt = [[x1, y1]];
  for (let i = 1; i < ile; i++) { const t = i / ile, o = (Math.random() * 2 - 1) * 11 * Math.sin(t * Math.PI); pkt.push([x1 + (x2 - x1) * t + nx * o, y1 + (y2 - y1) * t + ny * o]); }
  pkt.push([x2, y2]);
  blyskawice.push({ pkt: pkt, czas: 0.28, max: 0.28, kolor: kolor || '#9fd8ff', a: [x1 | 0, y1 | 0, x2 | 0, y2 | 0] });
  if (blyskawice.length > 40) blyskawice.shift();
}

// =====================================================================
//  STWORZENIA GRACZA: działka, wieże, krzaki z owocami, pszczoły, miny,
//  wabiki, chowańce, czarne dziury... Wspólna lista `stwory`
//  (prosta do narysowania i do wysłania kolegom w grze online).
// =====================================================================
let stwory = [];
function mnStw() { return 1 + (FLAGI.mnStworow || 0); }
function dodajStwora(typ, x, y, czas, dane) {
  const T = TYPY_STWOROW[typ];
  const s = Object.assign({ typ: typ, x: ogr(x, POD_MIN, POD_MAX), y: ogr(y, POD_MIN, POD_MAX), czas: czas, max: czas, wl: gracz, t: 0, ik: T.ik, r: T.r || 12, kat: 0 }, dane || {});
  if (stwory.length >= 90) return s;       // limit - nie dodajemy, ale zwracamy obiekt
  stwory.push(s);
  return s;
}
function postawDzialko(typ, czas, dane) {
  if (FLAGI.fabryka) { czas *= 2; dane.co *= 0.77; }
  const k = Math.random() * Math.PI * 2;
  return dodajStwora(typ, gracz.x + Math.cos(k) * 36, gracz.y + Math.sin(k) * 36, czas, dane);
}
function aktualizujStwory(dt) {
  const z0 = gracz;
  for (let i = stwory.length - 1; i >= 0; i--) {
    const s = stwory[i]; if (!s) continue;
    s.czas -= dt;
    if (s.wl && gracze.indexOf(s.wl) < 0) { stwory.splice(i, 1); continue; }
    if (s.wl) kontekst(s.wl);
    const T = TYPY_STWOROW[s.typ];
    // Przeładowanie (Inżynier): wszystkie stworzenia właściciela działają 2× szybciej
    const szyb = s.wl && s.wl.buffy && s.wl.buffy.przeladowanie ? 2 : 1;
    try { if (T.tik) T.tik(s, dt * szyb); } catch (e) { zglosBlad(e, 'stwor ' + s.typ); }
    if (s.usun || s.czas <= 0) {
      if (!s.usun && T.koniec) { try { T.koniec(s); } catch (e) { zglosBlad(e, 'stwor koniec ' + s.typ); } }
      const j = stwory.indexOf(s); if (j >= 0) stwory.splice(j, 1);
    }
  }
  kontekst(z0);
}
function wrogBlisko(x, y, r) { return najblizszyWrog(x, y, r); }
// ruch latających / biegających stworzeń w stronę celu
function ruszStwora(s, tx, ty, v, dt, min) {
  const dx = tx - s.x, dy = ty - s.y, d = Math.hypot(dx, dy);
  if (d > (min || 4)) { const k = Math.min(d, v * dt); s.x += dx / d * k; s.y += dy / d * k; s.kat = Math.atan2(dy, dx); }
  return d;
}
function strzalDzialka(s, kolor, ksztalt, wybuch) {
  s.t -= 0;
  const c = wrogBlisko(s.x, s.y, 250); if (!c) return false;
  s.kat = Math.atan2(c.y - s.y, c.x - s.x);
  wystrzel({ x: s.x, y: s.y, cel: c, predkosc: wybuch ? 460 : 640, obr: s.obr * mnStw() * (wybuch ? 0.5 : 1), typ: 'fiz', kolor: kolor, ksztalt: ksztalt, zr: s.zr, zycie: 0.7, naprowadza: wybuch ? 4 : 0,
    wybuch: wybuch ? { r: 60, obr: s.obr * mnStw() } : null });
  if (mozna('dzialko', 90)) ton(420, 0.04, 'square', 0.04);
  return true;
}

const TYPY_STWOROW = {
  wiezyczka: { ik: '🗼', r: 11, wiezyczka: true, kolor: '#b8b8c8',
    tik(s, dt) { s.t -= dt; if (s.t <= 0 && strzalDzialka(s, '#ffe08a', 'kula')) s.t = s.co; } },
  dzialko: { ik: '🔫', r: 13, wiezyczka: true, kolor: '#5aa8e6',
    tik(s, dt) { s.t -= dt; if (s.t <= 0 && strzalDzialka(s, '#ffe08a', 'kula')) s.t = s.co; } },
  dzialoGromu: { ik: '💥', r: 15, wiezyczka: true, kolor: '#e6743c',
    tik(s, dt) { s.t -= dt; if (s.t <= 0 && strzalDzialka(s, '#ffb04a', 'rakieta', true)) s.t = s.co; } },
  tesla: { ik: '⚡', r: 12, wiezyczka: true, kolor: '#9fd8ff',
    tik(s, dt) { s.t -= dt; if (s.t > 0) return; const c = wrogBlisko(s.x, s.y, 220); if (!c) return; s.t = s.co; s.kat = Math.atan2(c.y - s.y, c.x - s.x); lancuch({ x: s.x, y: s.y - 14 }, c, s.obr * mnStw(), 'mag', 3, 150, 1, s.zr); } },
  // fala zimna co kilka sekund, co trzecia zamraża
  wiezaMrozu: { ik: '❄️', r: 12, wiezyczka: true, kolor: '#9fd8ff',
    tik(s, dt) { s.t -= dt; if (s.t > 0) return; s.t = s.co; s.n = (s.n || 0) + 1; const r = s.aura || 120;
      fale.push({ x: s.x, y: s.y, czas: 0.4, max: 0.4, r: r, kolor: '#9fd8ff' });
      wrogowie.forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - s.x, w.y - s.y) > r + w.r * 0.5) return;
        spowolnij(w, 0.45, 1.6); zadaj(w, s.obr * mnStw(), 'mag', { obszar: true, zr: s.zr }); if (s.n % 3 === 0) oglusz(w, 0.8, { zrodlo: s.zr }); }); } },
  // pocisk po łuku w największą grupę
  mozdzierz: { ik: '🧨', r: 13, wiezyczka: true, kolor: '#c08a5a',
    tik(s, dt) { s.t -= dt; if (s.t > 0) return; const c = skupisko(s.x, s.y, 380, 75); if (!c) return; s.t = s.co; s.kat = Math.atan2(c.y - s.y, c.x - s.x);
      granat(s.x, s.y, c.x, c.y, 75, s.obr * mnStw(), 'fiz', s.zr, 0.8, 0); if (mozna('mozdzierz', 150)) ton(140, 0.08, 'square', 0.05); } },
  // leczy drużynę wokół
  zrodlo: { ik: '⛲', r: 13, kolor: '#5ae0c0',
    tik(s, dt) { s.t -= dt; if (s.t > 0) return; s.t = s.co; leczDruzyne(s.x, s.y, s.aura || 130, 0, true, s.lecz * s.co * mnStw());
      if (Math.random() < 0.5) czastki.push({ x: s.x + losowo(-10, 10), y: s.y - 8, vx: 0, vy: -40, czas: 0.6, max: 0.6, kolor: '#7ee8d0' }); } },
  // jeden mocny strzał przebijający w najgroźniejszego wroga
  snajper: { ik: '🎯', r: 12, wiezyczka: true, kolor: '#e8d8a0',
    tik(s, dt) { s.t -= dt; if (s.t > 0) return;
      let c = null, naj = -1;
      for (const w of wrogowie) { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - s.x, w.y - s.y) > 420) continue; const v = (w.boss ? 1e9 : w.elita ? 1e6 : 0) + w.hp; if (v > naj) { naj = v; c = w; } }
      if (!c) return; s.t = s.co; s.kat = Math.atan2(c.y - s.y, c.x - s.x);
      wystrzel({ x: s.x, y: s.y, kat: s.kat, predkosc: 1100, obr: s.obr * mnStw(), typ: 'fiz', kolor: '#ffe8a0', ksztalt: 'strzala', zr: s.zr, zycie: 0.45, przebija: 99 });
      if (mozna('snajper', 120)) ton(900, 0.05, 'sawtooth', 0.05); } },
  krzak: { ik: '🌳', r: 14,
    tik(s, dt) {
      s.t -= dt;
      if (s.t <= 0) { s.t = s.co; for (let n = 0; n < (s.owoce || 1); n++) { const k = Math.random() * Math.PI * 2, d = losowo(22, 46); dodajStwora('owoc', s.x + Math.cos(k) * d, s.y + Math.sin(k) * d, 12, { lecz: s.lecz * mnStw(), tarcza: !!s.tarcza, ik: s.ikOwocu || '🍎' }); } }
      if (s.regen && s.aura) { s.tr = (s.tr || 0) - dt; if (s.tr <= 0) { s.tr = 0.5; leczDruzyne(s.x, s.y, s.aura, 0, true, s.regen * 0.5 * mnStw()); } }
    } },
  owoc: { ik: '🍎', r: 8,
    tik(s, dt) {
      for (const p of gracze) {
        if (p.powalony || p.martwy || !p._D) continue;
        const d = Math.hypot(p.x - s.x, p.y - s.y);
        if (d < 60 && d > 1) { s.x += (p.x - s.x) / d * Math.min(d, 160 * dt); s.y += (p.y - s.y) / d * Math.min(d, 160 * dt); }
        if (d < 20 + p.r) {
          const z = gracz; kontekst(p);
          leczGracza(D.hpMax * s.lecz, 'Owoce'); if (s.tarcza) dajTarcze(D.hpMax * s.lecz, 4, true);
          czastkiLeczenia(p.x, p.y); tekstSwiat(p.x, p.y - 26, s.ik + ' +' + Math.round(D.hpMax * s.lecz), '#7ee87a', 0.8, 12); DZ.mikstura();
          kontekst(z); s.usun = true; return;
        }
      }
    } },
  pszczola: { ik: '🐝', r: 7,
    tik(s, dt) {
      s.t -= dt; s.faza = (s.faza || Math.random() * 6) + dt * 9;
      const c = najblizszyWrog(s.x, s.y, 240);
      if (c && Math.hypot(c.x - gracz.x, c.y - gracz.y) < 320) {
        const d = ruszStwora(s, c.x + Math.cos(s.faza) * 10, c.y + Math.sin(s.faza) * 10, 280, dt, 2);
        if (d < c.r + 14 && s.t <= 0) { s.t = 0.6; zadaj(c, s.obr * mnStw(), 'fiz', { zr: s.zr }); }
      } else ruszStwora(s, gracz.x + Math.cos(s.faza) * 30, gracz.y + Math.sin(s.faza) * 30, 260, dt, 2);
    } },
  wilk: { ik: '🐺', r: 12,
    tik(s, dt) {
      s.t -= dt;
      if (Math.hypot(gracz.x - s.x, gracz.y - s.y) > 420) { s.x = gracz.x + 20; s.y = gracz.y; }
      const c = najblizszyWrog(gracz.x, gracz.y, 230);
      if (c) { const d = ruszStwora(s, c.x, c.y, 240, dt, c.r + 8); if (d < c.r + 20 && s.t <= 0) { s.t = 0.8; zadaj(c, s.obr * mnStw(), 'fiz', { zr: s.zr }); if (mozna('wilk', 200)) ton(160, 0.06, 'sawtooth', 0.05); } }
      else ruszStwora(s, gracz.x - 26, gracz.y + 10, 220, dt, 10);
    } },
  smok: { ik: '🐉', r: 12,
    tik(s, dt) {
      s.t -= dt; s.faza = (s.faza || 0) + dt * 2;
      ruszStwora(s, gracz.x + Math.cos(s.faza) * 34, gracz.y - 24 + Math.sin(s.faza) * 10, 260, dt, 3);
      if (s.t > 0) return; const c = najblizszyWrog(s.x, s.y, 170); if (!c) return; s.t = 2;
      const k0 = Math.atan2(c.y - s.y, c.x - s.x), zas = 160 * mnObszaru(); s.kat = k0;
      stozki.push({ x: s.x, y: s.y, kat: k0, r: zas, pol: 0.5, czas: 0.35, max: 0.35, kolor: '#ff7a3c' });
      wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0) return; const d = Math.hypot(w.x - s.x, w.y - s.y); if (d > zas + w.r || roznicaKata(Math.atan2(w.y - s.y, w.x - s.x), k0) > 0.5) return;
        zadaj(w, s.obr * mnStw(), 'mag', { zr: s.zr, obszar: true }); podpal(w, s.obr * mnStw() * 0.15, 3, 'mag', s.zr); });
      szum(0.25, 0.05, 'lowpass', 900);
    } },
  totem: { ik: '🗿', r: 13,
    tik(s, dt) { s.t -= dt; if (s.t > 0) return; s.t = 0.5; const r = s.aura;
      wrogowie.forEach(w => { if (!w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - s.x, w.y - s.y) < r + w.r * 0.5) { zadaj(w, s.obr * mnStw(), 'mag', { dot: true, obszar: true, zr: s.zr }); podpal(w, s.obr * mnStw() * 0.2, 1.5, 'mag', s.zr); } }); } },
  plon: { ik: '🌱', r: 10,
    tik(s, dt) { s.t += dt; if (s.t > 8 && s.ik === '🌱') s.ik = '🌾'; s.tz = (s.tz || 0) - dt; if (s.tz > 0 || !fala.aktywna) return; s.tz = 1; if (KLASY[gracz.klasa] && KLASY[gracz.klasa].plonuj) KLASY[gracz.klasa].plonuj(s); } },
  mina: { ik: '⚙️', r: 8,
    tik(s, dt) { if (s.wabi) wrogowie.forEach(w => { if (w.martwy || w.boss || w.zauroczony > 0) return; const d = Math.hypot(w.x - s.x, w.y - s.y); if (d < 140 && d > 10) { w.x += (s.x - w.x) / d * 40 * dt; w.y += (s.y - w.y) / d * 40 * dt; } });
      const c = najblizszyWrog(s.x, s.y, 24); if (!c) return; if (s.spow) obszarowe(s.x, s.y, s.r, '#ffb070', w => spowolnij(w, s.spow, 2), true); s.usun = true; DZ.wybuch(); rozbryzg(s.x, s.y, '#ffb070', 16); fale.push({ x: s.x, y: s.y, czas: 0.35, max: 0.35, r: s.r, kolor: '#ffb070' });
      wrogowie.slice().forEach(w => { if (!w.martwy && Math.hypot(w.x - s.x, w.y - s.y) < s.r + w.r * 0.5) zadaj(w, s.obr * mnStw(), 'fiz', { obszar: true, zr: s.zr }); }); } },
  wnyki: { ik: '🪤', r: 9,
    tik(s) { const c = najblizszyWrog(s.x, s.y, 22); if (!c) return; s.usun = true; oglusz(c, 1.5, { zrodlo: s.zr }); zadaj(c, s.obr * mnStw(), 'fiz', { zr: s.zr }); ton(240, 0.08, 'square', 0.07); } },
  dziura: { ik: '🌀', r: 16,
    tik(s, dt) { s.t -= dt;
      wrogowie.forEach(w => { if (w.martwy || w.zauroczony > 0 || w.boss) return; const d = Math.hypot(w.x - s.x, w.y - s.y); if (d > s.r || d < 6) return; const k = Math.min(1, dt * (w.ciezki ? 1.2 : 2.6)); w.x += (s.x - w.x) * k; w.y += (s.y - w.y) * k; });
      if (s.t <= 0) { s.t = 0.5; wrogowie.forEach(w => { if (!w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - s.x, w.y - s.y) < s.r) zadaj(w, s.obr * mnStw(), 'mag', { dot: true, obszar: true, zr: s.zr }); }); } } },
  wabik: { ik: '🎃', r: 13,
    tik(s) { wrogowie.forEach(w => { if (!w.martwy && !w.boss && !(w.zauroczony > 0) && Math.hypot(w.x - s.x, w.y - s.y) < s.aura) { w.wabik = s; w.tWabik = 0.3; } }); },
    koniec(s) { DZ.wybuch(); rozbryzg(s.x, s.y, '#ff9a3c', 18); fale.push({ x: s.x, y: s.y, czas: 0.4, max: 0.4, r: 110 * mnObszaru(), kolor: '#ff9a3c' });
      obszarowe(s.x, s.y, 110, '#ff9a3c', w => zadaj(w, s.obr * mnStw(), 'mag', { obszar: true, zr: s.zr }), true); } },
};
const KODY_STWOROW = Object.keys(TYPY_STWOROW);

// =====================================================================
//  FALE, TRUDNOŚĆ, PRÓBY, FALE SPECJALNE
// =====================================================================
const TRUDNOSCI = [
  { n: 'Spacerek', ik: '🌱', hp: 0.4, atak: 0.33, tempo: 0.72, spawn: 0.9, ms: 0.95, elity: 0.5, zloto: 1.0, skrzynie: 1.1, hpBoss: 0.8, zamach: 1.1,
    opis: ['Wrogowie mają o 60% mniej zdrowia i biją o 67% słabiej', 'Elity rzadziej', 'Na spokojne poznanie przedmiotów'] },
  { n: 'Normalny', ik: '⚔️', hp: 1.15, atak: 1.15, tempo: 1.04, spawn: 1, ms: 1, elity: 1.15, zloto: 1.05,
    opis: ['Tak, jak gra ma wyglądać', 'Boss co 5 fal'] },
  // kolejne poziomy liczone względem Normalnego (×1,15 zdrowia i obrażeń)
  { n: 'Trudny', ik: '🔥', hp: 1.15 * 1.3, atak: 1.15 * 1.25, tempo: 1.1, spawn: 1.04, ms: 1.02, elity: 1.15, zloto: 1.1, zamach: 0.96,
    opis: ['+30% zdrowia, +25% obrażeń wrogów (względem Normalnego)', 'Szybciej rosną w siłę'] },
  { n: 'Koszmar', ik: '💀', hp: 1.15 * 1.65, atak: 1.15 * 1.5, tempo: 1.17, spawn: 1.08, ms: 1.04, elity: 2.3, zloto: 1.15, specjalneOd: 1, falaStart: 'elitarna', hpBoss: 1.1, zamach: 0.93,
    opis: ['+65% zdrowia, +50% obrażeń wrogów (względem Normalnego)', 'Dwa razy więcej elit', 'Pierwsza fala to fala elit', 'Bossowie +10% zdrowia', 'Wrogowie nieco szybsi'] },
  { n: 'Piekło', ik: '👹', hp: 1.15 * 2, atak: 1.15 * 1.75, tempo: 1.22, spawn: 1.1, ms: 1.06, elity: 2.3, zloto: 1.2, specjalneOd: 1, falaStart: 'horda', afiksy: 1, hpBoss: 1.1, zamach: 0.9,
    opis: ['+100% zdrowia, +75% obrażeń wrogów (względem Normalnego)', 'Jak Koszmar: dwa razy więcej elit, bossowie +10% zdrowia', 'Elity mają dodatkowy afiks', 'Start od hordy'] },
  { n: 'Otchłań', ik: '🕳️', hp: 1.15 * 2.5, atak: 1.15 * 2, tempo: 1.27, spawn: 1.12, ms: 1.08, elity: 2.6, zloto: 1.25, specjalneOd: 1, falaStart: 'horda', afiksy: 1, hpBoss: 1.2, zamach: 0.88,
    opis: [] },
];

const SPECJALNE = {
  horda:    { n: 'Horda', ik: '🐀', opis: 'Dwa razy więcej słabszych wrogów · +40% złota', ustaw(f) { f.mnSpawn *= 2; f.mnHpWrogow = 0.65; f.mnZlota = 1.4; } },
  elitarna: { n: 'Fala elit', ik: '👑', opis: 'Mniej wrogów, ale co kilka sekund elita', ustaw(f) { f.mnSpawn *= 0.6; f.elityCo = Math.max(4, 8 - f.nr * 0.1); f.tElity = 3; } },
  zacmienie:{ n: 'Zaćmienie', ik: '🌑', opis: 'Widzisz tylko blisko siebie · +50% doświadczenia', ustaw(f) { f.ciemnosc = true; f.mnXp = 1.5; } },
  zlota:    { n: 'Gorączka złota', ik: '💰', opis: 'Złote gobliny uciekają z łupem — złap je!', ustaw(f) { f.zloteGobliny = 5; f.tGoblina = 3; } },
  ania:     { n: 'Nalot nietoperzy', ik: '🦇', opis: 'Nietoperze w dziesiątkach egzemplarzy', ustaw(f) { f.wymuszony = 'okrazacz'; f.mnSpawn *= 1.15; } },
  patryk:   { n: 'Smród skunksów', ik: '🦨', opis: 'Wszędzie trujący gaz', ustaw(f) { f.wymuszony = 'trujacy'; } },
  pajaki:   { n: 'Pajęczyna', ik: '🕷️', opis: 'Roje pająków', ustaw(f) { f.wymuszony = 'pajak'; f.mnSpawn *= 1.6; } },
};

const PROBY = [
  { id: 'krew', n: 'Próba Krwi', ik: '🩸', opis: 'Zaczynasz falę z <b>1 punktem zdrowia</b>.', nagroda: 'Na stałe <b>+12% maks. zdrowia</b>',
    start() {}, daj() { gracz.stale.hpProc = (gracz.stale.hpProc || 0) + 12; } },
  { id: 'czempion', n: 'Czempion Lochu', ik: '🏆', opis: 'Pojawia się <b>czempion</b>: elita z 3 afiksami i podwójnym zdrowiem. Zabij go przed końcem fali.', nagroda: '<b>Złoty augment</b> do wyboru',
    start() { fala.czempionZa = 4; }, sukces() { return !!fala.czempionZabity; }, daj() { gracz.augmentyDoWyboru.push('z'); } },
  { id: 'goraczka', n: 'Gorączka', ik: '🌡️', opis: 'Wrogowie są o <b>35% szybsi</b> i jest ich o 30% więcej.', nagroda: '<b>Podwójne złoto</b> z tej fali',
    start() { fala.mnMsWrogow = 1.35; fala.mnSpawn *= 1.3; }, daj() { dodajZloto(run.zlotoFali || 0, true, 'Gorączka'); } },
  { id: 'szklo', n: 'Szklana fala', ik: '🥂', opis: 'Otrzymujesz <b>podwójne obrażenia</b>.', nagroda: '<b>3 darmowe wybory</b> statystyk (co najmniej rzadkie)',
    start() { fala.mnOtrzymanych = 2; }, daj() { gracz.darmoweWybory += 3; } },
  { id: 'rozbrojenie', n: 'Rozbrojenie', ik: '🚫', opis: 'Działa tylko Twoja <b>pierwsza broń</b>.', nagroda: 'Losowa broń zyskuje <b>tier</b>',
    warunek: () => gracz.bronie.length >= 2, start() { fala.rozbrojenie = true; },
    daj() { const k = gracz.bronie.filter(b => b.tier < 3); if (k.length) { const b = losZ(k); b.tier++; toast('⬆️ ' + nazwaBroni(b)); } else dodajZloto(80, true, 'Rozbrojenie'); } },
  { id: 'ciemnosc', n: 'Ciemność', ik: '🌑', opis: 'Widzisz tylko w <b>małym kręgu</b> wokół siebie.', nagroda: '<b>Pryzmatyczne kowadło</b>',
    start() { fala.ciemnosc = true; }, daj() { gracz.kowadla++; } },
  { id: 'glod', n: 'Głód', ik: '🍽️', opis: '<b>Nie możesz się leczyć</b> w żaden sposób.', nagroda: '<b>+1 miejsce</b> na przedmiot',
    start() { fala.bezLeczenia = true; }, daj() { gracz.slotyPrzedm++; } },
  { id: 'nawalnica', n: 'Nawałnica', ik: '🌊', opis: 'Fala trwa o <b>50% dłużej</b> i wrogów jest 2× więcej.', nagroda: '<b>Legendarna skrzynia</b>',
    warunek: () => !fala.bossNastepny, start() { fala.dlugosc *= 1.5; fala.mnSpawn *= 2; }, daj() { gracz.skrzynie.push({ tier: 3 }); } },
  { id: 'polowanie', n: 'Polowanie', ik: '🏹', opis: 'Co 7 s pojawia się <b>elita</b>.', nagroda: 'Na stałe <b>+8% obrażeń</b>',
    start() { fala.elityCo = 7; fala.tElity = 4; }, daj() { gracz.stale.obrBonus = (gracz.stale.obrBonus || 0) + 8; } },
  { id: 'taniec', n: 'Taniec', ik: '💃', opis: 'Każde trafienie zabiera 5% złota. Daj się trafić <b>najwyżej 8 razy</b>.', nagroda: '<b>Pryzmatyczny augment</b> do wyboru',
    sukces() { return (run.trafFali || 0) <= 8; }, daj() { gracz.augmentyDoWyboru.push('p'); } },
];
const DEF_PROB = {}; PROBY.forEach(p => DEF_PROB[p.id] = p);

function dlugoscFali(nr) { return Math.min(90, 30 + 5 * (nr - 1)); }
function czyFalaBossa(nr) { return nr % 5 === 0; }
function czyAugmentPo(nr) { return nr === 3 || nr === 7 || nr === 11 || nr === 15 || (nr >= 20 && nr % 5 === 0); }
function czyProbaPrzed(nr) { return nr >= 3 && !czyFalaBossa(nr) && (nr % 5 === 3 || (nr > 5 && nr % 5 === 1)); }

function tierAugmentu(nr) {
  let w;
  if (nr <= 0) w = [['s', 100], ['z', 0], ['p', 0]];
  else if (nr <= 3) w = [['s', 60], ['z', 35], ['p', 5]];
  else if (nr <= 7) w = [['s', 35], ['z', 50], ['p', 15]];
  else if (nr <= 11) w = [['s', 20], ['z', 55], ['p', 25]];
  else w = [['s', 10], ['z', 55], ['p', 35]];
  const L = D ? D.szczescie / 100 : 0;
  w[1][1] *= 1 + L * 0.5; w[2][1] *= 1 + L;
  let t = losWazony(w);
  if (FLAGI.lepszeAugmenty && t === 's') t = 'z';
  return t;
}

// ---------------------------------------------------------------------
function startFali(nr) {
  const z0 = lokalny || gracz;
  kontekst(z0);
  const T = TRUDNOSCI[run.trudnosc];
  fala = { nr: nr, aktywna: true, czas: 0, dlugosc: dlugoscFali(nr), tSpawn: 0.4, mnSpawn: mnDruzyny(), boss: czyFalaBossa(nr), specjalna: null,
    proba: null, trafienia: 0, bossZabity: false, koniecZa: -1 };
  wrogowie = []; pociski = []; pociskiWrogow = []; kulki = []; monety = []; skrzynieNaZiemi = [];
  kaluze = []; polaEfektow = []; wiry = []; scianyMagiczne = []; bomby = []; uderzeniaBossa = []; zapowiedzi = []; opoznioneLista = []; efektyCzasowe = [];
  czastki = []; teksty = []; fale = []; blyskawice = []; ciecia = []; stozki = []; stwory = [];
  // fala specjalna
  if (!fala.boss) {
    if (T.falaStart && nr === 1) fala.specjalna = T.falaStart;
    else if (nr >= (T.specjalneOd || 4) && Math.random() < 0.22) fala.specjalna = losZ(Object.keys(SPECJALNE));
    if (fala.specjalna) SPECJALNE[fala.specjalna].ustaw(fala);
  }
  // próba (w drużynie wybiera ją gospodarz)
  if (run.wybranaProba) { fala.proba = DEF_PROB[run.wybranaProba]; run.wybranaProba = null; if (fala.proba.start) fala.proba.start(); }
  const n = gracze.length;
  gracze.forEach((p, i) => {
    kontekst(p);
    run.zlotoFali = 0; run.trafFali = 0; run.falaMaks = Math.max(run.falaMaks || 0, nr);
    const k = n > 1 ? i / n * Math.PI * 2 : 0;
    p.x = SRODEK + (n > 1 ? Math.cos(k) * 55 : 0); p.y = SRODEK + (n > 1 ? Math.sin(k) * 55 : 0); p.netX = undefined;
    p.tarcze = []; p.zastoj = 0; p.niewr = 1; p.celKat = null; p.spowG = 0; p.powalony = false; p.reanim = 0; p.dash = null;
    if (p.umi) p.umi.cd = 0; if (p.umi2) p.umi2.cd = 0; p.stanKlasy && (p.stanKlasy.zarodniki = false); p.oreze.forEach(o => { o.cd = Math.random() * 0.8; });
    zastosujStaty();
    p.hp = D.hpMax;
    hak('naStartFali');
    zastosujStaty();
    if (fala.proba && fala.proba.id === 'krew') p.hp = 1;
  });
  kontekst(z0);
  stan = 'walka';
  // boss
  let pod = '';
  if (fala.boss) {
    const idx = Math.floor(nr / 5) - 1;
    const b = stworzBossa(idx, SRODEK, SRODEK - 280);
    wrogowie.push(b);
    if (nr >= 30 && nr % 10 === 0) wrogowie.push(stworzBossa(idx + 1, SRODEK, SRODEK + 280));
    fala.bossy = wrogowie.filter(w => w.boss);
    DZ.boss();
    pod = '⚠️ BOSS: ' + fala.bossy.map(w => w.n).join(' + ');
  } else if (fala.specjalna) pod = SPECJALNE[fala.specjalna].ik + ' ' + SPECJALNE[fala.specjalna].n + ' — ' + SPECJALNE[fala.specjalna].opis;
  if (fala.proba) pod = (pod ? pod + '<br>' : '') + fala.proba.ik + ' ' + fala.proba.n;
  baner('🌊 Fala ' + nr, pod || czas(fala.dlugosc) + ' — przetrwaj!');
  if (nr === 11) dziennik('🥀 Zmęczenie: od teraz leczenie słabnie o 2,5% z każdą falą.');
  DZ.fala();
  for (let i = 0; i < (fala.boss ? 1 : 2); i++) spawnGrupy(true);
  odswiezHud(true);
  if (!druzyna()) zapiszGre(nr);
  if (typeof SIEC !== 'undefined' && SIEC.rola === 'host') siecStartFali();
}

function aktualizujFale(dt) {
  fala.czas += dt;
  const T = TRUDNOSCI[run.trudnosc], nr = fala.nr;
  if (fala.koniecZa > 0) { fala.koniecZa -= dt; if (fala.koniecZa <= 0) koniecFali(); return; }
  fala.tSpawn -= dt;
  if (fala.tSpawn <= 0) {
    let int = Math.max(0.5, 1.9 - nr * 0.06) / (T.spawn || 1) / fala.mnSpawn;
    if (fala.boss) int *= 2.4;
    fala.tSpawn = int * losowo(0.8, 1.2);
    spawnGrupy(false);
  }
  if (fala.elityCo) { fala.tElity -= dt; if (fala.tElity <= 0) { fala.tElity = fala.elityCo; zapowiedzSpawnu(losZ(dostepneTypy()), { elita: true }); } }
  if (fala.czempionZa > 0) { fala.czempionZa -= dt; if (fala.czempionZa <= 0) { fala.czempionZa = -1; zapowiedzSpawnu('ogr', { elita: true, afiksy: 3, czempion: true }); baner('🏆 Czempion!', 'Zabij go przed końcem fali'); } }
  if (fala.zloteGobliny > 0) { fala.tGoblina -= dt; if (fala.tGoblina <= 0) { fala.tGoblina = 6; fala.zloteGobliny--; zapowiedzSpawnu('goblin', { zloty: true }); } }
  // zapowiedzi pojawienia się
  for (let i = zapowiedzi.length - 1; i >= 0; i--) {
    const z = zapowiedzi[i]; z.czas -= dt;
    if (z.czas <= 0) { zapowiedzi.splice(i, 1); pojawWroga(z); }
  }
  // boss, którego nie da się pokonać w rozsądnym czasie, wpada w furię (żeby walka nie trwała w nieskończoność)
  if (fala.boss && fala.czas > 100) {
    fala.tFurii = (fala.tFurii || 0) - dt;
    if (fala.tFurii <= 0) {
      fala.tFurii = 5;
      if (!fala.furia) { fala.furia = true; baner('😡 Boss wpada w furię!', 'Z każdą chwilą bije mocniej'); }
      wrogowie.forEach(w => { if (w.boss && !w.martwy) { w.atak *= 1.2; w.ms = Math.min(w.ms * 1.03, 200); w.poswiata = '#ff2a1a'; } });
    }
  }
  if (!fala.boss && fala.czas >= fala.dlugosc) koniecFali();
}

function dostepneTypy() { return PULA_WROGOW.filter(p => fala.nr >= p[0]).map(p => p[1]); }
function losujTyp() {
  if (fala.wymuszony && Math.random() < 0.6) return fala.wymuszony;
  const nr = fala.nr;
  return losWazony(PULA_WROGOW.filter(p => nr >= p[0]).map(p => {
    let w = p[2];
    if ((p[1] === 'szczur' || p[1] === 'goblin') && nr > 8) w *= Math.max(0.25, 1 - (nr - 8) * 0.06);
    return [p[1], w];
  }));
}
function spawnGrupy(odRazu) {
  const zywi = wrogowie.filter(w => !w.martwy).length + zapowiedzi.length;
  if (zywi >= limitWrogow()) return;
  const nr = fala.nr, T = TRUDNOSCI[run.trudnosc];
  let ile = 1 + Math.floor(nr / 6) + (Math.random() < 0.5 ? 1 : 0);
  if (fala.boss) ile = Math.max(1, Math.round(ile * 0.6));
  const typ = losujTyp();
  if (typ === 'pajak') ile += 2;
  const kotw = losZ(zywiGracze()) || gracz;
  // jedno miejsce dla całej grupy
  let x, y, prob = 0;
  do { const k = Math.random() * Math.PI * 2, d = losowo(240, 520); x = kotw.x + Math.cos(k) * d; y = kotw.y + Math.sin(k) * d; prob++; }
  while ((x < POD_MIN + 20 || x > POD_MAX - 20 || y < POD_MIN + 20 || y > POD_MAX - 20) && prob < 30);
  x = ogr(x, POD_MIN + 20, POD_MAX - 20); y = ogr(y, POD_MIN + 20, POD_MAX - 20);
  for (let i = 0; i < ile; i++) {
    const t = i === 0 ? typ : (Math.random() < 0.6 ? typ : losujTyp());
    let pE = Math.min(0.12, Math.max(0, 0.004 * (nr - 1))) * T.elity;
    if (nr <= 2 && !T.specjalneOd) pE = 0;
    zapowiedzSpawnu(t, { elita: Math.random() < pE }, x + losowo(-40, 40), y + losowo(-40, 40), odRazu ? 0.6 : 0.85);
  }
}
function zapowiedzSpawnu(typ, opcje, x, y, czasZ) {
  if (x === undefined) { const kotw = losZ(zywiGracze()) || gracz; let prob = 0; do { const k = Math.random() * Math.PI * 2, d = losowo(220, 460); x = kotw.x + Math.cos(k) * d; y = kotw.y + Math.sin(k) * d; prob++; } while ((x < POD_MIN || x > POD_MAX || y < POD_MIN || y > POD_MAX) && prob < 30); }
  zapowiedzi.push({ typ: typ, opcje: opcje || {}, x: ogr(x, POD_MIN, POD_MAX), y: ogr(y, POD_MIN, POD_MAX), czas: czasZ || 0.85, max: czasZ || 0.85 });
}
function pojawWroga(z) {
  const o = z.opcje || {};
  const w = stworzWroga(z.typ, z.x, z.y, { elita: o.elita, afiksy: o.afiksy });
  if (o.czempion) { w.czempion = true; w.hp *= 2; w.hpMax = w.hp; w.n = 'Czempion'; }
  if (o.zloty) { w.zloty = true; w.zach = 'uciekajacy'; w.ik = '💰'; w.kolor = '#ffd24a'; w.zl *= 18; w.hp *= 2.5; w.hpMax = w.hp; w.ms *= 1.15; w.atak = 0; w.znika = 12; }
  if (fala.boss) w.xp *= 0.6;
  wrogowie.push(w);
}

function bossPokonany(w) {
  DZ.zwyciestwo();
  baner('👑 ' + w.n + ' pokonany!', 'Skrzynia bossa czeka');
  dlaKazdego(() => {
    dodajZloto(40 + fala.nr * 6, true, 'Nagroda za bossa');
    if (fala.nr % 10 === 0) { gracz.kowadla++; toast('🔨 Za bossa: Pryzmatyczne kowadło!'); }
  });
  if (fala.boss && wrogowie.every(o => !o.boss || o.martwy)) { fala.bossZabity = true; fala.koniecZa = 2.2; }
}

function koniecFali() {
  if (!fala.aktywna) return;
  fala.aktywna = false; stan = 'przerwa';
  const z0 = lokalny || gracz;
  // to, co zostało na ziemi: połowa liczy się jak zebrana (potem działają mnożniki), połowa przepada
  wrogowie.forEach(w => { if (!w.martwy) { rozbryzg(w.x, w.y, '#5a4a6a', 6); } });
  wrogowie = []; pociskiWrogow = []; zapowiedzi = []; bomby = []; kaluze = []; uderzeniaBossa = []; stwory = [];
  let xp = 0, zl = 0; kulki.forEach(k => xp += k.xp); monety.forEach(m => zl += m.v);
  xp *= 0.5; zl *= 0.5;
  const sk = skrzynieNaZiemi.filter(s => s.boss || Math.random() < 0.5), skPrzepadlo = skrzynieNaZiemi.length - sk.length;
  // minimum skrzyń na falę
  const brakSk = Math.max(0, zakresSkrzyn(fala.nr)[0] - (fala.skrzynie || 0));
  for (let i = 0; i < brakSk; i++) { sk.push({ tier: tierSkrzyni(null), boss: false }); fala.skrzynie = (fala.skrzynie || 0) + 1; }
  kulki = []; monety = []; skrzynieNaZiemi = [];
  dlaKazdego(p => {
    const bylPowalony = p.powalony;
    if (p.powalony) p.hp = Math.max(1, D.hpMax * 0.35);
    p.powalony = false; p.reanim = 0;
    // połowa tego, co zostało na ziemi, zbiera się sama
    const zl0 = gracz.zloto, xp0 = run.xp;
    if (xp > 0) dodajXp(xp);
    if (zl > 0) dodajZloto(zl);
    if (xp > 0.5 || zl > 0.5 || skPrzepadlo) dziennik('🧲 Połowa łupów z ziemi: +' + Math.floor(gracz.zloto - zl0) + ' 💰 · +' + Math.round(run.xp - xp0) + ' ✨' + (skPrzepadlo ? ' · przepadło skrzyń: ' + skPrzepadlo : '') + ' (resztę zbieraj w trakcie fali)');
    sk.forEach(s => p.skrzynie.push({ tier: s.tier, boss: s.boss }));
    dodajZloto(0.3 * zlotoNaFale(fala.nr), false, 'Nagroda za falę');
    // próba
    run.wynikProby = null;
    if (fala.proba) {
      // w drużynie nagroda tylko dla tych, którzy skończyli falę na nogach (i byli w niej od początku)
      const ok = !bylPowalony && run.spoznionyFala !== fala.nr && (fala.proba.sukces ? fala.proba.sukces() : true);
      run.wynikProby = { id: fala.proba.id, ok: ok };
      if (ok) { try { fala.proba.daj(); } catch (e) { zglosBlad(e, 'proba'); } run.probyZaliczone = (run.probyZaliczone || 0) + 1; }
    }
    hak('naKoniecFali');
    oznaczStaty(); zastosujStaty();
    run.przerwa = { nr: fala.nr, augment: czyAugmentPo(fala.nr) ? tierAugmentu(fala.nr) : null, sklep: false, proba: false, kowadloPo1: fala.nr === (KLASY[gracz.klasa].kowadloPo || 1) };
    if (run.przerwa.kowadloPo1) gracz.kowadla++;
  });
  kontekst(z0);
  if (!druzyna()) zapiszGre();
  DZ.zwyciestwo();
  baner('✅ Fala ' + fala.nr + ' przetrwana!', '');
  if (typeof SIEC !== 'undefined' && SIEC.rola === 'host') siecKoniecFali();
  setTimeout(() => { if (stan === 'przerwa') { kontekst(lokalny || gracz); kolejkaPrzerwy(); } }, 1100);
}

// Kolejność ekranów między falami
function kolejkaPrzerwy() {
  const p = run.przerwa;
  if (!p) {
    // zabezpieczenie: przerwa bez kolejki ekranów (np. po wczytaniu) - w grze solo po prostu następna fala
    if (stan === 'przerwa' && !druzyna() && gracz && fala && !fala.aktywna) { zamknijEkran(); zamknijModal(); startFali((fala.nr || 0) + 1); }
    return;
  }
  zapiszGre();
  if (run.augOferta) { pokazAugmenty(run.augOferta.tier); return; }
  if (p.start) {
    if (p.augment) { const t = p.augment; p.augment = null; pokazAugmenty(t); return; }
    if (gracz.darmoweWybory > 0) { pokazWyborStatow(true); return; }
    if (gracz.kowadla > 0) { pokazKowadlo(); return; }
    run.przerwa = null; if (druzyna()) { gotowyDoFali(1); return; } zapiszGre(); startFali(1); zamknijEkran(); return;
  }
  if (run.wynikProby) { const w = run.wynikProby; run.wynikProby = null; pokazWynikProby(w); return; }
  if (gracz.doWyboru > 0) { pokazWyborStatow(false); return; }
  if (gracz.darmoweWybory > 0) { pokazWyborStatow(true); return; }
  if (gracz.skrzynie.length) { pokazSkrzynie(); return; }
  if (p.augment) { const t = p.augment; p.augment = null; pokazAugmenty(t); return; }
  if (gracz.augmentyDoWyboru && gracz.augmentyDoWyboru.length) { pokazAugmenty(gracz.augmentyDoWyboru.shift()); return; }
  if (gracz.kowadla > 0) { pokazKowadlo(); return; }
  if (!p.sklep) { if (!p.sklepOtwarty) { p.sklepOtwarty = true; nowySklep(); hak('naSklep'); zapiszGre(); } pokazSklep(); return; }
  if (!p.proba && czyProbaPrzed(p.nr + 1) && !(typeof SIEC !== 'undefined' && SIEC.rola === 'klient')) { p.proba = true; pokazProby(); return; }
  run.przerwa = null;
  if (druzyna()) { if (typeof SIEC !== 'undefined') SIEC.cofnijPrzerwe = p.sklepOtwarty ? p : null; gotowyDoFali(p.nr + 1); return; }
  zamknijEkran();
  startFali(p.nr + 1);
}

// =====================================================================
//  RYSOWANIE
// =====================================================================
let kamX = 0, kamY = 0;
const ciemnosc = document.createElement('canvas'), ciemnoscCtx = ciemnosc.getContext('2d');
const swiatlaPochodni = [];
const drobinki = [];
function sprite(r, fn) { const c = document.createElement('canvas'); c.width = c.height = r * 2; fn(c.getContext('2d'), r); return c; }
const SPR_SWIATLO = sprite(64, (c, r) => { const g = c.createRadialGradient(r, r, 0, r, r, r); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(0.55, 'rgba(0,0,0,0.75)'); g.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = g; c.fillRect(0, 0, r * 2, r * 2); });
const SPR_POCHODNIA = sprite(64, (c, r) => { const g = c.createRadialGradient(r, r, 2, r, r, r); g.addColorStop(0, 'rgba(255,150,60,0.16)'); g.addColorStop(1, 'rgba(255,120,40,0)'); c.fillStyle = g; c.fillRect(0, 0, r * 2, r * 2); });
const SPR_GRACZ = sprite(64, (c, r) => { const g = c.createRadialGradient(r, r, 2, r, r, r); g.addColorStop(0, 'rgba(255,200,130,0.07)'); g.addColorStop(1, 'rgba(255,200,130,0)'); c.fillStyle = g; c.fillRect(0, 0, r * 2, r * 2); });
// kryształ doświadczenia (szlifowany, z miękką poświatą)
const SPR_KULKA = sprite(32, (c, r) => {
  const g = c.createRadialGradient(r, r, 0, r, r, r); g.addColorStop(0, 'rgba(120,240,140,0.45)'); g.addColorStop(1, 'rgba(120,240,140,0)'); c.fillStyle = g; c.fillRect(0, 0, r * 2, r * 2);
  const w = r * 0.42, h = r * 0.62;
  c.fillStyle = '#1e7a3a'; c.beginPath(); c.moveTo(r, r - h); c.lineTo(r + w, r); c.lineTo(r, r + h); c.lineTo(r - w, r); c.closePath(); c.fill();
  c.fillStyle = '#5ae07a'; c.beginPath(); c.moveTo(r, r - h); c.lineTo(r + w, r); c.lineTo(r, r + h * 0.15); c.closePath(); c.fill();
  c.fillStyle = '#b8ffb8'; c.beginPath(); c.moveTo(r, r - h); c.lineTo(r - w, r); c.lineTo(r, r + h * 0.15); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(10,40,20,0.8)'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(r, r - h); c.lineTo(r + w, r); c.lineTo(r, r + h); c.lineTo(r - w, r); c.closePath(); c.stroke();
  c.fillStyle = 'rgba(255,255,255,0.9)'; c.fillRect(r - w * 0.35, r - h * 0.45, 2.2, 2.2);
});
const SPR_MONETA = sprite(16, (c, r) => { c.fillStyle = '#8a5a08'; c.beginPath(); c.arc(r, r + 1, r - 1, 0, Math.PI * 2); c.fill(); c.fillStyle = '#ffd24a'; c.beginPath(); c.arc(r, r, r * 0.8, 0, Math.PI * 2); c.fill();
  c.strokeStyle = '#c8961c'; c.lineWidth = 1.6; c.beginPath(); c.arc(r, r, r * 0.55, 0, Math.PI * 2); c.stroke(); c.fillStyle = '#fff6c0'; c.fillRect(r - 4, r - 6, 3, 3); });
const OBRAZY_TWARZY = {};   // (dawniej zdjęcia — gra nie jest już spersonalizowana)

function ustawKamere(dt) {
  const cx = gracz.x - WID_SW / 2, cy = gracz.y - WYS_SW * KAM_PION;
  const k = dt ? Math.min(1, dt * 9) : 1;
  kamX += (cx - kamX) * k; kamY += (cy - kamY) * k;
  const maxX = ARENA * KAFEL - WID_SW, maxY = ARENA * KAFEL - WYS_SW;
  kamX = ogr(kamX, Math.min(0, maxX / 2), Math.max(maxX / 2, maxX));
  kamY = ogr(kamY, Math.min(-60, maxY / 2), Math.max(maxY / 2, maxY + 40));
}
function naEkranie(x, y, m) { m = m || 60; return x > kamX - m && x < kamX + WID_SW + m && y > kamY - m && y < kamY + WYS_SW + m; }

// Lista postaci do narysowania: w grze lokalnej i u gospodarza - prawdziwi gracze,
// u klienta gry online - postacie z ostatniego stanu od gospodarza.
function graczeDoRysowania() {
  if (typeof SIEC !== 'undefined' && SIEC.rola === 'klient') return SIEC.widokGraczy || [];
  const z0 = gracz;
  gracze.forEach(p => { kontekst(p); p.roz = rozmiarGracza(); p.ts = tarczaSuma(); p.hpMaxR = D ? D.hpMax : 100; });
  kontekst(z0);
  return gracze;
}
function rysuj() {
  if (lokalny && stan === 'walka' && SIEC.rola !== 'klient') kontekst(lokalny);
  swiatlaPochodni.length = 0;
  if (widok.width !== Math.round(WID * DPR) || widok.height !== Math.round(WYS * DPR)) { widok.width = Math.round(WID * DPR); widok.height = Math.round(WYS * DPR); }
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.fillStyle = '#0a0810'; ctx.fillRect(0, 0, WID, WYS);
  if (!gracz) return;
  SKALA_RYS = ZOOM * DPR;
  ctx.setTransform(ZOOM * DPR, 0, 0, ZOOM * DPR, -kamX * ZOOM * DPR, -kamY * ZOOM * DPR);
  rysujPodloge();
  rysujPlansze();
  rysujLupy();
  rysujWrogow();
  rysujStwory();
  graczeDoRysowania().forEach(p => rysujGracza(p));
  rysujOrby();
  rysujPociski();
  rysujEfekty();
  ctx.setTransform(ZOOM * DPR, 0, 0, ZOOM * DPR, 0, 0);
  rysujOswietlenie();
  ctx.setTransform(ZOOM * DPR, 0, 0, ZOOM * DPR, -kamX * ZOOM * DPR, -kamY * ZOOM * DPR);
  rysujTeksty();
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  rysujInterfejsPlotna();
}

function rysujPodloge() {
  const tx0 = Math.max(0, Math.floor(kamX / KAFEL) - 1), tx1 = Math.min(ARENA - 1, Math.ceil((kamX + WID_SW) / KAFEL) + 1);
  const ty0 = Math.max(0, Math.floor(kamY / KAFEL) - 1), ty1 = Math.min(ARENA - 1, Math.ceil((kamY + WYS_SW) / KAFEL) + 1);
  const t = Date.now();
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    const ex = tx * KAFEL, ey = ty * KAFEL;
    const sciana = tx < MUR || ty < MUR || tx >= ARENA - MUR || ty >= ARENA - MUR;
    if (!sciana) {
      const z = (tx * 73856093 ^ ty * 19349663) >>> 0, war = z % 5, od = (z % 7) * 3;
      ctx.fillStyle = 'rgb(' + (32 + od) + ',' + (28 + od) + ',' + (25 + od) + ')';
      ctx.fillRect(ex, ey, KAFEL, KAFEL);
      if (ty === MUR) { ctx.fillStyle = 'rgba(0,0,0,0.34)'; ctx.fillRect(ex, ey, KAFEL, 6); ctx.fillStyle = 'rgba(0,0,0,0.15)'; ctx.fillRect(ex, ey + 6, KAFEL, 8); }
      if (tx === MUR) { ctx.fillStyle = 'rgba(0,0,0,0.2)'; ctx.fillRect(ex, ey, 6, KAFEL); }
      if (tx === ARENA - MUR - 1) { ctx.fillStyle = 'rgba(0,0,0,0.14)'; ctx.fillRect(ex + KAFEL - 5, ey, 5, KAFEL); }
      if (war === 1) { ctx.strokeStyle = 'rgba(0,0,0,0.34)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(ex + 9, ey + 7); ctx.lineTo(ex + 22, ey + 24); ctx.lineTo(ex + 15, ey + 40); ctx.stroke(); }
      else if (war === 2) { ctx.fillStyle = 'rgba(40,60,70,0.22)'; ctx.beginPath(); ctx.ellipse(ex + 24, ey + 26, 11, 7.5, 0.5, 0, Math.PI * 2); ctx.fill(); }
      else if (war === 3) { ctx.fillStyle = 'rgba(90,80,66,0.3)'; ctx.fillRect(ex + 10, ey + 31, 3, 3); ctx.fillRect(ex + 27, ey + 13, 2, 2); ctx.fillRect(ex + 33, ey + 32, 2, 2); }
      else if (war === 4 && z % 23 === 0) { ctx.globalAlpha = 0.3; rysujIk(ctx, z % 2 ? '🦴' : '💀', ex + 22, ey + 22, 13, 's'); ctx.globalAlpha = 1; }
      ctx.strokeStyle = 'rgba(0,0,0,0.3)'; ctx.lineWidth = 1; ctx.strokeRect(ex + 0.5, ey + 0.5, KAFEL - 1, KAFEL - 1);
    } else {
      const z2 = (tx * 83492791 ^ ty * 29996224) >>> 0;
      ctx.fillStyle = 'rgb(' + (22 + z2 % 5) + ',' + (20 + z2 % 4) + ',' + (26 + z2 % 6) + ')';
      ctx.fillRect(ex, ey, KAFEL, KAFEL);
      const przyPodlodze = tx >= MUR - 1 && ty >= MUR - 1 && tx <= ARENA - MUR && ty <= ARENA - MUR;
      if (przyPodlodze) {
        ctx.strokeStyle = 'rgba(255,255,255,0.055)'; ctx.lineWidth = 1; const pol = KAFEL / 2;
        ctx.beginPath(); ctx.moveTo(ex, ey + pol + 0.5); ctx.lineTo(ex + KAFEL, ey + pol + 0.5); ctx.stroke();
        const pr = (ty % 2 === 0) ? 0 : pol;
        ctx.beginPath(); ctx.moveTo(ex + pr + 0.5, ey); ctx.lineTo(ex + pr + 0.5, ey + pol); ctx.moveTo(ex + (pr + pol) % KAFEL + 0.5, ey + pol); ctx.lineTo(ex + (pr + pol) % KAFEL + 0.5, ey + KAFEL); ctx.stroke();
        if (ty === MUR - 1 && tx % 4 === 1 && tx > MUR && tx < ARENA - MUR - 1) {
          const px = ex + KAFEL / 2, py = ey + KAFEL * 0.72, mig = 0.72 + Math.sin(t / 140 + tx * 2.1) * 0.28;
          swiatlaPochodni.push([px, py, mig]);
          ctx.fillStyle = '#5a3a20'; ctx.fillRect(px - 1.6, py - 2, 3.2, 9);
          ctx.fillStyle = '#ffb03c'; ctx.beginPath(); ctx.ellipse(px, py - 5, 3 * mig, 5.5 * mig, 0, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = '#ffe89a'; ctx.beginPath(); ctx.ellipse(px, py - 5.5, 1.4 * mig, 2.8 * mig, 0, 0, Math.PI * 2); ctx.fill();
        }
      }
    }
  }
}

const KOLORY_POL = { mroz: '200,240,255', trucizna: '120,220,90', kwas: '210,240,60', ogien: '255,130,40' };
function rysujPlansze() {
  const t = Date.now();
  // kałuże: gaz, ogień, pajęczyna
  kaluze.forEach(k => {
    if (!naEkranie(k.x, k.y)) return;
    const a = Math.min(1, k.czas / k.max * 1.5);
    const g = ctx.createRadialGradient(k.x, k.y, 2, k.x, k.y, k.r);
    if (k.rodzaj === 'gaz') { g.addColorStop(0, 'rgba(154,224,90,' + 0.42 * a + ')'); g.addColorStop(1, 'rgba(90,150,50,0)'); }
    else { g.addColorStop(0, 'rgba(255,140,40,' + 0.5 * a + ')'); g.addColorStop(1, 'rgba(200,60,20,0)'); }
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(k.x, k.y, k.r, 0, Math.PI * 2); ctx.fill();
  });
  polaEfektow.forEach(p => {
    if (!naEkranie(p.x, p.y, p.r + 20)) return;
    const a = Math.min(1, p.czas / 0.8), g = ctx.createRadialGradient(p.x, p.y, 2, p.x, p.y, p.r);
    const k = KOLORY_POL[p.rodzaj] || KOLORY_POL.mroz;
    g.addColorStop(0, 'rgba(' + k + ',' + 0.32 * a + ')'); g.addColorStop(1, 'rgba(' + k + ',' + 0.06 * a + ')');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
    if (p.rodzaj === 'ogien' && p.r > 34 && poziomEfektow() < 2) {   // języki ognia na płonącej plamie
      const n = p.r > 55 ? 4 : 3, t = Date.now() / 1000, z = (p.x * 7 + p.y * 3) % 6.28;
      ctx.globalAlpha = 0.85 * a;
      for (let i = 0; i < n; i++) { const k2 = z + i * 6.28 / n + t * 0.4, d = p.r * 0.45, s = 10 + 3 * Math.sin(t * 9 + i * 2.1);
        rysujIk(ctx, '🔥', p.x + Math.cos(k2) * d, p.y + Math.sin(k2) * d * 0.7 - s * 0.3, s); }
      ctx.globalAlpha = 1;
    }
  });
  // zapowiedzi pojawienia się wrogów
  zapowiedzi.forEach(z => {
    const p = 1 - z.czas / z.max;
    ctx.save(); ctx.globalAlpha = 0.45 + 0.45 * Math.sin(p * Math.PI * 3);
    ctx.strokeStyle = z.opcje && z.opcje.elita ? '#ffd24a' : '#e6543c'; ctx.lineWidth = 3;
    const s = 9;
    ctx.beginPath(); ctx.moveTo(z.x - s, z.y - s); ctx.lineTo(z.x + s, z.y + s); ctx.moveTo(z.x + s, z.y - s); ctx.lineTo(z.x - s, z.y + s); ctx.stroke();
    ctx.restore();
  });
  // uderzenia bossa (zapowiedź)
  uderzeniaBossa.forEach(u => {
    if (u.zadane) return;
    const p = Math.min(1, u.czas / u.zapowiedz);
    ctx.fillStyle = u.mroz ? 'rgba(120,200,255,' + (0.1 + 0.2 * p) + ')' : 'rgba(220,40,30,' + (0.12 + 0.22 * p) + ')';
    ctx.beginPath(); ctx.arc(u.x, u.y, u.r, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = u.mroz ? 'rgba(190,235,255,0.9)' : 'rgba(255,90,60,0.85)'; ctx.lineWidth = 2.5; ctx.setLineDash([8, 6]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(u.x, u.y, u.r * p, 0, Math.PI * 2); ctx.strokeStyle = 'rgba(255,200,160,0.9)'; ctx.lineWidth = 2; ctx.stroke();
  });
  // meteory i runy
  efektyCzasowe.forEach(e => {
    const p = 1 - e.czas / e.max;
    if (e.rodzaj === 'meteor') {
      ctx.fillStyle = 'rgba(255,120,40,' + (0.12 + 0.25 * p) + ')'; ctx.beginPath(); ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,170,90,0.85)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(e.x, e.y, e.r * p, 0, Math.PI * 2); ctx.stroke();
      const my = e.y - 220 * (1 - p); rysujIk(ctx, '☄️', e.x + 60 * (1 - p), my, 22);
    } else if (e.rodzaj === 'granat') {
      ctx.strokeStyle = 'rgba(255,160,90,' + (0.4 + 0.4 * p) + ')'; ctx.lineWidth = 2; ctx.setLineDash([6, 5]); ctx.beginPath(); ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      const bx = e.sx + (e.x - e.sx) * p, by = e.sy + (e.y - e.sy) * p - Math.sin(p * Math.PI) * 60;
      rysujIk(ctx, '💣', bx, by, e.r > 150 ? 26 : 18);
    } else if (e.rodzaj === 'detonacja') {
      // kula przyklejona do wroga: ciemna kula z iskrzącym lontem, pierścień odliczania
      const pul = 0.5 + 0.5 * Math.sin(Date.now() / (60 + 140 * (1 - p)));
      ctx.save(); ctx.globalAlpha = 0.35 + 0.35 * p; ctx.strokeStyle = '#ff7a2a'; ctx.lineWidth = 2; ctx.setLineDash([5, 5]);
      ctx.beginPath(); ctx.arc(e.x, e.y, (e.r || 100) * mnObszaru(), 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      ctx.globalAlpha = 0.9; ctx.lineWidth = 3; ctx.strokeStyle = '#ffd24a'; ctx.beginPath(); ctx.arc(e.x, e.y - 6, 16, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (1 - p)); ctx.stroke();
      ctx.globalAlpha = 1; rysujPoswiate(e.x, e.y - 6, 18 + 8 * pul, '#ff7a2a', 0.8 + 0.5 * p);
      ctx.fillStyle = '#1e1a24'; ctx.beginPath(); ctx.arc(e.x, e.y - 6, 7, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = 'rgba(255,160,90,0.9)'; ctx.lineWidth = 1.2; ctx.stroke();
      ctx.fillStyle = pul > 0.5 ? '#ffe08a' : '#ff6a2a'; ctx.beginPath(); ctx.arc(e.x + 4, e.y - 13, 2 + pul * 1.5, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    } else if (e.rodzaj === 'slupOgnia') {
      // Erupcja: słup ognia bijący w górę
      const a = Math.sin(Math.min(1, p) * Math.PI), sz = 26 + 18 * a, wys = 150 * a;
      ctx.save(); ctx.globalAlpha = 0.5 * a; ctx.fillStyle = '#ff6a2a'; ctx.beginPath(); ctx.arc(e.x, e.y, (e.r || 120) * (0.4 + 0.6 * p), 0, Math.PI * 2); ctx.fill();
      const g = ctx.createLinearGradient(0, e.y - wys, 0, e.y); g.addColorStop(0, 'rgba(255,220,120,0)'); g.addColorStop(0.35, 'rgba(255,170,60,0.75)'); g.addColorStop(1, 'rgba(255,90,30,0.95)');
      ctx.globalAlpha = a; ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(e.x - sz, e.y); ctx.quadraticCurveTo(e.x - sz * 0.6, e.y - wys * 0.6, e.x, e.y - wys); ctx.quadraticCurveTo(e.x + sz * 0.6, e.y - wys * 0.6, e.x + sz, e.y); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,245,200,0.85)'; ctx.beginPath(); ctx.moveTo(e.x - sz * 0.35, e.y); ctx.quadraticCurveTo(e.x, e.y - wys * 0.7, e.x + sz * 0.35, e.y); ctx.closePath(); ctx.fill();
      ctx.restore();
    } else if (e.rodzaj === 'runy') {
      for (let n = 0; n < 3; n++) {
        const k = p * 7 + n * 2.09, r = 34 - p * 10, x = e.x + Math.cos(k) * r, y = e.y + Math.sin(k) * r;
        ctx.save(); ctx.translate(x, y); ctx.rotate(k + 1.57); ctx.shadowColor = '#c9a8ff'; ctx.shadowBlur = 10;
        ctx.fillStyle = '#e6dcff'; ctx.beginPath(); ctx.moveTo(0, -9); ctx.lineTo(3, 0); ctx.lineTo(0, 9); ctx.lineTo(-3, 0); ctx.closePath(); ctx.fill(); ctx.restore();
      }
    }
  });
  // wiry
  wiry.forEach(wr => {
    const wz = wr.rozruch > 0 ? 1 - wr.rozruch / 0.7 : 1, zn = Math.min(1, wr.czas / 0.5);
    ctx.save(); ctx.globalAlpha = 0.16 * zn; ctx.fillStyle = '#6a4ac4'; ctx.beginPath(); ctx.arc(wr.x, wr.y, wr.r * wz, 0, Math.PI * 2); ctx.fill();
    ctx.lineCap = 'round';
    for (let ra = 0; ra < 3; ra++) {
      ctx.globalAlpha = (wr.rozruch > 0 ? 0.45 : 0.8) * zn; ctx.strokeStyle = ra % 2 ? '#c9a8ff' : '#e6dcff'; ctx.lineWidth = 3 - ra * 0.6; ctx.beginPath();
      for (let s = 0; s <= 26; s++) { const tt = s / 26, kt = wr.faza * (ra % 2 ? -1 : 1) + ra * 2.09 + tt * Math.PI * 2.4, rr = wr.r * wz * (0.12 + tt * 0.88);
        const qx = wr.x + Math.cos(kt) * rr, qy = wr.y + Math.sin(kt) * rr * 0.62; if (s) ctx.lineTo(qx, qy); else ctx.moveTo(qx, qy); }
      ctx.stroke();
    }
    ctx.restore();
  });
  // bomby
  bomby.forEach(bm => {
    const post = 1 - bm.lont / bm.max;
    ctx.save(); ctx.globalAlpha = 0.14 + post * 0.18; ctx.fillStyle = '#e63c2c'; ctx.beginPath(); ctx.arc(bm.x, bm.y, bm.r, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = 0.85; ctx.strokeStyle = '#ff6a4a'; ctx.lineWidth = 2; ctx.setLineDash([8, 6]); ctx.lineDashOffset = -t / 30; ctx.beginPath(); ctx.arc(bm.x, bm.y, bm.r, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
    ctx.globalAlpha = 1; ctx.strokeStyle = '#ffd24a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(bm.x, bm.y, bm.r * post, 0, Math.PI * 2); ctx.stroke();
    rysujIk(ctx, '💣', bm.x + (Math.random() - 0.5) * 3 * (1 + post * 2), bm.y, 22);
    ctx.restore();
  });
}

function rysujLupy() {
  const t = Date.now();
  skrzynieNaZiemi.forEach(sk => {
    if (!naEkranie(sk.x, sk.y)) return;
    const kol = TIERY[sk.tier].kolor, ex = sk.x, ey = sk.y + Math.sin((sk.faza || 0) * 3) * 1.5, s = sk.boss ? 1.3 : 1;
    rysujPoswiate(ex, ey, (30 + Math.sin(t / 380 + (sk.faza || 0)) * 4) * s, kol, 0.95);
    ctx.save(); ctx.translate(ex, ey); ctx.scale(s, s);
    ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.beginPath(); ctx.ellipse(0, 11, 15, 4, 0, 0, Math.PI * 2); ctx.fill();
    ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(14,8,18,0.95)'; ctx.lineWidth = 2;
    // skrzynia: korpus, wieko z łukiem, okucia w kolorze tieru, zamek z kamieniem
    ctx.fillStyle = '#6b4424'; ctx.beginPath(); ctx.rect(-14, -6, 28, 16); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#86562c'; ctx.beginPath(); ctx.moveTo(-14, -6); ctx.lineTo(-14, -11); ctx.quadraticCurveTo(0, -20, 14, -11); ctx.lineTo(14, -6); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = 'rgba(40,22,10,0.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-14, 2); ctx.lineTo(14, 2); ctx.stroke();
    ctx.fillStyle = kol; [-10.5, 7.5].forEach(x => { ctx.fillRect(x, -15.5 + Math.abs(x) * 0.12, 3, 25.5 - Math.abs(x) * 0.12); });
    ctx.fillRect(-14, -7.2, 28, 2.2);
    ctx.drawImage(odznaka(sk.tier === 'p' ? 'p' : 't' + sk.tier, 48), -6.5, -9, 13, 13);
    ctx.restore();
  });
  monety.forEach(m => {
    if (!naEkranie(m.x, m.y, 20)) return;
    const s2 = 0.55 + 0.45 * Math.abs(Math.cos(m.faza)), r = 4.5 + Math.min(3, m.v * 0.25);
    ctx.drawImage(SPR_MONETA, m.x - r * s2, m.y - r, r * 2 * s2, r * 2);
  });
  kulki.forEach(k => {
    if (!naEkranie(k.x, k.y, 20)) return;
    const r = (11 + Math.min(7, k.xp * 0.3)) * (0.9 + Math.sin(k.faza) * 0.1);
    ctx.drawImage(SPR_KULKA, k.x - r, k.y - r, r * 2, r * 2);
  });
}

// ---------- jakość efektów: gdy gra zaczyna zwalniać, sama ścisza efekty ----------
const JAKOSC = { poziom: 0, sr: 16.7, wolno: 0, szybko: 0, spadki: 0 };
function mierzKlatke(ms) {
  if (stan !== 'walka' || !(ms > 0) || ms > 200) return;
  JAKOSC.sr += (ms - JAKOSC.sr) * 0.04;
  // średnio wolniej niż ~48 klatek/s przez półtorej sekundy - lżejsze efekty
  if (JAKOSC.sr > 20.5) { if (++JAKOSC.wolno > 90 && JAKOSC.poziom < 2) { JAKOSC.poziom++; JAKOSC.spadki++; JAKOSC.wolno = 0; JAKOSC.szybko = 0; JAKOSC.sr = 17; } }
  else JAKOSC.wolno = Math.max(0, JAKOSC.wolno - 1);
  // długo płynnie - wracamy do pełnych (najwyżej raz, żeby nie przełączać w kółko)
  if (JAKOSC.sr < 17.5) { if (++JAKOSC.szybko > 1500 && JAKOSC.poziom > 0 && JAKOSC.spadki < 2) { JAKOSC.poziom--; JAKOSC.szybko = 0; } } else JAKOSC.szybko = 0;
}
// 0 - pełne, 1 - lżejsze (bez poświat pocisków), 2 - oszczędne
function poziomEfektow() { return USTAW.efekty === 'oszczedne' ? 2 : JAKOSC.poziom; }

// gotowe poświaty (miękkie kółka w kolorze) - zamiast kosztownego shadowBlur
const SPR_POSWIATY = new Map();
function rgbKoloru(k) {
  if (k && k[0] === '#') { const h = k.length === 4 ? k.slice(1).split('').map(c => c + c).join('') : k.slice(1, 7); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
  const m = /(\d+)\D+(\d+)\D+(\d+)/.exec(k || ''); return m ? [+m[1], +m[2], +m[3]] : [255, 255, 255];
}
function poswiata(kolor, sila) {
  const k = kolor + '|' + (sila || 1);
  let c = SPR_POSWIATY.get(k);
  if (!c) {
    const [r, g, b] = rgbKoloru(kolor), a = 0.55 * (sila || 1);
    c = sprite(48, (x, R) => { const gr = x.createRadialGradient(R, R, 0, R, R, R); gr.addColorStop(0, 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')'); gr.addColorStop(0.45, 'rgba(' + r + ',' + g + ',' + b + ',' + (a * 0.45) + ')'); gr.addColorStop(1, 'rgba(' + r + ',' + g + ',' + b + ',0)'); x.fillStyle = gr; x.fillRect(0, 0, R * 2, R * 2); });
    SPR_POSWIATY.set(k, c);
  }
  return c;
}
function rysujPoswiate(x, y, R, kolor, sila) { ctx.drawImage(poswiata(kolor, sila), x - R, y - R, R * 2, R * 2); }

// Wrogowie: emoji z ciemnym obrysem, kołysanie w marszu, pojawianie się i znikanie,
// biały błysk przy trafieniu, kolorowy krąg pod stopami.
const smierciWrogow = [], iskry = [];
let poprzedniWrogowie = new Map();
function wysokie(p) { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); }
function dodajIskry(x, y, kolor, n, sila) {
  if (iskry.length > 90) return;
  for (let i = 0; i < n; i++) { const k = Math.random() * 6.283, v = (90 + Math.random() * 170) * (sila || 1); iskry.push({ x: x, y: y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, t: 0, max: 0.16 + Math.random() * 0.1, kolor: kolor }); }
}
const SPR_PODSTAW = new Map();
function podstawaWroga(kolor, r, ranga) {
  const rr = Math.round(r), k = kolor + '|' + rr + '|' + ranga;
  let c = SPR_PODSTAW.get(k);
  if (!c) {
    const S = 3, sz = rr * 2.1, x0 = document.createElement('canvas'); x0.width = Math.ceil(sz * S); x0.height = Math.ceil(sz * 0.4 * S);
    const x = x0.getContext('2d'); x.scale(S, S); const cx = sz / 2, cy = sz * 0.2;
    x.fillStyle = 'rgba(0,0,0,0.38)'; x.beginPath(); x.ellipse(cx, cy, rr * 0.9, rr * 0.35, 0, 0, Math.PI * 2); x.fill();
    if (kolor) { x.globalAlpha = ranga ? 0.9 : 0.5; x.strokeStyle = kolor; x.lineWidth = ranga === 2 ? 2.6 : (ranga ? 2 : 1.4); x.beginPath(); x.ellipse(cx, cy, rr * 0.95, rr * 0.38, 0, 0, Math.PI * 2); x.stroke(); }
    x0.sz = sz; c = x0; SPR_PODSTAW.set(k, c);
  }
  return c;
}
function rysujWrogow() {
  const t = Date.now(), teraz = performance.now(), q = poziomEfektow();
  const obecni = new Map();
  for (let i = 0; i < wrogowie.length; i++) {
    const w = wrogowie[i];
    if (w.martwy) continue;
    obecni.set(w.id, w);
    if (w._ur === undefined) { w._ur = teraz; w._px = w.x; w._py = w.y; w._faza = Math.random() * 6.28; w._lean = 0; w._hpP = w.hpMax ? w.hp / w.hpMax : 1; }
    const dx = w.x - w._px, dy = w.y - w._py, dl = Math.hypot(dx, dy); w._px = w.x; w._py = w.y;
    if (dl < 40) { w._faza += Math.min(dl, 6) * 0.17; w._lean += ((dl > 0.2 ? Math.sign(dx) * 0.12 : 0) - w._lean) * 0.12; w._ruch = (w._ruch || 0) * 0.85 + Math.min(1, dl / 1.2) * 0.15; }
    if (!naEkranie(w.x, w.y, w.r + 40)) continue;
    const wys = w.wysokosc || 0, ey = w.y - wys;
    // zamach przed ciosem: czerwony klin w stronę celu, wypełnia się do momentu uderzenia
    const zp = w.zamach > 0 && w.zamachMax ? 1 - w.zamach / w.zamachMax : (w.zamP || 0);
    if (zp > 0) {
      const R = w.r + 6 + ZASIEG_ZAMACHU + 13, k = w.zamKat || 0, pol = 0.85;
      ctx.save();
      ctx.fillStyle = 'rgba(255,60,40,' + (0.12 + 0.16 * zp).toFixed(3) + ')';
      ctx.beginPath(); ctx.moveTo(w.x, w.y); ctx.arc(w.x, w.y, R, k - pol, k + pol); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,90,60,' + (0.25 + 0.3 * zp).toFixed(3) + ')';
      ctx.beginPath(); ctx.moveTo(w.x, w.y); ctx.arc(w.x, w.y, w.r * 0.6 + (R - w.r * 0.6) * zp, k - pol, k + pol); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = 'rgba(255,120,90,0.85)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(w.x, w.y, R, k - pol, k + pol); ctx.stroke();
      ctx.restore();
    }
    const wiek = (teraz - w._ur) / 260, poj = wiek >= 1 ? 1 : Math.max(0.05, wysokie(Math.max(0, wiek)));
    const ruch = w.boss ? 0.45 : (w._ruch || 0), kol = Math.sin(w._faza);
    const bob = w.duch ? Math.sin(t / 380 + w.id) * 3 : -Math.abs(kol) * w.r * 0.13 * ruch;
    const kat = w._lean * ruch + kol * 0.085 * ruch;
    ctx.save();
    // cień i krąg pod stopami (kolor wroga; elity złote, boss mocniejszy) - gotowy obrazek
    const pod = podstawaWroga(w.sojusznik || (q > 0 && !w.elita && !w.boss) ? '' : (w.elita ? '#ffd24a' : (w.zauroczony > 0 ? '#ff7ae0' : w.kolor)), w.r, w.boss ? 2 : (w.elita ? 1 : 0));
    ctx.drawImage(pod, w.x - pod.sz * poj / 2, w.y + w.r * 0.8 - pod.sz * 0.4 * poj / 2, pod.sz * poj, pod.sz * 0.4 * poj);
    // poświata: elita, boss, zauroczony, szykujący atak
    if (q < 2) {
      if (w.przygotowanie > 0) rysujPoswiate(w.x, ey, w.r * 2.6, '#ffd24a', 1.3);
      else if (w.boss) rysujPoswiate(w.x, ey, w.r * (2.3 + Math.sin(t / 220) * 0.15), w.poswiata || w.kolor, 1);
      else if (w.zauroczony > 0) rysujPoswiate(w.x, ey, w.r * 2.2, '#ff7ae0', 1);
      else if (w.elita) rysujPoswiate(w.x, ey, w.r * (2.1 + Math.sin(t / 260) * 0.12), '#ffd24a', 0.85);
    }
    ctx.translate(w.x, ey + bob); if (q < 2 && kat) ctx.rotate(kat);
    const sx = poj * (1 + 0.05 * kol * ruch), sy = poj * (1 - 0.05 * kol * ruch);
    if (sx !== 1 || sy !== 1) ctx.scale(sx, sy);
    if (w.duch) ctx.globalAlpha = 0.65;
    const tw = w.obraz && OBRAZY_TWARZY[w.obraz];
    if (tw && tw.complete && tw.naturalWidth) {
      const rr = w.r * 1.12;
      ctx.beginPath(); ctx.arc(0, 0, rr + 2.2, 0, Math.PI * 2); ctx.fillStyle = w.elita ? '#ffd24a' : w.kolor; ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.arc(0, 0, rr, 0, Math.PI * 2); ctx.clip(); ctx.drawImage(tw, -rr, -rr, rr * 2, rr * 2); ctx.restore();
      rysujIk(ctx, w.ik, rr * 0.78, rr * 0.72, w.r * 0.85, 'o');
    } else {
      const blysk = w.trafiony > 0 ? Math.min(1, w.trafiony / 0.1) * 0.5 : 0;
      if (!rysujWygladWroga(w, blysk, kat)) {
        rysujIk(ctx, w.ik, 0, 0, w.r * 1.7, w.kolor === '#9a9aaa' ? 'so' : 'o', SKALA_RYS);
        if (blysk > 0) { ctx.globalAlpha = blysk * (w.duch ? 0.65 : 1); rysujIk(ctx, w.ik, 0, 0, w.r * 1.7, 'b', SKALA_RYS); }
      }
    }
    ctx.restore();
    if (w.trafiony > 0 && !w._tr && q === 0 && teraz - (w._tIskry || 0) > 140) { w._tIskry = teraz; dodajIskry(w.x, ey, w.elita ? '#ffe08a' : '#fff4d8', 3); }
    w._tr = w.trafiony > 0;
    ctx.save();
    if (w.zauroczony > 0) rysujIk(ctx, w.sojusznik ? '💀' : '💗', w.x, ey - w.r - 14, 12, 'o');
    if (w.spow > 0 && w.spowCzas > 0) { ctx.globalAlpha = 0.85; ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 1.6; ctx.setLineDash([3, 3]); ctx.lineDashOffset = -t / 60; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 4, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; }
    if (w.ogl > 0) for (let s = 0; s < 3; s++) { const k = t / 200 + s * 2.1; rysujIk(ctx, '⭐', w.x + Math.cos(k) * w.r * 0.8, ey - w.r - 2 + Math.sin(k) * 3, 10); }
    if (w.ogien) rysujIk(ctx, '🔥', w.x + w.r * 0.7, ey - w.r * 0.7 + Math.sin(t / 120) * 1.2, 11);
    if (w.krew) rysujIk(ctx, '🩸', w.x - w.r * 0.7, ey - w.r * 0.7, 9);
    if (w.naznaczony > 0) { ctx.strokeStyle = 'rgba(230,60,60,0.8)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 7, 0, Math.PI * 2); ctx.stroke(); }
    if (w.tarcza > 0) { ctx.strokeStyle = 'rgba(230,240,255,0.85)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 3, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * w.tarcza / w.tarczaMax); ctx.stroke(); }
    if (w.pole) { ctx.globalAlpha = 0.12; ctx.fillStyle = '#5aa8ff'; ctx.beginPath(); ctx.arc(w.x, w.y, 190, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 0.5; ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 2; ctx.setLineDash([9, 7]); ctx.lineDashOffset = t / 40; ctx.beginPath(); ctx.arc(w.x, w.y, 190, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; }
    if (w.elita && (w.afIk || w.afiksy.length)) rysujIki(ctx, w.afIk || w.afiksy.map(a => AFIKSY[a] ? AFIKSY[a].ik : '').join(''), w.x, ey - w.r - 16, 9, 'o');
    ctx.restore();
    // pasek zdrowia: biała część pokazuje świeżo zadane obrażenia
    const proc = Math.max(0, Math.min(1, w.hp / w.hpMax));
    w._hpP = w._hpP === undefined || w._hpP < proc ? proc : w._hpP + (proc - w._hpP) * 0.08;
    if (!w.boss && (proc < 1 || w.elita)) {
      const sz = Math.max(18, w.r * 2), y = ey - w.r - 10, x = w.x - sz / 2;
      ctx.fillStyle = 'rgba(0,0,0,0.7)'; ctx.fillRect(x - 1, y - 1, sz + 2, 6);
      if (w._hpP > proc) { ctx.fillStyle = 'rgba(255,240,220,0.85)'; ctx.fillRect(x, y, sz * w._hpP, 4); }
      ctx.fillStyle = w.zauroczony > 0 ? '#ff7ae0' : (w.elita ? '#ffb03c' : '#e0453a'); ctx.fillRect(x, y, sz * proc, 4);
      ctx.fillStyle = 'rgba(255,255,255,0.22)'; ctx.fillRect(x, y, sz * proc, 1.3);
    }
  }
  // wrogowie, którzy zniknęli od ostatniej klatki - krótka animacja „puf”
  if (stan === 'walka' || stan === 'pauza') {
    let n = 0;
    poprzedniWrogowie.forEach((w, id) => {
      if (obecni.has(id) || n >= 24 || !naEkranie(w.x, w.y, 40)) return;
      n++; smierciWrogow.push({ x: w.x, y: w.y - (w.wysokosc || 0), ik: w.ik, r: w.r, kolor: w.kolor, t0: teraz, boss: w.boss, kat: w._lean || 0 });
      if (q < 2) dodajIskry(w.x, w.y - (w.wysokosc || 0), w.kolor || '#ffffff', w.boss ? 14 : 5, w.boss ? 1.8 : 1);
    });
  }
  poprzedniWrogowie = obecni;
  for (let i = smierciWrogow.length - 1; i >= 0; i--) {
    const s = smierciWrogow[i], p = (teraz - s.t0) / (s.boss ? 700 : 300);
    if (p >= 1 || p < 0) { smierciWrogow.splice(i, 1); continue; }
    ctx.save();
    ctx.globalAlpha = (1 - p) * 0.8; ctx.strokeStyle = s.kolor || '#fff'; ctx.lineWidth = 3 * (1 - p) + 0.5;
    ctx.beginPath(); ctx.arc(s.x, s.y, s.r * (0.6 + p * 1.5), 0, Math.PI * 2); ctx.stroke();
    ctx.translate(s.x, s.y - p * 6); ctx.rotate(s.kat + p * 0.6); const sk = 1 + p * 0.35; ctx.scale(sk, sk * (1 - p * 0.5));
    ctx.globalAlpha = (1 - p) * (1 - p);
    const pw = { ik: s.ik, r: s.r, kolor: s.kolor, id: 0, _faza: 0, _ruch: 0 };
    if (!rysujWygladWroga(pw, p < 0.45 ? (1 - p / 0.45) * 0.8 : 0, 0)) {
      rysujIk(ctx, s.ik, 0, 0, s.r * 1.7, 'o', SKALA_RYS);
      if (p < 0.45) { ctx.globalAlpha = (1 - p / 0.45) * 0.8; rysujIk(ctx, s.ik, 0, 0, s.r * 1.7, 'b', SKALA_RYS); }
    }
    ctx.restore();
  }
}

// Nakrycia głowy postaci (głowa: środek (0,-13), promień ~7,6) — każda klasa wygląda inaczej
function rysujNakrycieGlowy(c, typ, k, kol) {
  const sciezka = (f) => { c.beginPath(); f(); c.fill(); };
  const obrys = () => { c.strokeStyle = 'rgba(0,0,0,0.45)'; c.lineWidth = 0.8; c.stroke(); };
  switch (typ) {
    case 'maska':   // Assassin: ciemny kaptur i chusta na twarz
      c.fillStyle = '#20202c'; sciezka(() => { c.arc(0, -14, 9.4, Math.PI * 0.9, Math.PI * 2.1); c.lineTo(9, -6); c.lineTo(-9, -6); c.closePath(); }); obrys();
      c.fillStyle = '#3a2a5a'; sciezka(() => { c.moveTo(-7.4, -10.6); c.lineTo(7.4, -10.6); c.lineTo(6.6, -6.2); c.quadraticCurveTo(0, -4.4, -6.6, -6.2); c.closePath(); }); obrys();
      c.fillStyle = '#c8b8ff'; c.fillRect(-5, -12.6, 2.6, 0.9); c.fillRect(2.6, -12.6, 2.6, 0.9); break;
    case 'slomkowy':   // Farmer: słomkowy kapelusz z szerokim rondem
      c.fillStyle = '#e6c56a'; sciezka(() => c.ellipse(0, -17.8, 14.5, 3.4, 0, 0, Math.PI * 2)); obrys();
      sciezka(() => { c.moveTo(-7, -18); c.quadraticCurveTo(-6.4, -26, 0, -26.4); c.quadraticCurveTo(6.4, -26, 7, -18); c.closePath(); }); obrys();
      c.fillStyle = '#c0392b'; c.fillRect(-7, -20.4, 14, 2); c.strokeStyle = 'rgba(120,80,20,0.6)'; c.lineWidth = 0.6;
      for (let i = -12; i <= 12; i += 4) { c.beginPath(); c.moveTo(i, -19.5); c.lineTo(i * 1.05, -16.4); c.stroke(); } break;
    case 'kajdany': c.fillStyle = '#8a8a96'; sciezka(() => c.ellipse(0, -5.2, 7.2, 2.1, 0, 0, Math.PI * 2)); c.strokeStyle = '#5a5a66'; c.lineWidth = 1.2; c.beginPath(); c.arc(4, -2.5, 1.6, 0, Math.PI * 2); c.arc(6.5, -0.5, 1.6, 0, Math.PI * 2); c.stroke(); break;
    case 'helm': c.fillStyle = '#c8ccd8'; sciezka(() => { c.arc(0, -13.5, 8.6, Math.PI, Math.PI * 2); c.lineTo(8.6, -9); c.lineTo(5.5, -9); c.lineTo(5.5, -12); c.lineTo(-5.5, -12); c.lineTo(-5.5, -9); c.lineTo(-8.6, -9); c.closePath(); }); obrys();
      c.fillStyle = '#2a2a34'; c.fillRect(-5, -12.3, 10, 1.1); c.fillStyle = '#c0392b'; sciezka(() => { c.moveTo(-1, -22); c.quadraticCurveTo(-7, -27, -9, -21); c.quadraticCurveTo(-5, -22, -1, -20); }); break;
    case 'melonik': c.fillStyle = '#1e5a2a'; sciezka(() => c.ellipse(0, -18.6, 10.5, 2.3, 0, 0, Math.PI * 2)); sciezka(() => { c.arc(0, -19, 6.4, Math.PI, Math.PI * 2); }); c.fillStyle = '#e6c15c'; c.fillRect(-6.3, -20.3, 12.6, 1.3);
      c.fillStyle = '#6ae07a'; [[-2.4, -23], [-0.8, -24.6], [0.8, -23]].forEach(([x, y]) => sciezka(() => c.arc(x + 3, y, 1.2, 0, Math.PI * 2))); break;
    case 'kaptur': c.fillStyle = k; sciezka(() => { c.arc(0, -14, 9.6, Math.PI * 0.92, Math.PI * 2.08); c.lineTo(9.4, -5); c.lineTo(7.2, -5); c.lineTo(7.4, -12); c.quadraticCurveTo(0, -19.5, -7.4, -12); c.lineTo(-7.2, -5); c.lineTo(-9.4, -5); c.closePath(); }); obrys();
      if (kol.piorko) { c.fillStyle = kol.piorko; sciezka(() => c.ellipse(7.5, -22, 1.3, 4.2, 0.5, 0, Math.PI * 2)); } break;
    case 'opaska': c.fillStyle = kol.wlosy; sciezka(() => c.arc(0, -22, 2.6, 0, Math.PI * 2)); c.fillStyle = '#c0392b'; c.fillRect(-8, -17.2, 16, 2.4); sciezka(() => { c.moveTo(-7.5, -16.5); c.lineTo(-12.5, -14); c.lineTo(-11.5, -12.5); c.lineTo(-7.5, -15); }); break;
    case 'kapeluszMaga': c.fillStyle = k; sciezka(() => c.ellipse(0, -18.6, 11.5, 2.5, 0, 0, Math.PI * 2)); sciezka(() => { c.moveTo(-6.5, -19); c.quadraticCurveTo(-2, -27, 4.5, -34); c.quadraticCurveTo(2.5, -26, 6.5, -19); c.closePath(); }); obrys();
      c.fillStyle = '#ffe08a'; c.font = '5px sans-serif'; c.textAlign = 'center'; c.fillText('★', 0.5, -22); break;
    case 'rogi': c.fillStyle = '#9a9aa6'; sciezka(() => { c.arc(0, -14, 8.4, Math.PI, Math.PI * 2); c.closePath(); }); obrys(); c.fillStyle = '#e8dcc0';
      sciezka(() => { c.moveTo(-7.5, -16); c.quadraticCurveTo(-13, -18, -12.5, -26); c.quadraticCurveTo(-10.5, -20, -6, -19.5); c.closePath(); }); sciezka(() => { c.moveTo(7.5, -16); c.quadraticCurveTo(13, -18, 12.5, -26); c.quadraticCurveTo(10.5, -20, 6, -19.5); c.closePath(); }); break;
    case 'cylinder': c.fillStyle = '#1a1a22'; sciezka(() => c.ellipse(0, -18.6, 10, 2.2, 0, 0, Math.PI * 2)); c.fillRect(-5.6, -30, 11.2, 11.6); c.fillStyle = '#e6c15c'; c.fillRect(-5.6, -21.6, 11.2, 1.8); break;
    case 'kowboj': c.fillStyle = '#7a4a2a'; sciezka(() => { c.ellipse(0, -18.4, 13, 2.8, 0, 0, Math.PI * 2); }); sciezka(() => { c.moveTo(-6, -18.5); c.lineTo(-5.5, -25); c.quadraticCurveTo(0, -23, 5.5, -25); c.lineTo(6, -18.5); c.closePath(); }); obrys(); c.fillStyle = '#2a1a10'; c.fillRect(-6, -20.6, 12, 1.4); break;
    case 'gogle': c.fillStyle = '#6a4a2a'; sciezka(() => { c.arc(0, -14, 8.3, Math.PI, Math.PI * 2); c.closePath(); }); c.fillStyle = '#2a2a2a'; c.fillRect(-8.2, -17.6, 16.4, 1.8);
      c.fillStyle = '#9fd8ff'; c.strokeStyle = '#3a3a3a'; c.lineWidth = 1; [-3.3, 3.3].forEach(x => { c.beginPath(); c.arc(x, -17.6, 2.5, 0, Math.PI * 2); c.fill(); c.stroke(); }); break;
    case 'kask': c.fillStyle = '#f0c030'; sciezka(() => { c.arc(0, -14.5, 8.6, Math.PI, Math.PI * 2); c.closePath(); }); sciezka(() => c.ellipse(0, -14.5, 10.5, 1.8, 0, 0, Math.PI * 2)); obrys();
      c.fillStyle = '#ffffff'; sciezka(() => c.arc(0, -20.5, 1.8, 0, Math.PI * 2)); c.fillStyle = '#c09020'; c.fillRect(-0.6, -23, 1.2, 8); break;
    case 'wieniec': c.fillStyle = '#4aa04a'; for (let i = 0; i < 7; i++) { const a = Math.PI * (1.05 + i * 0.15); sciezka(() => c.ellipse(Math.cos(a) * 8, -14 + Math.sin(a) * 8, 1.6, 3, a + Math.PI / 2, 0, Math.PI * 2)); }
      c.fillStyle = '#e04a4a'; sciezka(() => c.arc(0, -22, 1.2, 0, Math.PI * 2)); break;
    case 'fedora': c.fillStyle = '#5a1a6a'; sciezka(() => c.ellipse(0, -18.6, 11.5, 2.4, -0.08, 0, Math.PI * 2)); sciezka(() => { c.moveTo(-6, -19); c.lineTo(-5, -25); c.quadraticCurveTo(0, -27, 5, -25); c.lineTo(6, -19); c.closePath(); }); obrys();
      c.fillStyle = '#1a1a1a'; c.fillRect(-6, -21, 12, 1.5); c.fillStyle = '#fff'; c.fillRect(3.2, -26.5, 3.4, 4.6); c.fillStyle = '#c0392b'; c.fillRect(4.3, -25, 1.2, 1.2); break;
    case 'aureola': c.strokeStyle = '#ffe08a'; c.lineWidth = 1.6; c.shadowColor = '#ffe08a'; c.shadowBlur = 6; c.beginPath(); c.ellipse(0, -25, 6.5, 1.8, 0, 0, Math.PI * 2); c.stroke(); c.shadowBlur = 0;
      c.fillStyle = '#9fe8ff'; sciezka(() => { c.moveTo(0, -20.5); c.lineTo(1.8, -18); c.lineTo(0, -15.5); c.lineTo(-1.8, -18); c.closePath(); }); break;
    case 'czaszka': c.fillStyle = '#16141c'; sciezka(() => { c.arc(0, -14, 9.6, Math.PI * 0.92, Math.PI * 2.08); c.lineTo(9.4, -5); c.lineTo(7.2, -5); c.lineTo(7.4, -12); c.quadraticCurveTo(0, -19.5, -7.4, -12); c.lineTo(-7.2, -5); c.lineTo(-9.4, -5); c.closePath(); });
      c.fillStyle = '#e8e4d8'; sciezka(() => c.arc(0, -20, 2.4, 0, Math.PI * 2)); c.fillStyle = '#16141c'; c.fillRect(-1.3, -20.5, 0.9, 0.9); c.fillRect(0.4, -20.5, 0.9, 0.9); break;
    case 'macki': c.fillStyle = '#6a4ac4'; for (let i = 0; i < 3; i++) sciezka(() => { const x = -6 + i * 6; c.moveTo(x - 1.5, -18); c.quadraticCurveTo(x - 3, -24, x + 1, -26); c.quadraticCurveTo(x - 0.5, -22, x + 1.5, -18); c.closePath(); }); break;
  }
}
// Ciało postaci (bez pasków i broni) w układzie postaci: środek (0,0), głowa ~(0,-13).
// Używane na planszy i w portretach (wybór postaci, karta postaci).
function rysujCialo(c, K, krok, odd, fal, mrug) {
  const kol = K.kolory;
  // ciemny kontur sylwetki - postać lepiej odcina się od podłogi
  c.fillStyle = 'rgba(12,8,18,0.7)'; c.beginPath(); c.arc(0, -13 + odd * 0.2, 9.1, 0, Math.PI * 2); c.fill();
  c.beginPath(); c.moveTo(-8.4, -6.4); c.lineTo(8.4, -6.4); c.lineTo(10.6 - fal, 14.2); c.quadraticCurveTo(0, 17, -11.6 - fal, 13.4); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(-11, -5.4); c.lineTo(11, -5.4); c.lineTo(11, 6.5); c.lineTo(-11, 6.5); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(-7.4, 9.5); c.lineTo(7.4, 9.5); c.lineTo(7.6, 15.8); c.lineTo(-7.6, 15.8); c.closePath(); c.fill();
  function zao(x, y, w, h, r, k) { c.fillStyle = k; c.beginPath(); if (c.roundRect) c.roundRect(x, y, w, h, r); else c.rect(x, y, w, h); c.fill(); }
  const gPl = c.createLinearGradient(0, -6, 0, 14); gPl.addColorStop(0, kol.plaszcz[0]); gPl.addColorStop(1, kol.plaszcz[1]);
  c.fillStyle = gPl; c.beginPath(); c.moveTo(-7, -5); c.lineTo(7, -5); c.lineTo(9 - fal, 13); c.quadraticCurveTo(0, 15.5, -10 - fal, 12); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(0,0,0,0.4)'; c.lineWidth = 1; c.stroke();
  const WY = K.wyglad || {};
  if (WY.czapka === 'wampir') { c.fillStyle = '#7a0a1a'; c.beginPath(); c.moveTo(-9.5, -5); c.lineTo(-11, -19); c.lineTo(-4, -8); c.closePath(); c.moveTo(9.5, -5); c.lineTo(11, -19); c.lineTo(4, -8); c.closePath(); c.fill(); }
  zao(-5, 5 + Math.max(0, krok) * 1.5, 4, 8 - Math.max(0, krok) * 1.5, 1.5, '#2f3a4f'); zao(1, 5 + Math.max(0, -krok) * 1.5, 4, 8 - Math.max(0, -krok) * 1.5, 1.5, '#2f3a4f');
  zao(-6 + krok * 1.3, 11, 5.6, 3.6, 1.6, '#4a2c1a'); zao(0.4 - krok * 1.3, 11, 5.6, 3.6, 1.6, '#4a2c1a');
  const gTu = c.createLinearGradient(-7, -6, 7, 8); gTu.addColorStop(0, kol.tunika[0]); gTu.addColorStop(1, kol.tunika[1]);
  c.fillStyle = gTu; c.beginPath(); c.moveTo(-6.5, -5 + odd * 0.3); c.lineTo(6.5, -5 + odd * 0.3); c.lineTo(8.2, 7.5); c.lineTo(-8.2, 7.5); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(0,0,0,0.45)'; c.stroke();
  zao(-7.6, 1.4, 15.2, 2.7, 1, '#5a3a1e'); zao(-1.6, 1.1, 3.2, 3.3, 0.8, '#ffd24a');
  zao(-9.6, -4 - krok * 1.2, 3.4, 8, 1.6, kol.tunika[1]); zao(6.2, -4 + krok * 1.2, 3.4, 8, 1.6, kol.tunika[1]);
  c.fillStyle = kol.skora ? kol.skora[0] : '#efc39a'; c.beginPath(); c.arc(-7.9, 4.6 - krok * 1.2, 1.9, 0, Math.PI * 2); c.arc(7.9, 4.6 + krok * 1.2, 1.9, 0, Math.PI * 2); c.fill();
  const gGl = c.createRadialGradient(-2, -15, 1, 0, -13, 9); gGl.addColorStop(0, kol.skora ? kol.skora[0] : '#f6d2ae'); gGl.addColorStop(1, kol.skora ? kol.skora[1] : '#dca57c');
  c.fillStyle = gGl; c.beginPath(); c.arc(0, -13 + odd * 0.2, 7.6, 0, Math.PI * 2); c.fill(); c.strokeStyle = 'rgba(0,0,0,0.35)'; c.lineWidth = 0.9; c.stroke();
  if (!WY.lysy) {   // krótkie włosy
    c.fillStyle = kol.wlosy; c.beginPath(); c.arc(0, -14.5, 8, Math.PI * 1.02, Math.PI * 1.98); c.fill();
    c.beginPath(); c.moveTo(-7.8, -14); c.lineTo(-6, -15.2); c.lineTo(-3.5, -14.2); c.lineTo(-1, -15.4); c.lineTo(1.8, -14.2); c.lineTo(4.5, -15.3); c.lineTo(7.8, -14); c.lineTo(7.5, -17.5); c.lineTo(-7.5, -17.5); c.closePath(); c.fill();
  } else { c.fillStyle = 'rgba(0,0,0,0.25)'; c.fillRect(-5.5, -15.6, 11, 1.4); }
  c.fillStyle = '#1e1a16';
  if (WY.oczy) {   // wrogowie: świecące oczy
    c.fillStyle = WY.oczy; c.beginPath(); c.ellipse(-2.6, -11.4, 1.5, 1.1, 0.25, 0, Math.PI * 2); c.ellipse(3.2, -11.4, 1.5, 1.1, -0.25, 0, Math.PI * 2); c.fill();
    c.fillStyle = 'rgba(0,0,0,0.6)'; c.fillRect(-4.6, -13.4, 3.4, 0.9); c.fillRect(1.6, -13.4, 3.4, 0.9);
  } else if (mrug) { c.fillRect(-4, -11.6, 2.8, 0.9); c.fillRect(1.7, -11.6, 2.8, 0.9); }
  else { c.beginPath(); c.ellipse(-2.5, -11.3, 1.25, 1.65, 0, 0, Math.PI * 2); c.ellipse(3.1, -11.3, 1.25, 1.65, 0, 0, Math.PI * 2); c.fill(); c.fillStyle = '#fff'; c.fillRect(-2.3, -12.3, 0.7, 0.7); c.fillRect(3.3, -12.3, 0.7, 0.7); }
  if (!WY.oczy) {
    c.fillStyle = 'rgba(0,0,0,0.55)'; c.fillRect(-4.2, -13.6, 3, 0.8); c.fillRect(1.6, -13.6, 3, 0.8);   // brwi
    c.strokeStyle = '#7a3a2a'; c.lineWidth = 0.9; c.beginPath(); c.moveTo(-1.2, -8.4); c.lineTo(2.2, -8.4); c.stroke();
  }
  if (WY.chusta) { c.fillStyle = WY.chusta; c.beginPath(); c.moveTo(-7.4, -9.8); c.lineTo(7.4, -9.8); c.quadraticCurveTo(7, -5.6, 0.3, -5); c.quadraticCurveTo(-6.6, -5.6, -7.4, -9.8); c.fill(); }
  if (WY.uszy) { c.fillStyle = '#e8b890'; c.beginPath(); c.moveTo(-7.2, -13.5); c.lineTo(-12.5, -18.5); c.lineTo(-6.6, -10.6); c.closePath(); c.moveTo(7.2, -13.5); c.lineTo(12.5, -18.5); c.lineTo(6.6, -10.6); c.closePath(); c.fill(); c.strokeStyle = 'rgba(0,0,0,0.35)'; c.lineWidth = 0.6; c.stroke(); }
  if (WY.broda) { c.fillStyle = WY.broda === true ? kol.wlosy : WY.broda; c.beginPath(); c.moveTo(-7, -11); c.quadraticCurveTo(-6.5, -3.5, 0.3, -2.6); c.quadraticCurveTo(7, -3.5, 7.4, -11); c.quadraticCurveTo(4, -7.6, 0.3, -9.4); c.quadraticCurveTo(-3.5, -7.6, -7, -11); c.fill(); }
  rysujNakrycieGlowy(c, WY.czapka, WY.kol || kol.plaszcz[0], kol);
}
function rysujGracza(g) {
  const K = KLASY[g.klasa], kol = K.kolory, rozm = g.roz || 1, hpMaxR = g.hpMaxR || 100;
  const gx = g.x, gy = g.y;
  ctx.save();
  const stK = g.stanKlasy || {}, niewid = g.niewidzialny > 0, nietop = g.forma === 'nietoperz' || g.batAkt, wirAkt = !!stK.wir || g.wirAkt, salwaAkt = stK.salwa > czasGry || g.salwaAkt;
  if (g.powalony) ctx.globalAlpha = 0.45;
  else if (niewid) ctx.globalAlpha = g === lokalnyWidok() || g === lokalny ? 0.32 : 0.1;
  else if (nietop) ctx.globalAlpha = 0.18;
  else if (g.migotanie > 0 || (g.niewr > 0 && Math.floor(Date.now() / 90) % 2)) ctx.globalAlpha = 0.55;
  if (salwaAkt && !g.powalony) { const p = 0.5 + 0.5 * Math.sin(Date.now() / 90); ctx.save(); ctx.globalAlpha = 0.35 + 0.25 * p; ctx.strokeStyle = '#bff4a0'; ctx.lineWidth = 3; ctx.shadowColor = '#9fe8ff'; ctx.shadowBlur = 12; ctx.beginPath(); ctx.arc(gx, gy - 2, 19 * rozm + 2 * p, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.beginPath(); ctx.ellipse(gx, gy + 11 * rozm, 12 * rozm, 4.5 * rozm, 0, 0, Math.PI * 2); ctx.fill();
  if (!g.powalony && !niewid) {   // krąg pod stopami: Twoja postać jasnoniebieski, koledzy złoci
    const ja = g === lokalnyWidok() || (g === lokalny && !(typeof SIEC !== 'undefined' && SIEC.rola === 'klient'));
    ctx.save(); ctx.globalAlpha = 0.55 + 0.15 * Math.sin(Date.now() / 300); ctx.strokeStyle = ja ? '#7ee8ff' : '#ffd27a'; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.ellipse(gx, gy + 11 * rozm, 14 * rozm, 5.4 * rozm, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  }
  const kier = (g.kierX || 0) < -0.15 ? -1 : 1;
  const ruch = g.wRuchu ? 1 : 0;
  g.faza = (g.faza || 0) + (ruch ? 0.22 : 0);
  const krok = ruch ? Math.sin(g.faza) : 0, odd = Math.sin(Date.now() / 420) * 0.6, fal = Math.sin(Date.now() / 180) * (ruch ? 1.6 : 0.6);
  ctx.translate(gx, gy + 2); ctx.scale(kier * g.r / 16 * rozm, g.r / 16 * rozm);
  rysujCialo(ctx, K, krok, odd, fal, (Date.now() % 3800) < 120);
  ctx.restore();
  if (g.powalony) { rysujPowalonego(g); return; }
  if (nietop) { const t = Date.now() / 160;
    for (let i = 0; i < 6; i++) { const a = t + i * 1.05, r = 12 + 6 * Math.sin(t * 1.7 + i); rysujIk(ctx, '🦇', gx + Math.cos(a) * r, gy - 4 + Math.sin(a) * r * 0.7, 15, 'o'); } }
  if (wirAkt) { const t = Date.now() / 70; ctx.save(); ctx.strokeStyle = '#c8c8d8'; ctx.lineWidth = 2.2; ctx.shadowColor = '#ffffff'; ctx.shadowBlur = 6;
    for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(gx, gy - 2, 26 + i * 9, t + i * 2.1, t + i * 2.1 + 1.6); ctx.stroke(); } ctx.restore(); }
  // zastój Zhonyi - złota bańka
  if (g.zastoj > 0) { ctx.save(); ctx.globalAlpha = 0.5; ctx.fillStyle = '#ffd24a'; ctx.beginPath(); ctx.arc(gx, gy - 2, 22 * rozm, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
  // tarcza
  const ts = g.ts || 0;
  if (ts > 0) { ctx.save(); ctx.globalAlpha = 0.35 + Math.min(0.4, ts / hpMaxR); ctx.strokeStyle = '#eef4ff'; ctx.lineWidth = 2.5; ctx.shadowColor = '#bfe0ff'; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(gx, gy - 2, 20 * rozm, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  if (g.spowG > 0 && g.spowGCzas > 0) { ctx.save(); ctx.globalAlpha = 0.8; ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 2; ctx.setLineDash([4, 4]); ctx.lineDashOffset = Date.now() / 50; ctx.beginPath(); ctx.arc(gx, gy, 18 * rozm, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  // pasek zdrowia nad postacią
  const sz = 34, proc = Math.max(0, g.hp / hpMaxR);
  ctx.fillStyle = 'rgba(0,0,0,0.65)'; ctx.fillRect(gx - sz / 2 - 1, gy - 30 * rozm, sz + 2, 6);
  ctx.fillStyle = proc > 0.5 ? '#5fc46a' : (proc > 0.25 ? '#e6c15c' : '#e6543c'); ctx.fillRect(gx - sz / 2, gy - 30 * rozm + 1, sz * proc, 4);
  if (ts > 0) { ctx.fillStyle = 'rgba(240,245,255,0.9)'; ctx.fillRect(gx - sz / 2, gy - 30 * rozm + 1, sz * Math.min(1, ts / hpMaxR), 2); }
  // naładowanie (energia): cienki niebieski pasek; pełny = iskrzy wokół postaci
  const en = g === lokalnyWidok() ? (((lokalny || gracz) || {}).maEnergie ? ((lokalny || gracz).energia || 0) : -1) : (g.en !== undefined ? g.en : -1);
  if (en >= 0) {
    ctx.fillStyle = 'rgba(0,0,0,0.65)'; ctx.fillRect(gx - sz / 2 - 1, gy - 30 * rozm + 6, sz + 2, 3);
    ctx.fillStyle = en >= 100 ? '#bff4ff' : '#4ac4ff'; ctx.fillRect(gx - sz / 2, gy - 30 * rozm + 6.5, sz * Math.min(1, en / 100), 2);
    if (en >= 100) {
      const t = Date.now() / 120;
      ctx.save(); ctx.strokeStyle = '#9fe8ff'; ctx.lineWidth = 1.6; ctx.shadowColor = '#7ae0ff'; ctx.shadowBlur = 8; ctx.globalAlpha = 0.85;
      for (let i = 0; i < 3; i++) { const a = t + i * 2.1, r1 = 15 * rozm, r2 = 21 * rozm; ctx.beginPath(); ctx.moveTo(gx + Math.cos(a) * r1, gy - 2 + Math.sin(a) * r1);
        ctx.lineTo(gx + Math.cos(a + 0.25) * r2, gy - 2 + Math.sin(a + 0.25) * r2); ctx.lineTo(gx + Math.cos(a + 0.45) * (r1 + 2), gy - 2 + Math.sin(a + 0.45) * (r1 + 2)); ctx.stroke(); }
      ctx.restore();
    }
  }
  if (g.nick && (gracze.length > 1 || (typeof SIEC !== 'undefined' && SIEC.rola))) {
    ctx.font = '800 9px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineWidth = 3; ctx.strokeText(g.nick, gx, gy - 33 * rozm); ctx.fillStyle = g === lokalnyWidok() ? '#ffe08a' : '#bfe0ff'; ctx.fillText(g.nick, gx, gy - 33 * rozm);
  }
  // celowanie prawą gałką: strzałka kierunku
  const ckat = g === lokalnyWidok() ? ((lokalny || gracz) || {}).celKat : null;
  if (ckat !== null && ckat !== undefined) {
    ctx.save(); ctx.translate(gx, gy - 2); ctx.rotate(ckat); ctx.globalAlpha = 0.75; ctx.strokeStyle = '#7ae0ff'; ctx.lineWidth = 2; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(24, 0); ctx.lineTo(62, 0); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = '#7ae0ff';
    ctx.beginPath(); ctx.moveTo(70, 0); ctx.lineTo(61, -5); ctx.lineTo(61, 5); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  // bronie wokół postaci
  const n = g.bronie.length;
  g.bronie.forEach((b, i) => {
    let ka = b.kat !== undefined ? b.kat : 0;
    let bx, by;
    if (n === 1) { const w = b.anim > 0 ? 20 : 13; bx = gx + Math.cos(ka) * w; by = gy + Math.sin(ka) * w; }
    else { const ks = -Math.PI / 2 + (i + 0.5) * Math.PI * 2 / n; const r = 22 * rozm; bx = gx + Math.cos(ks) * r; by = gy - 2 + Math.sin(ks) * r * 0.8;
      if (b.anim > 0) { bx += Math.cos(ka) * 7; by += Math.sin(ka) * 7; } }
    if ((b.tier || 0) >= 2 && poziomEfektow() < 2) rysujPoswiate(bx + Math.cos(ka) * 8, by + Math.sin(ka) * 8, 12 + b.tier * 2.5, TIERY[b.tier].kolor, b.tier >= 4 ? 0.75 + 0.25 * Math.sin(Date.now() / 200) : 0.6);
    ctx.save(); ctx.translate(bx, by); ctx.rotate(ka); ctx.shadowColor = 'rgba(8,4,12,0.75)'; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 1.4 * DPR; ctx.shadowBlur = 0;
    rysujKsztaltBroni(ctx, b); ctx.restore();
  });
  if (g.blysk > 0 && !g._blyskByl) { dodajIskry(gx, gy - 4, '#ffe08a', 10, 1.5); dodajIskry(gx, gy - 4, '#ffffff', 5, 1.1); }
  g._blyskByl = g.blysk > 0;
  if (g.blysk > 0) {
    const p = 1 - g.blysk / 1.2;
    if (p < 0.6 && poziomEfektow() < 2) {   // słup światła przy awansie
      const a = (1 - p / 0.6); ctx.save(); ctx.globalAlpha = a * 0.5; const gr = ctx.createLinearGradient(0, gy - 90, 0, gy + 10); gr.addColorStop(0, 'rgba(255,224,138,0)'); gr.addColorStop(1, 'rgba(255,224,138,0.9)');
      ctx.fillStyle = gr; ctx.fillRect(gx - 14 * a, gy - 90, 28 * a, 100); ctx.restore();
    }
    ctx.save(); ctx.globalAlpha = Math.max(0, g.blysk / 1.2) * 0.85; ctx.strokeStyle = '#ffe08a'; ctx.lineWidth = 4 - p * 2.6;
    ctx.beginPath(); ctx.arc(gx, gy, 16 + p * 92, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  }
}
// Portret postaci (taki jak na planszy, z bronią startową) jako obrazek - do wyboru postaci i karty postaci
const PORTRETY = {};
function portretPostaci(klasa, px) {
  px = px || 112;
  const k = klasa + '|' + px;
  if (PORTRETY[k]) return PORTRETY[k];
  const K = KLASY[klasa]; if (!K) return '';
  try {
    const c = document.createElement('canvas'); c.width = c.height = px;
    const x = c.getContext('2d'), S = px / 50;
    x.translate(px * 0.47, px * 0.62); x.scale(S, S);
    x.fillStyle = 'rgba(0,0,0,0.35)'; x.beginPath(); x.ellipse(0, 12.5, 12, 3.6, 0, 0, Math.PI * 2); x.fill();
    const br = BRONIE[K.start] ? K.start : null;
    x.save(); x.scale(0.95, 0.95); rysujCialo(x, K, 0, 0, 0.6, false); x.restore();
    if (br) { x.save(); x.translate(9, 3); x.rotate(-1.0); x.shadowColor = 'rgba(0,0,0,0.6)'; x.shadowOffsetY = S * 0.8; rysujKsztaltBroni(x, { rodzaj: br, tier: 1, kat: -1.0, anim: 0 }); x.restore(); }
    PORTRETY[k] = c.toDataURL('image/png');
  } catch (e) { PORTRETY[k] = ''; }
  return PORTRETY[k];
}
function htmlPortretu(klasa, px) {
  const K = KLASY[klasa], src = portretPostaci(klasa, (px || 64) * 2);
  return '<div class="port" style="--kp:' + K.kolory.plaszcz[0] + ';width:' + (px || 64) + 'px;height:' + (px || 64) + 'px">' + (src ? '<img class="p" alt="" src="' + src + '">' : '<span style="font-size:30px">' + K.ik + '</span>') + '<span class="ikk">' + K.ik + '</span></div>';
}
function lokalnyWidok() { return (typeof SIEC !== 'undefined' && SIEC.rola === 'klient') ? SIEC.mojWidok : lokalny; }
function rysujPowalonego(g) {
  const t = Date.now();
  ctx.save(); rysujIk(ctx, '💀', g.x, g.y - 26, 18, 'o');
  ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(g.x, g.y, 26, 0, Math.PI * 2); ctx.stroke();
  if (g.reanim > 0) { ctx.strokeStyle = '#7ee87a'; ctx.beginPath(); ctx.arc(g.x, g.y, 26, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, g.reanim / CZAS_PODNOSZENIA)); ctx.stroke(); }
  ctx.globalAlpha = 0.5 + 0.3 * Math.sin(t / 200); ctx.strokeStyle = '#ff6a5a'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.arc(g.x, g.y, 52, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
  if (g.nick) { ctx.globalAlpha = 1; ctx.font = '800 9px system-ui, sans-serif'; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineWidth = 3; ctx.strokeText(g.nick, g.x, g.y - 40); ctx.fillStyle = '#ff9a8a'; ctx.fillText(g.nick, g.x, g.y - 40); }
  ctx.restore();
}
// stworzenia gracza (działka, krzaki, pszczoły...) - u klienta z ostatniego stanu od gospodarza
function rysujStwory() {
  const t = Date.now();
  const lista = (typeof SIEC !== 'undefined' && SIEC.rola === 'klient') ? (SIEC.stwory || []) : stwory;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const s of lista) {
    if (!naEkranie(s.x, s.y, 60)) continue;
    const T = TYPY_STWOROW[s.typ] || {};
    const proc = s.max > 9000 || s.max === undefined ? 1 : Math.max(0, s.czas / s.max);
    if (s.aura && (s.typ === 'totem' || s.typ === 'krzak' || s.typ === 'wabik')) { ctx.save(); ctx.globalAlpha = 0.1; ctx.fillStyle = s.typ === 'totem' ? '#ff7a3c' : (s.typ === 'wabik' ? '#ff9a3c' : '#7ee87a'); ctx.beginPath(); ctx.arc(s.x, s.y, s.aura, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
    if (s.typ === 'dziura') {
      ctx.save(); const g = ctx.createRadialGradient(s.x, s.y, 2, s.x, s.y, s.r || 120); g.addColorStop(0, 'rgba(10,0,30,0.85)'); g.addColorStop(0.4, 'rgba(90,40,180,0.35)'); g.addColorStop(1, 'rgba(90,40,180,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(s.x, s.y, s.r || 120, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(200,170,255,0.6)'; ctx.lineWidth = 2; for (let n = 0; n < 3; n++) { ctx.beginPath(); ctx.arc(s.x, s.y, 12 + n * 10, t / 200 + n * 2, t / 200 + n * 2 + 3.5); ctx.stroke(); } ctx.restore(); continue;
    }
    if (T.wiezyczka) {
      ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(s.x, s.y + 9, 13, 5, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#3a3a46'; ctx.beginPath(); ctx.arc(s.x, s.y + 2, 10, 0, Math.PI * 2); ctx.fill();
      ctx.translate(s.x, s.y - 2); ctx.rotate(s.kat || 0);
      ctx.fillStyle = T.kolor || '#b8b8c8';
      if (s.typ === 'tesla') { ctx.beginPath(); ctx.arc(0, 0, 6, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#e8f8ff'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(0, 0, 9 + Math.sin(t / 80) * 1.5, 0, Math.PI * 2); ctx.stroke(); }
      else { ctx.fillRect(-6, -6, 12, 12); ctx.fillStyle = '#20202a'; ctx.fillRect(4, s.typ === 'dzialoGromu' ? -3.5 : -2, s.typ === 'dzialoGromu' ? 14 : 11, s.typ === 'dzialoGromu' ? 7 : 4); }
      ctx.restore();
    } else {
      const bob = (s.typ === 'pszczola' || s.typ === 'smok' || s.typ === 'owoc') ? Math.sin(t / 150 + s.x) * 2.5 : 0;
      const roz = s.typ === 'krzak' ? (s.ik === '🌲' ? 30 : 24) : s.typ === 'owoc' ? 15 : s.typ === 'pszczola' ? 13 : s.typ === 'smok' || s.typ === 'wilk' ? 22 : 20;
      if (s.typ === 'mina' || s.typ === 'wnyki') { ctx.save(); ctx.globalAlpha = 0.85; }
      if (s.typ === 'wilk' && Math.cos(s.kat || 0) > 0) { ctx.save(); ctx.translate(s.x, s.y + bob); ctx.scale(-1, 1); rysujIk(ctx, s.ik, 0, 0, roz); ctx.restore(); }
      else rysujIk(ctx, s.ik, s.x, s.y + bob, roz);
      if (s.typ === 'mina') { ctx.fillStyle = Math.floor(t / 300) % 2 ? '#ff3a2a' : '#5a1a10'; ctx.beginPath(); ctx.arc(s.x, s.y - 2, 2.2, 0, Math.PI * 2); ctx.fill(); }
      if (s.typ === 'mina' || s.typ === 'wnyki') ctx.restore();
    }
    if (proc < 1 && s.typ !== 'owoc' && s.typ !== 'mina' && s.typ !== 'wnyki' && s.typ !== 'pszczola') {
      ctx.strokeStyle = 'rgba(255,224,138,0.75)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(s.x, s.y, (s.typ === 'krzak' ? 18 : 15), -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * proc); ctx.stroke();
    }
  }
}
function rysujOrby() {
  orbyRys.forEach(o => { ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.kat * 2); ctx.fillStyle = o.kolor; ctx.globalAlpha = 0.3; ctx.beginPath(); ctx.arc(0, 0, 10, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1;
    ctx.beginPath(); ctx.moveTo(0, -9); ctx.lineTo(3.5, 0); ctx.lineTo(0, 9); ctx.lineTo(-3.5, 0); ctx.closePath(); ctx.fill(); ctx.restore(); });
}

function rysujPociski() {
  pociski.forEach(p => {
    ctx.save(); ctx.translate(p.x, p.y); const k = Math.atan2(p.vy, p.vx);
    ctx.fillStyle = p.kolor;
    if (p.ksztalt === 'pustka' || p.ksztalt === 'czakram') { ctx.globalAlpha = 0.3; ctx.beginPath(); ctx.arc(0, 0, p.ksztalt === 'pustka' ? 13 : 9, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1; }
    if (p.ksztalt === 'belt' || p.ksztalt === 'strzala') {
      ctx.rotate(k); if (p.duza) { ctx.scale(1.6, 1.6); ctx.shadowColor = '#9fe8ff'; ctx.shadowBlur = 10; } ctx.fillStyle = '#8a6a3c'; ctx.fillRect(-11, -1.2, 18, 2.4);
      ctx.fillStyle = '#d8d8e0'; ctx.beginPath(); ctx.moveTo(11, 0); ctx.lineTo(5, -3.6); ctx.lineTo(5, 3.6); ctx.closePath(); ctx.fill();
      ctx.fillStyle = p.ksztalt === 'belt' ? '#c0392b' : '#f0f0f0'; ctx.beginPath(); ctx.moveTo(-11, 0); ctx.lineTo(-15, -3.6); ctx.lineTo(-8, 0); ctx.lineTo(-15, 3.6); ctx.closePath(); ctx.fill();
    } else if (p.ksztalt === 'wlocznia') {
      ctx.rotate(k); ctx.fillStyle = '#c8b890'; ctx.fillRect(-13, -1.6, 22, 3.2); ctx.fillStyle = '#e0e0ea'; ctx.beginPath(); ctx.moveTo(13, 0); ctx.lineTo(4, -5); ctx.lineTo(4, 5); ctx.closePath(); ctx.fill();
    } else if (p.ksztalt === 'bumerang') {
      ctx.rotate(p.obrot); ctx.strokeStyle = p.kolor; ctx.lineWidth = 4.5; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-7, -9); ctx.lineTo(6, 0); ctx.lineTo(-7, 9); ctx.stroke();
    } else if (p.ksztalt === 'granat') {
      const prog = p.maxZycie ? 1 - p.zycie / p.maxZycie : 0.5; ctx.translate(0, -Math.sin(prog * Math.PI) * 34);
      ctx.fillStyle = '#2a2a30'; ctx.beginPath(); ctx.arc(0, 0, 6, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#ffb070'; ctx.fillRect(-1, -9, 2, 4);
    } else if (p.ksztalt === 'rakieta') {
      ctx.rotate(k); ctx.fillStyle = '#d8d8e0'; ctx.fillRect(-8, -2.5, 13, 5); ctx.fillStyle = '#e6543c'; ctx.beginPath(); ctx.moveTo(9, 0); ctx.lineTo(4, -3); ctx.lineTo(4, 3); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#ffb04a'; ctx.beginPath(); ctx.arc(-10, 0, 2.5 + Math.random() * 1.5, 0, Math.PI * 2); ctx.fill();
    } else if (p.ksztalt === 'kolec') {
      ctx.rotate(k); ctx.fillStyle = '#5ac46a'; ctx.beginPath(); ctx.moveTo(9, 0); ctx.lineTo(-6, -3.5); ctx.lineTo(-3, 0); ctx.lineTo(-6, 3.5); ctx.closePath(); ctx.fill();
    } else if (p.ksztalt === 'kosc') {
      ctx.rotate(Date.now() / 90); ctx.fillStyle = '#e8f4ff'; ctx.fillRect(-6, -1.6, 12, 3.2); ctx.beginPath(); ctx.arc(-6, 0, 2.6, 0, Math.PI * 2); ctx.arc(6, 0, 2.6, 0, Math.PI * 2); ctx.fill();
    } else if (p.ksztalt === 'czakram') {
      ctx.rotate(Date.now() / 60); ctx.strokeStyle = p.kolor || '#e0e8f0'; ctx.lineWidth = 2.6; ctx.beginPath(); ctx.arc(0, 0, 7, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = '#ffffff'; for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2; ctx.beginPath(); ctx.moveTo(Math.cos(a) * 6.5, Math.sin(a) * 6.5); ctx.lineTo(Math.cos(a + 0.4) * 11, Math.sin(a + 0.4) * 11); ctx.lineTo(Math.cos(a + 0.55) * 6.5, Math.sin(a + 0.55) * 6.5); ctx.closePath(); ctx.fill(); }
    } else if (p.ksztalt === 'shuriken') {
      ctx.rotate(Date.now() / 45); ctx.fillStyle = '#d8d8e8'; ctx.beginPath();
      for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2; ctx.lineTo(Math.cos(a) * 9, Math.sin(a) * 9); ctx.lineTo(Math.cos(a + Math.PI / 4) * 3, Math.sin(a + Math.PI / 4) * 3); }
      ctx.closePath(); ctx.fill(); ctx.fillStyle = '#3a3a4a'; ctx.beginPath(); ctx.arc(0, 0, 1.6, 0, Math.PI * 2); ctx.fill();
    } else if (p.ksztalt === 'noz') {
      ctx.rotate(k); ctx.fillStyle = '#3a2a2a'; ctx.fillRect(-9, -1.4, 6, 2.8); ctx.fillStyle = '#e8e8f0'; ctx.beginPath(); ctx.moveTo(-3, -2.2); ctx.lineTo(9, 0); ctx.lineTo(-3, 2.2); ctx.closePath(); ctx.fill();
    } else if (p.ksztalt === 'pustka') {
      ctx.beginPath(); ctx.arc(0, 0, 8, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#1a0a30'; ctx.beginPath(); ctx.arc(0, 0, 4, 0, Math.PI * 2); ctx.fill();
    } else { const im = spritePociskuGracza(p.kolor || '#ffe08a'); ctx.drawImage(im, -im.R, -im.R, im.R * 2, im.R * 2); }
    ctx.restore();
  });
  rysujPociskiWrogow();
}
// Pociski gracza (kule): miękki blask w kolorze i biały środek - bez ciemnego obrysu (ten mają tylko wrogie)
const SPR_POC_GRACZA = new Map();
function spritePociskuGracza(kolor) {
  let c = SPR_POC_GRACZA.get(kolor);
  if (!c) {
    const S = 3, R = 10, [r, g, b] = rgbKoloru(kolor);
    c = document.createElement('canvas'); c.width = c.height = R * 2 * S;
    const x = c.getContext('2d'); x.scale(S, S); x.translate(R, R);
    const gr = x.createRadialGradient(0, 0, 0, 0, 0, R); gr.addColorStop(0, 'rgba(' + r + ',' + g + ',' + b + ',0.55)'); gr.addColorStop(0.5, 'rgba(' + r + ',' + g + ',' + b + ',0.22)'); gr.addColorStop(1, 'rgba(' + r + ',' + g + ',' + b + ',0)');
    x.fillStyle = gr; x.beginPath(); x.arc(0, 0, R, 0, Math.PI * 2); x.fill();
    x.fillStyle = kolor; x.beginPath(); x.arc(0, 0, 5, 0, Math.PI * 2); x.fill();
    x.fillStyle = 'rgba(255,255,255,0.85)'; x.beginPath(); x.arc(-0.8, -0.8, 2.4, 0, Math.PI * 2); x.fill();
    c.R = R; SPR_POC_GRACZA.set(kolor, c);
  }
  return c;
}
// Pociski wrogów: ciemny obrys + jasny środek - dobrze widoczne, ale małe i bez wielkich poświat.
// Przy dużej liczbie pocisków (lub słabszym sprzęcie) bez poświat i smug.
const SPR_POC_WROGA = new Map();
function spritePociskuWroga(kolor, r, poswiata) {
  const k = kolor + '|' + r + '|' + (poswiata ? 1 : 0);
  let c = SPR_POC_WROGA.get(k);
  if (!c) {
    const S = 3, R = (r + (poswiata ? 7 : 2.5));
    c = document.createElement('canvas'); c.width = c.height = Math.ceil(R * 2 * S);
    const x = c.getContext('2d'); x.scale(S, S); x.translate(R, R);
    const [cr, cg, cb] = rgbKoloru(kolor);
    if (poswiata) { const g = x.createRadialGradient(0, 0, r * 0.6, 0, 0, R); g.addColorStop(0, 'rgba(' + cr + ',' + cg + ',' + cb + ',0.32)'); g.addColorStop(1, 'rgba(' + cr + ',' + cg + ',' + cb + ',0)'); x.fillStyle = g; x.beginPath(); x.arc(0, 0, R, 0, Math.PI * 2); x.fill(); }
    x.fillStyle = 'rgba(16,6,18,0.92)'; x.beginPath(); x.arc(0, 0, r + 1.5, 0, Math.PI * 2); x.fill();
    x.fillStyle = kolor; x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.fill();
    const g2 = x.createRadialGradient(-r * 0.25, -r * 0.25, 0, 0, 0, r * 0.75); g2.addColorStop(0, 'rgba(255,255,255,0.95)'); g2.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g2; x.beginPath(); x.arc(0, 0, r * 0.75, 0, Math.PI * 2); x.fill();
    c.R = R; SPR_POC_WROGA.set(k, c);
  }
  return c;
}
function rysujPociskiWrogow() {
  const n = pociskiWrogow.length, q = poziomEfektow(), bogato = q === 0 && n < 45;
  const t = Date.now();
  for (let i = 0; i < n; i++) {
    const p = pociskiWrogow[i];
    if (!naEkranie(p.x, p.y, 30)) continue;
    const v = Math.hypot(p.vx, p.vy) || 1;
    if (p.ksztalt === 'belt') {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(Math.atan2(p.vy, p.vx));
      ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(16,6,18,0.9)'; ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.moveTo(-14, 0); ctx.lineTo(11, 0); ctx.stroke();
      ctx.fillStyle = '#5a2a1a'; ctx.fillRect(-11, -1.1, 17, 2.2);
      ctx.beginPath(); ctx.moveTo(12, 0); ctx.lineTo(4.5, -4.2); ctx.lineTo(4.5, 4.2); ctx.closePath(); ctx.stroke(); ctx.fillStyle = '#ff6a4a'; ctx.fill();
      ctx.fillStyle = '#e0453a'; ctx.beginPath(); ctx.moveTo(-10, 0); ctx.lineTo(-15, -3.8); ctx.lineTo(-7.5, 0); ctx.lineTo(-15, 3.8); ctx.closePath(); ctx.fill();
      ctx.restore(); continue;
    }
    if (p.ksztalt === 'kosc') {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(t / 90);
      ctx.strokeStyle = 'rgba(16,6,18,0.85)'; ctx.lineWidth = 2; ctx.fillStyle = '#e8f4ff';
      ctx.beginPath(); ctx.rect(-6, -1.6, 12, 3.2); ctx.arc(-6, 0, 2.6, 0, Math.PI * 2); ctx.moveTo(8.6, 0); ctx.arc(6, 0, 2.6, 0, Math.PI * 2); ctx.stroke(); ctx.fill();
      ctx.restore(); continue;
    }
    const r = p.r || 5, kol = p.kolor || '#c46ce8';
    if (bogato) {   // krótka smuga za pociskiem
      const dl = Math.min(18, v * 0.045), ux = p.vx / v, uy = p.vy / v;
      ctx.globalAlpha = 0.35; ctx.strokeStyle = kol; ctx.lineCap = 'round'; ctx.lineWidth = r * 1.3;
      ctx.beginPath(); ctx.moveTo(p.x - ux * 2, p.y - uy * 2); ctx.lineTo(p.x - ux * dl, p.y - uy * dl); ctx.stroke(); ctx.globalAlpha = 1;
    }
    const im = spritePociskuWroga(kol, r, bogato);
    ctx.drawImage(im, p.x - im.R, p.y - im.R, im.R * 2, im.R * 2);
    if (p.siec) { ctx.strokeStyle = 'rgba(40,40,60,0.9)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(p.x - r, p.y); ctx.lineTo(p.x + r, p.y); ctx.moveTo(p.x, p.y - r); ctx.lineTo(p.x, p.y + r); ctx.stroke(); }
  }
  ctx.lineCap = 'butt';
}

function rysujEfekty() {
  const t = Date.now();
  ciecia.forEach(c => {
    const p = 1 - c.czas / c.max;
    ctx.save(); ctx.globalAlpha = (1 - p) * 0.75;
    if (c.linia) { ctx.strokeStyle = '#f0e8d0'; ctx.lineWidth = 6 * (1 - p) + 1; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(c.x + Math.cos(c.kat) * 14, c.y + Math.sin(c.kat) * 14); ctx.lineTo(c.x + Math.cos(c.kat) * c.r, c.y + Math.sin(c.kat) * c.r); ctx.stroke(); }
    else {
      // sierp cięcia: gruby przy końcu ostrza, cienki na początku zamachu
      const l = Math.min(c.luk, Math.PI * 2), a0 = c.kat - l / 2, a1 = a0 + l * Math.min(1, p * 1.6 + 0.2), sr = (a0 + a1) / 2;
      ctx.fillStyle = 'rgba(255,245,220,0.16)'; ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.arc(c.x, c.y, c.r, a0, a1); ctx.closePath(); ctx.fill();
      const ri = c.r * 0.62, ro = c.r * 0.98;
      ctx.fillStyle = c.kolor; ctx.globalAlpha = (1 - p) * 0.55;
      ctx.beginPath(); ctx.arc(c.x, c.y, ro, a0, a1); ctx.quadraticCurveTo(c.x + Math.cos(a1) * ri * 1.1, c.y + Math.sin(a1) * ri * 1.1, c.x + Math.cos(a1) * ri, c.y + Math.sin(a1) * ri);
      ctx.arc(c.x, c.y, ri + (ro - ri) * 0.75, a1, a0, true); ctx.closePath(); ctx.fill();
      ctx.globalAlpha = (1 - p) * 0.95; ctx.strokeStyle = '#fffaf0'; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(c.x, c.y, ro, Math.max(a0, a1 - l * 0.55), a1); ctx.stroke();
      if (p < 0.5) { ctx.globalAlpha = 0.6 * (1 - p * 2); ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(c.x + Math.cos(a1) * ro, c.y + Math.sin(a1) * ro, 3.2, 0, Math.PI * 2); ctx.fill(); }
    }
    ctx.restore();
  });
  stozki.forEach(s => { const p = 1 - s.czas / s.max; ctx.save(); ctx.globalAlpha = (1 - p) * 0.55; ctx.fillStyle = s.kolor; ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.arc(s.x, s.y, s.r * (0.4 + p * 0.6), s.kat - s.pol, s.kat + s.pol); ctx.closePath(); ctx.fill(); ctx.restore(); });
  fale.forEach(f => {
    const p = 1 - f.czas / f.max;
    ctx.save(); ctx.globalAlpha = (1 - p) * (f.slaba ? 0.25 : 0.85);
    ctx.strokeStyle = f.kolor || '#ffd24a'; ctx.lineWidth = (f.slaba ? 3 : 7) * (1 - p) + 1;
    const r = f.odwrot ? f.r * (1 - p * 0.85) : f.r * (0.2 + p * 0.85);
    ctx.beginPath(); ctx.arc(f.x, f.y, Math.max(1, r), 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  });
  scianyMagiczne.forEach(sc => {
    const a = Math.min(1, (sc.max - sc.czas) / 0.25, sc.czas / 0.5);
    ctx.save(); ctx.lineCap = 'round'; ctx.globalAlpha = 0.4 * a; ctx.strokeStyle = '#7ec4ff'; ctx.lineWidth = sc.grubosc + 8; ctx.shadowColor = '#7ec4ff'; ctx.shadowBlur = 18;
    ctx.beginPath(); ctx.moveTo(sc.x1, sc.y1); ctx.lineTo(sc.x2, sc.y2); ctx.stroke(); ctx.shadowBlur = 0;
    ctx.globalAlpha = (0.75 + Math.sin(t / 90) * 0.15) * a; ctx.strokeStyle = '#dff2ff'; ctx.lineWidth = sc.grubosc * 0.45; ctx.beginPath(); ctx.moveTo(sc.x1, sc.y1); ctx.lineTo(sc.x2, sc.y2); ctx.stroke(); ctx.restore();
  });
  blyskawice.forEach(bl => {
    const a = Math.max(0, bl.czas / bl.max) * (0.75 + Math.random() * 0.25);
    ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha = a; ctx.beginPath();
    bl.pkt.forEach((q, i) => { if (i) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]); });
    ctx.strokeStyle = bl.kolor; ctx.globalAlpha = a * 0.35; ctx.lineWidth = 9; ctx.stroke(); ctx.globalAlpha = a; ctx.lineWidth = 4; ctx.stroke(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.6; ctx.stroke(); ctx.restore();
  });
  // odpryski: kurczą się z czasem
  czastki.forEach(c => { const z = Math.max(0, c.czas / c.max), s = 1.4 + 3 * z; ctx.globalAlpha = Math.min(1, z * 1.4); ctx.fillStyle = c.kolor; ctx.fillRect(c.x - s / 2, c.y - s / 2, s, s); });
  // iskry trafień: krótkie jasne kreski
  const teraz = performance.now(), dt = Math.min(0.05, Math.max(0, (teraz - (rysujEfekty.t || teraz)) / 1000)); rysujEfekty.t = teraz;
  if (iskry.length) {
    ctx.lineCap = 'round'; ctx.lineWidth = 1.8;
    for (let i = iskry.length - 1; i >= 0; i--) {
      const k = iskry[i]; k.t += dt; if (k.t >= k.max) { iskry.splice(i, 1); continue; }
      k.x += k.vx * dt; k.y += k.vy * dt; k.vx *= 0.86; k.vy *= 0.86;
      ctx.globalAlpha = 1 - k.t / k.max; ctx.strokeStyle = k.kolor;
      ctx.beginPath(); ctx.moveTo(k.x, k.y); ctx.lineTo(k.x - k.vx * 0.035, k.y - k.vy * 0.035); ctx.stroke();
    }
    ctx.lineCap = 'butt';
  }
  ctx.globalAlpha = 1;
}

function rysujTeksty() {
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  const L = USTAW.liczby;
  teksty.forEach(t => {
    if (t.o && (L === 'brak' || (L === 'wazne' && t.o === 1))) return;
    ctx.globalAlpha = Math.max(0, Math.min(1, t.czas / t.max * 1.6));
    ctx.font = '900 ' + Math.round(t.rozm * SKALA_TEKSTU) + 'px system-ui, sans-serif';
    ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineWidth = 3; ctx.fillStyle = t.kolor; tekstZObrysem(ctx, t.t, t.x, t.y);
  });
  ctx.globalAlpha = 1;
}

function rysujOswietlenie() {
  // Ciemność liczona w 1/4 rozdzielczości - to miękki gradient, a tak jest wielokrotnie szybciej
  const SK = 4, Wp = Math.ceil(widok.width / SK), Hp = Math.ceil(widok.height / SK);
  if (ciemnosc.width !== Wp || ciemnosc.height !== Hp) { ciemnosc.width = Wp; ciemnosc.height = Hp; }
  const c = ciemnoscCtx, teraz = Date.now(), ciemno = fala.ciemnosc && stan === 'walka';
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1; c.clearRect(0, 0, Wp, Hp);
  c.fillStyle = ciemno ? 'rgba(4,3,10,0.94)' : 'rgba(6,5,14,0.42)'; c.fillRect(0, 0, Wp, Hp);
  const sk = ZOOM * DPR / SK;
  c.setTransform(sk, 0, 0, sk, 0, 0); c.globalCompositeOperation = 'destination-out';
  function sw(x, y, r, s) { c.globalAlpha = s; c.drawImage(SPR_SWIATLO, x - r, y - r, r * 2, r * 2); }
  const gx = gracz.x - kamX, gy = gracz.y - kamY;
  sw(gx, gy, (ciemno ? 150 : 340) * (1 + Math.sin(teraz / 230) * 0.025), 1);
  graczeDoRysowania().forEach(p => { if (p !== lokalnyWidok() && p !== gracz) sw(p.x - kamX, p.y - kamY, ciemno ? 110 : 220, 0.9); });
  if (!ciemno) {
    swiatlaPochodni.forEach(p => sw(p[0] - kamX, p[1] - kamY, 125 * p[2], 0.9));
    for (let i = 0; i < pociski.length && i < 30; i++) sw(pociski[i].x - kamX, pociski[i].y - kamY, 40, 0.5);
    wrogowie.forEach(w => { if (w.boss && !w.martwy) sw(w.x - kamX, w.y - kamY, 160, 0.7); });
  }
  efektyCzasowe.forEach(e => { if (e.rodzaj === 'meteor') sw(e.x - kamX, e.y - kamY, e.r * 1.5, 0.8); });
  c.globalAlpha = 1;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.imageSmoothingEnabled = true; ctx.drawImage(ciemnosc, 0, 0, widok.width, widok.height); ctx.restore();
  if (poziomEfektow() > 0) return;   // lżejsze efekty: bez blasku pochodni i pyłków
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  swiatlaPochodni.forEach(p => { const a = p[2]; ctx.globalAlpha = a; ctx.drawImage(SPR_POCHODNIA, p[0] - kamX - 92, p[1] - kamY - 92, 184, 184); });
  ctx.globalAlpha = 1; ctx.drawImage(SPR_GRACZ, gx - 170, gy - 170, 340, 340);
  if (drobinki.length === 0) for (let i = 0; i < 26; i++) drobinki.push({ dx: (Math.random() - 0.5) * 440, dy: (Math.random() - 0.5) * 440, f: Math.random() * 6.28, s: 0.6 + Math.random() * 1.2 });
  ctx.fillStyle = 'rgb(255,225,170)';
  drobinki.forEach(d => { d.f += 0.012; d.dy -= 0.12 * d.s; d.dx += Math.sin(d.f) * 0.18; if (d.dy < -220) d.dy += 440; if (d.dx < -220) d.dx += 440; if (d.dx > 220) d.dx -= 440;
    const a = Math.max(0, 1 - Math.hypot(d.dx, d.dy) / 210) * 0.5; if (a <= 0.02) return; ctx.globalAlpha = a; ctx.fillRect(gx + d.dx - d.s / 2, gy + d.dy - d.s / 2, d.s, d.s); });
  ctx.restore();
}

// Pasek bossa i strzałki do rzeczy poza ekranem
function rysujInterfejsPlotna() {
  if (stan !== 'walka' && stan !== 'pauza') return;
  const bossy = wrogowie.filter(w => w.boss && !w.martwy);
  const nSlot = gracz ? (gracz.oreze ? gracz.oreze.length : 0) + (gracz.przedmioty ? gracz.przedmioty.filter(p => p).length : 0) : 0;
  let y0 = 74 + (nSlot ? 30 : 0) + (nSlot > 12 ? 31 : 0);
  if (bossy.length) { try { const hb = $('hud').getBoundingClientRect(), wr = widok.getBoundingClientRect(); if (hb.height && wr.height) y0 = (hb.bottom - wr.top) * WYS / wr.height + 10; } catch (e) {} }
  const sz = Math.min(WID - 60, 520), x = (WID - sz) / 2;
  bossy.forEach((b, i) => {
    const y = y0 + i * 26;
    ctx.fillStyle = 'rgba(10,8,16,0.8)'; ctx.fillRect(x - 2, y - 2, sz + 4, 14);
    ctx.fillStyle = '#3a1010'; ctx.fillRect(x, y, sz, 10);
    const g = ctx.createLinearGradient(x, 0, x + sz, 0); g.addColorStop(0, '#e6b53c'); g.addColorStop(1, '#c0392b');
    ctx.fillStyle = g; ctx.fillRect(x, y, sz * Math.max(0, b.hp / b.hpMax), 10);
    ctx.font = '800 10px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = '#fff'; ctx.strokeStyle = '#000'; ctx.lineWidth = 3;
    const napis = b.ik + ' ' + b.n + ' — ' + fmtK(Math.max(0, b.hpBossa !== undefined ? b.hpBossa : b.hp)); tekstZObrysem(ctx, napis, WID / 2, y + 22);
  });
  // drużyna: leżę powalony
  if (gracz && gracz.powalony && druzyna()) {
    ctx.save(); ctx.font = '800 13px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.9)'; ctx.fillStyle = '#ffb0a0';
    const y = WYS * 0.6 + Math.sin(Date.now() / 300) * 2;
    ctx.strokeText('💀 Leżysz! Kolega musi stać obok 3 sekundy', WID / 2, y); ctx.fillText('💀 Leżysz! Kolega musi stać obok 3 sekundy', WID / 2, y);
    ctx.restore();
  }
  // strzałki
  const cele = bossy.slice();
  skrzynieNaZiemi.forEach(s => cele.push({ x: s.x, y: s.y, sk: true, tier: s.tier }));
  wrogowie.forEach(w => { if (w.czempion && !w.martwy) cele.push(w); });
  graczeDoRysowania().forEach(p => { if (p !== lokalnyWidok()) cele.push({ x: p.x, y: p.y, kolega: true, powalony: p.powalony }); });
  cele.forEach(c => {
    const sx = (c.x - kamX) * ZOOM, sy = (c.y - kamY) * ZOOM;
    if (sx > 0 && sx < WID && sy > 0 && sy < WYS) return;
    const cx = WID / 2, cy = WYS * 0.55, k = Math.atan2(sy - cy, sx - cx);
    const px = ogr(cx + Math.cos(k) * 1000, 16, WID - 16), py = ogr(cy + Math.sin(k) * 1000, 70, WYS - 16);
    ctx.save(); ctx.translate(px, py); ctx.rotate(k); ctx.fillStyle = c.kolega ? (c.powalony ? '#ff9a8a' : '#7ee8ff') : (c.sk ? TIERY[c.tier].kolor : '#ff5a3a'); ctx.globalAlpha = 0.85;
    ctx.beginPath(); ctx.moveTo(10, 0); ctx.lineTo(-6, -7); ctx.lineTo(-6, 7); ctx.closePath(); ctx.fill(); ctx.restore();
  });
}

// =====================================================================
//  WYGLĄD WROGÓW: ludzie lochu (kusznicy, łucznicy, kultyści, magowie...)
//  rysowani tak jak nasze postacie - z bronią celującą w gracza - oraz szlamy
//  jako galaretki z oczami. Pozostałe potwory to emoji z obrysem.
//  Rozpoznajemy po ikonie, więc działa tak samo u gospodarza i u klienta.
// =====================================================================
const WYGLAD_WROGOW = {
  '🏹': { kolory: { plaszcz: ['#4a3c30', '#241c16'], tunika: ['#6a5640', '#3a2e22'], wlosy: '#2a1a10', skora: ['#c9a080', '#9a7458'] }, wyglad: { czapka: 'kaptur', kol: '#3a2e24', oczy: '#ff5a3a', chusta: '#2a2220' }, bron: 'kusza' },
  '🎯': { kolory: { plaszcz: ['#2e4a2a', '#16241a'], tunika: ['#4a6a3a', '#26361e'], wlosy: '#3a2a1a', skora: ['#c9a080', '#9a7458'] }, wyglad: { czapka: 'kaptur', kol: '#24401f', oczy: '#ffd24a', chusta: '#1e2a1a' }, bron: 'luk' },
  '🕯️': { kolory: { plaszcz: ['#4a1a5a', '#200a2a'], tunika: ['#5a2a6a', '#2a1036'], wlosy: '#000000', skora: ['#b8a8b0', '#8a7888'] }, wyglad: { czapka: 'kaptur', kol: '#3a1048', oczy: '#ff7ae0' }, bron: 'kosturPustki' },
  '🛡️': { kolory: { plaszcz: ['#4a5468', '#262c38'], tunika: ['#8a94a8', '#4a5468'], wlosy: '#3a2a1a', skora: ['#d8b090', '#a88060'] }, wyglad: { czapka: 'helm', oczy: '#ffb03c' }, bron: 'mieczTarcza' },
  '🧨': { kolory: { plaszcz: ['#5a4030', '#2a1e14'], tunika: ['#7a5a3a', '#4a3420'], wlosy: '#5a3a1a', skora: ['#d8b090', '#a88060'] }, wyglad: { czapka: 'gogle', oczy: '#ff8a3a', broda: '#4a2a14' }, bron: 'granatnik' },
  '🔮': { kolory: { plaszcz: ['#1e3a7a', '#0e1a3a'], tunika: ['#2a5aa0', '#163060'], wlosy: '#e8e8f0', skora: ['#d8c0b0', '#a89080'] }, wyglad: { czapka: 'kapeluszMaga', kol: '#1e3a7a', oczy: '#7ae0ff', broda: '#e8e8f0' }, bron: 'rozdzkaZimy' },
  '🧙': { kolory: { plaszcz: ['#3a1a5a', '#1a0a2a'], tunika: ['#4a2a6a', '#24123a'], wlosy: '#8a8a9a', skora: ['#b8a8a0', '#887870'] }, wyglad: { czapka: 'kapeluszMaga', kol: '#2a1040', oczy: '#c46ce8', broda: '#9a9aaa' }, bron: 'kosturPustki' },
  '🤺': { kolory: { plaszcz: ['#2a3a6a', '#101830'], tunika: ['#5a6a9a', '#2a3456'], wlosy: '#000000', skora: ['#9ab8e8', '#5a78a8'] }, wyglad: { czapka: 'helm', oczy: '#7ae0ff' }, bron: 'halabarda' },
};
const SZLAMY = { '🟢': true };
const CACHE_WYGLADU = new Map();
const KROKI_WYGLADU = [0, 1, 0, -1];
// gotowa klatka ciała (bez broni): ik, klatka chodu 0-3, kierunek, skala w pikselach na jednostkę
function klatkaWygladu(ik, klatka, kier, sk, bialy) {
  const k = ik + '|' + klatka + '|' + kier + '|' + sk + (bialy ? '|b' : '');
  let c = CACHE_WYGLADU.get(k);
  if (c) return c;
  if (CACHE_WYGLADU.size > 400) CACHE_WYGLADU.clear();
  if (bialy) {
    const z = klatkaWygladu(ik, klatka, kier, sk, false);
    c = document.createElement('canvas'); c.width = z.width; c.height = z.height;
    const x = c.getContext('2d'); x.drawImage(z, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = '#ffffff'; x.fillRect(0, 0, c.width, c.height);
  } else {
    c = document.createElement('canvas'); c.width = Math.ceil(36 * sk); c.height = Math.ceil(58 * sk);
    const x = c.getContext('2d'); x.scale(sk, sk); x.translate(18, 39); x.scale(kier, 1);
    rysujCialo(x, WYGLAD_WROGOW[ik], KROKI_WYGLADU[klatka], 0, 0.6, false);
  }
  CACHE_WYGLADU.set(k, c);
  return c;
}
// kąt, w który patrzy/celuje wróg (cel u gospodarza, u klienta - najbliższy gracz)
function katCeluWroga(w) {
  if (w.zamach > 0 || w.zamP > 0) return w.zamKat || 0;
  let c = w.cel && !w.cel.powalony ? w.cel : null;
  if (!c) { let best = 1e9; ((typeof SIEC !== 'undefined' && SIEC.rola === 'klient') ? (SIEC.widokGraczy || []) : gracze).forEach(p => { const d = Math.hypot(p.x - w.x, p.y - w.y); if (d < best && !p.powalony) { best = d; c = p; } }); }
  return c ? Math.atan2(c.y - w.y, c.x - w.x) : 0;
}
// Rysuje wroga w (0,0) bieżącego układu (już przesuniętego na pozycję wroga). Zwraca false, gdy to zwykłe emoji.
function rysujWygladWroga(w, blysk, katSwiata) {
  const r = w.r;
  if (SZLAMY[w.ik]) { rysujSzlam(w, blysk, katSwiata); return true; }
  const W = WYGLAD_WROGOW[w.ik];
  if (!W) return false;
  const ka = katCeluWroga(w) - (katSwiata || 0), kier = Math.cos(ka) < 0 ? -1 : 1;
  const s = r / 13.5, sk = Math.max(0.5, Math.round(s * SKALA_RYS * 4) / 4);
  const klatka = (w._ruch || 0) > 0.3 ? Math.floor(((w._faza || 0) / (Math.PI / 2)) % 4 + 4) % 4 : 0;
  const im = klatkaWygladu(w.ik, klatka, kier, sk, false), szer = im.width / sk * s, wys = im.height / sk * s;
  const bron = () => {
    const bx = Math.cos(ka) * r * 0.8, by = 2 * s + Math.sin(ka) * r * 0.6;
    ctx.save(); ctx.translate(bx, by); ctx.rotate(ka); ctx.scale(s * 0.95, s * 0.95);
    rysujKsztaltBroni(ctx, { rodzaj: W.bron, tier: 0, kat: ka, anim: 0 }); ctx.restore();
  };
  const zaPlecami = Math.sin(ka) < -0.35;   // broń celuje w górę - chowa się za postacią
  if (zaPlecami) bron();
  ctx.drawImage(im, -18 * s, -39 * s + 2 * s, szer, wys);
  if (blysk > 0) { const a = ctx.globalAlpha; ctx.globalAlpha = a * blysk; ctx.drawImage(klatkaWygladu(w.ik, klatka, kier, sk, true), -18 * s, -37 * s, szer, wys); ctx.globalAlpha = a; }
  if (!zaPlecami) bron();
  return true;
}
// Szlam: galaretka, która faluje i zerka na gracza
function rysujSzlam(w, blysk, katSwiata) {
  const r = w.r * 1.05, t = Date.now() / 1000, f = Math.sin(t * 5 + w.id) * 0.07 + Math.sin((w._faza || 0) * 1.3) * 0.05;
  const sx = r * (1 + f), sy = r * 0.82 * (1 - f), [cr, cg, cb] = rgbKoloru(w.kolor || '#5ac46a');
  ctx.save();
  ctx.beginPath(); ctx.moveTo(-sx, r * 0.55);
  ctx.bezierCurveTo(-sx * 1.05, -sy * 0.9, -sx * 0.4, -sy * 1.25, 0, -sy * 1.2);
  ctx.bezierCurveTo(sx * 0.4, -sy * 1.25, sx * 1.05, -sy * 0.9, sx, r * 0.55);
  ctx.quadraticCurveTo(0, r * 0.75, -sx, r * 0.55); ctx.closePath();
  const g = ctx.createLinearGradient(0, -sy * 1.2, 0, r * 0.7);
  g.addColorStop(0, 'rgb(' + Math.min(255, cr + 70) + ',' + Math.min(255, cg + 70) + ',' + Math.min(255, cb + 70) + ')'); g.addColorStop(1, 'rgb(' + (cr * 0.55 | 0) + ',' + (cg * 0.55 | 0) + ',' + (cb * 0.55 | 0) + ')');
  ctx.fillStyle = g; ctx.globalAlpha *= 0.94; ctx.fill(); ctx.globalAlpha /= 0.94;
  ctx.strokeStyle = 'rgba(14,8,20,0.9)'; ctx.lineWidth = Math.max(1.2, r * 0.1); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.beginPath(); ctx.ellipse(-sx * 0.4, -sy * 0.75, r * 0.2, r * 0.12, -0.5, 0, Math.PI * 2); ctx.fill();
  // oczy patrzą na gracza
  const ka = katCeluWroga(w) - (katSwiata || 0), ox = Math.cos(ka) * r * 0.07, oy = Math.sin(ka) * r * 0.05;
  [-1, 1].forEach(st => {
    ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.ellipse(st * r * 0.3, -sy * 0.3, r * 0.16, r * 0.2, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#14101c'; ctx.beginPath(); ctx.arc(st * r * 0.3 + ox, -sy * 0.28 + oy, r * 0.09, 0, Math.PI * 2); ctx.fill();
  });
  if (blysk > 0) { ctx.globalAlpha *= blysk; ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.moveTo(-sx, r * 0.55); ctx.bezierCurveTo(-sx * 1.05, -sy * 0.9, -sx * 0.4, -sy * 1.25, 0, -sy * 1.2); ctx.bezierCurveTo(sx * 0.4, -sy * 1.25, sx * 1.05, -sy * 0.9, sx, r * 0.55); ctx.quadraticCurveTo(0, r * 0.75, -sx, r * 0.55); ctx.fill(); }
  ctx.restore();
}

// =====================================================================
//  EKRANY I INTERFEJS
// =====================================================================
const ekranEl = $('ekran'), modalEl = $('modal'), modalTresc = $('modalTresc');
const AKCJE = {};
// Treść ekranu/okna dostaje opakowanie: na komputerze dużo kart układa się w kolumny,
// a reszta (np. menu, skrzynia) stoi w wąskiej, czytelnej kolumnie na środku.
function ulozTresc(el) {
  const karty = el.querySelectorAll(':scope > .karta, :scope > .slot-pusty').length;
  const siatka = el.querySelector(':scope > .siatka3, :scope > .siatka2');
  const wiersze = el.querySelectorAll(':scope > .wiersz-stat').length;
  const szer = karty >= 3 || !!siatka || wiersze >= 8;
  el.classList.toggle('szeroka', szer);
  return szer;
}
function pokazEkran(html, op) {
  op = op || {};
  const sc = ekranEl.scrollTop;
  ekranEl.innerHTML = '<div class="ekran-tresc' + (op.klasa ? ' ' + op.klasa : '') + '">' + html + '</div>';
  if (!op.klasa) ulozTresc(ekranEl.firstElementChild);
  ekranEl.classList.add('widoczny');
  ekranEl.classList.toggle('polprzezroczysty', !!op.polprzezroczysty);
  ekranEl.scrollTop = op.zachowaj ? sc : 0;
}
function zamknijEkran() { ekranEl.classList.remove('widoczny'); ekranEl.innerHTML = ''; }
function pokazModal(html, zachowaj) {
  const sc = modalTresc.scrollTop; delete modalEl.dataset.build; delete modalEl.dataset.szczegol; delete modalEl.dataset.zBuildu;
  modalTresc.innerHTML = '<div class="modal-tresc">' + html + '</div>';
  modalEl.classList.toggle('szeroki', ulozTresc(modalTresc.firstElementChild));
  modalEl.classList.add('widoczny'); modalTresc.scrollTop = zachowaj ? sc : 0;
}
function zamknijModal() { modalEl.classList.remove('widoczny'); modalTresc.innerHTML = ''; delete modalEl.dataset.build; delete modalEl.dataset.szczegol; delete modalEl.dataset.zBuildu; }
modalEl.addEventListener('click', e => { if (e.target === modalEl && !modalEl.dataset.wymuszony) zamknijModal(); });
document.addEventListener('click', e => {
  let el = e.target.closest('[data-a]');
  // karta, którą da się wybrać w całości (np. próba): klik w kartę = klik w jej główny przycisk
  if (!el) { const k = e.target.closest('[data-pad][data-klik]'); if (k) el = k.querySelector('[data-a="' + k.dataset.pad + '"]'); }
  if (!el || el.disabled) return;
  const f = AKCJE[el.dataset.a];
  if (!f) return;
  e.preventDefault(); DZ.klik();
  try { f(el.dataset, el); } catch (er) { zglosBlad(er, 'akcja ' + el.dataset.a); console.error(er); }
});
// Komunikaty z kontekstu zdalnego gracza (u gospodarza gry online) trafiają do niego, nie na ekran gospodarza
function doZdalnego(rodzaj, t, pod) { if (gracz && gracz.zdalny && typeof SIEC !== 'undefined' && SIEC.rola === 'host') { siecZdarzenieGracza(gracz, [rodzaj, t, pod || '']); return true; } return false; }
function toast(t) { if (doZdalnego('toast', t)) return; const el = $('toast'); el.innerHTML = t; el.style.opacity = '1'; clearTimeout(toast._t); toast._t = setTimeout(() => el.style.opacity = '0', 2200); }
function baner(t, pod) { if (typeof SIEC !== 'undefined' && SIEC.rola === 'host') siecZdarzenie(['ban', t, pod || '']); const el = $('baner'); el.innerHTML = t + (pod ? '<small>' + pod + '</small>' : ''); el.style.opacity = '1'; clearTimeout(baner._t); baner._t = setTimeout(() => el.style.opacity = '0', 2600); }
function dziennik(t) {
  if (doZdalnego('dz', t)) return;
  const d = $('dziennik'), el = document.createElement('div'); el.className = 'wpis'; el.textContent = t; d.appendChild(el);
  setTimeout(() => el.remove(), 2900); while (d.children.length > 4) d.removeChild(d.firstChild);
}

// kontekst do opisów w Kodeksie (bez rozpoczętej gry)
function wKontekscie(fn) {
  if (gracz && D) return fn();
  const zg = gracz, zd = D, zr = run, zf = fala;
  run = { trudnosc: 1, zrodla: {} }; gracz = nowyGracz('wiezniarka'); fala = { nr: 1 }; przebudujHaki(); D = Object.assign({}, BAZA_STATOW);
  try { return fn(); } finally { gracz = zg; D = zd; run = zr; fala = zf; if (gracz) przebudujHaki(); }
}

// ---------------------------------------------------------------------
//  KARTY
// ---------------------------------------------------------------------
// ---- znaczniki na kartach: jak efekt działa i od czego się skaluje (wyliczane z kodu efektu) ----
const _tagiCache = {};
function zrodloDef(d) { let s = ''; for (const k in d) if (typeof d[k] === 'function') s += String(d[k]); return s; }
const SKALE_TAG = [['D.ad', '⚔️'], ['D.ap', '✨'], ['D.hpMax', '❤️'], ['D.pancerz', '🛡️'], ['D.odpMag', '🔰'], ['D.as', '⚡'], ['gracz.zloto', '💰'], ['D.szczescie', '🍀'], ['D.ms', '👟'], ['D.kryt', '🎯'], ['D.haste', '⏱️']];
function tagiDef(d, rodzaj, klucz) {
  klucz = rodzaj + ':' + (klucz || d.id); if (_tagiCache[klucz]) return _tagiCache[klucz];
  const src = zrodloDef(d), t = [];
  if (rodzaj === 'bron') t.push(['oh', '🎯 każde trafienie nakłada Twoje efekty on-hit']);
  else if (d.naTrafienie || /onHit(Fiz|Mag|Praw)/.test(src)) t.push(['oh', '🎯 on-hit' + (/k\.glowny/.test(src) ? ' · raz na atak' : ' · każdy trafiony wróg')]);
  if (/zastosujOnHit|trafienieAtakiem/.test(src)) t.push(['oh2', '🔁 dodatkowo nakłada efekty on-hit']);
  if (d.podwojnyOnHit) t.push(['oh2', '×2 wszystkie efekty on-hit']);
  if (d.onHitKryt) t.push(['oh2', '🎯 krytyki nakładają efekty on-hit dodatkowo']);
  if (d.naKryt) t.push(['', '💥 przy krytyku']);
  if (d.naZabicie) t.push(['', '☠️ przy zabójstwie']);
  if (d.naOtrzymanie) t.push(['', '🩹 gdy obrywasz']);
  if (d.naUniku) t.push(['', '💨 przy uniku']);
  if (d.naUmiejetnosci) t.push(['', '✨ po użyciu umiejętności']);
  if (rodzaj === 'prz' && d.wielokrotny) t.push(['', '🔁 możesz mieć kilka — każdy działa osobno']);
  if (rodzaj === 'ore') { if (d.cd) t.push(['cd', '⏱️ co ' + fmt(d.cd) + ' s (Przyspieszenie skraca)']); else if (d.co) t.push(['cd', '⚔️ co ' + d.co + '. atak broni głównej']); }
  else if (rodzaj !== 'bron' && d.cd) t.push(['cd', '⏱️ odnowienie ' + fmt(d.cd) + ' s (Przyspieszenie skraca)']);
  const sk = SKALE_TAG.filter(([w]) => src.indexOf(w) >= 0).map(([, ik]) => ik);
  if (rodzaj === 'bron') Object.keys(d.skal || {}).forEach(k => { const ik = (IKONY_SKAL[k] || k).split(' ')[0]; if (sk.indexOf(ik) < 0) sk.push(ik); });
  if (sk.length) t.push(['sk', '📈 skaluje się z: ' + sk.join(' ')]);
  return (_tagiCache[klucz] = t);
}
function htmlTagow(t) { return t.length ? '<div class="tagi">' + t.map(([k, s]) => '<span class="tag' + (k ? ' tag-' + k : '') + '">' + s + '</span>').join('') + '</div>' : ''; }
// cała karta jako jeden cel dla pada/klawiatury: A klika główny przycisk karty, X — drugi
function kartaPad(html, akcja, nazwa, akcja2, nazwa2) {
  return html.replace(/^<div /, '<div data-pad="' + akcja + '" data-padn="' + nazwa + '"' + (akcja2 ? ' data-pad2="' + akcja2 + '" data-pad2n="' + nazwa2 + '"' : '') + ' ');
}
function nazwaTieruPrzedmiotu(d) { return d.t === 'p' ? '<span class="kol-p">Pryzmatyczny przedmiot</span>' : '<span class="kol-t' + d.t + '">' + TIERY[d.t].nazwa + ' przedmiot</span>'; }
function kartaPrzedmiotu(inst, dol, op) {
  op = op || {};
  const d = DEF_PRZ[inst.id], kl = d.t === 'p' ? 'tp' : 't' + d.t;
  let cd = d.cd ? '<span class="cd-tag">⏱️ ' + fmt(d.cd) + ' s</span>' : '';
  return '<div class="karta ' + kl + '">' +
    '<div class="karta-gora"><div class="karta-ik">' + d.ik + (inst.gw ? '<span class="gw">' + gwiazdki(inst.gw) + '</span>' : '') + '</div>' +
    '<div><div class="karta-nazwa">' + esc(d.n) + cd + '</div><div class="karta-tier">' + nazwaTieruPrzedmiotu(d) + (d.t === 'p' ? ' · bez ulepszeń' : '') + '</div></div></div>' +
    '<div class="karta-srodek">' + (d.s ? '<div class="karta-staty">' + opisStatow(d.s) + '</div>' : '') +
    (d.opis && !op.bezOpisu ? '<div class="karta-opis">' + d.opis(inst) + '</div>' + htmlTagow(tagiDef(d, 'prz')) : '') + '</div>' +
    (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaBroni(b, dol) {
  const B = BRONIE[b.rodzaj];
  return '<div class="karta glowna t' + b.tier + '"><div class="karta-gora"><div class="karta-ik">' + B.ikona + '</div><div><div class="karta-nazwa">' + B.nazwa + ' ' + TIERY[b.tier].rz + '</div>' +
    '<div class="karta-tier"><span class="kol-t' + b.tier + '">' + TIERY[b.tier].nazwaZ + '</span> · ⭐ broń główna · ' + (B.dystans ? 'dystansowa' : 'wręcz') + '</div></div></div>' +
    '<div class="karta-opis">' + opisBroni(b) + (b.mistrz ? '<br>🏆 <b>Mistrzostwo ' + rzymskaM(b.mistrz) + '</b> (+' + (15 * b.mistrz) + '% obrażeń)' + (b.perki && b.perki.length ? ': ' + b.perki.map(p => PERKI_MISTRZA[p] ? PERKI_MISTRZA[p].ik + ' ' + PERKI_MISTRZA[p].n : '').join(', ') : '') : '') +
    (b.ewo ? '<br>🧬 Ewolucja broni: ' + EWO_BRONI.slice(0, b.ewo).join(' · ') : '') + '</div>' + htmlTagow(tagiDef(B, 'bron', b.rodzaj)) + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function rzymskaM(n) { return ['', 'I', 'II', 'III', 'IV', 'V'][n] || String(n); }
function kartaOreza(o, dol, op) {
  op = op || {};
  const d = DEF_ORE[o.id], R = RODZINY[d.rodz];
  const cd = d.cd ? '<span class="cd-tag">⏱️ ' + fmt(d.cd) + ' s</span>' : (d.co ? '<span class="cd-tag">⚔️ co ' + d.co + '. atak</span>' : '');
  return '<div class="karta t' + o.tier + '"><div class="karta-gora"><div class="karta-ik">' + d.ik + '</div><div><div class="karta-nazwa">' + esc(d.n) + ' ' + TIERY[o.tier].rz + cd + '</div>' +
    '<div class="karta-tier"><span class="kol-t' + o.tier + '">' + TIERY[o.tier].nazwaZ + ' broń</span> · ' + R.ik + ' ' + R.n + '</div></div></div>' +
    '<div class="karta-srodek">' + (op.bezOpisu ? '<div class="karta-staty">' + opisStatow(statyOreza(o)) + '</div>' : opisOreza(o) + htmlTagow(tagiDef(d, 'ore'))) + '</div>' +
    (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaPancerza(p, dol, naglowek) {
  const d = DEF_PANC[p.id];
  return '<div class="karta t' + p.tier + '">' + (naglowek ? '<div class="sekcja" style="margin-top:0">' + naglowek + '</div>' : '') +
    '<div class="karta-gora"><div class="karta-ik">' + d.ik + '</div><div><div class="karta-nazwa">' + d.n + '</div><div class="karta-tier"><span class="kol-t' + p.tier + '">' + TIERY[p.tier].nazwa + '</span> · ' + IKONY_SLOTOW[d.slot] + ' ' + NAZWY_SLOTOW[d.slot] + '</div></div></div>' +
    '<div class="karta-srodek"><div class="karta-staty">' + opisStatow(statyPancerza(p)) + '</div></div>' + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaAugmentu(a, dol, inst) {
  const T = TIERY_AUG[a.r];
  inst = inst || (gracz && gracz.augmenty.find(x => x.id === a.id)) || { id: a.id, poz: 1 };
  const poz = inst.poz || 1;
  const st = statyAugmentu(inst);
  return '<div class="karta ' + T.klasa + '"><div class="karta-gora"><div class="karta-ik">' + a.ik + '</div><div><div class="karta-nazwa">' + a.n + (poz > 1 ? ' <span style="color:#ffe08a">' + rzymska(poz) + '</span>' : '') + '</div>' +
    '<div class="karta-tier" style="color:' + T.kolor + '">' + (a.r === 'p' ? '<span class="kol-p gem-ap">' + T.nazwa + '</span>' : '<span class="gem-a' + a.r + '">' + T.nazwa + '</span>') + ' · poziom ' + rzymska(poz) + '/III</div></div></div>' +
    (st ? '<div class="karta-staty">' + opisStatow(st) + '</div>' : '') +
    (a.opis ? '<div class="karta-opis">' + a.opis(inst) + '</div>' : '') + htmlTagow(tagiDef(a, 'aug')) + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function pasekGorny(tytul) {
  return '<div class="gornypasek"><div class="zloto-duze">💰 ' + Math.floor(gracz.zloto) + '</div><div style="display:flex;gap:6px">' +
    '<button class="btn-maly" data-a="modalPostac">' + KLASY[gracz.klasa].ik + ' Postać</button><button class="btn-maly" data-a="modalStaty">📊 Staty</button><button class="btn-maly" data-a="modalBuild">🎒 Build</button></div></div>' +
    (tytul ? '<div class="tytul">' + tytul + '</div>' : '');
}
function poZmianieBuildu() { przebudujHaki(); oznaczStaty(); zastosujStaty(); }

// ---------------------------------------------------------------------
//  MENU, TRUDNOŚĆ, POSTAĆ
// ---------------------------------------------------------------------
function pokazMenu() {
  stan = 'menu'; gracz = null; run = null; D = null; fala = { nr: 0 }; gracze = []; lokalny = null; stwory = [];
  const z = lStorGet('wiezien_zapis', null);
  let kont = '';
  if (z && z.gracz && z.run && z.wersja === 2 && KLASY[z.gracz.klasa]) kont = '<button class="btn ziel" data-a="kontynuuj">⏩ Kontynuuj<br><small style="font-weight:700">' + KLASY[z.gracz.klasa].ik + ' ' + KLASY[z.gracz.klasa].n + ' · fala ' + (z.wznowFale || ((z.run.przerwa && z.run.przerwa.nr || 0) + 1)) + ' · ' + TRUDNOSCI[z.run.trudnosc].n + '</small></button>';
  pokazEkran('<div style="max-width:440px;margin:0 auto">' +
    '<div class="tytul duzy">⛓️ Więzień<br>Labiryntu</div><div class="podtytul">Nieskończone lochy. Fale potworów, setki kombinacji broni, przedmiotów i augmentów, bossowie.</div>' +
    '<div class="menu-klucz" style="text-align:center;font-size:60px;margin:6px 0 10px;filter:drop-shadow(0 4px 14px rgba(230,193,92,0.35))">🗝️</div>' +
    kont + '<button class="btn" data-a="nowaGra">⚔️ Nowa gra</button>' +
    '<button class="btn ziel" data-a="online">👥 Gra z przyjaciółmi (online)</button>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="kodeks">📖 Kodeks</button><button class="btn drugi" data-a="rekordy">🏆 Rekordy</button></div>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="jakGrac">❓ Jak grać</button><button class="btn drugi" data-a="dzwiek">' + (dzwiekWlaczony ? '🔊 Dźwięk' : '🔇 Bez dźwięku') + '</button></div>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="ustawienia">⚙️ Ustawienia</button><button class="btn drugi" data-a="sterowanie">🎮 Sterowanie' + (PAD.podlaczony ? ' <span class="ziel">· pad</span>' : '') + '</button></div>' +
    przyciskPelnego() +
    '<div class="podtytul" style="margin-top:18px;opacity:0.6">' + KLUCZE_KLAS.length + ' postaci · ' + KLUCZE_BRONI.length + ' broni głównych · ' + OREZE.length + ' broni dodatkowych · ' + PRZEDMIOTY.length + ' przedmiotów · ' + PRYZMATY.length + ' pryzmatycznych · ' + AUGMENTY.length + ' augmentów</div></div>');
}
// ---------------------------------------------------------------------
//  USTAWIENIA
// ---------------------------------------------------------------------
const OPCJE_USTAWIEN = [
  { k: 'orientacja', n: '📱 Orientacja (telefon, tablet)', o: [['auto', 'Obie'], ['pion', 'Pionowa'], ['poziom', 'Pozioma']],
    op: 'Poziomo plansza zajmuje cały ekran: drążek pojawia się pod kciukiem w dowolnym miejscu, przyciski są w prawym dolnym rogu. Najlepiej na pełnym ekranie.' },
  { k: 'uklad', n: '🕹️ Sterowanie na ekranie (poziomo)', o: [['auto', 'Automatyczne'], ['tel', 'Dotykowe'], ['pc', 'Myszka']],
    op: 'Automatyczne: na ekranie dotykowym drążek pod kciukiem i duże przyciski, przy myszce mały pasek akcji.' },
  { k: 'interfejs', n: '🔠 Wielkość napisów', o: [[0.9, 'Mniejsze'], [1, 'Normalne'], [1.15, 'Większe']] },
  { k: 'liczby', n: '💥 Liczby obrażeń', o: [['wszystkie', 'Wszystkie'], ['wazne', 'Tylko ważne'], ['brak', 'Wyłączone']],
    op: '„Tylko ważne” — trafienia krytyczne oraz obrażenia zadane elitom i bossom.' },
  { k: 'efekty', n: '✨ Efekty', o: [['pelne', 'Pełne'], ['oszczedne', 'Oszczędne']], op: 'Pełne: gdy gra zaczyna zwalniać, sama ścisza efekty. Oszczędne: dużo mniej iskier, poświat i odprysków — czytelniej i lżej dla słabszego sprzętu.' },
  { k: 'ikony', n: '🖼️ Ikony', o: [['auto', 'Automatyczne'], ['zawsze', 'Wbudowane'], ['systemowe', 'Systemowe']],
    op: 'Automatyczne: ikony, których brakuje na tym urządzeniu (puste kwadraciki), gra pokazuje jako obrazki. Wbudowane: nowsze ikony zawsze z gry. Systemowe: tylko ikony urządzenia. (Obrazki ikon: Noto Color Emoji, Google — licencja SIL OFL 1.1.)' },
  { k: 'mysz', n: '🖱️ Ruch myszą (komputer)', o: [[true, 'Włączony'], [false, 'Wyłączony']], op: 'Przytrzymaj lewy przycisk myszy na planszy, a postać pójdzie w stronę kursora.' },
];
function pokazUstawienia(zachowaj) {
  let h = '<div class="tytul">⚙️ Ustawienia</div>';
  OPCJE_USTAWIEN.forEach(O => {
    h += '<div class="sekcja">' + O.n + '</div><div class="zakladki opcje" style="margin:4px 0 2px">' +
      O.o.map(([v, n]) => '<button class="' + (USTAW[O.k] === v ? 'akt' : '') + '" data-a="ustaw" data-k="' + O.k + '" data-v="' + v + '">' + n + '</button>').join('') + '</div>' +
      (O.op ? '<div class="podtytul" style="text-align:left;margin:2px 2px 4px;font-size:11.5px">' + O.op + '</div>' : '');
  });
  h += '<div class="sekcja">🔊 Dźwięk</div><button class="btn drugi" data-a="dzwiekUst" style="margin-top:4px">' + (dzwiekWlaczony ? '🔊 Włączony' : '🔇 Wyłączony') + '</button>';
  const pe = przyciskPelnego(); if (pe) h += '<div class="sekcja">⛶ Ekran</div>' + pe;
  h += '<button class="btn" data-a="zamknijModal">Gotowe</button>';
  pokazModal(h, zachowaj);
}
AKCJE.ustawienia = () => pokazUstawienia(false);
AKCJE.ustaw = d => {
  const O = OPCJE_USTAWIEN.find(x => x.k === d.k); if (!O) return;
  const opc = O.o.find(([v]) => String(v) === d.v); if (!opc) return;
  USTAW[d.k] = opc[0]; zapiszUstawienia();
  if (d.k === 'orientacja') zablokujOrientacje();
  if (d.k === 'ikony') wykryjBrakiEmoji();
  dopasujRozmiar(); pokazUstawienia(true);
  if (stan === 'menu' && ekranEl.classList.contains('widoczny')) pokazMenu();
};
AKCJE.dzwiekUst = () => { dzwiekWlaczony = !dzwiekWlaczony; lStorSet('wiezien_dzwiek', dzwiekWlaczony); pokazUstawienia(true); };
AKCJE.dzwiek = () => { dzwiekWlaczony = !dzwiekWlaczony; lStorSet('wiezien_dzwiek', dzwiekWlaczony); pokazMenu(); };
AKCJE.menu = () => { zamknijModal(); pokazMenu(); };
AKCJE.nowaGra = () => {
  const z = lStorGet('wiezien_zapis', null);
  if (z && z.gracz) { pokazModal('<div class="tytul">Nowa gra?</div><div class="podtytul">Masz zapisaną grę. Nowa gra ją nadpisze.</div><button class="btn czerw" data-a="nowaGraTak">Tak, zaczynam od nowa</button><button class="btn drugi" data-a="zamknijModal">Anuluj</button>'); return; }
  pokazTrudnosc();
};
AKCJE.nowaGraTak = () => { zamknijModal(); lStorDel('wiezien_zapis'); pokazTrudnosc(); };
let wyborTrudnosci = 1;
function pokazTrudnosc() {
  const rek = lStorGet('wiezien_rekordy', {});
  let h = '<div class="tytul">Poziom zagrożenia</div><div class="podtytul">Im wyżej, tym potwory silniejsze i szybciej rosną w siłę. Na każdym poziomie po 10. i 20. fali robi się naprawdę groźnie.</div>';
  TRUDNOSCI.forEach((T, i) => {
    const r = rek[i];
    h += '<div class="kafel' + (i === wyborTrudnosci ? ' wybrany' : '') + '" data-a="wybierzTrudnosc" data-i="' + i + '" style="text-align:left;margin-bottom:8px;display:flex;gap:10px;align-items:center">' +
      '<div class="ik">' + T.ik + '</div><div style="flex:1"><div class="n">' + T.n + (r ? ' <span style="color:#ffe08a;font-size:11px">· rekord: fala ' + r.fala + '</span>' : '') + '</div><div class="o">' + T.opis.join(' · ') + '</div></div></div>';
  });
  h += '<button class="btn" data-a="dalejDoPostaci">Dalej ▶</button><button class="btn drugi" data-a="menu">◀ Menu</button>';
  pokazEkran(h);
}
AKCJE.wybierzTrudnosc = d => { wyborTrudnosci = +d.i; pokazTrudnosc(); };
AKCJE.dalejDoPostaci = () => pokazPostacie();
let wyborKlasy = 'wiezniarka';
// ---------------------------------------------------------------------
//  KARTA POSTACI (pauza, przerwa): poziom trudności, staty bazowe, pasywka, umiejętności (przeliczniki, odnowienie
//  bazowe i po przyspieszeniu), auto-użycie i drzewko ewolucji
// ---------------------------------------------------------------------
const CENY_EWO = [90, 180, 320], POZIOM_EWO = [3, 10, 20];
function rzymskaR(n) { return ['0', 'I', 'II', 'III'][n || 0]; }
function cenaEwo(r) { return Math.round(CENY_EWO[r] * mnCeny()); }
function blokUmiejetnosci(U, nr, zGraczem) {
  const cdB = cdBazoweUmi(U), auto = zGraczem && gracz.autoUmi && gracz.autoUmi[nr];
  const cdTxt = U.pasywna ? '<span class="cd-tag">⚡ sama, z energii</span>' : U.przelacz ? '<span class="cd-tag">🔁 przełącznik</span>' :
    '<span class="cd-tag">⏱️ ' + fmt(cdB) + ' s' + (zGraczem && D && (D.haste > 0 || FLAGI.cdUmi) ? ' → <b>' + fmt(cdUmiTeraz(U)) + ' s</b>' : '') + '</span>' + (U.auto ? ' <span class="cd-tag">🤖 sama</span>' : '');
  const przel = zGraczem && !U.pasywna && !U.przelacz && !U.auto ? ' <button class="btn-maly' + (auto ? ' ziel' : '') + '" data-a="autoUmi" data-n="' + nr + '" style="padding:2px 8px;font-size:11px">🤖 auto: ' + (auto ? 'wł.' : 'wył.') + '</button>' : '';
  return '<div class="blok-umi"><b>' + U.ik + ' ' + U.n + '</b> ' + cdTxt + (nr === 2 ? ' <span class="cd-tag">2. · R / Q · pad RB</span>' : '') + przel + '<br>' + wKontekscie(() => U.opis(zGraczem ? mnUmi() : 1)) + '</div>';
}
function htmlPostaci(wModalu) {
  const K = KLASY[gracz.klasa], T = TRUDNOSCI[run.trudnosc];
  let h = '<div style="display:flex;justify-content:center;margin-top:2px">' + htmlPortretu(gracz.klasa, 84) + '</div><div class="tytul" style="font-size:20px;margin-top:2px">' + K.ik + ' ' + K.n + '</div><div class="podtytul">' + (K.rola ? K.rola + ' · ' : '') + 'poziom ' + gracz.poziom + '</div>';
  h += '<div class="info-pole">' + T.ik + ' Poziom zagrożenia: <b>' + T.n + '</b>' + (T.opis.length ? '<br><span style="opacity:0.8;font-size:12px">' + T.opis.join(' · ') + '</span>' : '') + '</div>';
  const st = [['❤️', 'zdrowie', BAZA_STATOW.hpMax + (K.staty.hpMax || 0)], ['👟', 'ruch', BAZA_STATOW.ms + (K.staty.ms || 0)], ['📈', 'zdrowia za poziom', K.hpZaPoziom || 5]];
  h += '<div class="info-pole"><b>Na start:</b> ' + st.map(x => x[0] + ' ' + x[2] + ' ' + x[1]).join(' · ') + (Object.keys(K.staty).filter(k => k !== 'hpMax' && k !== 'ms').length ? '<br>' + opisStatow(Object.fromEntries(Object.entries(K.staty).filter(([k]) => k !== 'hpMax' && k !== 'ms'))).replace(/<br>/g, ' · ') : '') + '</div>';
  h += '<div class="info-pole"><b>Pasywka:</b> ' + K.opis + '</div>';
  if (K.umi || K.umi2) {
    h += '<div class="sekcja">✨ Umiejętności <span class="licz">+' + Math.round(premiaPoziomuUmi() * 100) + '% z poziomu (co 3 poziomy +4%)</span></div>';
    if (K.umi) h += blokUmiejetnosci(K.umi, 1, true);
    if (K.umi2) h += blokUmiejetnosci(K.umi2, 2, true);
    h += '<div class="podtytul" style="font-size:11px">🤖 Auto: umiejętność sama się użyje, gdy będzie gotowa. Na dotyku przytrzymaj jej przycisk, na padzie wciśnij gałkę (L3 / R3).</div>';
  } else h += '<div class="info-pole">Bez umiejętności — cała siła w broni.</div>';
  h += '<div class="sekcja">🧬 Ewolucja</div>' + htmlEwolucji(false);
  return h;
}
function htmlEwolucji(zKupnem) {
  const K = KLASY[gracz.klasa]; let h = '';
  (K.ewo || []).forEach(e => {
    const r = ewo(e.id);
    h += '<div class="karta" style="margin-bottom:8px"><div class="karta-gora"><div class="karta-ik">' + e.ik + '</div><div><div class="karta-nazwa">' + e.n + '</div><div class="karta-tier">' +
      [0, 1, 2].map(i => '<span style="color:' + (i < r ? '#ffe08a' : 'rgba(255,255,255,0.25)') + '">●</span>').join(' ') + ' <span style="opacity:0.8">ranga ' + rzymskaR(r) + '/III</span></div></div></div><div class="karta-opis">' +
      e.r.map((t, i) => '<div style="' + (i < r ? 'color:#ffe08a' : i === r ? '' : 'opacity:0.55') + '">' + (i < r ? '✔' : rzymska(i + 1)) + ' · ' + t + (i >= r ? ' <span class="cd-tag">od poz. ' + POZIOM_EWO[i] + '</span>' : '') + '</div>').join('') + '</div>';
    if (zKupnem && r < 3) {
      const c = cenaEwo(r), pozOk = gracz.poziom >= POZIOM_EWO[r], stac = gracz.zloto >= c;
      h += '<div class="karta-dol"><span class="cena"' + (stac ? '' : ' style="color:#a05a4a"') + '>' + c + ' 💰</span><button class="btn-maly zl" data-a="ewoKup" data-id="' + e.id + '"' + (pozOk && stac ? '' : ' disabled') + '>' + (pozOk ? 'Rozwiń do ' + rzymska(r + 1) : 'od poziomu ' + POZIOM_EWO[r]) + '</button></div>';
    }
    h += '</div>';
  });
  return h;
}
function moznaEwolucje() { const K = KLASY[gracz.klasa]; return (K.ewo || []).some(e => { const r = ewo(e.id); return r < 3 && gracz.poziom >= POZIOM_EWO[r] && gracz.zloto >= cenaEwo(r); }); }
function pokazEwolucje() {
  const K = KLASY[gracz.klasa];
  let h = pasekGorny() + '<div class="tytul">🧬 Ewolucja — ' + K.ik + ' ' + K.n + '</div><div class="podtytul">Każda gałąź ma 3 rangi (od poziomu 3, 10 i 20). Umiejętności rosną też same: +4% co 3 poziomy (teraz +' + Math.round(premiaPoziomuUmi() * 100) + '%).</div>';
  h += htmlEwolucji(true) + '<button class="btn drugi" data-a="ewoWroc">◀ Wróć do sklepu</button>';
  pokazEkran(h);
}
AKCJE.ewolucja = () => pokazEwolucje();
AKCJE.ewoWroc = () => pokazSklep(false);
AKCJE.ewoKup = d => {
  const K = KLASY[gracz.klasa], e = (K.ewo || []).find(x => x.id === d.id); if (!e) return;
  const r = ewo(e.id); if (r >= 3 || gracz.poziom < POZIOM_EWO[r]) return;
  const c = cenaEwo(r); if (gracz.zloto < c) { toast('💰 Za mało złota'); return; }
  gracz.zloto -= c; gracz.ewo = gracz.ewo || {}; gracz.ewo[e.id] = r + 1; if (e.naZakup) e.naZakup(r + 1);
  poZmianieBuildu(); DZ.pryzmat(); toast('🧬 ' + e.ik + ' ' + e.n + ' → ranga ' + rzymska(r + 1)); pokazEwolucje();
};
AKCJE.autoUmi = d => { const nr = +d.n; gracz.autoUmi = gracz.autoUmi || {}; gracz.autoUmi[nr] = !gracz.autoUmi[nr]; toast('🤖 Auto-użycie ' + (gracz.autoUmi[nr] ? 'włączone' : 'wyłączone'));
  if (ekranEl.classList.contains('widoczny') && ekwZakladka === 'postac' && (stan === 'pauza' || stan === 'walka')) pokazEkwipunek('postac'); else if (modalEl.classList.contains('widoczny')) AKCJE.modalPostac(); };
function opisKlasyHtml(K) {
  const U = K.umi, U2 = K.umi2;
  const blokUmi = (X, kl) => wKontekscie(() => blokUmiejetnosci(X, kl, false));
  return '<div style="display:flex;align-items:center;gap:10px">' + htmlPortretu(KLUCZE_KLAS.find(k => KLASY[k] === K), 72) + '<div style="font-size:16px;font-weight:900;color:#ffe08a">' + K.ik + ' ' + K.n + (U2 ? ' <span class="cd-tag">2 umiejętności</span>' : (!U ? ' <span class="cd-tag">bez umiejętności</span>' : '')) + (K.rola ? '<div style="opacity:0.8;font-size:12px;font-weight:700;color:#e8dcc0">' + K.rola + '</div>' : '') + '</div></div>' + K.opis +
    '<div style="margin-top:6px">❤️ <b>' + (BAZA_STATOW.hpMax + (K.staty.hpMax || 0)) + '</b> zdrowia · 👟 <b>' + (BAZA_STATOW.ms + (K.staty.ms || 0)) + '</b> ruchu</div>' +
    (Object.keys(K.staty).length ? '<div style="margin-top:6px">' + opisStatow(K.staty) + '</div>' : '') +
    '<div style="margin-top:6px">⭐ Broń główna: <b>' + opisBroniStartowej(K) + '</b> · 🗡️ broni dodatkowych: <b>' + K.slotyOreza + '</b> · 🎒 przedmiotów: <b>' + K.slotyPrzedm + '</b> + 🔨 pryzmatów: <b>' + (K.slotyPryzm || 2) + '</b></div>' +
    (K.rodziny ? '<div style="margin-top:4px">🧩 Dobrze łączy się z rodzinami: <b>' + opisRodzinKlasy(K) + '</b></div>' : '') +
    (U ? blokUmi(U, 1) : '') + (U2 ? blokUmi(U2, 2) : '') + (K.ewo ? '<div style="margin-top:6px;opacity:0.85">🧬 Ewolucja: ' + K.ewo.map(e => e.ik + ' ' + e.n).join(' · ') + '</div>' : '');
}
function pokazPostacie() {
  const K0 = KLASY[wyborKlasy];
  let h = '<div class="tytul">Wybierz postać</div><div class="podtytul">' + TRUDNOSCI[wyborTrudnosci].ik + ' ' + TRUDNOSCI[wyborTrudnosci].n + ' · dotknij postaci, żeby zobaczyć szczegóły</div><div class="siatka3">';
  KLUCZE_KLAS.forEach(k => {
    const K = KLASY[k];
    h += '<div class="kafel' + (k === wyborKlasy ? ' wybrany' : '') + '" data-a="wybierzKlase" data-k="' + k + '">' + htmlPortretu(k, 58) + '<div class="n">' + K.n + '</div>' +
      '<div class="o">' + BRONIE_IK(K) + ' ' + (K.umi ? K.umi.ik : '') + (K.umi2 ? K.umi2.ik : '') + '</div></div>';
  });
  h += '</div>';
  h += '<button class="btn" data-a="startRunu" style="margin-top:12px">⚔️ Do lochu jako ' + K0.ik + ' ' + K0.n + '</button><button class="btn drugi" data-a="nowaGraWstecz">◀ Wstecz</button>';
  pokazEkran(h, { zachowaj: true });
}
function BRONIE_IK(K) { return K.start === 'losowa' ? '🎲' : K.start === 'wybor' ? '✋' : K.start === 'wybor2' ? '✋✋' : BRONIE[K.start].ikona; }
AKCJE.wybierzKlase = d => {
  wyborKlasy = d.k; pokazPostacie();
  pokazModal('<div class="info-pole">' + opisKlasyHtml(KLASY[d.k]) + '</div><button class="btn" data-a="startRunuZModala">⚔️ Do lochu!</button><button class="btn drugi" data-a="zamknijModal">Inna postać</button>');
};
AKCJE.startRunuZModala = () => { zamknijModal(); rozpocznijRun(wyborTrudnosci, wyborKlasy); };
AKCJE.nowaGraWstecz = () => pokazTrudnosc();
AKCJE.startRunu = () => rozpocznijRun(wyborTrudnosci, wyborKlasy);

function bronStartowa(K) { return (K.start === 'losowa' || K.start === 'wybor' || K.start === 'wybor2') ? losZ(KLUCZE_BRONI) : (BRONIE[K.start] ? K.start : 'miecz'); }
function czyWyborBroni(K) { return K.start === 'wybor' || K.start === 'wybor2'; }
function rozpocznijRun(trudnosc, klasa) {
  run = { trudnosc: trudnosc, zabici: 0, zadane: 0, przyjete: 0, leczenie: 0, zloto: 0, xp: 0, ataki: 0, trafienia: 0, zrodla: {}, zlotoFali: 0,
    start: Date.now(), falaMaks: 0, przerzutyStatow: 0 };
  gracz = nowyGracz(klasa); fala = { nr: 0, aktywna: false };
  gracz._run = run; gracz.nick = lStorGet('wiezien_nick', '') || KLASY[klasa].n; gracz.id = (typeof SIEC !== 'undefined' && SIEC.mojeId) || 0;
  gracze = [gracz]; lokalny = gracz;
  const K = KLASY[klasa];
  if (!czyWyborBroni(K)) gracz.bronie.push(nowaBron(bronStartowa(K), 0));
  przebudujHaki(); zastosujStaty(); gracz.hp = D.hpMax;
  if (K.dar) K.dar(gracz.stanKlasy);
  gracz.darmoweWybory += 2;
  poZmianieBuildu(); gracz.hp = D.hpMax;
  run.przerwa = { start: true, augment: 's', nr: 0 };
  stan = 'przerwa';
  ustawKamere();
  if (czyWyborBroni(K)) pokazWyborBroniStart(); else kolejkaPrzerwy();
  if (!lStorGet('wiezien_pomoc', false)) { lStorSet('wiezien_pomoc', true); AKCJE.jakGrac(); }
}
function pokazWyborBroniStart() {
  const K = KLASY[gracz.klasa], dwie = K.start === 'wybor2', tier = dwie ? 0 : 1;
  if (!run.ofertaBroni) run.ofertaBroni = tasuj(KLUCZE_BRONI.slice()).slice(0, dwie ? 5 : 3);
  const druga = dwie && gracz.bronie.length === 1;
  let h = '<div class="tytul">' + (dwie ? (druga ? '🤜 Druga broń' : '🤛 Pierwsza broń') : 'Twoja jedyna broń') + '</div><div class="podtytul">' +
    (dwie ? 'Akimbo walczy dwiema broniami głównymi naraz. ' + (druga ? 'Pierwsza: <b>' + BRONIE[gracz.bronie[0].rodzaj].ikona + ' ' + BRONIE[gracz.bronie[0].rodzaj].nazwa + '</b>. Wybierz drugą.' : 'Wybierz pierwszą z dwóch.') : 'Wybierz broń główną, z którą przejdziesz cały loch. Zaczyna na II tierze.') + '</div>';
  run.ofertaBroni.forEach(r => { if (druga && gracz.bronie[0].rodzaj === r) return; h += wKontekscie(() => kartaBroni({ rodzaj: r, tier: tier }, '<button class="btn-maly zl" data-a="bronStart" data-r="' + r + '">Wybieram</button>')); });
  pokazEkran(h);
}
AKCJE.bronStart = d => {
  const K = KLASY[gracz.klasa];
  if (K.start === 'wybor2') { gracz.bronie.push(nowaBron(d.r, 0)); if (gracz.bronie.length < 2) { DZ.wybor(); pokazWyborBroniStart(); return; } }
  else gracz.bronie = [nowaBron(d.r, 1)];
  run.ofertaBroni = null; poZmianieBuildu(); DZ.wybor(); kolejkaPrzerwy();
};

AKCJE.jakGrac = () => pokazModal('<div class="tytul">❓ Jak grać</div><div class="info-pole">' +
  '<b>Ruch:</b> na telefonie trzymanym pionowo przeciągnij palcem po dolnym pasku (drążek pojawi się pod palcem). <b>Poziomo</b> dotknij planszy w dowolnym miejscu — drążek pojawi się pod kciukiem, a przyciski są w prawym dolnym rogu (⛶ pełny ekran w menu). Na komputerze <b>WASD</b> / strzałki albo przytrzymaj <b>lewy przycisk myszy</b> — postać idzie w stronę kursora. Atakujesz <b>automatycznie</b>.<br>' +
  '<b>⚠️ Zamach:</b> wrogowie walczący wręcz przed ciosem się zamachują (czerwony klin). Odskocz albo przebiegnij obok, zanim się wypełni — cios trafi w powietrze. Ogłuszenie przerywa zamach.<br>' +
  '<b>✨ Umiejętność:</b> każda postać ma swoją — przycisk po prawej, na komputerze <b>E</b>, spacja albo <b>prawy przycisk myszy</b> (w stronę kursora). Druga umiejętność: <b>R</b> lub <b>Q</b>, pauza: <b>Esc</b>. Odnawia się szybciej z Przyspieszeniem.<br>' +
  '<b>🧬 Ewolucja:</b> w sklepie rozwijasz postać — 3 gałęzie (umiejętności, broń albo pasywka) po 3 rangi, odblokowywane na poziomach 3, 10 i 20. Umiejętności rosną też same: +4% co 3 poziomy. Szczegóły postaci: przycisk <b>Postać</b> w przerwie i w pauzie.<br>' +
  '<b>🤖 Auto-użycie:</b> przytrzymaj przycisk umiejętności (komputer: prawy klik na nim albo Shift+E / Shift+R, pad: wciśnij gałkę), a umiejętność sama się użyje, gdy będzie gotowa.<br>' +
  '<b>🎮 Pad:</b> podłącz kontroler (kabel albo Bluetooth) i naciśnij dowolny przycisk — gra przełączy się na sterowanie padem. Prawą gałką celujesz (puszczona = automatyczne namierzanie). Szczegóły w menu „Sterowanie”.<br>' +
  '<b>⭐ Broń główna</b> to Twoja broń z klasy — to ona atakuje. Ulepszasz ją w sklepie (tiery I–V). Skaluje się od kilku statystyk naraz.<br>' +
  '<b>🗡️ Bronie dodatkowe</b> (jak przedmioty w LoL-u) dają <b>statystyki</b> broni głównej i co kilka sekund albo co N-ty atak same coś odpalają. Dwie takie same o tym samym tierze łączą się w wyższy. Ta sama rodzina co broń główna daje <b>premię zestawu</b>.<br>' +
  '<b>🎒 Przedmioty</b> nie dają statystyk — mają pasywki: działka, krzaki z leczącymi owocami, pszczoły, miny... Ulepszasz je gwiazdkami ★.<br>' +
  '<b>💎 Tiery</b> poznasz po kamieniu w rogu ikony: <span class="kol-t0">I zwykły</span> · <span class="kol-t1">II rzadki</span> · <span class="kol-t2">III epicki</span> · <span class="kol-t3">IV legendarny</span> · <span class="kol-t4">V mityczny</span> · <span class="kol-p">pryzmatyczny</span>. Augmenty: <span class="gem-as">szare</span>, <span class="gem-az">złote</span>, <span class="gem-ap">pryzmatyczne</span>.<br>' +
  '<b>🛡️ Pancerz</b> (4 części) daje statystyki obronne. Pryzmaty — tylko z Pryzmatycznego Kowadła, bez ulepszania.<br>' +
  '<b>🧬 Augmenty</b> (szare, złote, pryzmatyczne) ulepszasz w sklepie do poziomu III.<br>' +
  '<b>Sprzedaż:</b> wszystko sprzedasz w sklepie albo w 🎒 Build między falami.<br>' +
  '<b>🎯 On-hit</b> <span class="onhit">on-hit</span> (przy trafieniu): każde trafienie bronią główną nakłada Twoje efekty on-hit (staty „On-hit” i wszystko z tym znacznikiem). Działają na <b>każdego</b> trafionego wroga (cały łuk ciosu, przebite pociskiem, w wybuchu), a efekty oznaczone „<b>raz na atak</b>” — tylko na pierwszego trafionego wroga danego ataku. Cechy samej broni (np. krwawienie) to nie on-hit. Znacznik 🔁 / ×2 oznacza, że coś nakłada efekty on-hit <b>dodatkowe razy</b>. ⏱️ — odnowienie, które skraca Przyspieszenie. 📈 pokazuje, od czego efekt rośnie.<br>' +
  '<b>⚡ Naładowanie:</b> niektóre przedmioty, bronie i augmenty mają „naładowany atak”. Energia (niebieski pasek pod zdrowiem) ładuje się z <b>biegania</b> i ataków; przy 100 następny atak bronią główną jest naładowany i odpala te efekty.<br>' +
  '<b>Miejsca:</b> przedmioty zwykłe i pryzmatyczne mają osobne miejsca (np. 4 + 2).<br>' +
  '<b>⚒️ Kowadło statystyk</b> w sklepie: czyste statystyki za złoto (wybierasz 1 z 3). Każde kolejne w tym samym sklepie jest droższe.<br>' +
  '<b>🎲 Szanse są równe:</b> sklep, skrzynie, augmenty, kowadła i statystyki losują się tak samo dla każdej postaci. Zmienia je tylko 🍀 szczęście, które każdy może zdobyć z przedmiotów i ulepszeń.<br>' +
  '<b>Drużyna:</b> złoto i doświadczenie są wspólne — każdy dostaje pełną wartość tego, co ktokolwiek podniesie, a potem działają <b>jego własne</b> premie (zysk złota, doświadczenie, Midas…).<br>' +
  '<b>🦇 Wampiryzm</b> (jedna statystyka, rzadka) leczy o procent zadanych obrażeń — najwyżej 1–5% zdrowia na sekundę. Więcej leczenia dają przedmioty: owoce, źródła, przekąski, tarcze. <b>💗 Regeneracja:</b> każda postać sama odzyskuje trochę zdrowia (0,6 + 0,3% maks. zdrowia na sekundę). Od 11. fali działa <b>🥀 zmęczenie</b>: leczenie słabnie o 2,5% z każdą falą (regeneracja nie).<br>' +
  '<b>Fale:</b> przetrwaj do końca czasu. Co 5. fala to <b>boss</b>. Z łupów, których nie zbierzesz (doświadczenie, złoto, skrzynie), po fali zostaje Ci <b>połowa</b> — reszta przepada.<br>' +
  '<b>Obrażenia:</b> <span class="fiz">fizyczne</span> (pancerz), <span class="mag">magiczne</span> (odporność), <span class="praw">prawdziwe</span> (ignorują obronę).</div><button class="btn" data-a="zamknijModal">Rozumiem</button>');

AKCJE.rekordy = () => {
  const rek = lStorGet('wiezien_rekordy', {}), rk = lStorGet('wiezien_rekordy_klas', {});
  let h = '<div class="tytul">🏆 Rekordy</div><div class="sekcja">Poziomy zagrożenia</div>';
  TRUDNOSCI.forEach((T, i) => { const r = rek[i]; h += '<div class="wiersz-stat"><span class="ik">' + T.ik + '</span><span class="n">' + T.n + '</span><span class="v' + (r ? '' : ' zero') + '">' + (r ? 'fala ' + r.fala + ' · ' + (KLASY[r.klasa] ? KLASY[r.klasa].ik : '') : '—') + '</span></div>'; });
  h += '<div class="sekcja">Postacie (najdalsza fala)</div>';
  KLUCZE_KLAS.forEach(k => { const r = rk[k]; h += '<div class="wiersz-stat"><span class="ik">' + KLASY[k].ik + '</span><span class="n">' + KLASY[k].n + '</span><span class="v' + (r ? '' : ' zero') + '">' + (r ? r : '—') + '</span></div>'; });
  pokazModal(h + '<button class="btn" data-a="zamknijModal">Zamknij</button>');
};

// ---------------------------------------------------------------------
//  RYZYKO (Hazardzista): przy każdym wyborze raz (ranga II: dwa razy) za darmo —
//  1/3 przepada, 1/3 zostaje, 1/3 ulepsza się. Krótka animacja kostki (0,65 s).
// ---------------------------------------------------------------------
function limitHazardu() { return ewo('pas') >= 2 ? 2 : 1; }
function moznaHazard(o) { return !!(gracz && KLASY[gracz.klasa].hazard && o && (o.hz || 0) < limitHazardu()); }
function przyciskHazardu(akcja, o, ex) { return moznaHazard(o) ? '<button class="btn hazard" data-a="' + akcja + '"' + (ex || '') + '>🎲 Zaryzykuj za darmo <span style="opacity:0.8;font-weight:700">(przepadnie / zostanie / ulepszy się)</span></button>' : ''; }
function rzutHazardu(o, wartoscZl, fn) {
  if (!moznaHazard(o)) return;
  o.hz = (o.hz || 0) + 1;
  const pL = ewo('pas') >= 1 ? 0.25 : 1 / 3, r = Math.random(), wynik = r < pL ? 'przepada' : r < pL + 1 / 3 ? 'zostaje' : 'lepiej';
  const tekst = { przepada: '💥 Przepadło!', zostaje: '➖ Bez zmian', lepiej: '⬆️ Ulepszone!' }[wynik], kol = { przepada: '#ff6a5a', zostaje: '#e8e0d0', lepiej: '#7ee87a' }[wynik];
  pokazModal('<div class="hazard-anim"><div class="hazard-kostka">🎲</div><div class="hazard-wynik" style="color:' + kol + '">' + tekst + '</div></div>');
  DZ.klik(); setTimeout(() => (wynik === 'lepiej' ? DZ.pryzmat : wynik === 'przepada' ? DZ.obrazenia : DZ.klik)(), 420);
  setTimeout(() => {
    zamknijModal();
    if (wynik === 'przepada' && ewo('pas') >= 3 && wartoscZl > 0) { const z = Math.round(wartoscZl * 0.3); gracz.zloto += z; toast('🎲 Przepadło — rekompensata +' + z + ' 💰'); } else toast('🎲 ' + tekst);
    fn(wynik);
  }, 650);
}
const AUG_WYZEJ = { s: 'z', z: 'p' };
AKCJE.hazardAug = () => { const o = run.augOferta; if (!o) return; rzutHazardu(o, 40 + 8 * fala.nr, w => {
  if (w === 'przepada') { run.augOferta = null; kolejkaPrzerwy(); return; }
  if (w === 'lepiej') { if (AUG_WYZEJ[o.tier]) { o.tier = AUG_WYZEJ[o.tier]; o.ids = losujAugmenty(o.tier, 3); } else { gracz.przerzutyAug++; toast('🎲 Już pryzmatyczny — +1 przerzut augmentów'); } }
  pokazAugmenty(o.tier); }); };
AKCJE.hazardStat = () => { const o = run.hzStat || (run.hzStat = {}); rzutHazardu(o, 25 + 5 * fala.nr, w => {
  if (w === 'przepada') { if (run.opcjeDarmowe) gracz.darmoweWybory--; else gracz.doWyboru--; run.opcjeStatow = null; run.hzStat = null; kolejkaPrzerwy(); return; }
  if (w === 'lepiej') run.opcjeStatow.forEach(op => { op.t = Math.min(3, op.t + 1); const u = ULEPSZENIA_STATOW.find(x => x.k === op.k); if (u) op.v = u.w[op.t]; });
  pokazWyborStatow(run.opcjeDarmowe); }); };
AKCJE.hazardSkrz = () => { const z = run.zawSkrzyni, s = gracz.skrzynie[0]; if (!z || !s) return; rzutHazardu(z, 30 + 10 * s.tier + 4 * fala.nr, w => {
  if (w === 'przepada') { nastepnaSkrzynia(); return; }
  if (w === 'lepiej') { if (s.tier < 3) { s.tier++; const hz = z.hz; run.zawSkrzyni = generujZawartosc(s); run.zawSkrzyni.hz = hz; } else { const zl = Math.round(40 + 12 * fala.nr); gracz.zloto += zl; toast('🎲 Skrzynia już legendarna — +' + zl + ' 💰'); } }
  pokazSkrzynie(); }); };
AKCJE.hazardOferta = d => { const o = run.sklep && run.sklep.oferty[+d.i]; if (!o || o.kupiona || o.rodzaj === 'kowadlo') return; rzutHazardu(o, cenaOferty(o), w => {
  if (w === 'przepada') o.kupiona = o.przepadla = true;
  if (w === 'lepiej') { if (o.rodzaj === 'oreze') o.o.tier = Math.min(3, o.o.tier + 1); else if (o.rodzaj === 'pancerz') o.p.tier = Math.min(3, o.p.tier + 1); else o.gw = Math.min(MAKS_GWIAZDEK, (o.gw || 0) + 1); }
  pokazSklep(true); }); };

// ---------------------------------------------------------------------
//  AUGMENTY
// ---------------------------------------------------------------------
function losujAugmenty(tier, n, bez) {
  const pula = AUGMENTY.filter(a => a.r === tier && !gracz.augmenty.some(x => x.id === a.id) && (!a.warunek || a.warunek()) && (!bez || bez.indexOf(a.id) < 0));
  return tasuj(pula).slice(0, n).map(a => a.id);
}
function pokazAugmenty(tier) {
  if (!run.augOferta) run.augOferta = { tier: tier, ids: losujAugmenty(tier, 3) };
  const o = run.augOferta, T = TIERY_AUG[o.tier];
  let h = pasekGorny() + '<div class="tytul">🧬 Wybierz augment</div><div class="podtytul" style="color:' + T.kolor + '">' + (o.tier === 'p' ? '<span class="kol-p" style="font-weight:900">' + T.nazwa + '</span>' : T.nazwa) + '</div>';
  o.ids.forEach(id => { h += kartaPad(kartaAugmentu(DEF_AUG[id], '<button class="btn-maly zl" data-a="augWybierz" data-id="' + id + '" style="margin-left:auto">Wybieram</button>', { id: id, poz: 1 }), 'augWybierz', 'wybierz'); });
  if (!o.ids.length) h += '<div class="slot-pusty">Brak dostępnych augmentów tego rodzaju — dostajesz 50 złota.</div><button class="btn" data-a="augPomin">Dalej</button>';
  h += przyciskHazardu('hazardAug', o);
  h += '<button class="btn drugi" data-a="augPrzerzuc"' + (gracz.przerzutyAug > 0 ? '' : ' disabled') + '>🎲 Przerzuć (zostało: ' + gracz.przerzutyAug + ')</button>';
  pokazEkran(h);
}
AKCJE.augWybierz = d => {
  const a = DEF_AUG[d.id], inst = { id: d.id, poz: 1 };
  gracz.augmenty.push(inst); run.augOferta = null;
  if (a.natychmiast) { try { a.natychmiast(inst); } catch (e) { zglosBlad(e, 'natychmiast ' + d.id); } }
  poZmianieBuildu(); DZ.wybor(); toast(a.ik + ' ' + a.n);
  kolejkaPrzerwy();
};
AKCJE.augPomin = () => { run.augOferta = null; gracz.zloto += 50; kolejkaPrzerwy(); };
AKCJE.augPrzerzuc = () => { if (gracz.przerzutyAug <= 0) return; gracz.przerzutyAug--; const o = run.augOferta; o.ids = losujAugmenty(o.tier, 3, o.ids).concat(losujAugmenty(o.tier, 3)).filter((v, i, t) => t.indexOf(v) === i).slice(0, 3); pokazAugmenty(o.tier); };
AKCJE.ulepszAug = d => {
  const a = gracz.augmenty[+d.i]; if (!a || (a.poz || 1) >= MAKS_POZ_AUG) return;
  const c = cenaUlepszeniaAug(a); if (gracz.zloto < c) return;
  gracz.zloto -= c; a.poz = (a.poz || 1) + 1;
  const def = DEF_AUG[a.id]; if (def.naUlepszenie) { try { def.naUlepszenie(a); } catch (e) { zglosBlad(e, 'naUlepszenie ' + a.id); } }
  poZmianieBuildu(); DZ.wybor(); toast(def.ik + ' ' + def.n + ' → ' + rzymska(a.poz)); odswiezEkranPrzerwy();
};

// ---------------------------------------------------------------------
//  WYBÓR STATYSTYK
// ---------------------------------------------------------------------
// Jakość statystyk zależy od numeru fali (nie od poziomu), więc jest taka sama dla każdej postaci.
function losTierStatu(min) {
  const L = 1 + D.szczescie / 100, nr = Math.max(1, (fala && fala.nr) || 1);
  const p3 = Math.min(0.1, 0.007 * nr) * L, p2 = Math.min(0.28, 0.02 * nr) * L, p1 = Math.min(0.5, 0.12 + 0.033 * nr) * L;
  const r = Math.random(); let t = r < p3 ? 3 : r < p3 + p2 ? 2 : r < p3 + p2 + p1 ? 1 : 0;
  return Math.max(min || 0, t);
}
function losujOpcjeStatow(min) {
  // statystyka z progiem (wampiryzm) pojawia się tylko, gdy wylosuje się jej tier - inaczej bierzemy następną
  const wyn = [];
  for (const u of tasuj(ULEPSZENIA_STATOW.slice())) { if (wyn.length >= 4) break; const t = losTierStatu(min); if (u.odTieru > t) continue; wyn.push({ k: u.k, t: t, v: u.w[t] }); }
  return wyn;
}
function losUlepszeniaStatu(t) { return losZ(ULEPSZENIA_STATOW.filter(u => !(u.odTieru > t))); }
function kosztPrzerzutuStatow() { return Math.round((1 + fala.nr * 0.5) * (1 + run.przerzutyStatow * 0.5)); }
function pokazWyborStatow(darmowy) {
  if (!run.opcjeStatow || run.opcjeDarmowe !== darmowy) { run.opcjeStatow = losujOpcjeStatow(darmowy ? 1 : 0); run.opcjeDarmowe = darmowy; }
  const ile = darmowy ? gracz.darmoweWybory : gracz.doWyboru;
  let h = pasekGorny() + '<div class="tytul">' + (darmowy ? '🎁 Darmowe ulepszenie' : '⭐ Poziom ' + (gracz.poziom - gracz.doWyboru + 1)) + '</div><div class="podtytul">Wybierz statystykę · ' + (ile > 1 ? 'zostało jeszcze <b>' + ile + '</b>' : 'ostatni wybór') + '</div><div class="siatka2">';
  run.opcjeStatow.forEach((o, i) => {
    const S = STAT[o.k];
    h += '<div class="kafel karta t' + o.t + ' wybieralna" data-a="statWybierz" data-i="' + i + '" style="margin:0"><div class="ik">' + S.i + '</div><div class="n">' + S.n + '</div>' +
      '<div style="font-size:20px;font-weight:900;color:' + TIERY[o.t].kolor + ';margin-top:4px">+' + fmt(o.v) + (S.j === '%' ? '%' : (S.j || '')) + '</div>' +
      '<div class="o">Teraz: ' + wartoscStatuTekst(o.k, D[o.k]) + '</div><div class="o" style="margin-top:2px;opacity:0.75">' + S.o + '</div></div>';
  });
  h += '</div>' + przyciskHazardu('hazardStat', run.hzStat || (run.hzStat = {}), ' style="margin-top:12px"') + '<button class="btn drugi" data-a="statPrzerzuc" style="margin-top:12px"' + (gracz.zloto >= kosztPrzerzutuStatow() ? '' : ' disabled') + '>🎲 Przerzuć (' + kosztPrzerzutuStatow() + ' 💰)</button>';
  pokazEkran(h);
}
AKCJE.statWybierz = d => {
  const o = run.opcjeStatow[+d.i]; if (!o) return;
  gracz.ulepszenia[o.k] = (gracz.ulepszenia[o.k] || 0) + o.v;
  if (run.opcjeDarmowe) gracz.darmoweWybory--; else gracz.doWyboru--;
  run.opcjeStatow = null; run.hzStat = null; poZmianieBuildu(); DZ.wybor();
  kolejkaPrzerwy();
};
AKCJE.statPrzerzuc = () => { const k = kosztPrzerzutuStatow(); if (gracz.zloto < k) return; gracz.zloto -= k; run.przerzutyStatow++; run.opcjeStatow = losujOpcjeStatow(run.opcjeDarmowe ? 1 : 0); run.hzStat = null; pokazWyborStatow(run.opcjeDarmowe); };

// ---------------------------------------------------------------------
//  SKRZYNIE
// ---------------------------------------------------------------------
// Każda postać losuje bronie z tej samej puli, po równo.
function losujIdOreza() { return losZ(OREZE).id; }
function generujZawartosc(s) {
  const nr = Math.max(1, fala.nr), t = s.tier;
  if (s.boss) {
    const r = Math.random();
    if (r < 0.3 && gracz.bronie.some(b => b.tier < MAKS_TIER_BRONI)) return { r: 'kamien' };
    return r < 0.65 ? { r: 'oreze', o: nowyOrez(losujIdOreza(), t) } : { r: 'pancerz', p: nowyPancerz(losZ(PANCERZE).id, t) };
  }
  const r = Math.random();
  if (r < 0.2) return { r: 'zloto', ile: Math.round((15 + 5 * nr) * (1 + t * 0.7)) };
  if (r < 0.52) return { r: 'oreze', o: nowyOrez(losujIdOreza(), t) };
  if (t >= 2 && r < 0.58 && gracz.bronie.some(b => b.tier < MAKS_TIER_BRONI)) return { r: 'kamien' };
  return { r: 'pancerz', p: nowyPancerz(losZ(PANCERZE).id, t) };
}
function paraOreza(o) { return gracz.oreze.find(x => x !== o && x.id === o.id && x.tier === o.tier && x.tier < 3); }
function pokazSkrzynie() {
  const s = gracz.skrzynie[0];
  if (!run.zawSkrzyni) run.zawSkrzyni = generujZawartosc(s);
  const z = run.zawSkrzyni;
  let h = pasekGorny() + '<div class="tytul">📦 ' + (s.boss ? 'Skrzynia bossa' : 'Skrzynia') + ' <span class="kol-t' + s.tier + '">(' + TIERY[s.tier].nazwaZ.toLowerCase() + ')</span></div><div class="podtytul">Zostało skrzyń: <b>' + gracz.skrzynie.length + '</b></div>';
  if (z.r === 'zloto') h += '<div class="karta t' + s.tier + '" style="text-align:center"><div style="font-size:44px">💰</div><div class="karta-nazwa">' + z.ile + ' złota</div></div><button class="btn" data-a="skrzZloto">Weź</button>';
  else if (z.r === 'kamien') {
    const b = gracz.bronie[0];
    h += '<div class="karta t3" style="text-align:center"><div style="font-size:44px">💎</div><div class="karta-nazwa">Kamień Kowalski</div><div class="karta-opis">Twoja broń główna <b>' + BRONIE[b.rodzaj].ikona + ' ' + nazwaBroni(b) + '</b> zyskuje <b>+1 tier</b> za darmo.</div></div><button class="btn ziel" data-a="skrzKamien">⬆️ Ulepsz broń główną</button>';
  }
  else if (z.r === 'pancerz') {
    const slot = DEF_PANC[z.p.id].slot, ob = gracz.pancerz[slot];
    h += kartaPancerza(z.p, '', '✨ Nowy');
    if (ob) h += kartaPancerza(ob, '', 'Teraz noszone');
    h += '<button class="btn" data-a="skrzZaloz">' + (ob ? 'Załóż (stary sprzedany za ' + Math.round(cenaPancerza(ob) * 0.5) + ' 💰)' : 'Załóż') + '</button>';
    h += '<button class="btn drugi" data-a="skrzSprzedaj">Sprzedaj (+' + Math.round(cenaPancerza(z.p) * 0.5) + ' 💰)</button>';
  } else if (z.r === 'oreze') {
    h += kartaOreza(z.o);
    const para = paraOreza(z.o);
    if (para) h += '<button class="btn ziel" data-a="skrzPolacz">⬆️ Połącz z posiadaną → ' + DEF_ORE[z.o.id].n + ' ' + TIERY[z.o.tier + 1].rz + '</button>';
    if (gracz.oreze.length < gracz.slotyOreza) h += '<button class="btn" data-a="skrzWezOreze">Weź broń (' + (gracz.oreze.length + 1) + '/' + gracz.slotyOreza + ')</button>';
    else if (gracz.oreze.length) h += '<button class="btn" data-a="skrzZamienOreze">Zamień z posiadaną…</button>';
    h += '<button class="btn drugi" data-a="skrzSprzedaj">Sprzedaj (+' + wartoscSprzedazyOreza(z.o) + ' 💰)</button>';
  }
  h += przyciskHazardu('hazardSkrz', z);
  pokazEkran(h);
}
function nastepnaSkrzynia() { gracz.skrzynie.shift(); run.zawSkrzyni = null; poZmianieBuildu(); kolejkaPrzerwy(); }
AKCJE.skrzZloto = () => { gracz.zloto += run.zawSkrzyni.ile; DZ.moneta(); nastepnaSkrzynia(); };
AKCJE.skrzKamien = () => { const b = gracz.bronie.find(x => x.tier < MAKS_TIER_BRONI); if (b) { b.tier++; toast('💎 ' + nazwaBroni(b)); DZ.pryzmat(); } nastepnaSkrzynia(); };
AKCJE.skrzZaloz = () => { const p = run.zawSkrzyni.p, slot = DEF_PANC[p.id].slot, ob = gracz.pancerz[slot]; if (ob) gracz.zloto += Math.round(cenaPancerza(ob) * 0.5); gracz.pancerz[slot] = p; DZ.zakup(); nastepnaSkrzynia(); };
AKCJE.skrzSprzedaj = () => { const z = run.zawSkrzyni; gracz.zloto += z.r === 'pancerz' ? Math.round(cenaPancerza(z.p) * 0.5) : wartoscSprzedazyOreza(z.o); DZ.moneta(); nastepnaSkrzynia(); };
AKCJE.skrzPolacz = () => { const z = run.zawSkrzyni, para = paraOreza(z.o); if (para) { para.tier++; toast('⬆️ ' + nazwaOreza(para)); DZ.wybor(); } nastepnaSkrzynia(); };
AKCJE.skrzWezOreze = () => { gracz.oreze.push(run.zawSkrzyni.o); DZ.zakup(); nastepnaSkrzynia(); };
AKCJE.skrzZamienOreze = () => wyborZamianyOreza(run.zawSkrzyni.o, () => nastepnaSkrzynia());

function wyborZamianyOreza(nowa, potem) {
  run.oczekOre = { o: nowa, potem: potem };
  let h = '<div class="tytul">Którą broń zamienić?</div><div class="podtytul">Wymieniona broń zostanie sprzedana.</div>' +
    '<div class="sekcja">✨ Nowa</div>' + kartaOreza(nowa) + '<div class="sekcja">🗡️ Twoje bronie — wybierz, którą oddać</div>';
  gracz.oreze.forEach((o, i) => { h += kartaPad(kartaOreza(o, '<button class="btn-maly zl" data-a="zamienOreze" data-i="' + i + '" style="margin-left:auto">Zamień (+' + wartoscSprzedazyOreza(o) + ' 💰)</button>'), 'zamienOreze', 'zamień'); });
  h += '<button class="btn drugi" data-a="zamknijModal">Anuluj</button>';
  pokazModal(h);
}
AKCJE.zamienOreze = d => { const o = run.oczekOre, i = +d.i, st = gracz.oreze[i]; if (!o || !st) return; gracz.zloto += wartoscSprzedazyOreza(st); gracz.oreze[i] = o.o; run.oczekOre = null; zamknijModal(); poZmianieBuildu(); DZ.zakup(); o.potem(); };

// dodanie przedmiotu, gdy brak miejsca - wybór, co sprzedać
function dodajPrzedmiotZWyborem(inst, potem) {
  const pr = czyPryzmat(inst);
  if (wolneSlotyPrzedm(pr) > 0) { gracz.przedmioty = gracz.przedmioty.filter(p => p); gracz.przedmioty.push(inst); poZmianieBuildu(); potem(); return; }
  run.oczekPrz = { inst: inst, potem: potem };
  let h = '<div class="tytul">Brak miejsca</div><div class="podtytul">Sprzedaj jeden ' + (pr ? 'przedmiot <b>pryzmatyczny</b>' : 'zwykły przedmiot') + ', żeby zrobić miejsce na nowy.</div>' +
    '<div class="sekcja">✨ Nowy</div>' + kartaPrzedmiotu(inst) + '<div class="sekcja">🎒 Twoje ' + (pr ? 'pryzmaty' : 'przedmioty') + ' — wybierz, który sprzedać</div>';
  gracz.przedmioty.forEach((p, i) => { if (p && czyPryzmat(p) === pr) h += kartaPad(kartaPrzedmiotu(p, '<button class="btn-maly czerw" data-a="zamienPrz" data-i="' + i + '" style="margin-left:auto">Sprzedaj (+' + wartoscSprzedazy(p) + ' 💰)</button>'), 'zamienPrz', 'sprzedaj'); });
  h += '<button class="btn drugi" data-a="porzucPrz">Zrezygnuj z nowego (+' + wartoscSprzedazy(inst) + ' 💰)</button>';
  modalEl.dataset.wymuszony = '1';
  pokazModal(h);
}
AKCJE.zamienPrz = d => { const o = run.oczekPrz, i = +d.i; gracz.zloto += wartoscSprzedazy(gracz.przedmioty[i]); cofnijPrzedmiot(gracz.przedmioty[i]); gracz.przedmioty[i] = o.inst; run.oczekPrz = null; delete modalEl.dataset.wymuszony; zamknijModal(); poZmianieBuildu(); DZ.zakup(); o.potem(); };
AKCJE.porzucPrz = () => { const o = run.oczekPrz; gracz.zloto += wartoscSprzedazy(o.inst); run.oczekPrz = null; delete modalEl.dataset.wymuszony; zamknijModal(); poZmianieBuildu(); o.potem(); };

// ---------------------------------------------------------------------
//  KOWADŁO PRYZMATYCZNE
// ---------------------------------------------------------------------
function ileWKowadle() { const K = KLASY[gracz.klasa]; return K.kowadloWybor ? K.kowadloWybor() : 3; }
function pokazKowadlo() {
  if (!run.ofertaKow) run.ofertaKow = tasuj(PRYZMATY.filter(p => !maPrzedmiot(p.id)).map(p => p.id)).slice(0, ileWKowadle());
  let h = pasekGorny() + '<div class="tytul">🔨 <span class="kol-p">Pryzmatyczne Kowadło</span></div><div class="podtytul">Wybierz jeden przedmiot pryzmatyczny. Miejsca na pryzmaty: <b>' + liczPrzedm(true) + '/' + slotyTypu(true) + '</b></div>';
  run.ofertaKow.forEach(id => { h += kartaPad(kartaPrzedmiotu(nowyPrzedmiot(id), '<button class="btn-maly zl" data-a="kowWybierz" data-id="' + id + '" style="margin-left:auto">Wybieram</button>'), 'kowWybierz', 'wybierz'); });
  if (!run.przerzutKow) h += '<button class="btn drugi" data-a="kowPrzerzuc">🎲 Przerzuć (raz, za darmo)</button>';
  h += '<button class="btn drugi" data-a="kowPomin">Odrzuć kowadło (+60 💰)</button>';
  pokazEkran(h);
}
AKCJE.kowWybierz = d => { gracz.kowadla--; run.ofertaKow = null; run.przerzutKow = false; DZ.pryzmat(); dodajPrzedmiotZWyborem(nowyPrzedmiot(d.id), () => { const def = DEF_PRZ[d.id]; if (def.natychmiast) { try { def.natychmiast(); } catch (e) { zglosBlad(e, 'pryzmat natychmiast'); } poZmianieBuildu(); } kolejkaPrzerwy(); }); };
AKCJE.kowPrzerzuc = () => { run.przerzutKow = true; const st = run.ofertaKow; run.ofertaKow = tasuj(PRYZMATY.filter(p => !maPrzedmiot(p.id) && st.indexOf(p.id) < 0).map(p => p.id)).slice(0, ileWKowadle()); if (run.ofertaKow.length < 3) run.ofertaKow = st; pokazKowadlo(); };
AKCJE.kowPomin = () => { gracz.kowadla--; run.ofertaKow = null; run.przerzutKow = false; gracz.zloto += 60; kolejkaPrzerwy(); };

// ---------------------------------------------------------------------
//  SKLEP
// ---------------------------------------------------------------------
function losujTierSklepu() {
  const nr = Math.max(1, fala.nr), L = 1 + D.szczescie / 100;
  const p3 = Math.min(0.1, Math.max(0, (nr - 6) * 0.009)) * L, p2 = Math.min(0.28, Math.max(0, (nr - 2) * 0.024)) * L, p1 = Math.min(0.5, 0.1 + nr * 0.03) * L;
  const r = Math.random(); return r < p3 ? 3 : r < p3 + p2 ? 2 : r < p3 + p2 + p1 ? 1 : 0;
}
function losujOferte(oferty) {
  const nr = Math.max(1, fala.nr);
  if (nr >= 4 && !oferty.some(o => o.rodzaj === 'kowadlo') && Math.random() < 0.06 * (1 + D.szczescie / 200)) return { rodzaj: 'kowadlo' };
  const r = Math.random(), szansaOreza = gracz.slotyOreza > 0 ? 0.4 : 0;
  if (r < szansaOreza) {
    let t = losujTierSklepu(); if (t > 0 && Math.random() < 0.35) t--;
    let id = losujIdOreza(), prob = 0;
    while (oferty.some(o => o.rodzaj === 'oreze' && o.o.id === id) && prob++ < 6) id = losujIdOreza();
    return { rodzaj: 'oreze', o: nowyOrez(id, t) };
  }
  if (r < szansaOreza + 0.1) return { rodzaj: 'pancerz', p: nowyPancerz(losZ(PANCERZE).id, Math.max(0, losujTierSklepu() - (Math.random() < 0.4 ? 1 : 0))) };
  let t = losujTierSklepu();
  for (; t >= 0; t--) {
    const pula = PRZEDMIOTY.filter(p => p.t === t && !(p.unik && maPrzedmiot(p.id)) && !oferty.some(o => o.id === p.id));
    if (pula.length) return { rodzaj: 'przedmiot', id: losZ(pula).id };
  }
  return { rodzaj: 'przedmiot', id: 'rog' };
}
function cenaOferty(o) {
  if (o.rodzaj === 'kowadlo') return Math.round(120 * mnCeny() + 4 * fala.nr);
  if (o.rodzaj === 'oreze') return cenaOreza(o.o.tier);
  if (o.rodzaj === 'pancerz') return cenaPancerza(o.p);
  return cenaPrzedmiotu(DEF_PRZ[o.id]);
}
function nowySklep() {
  const stare = run.sklep ? run.sklep.oferty.filter(o => o && o.zabl && !o.kupiona) : [];
  run.sklep = { oferty: stare, przerzuty: 0, darmowe: gracz.darmowePrzerzuty };
  while (run.sklep.oferty.length < 5) run.sklep.oferty.push(losujOferte(run.sklep.oferty));
}
function kosztPrzerzutuSklepu() { return Math.max(1, Math.round((2 + fala.nr * 0.6) * (1 + run.sklep.przerzuty * 0.45) * Math.max(0.4, 1 - gracz.rabat / 100) * Math.max(0.2, 1 - 0.35 * (FLAGI.oszczedny || 0)))); }
function cenaUlepszeniaBroniGl(b) { return Math.round(cenaUlepszeniaGlownej(b) * Math.max(0.5, 1 - 0.15 * (FLAGI.oszczedny || 0))); }
// ---------------------------------------------------------------------
//  SKLEP. Komputer (układ poziomy): po lewej to, co masz (broń główna obok ewolucji,
//  bronie dodatkowe, przedmioty, pryzmaty, pancerz) i pionowy pasek augmentów,
//  po prawej to, co możesz kupić - 5 kart tej samej wielkości, przerzut i statystyki.
//  Telefon: dwie zakładki - 🛒 Kup i 🎒 Twój build (ulepszanie, ewolucja).
// ---------------------------------------------------------------------
// kolumny tylko na dużym ekranie; telefon (także poziomo, gdzie jest mało wysokości) - zakładki
function czySklepPC() { return $('gra').classList.contains('pc') && (ekranEl.clientHeight || window.innerHeight) >= 540; }
function htmlAkcjiSklepu(sk) {
  const kp = sk.darmowe > 0 ? 0 : kosztPrzerzutuSklepu(), ck = cenaKowadlaStatow();
  return '<div class="sklep-akcje">' +
    '<button class="akcja-sklepu przerzut' + (sk._kreci ? ' kreci' : '') + '" data-a="przerzucSklep"' + (gracz.zloto >= kp ? '' : ' disabled') + '>' + IKONA_PRZERZUT +
      '<span class="as-tekst"><b>Przerzuć</b><span>' + (kp ? kp + ' 💰' : 'za darmo' + (sk.darmowe > 1 ? ' (' + sk.darmowe + ')' : '')) + '</span></span></button>' +
    '<button class="akcja-sklepu staty" data-a="kowadloStatow"' + (gracz.zloto >= ck ? '' : ' disabled') + '>' + IKONA_STATY +
      '<span class="as-tekst"><b>Statystyki</b><span>' + ck + ' 💰 · 1 z 3</span></span></button></div>';
}
function htmlPrzyciskuEwolucji() {
  const K = KLASY[gracz.klasa]; if (!K.ewo) return '';
  return '<button class="akcja-sklepu ewo' + (moznaEwolucje() ? ' gotowa' : '') + '" data-a="ewolucja">' + IKONA_EWO + '<span class="as-tekst"><b>Ewolucja postaci' + (moznaEwolucje() ? ' ⬆' : '') + '</b><span>' +
    K.ewo.map(e => e.ik + ' ' + rzymskaR(ewo(e.id))).join(' · ') + '</span></span></button>';
}
// karta oferty: zawsze tej samej wielkości (opis przycięty, pełny po kliknięciu w kartę albo ℹ️)
function kartaOferty(o, i, wModalu) {
  if (o.kupiona && !wModalu) return '<div class="oferta-pusta">' + (o.przepadla ? '🎲 Przepadło' : '✔ Kupione') + '</div>';
  const cena = cenaOferty(o), stac = gracz.zloto >= cena;
  const kupA = wModalu ? 'kupZInfo' : 'kup';
  const dol = '<span class="cena"' + (stac ? '' : ' style="color:#a05a4a"') + '>' + cena + ' 💰</span><span class="of-btn">' +
    (!wModalu ? '<button class="btn-maly info" data-a="ofertaInfo" data-i="' + i + '" title="Pełny opis">ℹ️</button>' : '') +
    (o.rodzaj !== 'kowadlo' && moznaHazard(o) ? '<button class="btn-maly hazard" data-a="hazardOferta" data-i="' + i + '" title="Zaryzykuj za darmo">🎲</button>' : '') +
    '<button class="btn-maly" data-a="zablokuj" data-i="' + i + '" title="' + (o.zabl ? 'Odblokuj' : 'Zablokuj - zostanie po przerzucie') + '">' + (o.zabl ? '🔒' : '🔓') + '</button>' +
    '<button class="btn-maly zl" data-a="' + kupA + '" data-i="' + i + '"' + (stac ? '' : ' disabled') + '>Kup</button></span>';
  let karta = '';
  if (o.rodzaj === 'kowadlo') karta = '<div class="karta tp"><div class="karta-gora"><div class="karta-ik">🔨</div><div><div class="karta-nazwa">Pryzmatyczne Kowadło</div><div class="karta-tier"><span class="kol-p">Wybór przedmiotu pryzmatycznego</span></div></div></div><div class="karta-srodek"><div class="karta-opis">Po zakupie wybierasz jeden z 3 przedmiotów pryzmatycznych.</div></div><div class="karta-dol">' + dol + '</div></div>';
  else if (o.rodzaj === 'oreze') karta = kartaOreza(o.o, (paraOreza(o.o) ? '<span class="tag tag-ok">⬆️ połączy się</span>' : '') + dol);
  else if (o.rodzaj === 'pancerz') { const ob = gracz.pancerz[DEF_PANC[o.p.id].slot]; karta = kartaPancerza(o.p, (ob ? '<span class="tag">zamieni: ' + DEF_PANC[ob.id].ik + ' ' + TIERY[ob.tier].rz + '</span>' : '') + dol); }
  else { const ile = gracz.przedmioty.filter(p => p && p.id === o.id).length; karta = kartaPrzedmiotu(Object.assign(nowyPrzedmiot(o.id), { gw: o.gw || 0 }), (ile ? '<span class="tag tag-ok">masz: ' + ile + ' · działa osobno</span>' : '') + dol); }
  if (wModalu) return karta;
  karta = karta.replace('<div class="karta ', '<div class="karta oferta' + (o.zabl ? ' zablok' : '') + ' ').replace('<div class="karta-srodek">', '<div class="karta-srodek" data-a="ofertaInfo" data-i="' + i + '">');
  return kartaPad(karta, 'kup', 'kup', 'zablokuj', o.zabl ? 'odblokuj' : 'zablokuj');
}
function ileUlepszenDostepnych() {
  const z = gracz.zloto, K = KLASY[gracz.klasa]; let n = 0;
  gracz.bronie.forEach(b => { if (b.tier < MAKS_TIER_BRONI && z >= cenaUlepszeniaBroniGl(b)) n++; });
  gracz.oreze.forEach(o => { if (paraOreza(o) || (o.tier < 3 && z >= cenaUlepszeniaOreza(o))) n++; });
  gracz.przedmioty.forEach(p => { if (p && (!czyPryzmat(p) || K.ulepszaPryzmaty) && (p.gw || 0) < MAKS_GWIAZDEK && z >= cenaUlepszenia(p)) n++; });
  gracz.augmenty.forEach(a => { if ((a.poz || 1) < MAKS_POZ_AUG && z >= cenaUlepszeniaAug(a)) n++; });
  if (moznaEwolucje()) n++;
  return n;
}
// pionowy pasek augmentów (komputer)
function pasekAugmentow(zarz) {
  let h = '<div class="sp-aug-tyt" title="Augmenty">🧬<b>' + gracz.augmenty.length + '</b></div>';
  if (!gracz.augmenty.length) h += '<div class="sp-aug-pusto">brak</div>';
  gracz.augmenty.forEach((a, i) => {
    const d = DEF_AUG[a.id], T = TIERY_AUG[d.r], mozna = zarz && (a.poz || 1) < MAKS_POZ_AUG && gracz.zloto >= cenaUlepszeniaAug(a);
    h += kafelek('aug', i, d.ik, d.n, d.r === 'p' ? KOLOR_PRYZMAT : T.kolor, rzymska(a.poz || 1), '', mozna ? '⬆' : '', (d.r === 'p' ? 'pryzm g-ap' : 'g-a' + d.r) + ' kfl-maly');
  });
  return h;
}
function pokazSklep(zachowaj) {
  const sk = run.sklep, nr = fala.nr, pc = czySklepPC();
  sk.zak = sk.zak || 'kup';
  const boss = czyFalaBossa(nr + 1);
  const falaBtn = (kl) => '<button class="btn' + (kl ? ' ' + kl : '') + '" data-a="dalejZeSklepu">▶ Fala ' + (nr + 1) + (boss ? ' — 👑 boss' : '') + '</button>';
  const akcje = htmlAkcjiSklepu(sk), ewoBtn = htmlPrzyciskuEwolucji();
  const oferty = '<div class="sp-oferty">' + sk.oferty.map((o, i) => kartaOferty(o, i)).join('') + '</div>';
  sk._kreci = false;
  let h;
  if (pc) {
    h = '<div class="sp-gora"><div class="zloto-duze">💰 ' + Math.floor(gracz.zloto) + '</div>' +
      '<div class="sp-tytul">🛒 Sklep<small>przed falą <b>' + (nr + 1) + '</b>' + (boss ? ' — <span class="czer">BOSS!</span>' : '') + '</small></div>' +
      falaBtn('sp-fala') +
      '<div class="sp-gora-btn"><button class="btn-maly" data-a="modalPostac">' + KLASY[gracz.klasa].ik + ' Postać</button><button class="btn-maly" data-a="modalStaty">📊 Staty</button><button class="btn-maly" data-a="modalBuild">🎒 Build</button></div></div>' +
      '<div class="sp-uklad"><div class="sp-aug">' + pasekAugmentow(true) + '</div>' +
      '<div class="sp-build">' + sekcjeBuildu(true, { ewo: ewoBtn, bezAug: true }) + '</div>' +
      '<div class="sp-sklep"><div class="sekcja" style="margin-top:0">🛒 Na sprzedaż <span class="licz">' + sk.oferty.filter(o => !o.kupiona).length + '/5</span></div>' + akcje + oferty + '</div></div>';
  } else {
    const ile = ileUlepszenDostepnych();
    h = pasekGorny() + '<div class="sp-tel-naglowek"><div class="sp-tel-tytul">🛒 Sklep <small>przed falą <b>' + (nr + 1) + '</b>' + (boss ? ' — <span class="czer">BOSS!</span>' : '') + '</small></div>' + falaBtn() + '</div>' +
      '<div class="sp-tel-pasek"><div class="zakladki sp-zak"><button class="' + (sk.zak === 'kup' ? 'akt' : '') + '" data-a="sklepZak" data-z="kup">🛒 Kup</button>' +
      '<button class="' + (sk.zak === 'build' ? 'akt' : '') + '" data-a="sklepZak" data-z="build">🎒 Twój build' + (ile ? ' <span class="licznik-ul">⬆' + ile + '</span>' : '') + '</button></div>';
    if (sk.zak === 'build') h += '</div>' + sekcjeBuildu(true, { ewo: ewoBtn });
    else h += akcje + '</div>' + oferty;
    h += falaBtn() .replace('class="btn"', 'class="btn" style="margin-top:14px"');
  }
  pokazEkran(h, { zachowaj: zachowaj, klasa: pc ? 'sklep-pc' : 'sklep-tel' });
  dopasujOferty();
}
// Komputer: wszystkie oferty jednakowej wysokości, tak żeby sklep zmieścił się na ekranie
function dopasujOferty() {
  const kont = ekranEl.querySelector('.sp-oferty'); if (!kont) return;
  if (czySklepPC()) {
    const sk = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--skalaUI')) || 1;
    // ile miejsca zostało pod nagłówkiem (we współrzędnych zawartości ekranu - z poprawką na powiększenie interfejsu)
    const rE = ekranEl.getBoundingClientRect(), rK = kont.getBoundingClientRect(), zoom = (rK.width / (kont.offsetWidth || rK.width)) || sk;
    const wys = (rE.bottom - rK.top - parseFloat(getComputedStyle(ekranEl).paddingBottom || 0) - 6) / zoom - 4 * 8;
    const h = Math.round(ogr(wys / 5, 100, 210));
    kont.style.setProperty('--hOf', h + 'px'); kont.classList.toggle('ciasno', h < 124);
  }
  kont.querySelectorAll('.karta-srodek').forEach(e => e.classList.toggle('ucieta', e.scrollHeight > e.clientHeight + 3));
}
AKCJE.sklepZak = d => { if (!run.sklep) return; run.sklep.zak = d.z === 'build' ? 'build' : 'kup'; pokazSklep(false); };
AKCJE.ofertaInfo = d => {
  const o = run.sklep && run.sklep.oferty[+d.i]; if (!o || o.kupiona) return;
  pokazModal(kartaOferty(o, +d.i, true) + '<button class="btn drugi" data-a="zamknijModal" style="margin-top:10px">Zamknij</button>');
};
AKCJE.kupZInfo = d => { zamknijModal(); AKCJE.kup(d); };
const IKONA_PRZERZUT = '<svg class="as-ik" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.3-4.9L4 8"/><path d="M4 3v5h5"/><path d="M4 13a8 8 0 0 0 14.3 4.9L20 16"/><path d="M20 21v-5h-5"/></svg>';
const IKONA_EWO = '<svg class="as-ik" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M7 3c0 6 10 6 10 12M17 3c0 6-10 6-10 12M7 21c0-2 1.5-3.4 5-4.5 3.5 1.1 5 2.5 5 4.5"/><path d="M8.5 6.5h7M8 11h8" stroke-width="1.6"/></svg>';
const IKONA_STATY = '<svg class="as-ik" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18" fill="none" stroke-width="2.4" stroke-linecap="round"/><rect x="4.5" y="13" width="3.6" height="6" rx="1"/><rect x="10.2" y="9" width="3.6" height="10" rx="1"/><rect x="15.9" y="11" width="3.6" height="8" rx="1"/><path d="M17.7 2.5l3.3 3.6h-2.2v3h-2.2v-3h-2.2z"/></svg>';

// ---------------------------------------------------------------------
//  KOWADŁO STATYSTYK — czyste statystyki za złoto (jak kowadła w Arenie LoL-a).
//  Kupujesz ile chcesz; w jednym sklepie każde kolejne jest droższe o 20% ceny bazowej.
// ---------------------------------------------------------------------
function cenaKowadlaStatow() { const k = (run.sklep && run.sklep.kowStat) || 0; return Math.round(70 * mnCeny() * (1 + 0.2 * k)); }
function pokazKowadloStatow() {
  if (!run.kowStat) run.kowStat = losujOpcjeStatow(1).slice(0, 3);
  const c = cenaKowadlaStatow(), stac = gracz.zloto >= c;
  let h = pasekGorny() + '<div class="tytul">⚒️ Kowadło statystyk</div><div class="podtytul">Wybierz jedną statystykę — kosztuje <b class="zl">' + c + ' 💰</b>' +
    (run.sklep && run.sklep.kowStat ? ' (kolejne w tym sklepie drożeje)' : '') + '.</div><div class="siatka3 trzy">';
  run.kowStat.forEach((o, i) => {
    const S = STAT[o.k];
    h += '<div class="kafel karta t' + o.t + ' wybieralna" data-a="kowStatWybierz" data-i="' + i + '" style="margin:0' + (stac ? '' : ';opacity:0.45') + '"><div class="ik">' + S.i + '</div><div class="n">' + S.n + '</div>' +
      '<div style="font-size:20px;font-weight:900;color:' + TIERY[o.t].kolor + ';margin-top:4px">+' + fmt(o.v) + (S.j === '%' ? '%' : (S.j || '')) + '</div>' +
      '<div class="o">Teraz: ' + wartoscStatuTekst(o.k, D[o.k]) + '</div></div>';
  });
  h += '</div><button class="btn drugi" data-a="kowStatWroc" style="margin-top:12px">◀ Wróć do sklepu</button>';
  pokazEkran(h);
}
AKCJE.kowadloStatow = () => { if (gracz.zloto >= cenaKowadlaStatow()) pokazKowadloStatow(); };
AKCJE.kowStatWybierz = d => {
  const c = cenaKowadlaStatow(), o = run.kowStat && run.kowStat[+d.i];
  if (!o) return;
  if (gracz.zloto < c) { toast('💰 Za mało złota'); return; }
  gracz.zloto -= c; gracz.ulepszenia[o.k] = (gracz.ulepszenia[o.k] || 0) + o.v;
  run.sklep.kowStat = (run.sklep.kowStat || 0) + 1; run.kowStat = null;
  poZmianieBuildu(); DZ.pryzmat(); toast('⚒️ ' + STAT[o.k].i + ' ' + STAT[o.k].n + ' +' + fmt(o.v) + (STAT[o.k].j === '%' ? '%' : ''));
  pokazSklep(false);
};
AKCJE.kowStatWroc = () => pokazSklep(false);
AKCJE.przerzucSklep = () => {
  const sk = run.sklep; let k = 0;
  if (sk.darmowe > 0) sk.darmowe--; else { k = kosztPrzerzutuSklepu(); if (gracz.zloto < k) return; sk.przerzuty++; }
  gracz.zloto -= k;
  const nowe = sk.oferty.filter(o => o.zabl && !o.kupiona);
  while (nowe.length < 5) nowe.push(losujOferte(nowe));
  sk.oferty = nowe; sk._kreci = true; DZ.klik(); pokazSklep(true);
};
AKCJE.zablokuj = d => { const o = run.sklep.oferty[+d.i]; o.zabl = !o.zabl; pokazSklep(true); };
AKCJE.kup = d => {
  const o = run.sklep.oferty[+d.i]; if (!o || o.kupiona) return;
  const cena = cenaOferty(o); if (gracz.zloto < cena) return;
  if (o.rodzaj === 'kowadlo') { gracz.zloto -= cena; o.kupiona = true; gracz.kowadla++; DZ.pryzmat(); pokazKowadloZeSklepu(); return; }
  if (o.rodzaj === 'oreze') {
    const para = paraOreza(o.o);
    if (para) { gracz.zloto -= cena; o.kupiona = true; para.tier++; toast('⬆️ Połączono: ' + nazwaOreza(para)); poZmianieBuildu(); DZ.wybor(); pokazSklep(true); return; }
    if (gracz.oreze.length < gracz.slotyOreza) { gracz.zloto -= cena; o.kupiona = true; gracz.oreze.push(o.o); poZmianieBuildu(); DZ.zakup(); pokazSklep(true); return; }
    if (!gracz.oreze.length) { toast('Ta postać nie ma miejsc na bronie dodatkowe'); return; }
    wyborZamianyOreza(o.o, () => { gracz.zloto -= cena; o.kupiona = true; pokazSklep(true); });
    return;
  }
  if (o.rodzaj === 'pancerz') {
    const slot = DEF_PANC[o.p.id].slot, ob = gracz.pancerz[slot];
    gracz.zloto -= cena; o.kupiona = true; if (ob) gracz.zloto += Math.round(cenaPancerza(ob) * 0.5);
    gracz.pancerz[slot] = o.p; poZmianieBuildu(); DZ.zakup(); pokazSklep(true); return;
  }
  const inst = nowyPrzedmiot(o.id); if (o.gw) inst.gw = o.gw;
  gracz.zloto -= cena; o.kupiona = true;
  dodajPrzedmiotZWyborem(inst, () => { DZ.zakup(); pokazSklep(true); });
};
function pokazKowadloZeSklepu() { run.przerwa.wrocDoSklepu = true; pokazKowadlo(); }
AKCJE.dalejZeSklepu = () => { run.przerwa.sklep = true; zapiszGre(); kolejkaPrzerwy(); };
// ---- zarządzanie buildem: ulepszanie i sprzedaż (sklep i 🎒 Build między falami) ----
AKCJE.ulepszPrz = d => { const p = gracz.przedmioty[+d.i]; if (!p || (DEF_PRZ[p.id].t === 'p' && !KLASY[gracz.klasa].ulepszaPryzmaty) || (p.gw || 0) >= MAKS_GWIAZDEK) return; const c = cenaUlepszenia(p); if (gracz.zloto < c) return; gracz.zloto -= c; p.gw = (p.gw || 0) + 1; poZmianieBuildu(); DZ.wybor(); odswiezEkranPrzerwy(); };
AKCJE.sprzedajPrz = d => { const i = +d.i, p = gracz.przedmioty[i]; if (!p) return; if (d.pewne) { run._zBuildu = !!modalEl.dataset.zBuildu; AKCJE.sprzedajPrzTak(d); return; } run._zBuildu = !!modalEl.dataset.build; pokazModal('<div class="tytul">Sprzedać?</div>' + kartaPrzedmiotu(p, '', { bezOpisu: true }) + '<button class="btn czerw" data-a="sprzedajPrzTak" data-i="' + i + '">Sprzedaj za ' + wartoscSprzedazy(p) + ' 💰</button><button class="btn drugi" data-a="zamknijModal">Anuluj</button>'); };
AKCJE.sprzedajPrzTak = d => { const i = +d.i, p = gracz.przedmioty[i]; if (!p) return; gracz.zloto += wartoscSprzedazy(p); cofnijPrzedmiot(p); gracz.przedmioty.splice(i, 1); zamknijModal(); poZmianieBuildu(); DZ.moneta(); toast('💰 Sprzedano'); if (run._zBuildu) { run._zBuildu = false; AKCJE.modalBuild(); } odswiezEkranPrzerwy(); };
AKCJE.zamknijModal = () => { const zb = run && run._zBuildu; if (run) run._zBuildu = false; zamknijModal(); if (zb) AKCJE.modalBuild(); };
function cofnijPrzedmiot(p) { const d = p && DEF_PRZ[p.id]; if (d && d.cofnij) { try { d.cofnij(); } catch (e) { zglosBlad(e, 'cofnij ' + p.id); } } }
function cenaMistrzostwa(b) { return Math.round(CENY_MISTRZOSTWA[b.mistrz || 0] * mnCeny() * (1 - (KLASY[gracz.klasa].rabatBroni || 0))); }
AKCJE.mistrzostwo = d => {
  const b = gracz.bronie[+d.i]; if (!b || (b.mistrz || 0) >= MAKS_MISTRZOSTWA || gracz.zloto < cenaMistrzostwa(b)) return;
  const wolne = Object.keys(PERKI_MISTRZA).filter(p => !(b.perki || []).includes(p) && !(p === 'pociski' && !BRONIE[b.rodzaj].dystans));
  run.ofertaPerkow = tasuj(wolne).slice(0, 3); run.perkBron = +d.i;
  let h = '<div class="tytul">🏆 Mistrzostwo ' + rzymskaM((b.mistrz || 0) + 1) + '</div><div class="podtytul">' + BRONIE[b.rodzaj].ikona + ' ' + BRONIE[b.rodzaj].nazwa + ' dostaje <b>+15% obrażeń</b> i wybraną cechę. Koszt: <b class="zl">' + cenaMistrzostwa(b) + ' 💰</b></div>';
  run.ofertaPerkow.forEach(p => { const P = PERKI_MISTRZA[p]; h += '<div class="kafel karta wybieralna" data-a="perkWybierz" data-p="' + p + '" style="margin-bottom:8px;text-align:left"><div class="ik">' + P.ik + '</div><div class="n">' + P.n + '</div><div class="o">' + P.o + '</div></div>'; });
  pokazModal(h + '<button class="btn drugi" data-a="zamknijModal">Anuluj</button>');
};
AKCJE.perkWybierz = d => {
  const b = gracz.bronie[run.perkBron]; if (!b || !PERKI_MISTRZA[d.p]) return; const c = cenaMistrzostwa(b); if (gracz.zloto < c) return;
  gracz.zloto -= c; b.mistrz = (b.mistrz || 0) + 1; b.perki = (b.perki || []).concat([d.p]); run.ofertaPerkow = null;
  poZmianieBuildu(); DZ.pryzmat(); toast('🏆 ' + PERKI_MISTRZA[d.p].ik + ' ' + PERKI_MISTRZA[d.p].n); zamknijModal(); odswiezEkranPrzerwy();
};
AKCJE.ulepszGlowna = d => { const b = gracz.bronie[+d.i]; if (!b || b.tier >= MAKS_TIER_BRONI) return; const c = cenaUlepszeniaBroniGl(b); if (gracz.zloto < c) return; gracz.zloto -= c; b.tier++; poZmianieBuildu(); DZ.pryzmat(); toast('⬆️ ' + nazwaBroni(b)); odswiezEkranPrzerwy(); };
AKCJE.polaczOreze = d => { const i = +d.i, o = gracz.oreze[i]; if (!o) return; const j = gracz.oreze.findIndex((x, k) => k !== i && x.id === o.id && x.tier === o.tier); if (j < 0 || o.tier >= 3) return; o.tier++; gracz.oreze.splice(j, 1); poZmianieBuildu(); DZ.wybor(); toast('⬆️ ' + nazwaOreza(o)); odswiezEkranPrzerwy(); };
AKCJE.ulepszOreze = d => { const o = gracz.oreze[+d.i]; if (!o || o.tier >= 3) return; const c = cenaUlepszeniaOreza(o); if (gracz.zloto < c) return; gracz.zloto -= c; o.tier++; poZmianieBuildu(); DZ.wybor(); odswiezEkranPrzerwy(); };
AKCJE.sprzedajOreze = d => { const i = +d.i, o = gracz.oreze[i]; if (!o) return; gracz.zloto += wartoscSprzedazyOreza(o); gracz.oreze.splice(i, 1); poZmianieBuildu(); DZ.moneta(); toast('💰 Sprzedano: ' + DEF_ORE[o.id].n); odswiezEkranPrzerwy(); };
AKCJE.sprzedajPanc = d => { const p = gracz.pancerz[d.s]; if (!p) return; gracz.zloto += Math.round(cenaPancerza(p) * 0.5); gracz.pancerz[d.s] = null; poZmianieBuildu(); DZ.moneta(); odswiezEkranPrzerwy(); };
function odswiezEkranPrzerwy() {
  if (modalEl.classList.contains('widoczny') && modalEl.dataset.szczegol) {
    const [r, i] = modalEl.dataset.szczegol.split(':');
    if (elementBuildu(r, i)) pokazSzczegol(r, i, true);
    else if (modalEl.dataset.zBuildu) AKCJE.modalBuild(); else zamknijModal();
  } else if (modalEl.classList.contains('widoczny') && modalEl.dataset.build) { AKCJE.modalBuild(); }
  if (run.przerwa && run.przerwa.sklepOtwarty && !run.przerwa.sklep) pokazSklep(true);
  else if (stan === 'pauza') pokazEkwipunek(ekwZakladka);
}

// ---------------------------------------------------------------------
//  BUILD — zwarta siatka kafelków; dotknięcie kafelka otwiera szczegóły (opis, ulepszanie, sprzedaż)
// ---------------------------------------------------------------------
function elementBuildu(r, i) {
  i = r === 'panc' ? i : +i;
  if (r === 'glowna') return gracz.bronie[i];
  if (r === 'oreze') return gracz.oreze[i];
  if (r === 'przedm') return gracz.przedmioty[i];
  if (r === 'panc') return gracz.pancerz[i];
  if (r === 'aug') return gracz.augmenty[i];
  return null;
}
function kafelek(r, i, ik, nazwa, kol, znak, cd, odznaka, klasa) {
  return '<div class="kfl' + (klasa ? ' ' + klasa : '') + '" data-a="szczegol" data-r="' + r + '" data-i="' + i + '" style="--kol:' + kol + '" title="' + esc(nazwa) + '">' +
    '<div class="kfl-ik">' + ik + (znak ? '<span class="kfl-znak">' + znak + '</span>' : '') + (cd ? '<span class="kfl-cd">' + cd + '</span>' : '') + (odznaka ? '<span class="kfl-odz">' + odznaka + '</span>' : '') + '</div>' +
    '<div class="kfl-n">' + esc(nazwa) + '</div></div>';
}
function kafelekPusty(t) { return '<div class="kfl pusty"><div class="kfl-ik">＋</div><div class="kfl-n">' + t + '</div></div>'; }
function chipyStatow() {
  const ch = (ik, v, t) => '<span class="chip" title="' + t + '">' + ik + ' <b>' + v + '</b></span>';
  return '<div class="chipy">' + ch('❤️', D.hpMax, 'Maks. zdrowie') + ch('⚔️', f0(D.ad), 'Obrażenia od ataku') + ch('✨', f0(D.ap), 'Moc umiejętności') +
    ch('⚡', f0(D.as) + '%', 'Prędkość ataku') + ch('🎯', f0(D.kryt) + '%', 'Szansa na kryt') + ch('🛡️', f0(D.pancerz), 'Pancerz') + ch('🔰', f0(D.odpMag), 'Odporność na magię') +
    ch('💨', f0(Math.min(D.unik, FLAGI.unikMax || 80)) + '%', 'Unik') + ch('⏱️', f0(D.haste), 'Przyspieszenie') + ch('🦇', fmt(limitWampiryzmu() * 100) + '%/s', 'Limit wampiryzmu') + '</div>';
}
function sekcjeBuildu(zarzadzanie, op) {
  op = op || {};
  const z = gracz.zloto;
  let h = chipyStatow();
  // broń główna — szeroki kafelek (w sklepie obok niej przycisk ewolucji)
  h += '<div class="sekcja">⭐ Broń główna' + (op.ewo ? ' · 🧬 ewolucja' : '') + '</div>' + (op.ewo ? '<div class="sp-bron-ewo"><div>' : '');
  gracz.bronie.forEach((b, i) => {
    const B = BRONIE[b.rodzaj];
    const mozna = zarzadzanie && b.tier < MAKS_TIER_BRONI && z >= cenaUlepszeniaBroniGl(b);
    h += '<div class="kfl szeroki" data-a="szczegol" data-r="glowna" data-i="' + i + '" style="--kol:' + TIERY[b.tier].kolor + '"><div class="kfl-ik">' + B.ikona + (mozna ? '<span class="kfl-odz">⬆</span>' : '') + '</div>' +
      '<div style="flex:1;min-width:0"><div class="kfl-n" style="text-align:left;font-size:13px">' + B.nazwa + ' ' + TIERY[b.tier].rz + '</div>' +
      '<div class="kfl-op">' + f0(obrBroni(b)) + ' obrażeń na trafienie · co ' + fmt(odstepAtaku(b)) + ' s · ' + opisSkalowania(B) + '</div></div></div>';
  });
  if (op.ewo) h += '</div>' + op.ewo + '</div>';
  // bronie dodatkowe
  const zest = policzZestawy(), akt = Object.keys(zest).filter(t => zest[t] >= 2);
  h += '<div class="sekcja">🗡️ Bronie dodatkowe <span class="licz">' + gracz.oreze.length + '/' + gracz.slotyOreza + '</span></div><div class="kafelki">';
  gracz.oreze.forEach((o, i) => {
    const d = DEF_ORE[o.id], mozna = zarzadzanie && (paraOreza(o) || (o.tier < 3 && z >= cenaUlepszeniaOreza(o)));
    h += kafelek('oreze', i, d.ik, d.n + ' ' + TIERY[o.tier].rz, TIERY[o.tier].kolor, '', d.cd ? fmt(d.cd) + 's' : (d.co ? '×' + d.co : ''), mozna ? '⬆' : '', 'g-t' + o.tier);
  });
  for (let i = gracz.oreze.length; i < gracz.slotyOreza; i++) h += kafelekPusty('wolne');
  h += '</div>';
  if (akt.length) h += '<div class="chipy">' + akt.map(t => { const R = RODZINY[t]; return '<span class="chip">' + R.ik + ' ' + R.n + ' ×' + zest[t] + ': ' + opisStatow(R.staty(poziomZestawu(zest[t]))).replace(/<br>/g, ', ') + '</span>'; }).join('') + '</div>';
  // przedmioty zwykłe i pryzmatyczne — osobne miejsca
  [[false, '🎒 Przedmioty'], [true, '🔨 Pryzmaty']].forEach(([pr, tyt]) => {
    h += '<div class="sekcja">' + tyt + ' <span class="licz">' + liczPrzedm(pr) + '/' + slotyTypu(pr) + '</span></div><div class="kafelki">';
    gracz.przedmioty.forEach((p, i) => {
      if (!p || czyPryzmat(p) !== pr) return;
      const d = DEF_PRZ[p.id], mozna = zarzadzanie && (!pr || KLASY[gracz.klasa].ulepszaPryzmaty) && (p.gw || 0) < MAKS_GWIAZDEK && z >= cenaUlepszenia(p);
      h += kafelek('przedm', i, d.ik, d.n, pr ? KOLOR_PRYZMAT : TIERY[d.t].kolor, p.gw ? '★'.repeat(p.gw) : '', d.cd ? fmt(d.cd) + 's' : '', mozna ? '⬆' : '', pr ? 'pryzm g-p' : 'g-t' + d.t);
    });
    for (let i = liczPrzedm(pr); i < slotyTypu(pr); i++) h += kafelekPusty(pr ? 'z kowadła' : 'wolne');
    h += '</div>';
  });
  // pancerz
  h += '<div class="sekcja">🛡️ Pancerz</div><div class="kafelki">';
  SLOTY_PANCERZA.forEach(sl => {
    const p = gracz.pancerz[sl];
    if (p) { const d = DEF_PANC[p.id]; h += kafelek('panc', sl, d.ik, d.n, TIERY[p.tier].kolor, TIERY[p.tier].rz, '', '', 'g-t' + p.tier); }
    else h += kafelekPusty(IKONY_SLOTOW[sl] + ' ' + NAZWY_SLOTOW[sl]);
  });
  h += '</div>';
  // augmenty (w sklepie na komputerze - osobny pionowy pasek)
  if (!op.bezAug) {
    h += '<div class="sekcja">🧬 Augmenty <span class="licz">' + gracz.augmenty.length + '</span></div><div class="kafelki">';
    if (!gracz.augmenty.length) h += kafelekPusty('brak');
    gracz.augmenty.forEach((a, i) => {
      const d = DEF_AUG[a.id], T = TIERY_AUG[d.r], mozna = zarzadzanie && (a.poz || 1) < MAKS_POZ_AUG && z >= cenaUlepszeniaAug(a);
      h += kafelek('aug', i, d.ik, d.n, d.r === 'p' ? KOLOR_PRYZMAT : T.kolor, rzymska(a.poz || 1), '', mozna ? '⬆' : '', d.r === 'p' ? 'pryzm g-ap' : 'g-a' + d.r);
    });
    h += '</div>';
  }
  h += '<div class="podtytul" style="margin-top:6px;font-size:11px">' + (czySklepPC() ? 'Kliknij' : 'Dotknij') + ' kafelka, żeby zobaczyć opis' + (zarzadzanie ? ', ulepszyć albo sprzedać. ⬆ = stać Cię na ulepszenie.' : '.') + '</div>';
  return h;
}
function pokazSzczegol(r, i, zachowaj) {
  const el = elementBuildu(r, i); if (!el) return;
  const zarz = stan === 'przerwa', z = gracz.zloto;
  const zBuildu = zachowaj ? modalEl.dataset.zBuildu : (modalEl.classList.contains('widoczny') && modalEl.dataset.build ? '1' : '');
  let karta = '', dol = '';
  const bt = (a, t, kl, ok, ex) => '<button class="btn-maly ' + kl + '" data-a="' + a + '" data-i="' + i + '"' + (ex || '') + (ok === false ? ' disabled' : '') + '>' + t + '</button>';
  if (r === 'glowna') {
    if (zarz && el.tier < MAKS_TIER_BRONI) { const c = cenaUlepszeniaBroniGl(el); dol += bt('ulepszGlowna', '⬆️ Ulepsz do ' + TIERY[el.tier + 1].rz + ' (' + c + ' 💰)', 'zl', z >= c); }
    else if (zarz && KLASY[gracz.klasa].mistrzostwo && (el.mistrz || 0) < MAKS_MISTRZOSTWA) { const c = cenaMistrzostwa(el); dol += bt('mistrzostwo', '🏆 Mistrzostwo ' + rzymskaM((el.mistrz || 0) + 1) + ' (' + c + ' 💰)', 'zl', z >= c); }
    karta = kartaBroni(el, dol);
  } else if (r === 'oreze') {
    if (zarz) {
      if (paraOreza(el)) dol += bt('polaczOreze', '⬆️ Połącz', 'ziel');
      if (el.tier < 3) { const c = cenaUlepszeniaOreza(el); dol += bt('ulepszOreze', '⬆️ Ulepsz (' + c + ' 💰)', 'zl', z >= c); }
      dol += bt('sprzedajOreze', 'Sprzedaj +' + wartoscSprzedazyOreza(el) + ' 💰', 'czerw', true, ' style="margin-left:auto"');
    }
    karta = kartaOreza(el, dol);
  } else if (r === 'przedm') {
    if (zarz) {
      if ((!czyPryzmat(el) || KLASY[gracz.klasa].ulepszaPryzmaty) && (el.gw || 0) < MAKS_GWIAZDEK) { const c = cenaUlepszenia(el); dol += bt('ulepszPrz', '★ Ulepsz (' + c + ' 💰)', 'zl', z >= c); }
      dol += bt('sprzedajPrz', 'Sprzedaj +' + wartoscSprzedazy(el) + ' 💰', 'czerw', true, ' data-pewne="1" style="margin-left:auto"');
    }
    karta = kartaPrzedmiotu(el, dol);
  } else if (r === 'panc') {
    if (zarz) dol += '<button class="btn-maly czerw" data-a="sprzedajPanc" data-s="' + i + '" style="margin-left:auto">Sprzedaj +' + Math.round(cenaPancerza(el) * 0.5) + ' 💰</button>';
    karta = kartaPancerza(el, dol);
  } else if (r === 'aug') {
    if (zarz && (el.poz || 1) < MAKS_POZ_AUG) { const c = cenaUlepszeniaAug(el); dol += bt('ulepszAug', '⬆️ Ulepsz do ' + rzymska((el.poz || 1) + 1) + ' (' + c + ' 💰)', 'zl', z >= c); }
    karta = kartaAugmentu(DEF_AUG[el.id], dol, el);
  }
  pokazModal(karta + '<button class="btn drugi" data-a="szczegolWroc">◀ Wróć</button>', zachowaj);
  modalEl.dataset.szczegol = r + ':' + i;
  if (zBuildu) modalEl.dataset.zBuildu = '1';
}
AKCJE.szczegol = d => pokazSzczegol(d.r, d.i);
AKCJE.szczegolWroc = () => { const zb = modalEl.dataset.zBuildu; zamknijModal(); if (zb) AKCJE.modalBuild(); };

// ---------------------------------------------------------------------
//  PRÓBY
// ---------------------------------------------------------------------
function pokazProby() {
  if (!run.ofertaProb) run.ofertaProb = tasuj(PROBY.filter(p => !p.warunek || p.warunek()).map(p => p.id)).slice(0, 2);
  let h = pasekGorny() + '<div class="tytul">⚖️ Próba</div><div class="podtytul">Przed falą <b>' + (fala.nr + 1) + '</b> możesz przyjąć jedno utrudnienie. Jeśli przetrwasz (i spełnisz warunek) — dostajesz nagrodę.</div>' +
    (druzyna() ? '<div class="info-pole">👥 Próbę wybierasz dla <b>całej drużyny</b>. Nagrodę dostaje każdy, kto skończy falę na nogach.</div>' : '');
  run.ofertaProb.forEach(id => {
    const p = DEF_PROB[id];
    h += '<div class="karta az wybieralna" data-pad="probaWybierz" data-padn="podejmij" data-klik="1"><div class="karta-gora"><div class="karta-ik">' + p.ik + '</div><div><div class="karta-nazwa">' + p.n + '</div></div></div>' +
      '<div class="karta-opis"><span class="czer">Utrudnienie:</span> ' + p.opis + '<br><span class="ziel">Nagroda:</span> ' + p.nagroda + '</div>' +
      '<div class="karta-dol"><button class="btn-maly zl" data-a="probaWybierz" data-id="' + id + '" style="margin-left:auto">Podejmuję próbę</button></div></div>';
  });
  h += '<button class="btn drugi" data-a="probaOdmow">Bez próby — zwykła fala</button>';
  pokazEkran(h);
}
AKCJE.probaWybierz = d => { run.wybranaProba = d.id; run.ofertaProb = null; DZ.wybor(); kolejkaPrzerwy(); };
AKCJE.probaOdmow = () => { run.ofertaProb = null; kolejkaPrzerwy(); };
function pokazWynikProby(w) {
  const p = DEF_PROB[w.id];
  pokazEkran(pasekGorny() + '<div class="tytul">' + p.ik + ' ' + p.n + '</div>' +
    '<div class="karta ' + (w.ok ? 'az' : 't0') + '" style="text-align:center"><div style="font-size:46px">' + (w.ok ? '🏅' : '❌') + '</div>' +
    '<div class="karta-nazwa">' + (w.ok ? 'Próba zaliczona!' : 'Próba nieudana') + '</div><div class="karta-opis">' + (w.ok ? 'Nagroda: ' + p.nagroda : 'Tym razem bez nagrody.') + '</div></div>' +
    '<button class="btn" data-a="dalejPrzerwa">Dalej</button>');
}
AKCJE.dalejPrzerwa = () => kolejkaPrzerwy();

// ---------------------------------------------------------------------
//  EKWIPUNEK W TRAKCIE FALI (pauza) i MODALE
// ---------------------------------------------------------------------
let ekwZakladka = 'staty';
function htmlStatow() {
  let h = '';
  const grupy = { atak: '⚔️ Atak', obrona: '🛡️ Obrona', onhit: '🎯 On-hit (przy trafieniu)', uzyt: '🧰 Użytkowe' };
  Object.keys(grupy).forEach(g => {
    h += '<div class="sekcja">' + grupy[g] + '</div>';
    DEF_STATOW.filter(d => d.g === g).forEach(d => {
      const v = D[d.k], zero = Math.abs(v) < 0.001 && !d.baza;
      h += '<div class="wiersz-stat" data-a="opisStatu" data-k="' + d.k + '"><span class="ik">' + d.i + '</span><span class="n">' + d.n + '</span><span class="v' + (zero ? ' zero' : '') + '">' + wartoscStatuTekst(d.k, v) + '</span></div>';
    });
  });
  h += '<div class="info-pole">Zdrowie: <b>' + Math.round(gracz.hp) + ' / ' + D.hpMax + '</b> · Poziom <b>' + gracz.poziom + '</b><br>Redukcja: fizyczne <b>−' + Math.round(100 - 100 * 100 / (100 + Math.max(0, D.pancerz))) + '%</b>, magiczne <b>−' + Math.round(100 - 100 * 100 / (100 + Math.max(0, D.odpMag))) + '%</b>' +
    '<br>💗 Regeneracja: <b>' + fmt(regenNaSekunde()) + ' zdrowia/s</b>' +
    '<br>🦇 Limit wampiryzmu: <b>' + fmt(limitWampiryzmu() * 100) + '% zdrowia/s</b> (' + Math.round(limitWampiryzmu() * D.hpMax) + '/s)' +
    (zmeczenie(fala.nr) > 0 ? '<br>🥀 Zmęczenie: leczenie <b>−' + Math.round(zmeczenie(fala.nr) * 100) + '%</b> (regeneracji nie dotyczy)' : '') + '</div>';
  return h;
}
AKCJE.opisStatu = d => toast(STAT[d.k].i + ' ' + STAT[d.k].n + ': ' + STAT[d.k].o);
function htmlObrazen() {
  const lista = Object.keys(run.zrodla).map(k => [k, run.zrodla[k]]).sort((a, b) => b[1] - a[1]);
  const max = lista.length ? lista[0][1] : 1, suma = lista.reduce((s, x) => s + x[1], 0) || 1;
  let h = '<div class="sekcja">💥 Źródła obrażeń (cała gra)</div>';
  if (!lista.length) h += '<div class="slot-pusty">Jeszcze nic</div>';
  lista.slice(0, 25).forEach(([k, v]) => {
    h += '<div style="margin-bottom:7px"><div style="display:flex;justify-content:space-between;font-size:12px;font-weight:700"><span>' + esc(k) + '</span><span style="color:#ffe08a">' + fmtK(v) + ' · ' + Math.round(v / suma * 100) + '%</span></div>' +
      '<div style="background:rgba(255,255,255,0.06);border-radius:4px"><div class="wykres-pas" style="width:' + Math.max(2, v / max * 100) + '%"></div></div></div>';
  });
  h += '<div class="info-pole">Zabici: <b>' + run.zabici + '</b> · Zadane: <b>' + fmtK(run.zadane) + '</b> · Przyjęte: <b>' + fmtK(run.przyjete) + '</b> · Leczenie: <b>' + fmtK(run.leczenie) + '</b> · Złoto: <b>' + fmtK(run.zloto) + '</b></div>';
  return h;
}
function pokazEkwipunek(zak) {
  ekwZakladka = zak || 'staty';
  let h = '<div class="tytul">' + (druzyna() ? '🎒 Podgląd (gra trwa!)' : '⏸️ Pauza') + '</div><div class="podtytul">🌊 Fala ' + fala.nr + (fala.aktywna && !fala.boss ? ' · zostało ' + czas(fala.dlugosc - fala.czas) : '') + ' · 💰 ' + Math.floor(gracz.zloto) + '</div>';
  h += '<button class="btn ziel" data-a="wznow">▶ Wróć do walki</button>';
  h += '<div class="zakladki">' + [['postac', KLASY[gracz.klasa].ik + ' Postać'], ['staty', '📊 Staty'], ['build', '🎒 Build'], ['obr', '💥 Obrażenia']].map(z => '<button class="' + (z[0] === ekwZakladka ? 'akt' : '') + '" data-a="ekwZak" data-z="' + z[0] + '">' + z[1] + '</button>').join('') + '</div>';
  if (ekwZakladka === 'staty') h += htmlStatow();
  else if (ekwZakladka === 'postac') h += htmlPostaci(false);
  else if (ekwZakladka === 'build') h += sekcjeBuildu(false);
  else h += htmlObrazen();
  h += '<div class="rzad-btn" style="margin-top:16px"><button class="btn drugi" data-a="ustawienia">⚙️ Ustawienia</button><button class="btn drugi" data-a="sterowanie">🎮 Sterowanie</button></div>' + przyciskPelnego();
  if (!druzyna()) h += '<button class="btn czerw" data-a="poddaj" style="margin-top:6px">🏳️ Zakończ tę grę</button>';
  else h += '<button class="btn czerw" data-a="opuscDruzyne" style="margin-top:6px">🚪 Opuść drużynę</button>';
  pokazEkran(h, { polprzezroczysty: true });
}
AKCJE.ekwZak = d => pokazEkwipunek(d.z);
AKCJE.wznow = () => { zamknijEkran(); if (stan === 'pauza') stan = 'walka'; czasOstatni = null; };
AKCJE.poddaj = () => pokazModal('<div class="tytul">Zakończyć grę?</div><div class="podtytul">Twój wynik zostanie zapisany, a zapis gry usunięty.</div><button class="btn czerw" data-a="poddajTak">Tak, kończę</button><button class="btn drugi" data-a="zamknijModal">Graj dalej</button>');
AKCJE.poddajTak = () => { zamknijModal(); zamknijEkran(); stan = 'walka'; smiercGracza(true); };
AKCJE.modalPostac = () => pokazModal(htmlPostaci(true) + '<button class="btn" data-a="zamknijModal">Zamknij</button>');
AKCJE.modalStaty = () => pokazModal('<div class="tytul">📊 Statystyki</div>' + htmlStatow() + '<button class="btn" data-a="zamknijModal">Zamknij</button>');
AKCJE.modalBuild = () => {
  const zarz = stan === 'przerwa' && !(run.przerwa && run.przerwa.sklepOtwarty && !run.przerwa.sklep);   // w sklepie zarządza się na dole sklepu
  const otwarty = modalEl.classList.contains('widoczny') && modalEl.dataset.build;
  pokazModal('<div class="tytul">🎒 Twój build</div>' + (zarz ? '<div class="podtytul">Tu możesz sprzedawać i ulepszać — także przed sklepem.</div>' : '') + sekcjeBuildu(stan === 'przerwa') + '<button class="btn" data-a="zamknijModal">Zamknij</button>', otwarty);
  modalEl.dataset.build = '1';
};

$('btnEkw').addEventListener('click', () => {
  if (druzyna()) { if (ekranEl.classList.contains('widoczny')) { zamknijEkran(); } else if (stan === 'walka') pokazEkwipunek('staty'); return; }
  if (stan === 'walka') { stan = 'pauza'; pokazEkwipunek('staty'); }
  else if (stan === 'pauza') AKCJE.wznow();
});
// Przyciski umiejętności: na dotyku działają od razu przy dotknięciu (pointerdown), także DRUGIM palcem
// w trakcie ruchu drążkiem — przeglądarki nie wysyłają „click” dla drugiego palca.
function przelaczAuto(nr) {
  const ja = lokalny || gracz; if (!ja) return; const z0 = gracz; kontekst(ja);
  const U = umiPostaci(nr); if (U && !U.pasywna && !U.przelacz && !U.auto) { ja.autoUmi = ja.autoUmi || {}; ja.autoUmi[nr] = !ja.autoUmi[nr]; toast('🤖 ' + U.ik + ' ' + U.n + ': auto ' + (ja.autoUmi[nr] ? 'wł.' : 'wył.')); }
  kontekst(z0); odswiezHud(true);
}
function przyciskWalki(id, nr) {
  const el = $(id); let ostDotyk = -1e9, tPrzytrz = null;
  const pusc = () => { if (tPrzytrz) { clearTimeout(tPrzytrz); tPrzytrz = null; } };
  el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse') return;
    e.preventDefault(); e.stopPropagation(); ostDotyk = performance.now(); inicjujDzwiek(); uzyjUmiejetnosci(nr);
    el.classList.add('wcisniety'); setTimeout(() => el.classList.remove('wcisniety'), 140);
    pusc(); tPrzytrz = setTimeout(() => { tPrzytrz = null; przelaczAuto(nr); if (navigator.vibrate) try { navigator.vibrate(30); } catch (x) {} }, 550);
  });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(ev => el.addEventListener(ev, pusc));
  el.addEventListener('click', () => { if (performance.now() - ostDotyk < 800) return; uzyjUmiejetnosci(nr); });
  el.addEventListener('contextmenu', e => { e.preventDefault(); przelaczAuto(nr); });   // myszka: prawy przycisk na przycisku = auto
}
przyciskWalki('btnUmi', 1);
przyciskWalki('btnUmi2', 2);

// ---------------------------------------------------------------------
//  ŚMIERĆ
// ---------------------------------------------------------------------
function smiercGracza(poddanie) {
  if (gracz.martwy) return;
  gracz.martwy = true; gracz.hp = 0; stan = 'smierc';
  DZ.smierc();
  const rek = lStorGet('wiezien_rekordy', {}), r = rek[run.trudnosc];
  const nowyRekord = !r || fala.nr > r.fala;
  if (nowyRekord) { rek[run.trudnosc] = { fala: fala.nr, klasa: gracz.klasa, poziom: gracz.poziom, data: Date.now() }; lStorSet('wiezien_rekordy', rek); }
  const rk = lStorGet('wiezien_rekordy_klas', {}); if (!rk[gracz.klasa] || fala.nr > rk[gracz.klasa]) { rk[gracz.klasa] = fala.nr; lStorSet('wiezien_rekordy_klas', rk); }
  lStorDel('wiezien_zapis');
  setTimeout(() => pokazSmierc(nowyRekord, poddanie), poddanie ? 50 : 1300);
}
function pokazSmierc(nowyRekord, poddanie) {
  const T = TRUDNOSCI[run.trudnosc], K = KLASY[gracz.klasa];
  const min = Math.round((Date.now() - run.start) / 60000);
  let h = '<div class="tytul duzy" style="margin-top:8px">' + (poddanie ? '🏳️ Koniec' : '💀 Koniec wędrówki') + '</div>' +
    '<div class="podtytul">' + K.ik + ' ' + K.n + ' · ' + T.ik + ' ' + T.n + '</div>' +
    '<div class="karta az" style="text-align:center"><div style="font-size:15px;color:#d8cdb0">Twoja ostatnia fala</div><div style="font-size:54px;font-weight:900;color:#ffe08a;line-height:1.1">' + fala.nr + '</div>' +
    (nowyRekord ? '<div class="ziel">🏆 Nowy rekord!</div>' : '') + '</div>' +
    '<div class="info-pole">⭐ Poziom <b>' + gracz.poziom + '</b> · ⚔️ Zabici <b>' + run.zabici + '</b> · ⏱️ <b>' + min + ' min</b><br>💥 Zadane <b>' + fmtK(run.zadane) + '</b> · 🩸 Przyjęte <b>' + fmtK(run.przyjete) + '</b> · 💞 Leczenie <b>' + fmtK(run.leczenie) + '</b><br>💰 Zebrane złoto <b>' + fmtK(run.zloto) + '</b> · ⚖️ Próby zaliczone <b>' + (run.probyZaliczone || 0) + '</b></div>';
  h += htmlObrazen().replace('<div class="info-pole">', '<div class="info-pole" style="display:none">');
  h += '<div class="sekcja">Twój build</div><div class="lista-mini">';
  gracz.bronie.forEach(b => h += '<div class="mini" style="border-color:' + TIERY[b.tier].kolor + ';background:rgba(90,60,30,0.5)">' + BRONIE[b.rodzaj].ikona + '</div>');
  gracz.oreze.forEach(o => h += '<div class="mini" style="border-color:' + TIERY[o.tier].kolor + '">' + DEF_ORE[o.id].ik + '</div>');
  gracz.przedmioty.forEach(p => { if (p) { const d = DEF_PRZ[p.id]; h += '<div class="mini" style="border-color:' + (d.t === 'p' ? KOLOR_PRYZMAT : TIERY[d.t].kolor) + '">' + d.ik + (p.gw ? '<span class="gw">' + gwiazdki(p.gw) + '</span>' : '') + '</div>'; } });
  gracz.augmenty.forEach(a => h += '<div class="mini" style="border-color:' + TIERY_AUG[DEF_AUG[a.id].r].kolor + '">' + DEF_AUG[a.id].ik + '</div>');
  h += '</div><button class="btn" data-a="znowu" style="margin-top:16px">↺ Jeszcze raz</button><button class="btn drugi" data-a="menu">◀ Menu</button>';
  pokazEkran(h);
}
AKCJE.znowu = () => { const t = run.trudnosc, k = gracz.klasa; wyborTrudnosci = t; wyborKlasy = k; pokazPostacie(); };

// ---------------------------------------------------------------------
//  KODEKS
// ---------------------------------------------------------------------
let kodeksZak = 'postacie';
AKCJE.kodeks = () => { kodeksZak = 'postacie'; pokazKodeks(); };
AKCJE.kodZak = d => { kodeksZak = d.z; pokazKodeks(); };
function pokazKodeks() {
  wKontekscie(() => {
    let h = '<div class="tytul">📖 Kodeks</div><div class="zakladki" style="flex-wrap:wrap">' +
      [['postacie', '👤 Postacie'], ['glowne', '⭐ Bronie główne'], ['oreze', '🗡️ Bronie'], ['przedmioty', '🎒 Przedmioty'], ['pryzmaty', '🔨 Pryzmaty'], ['augmenty', '🧬 Augmenty'], ['wrogowie', '👹 Wrogowie']]
        .map(z => '<button style="flex:1 0 30%" class="' + (z[0] === kodeksZak ? 'akt' : '') + '" data-a="kodZak" data-z="' + z[0] + '">' + z[1] + '</button>').join('') + '</div>';
    if (kodeksZak === 'postacie') KLUCZE_KLAS.forEach(k => { h += '<div class="info-pole">' + opisKlasyHtml(KLASY[k]) + '</div>'; });
    if (kodeksZak === 'glowne') { h += '<div class="podtytul">Każda postać ma swoją broń główną. W sklepie ulepszasz ją do tieru V.</div>'; KLUCZE_RODZIN.forEach(r => { h += '<div class="sekcja">' + RODZINY[r].ik + ' ' + RODZINY[r].n + '</div>'; KLUCZE_BRONI.filter(k => BRONIE[k].rodz === r).forEach(k => h += kartaBroni({ rodzaj: k, tier: 0 })); }); }
    if (kodeksZak === 'oreze') {
      h += '<div class="podtytul">Bronie dodatkowe dają statystyki i same coś odpalają. Tier I–IV.</div>';
      KLUCZE_RODZIN.forEach(r => { h += '<div class="sekcja">' + RODZINY[r].ik + ' ' + RODZINY[r].n + ' — zestaw (2/3/4/5/6): ' + RODZINY[r].opis + '</div>'; OREZE.filter(o => o.rodz === r).forEach(o => h += kartaOreza(nowyOrez(o.id, 0))); });
    }
    if (kodeksZak === 'przedmioty') [0, 1, 2, 3].forEach(t => { h += '<div class="sekcja kol-t' + t + '">' + TIERY[t].nazwa + ' (' + PRZEDMIOTY.filter(p => p.t === t).length + ')</div>'; PRZEDMIOTY.filter(p => p.t === t).forEach(p => h += kartaPrzedmiotu(nowyPrzedmiot(p.id))); });
    if (kodeksZak === 'pryzmaty') { h += '<div class="podtytul">Tylko z Pryzmatycznego Kowadła. Nie da się ich ulepszać.</div>'; PRYZMATY.forEach(p => h += kartaPrzedmiotu(nowyPrzedmiot(p.id))); }
    if (kodeksZak === 'augmenty') ['s', 'z', 'p'].forEach(r => { h += '<div class="sekcja">' + TIERY_AUG[r].nazwa.replace(' augment', 'e augmenty') + '</div>'; AUGMENTY.filter(a => a.r === r).forEach(a => h += kartaAugmentu(a, '', { id: a.id, poz: 1 })); });
    if (kodeksZak === 'wrogowie') {
      Object.keys(TYPY_WROGOW).forEach(k => { const t = TYPY_WROGOW[k], od = PULA_WROGOW.find(p => p[1] === k); h += '<div class="wiersz-stat"><span class="ik">' + t.ik + '</span><span class="n">' + t.n + (od ? ' <small style="opacity:0.6">od fali ' + od[0] + '</small>' : '') + '</span><span class="v" style="font-size:11px">' + t.hp + ' ❤️ · ' + t.atak + ' ⚔️</span></div>' + (t.opis ? '<div class="podtytul" style="text-align:left;margin:-2px 0 6px 38px;font-size:11px">' + t.opis + '</div>' : ''); });
      h += '<div class="sekcja">Bossowie</div>'; BOSSOWIE.forEach((b, i) => h += '<div class="wiersz-stat"><span class="ik">' + b.ik + '</span><span class="n">' + b.n + '</span><span class="v" style="font-size:11px">fala ' + (i + 1) * 5 + '</span></div>');
      h += '<div class="sekcja">Afiksy elit</div>'; Object.keys(AFIKSY).forEach(a => h += '<span class="tag">' + AFIKSY[a].ik + ' ' + AFIKSY[a].n + '</span>');
    }
    h += '<button class="btn" data-a="menu" style="margin-top:14px">◀ Menu</button>';
    pokazEkran(h, { zachowaj: false });
  });
}

// ---------------------------------------------------------------------
//  HUD
// ---------------------------------------------------------------------
let ostHud = 0;
function odswiezWidocznosc() {
  const wGrze = !!gracz && (stan === 'walka' || stan === 'pauza');
  if (odswiezWidocznosc._o === wGrze) return; odswiezWidocznosc._o = wGrze;
  $('hud').style.display = wGrze ? '' : 'none';
  $('pasSterowania').style.visibility = wGrze ? 'visible' : 'hidden';
}
function odswiezHud(wymus) {
  odswiezWidocznosc();
  if (!gracz || !D) return;
  const t = performance.now(); if (!wymus && t - ostHud < 90) return; ostHud = t;
  const hp = Math.max(0, gracz.hp), ts = tarczaSuma();
  $('hpWyp').style.width = (hp / D.hpMax * 100) + '%';
  $('tarczaWyp').style.width = Math.min(100, ts / D.hpMax * 100) + '%';
  $('hpNapis').textContent = '❤️ ' + Math.ceil(hp) + ' / ' + D.hpMax + (ts > 0 ? '  🛡 ' + Math.round(ts) : '');
  $('xpWyp').style.width = (gracz.xp / gracz.xpNast * 100) + '%';
  $('xpNapis').textContent = 'Poziom ' + gracz.poziom + (gracz.doWyboru ? '  ⭐×' + gracz.doWyboru : '');
  $('falaInfo').innerHTML = (fala.boss ? '👑' : '🌊') + ' Fala ' + fala.nr + '<small>' + (fala.boss ? 'BOSS' : czas(fala.dlugosc - fala.czas)) + (fala.specjalna && SPECJALNE[fala.specjalna] ? ' · ' + SPECJALNE[fala.specjalna].ik : '') + (fala.proba ? ' · ' + fala.proba.ik : '') + (zmeczenie(fala.nr) > 0 ? ' · 🥀−' + Math.round(zmeczenie(fala.nr) * 100) + '%' : '') + '</small>';
  $('zlotoInfo').textContent = '💰 ' + Math.floor(gracz.zloto) + (gracz.skrzynie.length ? '  📦' + gracz.skrzynie.length : '');
  // umiejętności postaci (druga tylko u niektórych)
  [[1, 'btnUmi', 'umiIk', 'umiCd', 'umiCzas'], [2, 'btnUmi2', 'umi2Ik', 'umi2Cd', 'umi2Czas']].forEach(([nr, idB, idI, idC, idT]) => {
    const U = umiPostaci(nr), bu = $(idB); if (!bu) return;
    bu.style.display = U ? '' : 'none';
    if (!U) return;
    if (bu._k !== gracz.klasa) { bu._k = gracz.klasa; $(idI).textContent = U.ik; bu.title = U.n + (U.pasywna ? '' : ' · przytrzymaj: auto-użycie'); }
    bu.classList.toggle('auto', !!(U.auto || (gracz.autoUmi && gracz.autoUmi[nr])));
    if (U.pasywna) {   // np. Salwa Elfa: przycisk pokazuje energię
      const en = gracz.maEnergie ? (gracz.energia || 0) : 0, akt = SIEC.rola === 'klient' ? !!(SIEC.mojWidok && SIEC.mojWidok.salwaAkt) : !!(gracz.stanKlasy && gracz.stanKlasy.salwa > czasGry);
      $(idC).style.setProperty('--p', (akt ? 0 : 100 - en) + '%'); $(idT).textContent = akt ? '' : (en < 100 ? Math.floor(en) + '%' : '');
      bu.classList.toggle('gotowa', en >= 100 || !!akt); bu.classList.toggle('wlaczona', !!akt); return;
    }
    const u = stanUmi(nr), gotowa = !(u.cd > 0), akt = czyUmiAktywna(nr);
    $(idC).style.setProperty('--p', (gotowa || U.przelacz ? 0 : Math.min(100, u.cd / Math.max(0.1, u.cdMax) * 100)) + '%');
    $(idT).textContent = gotowa || U.przelacz ? '' : Math.ceil(u.cd);
    bu.classList.toggle('gotowa', gotowa && !gracz.powalony && !akt);
    bu.classList.toggle('wlaczona', akt);
  });
  // pasek broni dodatkowych i przedmiotów z odnowieniem
  const pasek = $('pasekPrzedm');
  const elem = gracz.oreze.map(o => ({ i: o, d: DEF_ORE[o.id], kol: TIERY[o.tier].kolor, st: '', tk: 't' + o.tier }))
    .concat(gracz.przedmioty.filter(p => p).map(p => { const d = DEF_PRZ[p.id]; return { i: p, d: d, kol: d.t === 'p' ? KOLOR_PRYZMAT : TIERY[d.t].kolor, st: p.gw ? p.gw + '★' : '', tk: d.t === 'p' ? 'tp' : 't' + d.t }; }));
  const sygn = elem.map(e => e.d.id + (e.i.tier || 0) + (e.i.gw || 0)).join(',');
  if (pasek._sygn !== sygn) {
    pasek._sygn = sygn;
    pasek.innerHTML = elem.map(e => '<div class="hud-slot ' + e.tk + '" title="' + esc(e.d.n) + (e.d.cd ? ' · ⏱️ ' + fmt(e.d.cd) + ' s' : '') + '" style="border-color:' + e.kol + '"><span class="ik">' + e.d.ik + '</span><div class="cd"></div><div class="cdn"></div>' + (e.st ? '<span class="st">' + e.st + '</span>' : '') + '</div>').join('');
  }
  const sloty = pasek.children;
  elem.forEach((e, i) => {
    const el = sloty[i]; if (!el) return;
    const p = e.i, proc = p.cd > 0 && p.cdMax ? p.cd / p.cdMax * 100 : 0;
    el.children[1].style.setProperty('--p', proc + '%');
    el.children[2].textContent = p.cd > 0.95 ? Math.ceil(p.cd) : '';
    el.classList.toggle('gotowy', !!e.d.cd && !(p.cd > 0));
  });
}

// =====================================================================
//  ODZNAKI TIERÓW: szlifowane kamienie rysowane przez grę (jednakowe na
//  każdym urządzeniu). Im wyższy tier, tym więcej szlifów i mocniejszy blask:
//  I szary okrągły · II niebieski romb · III fioletowy sześciokąt ·
//  IV złoty ośmiokąt · V czerwona gwiazda · pryzmat: tęczowy trójkąt.
//  Augmenty: kryształy (szary, złoty, tęczowy).
// =====================================================================
const ODZNAKI = {};
function wielokat(n, r, obrot, sx, sy) { const p = []; for (let i = 0; i < n; i++) { const a = obrot + i * Math.PI * 2 / n; p.push([Math.cos(a) * r * (sx || 1), Math.sin(a) * r * (sy || 1)]); } return p; }
function mieszaj(rgb, cel, t) { return 'rgb(' + rgb.map((v, i) => Math.round(v + (cel[i] - v) * t)).join(',') + ')'; }
function rysujKamien(x, R, ksztalt, kolor, opcje) {
  opcje = opcje || {};
  let P;
  if (ksztalt === 'kolo') P = wielokat(10, R * 0.8, -Math.PI / 2);
  else if (ksztalt === 'romb') P = [[0, -R * 0.95], [R * 0.7, 0], [0, R * 0.95], [-R * 0.7, 0]];
  else if (ksztalt === 'szesc') P = wielokat(6, R * 0.88, -Math.PI / 2);
  else if (ksztalt === 'osm') P = wielokat(8, R * 0.9, -Math.PI / 2 + Math.PI / 8);
  else if (ksztalt === 'gwiazda') { P = []; for (let i = 0; i < 16; i++) { const a = -Math.PI / 2 + i * Math.PI / 8, r = i % 2 ? R * 0.62 : R * 0.98; P.push([Math.cos(a) * r, Math.sin(a) * r]); } }
  else if (ksztalt === 'pryzmat') P = [[0, -R * 0.9], [R * 0.92, R * 0.72], [-R * 0.92, R * 0.72]];
  else P = [[0, -R * 0.98], [R * 0.52, -R * 0.42], [R * 0.52, R * 0.42], [0, R * 0.98], [-R * 0.52, R * 0.42], [-R * 0.52, -R * 0.42]];   // kryształ
  const rgb = rgbKoloru(kolor), BIEL = [255, 255, 255], CZERN = [10, 6, 16];
  const tecza = opcje.tecza ? ['#ff7ae0', '#7ae0ff', '#ffe07a', '#9aff9a', '#b89aff', '#ff9a7a'] : null;
  const Q = P.map(([a, b]) => [a * 0.5, b * 0.5 - R * 0.04]);
  const L = [-0.6, -0.8];
  if (opcje.blask) {
    const g = x.createRadialGradient(0, 0, R * 0.3, 0, 0, R * 1.35); g.addColorStop(0, 'rgba(' + rgb.join(',') + ',0.55)'); g.addColorStop(1, 'rgba(' + rgb.join(',') + ',0)');
    x.fillStyle = g; x.beginPath(); x.arc(0, 0, R * 1.35, 0, Math.PI * 2); x.fill();
  }
  // obrys
  x.lineJoin = 'round';
  x.beginPath(); P.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.closePath();
  x.fillStyle = 'rgb(' + CZERN.join(',') + ')'; x.strokeStyle = 'rgba(10,6,16,0.95)'; x.lineWidth = R * 0.22; x.stroke(); x.fill();
  // ścianki: jaśniejsze od strony światła (lewa góra)
  for (let i = 0; i < P.length; i++) {
    const j = (i + 1) % P.length, mx = (P[i][0] + P[j][0]) / 2, my = (P[i][1] + P[j][1]) / 2, d = Math.hypot(mx, my) || 1;
    const s = (mx / d) * L[0] + (my / d) * L[1];
    x.fillStyle = tecza ? tecza[i % tecza.length] : (s > 0 ? mieszaj(rgb, BIEL, s * 0.5) : mieszaj(rgb, CZERN, -s * 0.55));
    if (tecza && s < 0) x.globalAlpha = 0.75 + s * 0.2;
    x.beginPath(); x.moveTo(P[i][0], P[i][1]); x.lineTo(P[j][0], P[j][1]); x.lineTo(Q[j][0], Q[j][1]); x.lineTo(Q[i][0], Q[i][1]); x.closePath(); x.fill();
    x.globalAlpha = 1;
  }
  // tafla (środek)
  const g = x.createLinearGradient(-R * 0.4, -R * 0.5, R * 0.4, R * 0.4);
  g.addColorStop(0, tecza ? '#ffffff' : mieszaj(rgb, BIEL, 0.55)); g.addColorStop(1, tecza ? '#ffd0f4' : mieszaj(rgb, BIEL, 0.1));
  x.fillStyle = g; x.beginPath(); Q.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.closePath(); x.fill();
  x.strokeStyle = 'rgba(255,255,255,0.35)'; x.lineWidth = R * 0.05; x.stroke();
  // błysk
  const bx = Q[0][0] * 0.2 - R * 0.18, by = -R * 0.2, bs = R * 0.2;
  x.fillStyle = '#ffffff'; x.beginPath(); x.moveTo(bx, by - bs); x.quadraticCurveTo(bx, by, bx + bs, by); x.quadraticCurveTo(bx, by, bx, by + bs); x.quadraticCurveTo(bx, by, bx - bs, by); x.quadraticCurveTo(bx, by, bx, by - bs); x.fill();
  if (opcje.promienie) {
    x.strokeStyle = 'rgba(255,255,255,0.85)'; x.lineWidth = R * 0.06; x.lineCap = 'round';
    [[R * 0.92, -R * 0.78], [-R * 0.95, R * 0.55], [R * 0.75, R * 0.9]].forEach(([a, b]) => { x.beginPath(); x.moveTo(a - R * 0.13, b); x.lineTo(a + R * 0.13, b); x.moveTo(a, b - R * 0.13); x.lineTo(a, b + R * 0.13); x.stroke(); });
  }
}
const DEF_ODZNAK = {
  t0: ['kolo', '#b8b8b8'], t1: ['romb', '#5aa8e6'], t2: ['szesc', '#b06ce8'], t3: ['osm', '#e6b53c', { blask: true }], t4: ['gwiazda', '#ff5a4a', { blask: true, promienie: true }],
  p: ['pryzmat', '#ff7ae0', { tecza: true, blask: true }], as: ['krysztal', '#a8adb8'], az: ['krysztal', '#e6c15c', { blask: true }], ap: ['krysztal', '#ff7ae0', { tecza: true, blask: true }],
};
// obrazek odznaki (canvas) - do rysowania na planszy lub jako adres obrazka
function odznaka(k, px) {
  px = px || 48;
  const klucz = k + '|' + px;
  if (ODZNAKI[klucz]) return ODZNAKI[klucz];
  const D = DEF_ODZNAK[k] || DEF_ODZNAK.t0, c = document.createElement('canvas'); c.width = c.height = px;
  const x = c.getContext('2d'); x.translate(px / 2, px / 2);
  rysujKamien(x, px * 0.36, D[0], D[1], D[2]);
  ODZNAKI[klucz] = c; return c;
}
function kluczOdznaki(t) { return t === 'p' ? 'p' : (t === 's' || t === 'z') ? 'a' + t : 't' + t; }
// <img> z odznaką (np. w opisach)
function htmlOdznaki(t, rozm) { return '<img class="odznaka" alt="" src="' + odznaka(kluczOdznaki(t)).toDataURL() + '"' + (rozm ? ' style="width:' + rozm + 'px;height:' + rozm + 'px"' : '') + '>'; }
// Kamienie jako zmienne CSS: --gem-t0 ... --gem-p, --gem-as, --gem-az, --gem-ap
function przygotujOdznaki() {
  try {
    const st = document.documentElement.style;
    Object.keys(DEF_ODZNAK).forEach(k => st.setProperty('--gem-' + k, 'url("' + odznaka(k).toDataURL('image/png') + '")'));
  } catch (e) {}
}

// =====================================================================
//  ZAPIS GRY (w przeglądarce)
// =====================================================================
function czyste(o, gl) {
  if (o === null || typeof o !== 'object') return o;
  if (Array.isArray(o)) return o.map(x => czyste(x, gl + 1)).filter(x => x !== undefined);
  if (gl > 4 || ('hpMax' in o && 'x' in o)) return undefined;   // nie zapisujemy wrogów
  const w = {};
  for (const k in o) {
    if (k.charCodeAt(0) === 95) continue;            // pola zaczynające się od "_" to pamięć podręczna
    const v = o[k];
    if (typeof v === 'function') continue;
    if (v && typeof v === 'object') { const c = czyste(v, gl + 1); if (c !== undefined) w[k] = c; }
    else w[k] = v;
  }
  return w;
}
function zapiszGre(wznowFale) {
  if (!run || !gracz || gracz.martwy || druzyna()) return;
  try {
    const g = czyste(gracz, 0); g.tarcze = []; g.buffy = {};
    const r = czyste(run, 0); delete r.oczekPrz; delete r.oczekBron;
    lStorSet('wiezien_zapis', { wersja: 3, czas: Date.now(), gracz: g, run: r, falaNr: fala.nr || 0, wznowFale: wznowFale || 0 });
  } catch (e) { zglosBlad(e, 'zapis'); }
}
function wczytajGre() {
  const z = lStorGet('wiezien_zapis', null);
  if (!z || !z.gracz || !z.run || z.wersja !== 3 || !KLASY[z.gracz.klasa]) return false;
  try {
    run = z.run; run.zrodla = run.zrodla || {};
    gracz = nowyGracz(z.gracz.klasa); Object.assign(gracz, z.gracz); gracz._run = run; gracze = [gracz]; lokalny = gracz;
    gracz.tarcze = []; gracz.buffy = {}; gracz.martwy = false; gracz.augmentyDoWyboru = gracz.augmentyDoWyboru || [];
    migrujStareStaty(gracz.ulepszenia); migrujStareStaty(gracz.stale);
    gracz.przedmioty = (gracz.przedmioty || []).filter(p => p && DEF_PRZ[p.id]);
    gracz.augmenty = (gracz.augmenty || []).filter(a => a && DEF_AUG[a.id]);
    gracz.oreze = (gracz.oreze || []).filter(o => o && DEF_ORE[o.id]).map(o => Object.assign(o, { ore: 1 }));
    gracz.bronie = (gracz.bronie || []).filter(b => b && BRONIE[b.rodzaj]); if (!gracz.bronie.length) gracz.bronie = [nowaBron(bronStartowa(KLASY[gracz.klasa]), 0)];
    gracz.umi = { cd: 0, cdMax: 0 }; gracz.umi2 = { cd: 0, cdMax: 0 }; if (gracz.slotyOreza === undefined) gracz.slotyOreza = KLASY[gracz.klasa].slotyOreza !== undefined ? KLASY[gracz.klasa].slotyOreza : 4; if (gracz.slotyPryzm === undefined) gracz.slotyPryzm = KLASY[gracz.klasa].slotyPryzm || 2; gracz.slotyPryzm = Math.max(gracz.slotyPryzm, liczPrzedm(true)); gracz.slotyPrzedm = Math.max(gracz.slotyPrzedm, liczPrzedm(false));
    fala = { nr: z.falaNr || 0, aktywna: false };
    D = null; przebudujHaki(); zastosujStaty(); gracz.hp = D.hpMax;
    stan = 'przerwa';
    if (z.wznowFale) { fala.nr = z.wznowFale - 1; run.przerwa = { nr: fala.nr, sklep: true, proba: true, sklepOtwarty: true }; run.wybranaProba = null; }
    if (!run.przerwa) run.przerwa = { nr: fala.nr, sklep: true, proba: true, sklepOtwarty: true };
    ustawKamere();
    kolejkaPrzerwy();
    return true;
  } catch (e) { zglosBlad(e, 'wczytaj'); lStorDel('wiezien_zapis'); return false; }
}
AKCJE.kontynuuj = () => { if (!wczytajGre()) { toast('Nie udało się wczytać zapisu'); pokazMenu(); } };
// Starsze zapisy: kradzież życia i regeneracja zniknęły z gry - zamieniamy je na wampiryzm i zdrowie
function migrujStareStaty(o) {
  if (!o) return;
  if (o.kradziez) { o.omni = (o.omni || 0) + o.kradziez * 0.5; delete o.kradziez; }
  if (o.regen) { o.hpMax = (o.hpMax || 0) + o.regen * 15; delete o.regen; }
}

// =====================================================================
//  PAD — gra na kontrolerze (Xbox, PlayStation, Switch Pro, 8BitDo…)
//  przez Gamepad API przeglądarki: na komputerze i na telefonie.
//  Walka: lewa gałka / krzyżak = ruch, A/RT = umiejętność, B/RB/X/LT = druga umiejętność,
//  Y/Start = pauza i build. Menu: krzyżak/gałka przesuwa podświetlenie,
//  A wybiera, B wraca, LB/RB zmienia zakładki, prawa gałka przewija.
//  Z tego samego podświetlenia korzysta klawiatura (strzałki, Enter, Esc).
// =====================================================================
const PB = { A: 0, B: 1, X: 2, Y: 3, LB: 4, RB: 5, LT: 6, RT: 7, SELECT: 8, START: 9, L3: 10, R3: 11, GORA: 12, DOL: 13, LEWO: 14, PRAWO: 15 };
const PAD = {
  podlaczony: false, nazwa: '', id: '', typ: 'xbox', akt: null,
  tryb: false,              // układ ekranu pod pada (bez dotykowego drążka)
  fokusWidoczny: false,     // podświetlenie w menu
  mx: 0, my: 0,             // ruch z gałki — czyta go wejscieRuchu()
  poprz: [], kier: null, tKier: 0,
  fokus: { ekran: null, modal: null }, pamiec: { ekran: null, modal: null }, swiezy: { ekran: true, modal: true },
  wibracje: lStorGet('wiezien_wibracje', true), ostHp: null, tWibr: 0, sygPodp: '',
};
const ETYKIETY_PADA = {
  xbox: { A: 'A', B: 'B', X: 'X', Y: 'Y', LB: 'LB', RB: 'RB', LT: 'LT', RT: 'RT', START: '☰', n: 'Xbox' },
  ps:   { A: '✕', B: '○', X: '□', Y: '△', LB: 'L1', RB: 'R1', LT: 'L2', RT: 'R2', START: 'Options', n: 'PlayStation' },
  nin:  { A: 'B', B: 'A', X: 'Y', Y: 'X', LB: 'L', RB: 'R', LT: 'ZL', RT: 'ZR', START: '+', n: 'Nintendo' },
};
const KOLORY_PADA = {
  xbox: { A: '#4caf50', B: '#e05545', X: '#3d8fe0', Y: '#e6b53c' },
  ps:   { A: '#6f9be8', B: '#e06a6a', X: '#d47fc0', Y: '#4fbf98' },
  nin:  { A: '#8a8a96', B: '#8a8a96', X: '#8a8a96', Y: '#8a8a96' },
};
function typPada(id) {
  id = (id || '').toLowerCase();
  if (/xbox|045e|xinput/.test(id)) return 'xbox';
  if (/054c|playstation|dualshock|dualsense|^wireless controller/.test(id)) return 'ps';
  if (/057e|nintendo|pro controller|joy-con/.test(id)) return 'nin';
  return 'xbox';
}
function nazwaPada(id) {
  const n = (id || '').replace(/\(.*?\)/g, '').replace(/^[0-9a-f]{1,4}-[0-9a-f]{1,4}-/i, '').replace(/\s+/g, ' ').trim();
  return (n || 'Pad').slice(0, 34);
}
// mały znaczek przycisku, np. kl('A') -> zielone kółko z literą A (albo ✕ na padzie PlayStation)
function kl(k) {
  const t = ETYKIETY_PADA[PAD.typ][k] || k, kol = (KOLORY_PADA[PAD.typ] || {})[k];
  return '<span class="kl"' + (kol ? ' style="background:' + kol + ';color:#fff"' : '') + '>' + t + '</span>';
}

// ---------- odczyt padów ----------
// Gra działa w ramce Streamlita — gdyby przeglądarka pokazywała pada tylko głównej
// stronie, czytamy go z okien nadrzędnych (ta sama domena).
let oknaPadow = null;
function listaPadow() {
  if (!oknaPadow) {
    oknaPadow = [window];
    try { let w = window; for (let i = 0; i < 6 && w.parent && w.parent !== w; i++) { w = w.parent; void w.navigator; oknaPadow.push(w); } } catch (e) {}
  }
  for (const w of oknaPadow) {
    let l = null;
    try { l = w.navigator.getGamepads ? w.navigator.getGamepads() : null; } catch (e) { l = null; }
    if (!l) continue;
    const wyn = [];
    for (let i = 0; i < l.length; i++) if (l[i] && l[i].connected !== false && l[i].buttons && l[i].buttons.length) wyn.push(l[i]);
    if (wyn.length) return wyn;
  }
  return [];
}
function stanPada(p) {
  const przyc = [];
  for (let i = 0; i < 17; i++) { const b = p.buttons[i]; przyc[i] = !!b && (b.pressed || b.value > 0.5); }
  const a = p.axes || [];
  // pady bez standardowego mapowania: krzyżak bywa na osiach 6/7
  if (p.mapping !== 'standard' && p.buttons.length < 16 && a.length >= 8) {
    przyc[14] = przyc[14] || a[6] < -0.5; przyc[15] = przyc[15] || a[6] > 0.5;
    przyc[12] = przyc[12] || a[7] < -0.5; przyc[13] = przyc[13] || a[7] > 0.5;
  }
  return { przyc: przyc, lx: a[0] || 0, ly: a[1] || 0, rx: a[2] || 0, ry: a[3] || 0 };
}
function strefaMartwa(x, y, dz) {
  const d = Math.hypot(x, y);
  if (d < dz) return [0, 0];
  const s = Math.min(1, (d - dz) / (1 - dz));
  return [x / d * s, y / d * s];
}

function podlaczPada(p) {
  const nowy = !PAD.podlaczony;
  PAD.podlaczony = true; PAD.id = p.id; PAD.nazwa = nazwaPada(p.id); PAD.typ = typPada(p.id);
  odswiezEtykietyPada();
  if (nowy) toast('🎮 Pad podłączony: ' + esc(PAD.nazwa));
  const st = $('padStatus'); if (st) st.innerHTML = statusPadaHtml();
}
function odlaczPada() {
  PAD.podlaczony = false; PAD.akt = null; PAD.mx = PAD.my = 0; PAD.poprz = [];
  toast('🎮 Pad odłączony');
  wlaczTrybPada(false);
  // jak na konsoli: zgubiony pad w trakcie walki = pauza (w drużynie gra toczy się dalej)
  if (stan === 'walka' && gracz && !druzyna()) $('btnEkw').click();
  const st = $('padStatus'); if (st) st.innerHTML = statusPadaHtml();
}
function odswiezEtykietyPada() {
  document.querySelectorAll('.pad-kl[data-k]').forEach(el => {
    const k = el.dataset.k; el.textContent = ETYKIETY_PADA[PAD.typ][k] || k;
    const kol = (KOLORY_PADA[PAD.typ] || {})[k]; el.style.background = kol || ''; el.style.color = kol ? '#fff' : '';
  });
  $('padSrodek').innerHTML = '🎮 prawa gałka: celowanie<br>' + kl('LT') + ' 🧪 · ' + kl('RT') + ' ✨ · ' + kl('START') + ' ⏸️';
  PAD.sygPodp = '';
}
function wlaczTrybPada(wl) {
  wl = !!wl;
  if (PAD.tryb === wl) return;
  PAD.tryb = wl;
  $('gra').classList.toggle('tryb-pad', wl);
  dopasujRozmiar();
  if (!wl) $('padPodp').classList.remove('widoczny');
}

// ---------- wibracje ----------
function wibruj(sila, ms) {
  if (!PAD.wibracje || !PAD.akt || PAD.tWibr > performance.now()) return;
  PAD.tWibr = performance.now() + 110;
  const p = PAD.akt, v = p.vibrationActuator;
  try {
    if (v && v.playEffect) v.playEffect('dual-rumble', { startDelay: 0, duration: ms, weakMagnitude: Math.min(1, sila), strongMagnitude: Math.min(1, sila * 0.8) }).catch(() => {});
    else if (p.hapticActuators && p.hapticActuators[0]) p.hapticActuators[0].pulse(Math.min(1, sila), ms);
  } catch (e) {}
}
function wibracjeOdObrazen() {
  const ja = lokalny || gracz;
  if (!ja || stan !== 'walka' || !PAD.podlaczony) { PAD.ostHp = null; return; }
  const hp = ja.hp, max = (D && D.hpMax) || ja.hpMax || 100;
  if (PAD.ostHp !== null && hp < PAD.ostHp - 0.5) {
    const proc = (PAD.ostHp - hp) / Math.max(1, max);
    if (ja.martwy || ja.powalony || hp <= 0) wibruj(1, 450);
    else wibruj(0.22 + Math.min(0.7, proc * 4), Math.round(70 + Math.min(220, proc * 900)));
  }
  PAD.ostHp = hp;
}

// ---------- stan gry ----------
function trybWalki() {
  return stan === 'walka' && !!gracz && !ekranEl.classList.contains('widoczny') && !modalEl.classList.contains('widoczny');
}
function warstwaMenu() {
  if (modalEl.classList.contains('widoczny')) return { el: modalTresc, k: 'modal' };
  if (ekranEl.classList.contains('widoczny')) return { el: ekranEl, k: 'ekran' };
  return null;
}

// ---------- główna aktualizacja (co klatkę) ----------
function aktualizujPada(dt) {
  const pady = listaPadow();
  if (!pady.length) {
    if (PAD.podlaczony) odlaczPada();
    PAD.mx = PAD.my = 0;
    if (PAD.fokusWidoczny) { const w = warstwaMenu(); if (w && !trybWalki()) zapewnijFokus(w); }
    return;
  }
  // kilka padów: steruje ten, którego ktoś ostatnio użył
  let p = pady[0];
  for (const q of pady) if ((q.timestamp || 0) > (p.timestamp || 0)) p = q;
  PAD.akt = p;
  if (!PAD.podlaczony || PAD.id !== p.id) podlaczPada(p);
  const s = stanPada(p);
  const nowe = i => s.przyc[i] && !PAD.poprz[i];
  const cokolwiek = s.przyc.some((x, i) => x && !PAD.poprz[i]) || Math.hypot(s.lx, s.ly) > 0.4 || Math.hypot(s.rx, s.ry) > 0.4;
  const bylWidoczny = PAD.fokusWidoczny;
  if (cokolwiek) {
    if (!PAD.tryb) wlaczTrybPada(true);
    if (s.przyc.some((x, i) => x && !PAD.poprz[i])) inicjujDzwiek();
  }
  if (trybWalki()) {
    let [mx, my] = strefaMartwa(s.lx, s.ly, 0.2);
    if (s.przyc[PB.LEWO]) mx -= 1; if (s.przyc[PB.PRAWO]) mx += 1;
    if (s.przyc[PB.GORA]) my -= 1; if (s.przyc[PB.DOL]) my += 1;
    const d = Math.hypot(mx, my); if (d > 1) { mx /= d; my /= d; }
    PAD.mx = mx; PAD.my = my;
    // prawa gałka: celowanie (puszczona = postać sama namierza najbliższego wroga)
    const ja = lokalny || gracz, dr = Math.hypot(s.rx, s.ry);
    if (ja) { if (dr > 0.35) { ja.celKat = Math.atan2(s.ry, s.rx); PAD.celuje = true; } else if (PAD.celuje) { ja.celKat = null; PAD.celuje = false; } }
    const maDruga = !!(gracz && KLASY[gracz.klasa] && KLASY[gracz.klasa].umi2);
    if (nowe(PB.A) || nowe(PB.RT) || (!maDruga && nowe(PB.RB))) { if (uzyjUmiejetnosci(1)) wibruj(0.3, 70); }
    if (maDruga && (nowe(PB.RB) || nowe(PB.B) || nowe(PB.X) || nowe(PB.LT) || nowe(PB.LB))) { if (uzyjUmiejetnosci(2)) wibruj(0.25, 60); }
    if (nowe(PB.L3)) przelaczAuto(1);
    if (nowe(PB.R3)) przelaczAuto(2);
    if (nowe(PB.Y) || nowe(PB.START)) $('btnEkw').click();
    if (cokolwiek) PAD.fokusWidoczny = true;
    $('padPodp').classList.remove('widoczny');
  } else {
    PAD.mx = PAD.my = 0;
    if (PAD.celuje) { const ja = lokalny || gracz; if (ja) ja.celKat = null; PAD.celuje = false; }
    if (cokolwiek) PAD.fokusWidoczny = true;
    menuPada(s, nowe, dt, bylWidoczny);
  }
  PAD.poprz = s.przyc;
  wibracjeOdObrazen();
}

function menuPada(s, nowe, dt, bylWidoczny) {
  const w = warstwaMenu();
  odswiezPodpowiedz(w);
  if (!w) return;
  zapewnijFokus(w);
  // kierunek z krzyżaka albo lewej gałki (z powtarzaniem przy przytrzymaniu)
  let kier = null;
  if (s.przyc[PB.GORA]) kier = 'g'; else if (s.przyc[PB.DOL]) kier = 'd'; else if (s.przyc[PB.LEWO]) kier = 'l'; else if (s.przyc[PB.PRAWO]) kier = 'p';
  else if (Math.max(Math.abs(s.lx), Math.abs(s.ly)) > 0.55) kier = Math.abs(s.ly) >= Math.abs(s.lx) ? (s.ly < 0 ? 'g' : 'd') : (s.lx < 0 ? 'l' : 'p');
  if (kier) {
    if (kier !== PAD.kier) { PAD.kier = kier; PAD.tKier = 0.36; if (bylWidoczny) przesunFokus(w, kier); }
    else { PAD.tKier -= dt; if (PAD.tKier <= 0) { PAD.tKier = 0.1; przesunFokus(w, kier); } }
  } else PAD.kier = null;
  if (!bylWidoczny) return;   // pierwsze dotknięcie pada tylko pokazuje podświetlenie
  if (nowe(PB.A)) aktywuj(w);
  else if (nowe(PB.X)) aktywujDrugie(w);
  else if (nowe(PB.B)) wstecz(w);
  else if (nowe(PB.LB) || nowe(PB.LT)) zakladka(w, -1);
  else if (nowe(PB.RB) || nowe(PB.RT)) zakladka(w, 1);
  else if (nowe(PB.Y) || nowe(PB.START)) {
    if (w.k === 'modal') wstecz(w);
    else if (stan === 'pauza' || (stan === 'walka' && druzyna())) $('btnEkw').click();
  }
  // prawa gałka przewija ekran
  if (Math.abs(s.ry) > 0.22) w.el.scrollTop += Math.sign(s.ry) * (Math.abs(s.ry) - 0.22) / 0.78 * 1100 * dt;
}

// ---------- podświetlenie (fokus) w menu ----------
function kandydaci(root) {
  const lista = root.querySelectorAll('[data-a], button, input, textarea, [data-pad]');
  const wyn = [];
  for (const el of lista) {
    // przyciski wewnątrz karty-celu (data-pad) obsługuje sama karta: A = główna akcja, X = druga
    if (!el.dataset.pad && el.parentElement && el.parentElement.closest('[data-pad]')) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    wyn.push(el);
  }
  // pojemnik z innymi klikalnymi elementami w środku pomijamy (klika się to, co w nim)
  return wyn.filter(el => !wyn.some(x => x !== el && el.contains(x)));
}
function tytulWarstwy(el) { const t = el.querySelector('.tytul'); return t ? t.textContent : ''; }
function sygnatura(el) {
  const d = el.dataset || {};
  return (el.tagName) + '|' + Object.keys(d).sort().map(k => k + '=' + d[k]).join('&') + '|' + (el.id || '') + (d.a ? '' : '|' + (el.textContent || '').trim().slice(0, 24));
}
function zapamietaj(w, el) {
  const r = el.getBoundingClientRect();
  PAD.pamiec[w.k] = { syg: sygnatura(el), tytul: tytulWarstwy(w.el), x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
}
const PREF_FOKUSU = ['kowStatWybierz', 'kup', 'augWybierz', 'kowWybierz', 'statWybierz', 'bronStart', 'probaWybierz', 'skrzWezOreze', 'skrzZaloz', 'skrzPolacz', 'skrzZloto', 'skrzKamien',
  'wznow', 'kontynuuj', 'znowu', 'startRunuZModala', 'lobbyGotowy', 'dalejPrzerwa', 'augPomin', 'zalozDruzyne'];
function wWidoku(root, el) {
  const v = root.getBoundingClientRect(), r = el.getBoundingClientRect();
  return r.bottom > v.top + 4 && r.top < v.bottom - 4;
}
function fokusDomyslny(root, kand) {
  const akcja = e => e.dataset.a || e.dataset.pad;
  const mozna = e => !e.disabled && !(e.dataset.pad && (e.querySelector('[data-a="' + e.dataset.pad + '"]') || {}).disabled);
  for (const a of PREF_FOKUSU) { const el = kand.find(e => akcja(e) === a && mozna(e)); if (el) return el; }
  const kup = kand.find(e => akcja(e) === 'kup'); if (kup) return kup;
  const wyb = kand.find(e => e.classList.contains('wybrany')); if (wyb) return wyb;
  const glowny = e => e.classList.contains('btn') && !e.classList.contains('drugi') && !e.classList.contains('czerw') && !e.disabled;
  const wid = kand.filter(e => wWidoku(root, e));
  return wid.find(glowny) || wid[0] || kand.find(glowny) || kand[kand.length - 1];
}
function zapewnijFokus(w) {
  const f = PAD.fokus[w.k];
  if (f && f.isConnected && w.el.contains(f)) {
    if (PAD.fokusWidoczny && !f.classList.contains('pad-fokus')) f.classList.add('pad-fokus');
    return f;
  }
  const kand = kandydaci(w.el);
  if (!kand.length) { PAD.fokus[w.k] = null; return null; }
  const m = PAD.pamiec[w.k];
  let wyb = null;
  if (!PAD.swiezy[w.k] && m) {
    wyb = kand.find(el => sygnatura(el) === m.syg);
    if (!wyb && m.tytul === tytulWarstwy(w.el)) {
      let najD = Infinity;
      for (const el of kand) { const r = el.getBoundingClientRect(), d = Math.hypot((r.left + r.right) / 2 - m.x, ((r.top + r.bottom) / 2 - m.y) * 1.4); if (d < najD) { najD = d; wyb = el; } }
    }
  }
  let bezPrzew = false;
  if (!wyb) {
    wyb = fokusDomyslny(w.el, kand);
    // nic klikalnego nie widać (np. długi opis z przyciskiem na dole) — zostajemy na górze tekstu
    if (!wWidoku(w.el, wyb)) bezPrzew = true;
  }
  PAD.swiezy[w.k] = false;
  ustawFokus(w, wyb, bezPrzew);
  return wyb;
}
function ustawFokus(w, el, bezPrzew) {
  const st = PAD.fokus[w.k];
  if (st && st !== el) {
    st.classList.remove('pad-fokus');
    if ((st.tagName === 'INPUT' || st.tagName === 'TEXTAREA') && document.activeElement === st) st.blur();
  }
  PAD.fokus[w.k] = el;
  if (!el) return;
  if (PAD.fokusWidoczny) el.classList.add('pad-fokus');
  if (!bezPrzew) dopilnujWidocznosci(w.el, el);
  zapamietaj(w, el);
}
function dopilnujWidocznosci(sc, el) {
  const v = sc.getBoundingClientRect(), r = el.getBoundingClientRect();
  const mg = 14, md = PAD.tryb ? 48 : 18;
  if (r.height > v.height - mg - md || r.top < v.top + mg) sc.scrollTop -= (v.top + mg) - r.top;
  else if (r.bottom > v.bottom - md) sc.scrollTop += r.bottom - (v.bottom - md);
}
function pokazPodswietlenie() {
  PAD.fokusWidoczny = true;
  const w = warstwaMenu(); if (!w) return;
  const f = zapewnijFokus(w); if (f) f.classList.add('pad-fokus');
}
function ukryjPodswietlenie() {
  PAD.fokusWidoczny = false;
  document.querySelectorAll('.pad-fokus').forEach(e => e.classList.remove('pad-fokus'));
  $('padPodp').classList.remove('widoczny');
}
function przesunFokus(w, kier) {
  const f = zapewnijFokus(w); if (!f) return;
  const sc = w.el, v = sc.getBoundingClientRect(), kand = kandydaci(sc), pion = kier === 'g' || kier === 'd';
  // podświetlenie odjechało poza ekran (przewijanie gałką) — wracamy do tego, co widać
  if (!wWidoku(sc, f)) {
    const wid = kand.filter(e => wWidoku(sc, e));
    if (wid.length) { ustawFokus(w, kier === 'g' ? wid[wid.length - 1] : wid[0]); return; }
    if (pion) { sc.scrollTop += (kier === 'd' ? 1 : -1) * v.height * 0.55; return; }
    return;
  }
  const c = f.getBoundingClientRect(), cx = (c.left + c.right) / 2, cy = (c.top + c.bottom) / 2;
  let naj = null, najW = Infinity;
  for (const el of kand) {
    if (el === f) continue;
    const r = el.getBoundingClientRect(), rx = (r.left + r.right) / 2, ry = (r.top + r.bottom) / 2;
    const mh = Math.min(c.height, r.height) * 0.5, mw = Math.min(c.width, r.width) * 0.5;
    let gl, bok;
    if (kier === 'd') { if (ry <= cy + 2 || r.top < c.top + mh) continue; gl = Math.max(0, r.top - c.bottom); }
    else if (kier === 'g') { if (ry >= cy - 2 || r.bottom > c.bottom - mh) continue; gl = Math.max(0, c.top - r.bottom); }
    else if (kier === 'p') { if (rx <= cx + 2 || r.left < c.left + mw) continue; gl = Math.max(0, r.left - c.right); }
    else { if (rx >= cx - 2 || r.right > c.right - mw) continue; gl = Math.max(0, c.left - r.right); }
    if (pion) bok = Math.max(0, r.left - c.right, c.left - r.right);
    else { bok = Math.max(0, r.top - c.bottom, c.top - r.bottom); if (bok > 24) continue; }
    const wynik = gl + bok * 3 + (pion ? Math.abs(rx - cx) : Math.abs(ry - cy)) * 0.15;
    if (wynik < najW) { najW = wynik; naj = el; }
  }
  if (!naj) {
    // nic dalej w tym kierunku — przewijamy (np. długi opis w Kodeksie)
    if (pion) sc.scrollTop += (kier === 'd' ? 1 : -1) * v.height * 0.55;
    return;
  }
  // następny przycisk jest daleko za krawędzią ekranu — najpierw przewijamy, żeby dało się czytać
  const r = naj.getBoundingClientRect();
  const maxSc = sc.scrollHeight - sc.clientHeight;
  if (kier === 'd' && r.top > v.bottom && r.top - c.bottom > v.height * 0.55 && sc.scrollTop < maxSc - 2) { sc.scrollTop += v.height * 0.55; return; }
  if (kier === 'g' && r.bottom < v.top && c.top - r.bottom > v.height * 0.55 && sc.scrollTop > 2) { sc.scrollTop -= v.height * 0.55; return; }
  ustawFokus(w, naj);
}
function aktywuj(w) {
  const f = zapewnijFokus(w); if (!f) return;
  zapamietaj(w, f);
  if (f.tagName === 'INPUT' || f.tagName === 'TEXTAREA') { f.focus(); try { f.select(); } catch (e) {} return; }
  if (f.dataset.pad) { kliknijWKarcie(f, f.dataset.pad); return; }
  if (f.disabled) { f.classList.remove('pad-nie'); void f.offsetWidth; f.classList.add('pad-nie'); return; }
  f.classList.add('pad-wcisniety'); setTimeout(() => f.classList.remove('pad-wcisniety'), 130);
  f.click();
}
// karta-cel: klika jej przycisk o danej akcji (z jego danymi), a gdy jest wyłączony — potrząsa kartą
function kliknijWKarcie(f, akcja) {
  const b = f.querySelector('[data-a="' + akcja + '"]');
  if (!b || b.disabled) { f.classList.remove('pad-nie'); void f.offsetWidth; f.classList.add('pad-nie'); if (b && akcja === 'kup') toast('💰 Za mało złota'); return; }
  f.classList.add('pad-wcisniety'); setTimeout(() => f.classList.remove('pad-wcisniety'), 130);
  b.click();
}
function aktywujDrugie(w) {
  const f = zapewnijFokus(w); if (!f || !f.dataset.pad2) return false;
  zapamietaj(w, f); kliknijWKarcie(f, f.dataset.pad2); return true;
}
function wstecz(w) {
  if (w.k === 'modal') {
    const b = Array.from(modalTresc.querySelectorAll('[data-a="zamknijModal"]')).pop();
    if (b) { b.click(); return; }
    if (!modalEl.dataset.wymuszony) AKCJE.zamknijModal();
    return;
  }
  if (stan === 'pauza' || (stan === 'walka' && druzyna())) { $('btnEkw').click(); return; }
  // przyciski „◀ Menu” / „◀ Wstecz” (bez wychodzenia z drużyny — to tylko świadomym A)
  const b = Array.from(ekranEl.querySelectorAll('button[data-a]')).find(e => /^\s*◀/.test(e.textContent) && !e.disabled && e.dataset.a !== 'opuscTak');
  if (b) b.click();
}
function zakladka(w, d) {
  const z = w.el.querySelector('.zakladki:not(.opcje)'); if (!z) return;
  const bt = Array.from(z.querySelectorAll('button'));
  const i = bt.findIndex(b => b.classList.contains('akt'));
  const n = bt[((i < 0 ? 0 : i) + d + bt.length) % bt.length]; if (!n) return;
  zapamietaj(w, n);
  n.click();
}

// ---------- pasek podpowiedzi na dole (tylko w menu, gdy gra się padem) ----------
function odswiezPodpowiedz(w) {
  const el = $('padPodp');
  const pokaz = PAD.tryb && PAD.fokusWidoczny && !!w;
  el.classList.toggle('widoczny', pokaz);
  if (!pokaz) return;
  const zak = !!w.el.querySelector('.zakladki:not(.opcje)');
  const f = PAD.fokus[w.k], an = f && f.dataset.padn, a2 = f && f.dataset.pad2n;
  const syg = PAD.typ + w.k + zak + stan + an + a2;
  if (syg === PAD.sygPodp) return;
  PAD.sygPodp = syg;
  el.innerHTML = kl('A') + ' ' + (an || 'wybierz') + (a2 ? ' · ' + kl('X') + ' ' + a2 : '') + ' · ' + kl('B') + ' wstecz' + (zak ? ' · ' + kl('LB') + kl('RB') + ' zakładki' : '') + ' · 🕹️ przewijanie' +
    (stan === 'pauza' ? ' · ' + kl('START') + ' wznów' : '');
}

// ---------- klawiatura w menu (strzałki / WASD, Enter, Esc, Q/E) ----------
function klawiszMenu(e, wPolu) {
  if (trybWalki()) return false;
  const w = warstwaMenu(); if (!w) return false;
  const k = e.code;
  if (wPolu) {
    // w polu tekstowym (pseudonim, kod drużyny) piszemy normalnie
    if (k === 'Escape' || k === 'Enter' || k === 'NumpadEnter' || k === 'ArrowUp' || k === 'ArrowDown') {
      e.preventDefault(); e.target.blur(); pokazPodswietlenie();
      if (k === 'ArrowUp' || k === 'ArrowDown') przesunFokus(w, k === 'ArrowUp' ? 'g' : 'd');
    }
    return true;
  }
  const kier = { ArrowUp: 'g', KeyW: 'g', ArrowDown: 'd', KeyS: 'd', ArrowLeft: 'l', KeyA: 'l', ArrowRight: 'p', KeyD: 'p' }[k];
  if (kier) { e.preventDefault(); if (!PAD.fokusWidoczny) pokazPodswietlenie(); else przesunFokus(w, kier); return true; }
  if (k === 'Enter' || k === 'NumpadEnter' || k === 'Space') { e.preventDefault(); if (!PAD.fokusWidoczny) pokazPodswietlenie(); else aktywuj(w); return true; }
  if (k === 'Escape' || k === 'Backspace') { e.preventDefault(); wstecz(w); return true; }
  if (k === 'KeyQ' || k === 'PageUp') { e.preventDefault(); zakladka(w, -1); return true; }
  if (k === 'KeyX') { if (PAD.fokusWidoczny && aktywujDrugie(w)) { e.preventDefault(); return true; } return false; }
  if (k === 'KeyE' || k === 'PageDown') { e.preventDefault(); zakladka(w, 1); return true; }
  return false;
}

// dotyk albo myszka chowa podświetlenie; dotyk wraca też do układu z drążkiem
document.addEventListener('pointerdown', e => {
  if (PAD.fokusWidoczny) ukryjPodswietlenie();
  if (e.pointerType === 'touch') wlaczTrybPada(false);
  const el = e.target.closest && e.target.closest('[data-a], button, input, textarea');
  const w = warstwaMenu();
  if (el && w && w.el.contains(el)) { PAD.fokus[w.k] = el; zapamietaj(w, el); }
}, { capture: true, passive: true });

// nowy ekran / okno = nowe podświetlenie domyślne; przerysowanie tego samego = zostaje, gdzie było
(function () {
  const pe = pokazEkran, pm = pokazModal;
  pokazEkran = function (html, op) {
    const t0 = tytulWarstwy(ekranEl), byl = ekranEl.classList.contains('widoczny');
    pe(html, op);
    if (!(op && op.zachowaj) && (!byl || tytulWarstwy(ekranEl) !== t0)) PAD.swiezy.ekran = true;
  };
  pokazModal = function (html, zachowaj) {
    pm(html, zachowaj);
    if (!zachowaj) PAD.swiezy.modal = true;
  };
})();

// ---------- ekran „Pad i klawiatura” ----------
function statusPadaHtml() {
  return PAD.podlaczony
    ? '<span class="ziel">🎮 Podłączony:</span> <b>' + esc(PAD.nazwa) + '</b> <span style="opacity:0.7">(' + ETYKIETY_PADA[PAD.typ].n + ')</span>'
    : '🔌 Nie widzę pada. Podłącz go kablem albo przez Bluetooth i <b>naciśnij dowolny przycisk</b> — przeglądarka pokazuje pada grze dopiero po pierwszym wciśnięciu.';
}
AKCJE.sterowanie = () => pokazModal(htmlSterowania());
AKCJE.wibracje = () => { PAD.wibracje = !PAD.wibracje; lStorSet('wiezien_wibracje', PAD.wibracje); if (PAD.wibracje) { PAD.tWibr = 0; wibruj(0.7, 220); } pokazModal(htmlSterowania(), true); };
function htmlSterowania() {
  const w = (a, b) => '<div class="wiersz-stat"><span class="n">' + a + '</span><span style="font-size:12px;font-weight:800">' + b + '</span></div>';
  return '<div class="tytul">🎮 Sterowanie</div>' +
    '<div class="info-pole" id="padStatus">' + statusPadaHtml() + '</div>' +
    '<div class="sekcja">Walka — pad</div>' +
    w('🕹️ Ruch', 'lewa gałka albo krzyżak') + w('🎯 Celowanie', 'prawa gałka (puszczona = postać sama namierza)') + w('✨ Umiejętność postaci', kl('A') + ' albo ' + kl('RT') + ' (' + kl('RB') + ', gdy postać ma jedną)') + w('✨ Druga umiejętność (niektóre postacie)', kl('RB') + ', ' + kl('B') + ', ' + kl('X') + ' albo ' + kl('LT')) +
    w('🤖 Auto-użycie umiejętności', kl('L3') + ' / ' + kl('R3') + ' (wciśnij gałkę)') + w('⏸️ Pauza i build', kl('Y') + ' albo ' + kl('START')) +
    '<div class="sekcja">Menu i sklep — pad</div>' +
    w('Przesuwanie', 'krzyżak albo lewa gałka') + w('Wybierz / kup', kl('A')) + w('Zablokuj ofertę w sklepie', kl('X')) + w('Wstecz / zamknij', kl('B')) +
    w('Zakładki', kl('LB') + ' ' + kl('RB')) + w('Przewijanie', 'prawa gałka') +
    '<div class="sekcja">Klawiatura i myszka (komputer)</div>' +
    w('Ruch', 'WASD / strzałki') + w('Umiejętność · druga', 'E lub spacja · R lub Q') + w('🤖 Auto-użycie', 'Shift+E · Shift+R albo prawy klik na przycisku') + w('Pauza', 'Esc lub P') +
    w('Menu', 'strzałki, Enter, Esc, Q/E zakładki') +
    w('🖱️ Ruch myszą', 'przytrzymaj lewy przycisk') + w('🖱️ Umiejętność w stronę kursora', 'prawy przycisk') +
    '<div class="info-pole" style="font-size:11.5px">Działa w Chrome, Edge, Safari (także na iPhonie) i Firefoksie. Na telefonie sparuj pada w ustawieniach Bluetooth — tak jak słuchawki. ' +
    'Gdy grasz padem, dotykowy drążek się chowa i plansza robi się większa; dotknij ekranu, a wróci. Pseudonim i kod drużyny w grze online wpisuje się klawiaturą.</div>' +
    '<button class="btn drugi" data-a="wibracje">' + (PAD.wibracje ? '📳 Wibracje pada: włączone' : '📴 Wibracje pada: wyłączone') + '</button>' +
    '<button class="btn" data-a="zamknijModal">Zamknij</button>';
}
// zdarzenia przeglądarki — tylko dla szybszej reakcji (i tak sprawdzamy co klatkę)
window.addEventListener('gamepadconnected', () => { const l = listaPadow(); if (l.length) podlaczPada(l[0]); });

// =====================================================================
//  GRA ONLINE - DRUŻYNA (do 4 osób)
//  Połączenie bezpośrednie między przeglądarkami (WebRTC, biblioteka PeerJS).
//  Gospodarz (host) liczy całą walkę i rozsyła stan; każdy klient sam
//  porusza swoją postacią (bez opóźnienia) i sam przechodzi swoje ekrany
//  między falami (sklep, augmenty...), a potem odsyła swoją postać.
// =====================================================================
Object.assign(SIEC, {
  rola: null,            // null | 'host' | 'klient'
  peer: null, host: null, polaczenia: {}, kod: '', mojeId: 0, nastId: 1,
  lobby: [], trudnosc: 1, wGrze: false, gotowi: {}, dane: {}, nastepnaFala: 1,
  zdarzenia: [], zdarzeniaG: {}, dzwieki: [], tWysylki: 0, tPoz: 0, licznikStanu: 0,
  widokGraczy: [], mojWidok: null, znaneWrogi: {}, ostStan: null, ostatnio: {}, ostOdHosta: 0, tCzekania: 0,
  nrWiad: 0, zal: {}, rtt: 0, rttG: {}, lupOst: new Set(), zebraneLok: {}, vx: 0, vy: 0, zbieranie: 60,
});
const PREFIKS_PEER = 'wiezien-labiryntu-v3-';
const MAKS_GRACZY = 4;
const ZRODLA_PEERJS = ['https://cdn.jsdelivr.net/npm/peerjs@1.5.4/dist/peerjs.min.js', 'https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/peerjs/1.5.4/peerjs.min.js'];

function klasaPeer() { return window.Peer || (window.peerjs && window.peerjs.Peer) || null; }
function zaladujPeerJS() {
  return new Promise((ok, blad) => {
    if (klasaPeer()) { ok(); return; }
    let i = 0;
    const proba = () => {
      if (i >= ZRODLA_PEERJS.length) { blad(new Error('Nie udało się wczytać biblioteki sieciowej')); return; }
      const sc = document.createElement('script'); sc.src = ZRODLA_PEERJS[i++]; sc.async = true;
      sc.onload = () => { if (klasaPeer()) ok(); else proba(); };
      sc.onerror = () => proba();
      document.head.appendChild(sc);
    };
    proba();
  });
}
function losowyKod() { const z = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; let k = ''; for (let i = 0; i < 4; i++) k += z[Math.floor(Math.random() * z.length)]; return k; }
function mojNick() { return (lStorGet('wiezien_nick', '') || '').trim() || 'Gracz'; }
function mojaKlasa() { return lStorGet('wiezien_klasa_online', 'wiezniarka'); }

// ---------------------------------------------------------------------
//  WYSYŁANIE
// ---------------------------------------------------------------------
// Wiadomości idą jako tekst JSON (serialization 'raw'). Duże dzielimy na kawałki, bo kanał
// WebRTC ma limit rozmiaru jednej wiadomości (PeerJS w trybie 'json' po cichu gubi większe niż 16 kB).
const MAKS_KAWALKA = 12000;
function wyslij(conn, msg) {
  try {
    if (!conn || !conn.open) return false;
    const txt = typeof msg === 'string' ? msg : JSON.stringify(msg);
    const maks = conn.serialization === 'raw' ? MAKS_KAWALKA : MAKS_KAWALKA / 2;   // w trybie 'json' tekst jeszcze puchnie
    if (txt.length <= maks) { conn.send(txt); return true; }
    const id = (++SIEC.nrWiad).toString(36), cz = [];
    for (let a = 0; a < txt.length;) {
      let b = Math.min(txt.length, a + maks);
      const c = txt.charCodeAt(b - 1); if (b < txt.length && c >= 0xD800 && c <= 0xDBFF) b--;   // nie rozcinamy emoji
      cz.push(txt.slice(a, b)); a = b;
    }
    cz.forEach((t, i) => conn.send('~' + id + '|' + i + '|' + cz.length + '|' + t));
    return true;
  } catch (e) { zglosBlad(e, 'wyslij'); }
  return false;
}
// składanie kawałków po drugiej stronie
function odbierzSurowe(conn, d, fn) {
  if (typeof d !== 'string') { if (d) fn(d); return; }
  if (d.charCodeAt(0) !== 126) { fn(JSON.parse(d)); return; }        // '~' = kawałek
  const a = d.indexOf('|'), b = d.indexOf('|', a + 1), c = d.indexOf('|', b + 1);
  const id = d.slice(1, a), i = +d.slice(a + 1, b), n = +d.slice(b + 1, c);
  const buf = conn._kawalki || (conn._kawalki = {});
  const e = buf[id] || (buf[id] = { n: n, cz: [], ile: 0, t: Date.now() });
  if (e.cz[i] === undefined) { e.cz[i] = d.slice(c + 1); e.ile++; }
  if (e.ile >= e.n) { delete buf[id]; fn(JSON.parse(e.cz.join(''))); }
  for (const k in buf) if (Date.now() - buf[k].t > 20000) delete buf[k];
}
// ile bajtów czeka w kolejce kanału: nowy stan wysyłamy dopiero, gdy poprzedni prawie wyszedł.
// Na szybkim łączu to nic nie zmienia (15 razy/s), na wolnym stanów jest mniej, ale są świeże (zamiast kolejki sprzed sekundy).
function zatkane(conn) { try { return !!conn.dataChannel && conn.dataChannel.bufferedAmount > Math.max(3000, (conn._ostStan || 0) * 0.5); } catch (e) { return false; } }
function siecWyslijHost(msg) { wyslij(SIEC.host, msg); }
function rozeslij(msg) { for (const id in SIEC.polaczenia) wyslij(SIEC.polaczenia[id], msg); }
function siecZdarzenie(ev) { if (SIEC.rola === 'host' && SIEC.wGrze) { SIEC.zdarzenia.push(ev); if (SIEC.zdarzenia.length > 300) SIEC.zdarzenia.splice(0, 100); } }
function siecZdarzenieGracza(p, ev) { if (SIEC.rola !== 'host') return; (SIEC.zdarzeniaG[p.id] || (SIEC.zdarzeniaG[p.id] = [])).push(ev); }
// dźwięki gospodarza słychać też u klientów; dźwięki "osobiste" (obrażenia, awans...)
// słyszy tylko ten gracz, którego dotyczą
const DZ_OSOBISTE = { awans: 1, mikstura: 1, obrazenia: 1, unik: 1, tarcza: 1 };
(function () {
  Object.keys(DZ).forEach(k => {
    const f = DZ[k];
    DZ[k] = function (a) {
      if (SIEC.rola === 'host' && SIEC.wGrze && stan === 'walka') {
        if (DZ_OSOBISTE[k]) { if (gracz && gracz.zdalny) { siecZdarzenieGracza(gracz, ['s', k]); return; } }
        else if (SIEC.dzwieki.length < 12 && SIEC.dzwieki.indexOf(k) < 0) SIEC.dzwieki.push(k);
      } else if (gracze.length > 1 && DZ_OSOBISTE[k] && gracz !== lokalny) return;
      f.apply(DZ, arguments);
    };
  });
})();

// ---------------------------------------------------------------------
//  LOBBY - ZAKŁADANIE I DOŁĄCZANIE
// ---------------------------------------------------------------------
AKCJE.online = () => pokazOnline();
function pokazOnline(kodStartowy) {
  const nick = lStorGet('wiezien_nick', '');
  pokazEkran('<div style="max-width:440px;margin:0 auto">' +
    '<div class="tytul">👥 Gra z przyjaciółmi</div><div class="podtytul">Do 4 osób w jednej drużynie. Każdy gra na swoim telefonie i ma własną postać, sklep i augmenty — łupy są wspólne.</div>' +
    '<div class="sekcja">Twoje imię</div><input class="pole" id="poleNick" maxlength="14" placeholder="np. Wędrowiec" value="' + esc(nick) + '">' +
    '<div class="sekcja">Załóż drużynę</div><button class="btn" data-a="zalozDruzyne">🏠 Załóż drużynę</button>' +
    '<div class="sekcja">…albo dołącz do kolegi</div><input class="pole" id="poleKod" maxlength="4" placeholder="KOD" autocapitalize="characters" value="' + esc(kodStartowy || '') + '" style="font-size:24px">' +
    '<button class="btn ziel" data-a="dolacz">🔗 Dołącz</button>' +
    '<div class="info-pole">Połączenie idzie bezpośrednio między telefonami. Gdy na danych komórkowych się nie łączy — spróbujcie na Wi-Fi. Gospodarz musi mieć grę otwartą na ekranie przez całą rozgrywkę.</div>' +
    '<button class="btn drugi" data-a="menu">◀ Menu</button></div>');
}
function zapamietajNick() { const el = $('poleNick'); if (el) { const n = el.value.trim().slice(0, 14); lStorSet('wiezien_nick', n); } }
AKCJE.zalozDruzyne = () => { zapamietajNick(); zalozDruzyne(0); };
AKCJE.dolacz = () => {
  zapamietajNick();
  const kod = ($('poleKod').value || '').trim().toUpperCase();
  if (kod.length !== 4) { toast('Wpisz 4-znakowy kod drużyny'); return; }
  dolaczDoDruzyny(kod);
};
function bladSieci(tekst) {
  zakonczSiec();
  pokazEkran('<div class="tytul">📡 Problem z połączeniem</div><div class="info-pole">' + tekst + '</div><button class="btn" data-a="online">Spróbuj jeszcze raz</button><button class="btn drugi" data-a="menu">◀ Menu</button>');
}
function opcjePeer() { return Object.assign({ debug: 1 }, window.__opcjePeer || {}); }

async function zalozDruzyne(proba) {
  pokazEkran('<div class="tytul">🏠 Zakładam drużynę…</div><div class="podtytul">Łączenie z serwerem pośredniczącym</div>');
  try { await zaladujPeerJS(); } catch (e) { bladSieci('Nie udało się wczytać modułu gry online. Sprawdź internet.'); return; }
  const kod = losowyKod(), P = klasaPeer();
  let peer;
  try { peer = new P(PREFIKS_PEER + kod, opcjePeer()); } catch (e) { bladSieci('Błąd: ' + e.message); return; }
  SIEC.peer = peer;
  peer.on('open', () => {
    Object.assign(SIEC, { rola: 'host', kod: kod, mojeId: 1, nastId: 1, polaczenia: {}, wGrze: false, gotowi: {}, dane: {} });
    SIEC.lobby = [{ id: 1, nick: mojNick(), klasa: mojaKlasa(), gotowy: true, host: true }];
    pokazLobby();
  });
  peer.on('connection', conn => obsluzKlienta(conn));
  peer.on('error', e => {
    if (e && e.type === 'unavailable-id' && proba < 4) { try { peer.destroy(); } catch (x) {} zalozDruzyne(proba + 1); return; }
    if (SIEC.rola === 'host' && e && (e.type === 'peer-unavailable' || e.type === 'webrtc')) return;   // pojedynczy klient - nie przerywamy gry
    if (!SIEC.wGrze) bladSieci('Nie udało się założyć drużyny (' + (e && e.type || 'błąd') + ').');
  });
  peer.on('disconnected', () => { try { if (!peer.destroyed) peer.reconnect(); } catch (e) {} });
}
function obsluzKlienta(conn) {
  // przyjęcie nowego gracza (przy otwarciu kanału albo przy pierwszej wiadomości - co będzie pierwsze)
  const przyjmij = () => {
    if (conn.idGracza) return true;
    if (conn._odrzucony) return false;
    let powod = '';
    if (SIEC.wGrze) powod = 'Gra już trwa — dołączyć można tylko przed startem.';
    else if (SIEC.lobby.length + Object.keys(SIEC.polaczenia).filter(id => !SIEC.lobby.some(l => String(l.id) === id)).length >= MAKS_GRACZY) powod = 'Drużyna jest pełna (maks. 4 osoby).';
    if (powod) { conn._odrzucony = true; wyslij(conn, { t: 'odmowa', powod: powod }); setTimeout(() => { try { conn.close(); } catch (e) {} }, 500); return false; }
    const id = ++SIEC.nastId;
    conn.idGracza = id; SIEC.polaczenia[id] = conn; SIEC.ostatnio[id] = Date.now();
    return true;
  };
  conn.on('open', przyjmij);
  conn.on('data', d => { if (!przyjmij()) return; try { odbierzSurowe(conn, d, m => odbierzOdKlienta(conn, m)); } catch (e) { zglosBlad(e, 'odbior'); } });
  conn.on('close', () => klientRozlaczony(conn.idGracza));
  conn.on('error', () => {});
}
async function dolaczDoDruzyny(kod) {
  pokazEkran('<div class="tytul">🔗 Łączę z drużyną ' + esc(kod) + '…</div><div class="podtytul">To może potrwać kilka sekund</div><button class="btn drugi" data-a="anulujSiec">Anuluj</button>');
  try { await zaladujPeerJS(); } catch (e) { bladSieci('Nie udało się wczytać modułu gry online. Sprawdź internet.'); return; }
  const P = klasaPeer(); let peer;
  try { peer = new P(undefined, opcjePeer()); } catch (e) { bladSieci('Błąd: ' + e.message); return; }
  SIEC.peer = peer;
  const limit = setTimeout(() => { if (SIEC.rola !== 'klient') bladSieci('Nie udało się połączyć z drużyną <b>' + esc(kod) + '</b>. Sprawdź kod i czy gospodarz ma otwartą grę.'); }, 15000);
  peer.on('open', () => {
    // 'raw' = czysty tekst (sami robimy JSON i dzielimy duże wiadomości); gdyby biblioteka go nie znała - 'json'
    let conn;
    try { conn = peer.connect(PREFIKS_PEER + kod, { reliable: true, serialization: 'raw' }); } catch (e) { conn = null; }
    if (!conn) conn = peer.connect(PREFIKS_PEER + kod, { reliable: true, serialization: 'json' });
    conn.on('open', () => {
      clearTimeout(limit);
      Object.assign(SIEC, { rola: 'klient', host: conn, kod: kod, wGrze: false });
      wyslij(conn, { t: 'witaj', nick: mojNick(), klasa: mojaKlasa() });
    });
    conn.on('data', d => { SIEC.ostOdHosta = Date.now(); try { odbierzSurowe(conn, d, odbierzOdHosta); } catch (e) { zglosBlad(e, 'odbiorH'); } });
    conn.on('close', () => { if (SIEC.rola === 'klient') hostRozlaczony(); });
    conn.on('error', () => {});
  });
  peer.on('error', e => {
    clearTimeout(limit);
    if (e && e.type === 'peer-unavailable') bladSieci('Nie ma drużyny o kodzie <b>' + esc(kod) + '</b>.');
    else if (SIEC.rola !== 'klient') bladSieci('Nie udało się połączyć (' + (e && e.type || 'błąd') + ').');
  });
}
AKCJE.anulujSiec = () => { zakonczSiec(); pokazOnline(); };
function zakonczSiec() {
  try { if (SIEC.peer) SIEC.peer.destroy(); } catch (e) {}
  pokazInfoSieci('');
  Object.assign(SIEC, { rola: null, peer: null, host: null, polaczenia: {}, wGrze: false, lobby: [], gotowi: {}, dane: {}, widokGraczy: [], mojWidok: null, znaneWrogi: {}, zdarzenia: [], zdarzeniaG: {} });
}
AKCJE.opuscDruzyne = () => pokazModal('<div class="tytul">Opuścić drużynę?</div><button class="btn czerw" data-a="opuscTak">Tak, wychodzę</button><button class="btn drugi" data-a="zamknijModal">Zostaję</button>');
AKCJE.opuscTak = () => { zamknijModal(); zakonczSiec(); pokazMenu(); };

// ---------- ekran lobby ----------
function pokazLobby() {
  const host = SIEC.rola === 'host';
  const ja = SIEC.lobby.find(l => l.id === SIEC.mojeId) || {};
  let h = '<div style="max-width:440px;margin:0 auto"><div class="tytul">👥 Drużyna</div>';
  h += '<div class="podtytul">Kod drużyny — podaj go kolegom:</div><div class="kod">' + esc(SIEC.kod) + '</div>';
  if (host) h += '<button class="btn drugi" data-a="udostepnij">📤 Wyślij zaproszenie</button>';
  h += '<div class="sekcja">Gracze (' + SIEC.lobby.length + '/' + MAKS_GRACZY + ')</div>';
  SIEC.lobby.forEach(l => {
    const K = KLASY[l.klasa] || KLASY.wiezniarka;
    h += '<div class="gracz-lobby"><span class="ik">' + K.ik + '</span><span class="n">' + esc(l.nick) + (l.id === SIEC.mojeId ? ' <small style="opacity:0.6">(Ty)</small>' : '') + '<br><small style="font-weight:700;opacity:0.7">' + K.n + '</small></span>' +
      '<span class="s" style="color:' + (l.host ? '#ffe08a' : (l.gotowy ? '#7ec98a' : '#a89878')) + '">' + (l.host ? '👑 gospodarz' : (l.gotowy ? '✔ gotowy' : '… wybiera')) + '</span></div>';
  });
  h += '<div class="sekcja">Twoja postać</div><div class="mini-klasy">';
  KLUCZE_KLAS.forEach(k => { h += '<div class="kafel' + (k === ja.klasa ? ' wybrany' : '') + '" data-a="lobbyKlasa" data-k="' + k + '" title="' + KLASY[k].n + '">' + htmlPortretu(k, 40) + '</div>'; });
  h += '</div>';
  if (ja.klasa && KLASY[ja.klasa]) h += '<div class="info-pole">' + opisKlasyHtml(KLASY[ja.klasa]) + '</div>';
  h += '<div class="info-pole" style="font-size:11.5px">💰✨ <b>Złoto i doświadczenie są wspólne</b>: każdy dostaje pełną wartość tego, co ktokolwiek z drużyny podniesie, a potem działają jego własne premie (zysk złota, doświadczenie, Midas…). Skrzynie też trafiają do każdego.</div>';
  h += '<div class="sekcja">Poziom zagrożenia</div>';
  if (host) {
    h += '<div class="mini-klasy">' + TRUDNOSCI.map((T, i) => '<div class="kafel' + (i === SIEC.trudnosc ? ' wybrany' : '') + '" data-a="lobbyTrudnosc" data-i="' + i + '"><div class="ik">' + T.ik + '</div></div>').join('') + '</div>';
    h += '<div class="podtytul" style="margin-top:6px">' + TRUDNOSCI[SIEC.trudnosc].n + '</div>';
    const wszyscy = SIEC.lobby.every(l => l.gotowy);
    h += '<button class="btn ziel" data-a="lobbyStart"' + (wszyscy ? '' : ' disabled') + '>▶ Start (' + SIEC.lobby.length + ' ' + (SIEC.lobby.length === 1 ? 'osoba' : 'osoby') + ')</button>';
    if (!wszyscy) h += '<div class="podtytul">Czekam, aż wszyscy będą gotowi.</div>';
  } else {
    h += '<div class="podtytul">' + TRUDNOSCI[SIEC.trudnosc].ik + ' ' + TRUDNOSCI[SIEC.trudnosc].n + ' (wybiera gospodarz)</div>';
    h += '<button class="btn ' + (ja.gotowy ? 'drugi' : 'ziel') + '" data-a="lobbyGotowy">' + (ja.gotowy ? '✋ Jeszcze chwila' : '✔ Gotowe!') + '</button>';
  }
  h += '<button class="btn czerw" data-a="opuscTak">🚪 Wyjdź</button></div>';
  pokazEkran(h, { zachowaj: true });
}
AKCJE.udostepnij = () => {
  let link = '';
  try { const L = window.parent.location; link = L.origin + L.pathname + '?pokoj=' + SIEC.kod; } catch (e) { link = ''; }
  const tekst = 'Zagraj ze mną w Więźnia Labiryntu! Kod drużyny: ' + SIEC.kod, calosc = link ? tekst + ' ' + link : tekst;
  const recznie = () => pokazModal('<div class="tytul">📤 Zaproszenie</div><div class="podtytul">Skopiuj i wyślij kolegom:</div>' +
    '<textarea class="pole" id="poleZapr" rows="3" readonly style="font-size:14px;text-align:left">' + esc(calosc) + '</textarea>' +
    '<button class="btn" data-a="kopiujZapr">📋 Kopiuj</button><button class="btn drugi" data-a="zamknijModal">Zamknij</button>');
  const kopiuj = () => { try { navigator.clipboard.writeText(calosc).then(() => toast('📋 Skopiowano zaproszenie'), recznie); } catch (e) { recznie(); } };
  // udostępnianie systemowe (najpierw z okna strony - ramka gry może nie mieć do tego uprawnień)
  let nav = null;
  try { if (window.parent !== window && window.parent.navigator.share) nav = window.parent.navigator; } catch (e) {}
  if (!nav && navigator.share) nav = navigator;
  if (nav) { nav.share({ title: 'Więzień Labiryntu', text: tekst, url: link || undefined }).catch(e => { if (!e || e.name !== 'AbortError') kopiuj(); }); return; }
  kopiuj();
};
AKCJE.kopiujZapr = () => {
  const el = $('poleZapr'); if (!el) return;
  el.focus(); el.select();
  let ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
  if (!ok) try { navigator.clipboard.writeText(el.value); ok = true; } catch (e) {}
  toast(ok ? '📋 Skopiowano' : 'Zaznacz tekst i skopiuj ręcznie');
};
AKCJE.lobbyKlasa = d => {
  lStorSet('wiezien_klasa_online', d.k);
  if (SIEC.rola === 'host') { const ja = SIEC.lobby.find(l => l.id === SIEC.mojeId); ja.klasa = d.k; rozeslijLobby(); pokazLobby(); }
  else { siecWyslijHost({ t: 'klasa', klasa: d.k }); const ja = SIEC.lobby.find(l => l.id === SIEC.mojeId); if (ja) { ja.klasa = d.k; pokazLobby(); } }
};
AKCJE.lobbyTrudnosc = d => { SIEC.trudnosc = +d.i; rozeslijLobby(); pokazLobby(); };
AKCJE.lobbyGotowy = () => { const ja = SIEC.lobby.find(l => l.id === SIEC.mojeId); if (!ja) return; ja.gotowy = !ja.gotowy; siecWyslijHost({ t: 'gotowyL', gotowy: ja.gotowy }); pokazLobby(); };
AKCJE.lobbyStart = () => {
  if (SIEC.rola !== 'host' || !SIEC.lobby.every(l => l.gotowy)) return;
  SIEC.wGrze = true; SIEC.gotowi = {}; SIEC.dane = {};
  rozeslij({ t: 'startGry', trudnosc: SIEC.trudnosc });
  rozpocznijRunDruzyny(SIEC.trudnosc);
};
function rozeslijLobby() { rozeslij({ t: 'lobby', lobby: SIEC.lobby, trudnosc: SIEC.trudnosc, kod: SIEC.kod }); }
function rozpocznijRunDruzyny(trudnosc) {
  const ja = SIEC.lobby.find(l => l.id === SIEC.mojeId) || {};
  rozpocznijRun(trudnosc, ja.klasa || mojaKlasa());
  gracz.nick = ja.nick || mojNick(); gracz.id = SIEC.mojeId;
}

// ---------------------------------------------------------------------
//  WIADOMOŚCI U GOSPODARZA
// ---------------------------------------------------------------------
function odbierzOdKlienta(conn, d) {
  const id = conn.idGracza; if (!id || !d) return;
  SIEC.ostatnio[id] = Date.now();
  const z0 = gracz;
  switch (d.t) {
    case 'ping': break;
    case 'witaj':
      if (SIEC.lobby.some(l => l.id === id)) break;
      SIEC.lobby.push({ id: id, nick: String(d.nick || 'Gracz').slice(0, 14), klasa: KLASY[d.klasa] ? d.klasa : 'wiezniarka', gotowy: false });
      wyslij(conn, { t: 'id', id: id });
      rozeslijLobby(); if (!SIEC.wGrze) pokazLobby();
      DZ.wybor();
      break;
    case 'klasa': { const l = SIEC.lobby.find(x => x.id === id); if (l && KLASY[d.klasa]) { l.klasa = d.klasa; rozeslijLobby(); if (!SIEC.wGrze) pokazLobby(); } break; }
    case 'gotowyL': { const l = SIEC.lobby.find(x => x.id === id); if (l) { l.gotowy = !!d.gotowy; rozeslijLobby(); if (!SIEC.wGrze) pokazLobby(); } break; }
    case 'poz': {
      const p = gracze.find(q => q.id === id);
      if (p && stan === 'walka' && !(d.n < (p.netN || 0))) {
        p.netN = d.n || 0; p.netX = +d.x || p.x; p.netY = +d.y || p.y; p.netVX = +d.vx || 0; p.netVY = +d.vy || 0; p.netT = performance.now(); p.netKX = d.kx;
        p.celKat = (d.c === null || d.c === undefined) ? null : +d.c;
      }
      break;
    }
    case 'zb': if (stan === 'walka' && fala.aktywna && Array.isArray(d.k)) d.k.slice(0, 80).forEach(i => zbierzLupPoId(+i)); break;
    case 'po': { const r = performance.now() - (+d.c || 0); if (r >= 0 && r < 5000) { const st = SIEC.rttG[id]; SIEC.rttG[id] = st ? st * 0.75 + r * 0.25 : r; const p = gracze.find(q => q.id === id); if (p) p.opoz = Math.min(0.15, SIEC.rttG[id] / 2000); } break; }
    case 'umi': { const p = gracze.find(q => q.id === id); if (p && stan === 'walka') { kontekst(p); p.umiKier = Array.isArray(d.k) ? [+d.k[0] || 0, +d.k[1] || 0] : null; uzyjUmiejetnosci(d.n === 2 ? 2 : 1); kontekst(z0); } break; }
    case 'niegotowy':
      // klient chce wrócić do sklepu - tylko dopóki fala nie ruszyła
      if (SIEC.wGrze && stan === 'przerwa' && SIEC.gotowi[id]) {
        delete SIEC.gotowi[id]; delete SIEC.dane[id];
        wyslij(conn, { t: 'wrocDoSklepu' });
        odswiezCzekanieHosta();
      }
      break;
    case 'gotowy':
      // spóźniony gracz (drużyna ruszyła bez niego) dołącza do trwającej fali
      if (SIEC.wGrze && stan === 'walka' && fala.aktywna) { if (!gracze.some(q => q.id === id)) dolaczWTrakcie(id, conn, d); break; }
      SIEC.dane[id] = { gracz: d.gracz, run: d.run };
      SIEC.gotowi[id] = true;
      sprawdzStartFali();
      break;
  }
  kontekst(z0);
}
function klientRozlaczony(id) {
  if (!id || SIEC.rola !== 'host') return;
  delete SIEC.polaczenia[id];
  const l = SIEC.lobby.find(x => x.id === id);
  SIEC.lobby = SIEC.lobby.filter(x => x.id !== id);
  delete SIEC.gotowi[id]; delete SIEC.dane[id]; delete SIEC.ostatnio[id];
  if (l) toast('👋 ' + l.nick + ' opuszcza drużynę');
  const idx = gracze.findIndex(p => p.id === id);
  if (idx > 0) { gracze.splice(idx, 1); wrogowie.forEach(w => { if (w.cel && w.cel.id === id) w.cel = null; }); }
  rozeslijLobby();
  if (!SIEC.wGrze) pokazLobby();
  else if (stan === 'przerwa') sprawdzStartFali();
  if (SIEC.wGrze && stan === 'walka' && !zywiGracze().length) koniecDruzyny();
}

// Gotowość do kolejnej fali (po sklepie)
function gotowyDoFali(nr) {
  if (SIEC.rola === 'klient') {
    siecWyslijHost({ t: 'gotowy', nr: nr, gracz: czyste(gracz, 0), run: czyste(run, 0) });
    SIEC.czekam = true; pokazCzekanie(); return;
  }
  if (SIEC.rola === 'host') { SIEC.gotowi[SIEC.mojeId] = true; SIEC.nastepnaFala = nr; sprawdzStartFali(); return; }
  // drużyna lokalna (testy): każdy gracz po kolei przechodzi swoje ekrany przerwy
  const nast = gracze.find(p => p !== gracz && p._run && p._run.przerwa);
  if (nast) { kontekst(nast); kolejkaPrzerwy(); return; }
  kontekst(lokalny); zamknijEkran(); startFali(nr);
}
function sprawdzStartFali(wymus) {
  if (SIEC.rola !== 'host' || !SIEC.wGrze || stan !== 'przerwa') return;
  const ids = SIEC.lobby.map(l => l.id);
  const wszyscy = ids.every(id => SIEC.gotowi[id]);
  rozeslij({ t: 'czekam', gotowi: ids.filter(id => SIEC.gotowi[id]) });
  if (!SIEC.gotowi[SIEC.mojeId]) return;
  if (!wszyscy && !wymus) { if (!SIEC.czekamHost) SIEC.tCzekania = Date.now(); SIEC.czekamHost = true; pokazCzekanie(); return; }
  SIEC.czekamHost = false;
  // budujemy drużynę: gospodarz + postacie klientów z ich danych
  const z0 = lokalny;
  const nowi = [lokalny];
  ids.forEach(id => { if (id === SIEC.mojeId) return; const dane = SIEC.dane[id]; if (dane) nowi.push(zbudujZdalnego(id, dane)); });
  gracze = nowi;
  kontekst(z0);
  SIEC.gotowi = {}; SIEC.dane = {}; SIEC.cofnijPrzerwe = null;
  zamknijEkran();
  startFali(SIEC.nastepnaFala);
}
function odswiezCzekanieHosta() {
  const ids = SIEC.lobby.map(l => l.id);
  rozeslij({ t: 'czekam', gotowi: ids.filter(id => SIEC.gotowi[id]) });
  if (SIEC.czekamHost && stan === 'przerwa' && !$('modal').classList.contains('widoczny')) pokazCzekanie();
}
// Cofnięcie gotowości: wracasz do sklepu (ten sam sklep, te same oferty), dopóki fala nie ruszyła
function wrocDoSklepu() {
  const p = SIEC.cofnijPrzerwe; if (!p) return;
  SIEC.cofnijPrzerwe = null; SIEC.czekam = false; SIEC.cofam = false;
  p.sklep = false; run.przerwa = p;
  zamknijModal(); kolejkaPrzerwy();
}
AKCJE.cofnijGotowosc = () => {
  if (stan !== 'przerwa' || !SIEC.cofnijPrzerwe) return;
  if (SIEC.rola === 'klient') {
    if (!SIEC.czekam || SIEC.cofam) return;
    SIEC.cofam = true; siecWyslijHost({ t: 'niegotowy' });
    pokazEkran('<div class="tytul">🛒 Wracam do sklepu…</div><div class="podtytul">Jeśli fala zdążyła ruszyć, dołączysz do walki.</div>');
    return;
  }
  if (SIEC.rola === 'host') {
    delete SIEC.gotowi[SIEC.mojeId]; SIEC.czekamHost = false;
    odswiezCzekanieHosta(); wrocDoSklepu();
  }
};
// Gospodarz nie czeka na maruderów: fala rusza, a oni dołączą, gdy skończą zakupy
AKCJE.startBezNich = () => pokazModal('<div class="tytul">Zacząć bez nich?</div><div class="podtytul">Fala ruszy od razu. Kto jeszcze robi zakupy, dołączy do walki, gdy skończy.</div>' +
  '<button class="btn ziel" data-a="startBezNichTak">⏩ Tak, startujemy</button><button class="btn drugi" data-a="zamknijModal">Czekamy dalej</button>');
AKCJE.startBezNichTak = () => { zamknijModal(); sprawdzStartFali(true); };
function dolaczWTrakcie(id, conn, d) {
  const z0 = lokalny;
  const p = zbudujZdalnego(id, { gracz: d.gracz, run: d.run });
  kontekst(p);
  const kotw = zywiGracze()[0] || lokalny;
  p.x = ogr(kotw.x + losowo(-50, 50), POD_MIN, POD_MAX); p.y = ogr(kotw.y + losowo(-50, 50), POD_MIN, POD_MAX); p.netX = undefined;
  p.tarcze = []; p.zastoj = 0; p.niewr = 2; p.spowG = 0; p.powalony = false; p.reanim = 0;
  run.zlotoFali = 0; run.trafFali = 0; run.spoznionyFala = fala.nr; run.falaMaks = Math.max(run.falaMaks || 0, fala.nr);
  zastosujStaty(); p.hp = D.hpMax; hak('naStartFali'); zastosujStaty();
  kontekst(z0);
  gracze.push(p);
  wrogowie.forEach(w => w._w = false);           // nowy gracz musi poznać wszystkich wrogów
  SIEC.zal[id] = { ln: kulki.map(k => lupDoWyslania(k, 0)).concat(monety.map(m => lupDoWyslania(m, 1))) };
  const poz = {}; poz[id] = [Math.round(p.x), Math.round(p.y)];
  wyslij(conn, { t: 'start', nr: fala.nr, dlugosc: fala.dlugosc, boss: fala.boss, specjalna: fala.specjalna, proba: fala.proba ? fala.proba.id : '', poz: poz, wTrakcie: 1 });
  baner('⚔️ ' + esc(p.nick) + ' dołącza do walki!', '');
}
function zbudujZdalnego(id, dane) {
  const z0 = gracz;
  const l = SIEC.lobby.find(x => x.id === id) || {};
  const p = nowyGracz(dane.gracz.klasa || 'wiezniarka');
  Object.assign(p, dane.gracz);
  p._run = dane.run || { trudnosc: SIEC.trudnosc, zrodla: {} }; p._run.zrodla = p._run.zrodla || {};
  p.id = id; p.zdalny = true; p.nick = l.nick || p.nick || 'Gracz';
  p.tarcze = []; p.buffy = {}; p.augmentyDoWyboru = p.augmentyDoWyboru || []; p.skrzynie = p.skrzynie || [];
  p.przedmioty = (p.przedmioty || []).filter(q => q && DEF_PRZ[q.id]); p.augmenty = (p.augmenty || []).filter(a => a && DEF_AUG[a.id]);
  p.oreze = (p.oreze || []).filter(o => o && DEF_ORE[o.id]); p.bronie = (p.bronie || []).filter(b => b && BRONIE[b.rodzaj]); p.umi = { cd: 0, cdMax: 0 }; p.umi2 = { cd: 0, cdMax: 0 }; p.dash = null;
  p._D = null; p._brudne = true;
  gracz = p; D = null; run = p._run;
  przebudujHaki(); zastosujStaty();
  kontekst(z0);
  return p;
}
function statusCzekania() {
  const gotowi = SIEC.ostGotowi || [], teraz = Date.now();
  return (SIEC.lobby || []).map(l => {
    const ok = SIEC.rola === 'host' ? !!SIEC.gotowi[l.id] : gotowi.indexOf(l.id) >= 0;
    const cisza = SIEC.rola === 'host' && l.id !== SIEC.mojeId && !ok && teraz - (SIEC.ostatnio[l.id] || teraz) > 8000;
    return [l, ok, cisza];
  });
}
function pokazCzekanie() {
  const st = statusCzekania();
  SIEC.podpisCzekania = st.map(x => x[0].id + ':' + (x[1] ? 1 : 0) + (x[2] ? 1 : 0)).join(',');
  let h = '<div class="tytul">⏳ Czekamy na drużynę</div><div class="podtytul">Następna fala ruszy, gdy wszyscy skończą zakupy.</div>';
  st.forEach(([l, ok, cisza]) => {
    h += '<div class="gracz-lobby"><span class="ik">' + (KLASY[l.klasa] || KLASY.wiezniarka).ik + '</span><span class="n">' + esc(l.nick) + '</span><span class="s" style="color:' + (ok ? '#7ec98a' : (cisza ? '#ff8a7a' : '#a89878')) + '">' + (ok ? '✔ gotowy' : (cisza ? '📡 nie odpowiada' : '… w sklepie')) + '</span></div>';
  });
  if (SIEC.rola === 'host' && st.some(x => !x[1])) h += '<button class="btn ziel" data-a="startBezNich">⏩ Zacznij bez nich</button>';
  h += '<button class="btn drugi" data-a="modalBuild">🎒 Mój build</button>';
  if (SIEC.cofnijPrzerwe) h += '<button class="btn drugi" data-a="cofnijGotowosc">◀ Wróć do sklepu</button>';
  pokazEkran(h);
}

// Koniec fali u gospodarza: każdy klient dostaje swoją postać do przerwy
function siecKoniecFali() {
  SIEC.gotowi = {}; SIEC.dane = {}; SIEC.czekamHost = false;
  gracze.forEach(p => {
    if (!p.zdalny) return;
    const conn = SIEC.polaczenia[p.id]; if (!conn) return;
    wyslij(conn, { t: 'przerwa', nr: fala.nr, gracz: czyste(p, 0), run: czyste(p._run, 0), zdarzenia: SIEC.zdarzeniaG[p.id] || [] });
    SIEC.zdarzeniaG[p.id] = [];
  });
}
function siecStartFali() {
  const poz = {}; gracze.forEach(p => poz[p.id] = [Math.round(p.x), Math.round(p.y)]);
  // tylko do tych, którzy wchodzą do tej fali (maruderzy jeszcze robią zakupy)
  const msg = { t: 'start', nr: fala.nr, dlugosc: fala.dlugosc, boss: fala.boss, specjalna: fala.specjalna, proba: fala.proba ? fala.proba.id : '', poz: poz };
  gracze.forEach(p => { if (p.zdalny) wyslij(SIEC.polaczenia[p.id], msg); });
  SIEC.zdarzenia = []; SIEC.dzwieki = []; SIEC.zal = {}; SIEC.lupOst = new Set();
  wrogowie.forEach(w => w._w = false);
}
function koniecDruzyny() {
  if (stan === 'smierc') return;
  stan = 'smierc'; fala.aktywna = false;
  const z0 = gracz;
  const lista = gracze.map(p => {
    const r = p._run || {};
    return { nick: p.nick, klasa: p.klasa, poziom: p.poziom, zabici: r.zabici || 0, zadane: Math.round(r.zadane || 0), przyjete: Math.round(r.przyjete || 0),
      top: Object.keys(r.zrodla || {}).map(k => [k, Math.round(r.zrodla[k])]).sort((a, b) => b[1] - a[1]).slice(0, 4) };
  });
  kontekst(z0);
  const dane = { fala: fala.nr, trudnosc: run.trudnosc, lista: lista };
  if (SIEC.rola === 'host') rozeslij({ t: 'koniec', dane: dane });
  DZ.smierc();
  setTimeout(() => pokazKoniecDruzyny(dane), 1300);
}
function pokazKoniecDruzyny(d) {
  const T = TRUDNOSCI[d.trudnosc] || TRUDNOSCI[1];
  let h = '<div class="tytul duzy" style="margin-top:8px">💀 Drużyna poległa</div><div class="podtytul">' + T.ik + ' ' + T.n + '</div>' +
    '<div class="karta az" style="text-align:center"><div style="font-size:15px;color:#d8cdb0">Dotarliście do fali</div><div style="font-size:54px;font-weight:900;color:#ffe08a;line-height:1.1">' + d.fala + '</div></div>';
  const maks = Math.max(1, ...d.lista.map(x => x.zadane));
  d.lista.forEach(x => {
    const K = KLASY[x.klasa] || KLASY.wiezniarka;
    h += '<div class="karta t1"><div class="karta-gora"><div class="karta-ik">' + K.ik + '</div><div><div class="karta-nazwa">' + esc(x.nick) + '</div><div class="karta-tier">' + K.n + ' · poziom ' + x.poziom + '</div></div></div>' +
      '<div class="karta-opis">⚔️ Zabici <b>' + x.zabici + '</b> · 💥 Zadane <b>' + fmtK(x.zadane) + '</b> · 🩸 Przyjęte <b>' + fmtK(x.przyjete) + '</b></div>' +
      '<div style="background:rgba(255,255,255,0.06);border-radius:4px;margin-top:6px"><div class="wykres-pas" style="width:' + Math.max(2, x.zadane / maks * 100) + '%"></div></div>' +
      '<div class="karta-opis" style="font-size:11px">' + x.top.map(t => esc(t[0]) + ': ' + fmtK(t[1])).join(' · ') + '</div></div>';
  });
  h += '<button class="btn" data-a="opuscTak">◀ Menu</button>';
  pokazEkran(h);
}

// ---------------------------------------------------------------------
//  STAN GRY WYSYŁANY PRZEZ GOSPODARZA (ok. 15 razy na sekundę)
// ---------------------------------------------------------------------
function r1(v) { return Math.round(v); }
// kulki doświadczenia (0) i monety (1): nowe wysyłamy raz, potem tylko informację, że zniknęły
function lupDoWyslania(l, typ) { return [l.id, r1(l.x), r1(l.y), r1(l.vx || 0), r1(l.vy || 0), typ, Math.round((typ ? l.v : l.xp) * 10) / 10, Math.round(Math.max(0, l.opozn || 0) * 100)]; }
const LIMITY_ZAL = { vf: 40, vt: 90, vb: 40, vc: 40, vs: 30, dz: 12, e: 200 };
function siecWyslijStan(dt) {
  SIEC.tWysylki -= dt;
  if (SIEC.tWysylki > 0) return;
  // przy tłoku na ekranie rzadziej (mniej danych), normalnie 15 razy na sekundę
  SIEC.tWysylki = wrogowie.length + pociski.length + pociskiWrogow.length > 160 ? 1 / 10 : 1 / 15;
  const ids = Object.keys(SIEC.polaczenia);
  if (!ids.length) return;
  SIEC.licznikStanu++;
  const z0 = gracz;
  const G = graczeDoRysowania().map(p => [p.id, r1(p.x), r1(p.y), r1(Math.max(0, p.hp)), r1(p.hpMaxR || 100), r1(p.ts || 0), p.kierX < 0 ? -1 : 1, p.wRuchu ? 1 : 0,
    (p.zastoj > 0 ? 1 : 0) | (p.niewr > 0 ? 2 : 0) | (p.migotanie > 0 ? 4 : 0) | (p.powalony ? 8 : 0) | (p.niewidzialny > 0 ? 16 : 0) | (p.forma === 'nietoperz' ? 32 : 0) | (p.stanKlasy && p.stanKlasy.wir ? 64 : 0) | (p.stanKlasy && p.stanKlasy.salwa > czasGry ? 128 : 0), r1((p.reanim || 0) * 10), r1((p.roz || 1) * 100), p.klasa, p.nick,
    p.bronie.map(b => [b.rodzaj, b.tier, r1((b.kat || 0) * 100), b.anim > 0 ? 1 : 0]), r1((p.blysk || 0) * 10)]);
  kontekst(z0);
  const W = [], WN = [];
  for (const w of wrogowie) {
    if (w.martwy) continue;
    const fl = (w.elita ? 1 : 0) | (w.boss ? 2 : 0) | (w.zauroczony > 0 ? 4 : 0) | (w.sojusznik ? 8 : 0) | (w.trafiony > 0 ? 16 : 0) | (w.duch ? 32 : 0) |
      (w.przygotowanie > 0 ? 64 : 0) | (w.spow > 0 && w.spowCzas > 0 ? 128 : 0) | (w.ogl > 0 ? 256 : 0) | (w.ogien ? 512 : 0) | (w.krew ? 1024 : 0) |
      (w.naznaczony > 0 ? 2048 : 0) | (w.pole ? 4096 : 0) | (w.czempion ? 8192 : 0);
    W.push([w.id, r1(w.x), r1(w.y), r1(w.hp / w.hpMax * 1000), fl, r1(w.wysokosc || 0), w.tarczaMax ? r1(w.tarcza / w.tarczaMax * 100) : -1, w.boss ? r1(w.hp) : 0,
      w.zamach > 0 && w.zamachMax ? Math.max(1, r1((1 - w.zamach / w.zamachMax) * 100)) : 0, r1((w.zamKat || 0) * 100)]);
    if (!w._w) { w._w = true; WN.push([w.id, r1(w.r), w.ik, w.kolor, w.obraz || '', w.afiksy.map(a => AFIKSY[a].ik).join(''), w.boss ? w.n : '', w.poswiata || '']); }
    else if (w.boss && w._posw !== w.poswiata) { w._posw = w.poswiata; WN.push([w.id, r1(w.r), w.ik, w.kolor, '', '', w.n, w.poswiata || '']); }
  }
  const nowe = (lista, fn) => { const o = []; for (const e of lista) if (!e._w) { e._w = true; o.push(fn(e)); } return o; };
  // to, co pojawiło się w tej klatce (efekty, zdarzenia, nowe kulki/monety, zebrane łupy)
  const swieze = {
    wn: WN,
    vf: nowe(fale, f => [r1(f.x), r1(f.y), r1(f.r), f.kolor, f.czas, f.max, f.odwrot ? 1 : 0, f.slaba ? 1 : 0]),
    vt: nowe(teksty, t => [r1(t.x), r1(t.y), t.t, t.kolor, t.czas, t.max, t.rozm, t.o || 0]),
    vb: nowe(blyskawice, b => (b.a || [0, 0, 0, 0]).concat([b.kolor])),
    vc: nowe(ciecia, c => [r1(c.x), r1(c.y), r1(c.kat * 100), r1(c.luk * 100), r1(c.r), c.max, c.kolor, c.linia ? 1 : 0]),
    vs: nowe(stozki, s => [r1(s.x), r1(s.y), r1(s.kat * 100), r1(s.r), r1(s.pol * 100), s.max, s.kolor]),
    e: SIEC.zdarzenia, dz: SIEC.dzwieki,
    ln: [], lu: [],
  };
  const teraz = new Set();
  kulki.forEach(k => { teraz.add(k.id); if (!k._w) { k._w = true; swieze.ln.push(lupDoWyslania(k, 0)); } });
  monety.forEach(m => { teraz.add(m.id); if (!m._w) { m._w = true; swieze.ln.push(lupDoWyslania(m, 1)); } });
  SIEC.lupOst.forEach(id => { if (!teraz.has(id)) swieze.lu.push(id); });
  SIEC.lupOst = teraz;
  SIEC.zdarzenia = []; SIEC.dzwieki = [];
  const stanW = {
    t: 's', n: SIEC.licznikStanu, tc: Math.round(czasGry * 1000),
    f: [fala.nr, r1(fala.czas * 10), r1(fala.dlugosc), fala.boss ? 1 : 0, fala.specjalna || '', fala.proba ? fala.proba.id : '', fala.ciemnosc ? 1 : 0],
    g: G, w: W,
    p: pociski.map(p => [r1(p.x), r1(p.y), r1(p.vx), r1(p.vy), p.kolor, (p.ksztalt || 'kula') + (p.duza ? '+' : ''), r1((p.obrot || 0) * 10)]),
    pw: pociskiWrogow.map(p => [r1(p.x), r1(p.y), r1(p.vx), r1(p.vy), p.kolor, p.ksztalt || '', p.r || 5, p.siec ? 1 : 0]),
    sk: skrzynieNaZiemi.map(s => [r1(s.x), r1(s.y), s.tier]),
    kal: kaluze.map(k => [r1(k.x), r1(k.y), r1(k.r), r1(k.czas / k.max * 100), k.rodzaj]),
    bm: bomby.map(b => [r1(b.x), r1(b.y), r1(b.r), r1(b.lont / b.max * 100)]),
    ub: uderzeniaBossa.map(u => [r1(u.x), r1(u.y), r1(u.r), r1(u.czas / u.zapowiedz * 100), u.mroz ? 1 : 0, u.zadane ? 1 : 0]),
    wr: wiry.map(w => [r1(w.x), r1(w.y), r1(w.r), r1(w.czas * 10), r1(w.max * 10), r1(w.rozruch * 100), r1(w.faza * 10)]),
    sc: scianyMagiczne.map(s => [r1(s.x1), r1(s.y1), r1(s.x2), r1(s.y2), r1(s.czas * 10), r1(s.max * 10), s.grubosc]),
    zap: zapowiedzi.map(z => [r1(z.x), r1(z.y), r1(z.czas / z.max * 100), z.opcje && z.opcje.elita ? 1 : 0]),
    ec: efektyCzasowe.map(e => [e.rodzaj, r1(e.x), r1(e.y), r1(e.r || 0), r1(e.czas / e.max * 100), r1(e.sx || 0), r1(e.sy || 0)]),
    pe: polaEfektow.map(p => [r1(p.x), r1(p.y), r1(p.r), r1(p.czas * 10), p.rodzaj || '']),
    st: stwory.map(s => [s.typ, r1(s.x), r1(s.y), s.max > 9000 ? -1 : r1(s.czas / s.max * 100), r1((s.kat || 0) * 100), r1(s.r || 0), s.ik, r1(s.aura || 0)]),
    ob: orbyRys.map(o => [r1(o.x), r1(o.y), o.kolor, r1(o.kat * 100)]),
  };
  // co 2 s pełna lista łupów - gdyby coś się rozjechało, klient sam to naprawi
  if (SIEC.licznikStanu % 30 === 0) { stanW.la = []; kulki.forEach(k => stanW.la.push(lupDoWyslania(k, 0))); monety.forEach(m => stanW.la.push(lupDoWyslania(m, 1))); }
  for (const id of ids) {
    const conn = SIEC.polaczenia[id];
    const p = gracze.find(q => String(q.id) === String(id));
    if (!conn || !p) continue;
    // zaległości dla tego klienta: jeśli jego kanał jest zapchany, nic nie ginie - pójdzie w następnej klatce
    const q = SIEC.zal[id] || (SIEC.zal[id] = {});
    for (const k in swieze) { const a = q[k] || (q[k] = []); for (const x of swieze[k]) a.push(x); if (LIMITY_ZAL[k] && a.length > LIMITY_ZAL[k]) a.splice(0, a.length - LIMITY_ZAL[k]); }
    if (zatkane(conn)) continue;
    kontekst(p);
    stanW.ja = { hp: r1(p.hp), hpMax: D.hpMax, ts: r1(tarczaSuma()), xp: r1(p.xp), xpNast: p.xpNast, poziom: p.poziom, zloto: Math.floor(p.zloto), en: p.maEnergie ? Math.round(p.energia || 0) : -1,
      sk: p.skrzynie.length, dw: p.doWyboru, prz: p.przedmioty.map(q => q ? [Math.round((q.cd || 0) * 10) / 10, Math.round((q.cdMax || 0) * 10) / 10] : [0, 0]),
      ms: r1(D.ms), roz: rozmiarGracza(), spowG: p.spowG, zastoj: p.zastoj > 0 ? 1 : 0, pow: p.powalony ? 1 : 0, niewr: p.niewr > 0 ? 1 : 0, zb: r1(D.zbieranie),
      rtt: r1(SIEC.rttG[id] || 0),
      umi: [Math.round((p.umi.cd || 0) * 10) / 10, Math.round((p.umi.cdMax || 0) * 10) / 10], umi2: p.umi2 ? [Math.round((p.umi2.cd || 0) * 10) / 10, Math.round((p.umi2.cdMax || 0) * 10) / 10] : null, ua: [czyUmiAktywna(1) ? 1 : 0, czyUmiAktywna(2) ? 1 : 0], ore: p.oreze.map(q => [Math.round((q.cd || 0) * 10) / 10, Math.round((q.cdMax || 0) * 10) / 10]) };
    for (const k in q) stanW[k] = q[k];
    stanW.eg = SIEC.zdarzeniaG[p.id] || [];
    const txt = JSON.stringify(stanW);
    if (wyslij(conn, txt)) { conn._ostStan = txt.length; SIEC.zal[id] = {}; SIEC.zdarzeniaG[p.id] = []; }
  }
  kontekst(z0);
}

// ---------------------------------------------------------------------
//  KLIENT: odbiór wiadomości i stanu
// ---------------------------------------------------------------------
function odbierzOdHosta(d) {
  if (!d) return;
  switch (d.t) {
    case 'id': SIEC.mojeId = d.id; break;
    case 'odmowa': bladSieci(esc(d.powod || 'Gospodarz odrzucił połączenie.')); break;
    case 'lobby':
      SIEC.lobby = d.lobby || []; SIEC.trudnosc = d.trudnosc; SIEC.kod = d.kod || SIEC.kod;
      if (!SIEC.wGrze) pokazLobby();
      break;
    case 'startGry':
      SIEC.wGrze = true; SIEC.trudnosc = d.trudnosc;
      rozpocznijRunDruzyny(d.trudnosc);
      break;
    case 'czekam': SIEC.ostGotowi = d.gotowi || []; if (SIEC.czekam && !SIEC.cofam && stan === 'przerwa') pokazCzekanie(); break;
    case 'wrocDoSklepu': if (stan === 'przerwa' && SIEC.czekam) wrocDoSklepu(); break;
    case 'ping': break;
    case 'pp': siecWyslijHost({ t: 'po', c: d.c }); break;
    case 'start': klientStartFali(d); break;
    case 's': klientStan(d); break;
    case 'przerwa': klientPrzerwa(d); break;
    case 'koniec': stan = 'smierc'; DZ.smierc(); setTimeout(() => pokazKoniecDruzyny(d.dane), 900); break;
  }
}
function hostRozlaczony() {
  const wGrze = SIEC.wGrze;
  zakonczSiec();
  if (stan === 'smierc') return;
  stan = 'menu';
  pokazEkran('<div class="tytul">📡 Utracono połączenie</div><div class="info-pole">Gospodarz zamknął grę albo stracił internet.' + (wGrze ? ' Ta rozgrywka niestety się skończyła.' : '') + '</div><button class="btn" data-a="menu">◀ Menu</button>');
}
function klientStartFali(d) {
  SIEC.czekam = false; SIEC.cofam = false; SIEC.cofnijPrzerwe = null;
  fala = { nr: d.nr, aktywna: true, czas: 0, dlugosc: d.dlugosc, boss: !!d.boss, specjalna: d.specjalna || null, proba: d.proba ? DEF_PROB[d.proba] : null };
  [wrogowie, pociski, pociskiWrogow, kulki, monety, skrzynieNaZiemi, kaluze, polaEfektow, wiry, scianyMagiczne, bomby, uderzeniaBossa, zapowiedzi,
    efektyCzasowe, czastki, teksty, fale, blyskawice, ciecia, stozki, orbyRys].forEach(l => l.length = 0);
  SIEC.znaneWrogi = {}; SIEC.widokGraczy = []; SIEC.stwory = []; SIEC.ostN = 0; SIEC.zebraneLok = {};
  const p = d.poz && d.poz[SIEC.mojeId];
  if (p) { gracz.x = p[0]; gracz.y = p[1]; }
  gracz.zastoj = 0; gracz.spowG = 0; gracz.powalony = false;
  stan = 'walka'; zamknijEkran(); zamknijModal();
  let pod = '';
  if (fala.boss) pod = '⚠️ BOSS!'; else if (fala.specjalna && SPECJALNE[fala.specjalna]) pod = SPECJALNE[fala.specjalna].ik + ' ' + SPECJALNE[fala.specjalna].n;
  if (fala.proba) pod = (pod ? pod + '<br>' : '') + fala.proba.ik + ' ' + fala.proba.n;
  if (d.wTrakcie) { baner('⚔️ Dołączasz do walki!', 'Fala ' + d.nr); DZ.fala(); }
  else { baner('🌊 Fala ' + d.nr, pod || 'przetrwajcie!'); DZ.fala(); }
  ustawKamere();
}
function klientPrzerwa(d) {
  // gospodarz oddaje mi moją postać: od teraz to ja ją zmieniam (sklep, augmenty...)
  run = d.run || run; run.zrodla = run.zrodla || {};
  const g = nowyGracz(d.gracz.klasa); Object.assign(g, d.gracz);
  g.tarcze = []; g.buffy = {}; g.zdalny = false; g.id = SIEC.mojeId; g._run = run; g.powalony = false;
  g.przedmioty = (g.przedmioty || []).filter(q => q && DEF_PRZ[q.id]); g.augmenty = (g.augmenty || []).filter(a => a && DEF_AUG[a.id]);
  g.oreze = (g.oreze || []).filter(o => o && DEF_ORE[o.id]); g.umi = { cd: 0, cdMax: 0 }; g.umi2 = { cd: 0, cdMax: 0 }; g.dash = null;
  gracz = g; gracze = [g]; lokalny = g; D = null;
  przebudujHaki(); zastosujStaty();
  fala = { nr: d.nr, aktywna: false };
  stan = 'przerwa'; SIEC.czekam = false;
  (d.zdarzenia || []).forEach(zastosujZdarzenie);
  DZ.zwyciestwo(); baner('✅ Fala ' + d.nr + ' przetrwana!', '');
  setTimeout(() => { if (stan === 'przerwa') kolejkaPrzerwy(); }, 1100);
}
function zastosujZdarzenie(e) {
  switch (e[0]) {
    case 'r': rozbryzg(e[1], e[2], e[3], e[4]); break;
    case 'l': czastkiLeczenia(e[1], e[2]); break;
    case 'ban': baner(e[1], e[2]); break;
    case 'toast': toast(e[1]); break;
    case 'dz': dziennik(e[1]); break;
    case 's': if (DZ[e[1]]) DZ[e[1]](); break;
    case 'ssij': kulki.forEach(k => k.ssij = true); monety.forEach(m => m.ssij = true); break;
    case 'dash': if (gracz && stan === 'walka') gracz.dash = { vx: e[1] / 100 * e[3] / 0.2, vy: e[2] / 100 * e[3] / 0.2, t: 0.2 }; break;
    case 'korzen': if (gracz && stan === 'walka') gracz.korzen = e[1] / 10; break;
  }
}
// Klient pokazuje wrogów i innych graczy "na teraz": z dwóch ostatnich stanów liczy prędkość
// i przesuwa ich do przodu o czas, jaki minął (plus połowę pingu), zamiast pokazywać spóźniony obraz.
function wyprzedzenie() { return Math.min(0.12, (SIEC.rtt || 0) / 2000); }
function przyjmijPozycje(o, x, y, tH, teraz) {
  if (o.sT !== undefined && tH > o.sT) {
    const dtH = tH - o.sT, dx = x - o.sx, dy = y - o.sy;
    if (Math.hypot(dx, dy) > 160) { o.x = x; o.y = y; o.vx = 0; o.vy = 0; }          // teleport (np. mignięcie bossa)
    else { const vx = dx / dtH, vy = dy / dtH; o.vx = o.vx === undefined ? vx : o.vx * 0.35 + vx * 0.65; o.vy = o.vy === undefined ? vy : o.vy * 0.35 + vy * 0.65; }
    const v = Math.hypot(o.vx, o.vy); if (v > 700) { o.vx *= 700 / v; o.vy *= 700 / v; }
  } else if (o.sT === undefined) { o.vx = 0; o.vy = 0; }
  o.sx = x; o.sy = y; o.sT = tH; o.tOdb = teraz;
}
function przesunDoTeraz(o, teraz, k) {
  if (o.sT === undefined) return;
  const wiek = Math.min(0.25, (teraz - o.tOdb) / 1000 + wyprzedzenie());
  const tx = o.sx + (o.vx || 0) * wiek, ty = o.sy + (o.vy || 0) * wiek;
  o.x += (tx - o.x) * k; o.y += (ty - o.y) * k;
}
function klientStan(d) {
  if (stan !== 'walka') return;
  if (d.n && SIEC.ostN && d.n <= SIEC.ostN) return;
  SIEC.ostN = d.n; SIEC.ostStan = d;
  const teraz = performance.now(), tH = (d.tc || 0) / 1000, wyp = wyprzedzenie();
  const f = d.f; fala.nr = f[0]; fala.czas = f[1] / 10; fala.dlugosc = f[2]; fala.boss = !!f[3]; fala.specjalna = f[4] || null; fala.ciemnosc = !!f[6];
  // gracze
  const stare = {}; SIEC.widokGraczy.forEach(p => stare[p.id] = p);
  SIEC.widokGraczy = d.g.map(a => {
    const id = a[0], ja = id === SIEC.mojeId;
    const p = stare[id] || { id: id, x: a[1], y: a[2], faza: 0 };
    if (!ja) przyjmijPozycje(p, a[1], a[2], tH, teraz);
    p.hp = a[3]; p.hpMaxR = a[4]; p.ts = a[5]; p.kierX = a[6]; p.wRuchu = !!a[7];
    p.zastoj = a[8] & 1 ? 1 : 0; p.niewr = a[8] & 2 ? 1 : 0; p.migotanie = a[8] & 4 ? 0.1 : 0; p.powalony = !!(a[8] & 8);
    p.niewidzialny = a[8] & 16 ? 1 : 0; p.batAkt = !!(a[8] & 32); p.wirAkt = !!(a[8] & 64); p.salwaAkt = !!(a[8] & 128);
    p.reanim = a[9] / 10; p.roz = a[10] / 100; p.klasa = a[11]; p.nick = a[12]; p.r = 13;
    p.bronie = a[13].map(b => ({ rodzaj: b[0], tier: b[1], kat: b[2] / 100, anim: b[3] ? 0.1 : 0 }));
    p.blysk = a[14] / 10; p.spowG = 0;
    if (ja) { p.x = gracz.x; p.y = gracz.y; p.kierX = gracz.kierX || p.kierX; p.wRuchu = gracz.wRuchu; SIEC.mojWidok = p; }
    return p;
  });
  // wrogowie
  (d.wn || []).forEach(a => { const o = SIEC.znaneWrogi[a[0]] || (SIEC.znaneWrogi[a[0]] = {}); o.r = a[1]; o.ik = a[2]; o.kolor = a[3]; if (a[4]) o.obraz = a[4]; if (a[5]) o.afIk = a[5]; if (a[6]) o.n = a[6]; o.poswiata = a[7] || null; });
  const mapa = {}; wrogowie.forEach(w => mapa[w.id] = w);
  wrogowie = d.w.map(a => {
    const st = SIEC.znaneWrogi[a[0]] || { r: 14, ik: '❔', kolor: '#888' };
    const w = mapa[a[0]] || { id: a[0], x: a[1], y: a[2], afiksy: [] };
    przyjmijPozycje(w, a[1], a[2], tH, teraz); w.hpMax = 1000; w.hp = a[3]; w.r = st.r; w.ik = st.ik; w.kolor = st.kolor; w.obraz = st.obraz; w.n = st.n || ''; w.poswiata = st.poswiata;
    const fl = a[4];
    w.elita = !!(fl & 1); w.boss = !!(fl & 2); w.zauroczony = fl & 4 ? 1 : 0; w.sojusznik = !!(fl & 8); w.trafiony = fl & 16 ? 0.1 : 0; w.duch = !!(fl & 32);
    w.przygotowanie = fl & 64 ? 1 : 0; w.spow = fl & 128 ? 0.3 : 0; w.spowCzas = fl & 128 ? 1 : 0; w.ogl = fl & 256 ? 1 : 0; w.ogien = !!(fl & 512); w.krew = !!(fl & 1024);
    w.naznaczony = fl & 2048 ? 1 : 0; w.pole = !!(fl & 4096); w.czempion = !!(fl & 8192);
    w.wysokosc = a[5]; w.tarczaMax = a[6] >= 0 ? 100 : 0; w.tarcza = a[6] >= 0 ? a[6] : 0; w.hpBossa = a[7];
    // zamach przed ciosem: postęp z gospodarza, a między stanami dolicza się sam
    const zp = (a[8] || 0) / 100; if (zp > 0) { if (!(w.zamP > 0) || zp > w.zamP) w.zamP = zp; w.zamKat = (a[9] || 0) / 100; } else w.zamP = 0;
    w.afiksy = []; w.afIk = st.afIk || '';
    return w;
  });
  // pociski od razu "na teraz" (przesunięte o połowę pingu)
  pociski = d.p.map(a => { const dz = a[5] && a[5].endsWith('+'); return { x: a[0] + a[2] * wyp, y: a[1] + a[3] * wyp, vx: a[2], vy: a[3], kolor: a[4], ksztalt: dz ? a[5].slice(0, -1) : a[5], duza: dz, obrot: a[6] / 10 }; });
  pociskiWrogow = d.pw.map(a => ({ x: a[0] + a[2] * wyp, y: a[1] + a[3] * wyp, vx: a[2], vy: a[3], kolor: a[4], ksztalt: a[5] || null, r: a[6], siec: !!a[7] }));
  klientLupy(d);
  skrzynieNaZiemi = d.sk.map(a => ({ x: a[0], y: a[1], tier: a[2], faza: 0 }));
  kaluze = d.kal.map(a => ({ x: a[0], y: a[1], r: a[2], czas: a[3], max: 100, rodzaj: a[4] }));
  bomby = d.bm.map(a => ({ x: a[0], y: a[1], r: a[2], lont: a[3], max: 100 }));
  uderzeniaBossa = d.ub.map(a => ({ x: a[0], y: a[1], r: a[2], czas: a[3], zapowiedz: 100, mroz: !!a[4], zadane: !!a[5] }));
  wiry = d.wr.map(a => ({ x: a[0], y: a[1], r: a[2], czas: a[3] / 10, max: a[4] / 10, rozruch: a[5] / 100, faza: a[6] / 10 }));
  scianyMagiczne = d.sc.map(a => ({ x1: a[0], y1: a[1], x2: a[2], y2: a[3], czas: a[4] / 10, max: a[5] / 10, grubosc: a[6] }));
  zapowiedzi = d.zap.map(a => ({ x: a[0], y: a[1], czas: a[2], max: 100, opcje: { elita: !!a[3] } }));
  efektyCzasowe = d.ec.map(a => ({ rodzaj: a[0], x: a[1], y: a[2], r: a[3], czas: a[4], max: 100, sx: a[5], sy: a[6] }));
  polaEfektow = d.pe.map(a => ({ x: a[0], y: a[1], r: a[2], czas: a[3] / 10, rodzaj: a[4] }));
  SIEC.stwory = (d.st || []).map(a => ({ typ: a[0], x: a[1], y: a[2], czas: a[3] < 0 ? 1 : a[3], max: a[3] < 0 ? 99999 : 100, kat: a[4] / 100, r: a[5], ik: a[6], aura: a[7] }));
  orbyRys = d.ob.map(a => ({ x: a[0], y: a[1], kolor: a[2], kat: a[3] / 100 }));
  d.vf.forEach(a => fale.push({ x: a[0], y: a[1], r: a[2], kolor: a[3], czas: a[4], max: a[5], odwrot: !!a[6], slaba: !!a[7] }));
  d.vt.forEach(a => { if (teksty.length > 55) teksty.shift(); teksty.push({ x: a[0], y: a[1], t: a[2], kolor: a[3], czas: a[4], max: a[5], rozm: a[6], o: a[7] || 0 }); });
  d.vb.forEach(a => dodajBlyskawice(a[0], a[1], a[2], a[3], a[4]));
  d.vc.forEach(a => ciecia.push({ x: a[0], y: a[1], kat: a[2] / 100, luk: a[3] / 100, r: a[4], czas: a[5], max: a[5], kolor: a[6], linia: !!a[7] }));
  d.vs.forEach(a => stozki.push({ x: a[0], y: a[1], kat: a[2] / 100, r: a[3], pol: a[4] / 100, czas: a[5], max: a[5], kolor: a[6] }));
  (d.e || []).forEach(zastosujZdarzenie);
  (d.eg || []).forEach(zastosujZdarzenie);
  (d.dz || []).forEach(n => { if (DZ[n] && n !== 'kulka' && n !== 'moneta') DZ[n](); });   // własne zbieranie słychać od razu u siebie
  // moja postać (HUD)
  const ja = d.ja;
  if (ja) {
    gracz.hp = ja.hp; if (D) { D.hpMax = ja.hpMax; D.ms = ja.ms; } gracz.tarcze = ja.ts > 0 ? [{ v: ja.ts, czas: 1, max: 1 }] : [];
    gracz.xp = ja.xp; gracz.xpNast = ja.xpNast; gracz.poziom = ja.poziom; gracz.zloto = ja.zloto; gracz.maEnergie = ja.en >= 0; gracz.energia = Math.max(0, ja.en || 0);
    gracz.doWyboru = ja.dw; gracz.skrzynie.length = 0; for (let i = 0; i < ja.sk; i++) gracz.skrzynie.push({ tier: 0 });
    (ja.prz || []).forEach((c, i) => { const q = gracz.przedmioty[i]; if (q) { q.cd = c[0]; q.cdMax = c[1]; } });
    (ja.ore || []).forEach((c, i) => { const q = gracz.oreze[i]; if (q) { q.cd = c[0]; q.cdMax = c[1]; } });
    if (ja.umi) { gracz.umi.cd = ja.umi[0]; gracz.umi.cdMax = ja.umi[1]; } if (ja.umi2) { const u2 = stanUmi(2); u2.cd = ja.umi2[0]; u2.cdMax = ja.umi2[1]; } SIEC.umiAkt = ja.ua || [0, 0];
    if (ja.zb) SIEC.zbieranie = ja.zb; if (ja.rtt !== undefined) SIEC.rtt = ja.rtt;
    SIEC.ms = ja.ms; SIEC.roz = ja.roz; gracz.spowG = ja.spowG; gracz.zastoj = ja.zastoj ? 1 : 0; gracz.powalony = !!ja.pow; gracz.niewr = ja.niewr ? 0.1 : 0;
  }
}
// ---- łupy u klienta: kulki i monety żyją u niego, zbiera je od razu i tylko zgłasza gospodarzowi ----
function nowyLupKlienta(a) {
  const o = { id: a[0], x: a[1], y: a[2], vx: a[3], vy: a[4], faza: (a[0] % 7), opozn: (a[7] || 0) / 100 };
  if (a[5]) { o.v = a[6]; monety.push(o); } else { o.xp = a[6]; kulki.push(o); }
}
function klientLupy(d) {
  const teraz = Date.now();
  for (const id in SIEC.zebraneLok) if (teraz - SIEC.zebraneLok[id] > 3000) delete SIEC.zebraneLok[id];
  if (d.lu && d.lu.length) {
    const us = new Set(d.lu);
    kulki = kulki.filter(k => !us.has(k.id)); monety = monety.filter(m => !us.has(m.id));
  }
  const znane = new Set(); kulki.forEach(k => znane.add(k.id)); monety.forEach(m => znane.add(m.id));
  (d.ln || []).forEach(a => { if (!znane.has(a[0]) && !SIEC.zebraneLok[a[0]]) { nowyLupKlienta(a); znane.add(a[0]); } });
  if (d.la) {
    // pełna lista: usuń, czego już nie ma, dodaj brakujące (bez ruszania tych, które już lecą)
    const jest = new Set(d.la.map(a => a[0]));
    kulki = kulki.filter(k => jest.has(k.id)); monety = monety.filter(m => jest.has(m.id));
    d.la.forEach(a => { if (!znane.has(a[0]) && !SIEC.zebraneLok[a[0]]) nowyLupKlienta(a); });
  }
}
function aktualizujLupyKlienta(dt) {
  const ja = gracz, zbJa = SIEC.zbieranie || 60, teraz = Date.now(), zebrane = [];
  const inni = SIEC.widokGraczy.filter(p => p !== SIEC.mojWidok && !p.powalony);
  const tlum = Math.pow(0.92, dt * 60);
  const krokL = (lista, mon) => {
    for (let i = lista.length - 1; i >= 0; i--) {
      const k = lista[i]; k.faza += dt * (mon ? 5 : 6); if (k.opozn > 0) k.opozn -= dt;
      let px = ja.x, py = ja.y, zb = zbJa, moj = true, d = ja.powalony ? Infinity : Math.hypot(ja.x - k.x, ja.y - k.y);
      for (const p of inni) { const dd = Math.hypot(p.x - k.x, p.y - k.y); if (dd < d) { d = dd; px = p.x; py = p.y; zb = 60; moj = false; } }
      if (d !== Infinity && k.opozn <= 0 && (d < zb || k.ssij)) {
        const dd = d || 1, sila = 140 + Math.max(0, zb - d) * 6 + (k.ssij ? 600 : 0);
        k.vx += (px - k.x) / dd * sila * dt; k.vy += (py - k.y) / dd * sila * dt;
      }
      k.vx *= tlum; k.vy *= tlum; k.x += k.vx * dt; k.y += k.vy * dt;
      if (d < 16) {
        lista.splice(i, 1); SIEC.zebraneLok[k.id] = teraz;
        if (moj) { zebrane.push(k.id); if (mon) DZ.moneta(); else DZ.kulka(); }
      }
    }
  };
  krokL(kulki, false); krokL(monety, true);
  if (zebrane.length) siecWyslijHost({ t: 'zb', k: zebrane });
}
// pętla klienta: własny ruch bez opóźnienia, reszta przesuwana płynnie "na teraz"
function krokKlienta(dt) {
  if (stan !== 'walka') { aktualizujWizualne(dt); return; }
  const x0 = gracz.x, y0 = gracz.y;
  if (gracz.korzen > 0) gracz.korzen -= dt;
  if (!gracz.powalony) ruszGracza(dt, SIEC.ms || (D && D.ms) || 140, SIEC.roz || 1);
  if (!gracz.powalony && gracz.autoUmi) autoUmiejetnosci(gracz, true);
  if (dt > 0) { SIEC.vx = (gracz.x - x0) / dt; SIEC.vy = (gracz.y - y0) / dt; }
  const teraz = performance.now(), k = Math.min(1, dt * 18);
  wrogowie.forEach(w => { przesunDoTeraz(w, teraz, k); if (w.zamP > 0) w.zamP = Math.min(1, w.zamP + dt / 0.4); });
  SIEC.widokGraczy.forEach(p => { if (p === SIEC.mojWidok) { p.x = gracz.x; p.y = gracz.y; p.kierX = gracz.kierX; p.wRuchu = gracz.wRuchu; p.faza = gracz.faza; } else przesunDoTeraz(p, teraz, k); });
  pociski.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; if (p.ksztalt === 'bumerang') p.obrot += dt * 18; });
  pociskiWrogow.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; });
  aktualizujLupyKlienta(dt);
  wiry.forEach(w => { w.faza += dt * 5; if (w.rozruch > 0) w.rozruch -= dt; });
  aktualizujWizualne(dt);
  czasGry += dt;
  // pozycja i prędkość do gospodarza ok. 30 razy na sekundę (gospodarz przesuwa nas "na teraz")
  SIEC.tPoz -= dt;
  if (SIEC.tPoz <= 0) {
    SIEC.tPoz = 1 / 30; SIEC.nPoz = (SIEC.nPoz || 0) + 1;
    siecWyslijHost({ t: 'poz', n: SIEC.nPoz, x: Math.round(gracz.x), y: Math.round(gracz.y), vx: Math.round(SIEC.vx), vy: Math.round(SIEC.vy), kx: gracz.kierX < 0 ? -1 : 1,
      c: gracz.celKat === null || gracz.celKat === undefined ? null : Math.round(gracz.celKat * 100) / 100 });
  }
  ustawKamere(dt);
}

// ---------------------------------------------------------------------
//  ZNAKI ŻYCIA: co 2 s ping w obie strony; klient widzi, gdy gospodarz zamilknie,
//  gospodarz na ekranie czekania widzi, kto nie odpowiada
// ---------------------------------------------------------------------
function pokazInfoSieci(t) { const el = $('siecInfo'); if (!el) return; el.innerHTML = t; el.style.display = t ? 'block' : 'none'; }
setInterval(() => {
  if (!SIEC.rola) return;
  const teraz = Date.now();
  if (SIEC.rola === 'klient') {
    siecWyslijHost({ t: 'ping' });
    const cisza = SIEC.ostOdHosta ? teraz - SIEC.ostOdHosta : 0;
    pokazInfoSieci(SIEC.wGrze && stan !== 'smierc' && cisza > 5000 ? '📡 Gospodarz nie odpowiada… (' + Math.round(cisza / 1000) + ' s)<br><small style="font-weight:700">Niech otworzy grę na ekranie</small>' :
      (SIEC.wGrze && stan === 'walka' && SIEC.rtt > 250 ? '📶 Słabe łącze: ' + Math.round(SIEC.rtt) + ' ms' : ''));
  } else if (SIEC.rola === 'host') {
    if (stan !== 'walka') rozeslij({ t: 'ping' });
    // ktoś milczy ponad półtorej minuty - połączenie uznajemy za zerwane
    for (const id in SIEC.polaczenia) {
      if (teraz - (SIEC.ostatnio[id] || teraz) > 90000) { const c = SIEC.polaczenia[id]; try { c.close(); } catch (e) {} klientRozlaczony(+id); }
    }
    if (SIEC.czekamHost && stan === 'przerwa') {
      const podpis = statusCzekania().map(x => x[0].id + ':' + (x[1] ? 1 : 0) + (x[2] ? 1 : 0)).join(',');
      if (podpis !== SIEC.podpisCzekania && !$('modal').classList.contains('widoczny')) pokazCzekanie();
    }
  }
}, 2000);

// pomiar opóźnienia (ping) do każdego klienta - co sekundę, także w walce
setInterval(() => { if (SIEC.rola === 'host' && SIEC.wGrze) rozeslij({ t: 'pp', c: Math.round(performance.now() * 10) / 10 }); }, 1000);

// Zaproszenie z linku (?pokoj=KOD) - od razu ekran dołączania
function sprawdzZaproszenie() {
  let kod = '';
  try { kod = new URLSearchParams(window.parent.location.search).get('pokoj') || ''; } catch (e) {}
  if (!kod) try { kod = new URLSearchParams(window.location.search).get('pokoj') || ''; } catch (e) {}
  kod = (kod || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4);
  if (kod.length === 4) pokazOnline(kod);
}

// =====================================================================
//  PEŁNY EKRAN, ORIENTACJA I DRĄŻEK POD KCIUKIEM (poziomo na dotyku)
// =====================================================================
// okna od gry w górę (gra siedzi w ramkach strony Streamlit) - tylko te, do których mamy dostęp
function oknaWGore() {
  const lista = [window]; let w = window;
  for (let i = 0; i < 6; i++) { try { if (!w.parent || w.parent === w) break; void w.parent.document; w = w.parent; lista.push(w); } catch (e) { break; } }
  return lista;
}
function elementPelny(d) { try { return d.fullscreenElement || d.webkitFullscreenElement || null; } catch (e) { return null; } }
function czyAplikacja() {
  // gra uruchomiona z ikonki na ekranie początkowym (bez pasków przeglądarki)
  for (const w of oknaWGore()) {
    try { if (w.navigator.standalone === true || w.matchMedia('(display-mode: standalone)').matches || w.matchMedia('(display-mode: fullscreen)').matches) return true; } catch (e) {}
  }
  return false;
}
function czyPelnyEkran() { return oknaWGore().some(w => { try { return !!elementPelny(w.document); } catch (e) { return false; } }); }
function obslugaPelnegoEkranu() { const el = document.documentElement; return !!(el.requestFullscreen || el.webkitRequestFullscreen); }
function czyIPhone() { return /iPhone|iPod/.test(navigator.userAgent || ''); }
async function wejdzPelnyEkran() {
  // najpierw cała ramka gry na stronie (najwyżej, jak się da), potem sama gra
  const okna = oknaWGore(), kand = [];
  for (let i = okna.length - 1; i >= 1; i--) { try { const f = okna[i - 1].frameElement; if (f) kand.push(f); } catch (e) {} }
  kand.push(document.documentElement);
  for (const el of kand) {
    const f = el.requestFullscreen || el.webkitRequestFullscreen; if (!f) continue;
    try {
      const p = f.call(el, { navigationUI: 'hide' });
      if (p && p.then) await p; else await new Promise(r => setTimeout(r, 250));
      if (czyPelnyEkran()) { zablokujOrientacje(); setTimeout(dopasujRozmiar, 250); return true; }
    } catch (e) {}
  }
  return false;
}
function wyjdzPelnyEkran() {
  for (const w of oknaWGore()) { try { const d = w.document; if (elementPelny(d)) { (d.exitFullscreen || d.webkitExitFullscreen).call(d); return; } } catch (e) {} }
}
function instrukcjaPelnegoEkranu() {
  pokazModal('<div class="tytul">⛶ Pełny ekran</div>' +
    (czyIPhone()
      ? '<div class="info-pole">Safari na iPhonie nie pozwala stronie zasłonić swoich pasków. Da się to obejść, robiąc z gry <b>aplikację</b>:<br><br>' +
        '1. Stuknij <b>Udostępnij</b> (kwadrat ze strzałką w górę).<br>2. Wybierz <b>„Do ekranu początkowego”</b> (jeśli jest przełącznik „Otwórz jako aplikację” — zostaw włączony).<br>' +
        '3. Uruchamiaj grę z nowej ikonki — bez pasków Safari, poziomo i pionowo.</div>'
      : '<div class="info-pole">Ta przeglądarka nie pozwoliła włączyć pełnego ekranu. Spróbuj w Chrome albo dodaj grę do ekranu początkowego (menu przeglądarki → „Dodaj do ekranu głównego” / „Zainstaluj aplikację”).</div>') +
    '<button class="btn" data-a="zamknijModal">Rozumiem</button>');
}
AKCJE.pelnyEkran = async () => {
  if (czyPelnyEkran()) { wyjdzPelnyEkran(); setTimeout(dopasujRozmiar, 300); odswiezPrzyciskiPelnego(); return; }
  if (!obslugaPelnegoEkranu()) { instrukcjaPelnegoEkranu(); return; }
  const ok = await wejdzPelnyEkran();
  if (!ok) instrukcjaPelnegoEkranu();
  odswiezPrzyciskiPelnego();
};
function tekstPelnego() { return czyPelnyEkran() ? '⛶ Zamknij pełny ekran' : '⛶ Pełny ekran'; }
function przyciskPelnego(klasa) { return czyAplikacja() ? '' : '<button class="' + (klasa || 'btn drugi') + '" data-a="pelnyEkran" data-pelny="1">' + tekstPelnego() + '</button>'; }
function odswiezPrzyciskiPelnego() { setTimeout(() => document.querySelectorAll('[data-pelny]').forEach(b => { b.textContent = tekstPelnego(); }), 350); }
['fullscreenchange', 'webkitfullscreenchange'].forEach(ev => oknaWGore().forEach(w => { try { w.document.addEventListener(ev, () => { setTimeout(dopasujRozmiar, 200); odswiezPrzyciskiPelnego(); }); } catch (e) {} }));

// ---------- orientacja: automatyczna albo wybrana (pionowa / pozioma) ----------
function oknoGory() { const o = oknaWGore(); return o[o.length - 1]; }
function zablokujOrientacje() {
  // blokada działa tylko tam, gdzie przeglądarka pozwala (np. Chrome na Androidzie w pełnym ekranie)
  for (const w of oknaWGore().reverse()) {
    try {
      const so = w.screen && w.screen.orientation; if (!so) continue;
      if (USTAW.orientacja === 'auto') { if (so.unlock) so.unlock(); }
      else if (so.lock) so.lock(USTAW.orientacja === 'poziom' ? 'landscape' : 'portrait').catch(() => {});
      return;
    } catch (e) {}
  }
}
function sprawdzObrot() {
  const el = $('obrocInfo'); if (!el) return;
  const poziomo = window.innerWidth > window.innerHeight;
  const zle = USTAW.orientacja !== 'auto' && czyDotykowy() && ((USTAW.orientacja === 'poziom') !== poziomo);
  if (zle) {
    $('obrocTytul').textContent = USTAW.orientacja === 'poziom' ? 'Obróć urządzenie poziomo' : 'Obróć urządzenie pionowo';
    $('obrocTekst').innerHTML = 'Wybrana orientacja: <b>' + (USTAW.orientacja === 'poziom' ? 'pozioma' : 'pionowa') + '</b> (⚙️ Ustawienia).' +
      (czyIPhone() ? '<br>Żeby ekran się nie obracał, włącz blokadę obrotu w Centrum sterowania.' : '');
    el.classList.toggle('pion', USTAW.orientacja === 'pion');
    if (!el.classList.contains('widoczny') && stan === 'walka' && !druzyna()) { stan = 'pauza'; pokazEkwipunek('staty'); }
  }
  el.classList.toggle('widoczny', zle);
}
AKCJE.obrocAuto = () => { USTAW.orientacja = 'auto'; zapiszUstawienia(); zablokujOrientacje(); sprawdzObrot(); };

// ---------- drążek pod kciukiem (poziomo na dotyku): dotknij planszy w dowolnym miejscu ----------
const drazekPlyw = $('drazekPlyw'), galkaPlyw = drazekPlyw.querySelector('.galka');
let palecPlyw = null, srodekPlyw = { x: 0, y: 0 };
function ustawDrazekPlyw(x, y) { const r = $('gra').getBoundingClientRect(); drazekPlyw.style.left = (x - r.left) + 'px'; drazekPlyw.style.top = (y - r.top) + 'px'; }
function ustawGalkePlyw(dx, dy) {
  const dl = Math.hypot(dx, dy), o = Math.min(dl, 50), jx = dl ? dx / dl * o : 0, jy = dl ? dy / dl * o : 0;
  galkaPlyw.style.transform = 'translate(' + jx.toFixed(1) + 'px,' + jy.toFixed(1) + 'px)';
}
widok.addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' || palecPlyw !== null) return;
  const g = $('gra'); if (!g.classList.contains('dotyk') || g.classList.contains('tryb-pad')) return;
  e.preventDefault(); inicjujDzwiek();
  palecPlyw = e.pointerId; srodekPlyw = { x: e.clientX, y: e.clientY };
  ustawDrazekPlyw(e.clientX, e.clientY); drazekPlyw.classList.add('aktywny'); ustawGalkePlyw(0, 0);
  try { widok.setPointerCapture(e.pointerId); } catch (x) {}
  joy.aktywny = true; joy.x = 0; joy.y = 0;
});
widok.addEventListener('pointermove', e => {
  if (e.pointerId !== palecPlyw) return;
  let dx = e.clientX - srodekPlyw.x, dy = e.clientY - srodekPlyw.y; const dl = Math.hypot(dx, dy);
  // gdy kciuk ucieka daleko, drążek jedzie za nim (nie trzeba wracać do miejsca dotknięcia)
  if (dl > 70) { srodekPlyw.x += dx / dl * (dl - 70); srodekPlyw.y += dy / dl * (dl - 70); ustawDrazekPlyw(srodekPlyw.x, srodekPlyw.y); dx = e.clientX - srodekPlyw.x; dy = e.clientY - srodekPlyw.y; }
  joy.x = dx; joy.y = dy; ustawGalkePlyw(dx, dy);
});
function puscDrazekPlyw(e) {
  if (e && e.pointerId !== palecPlyw) return;
  palecPlyw = null; joy.aktywny = false; joy.x = 0; joy.y = 0;
  drazekPlyw.classList.remove('aktywny'); drazekPlyw.style.left = ''; drazekPlyw.style.top = ''; ustawGalkePlyw(0, 0);
}
['pointerup', 'pointercancel'].forEach(ev => widok.addEventListener(ev, puscDrazekPlyw));

// =====================================================================
//  STEROWANIE, PĘTLA GRY, START
// =====================================================================
// ---------- drążek ----------
const strefaDrazka = $('strefaDrazka'), drazekGalka = $('drazekGalka'), pasSter = $('pasSterowania');
const PROMIEN_DRAZKA = 52;
let idPalca = null;
function ustawGalke(dx, dy) {
  const dl = Math.hypot(dx, dy), o = Math.min(dl, PROMIEN_DRAZKA);
  const jx = dl ? dx / dl * o : 0, jy = dl ? dy / dl * o : 0;
  drazekGalka.style.transform = 'translate(calc(-50% + ' + jx.toFixed(1) + 'px), calc(-50% + ' + jy.toFixed(1) + 'px))';
}
function pozWStrefie(e) { const r = strefaDrazka.getBoundingClientRect(); return { x: e.clientX - r.left - r.width / 2, y: e.clientY - r.top - r.height / 2 }; }
pasSter.addEventListener('pointerdown', e => {
  if (idPalca !== null || e.target.closest('button')) return;
  if ($('gra').classList.contains('pc') || $('gra').classList.contains('tryb-pad')) return;   // bez drążka (komputer / pad)
  e.preventDefault(); inicjujDzwiek();
  if (!e.target.closest('#strefaDrazka')) {
    // drążek pojawia się pod palcem
    strefaDrazka.style.transform = 'none';
    const r = strefaDrazka.getBoundingClientRect(), pr = pasSter.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const px = ogr(e.clientX, pr.left + r.width / 2, pr.right - r.width / 2), py = ogr(e.clientY, pr.top + r.height / 2, pr.bottom - r.height / 2);
    strefaDrazka.style.transform = 'translate(' + (px - cx).toFixed(1) + 'px,' + (py - cy).toFixed(1) + 'px)';
  }
  idPalca = e.pointerId;
  try { pasSter.setPointerCapture(e.pointerId); } catch (x) {}
  const p = pozWStrefie(e); joy.aktywny = true; joy.x = p.x; joy.y = p.y; ustawGalke(p.x, p.y);
});
pasSter.addEventListener('pointermove', e => { if (idPalca !== e.pointerId) return; const p = pozWStrefie(e); joy.x = p.x; joy.y = p.y; ustawGalke(p.x, p.y); });
function puscDrazek(e) { if (e && idPalca !== e.pointerId) return; idPalca = null; joy.aktywny = false; joy.x = 0; joy.y = 0; ustawGalke(0, 0); strefaDrazka.style.transform = ''; }
['pointerup', 'pointercancel'].forEach(ev => pasSter.addEventListener(ev, puscDrazek));
// ---------- myszka (komputer) ----------
// lewy przycisk przytrzymany na planszy = idź w stronę kursora, prawy = umiejętność w stronę kursora
const MYSZ = { aktywna: false, x: 0, y: 0 };
function ustawMysz(e) { const r = widok.getBoundingClientRect(); MYSZ.x = (e.clientX - r.left) / r.width * WID; MYSZ.y = (e.clientY - r.top) / r.height * WYS; }
function kierunekMyszy() {
  if (!gracz) return null;
  const dx = MYSZ.x - (gracz.x - kamX) * ZOOM, dy = MYSZ.y - (gracz.y - kamY) * ZOOM, d = Math.hypot(dx, dy);
  return d < 6 ? null : [dx / d, dy / d, d];
}
widok.addEventListener('pointerdown', e => {
  if (e.pointerType !== 'mouse' || stan !== 'walka') return;
  ustawMysz(e);
  if (e.button === 2) {
    const k = kierunekMyszy();
    if (k && gracz) { gracz.kierRX = k[0]; gracz.kierRY = k[1]; }
    uzyjUmiejetnosci(1); e.preventDefault(); return;
  }
  if (e.button !== 0 || !USTAW.mysz) return;
  MYSZ.aktywna = true; inicjujDzwiek();
  try { widok.setPointerCapture(e.pointerId); } catch (x) {}
});
widok.addEventListener('pointermove', e => { if (MYSZ.aktywna) ustawMysz(e); });
['pointerup', 'pointercancel', 'lostpointercapture'].forEach(ev => widok.addEventListener(ev, () => { MYSZ.aktywna = false; }));
widok.addEventListener('contextmenu', e => e.preventDefault());

// sterowanie z klawiatury (komputer)
const MAPA_KL = { KeyA: 'l', ArrowLeft: 'l', KeyD: 'p', ArrowRight: 'p', KeyW: 'g', ArrowUp: 'g', KeyS: 'd', ArrowDown: 'd' };
document.addEventListener('keydown', e => {
  const wPolu = !!e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA');
  if (klawiszMenu(e, wPolu)) return;   // menu: strzałki / Enter / Esc (src/14_pad.js)
  if (wPolu) return;                    // pisanie pseudonimu albo kodu drużyny
  if (MAPA_KL[e.code]) { klawisze[MAPA_KL[e.code]] = true; e.preventDefault(); }
  if (e.shiftKey && (e.code === 'KeyE' || e.code === 'KeyR')) { if (stan === 'walka') przelaczAuto(e.code === 'KeyE' ? 1 : 2); e.preventDefault(); return; }
  if (e.code === 'KeyE' || e.code === 'Space') { uzyjUmiejetnosci(1); e.preventDefault(); }
  if (e.code === 'KeyR' || e.code === 'KeyF' || e.code === 'KeyQ') { uzyjUmiejetnosci(2); e.preventDefault(); }
  if (e.code === 'Escape' || e.code === 'KeyP') $('btnEkw').click();
});
document.addEventListener('keyup', e => { if (MAPA_KL[e.code]) klawisze[MAPA_KL[e.code]] = false; });
window.addEventListener('blur', () => { klawisze = {}; MYSZ.aktywna = false; });
document.addEventListener('visibilitychange', () => {
  if (document.hidden && stan === 'walka' && !druzyna()) { stan = 'pauza'; pokazEkwipunek('staty'); }
});
// iOS: blokada przewijania i powiększania strony gestami
document.addEventListener('touchmove', e => { if (!e.target.closest('#ekran') && !e.target.closest('#modalTresc') && e.cancelable) e.preventDefault(); }, { passive: false });
document.addEventListener('gesturestart', e => { if (e.cancelable) e.preventDefault(); });

// ---------- pętla ----------
let czasOstatni = null;
function krok(dt) {
  if (SIEC.rola === 'klient') { krokKlienta(dt); return; }
  if (stan === 'walka' && gracz && !gracz.martwy && gracze.length) {
    czasGry += dt;
    orbyRys.length = 0;
    // każdy gracz drużyny po kolei (w pojedynkę: tylko jeden)
    for (const p of gracze.slice()) {
      kontekst(p);
      odswiezStatyJesliTrzeba();
      if (!p.powalony) { aktualizujGracza(dt); autoUmiejetnosci(p, p === lokalny); }
      if (stan !== 'walka') { kontekst(lokalny); return; }
    }
    kontekst(lokalny);
    if (gracze.length > 1) aktualizujPodnoszenie(dt);
    aktualizujWrogow(dt);
    if (stan !== 'walka') return;
    aktualizujPociski(dt);
    aktualizujPlansze(dt);
    aktualizujStwory(dt);
    aktualizujLupy(dt);
    if (stan !== 'walka') return;
    aktualizujFale(dt);
    if (wrogowie.some(w => w.martwy)) wrogowie = wrogowie.filter(w => !w.martwy);
    kontekst(lokalny);
    ustawKamere(dt);
    if (SIEC.rola === 'host') siecWyslijStan(dt);
  } else if (stan === 'smierc' || stan === 'przerwa') {
    aktualizujWizualne(dt);
  }
}
function petla(t) {
  requestAnimationFrame(petla);
  if (czasOstatni === null) czasOstatni = t;
  const dt = Math.min(0.05, Math.max(0, (t - czasOstatni) / 1000)); mierzKlatke(t - czasOstatni); czasOstatni = t;
  if (document.hidden || window.__bezPetli) return;
  tPetli = performance.now();
  try { aktualizujPada(dt); } catch (e) { zglosBlad(e, 'pad'); }
  try { for (let i = 0; i < (window.__tempo || 1); i++) krok(dt); } catch (e) { zglosBlad(e, 'krok'); console.error(e); }
  odswiezWidocznosc();
  try { if (gracz && D) { rysuj(); odswiezHud(); } else { ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = '#0a0810'; ctx.fillRect(0, 0, WID, WYS); } } catch (e) { zglosBlad(e, 'rysuj'); console.error(e); }
}
// Gospodarz w tle (zminimalizowana karta): przeglądarka wstrzymuje animację,
// więc walkę liczymy dalej zegarem, żeby koledzy nie stanęli w miejscu.
let tPetli = performance.now();
setInterval(() => {
  if (SIEC.rola !== 'host' || !SIEC.wGrze || window.__bezPetli) return;
  const teraz = performance.now();
  if (!document.hidden && teraz - tPetli < 400) return;
  let zalegle = Math.min(1.5, (teraz - tPetli) / 1000); tPetli = teraz;
  try { while (zalegle > 0.001) { const d = Math.min(0.05, zalegle); krok(d); zalegle -= d; } } catch (e) { zglosBlad(e, 'krokTlo'); }
}, 200);

// ---------- API do testów automatycznych ----------
window.__test = {
  start(tr, kl) { rozpocznijRun(tr || 1, kl || 'wiezniarka'); },
  krok(dt, n) { for (let i = 0; i < (n || 1); i++) krok(dt || 1 / 60); },
  stan() { return { stan: stan, fala: fala.nr, hp: gracz && gracz.hp, hpMax: D && D.hpMax, wrogowie: wrogowie.length, poziom: gracz && gracz.poziom, zloto: gracz && gracz.zloto, bledy: BLEDY.slice() }; },
  get gracz() { return gracz; }, get run() { return run; }, get fala() { return fala; }, get D() { return D; },
  akcja(n, d) { AKCJE[n](d || {}); },
  kolejka() { kolejkaPrzerwy(); },
  dajPrzedmiot(id, gw) { gracz.przedmioty.push({ id: id, gw: gw || 0, cd: 0 }); const pr = czyPryzmat(id); if (wolneSlotyPrzedm(pr) < 0) { if (pr) gracz.slotyPryzm = liczPrzedm(true); else gracz.slotyPrzedm = liczPrzedm(false); } const d = DEF_PRZ[id]; if (d.natychmiast) d.natychmiast(); poZmianieBuildu(); },
  dajOreze(id, tier) { gracz.oreze.push(nowyOrez(id, tier || 0)); if (gracz.oreze.length > gracz.slotyOreza) gracz.slotyOreza = gracz.oreze.length; poZmianieBuildu(); },
  dajAugment(id, poz) { const inst = { id: id, poz: poz || 1 }; gracz.augmenty.push(inst); if (DEF_AUG[id].natychmiast) DEF_AUG[id].natychmiast(inst); poZmianieBuildu(); },
  bronGlowna(r, t) { gracz.bronie = [nowaBron(r, t || 0)]; poZmianieBuildu(); },
  umi(nr) { return uzyjUmiejetnosci(nr || 1); },
  startFali(n) { zamknijEkran(); startFali(n); },
  // drużyna lokalna (testy silnika): kolejny gracz sterowany botem na tym samym urządzeniu
  dodajGracza(kl, nick) {
    const z0 = gracz, r0 = run;
    const r = { trudnosc: r0.trudnosc, zabici: 0, zadane: 0, przyjete: 0, leczenie: 0, zloto: 0, xp: 0, ataki: 0, trafienia: 0, zrodla: {}, zlotoFali: 0, start: Date.now(), falaMaks: 0, przerzutyStatow: 0 };
    const p = nowyGracz(kl); p._run = r; p.nick = nick || KLASY[kl].n; p.id = gracze.length + 1;
    const K = KLASY[kl];
    p.bronie.push(nowaBron(bronStartowa(K), K.start === 'wybor' ? 1 : 0)); if (K.start === 'wybor2') p.bronie.push(nowaBron(bronStartowa(K), 0));
    gracze.push(p); gracz = p; run = r; D = null;
    przebudujHaki(); zastosujStaty(); if (K.dar) K.dar(p.stanKlasy); p.darmoweWybory += 2; poZmianieBuildu(); p.hp = D.hpMax;
    r.przerwa = { start: true, augment: 's', nr: 0 };
    kontekst(z0); run = r0;
    return p.id;
  },
  get gracze() { return gracze; }, get lokalny() { return lokalny; }, get SIEC() { return SIEC; },
  BLEDY: BLEDY,
};

// ---------- start ----------
wykryjBrakiEmoji();
przygotujOdznaki();
dopasujRozmiar();
pokazMenu();
sprawdzZaproszenie();
requestAnimationFrame(petla);
setTimeout(dopasujRozmiar, 300);
[1200, 3500, 8000].forEach(t => setTimeout(rozciagnijRamke, t));
// klawiatura i pad od razu trafiają do gry (bez klikania w ramkę Streamlita)
setTimeout(() => { try { window.focus(); } catch (e) {} }, 600);

</script>
</body>
</html>
'''

components.html(GRA_HTML, height=820, scrolling=False)
