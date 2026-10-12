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
  .btn-boczny:active { transform:scale(0.94); }
  .kolumna-btn { display:flex; flex-direction:column; gap:9px; }
  .btn-boczny.maly { width:50px; height:50px; border-radius:14px; font-size:22px; }
  .btn-boczny.maly .cdm { border-radius:13px; }
  #btnUmi { width:76px; height:76px; border-radius:22px; font-size:34px; border:2px solid #8a7a4e; background:linear-gradient(135deg,#4a3a6a,#2a2040); }
  #btnUmi .cdm { border-radius:20px; }
  #btnUmi .czas { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:900; color:#fff; text-shadow:0 2px 4px #000; }
  #btnUmi.gotowa { border-color:#ffe08a; box-shadow:0 0 16px rgba(255,224,138,0.55), 0 3px 10px rgba(0,0,0,0.45); animation:umiPuls 1.6s ease-in-out infinite; }
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
  .kol-t0 { color:var(--t0); } .kol-t1 { color:var(--t1); } .kol-t2 { color:var(--t2); } .kol-t3 { color:var(--t3); } .kol-t4 { color:var(--t4); }
  .kol-p { background:linear-gradient(90deg,#ff7ae0,#7ae0ff,#ffe07a); -webkit-background-clip:text; background-clip:text; color:transparent; }
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
  .kowadlo-statow { display:block; width:100%; margin:-4px 0 10px; padding:9px 10px; }
  #gra.pc .szeroka > .kowadlo-statow { width:min(100%, 600px); justify-self:center; }
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
      <button class="btn-boczny maly" id="btnMikstura" title="Mikstura (Q)">🧪<span class="cdm" id="miksturaCd"></span><span class="licznik" id="licznikMikstur">1</span><span class="pad-kl" data-k="X">X</span><span class="kb-kl">Q</span></button>
    </div>
    <div id="strefaDrazka"><div id="drazekBaza"><div id="drazekGalka"></div></div></div>
    <div id="padSrodek"></div>
    <button class="btn-boczny" id="btnUmi"><span id="umiIk">✨</span><span class="cdm" id="umiCd"></span><span class="czas" id="umiCzas"></span><span class="pad-kl" data-k="A">A</span><span class="kb-kl">E</span></button>
  </div>
  <div id="ekran"></div>
  <div id="modal"><div id="modalTresc"></div></div>
  <div id="padPodp"></div>
  <div id="toast"></div>
  <div id="siecInfo"></div>
</div>
<script>
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

// Układ komputerowy: szeroki ekran (poziomo) i myszka albo pad. Wtedy plansza zajmuje całe okno,
// zamiast dotykowego drążka jest mały pasek akcji, a menu układają się w kolumny.
function czyUkladPC() {
  const w = window.innerWidth, h = window.innerHeight;
  if (USTAW.uklad === 'tel' || w <= h) return false;
  if (USTAW.uklad === 'pc') return w >= 560;
  let mysz = false; try { mysz = matchMedia('(any-pointer: fine)').matches; } catch (e) {}
  return w >= 820 && w >= h * 1.15 && (mysz || (typeof PAD !== 'undefined' && PAD.tryb));
}
function dopasujRozmiar() {
  rozciagnijRamke();
  const g = $('gra'), pc = czyUkladPC();
  g.classList.toggle('pc', pc);
  const w = g.clientWidth || window.innerWidth, h = g.clientHeight || window.innerHeight;
  const pas = pc ? 0 : (typeof PAD !== 'undefined' && PAD.tryb) ? 64 : Math.round(ogr(h * 0.21, 132, 178));   // z padem: wąski pasek bez drążka
  document.documentElement.style.setProperty('--wysPaska', pas + 'px');
  const hc = Math.max(240, h - pas);
  widok.style.height = hc + 'px';
  if (pc) {
    // na komputerze widać więcej planszy w poziomie; wysokość widoku zbliżona do telefonu
    WYS = 500; WID = Math.round(WYS * w / hc);
    if (WID > 1150) { WID = 1150; WYS = Math.round(WID * hc / w); }
    SKALA_TEKSTU = 0.85;
  } else { WID = 380; WYS = Math.round(WID * hc / w); SKALA_TEKSTU = 1; }
  // płótno w rozdzielczości ekranu (ostre także na dużym monitorze), maks. 2× dla płynności
  DPR = ogr(w * (window.devicePixelRatio || 1) / WID, 1, 2);
  WYS_SW = WYS / ZOOM; WID_SW = WID / ZOOM;
  widok.width = Math.round(WID * DPR); widok.height = Math.round(WYS * DPR);
  // wielkość interfejsu: na komputerze rośnie z wysokością okna
  const sk = (pc ? ogr(h / 800, 1, 1.45) : 1) * (USTAW.interfejs || 1);
  document.documentElement.style.setProperty('--skalaUI', sk.toFixed(3));
  document.documentElement.style.setProperty('--skalaHud', ((pc ? ogr(h / 760, 1, 1.5) : 1) * (USTAW.interfejs || 1)).toFixed(3));
}
window.addEventListener('resize', () => setTimeout(dopasujRozmiar, 50));
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
  { k: 'regen', n: 'Regeneracja', i: '💗', j: '/s', d: 1, g: 'obrona', o: 'Zdrowie odzyskiwane co sekundę.' },
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
  { k: 'kradziez', n: 'Kradzież życia', i: '🩸', j: '%', g: 'atak', o: 'Leczy o procent obrażeń zadanych ATAKAMI. Razem z wszechwampiryzmem ma limit leczenia na sekundę (maks. 8% zdrowia/s).' },
  { k: 'omni', n: 'Wszechwampiryzm', i: '🦇', j: '%', g: 'atak', o: 'Leczy o procent WSZYSTKICH obrażeń (obszarowe i rozłożone w czasie: 1/3). Razem z kradzieżą życia ma limit: 2% maks. zdrowia na sekundę + 0,15% za każdy punkt (maks. 8%/s).' },
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
  { k: 'onHitFiz', n: 'Przy trafieniu (fizyczne)', i: '🟠', g: 'onhit', o: 'Każdy atak zadaje dodatkowo tyle obrażeń fizycznych.' },
  { k: 'onHitMag', n: 'Przy trafieniu (magiczne)', i: '🔵', g: 'onhit', o: 'Każdy atak zadaje dodatkowo tyle obrażeń magicznych.' },
  { k: 'onHitPraw', n: 'Przy trafieniu (prawdziwe)', i: '⚪', g: 'onhit', o: 'Każdy atak zadaje dodatkowo tyle obrażeń prawdziwych (ignorują pancerz).' },
];
const STAT = {}; DEF_STATOW.forEach(d => STAT[d.k] = d);
const BAZA_STATOW = {
  hpMax: 120, regen: 0.5, pancerz: 0, odpMag: 0, unik: 0, redukcja: 0, wytrwalosc: 0,
  ad: 0, ap: 0, as: 0, kryt: 5, krytObr: 0, obrBonus: 0, lethality: 0, przebPancP: 0, przebMag: 0, przebMagP: 0,
  kradziez: 0, omni: 0, zasieg: 0, pociski: 0, przebicie: 0, obszar: 0, haste: 0, ms: 140, leczenie: 0, szczescie: 0,
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
  hpMax: 'zdrowia', regen: 'regeneracji/s', pancerz: 'pancerza', odpMag: 'odp. na magię', unik: 'uniku', redukcja: 'redukcji obrażeń',
  wytrwalosc: 'nieustępliwości', ad: 'obrażeń od ataku', ap: 'mocy umiejętności', as: 'prędkości ataku', kryt: 'szansy na kryt',
  krytObr: 'obrażeń krytycznych', obrBonus: 'obrażeń', lethality: 'przebicia pancerza', przebPancP: 'przebicia pancerza',
  przebMag: 'przebicia magii', przebMagP: 'przebicia magii', kradziez: 'kradzieży życia', omni: 'wszechwampiryzmu', zasieg: 'zasięgu',
  pociski: 'pocisków', przebicie: 'przebicia pocisków', obszar: 'wielkości obszarów', haste: 'przyspieszenia', ms: 'prędkości ruchu',
  leczenie: 'mocy leczenia i tarcz', szczescie: 'szczęścia', zbieranie: 'zasięgu zbierania', chciwosc: 'zysku złota', xpBonus: 'doświadczenia',
  obrElity: 'obrażeń vs elity i bossowie', onHitFiz: 'fiz. obrażeń przy trafieniu', onHitMag: 'mag. obrażeń przy trafieniu', onHitPraw: 'prawdziwych obr. przy trafieniu',
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
  { k: 'regen', w: [0.5, 1, 1.7, 2.8] },
  { k: 'pancerz', w: [5, 9, 15, 23] },
  { k: 'odpMag', w: [5, 9, 15, 23] },
  { k: 'ad', w: [3, 6, 10, 15] },
  { k: 'ap', w: [5, 10, 16, 25] },
  { k: 'as', w: [5, 9, 14, 21] },
  { k: 'kryt', w: [3, 5, 8, 12] },
  { k: 'krytObr', w: [8, 14, 22, 34] },
  { k: 'obrBonus', w: [3, 5, 8, 12] },
  { k: 'kradziez', w: [1.5, 3, 4.5, 7] },
  { k: 'ms', w: [6, 10, 15, 22] },
  { k: 'zasieg', w: [6, 10, 15, 22] },
  { k: 'unik', w: [2, 3.5, 5, 7] },
  { k: 'szczescie', w: [6, 11, 18, 28] },
  { k: 'haste', w: [5, 9, 14, 21] },
  { k: 'lethality', w: [2, 4, 6, 9] },
  { k: 'przebMag', w: [3, 5, 8, 12] },
  { k: 'chciwosc', w: [5, 8, 12, 18] },
  { k: 'xpBonus', w: [6, 10, 15, 22] },
  { k: 'zbieranie', w: [20, 35, 55, 80] },
  { k: 'leczenie', w: [5, 8, 12, 18] },
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
    nazwa: 'Miecz', ikona: '🗡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.8, zasieg: 76, obr: 20, skal: { ad: 1.0 }, luk: 2.0,
    opisEf: t => 'Leczy o <b>' + (4 + 2 * t) + '%</b> zadanych obrażeń.',
    naTrafienie(w, b, k) { if (k.zadane > 0) leczWampirem(k.zadane * (0.04 + 0.02 * b.tier), 'Miecz'); },
  },
  mieczTarcza: {
    nazwa: 'Miecz i Tarcza', ikona: '🛡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.95, zasieg: 72, obr: 22, skal: { ad: 0.9, pancerz: 0.35 }, luk: 2.2,
    opisEf: t => 'Co 4. cios: tarcza <b>' + (25 + 15 * t) + ' + 20% pancerza</b> na 3 s i odrzut wrogów wokół.',
    naTrafienie(w, b, k) { if (!k.glowny || k.echo) return; b.licznik = (b.licznik || 0) + 1; if (b.licznik % 4) return; dajTarcze(25 + 15 * b.tier + 0.2 * D.pancerz, 3); obszarowe(gracz.x, gracz.y, 80, '#e8e8f0', o => odrzuc(o, 30), true); },
  },
  topor: {
    nazwa: 'Topór', ikona: '🪓', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.05, zasieg: 70, obr: 30, skal: { ad: 1.1, hpMax: 0.02 }, luk: 2.1,
    opisEf: t => 'Krwawienie: <b>' + (40 + 10 * t) + '%</b> obrażeń przez 2,5 s · krwawienie leczy Cię o 20% swoich obrażeń.',
    naTrafienie(w, b, k) { krwawienie(w, k.bazowe * (0.40 + 0.10 * b.tier) / 2.5, 2.5, true); },
  },
  mlot: {
    nazwa: 'Młot', ikona: '🔨', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.45, zasieg: 70, obr: 46, skal: { ad: 1.2, hpMax: 0.04 }, luk: 2.6,
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
    nazwa: 'Włócznia', ikona: '🔱', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 0.9, zasieg: 112, obr: 22, skal: { ad: 0.95, ms: 0.08 },
    opisEf: t => 'Pchnięcie trafia wszystkich w linii · co <b>' + (t >= 2 ? 3 : 4) + '.</b> atak rzut przebijającą włócznią (150% obrażeń).',
  },
  kastety: {
    nazwa: 'Kastety', ikona: '🥊', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.4, zasieg: 52, obr: 10, skal: { ad: 0.65, pancerz: 0.12, hpMax: 0.008 }, luk: 1.4,
    opisEf: t => 'Bardzo szybkie · co 4. cios ogłusza na <b>' + fmt(0.5 + 0.1 * t) + ' s</b>.',
    naTrafienie(w, b, k) { b.licznik = (b.licznik || 0) + (k.glowny ? 1 : 0); if (k.glowny && b.licznik % 4 === 0) oglusz(w, 0.5 + 0.1 * b.tier, { zrodlo: 'Kastety' }); odrzuc(w, 8); },
  },
  kosa: {
    nazwa: 'Kosa', ikona: '🌙', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.25, zasieg: 86, obr: 24, skal: { ad: 0.85, ap: 0.35 }, luk: Math.PI * 2,
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
    nazwa: 'Łuk', ikona: '🎯', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.72, zasieg: 250, obr: 17, skal: { ad: 0.9, as: 0.15 }, dystans: true,
    predkosc: 590, ksztalt: 'strzala', kolor: '#e8d8b0', kryt: 10, krytObr: 25,
    opisEf: t => '+10% szansy na kryt, +25% obr. krytycznych' + (t >= 3 ? ' · <b>2 strzały</b> naraz' : ''),
  },
  kusza: {
    nazwa: 'Kusza', ikona: '🏹', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 1.5, zasieg: 275, obr: 48, skal: { ad: 1.2 }, dystans: true,
    predkosc: 680, ksztalt: 'belt', kolor: '#d8d0b0', przebija: 2, przebPanc: 25,
    opisEf: t => 'Bełt przebija <b>' + (2 + t) + '</b> wrogów · ignoruje 25% pancerza.',
  },
  bumerang: {
    nazwa: 'Bumerang', ikona: '🪃', rodz: 'strzelecka', atak: 'bumerang', obrTyp: 'fiz', cd: 1.2, zasieg: 215, obr: 22, skal: { ad: 0.85, ms: 0.1 }, dystans: true,
    opisEf: t => 'Leci i wraca, raniąc w obie strony' + (t >= 3 ? ' · rzuca <b>2</b> bumerangi' : '') + '.',
  },
  pistolet: {
    nazwa: 'Pistolet', ikona: '🔫', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.5, zasieg: 225, obr: 12, skal: { ad: 0.7, szczescie: 0.15 }, dystans: true,
    predkosc: 820, ksztalt: 'kula', kolor: '#ffe08a', kryt: 8,
    opisEf: t => 'Szybkie strzały · co <b>6.</b> strzał to <b>salwa ' + (3 + Math.floor(t / 2)) + ' kul</b> (każda 70% obrażeń).',
    przyAtaku(b) { b.licznikP = (b.licznikP || 0) + 1; },
  },
  muszkiet: {
    nazwa: 'Muszkiet Snajpera', ikona: '🎖️', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 2.2, zasieg: 380, obr: 95, skal: { ad: 1.6 }, dystans: true,
    predkosc: 1100, ksztalt: 'belt', kolor: '#fff0c0', przebija: 4, krytObr: 50, celDaleki: true,
    opisEf: t => 'Bardzo wolny, ogromne obrażenia · celuje w <b>najdalszego</b> wroga w zasięgu · przebija ' + (4 + t) + ' wrogów · +50% obr. krytycznych.',
  },
  gwozdziarka: {
    nazwa: 'Gwoździarka', ikona: '🔩', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.3, zasieg: 210, obr: 7, skal: { ad: 0.45, pancerz: 0.06 }, dystans: true,
    predkosc: 640, ksztalt: 'belt', kolor: '#c0c8d0', przebija: 1,
    opisEf: t => 'Seria gwoździ · każdy przebija 1 wroga · trafienia kruszą pancerz o <b>' + (3 + t) + '%</b> (do 30%).',
    naTrafienie(w, b) { w.krusz = Math.min(0.3, (w.krusz || 0) + 0.03 + 0.01 * b.tier); },
  },

  // ======================= BROŃ MAGICZNA =======================
  rozdzka: {
    nazwa: 'Różdżka', ikona: '🪄', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.8, zasieg: 240, obr: 19, skal: { ap: 0.9, ad: 0.15 }, dystans: true,
    predkosc: 410, ksztalt: 'kula', kolor: '#c58ae6', naprowadza: 3.5,
    opisEf: t => 'Lekko naprowadzany pocisk' + (t >= 1 ? ' · odbija się do <b>' + (t >= 3 ? 2 : 1) + '</b> kolejnych wrogów' : '') + '.',
    odbicia: t => (t >= 3 ? 2 : (t >= 1 ? 1 : 0)),
  },
  rozdzkaOgnia: {
    nazwa: 'Różdżka Ognia', ikona: '🔥', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.1, zasieg: 220, obr: 20, skal: { ap: 0.8 }, dystans: true,
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
    nazwa: 'Różdżka Piorunów', ikona: '⚡', rodz: 'magiczna', atak: 'piorun', obrTyp: 'mag', cd: 0.72, zasieg: 220, obr: 12, skal: { ap: 0.6, as: 0.1 }, dystans: true,
    opisEf: t => 'Natychmiastowa błyskawica · przeskakuje na <b>' + (3 + t) + '</b> kolejnych wrogów (−25% za skok).',
  },
  rozdzkaZimy: {
    nazwa: 'Różdżka Zimy', ikona: '❄️', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.0, zasieg: 220, obr: 17, skal: { ap: 0.8, odpMag: 0.2 }, dystans: true,
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
    nazwa: 'Kostur Pustki', ikona: '🔮', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.3, zasieg: 235, obr: 26, skal: { ap: 0.9 }, dystans: true,
    predkosc: 330, ksztalt: 'pustka', kolor: '#9a6aff', przebija: 99,
    opisEf: t => 'Kula przelatuje przez wszystkich · dodatkowo <b>' + (20 + 5 * t) + '%</b> obrażeń jako prawdziwe.',
    naTrafienie(w, b, k) { zadaj(w, k.bazowe * (0.20 + 0.05 * b.tier), 'praw', { zr: 'Kostur Pustki' }); },
  },
  kosturKosci: {
    nazwa: 'Kostur Kości', ikona: '🦴', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.95, zasieg: 230, obr: 20, skal: { ap: 0.75, hpMax: 0.015 }, dystans: true,
    predkosc: 420, ksztalt: 'kosc', kolor: '#e8f0ff',
    opisEf: t => 'Zabici tym kosturem wrogowie mają <b>' + (10 + 4 * t) + '%</b> szansy powstać jako Twój szkielet na 8 s.',
    naZabicie(w, b) { if (!w.boss && !w.sojusznik && Math.random() < 0.10 + 0.04 * b.tier) wskrzesSojusznika(w); },
  },
  kosturNatury: {
    nazwa: 'Kostur Natury', ikona: '🌿', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 0.9, zasieg: 230, obr: 18, skal: { ap: 0.7, hpMax: 0.01, regen: 2 }, dystans: true,
    predkosc: 430, ksztalt: 'kolec', kolor: '#7ee87a',
    opisEf: t => 'Ciernie oplątują (spowolnienie 40% na 0,8 s) · co 5. trafienie leczy Cię o <b>' + (2 + t) + '%</b> maks. zdrowia.',
    naTrafienie(w, b, k) { spowolnij(w, 0.4, 0.8); if (!k.glowny) return; b.licznik = (b.licznik || 0) + 1; if (b.licznik % 5 === 0) leczGracza(D.hpMax * (0.02 + 0.01 * b.tier), 'Kostur Natury'); },
  },

  // ======================= ALCHEMIA =======================
  granatnik: {
    nazwa: 'Granatnik', ikona: '🧨', rodz: 'alchemia', atak: 'granat', obrTyp: 'fiz', cd: 1.35, zasieg: 245, obr: 30, skal: { ad: 0.7, ap: 0.5 }, dystans: true,
    promien: 68, kolor: '#ffb070',
    opisEf: t => 'Granat wybucha w miejscu celu (r <b>' + (68 + 6 * t) + '</b>) i rani wszystkich w zasięgu wybuchu.',
  },
  // ---- nowe bronie ----
  kosci: {
    nazwa: 'Kości do gry', ikona: '🎲', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 0.6, zasieg: 230, obr: 7, skal: { ad: 0.45, szczescie: 0.25 }, dystans: true,
    predkosc: 520, ksztalt: 'kula', kolor: '#f0f0f0',
    opisEf: t => 'Słabe, ale losowe: każdy rzut to <b>1–6</b> oczek (obrażenia ×oczka/3,5). Szóstka trafia za <b>×' + fmt(2.4 + 0.2 * t) + '</b>.',
    mnTrafienia(b, w, o) { if (!o.glowny) return 1; const r = 1 + Math.floor(Math.random() * 6); if (r === 6) { tekstSwiat(w.x, w.y - w.r - 14, '🎲 6!', '#ffe08a', 0.6, 12); return 2.4 + 0.2 * b.tier; } return r / 3.5; },
  },
  katana: {
    nazwa: 'Katana', ikona: '🗡️', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 0.75, zasieg: 72, obr: 20, skal: { ad: 0.9, kryt: 0.4 }, luk: 1.9, kryt: 15, krytObr: 25,
    opisEf: t => '+15% szansy na kryt, krytyki +25% · <b>trafienie krytyczne nakłada efekty przy trafieniu ' + (t >= 3 ? '3 razy' : '2 razy') + '</b>.',
    naTrafienie(w, b, k) { if (k.kryt && k.glowny && !w.martwy) zastosujOnHit(w, b, { razy: b.tier >= 3 ? 2 : 1 }); },
  },
  halabarda: {
    nazwa: 'Halabarda', ikona: '⚜️', rodz: 'biala', atak: 'pchniecie', obrTyp: 'fiz', cd: 1.15, zasieg: 140, obr: 34, skal: { ad: 1.0, pancerz: 0.25 }, przebPanc: 30,
    opisEf: t => 'Długie pchnięcie przez całą linię · ignoruje 30% pancerza · skaluje się z Twoim pancerzem · wrogowie dostają <b>' + (10 + 3 * t) + '%</b> więcej obrażeń przez 3 s.',
    naTrafienie(w, b, k) { w.naznaczony = Math.max(w.naznaczony || 0, 3); w.mnNazn = Math.max(w.mnNazn || 0, 0.10 + 0.03 * b.tier); },
  },
  buzdygan: {
    nazwa: 'Buzdygan', ikona: '🏏', rodz: 'biala', atak: 'wrecz', obrTyp: 'fiz', cd: 1.1, zasieg: 64, obr: 36, skal: { ad: 1.0, hpMax: 0.02 }, luk: 1.6,
    opisEf: t => 'Ciężkie uderzenia: <b>' + (15 + 5 * t) + '%</b> szansy na ogłuszenie (0,8 s) · <b>+' + (30 + 10 * t) + '%</b> obrażeń elitom i bossom.',
    mnTrafienia(b, w) { return (w.elita || w.boss) ? 1.3 + 0.1 * b.tier : 1; },
    naTrafienie(w, b, k) { if (k.glowny && Math.random() < 0.15 + 0.05 * b.tier) oglusz(w, 0.8, { zrodlo: 'Buzdygan' }); },
  },
  lukDlugi: {
    nazwa: 'Łuk Długi', ikona: '🎯', rodz: 'strzelecka', atak: 'pocisk', obrTyp: 'fiz', cd: 1.7, zasieg: 340, obr: 58, skal: { ad: 1.35 }, dystans: true, celDaleki: true,
    predkosc: 900, ksztalt: 'strzala', kolor: '#f0e0b0', przebija: 3, kryt: 10, krytObr: 40,
    opisEf: t => 'Snajperski: celuje w <b>najdalszego</b> wroga, przebija ' + (3 + t) + ' wrogów, krytyki +40% · im dalej leci, tym mocniej (do +' + (30 + 10 * t) + '%).',
    mnTrafienia(b, w) { const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); return 1 + Math.min(1, d / 340) * (0.3 + 0.1 * b.tier); },
  },
  ksiegaZaklec: {
    nazwa: 'Księga Zaklęć', ikona: '📕', rodz: 'magiczna', atak: 'pocisk', obrTyp: 'mag', cd: 1.1, zasieg: 250, obr: 13, skal: { ap: 0.6, haste: 0.3 }, dystans: true,
    predkosc: 360, ksztalt: 'kula', kolor: '#ff8ab0', naprowadza: 6, dodPociski: 2, rozrzut: 0.5,
    opisEf: t => 'Wystrzeliwuje <b>' + (3 + Math.floor(t / 2)) + '</b> naprowadzanych pocisków naraz (każdy 100% obrażeń) · skaluje się z przyspieszeniem.',
    dodPociskiT: t => 2 + Math.floor(t / 2), pelnePociski: true,
  },
  berloSlonca: {
    nazwa: 'Berło Słońca', ikona: '☀️', rodz: 'magiczna', atak: 'granat', obrTyp: 'mag', cd: 1.45, zasieg: 250, obr: 30, skal: { ap: 1.0 }, dystans: true,
    promien: 72, kolor: '#ffd24a',
    opisEf: t => 'Słoneczny wybuch w miejscu celu (r <b>' + (72 + 6 * t) + '</b>) · podpala trafionych na 2 s (<b>' + (20 + 6 * t) + '%</b> obr./s).',
    naTrafienie(w, b, k) { podpal(w, k.bazowe * (0.2 + 0.06 * b.tier), 2, 'mag', 'Berło Słońca'); },
  },
  kwasomiot: {
    nazwa: 'Kwasomiot', ikona: '🧪', rodz: 'alchemia', atak: 'stozek', obrTyp: 'fiz', cd: 0.4, zasieg: 115, obr: 8, skal: { ad: 0.35, ap: 0.25 }, dystans: false,
    pol: 0.38, kolor: '#9aff5a',
    opisEf: t => 'Strumień kwasu w stożku · <b>rozpuszcza pancerz</b>: każde trafienie −4% pancerza i odporności celu (do −' + (40 + 5 * t) + '%).',
    naTrafienie(w, b, k) { w.krusz = Math.min(0.40 + 0.05 * b.tier, (w.krusz || 0) + 0.04); },
  },
  miotaczOgnia: {
    nazwa: 'Miotacz Ognia', ikona: '🌋', rodz: 'alchemia', atak: 'stozek', obrTyp: 'mag', cd: 0.35, zasieg: 125, obr: 8, skal: { ap: 0.35, ad: 0.25 }, dystans: false,
    pol: 0.42, kolor: '#ff8a3a',
    opisEf: t => 'Strumień ognia w stożku · podpala na 2 s (<b>' + (30 + 8 * t) + '%</b> obr./s).',
    naTrafienie(w, b, k) { podpal(w, k.bazowe * (0.30 + 0.08 * b.tier), 2, 'mag', 'Miotacz Ognia'); },
  },
};
const KLUCZE_BRONI = Object.keys(BRONIE);

function nowaBron(rodzaj, tier) { return { rodzaj: rodzaj, tier: tier || 0, cd: Math.random() * 0.4, licznik: 0 }; }
function nazwaBroni(b) { return BRONIE[b.rodzaj].nazwa + ' ' + TIERY[b.tier].rz; }
function obrBroni(b) {
  const B = BRONIE[b.rodzaj];
  let v = B.obr * MN_BRONI[b.tier];
  for (const k in B.skal) v += B.skal[k] * (k === 'zloto' ? gracz.zloto : (D[k] || 0));
  const kl = KLASY[gracz.klasa];
  if (kl && kl.mnBroni) v *= kl.mnBroni(B, b);
  v *= (FLAGI.mnGlownej || 1) * (1 + (FLAGI.mnGlownejAug || 0));
  return Math.max(1, v);
}
// faktyczny odstęp między atakami (z prędkością ataku)
function odstepAtaku(b) { const B = BRONIE[b.rodzaj]; const t = ogr((1 + D.as / 100) * (B.tempo ? B.tempo(b) : 1), 0.2, B.cd / 0.1); return B.cd / t; }
function zasiegBroni(b) {
  const B = BRONIE[b.rodzaj];
  const premia = D.zasieg / 100 * (B.dystans ? 1 : 0.5);
  return B.zasieg * Math.max(0.4, 1 + premia);
}
function opisSkalowania(B) {
  return Object.keys(B.skal).map(k => {
    const v = B.skal[k];
    if (k === 'hpMax') return fmt(v * 100) + '% ' + IKONY_SKAL[k];
    if (k === 'regen') return fmt(v * 100) + '% 💗 regeneracji';
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
      c.fillStyle = '#d8d0c0'; c.fillRect(-10, -1.5, 22, 3); c.font = '11px sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('💀', 16, 0); break;
    case 'kosturNatury':
      c.fillStyle = '#5a3a1a'; c.fillRect(-10, -1.6, 22, 3.2); c.fillStyle = '#5ac46a'; c.beginPath(); c.ellipse(15, -4, 5, 2.5, -0.6, 0, Math.PI * 2); c.ellipse(16, 3, 4.5, 2.2, 0.6, 0, Math.PI * 2); c.fill();
      c.fillStyle = kol; c.fillRect(8, -2.2, 3, 4.4); break;
    case 'rozdzkaOgnia': rozdzkaZKrysztalem('#ff7a3c'); break;
    case 'rozdzkaZimy': rozdzkaZKrysztalem('#7ec4e8'); break;
    case 'rozdzkaPior': rozdzkaZKrysztalem('#ffe066'); break;
    case 'kosturPustki': rozdzkaZKrysztalem('#9a6aff', true); break;
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
  { id: 'toporRzeznika', rodz: 'biala', ik: '🪓', n: 'Topór Rzeźnika', s: { ad: 15, kradziez: 1 }, co: 4,
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
  { id: 'butlaGazu', rodz: 'alchemia', ik: '☁️', n: 'Butla Gazu', s: { hpMax: 40, regen: 1 },
    opis: i => 'Trujący opar wokół Ciebie (r 85): co 0,5 s <span class="mag">' + f0((6 + 0.08 * D.ap + 0.005 * D.hpMax) * MO(i)) + '</span> (6 + 8% ✨ + 0,5% maks. zdrowia).',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t < 0.5) return; i.t = 0; aura(85, '#9ae05a', w => zadaj(w, (6 + 0.08 * D.ap + 0.005 * D.hpMax) * MO(i), 'mag', { dot: true, obszar: true, zr: 'Butla Gazu' })); } },
  { id: 'rakietnica', rodz: 'alchemia', ik: '🚀', n: 'Rakietnica', s: { ad: 10, ap: 10 }, cd: 7,
    opis: i => 'Co <b>7 s</b> 4 rakiety w różnych wrogów (wybuch r 50): <span class="fiz">' + f0((25 + 0.35 * D.ad + 0.35 * D.ap) * MO(i)) + '</span> (25 + 35% ⚔️ + 35% ✨) każda.',
    tik(i) { if (!cdGotowe(i)) return; const cele = najblizsi(gracz.x, gracz.y, 280, 4); if (!cele.length) return; cdUstaw(i, 7); const v = (25 + 0.35 * D.ad + 0.35 * D.ap) * MO(i);
      cele.forEach((c, n) => wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, c) + (n - 1.5) * 0.4, cel: c, naprowadza: 6, predkosc: 420, obr: v * 0.5, typ: 'fiz', kolor: '#ffb04a', ksztalt: 'rakieta', zr: 'Rakietnica', zycie: 1.4, wybuch: { r: 50, obr: v } })); } },
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
  { id: 'opaska', slot: 'helm', n: 'Opaska Łowczyni', ik: '🎀', s: { kryt: 5, zasieg: 8 } },
  { id: 'koronaMaga', slot: 'helm', n: 'Diadem Maga', ik: '👑', s: { ap: 15, odpMag: 8 } },
  { id: 'helmBerserka', slot: 'helm', n: 'Rogaty Hełm', ik: '🐂', s: { hpMax: 35, as: 5 } },
  { id: 'zbrPlyt', slot: 'zbroja', n: 'Zbroja płytowa', ik: '🛡️', s: { pancerz: 22, hpMax: 30 } },
  { id: 'zbrBers', slot: 'zbroja', n: 'Napierśnik Berserkera', ik: '🥋', s: { ad: 7, as: 7, hpMax: 15 } },
  { id: 'zbrStraz', slot: 'zbroja', n: 'Zbroja Strażnika', ik: '🦺', s: { pancerz: 10, hpMax: 65 } },
  { id: 'szata', slot: 'zbroja', n: 'Szata Czarodziejki', ik: '👘', s: { ap: 16, odpMag: 14, hpMax: 15 } },
  { id: 'zbrKata', slot: 'zbroja', n: 'Kolczuga Kata', ik: '☠️', s: { pancerz: 12, lethality: 4 } },
  { id: 'plaszczCienia', slot: 'zbroja', n: 'Płaszcz Cienia', ik: '🧥', s: { unik: 5, ms: 8, hpMax: 15 } },
  { id: 'zbrSmocza', slot: 'zbroja', n: 'Smocza Łuska', ik: '🐲', s: { pancerz: 12, odpMag: 12, hpMax: 25 } },
  { id: 'butWichr', slot: 'buty', n: 'Buty Wichru', ik: '👟', s: { ms: 22 } },
  { id: 'butOkute', slot: 'buty', n: 'Buty okute', ik: '🥾', s: { pancerz: 10, ms: 8, hpMax: 15 } },
  { id: 'butWedr', slot: 'buty', n: 'Buty Wędrowca', ik: '🧦', s: { ms: 12, regen: 0.7 } },
  { id: 'butMaga', slot: 'buty', n: 'Buty Maga', ik: '🩴', s: { przebMag: 6, ms: 10 } },
  { id: 'butBers', slot: 'buty', n: 'Buty Berserkera', ik: '🥿', s: { as: 10, ms: 10 } },
  { id: 'butMerk', slot: 'buty', n: 'Buty Merkurego', ik: '👞', s: { odpMag: 12, wytrwalosc: 15, ms: 10 } },
  { id: 'amMocy', slot: 'amulet', n: 'Amulet Mocy', ik: '📿', s: { ad: 9 } },
  { id: 'amZycia', slot: 'amulet', n: 'Amulet Życia', ik: '💠', s: { hpMax: 75 } },
  { id: 'amLowcy', slot: 'amulet', n: 'Amulet Łowcy', ik: '🔮', s: { ad: 5, xpBonus: 8 } },
  { id: 'amWiedzy', slot: 'amulet', n: 'Amulet Wiedzy', ik: '📖', s: { xpBonus: 18 } },
  { id: 'amZrodla', slot: 'amulet', n: 'Amulet Źródła', ik: '💧', s: { regen: 1.3 } },
  { id: 'amKrwi', slot: 'amulet', n: 'Amulet Krwi', ik: '🩸', s: { omni: 1 } },
  { id: 'amSzczescia', slot: 'amulet', n: 'Amulet Szczęścia', ik: '🧿', s: { szczescie: 14 } },
  { id: 'amChciwosci', slot: 'amulet', n: 'Amulet Chciwości', ik: '🪙', s: { chciwosc: 14 } },
  { id: 'amCzasu', slot: 'amulet', n: 'Amulet Czasu', ik: '⌚', s: { haste: 12 } },
  { id: 'amArkan', slot: 'amulet', n: 'Amulet Arkan', ik: '🔯', s: { ap: 12, przebMagP: 4 } },
];
const DEF_PANC = {}; PANCERZE.forEach(p => DEF_PANC[p.id] = p);
function nowyPancerz(id, tier) { return { id: id, tier: tier }; }
function statyPancerza(p) { const d = DEF_PANC[p.id], s = {}; for (const k in d.s) { const v = d.s[k] * MN_PANCERZA[p.tier]; s[k] = (k === 'regen' || k === 'omni') ? Math.round(v * 10) / 10 : Math.round(v); } return s; }
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
  { id: 'wiezyczka', t: 0, ik: '🗼', n: 'Mała Wieżyczka', cd: 10,
    opis: i => 'Co <b>10 s</b> stawia wieżyczkę na 8 s. Strzela co 0,8 s: <span class="fiz">' + f0((8 + 0.2 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (8 + 20% ⚔️ + 20% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 10); postawDzialko('wiezyczka', 8, { obr: (8 + 0.2 * D.ad + 0.2 * D.ap) * M(i), co: 0.8, zr: 'Mała Wieżyczka' }); } },
  { id: 'krzakJagod', t: 0, ik: '🫐', n: 'Krzak Jagód', cd: 16,
    opis: i => 'Co <b>16 s</b> sadzi krzak (12 s), który co 3 s zrzuca jagodę. Jagoda leczy tego, kto ją zbierze, o <b>' + fmt(4 * M(i)) + '%</b> maks. zdrowia (działa też na kolegów).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 16); dodajStwora('krzak', gracz.x + losowo(-40, 40), gracz.y + losowo(-40, 40), 12, { co: 3, lecz: 0.04 * M(i), ikOwocu: '🫐' }); } },
  { id: 'swieca', t: 0, ik: '🕯️', n: 'Świeca Mędrca',
    opis: i => 'Każdy nowy poziom leczy Cię o <b>' + Math.round(15 * M(i)) + '%</b> maks. zdrowia i daje tarczę ' + Math.round(10 * M(i)) + '% maks. zdrowia na 3 s.',
    naAwans(i) { leczGracza(D.hpMax * 0.15 * M(i), 'Świeca Mędrca'); dajTarcze(D.hpMax * 0.1 * M(i), 3); } },
  { id: 'sakiewka', t: 0, ik: '👛', n: 'Sakiewka Złodzieja',
    opis: i => 'Zabici wrogowie mają <b>10%</b> szansy upuścić dodatkowe <b>' + f0(2 * M(i)) + '</b> złota.',
    naZabicie(i, w) { if (!w.bezLupu && Math.random() < 0.1) rozsypMonety(w.x, w.y, 2 * M(i)); } },
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
    opis: i => 'Ataki mają <b>25%</b> szansy podpalić: <span class="mag">' + f0((5 + 0.15 * D.ad + 0.1 * D.ap) * M(i)) + '</span> (5 + 15% ⚔️ + 10% ✨) na sekundę przez 3 s.',
    naTrafienie(i, w, k) { if (k.glowny && Math.random() < 0.25) podpal(w, (5 + 0.15 * D.ad + 0.1 * D.ap) * M(i), 3, 'mag', 'Pochodnia'); } },
  { id: 'magnes', t: 0, ik: '🧲', n: 'Magnes', cd: 12,
    opis: i => 'Co <b>' + fmt(12 / M(i)) + ' s</b> przyciąga do Ciebie wszystkie kulki doświadczenia i monety z całej areny.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna || (kulki.length + monety.length) < 4) return; cdUstaw(i, 12 / M(i)); kulki.forEach(k => k.ssij = true); monety.forEach(m => m.ssij = true); fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 160, kolor: '#7ee87a', odwrot: true }); } },
  { id: 'kamienOdnowy', t: 0, ik: '💠', n: 'Kamień Odnowy',
    opis: i => 'Co 25 zabójstw i za każdą zabitą elitę leczysz się o <b>' + Math.round(10 * M(i)) + '%</b> maks. zdrowia.',
    naZabicie(i, w) { i.zab = (i.zab || 0) + 1; if (w.elita || w.boss || i.zab % 25 === 0) leczGracza(D.hpMax * 0.1 * M(i), 'Kamień Odnowy'); } },
  { id: 'talizmanUniku', t: 0, ik: '🍃', n: 'Talizman Wiatru',
    opis: i => 'Po <b>uniku</b> następny atak zadaje <b>+' + Math.round(60 * M(i)) + '%</b> obrażeń, a Ty zyskujesz +40 prędkości ruchu na 1 s.',
    naUniku(i) { i.gotowy = 1; dodajBuff('wiatr', { ms: 40 }, 1); },
    modZadanych(i, w, typ, o) { if (o.atak && i.gotowy) { i.gotowy = 0; return 1 + 0.6 * M(i); } return 1; } },
  { id: 'rog', t: 0, ik: '📯', n: 'Róg Bojowy',
    opis: i => 'Na początku każdej fali: <b>+' + Math.round(35 * M(i)) + '%</b> prędkości ataku i +20 prędkości ruchu na 8 s.',
    naStartFali(i) { dodajBuff('rog', { as: 35 * M(i), ms: 20 }, 8); } },
  { id: 'pulapka', t: 0, ik: '🪤', n: 'Wnyki', cd: 7,
    opis: i => 'Co <b>7 s</b> zostawia wnyki (20 s). Pierwszy wróg, który w nie wejdzie, jest unieruchomiony na 1,5 s i dostaje <span class="fiz">' + f0((20 + 0.3 * D.ad) * M(i)) + '</span> (20 + 30% ⚔️).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 7); dodajStwora('wnyki', gracz.x, gracz.y, 20, { obr: (20 + 0.3 * D.ad) * M(i), zr: 'Wnyki' }); } },
  { id: 'ksiazkaKucharska', t: 0, ik: '🍳', n: 'Książka Kucharska',
    opis: i => 'Mikstury leczą o <b>' + Math.round(40 * M(i)) + '%</b> mocniej, a po wypiciu dostajesz tarczę ' + Math.round(15 * M(i)) + '% maks. zdrowia na 4 s.',
    naMiksturze(i) { dajTarcze(D.hpMax * 0.15 * M(i), 4); }, mocMikstur(i) { return 0.4 * M(i); } },

  // ======================= RZADKIE (T2) =======================
  { id: 'dzialko', t: 1, ik: '🔫', n: 'Działko Strażnicze', cd: 12,
    opis: i => 'Co <b>12 s</b> stawia działko na 12 s. Strzela co 0,6 s: <span class="fiz">' + f0((12 + 0.3 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (12 + 30% ⚔️ + 20% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 12); postawDzialko('dzialko', 12, { obr: (12 + 0.3 * D.ad + 0.2 * D.ap) * M(i), co: 0.6, zr: 'Działko Strażnicze' }); } },
  { id: 'krzakZycia', t: 1, ik: '🌳', n: 'Krzak Życia', cd: 18,
    opis: i => 'Co <b>18 s</b> sadzi krzak (16 s), który co 2,5 s zrzuca owoc. Owoc leczy o <b>' + fmt(6 * M(i)) + '%</b> maks. zdrowia tego, kto go podniesie.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 18); dodajStwora('krzak', gracz.x + losowo(-40, 40), gracz.y + losowo(-40, 40), 16, { co: 2.5, lecz: 0.06 * M(i), ikOwocu: '🍎', ik: '🌳' }); } },
  { id: 'tesla', t: 1, ik: '⚡', n: 'Wieża Tesli', cd: 14,
    opis: i => 'Co <b>14 s</b> stawia wieżę (10 s). Co sekundę razi łańcuchem 3 wrogów: <span class="mag">' + f0((15 + 0.3 * D.ap) * M(i)) + '</span> (15 + 30% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 14); postawDzialko('tesla', 10, { obr: (15 + 0.3 * D.ap) * M(i), co: 1, zr: 'Wieża Tesli' }); } },
  { id: 'ul', t: 1, ik: '🐝', n: 'Ul', cd: 9,
    opis: i => 'Co <b>9 s</b> wypuszcza 3 pszczoły (6 s). Każda żądli co 0,6 s: <span class="fiz">' + f0((6 + 0.15 * D.ad + 0.15 * D.ap) * M(i)) + '</span> (6 + 15% ⚔️ + 15% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 9); for (let n = 0; n < 3; n++) dodajStwora('pszczola', gracz.x, gracz.y, 6, { obr: (6 + 0.15 * D.ad + 0.15 * D.ap) * M(i), zr: 'Ul', ruchomy: true }); } },
  { id: 'totemOgnia', t: 1, ik: '🗿', n: 'Totem Ognia', cd: 15,
    opis: i => 'Co <b>15 s</b> stawia totem (10 s): wrogowie w promieniu 100 płoną — <span class="mag">' + f0((10 + 0.2 * D.ap) * M(i)) + '</span> (10 + 20% ✨) co 0,5 s.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 15); dodajStwora('totem', gracz.x, gracz.y, 10, { obr: (10 + 0.2 * D.ap) * M(i), zr: 'Totem Ognia', aura: 100 * mnObszaru() }); } },
  { id: 'echoOstrza', t: 1, ik: '🔁', n: 'Echo Ostrza',
    opis: i => 'Co <b>' + Math.max(3, 7 - (i.gw || 0)) + '.</b> atak broni głównej powtarza się po chwili (echo pełnej mocy).',
    naAtak(i, b, cel, o) { if (o && o.echo) return; i.licz = (i.licz || 0) + 1; if (i.licz % Math.max(3, 7 - (i.gw || 0))) return; opoznione(0.15, () => echoAtaku(b, cel)); } },
  { id: 'iskrownik', t: 1, ik: '🔋', n: 'Iskrownik', cd: 4,
    opis: i => 'Co 4 s następny atak razi piorunem do 4 wrogów: <span class="mag">' + f0((30 + 0.3 * D.ap + 0.2 * D.ad) * M(i)) + '</span> (30 + 30% ✨ + 20% ⚔️).',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 4); lancuch(gracz, w, (30 + 0.3 * D.ap + 0.2 * D.ad) * M(i), 'mag', 4, 160, 1, 'Iskrownik'); } },
  { id: 'ostrzeBurzy', t: 1, ik: '⛈️', n: 'Ostrze Burzy', cd: 6,
    opis: i => 'Co 6 s następny atak zadaje dodatkowo <span class="mag">' + f0((40 + 0.5 * D.ad) * M(i)) + '</span> (40 + 50% ⚔️) i daje +40 prędkości ruchu na 1,5 s.',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 6); zadaj(w, (40 + 0.5 * D.ad) * M(i), 'mag', { zr: 'Ostrze Burzy' }); efektBlysk(w.x, w.y, '#9fd8ff'); dodajBuff('burza', { ms: 40 }, 1.5); } },
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
    opis: i => 'Ataki <b>wręcz</b> rozcinają też wrogów wokół celu (r 65): <span class="fiz">' + Math.round(50 * M(i)) + '%</span> obrażeń.',
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
    opis: i => 'Co 8 s trafienie <b>elity lub bossa</b> zadaje <span class="fiz">' + f0((60 + 0.06 * D.hpMax) * M(i)) + '</span> (60 + 6% maks. zdrowia) i daje <b>na stałe +8</b> maks. zdrowia. Zebrane: <b>' + (i.stos || 0) + '</b>.',
    naTrafienie(i, w, k) { if (!(w.elita || w.boss) || !cdGotowe(i)) return; cdUstaw(i, 8); zadaj(w, (60 + 0.06 * D.hpMax) * M(i), 'fiz', { zr: 'Stalowe Serce' }); i.stos = (i.stos || 0) + 1; przeliczStaty(); efektBlysk(w.x, w.y, '#ff6a6a'); },
    statyFlat(i, s) { s.hpMax += 8 * (i.stos || 0); } },
  { id: 'rozlupywacz', t: 1, ik: '⚒️', n: 'Czarny Rozłupywacz',
    opis: i => 'Obrażenia <span class="fiz">fizyczne</span> kruszą pancerz celu o ' + Math.round(5 * M(i)) + '% (do 30%).',
    naObrazenia(i, w, v, typ) { if (typ === 'fiz') w.krusz = Math.min(0.3, (w.krusz || 0) + 0.05 * M(i)); } },

  // ======================= EPICKIE (T3) =======================
  { id: 'dzialoGromu', t: 2, ik: '💥', n: 'Działo Gromu', cd: 14,
    opis: i => 'Co <b>14 s</b> stawia ciężkie działo (12 s). Co 1,2 s strzela pociskiem wybuchowym (r 60): <span class="fiz">' + f0((30 + 0.5 * D.ad + 0.3 * D.ap) * M(i)) + '</span> (30 + 50% ⚔️ + 30% ✨).',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 14); postawDzialko('dzialoGromu', 12, { obr: (30 + 0.5 * D.ad + 0.3 * D.ap) * M(i), co: 1.2, zr: 'Działo Gromu' }); } },
  { id: 'drzewoZycia', t: 2, ik: '🌲', n: 'Drzewo Życia', cd: 25,
    opis: i => 'Co <b>25 s</b> wyrasta drzewo (24 s): co 3 s zrzuca 2 owoce (leczą ' + fmt(7 * M(i)) + '% maks. zdrowia), a drużyna w promieniu 120 regeneruje 1,5% maks. zdrowia na sekundę.',
    tik(i) { if (!cdGotowe(i) || !fala.aktywna) return; cdUstaw(i, 25); dodajStwora('krzak', gracz.x + losowo(-30, 30), gracz.y + losowo(-30, 30), 24, { co: 3, lecz: 0.07 * M(i), ikOwocu: '🍐', ik: '🌲', owoce: 2, regen: 0.015 * M(i), aura: 120 }); } },
  { id: 'chowaniec', t: 2, ik: '🐺', n: 'Wilczy Chowaniec',
    opis: i => 'Wilk biegnie przy Tobie i gryzie co 0,8 s: <span class="fiz">' + f0((15 + 0.4 * D.ad + 0.01 * D.hpMax) * M(i)) + '</span> (15 + 40% ⚔️ + 1% maks. zdrowia). Jest niezniszczalny.',
    tik(i) { if (!fala.aktywna) return; if (!i._s || i._s.czas <= 0 || stwory.indexOf(i._s) < 0) i._s = dodajStwora('wilk', gracz.x + 20, gracz.y, 9999, { ruchomy: true, zr: 'Wilczy Chowaniec', zrodlo: i });
      i._s.obr = (15 + 0.4 * D.ad + 0.01 * D.hpMax) * M(i); } },
  { id: 'botrk', t: 2, ik: '👑', n: 'Ostrze Zniszczonego Króla',
    opis: i => 'Ataki zadają dodatkowo <span class="fiz">' + fmt(6 * M(i)) + '%</span> AKTUALNEGO zdrowia celu jako obrażenia fizyczne (bossowie: połowa) i leczą o 30% tej wartości.',
    naTrafienie(i, w, k) { if (w.hp > 0) { const v = zadaj(w, w.hp * 0.06 * M(i) * (w.boss ? 0.5 : 1), 'fiz', { onhit: true, zr: 'Ostrze Zniszczonego Króla' }); if (v > 0) leczWampirem(v * 0.3, 'BotRK'); } } },
  { id: 'huragan', t: 2, ik: '🌪️', n: 'Huragan Runaana',
    opis: i => 'Ataki <b>dystansowe</b> wystrzeliwują 2 dodatkowe pociski w pobliskich wrogów (<span class="fiz">' + Math.round(40 * M(i)) + '%</span> obrażeń, nakładają efekty przy trafieniu).',
    naAtak(i, b, cel) { const B = BRONIE[b.rodzaj]; if (!B.dystans) return; najblizsi(cel.x, cel.y, 260, 2, [cel]).forEach(w => strzalPomocniczy(b, w, 0.4 * M(i))); } },
  { id: 'guinsoo', t: 2, ik: '🟧', n: 'Ostrze Furii Guinsoo',
    opis: i => 'Twoja szansa na kryt nie działa — zamiast tego każdy 1% daje <span class="fiz">' + fmt(1.5 * M(i)) + '</span> obrażeń fizycznych przy trafieniu. Co 3. atak nakłada efekty przy trafieniu <b>dwukrotnie</b>.',
    bezKryt: true,
    statyPost(i, s) { s.onHitFiz += 1.5 * s.kryt * M(i); },
    naAtak(i, b) { i.licz = (i.licz || 0) + 1; if (i.licz % 3 === 0) b._podwojnyOnHit = true; } },
  { id: 'trojca', t: 2, ik: '🔺', n: 'Trójca', cd: 4,
    opis: i => '<b>Czaroostrze:</b> co 4 s następny atak zadaje dodatkowo <span class="fiz">' + f0((30 + 1.0 * D.ad) * M(i)) + '</span> (30 + 100% ⚔️) i daje +25 prędkości ruchu na 2 s.',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 4); zadaj(w, (30 + D.ad) * M(i), 'fiz', { zr: 'Trójca' }); efektBlysk(w.x, w.y, '#ffd24a'); dodajBuff('trojca', { ms: 25 }, 2); } },
  { id: 'krwiopijca', t: 2, ik: '🩸', n: 'Krwiopijca',
    opis: i => 'Nadmiar leczenia zamienia się w tarczę (do <b>' + f0((60 + 0.12 * D.hpMax) * M(i)) + '</b>).',
    naNadleczenie(i, v) { const max = (60 + 0.12 * D.hpMax) * M(i); const ob = tarczaSuma(); if (ob < max) dajTarcze(Math.min(v, max - ob), 6, true); } },
  { id: 'rabadon', t: 2, ik: '🎩', n: 'Kapelusz Rabadona',
    opis: i => 'Zwiększa Twoją moc umiejętności o <b>' + Math.round(30 * M(i)) + '%</b>.',
    statyMnoz(i, s) { s.ap *= 1 + 0.3 * M(i); } },
  { id: 'liandry', t: 2, ik: '🕯️', n: 'Udręka Liandry',
    opis: i => 'Obrażenia <span class="mag">magiczne</span> podpalają: <span class="mag">' + fmt(2 * M(i)) + '%</span> maks. zdrowia celu na sekundę przez 3 s (bossowie: 0,6%).',
    naObrazenia(i, w, v, typ, o) { if (typ === 'mag' && !o.dot && w.hp > 0) podpal(w, w.hpMax * (w.boss ? 0.006 : 0.02) * M(i), 3, 'mag', 'Udręka Liandry'); } },
  { id: 'zhonya', t: 2, ik: '⏳', n: 'Klepsydra Zhonyi', cd: 70,
    opis: () => 'Gdy zdrowie spadnie poniżej 25%: <b>zastój na 2 s</b> — jesteś niewrażliwy, ale nie ruszasz się i nie atakujesz. Odnowienie 70 s.',
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp > 0 && gracz.hp < D.hpMax * 0.25) { cdUstaw(i, 70); gracz.zastoj = 2; gracz.niewr = Math.max(gracz.niewr, 2); tekstSwiat(gracz.x, gracz.y - 28, '⏳ Zastój!', '#ffe08a'); DZ.tarcza(); } } },
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
  { id: 'luden', t: 2, ik: '🔊', n: 'Echo Ludena', cd: 6,
    opis: i => 'Co 6 s następne obrażenia magiczne wywołują echo: <span class="mag">' + f0((80 + 0.35 * D.ap) * M(i)) + '</span> (80 + 35% ✨) w cel i 3 pobliskich wrogów.',
    naObrazenia(i, w, v, typ, o) { if (typ !== 'mag' || o.zr === 'Echo Ludena' || !cdGotowe(i)) return; cdUstaw(i, 6); const obr = (80 + 0.35 * D.ap) * M(i);
      [w].concat(najblizsi(w.x, w.y, 200, 3, [w])).forEach(c => { dodajBlyskawice(w.x, w.y, c.x, c.y, '#c9a8ff'); zadaj(c, obr, 'mag', { zr: 'Echo Ludena' }); }); } },
  { id: 'shiv', t: 2, ik: '🗡', n: 'Nóż Statikka', cd: 3,
    opis: i => 'Co 3 s następny atak puszcza łańcuch piorunów na 5 celów: <span class="mag">' + f0((35 + 0.35 * D.ad + 0.2 * D.ap) * M(i)) + '</span> (35 + 35% ⚔️ + 20% ✨).',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 3); lancuch(gracz, w, (35 + 0.35 * D.ad + 0.2 * D.ap) * M(i), 'mag', 5, 170, 1, 'Nóż Statikka'); } },
  { id: 'kraken', t: 2, ik: '🦑', n: 'Pogromca Krakena',
    opis: i => 'Co 3. atak zadaje dodatkowo <span class="praw">' + f0((50 + 0.5 * D.ad) * M(i)) + '</span> (50 + 50% ⚔️) obrażeń prawdziwych.',
    naTrafienie(i, w, k) { if (!k.glowny) return; i.licz = (i.licz || 0) + 1; if (i.licz % 3 === 0) { zadaj(w, (50 + 0.5 * D.ad) * M(i), 'praw', { zr: 'Pogromca Krakena' }); efektBlysk(w.x, w.y, '#7ae0ff'); } } },
  { id: 'hydra', t: 2, ik: '🐉', n: 'Hydra Tytana',
    opis: i => 'Ataki zadają dodatkowo <span class="fiz">' + fmt(1.5 * M(i)) + '%</span> maks. zdrowia przy trafieniu, a wrogowie wokół celu (r 70) dostają <span class="fiz">' + fmt(2.5 * M(i)) + '%</span> maks. zdrowia.',
    statyPost(i, s) { s.onHitFiz += s.hpMax * 0.015 * M(i); },
    naTrafienie(i, w, k) { if (!k.glowny) return; const v = D.hpMax * 0.025 * M(i); obszarowe(w.x, w.y, 70, '#c0a080', o => { if (o !== w) zadaj(o, v, 'fiz', { obszar: true, zr: 'Hydra Tytana' }); }, true); } },
  { id: 'navori', t: 2, ik: '🔵', n: 'Ostrze Navori',
    opis: i => 'Trafienia krytyczne skracają odnowienie wszystkich broni, przedmiotów i umiejętności o <b>' + fmt(0.4 * M(i)) + ' s</b>.',
    naKryt(i) { skrocCd(0.4 * M(i)); } },
  { id: 'czarnyOgien', t: 2, ik: '🏮', n: 'Pochodnia Czarnego Ognia',
    opis: i => 'Obrażenia magiczne podpalają: <span class="mag">' + f0((30 + 0.12 * D.ap) * M(i)) + '</span> (30 + 12% ✨) przez 3 s. +3% obrażeń za każdego płonącego wroga w pobliżu (maks. 30%).',
    naObrazenia(i, w, v, typ, o) { if (typ === 'mag' && !o.dot && w.hp > 0) podpal(w, (30 + 0.12 * D.ap) * M(i) / 3, 3, 'mag', 'Pochodnia Czarnego Ognia'); },
    modZadanych(i) { if (!i._t || czasGry - i._t > 0.3) { i._t = czasGry; i._n = wrogowie.filter(w => !w.martwy && w.ogien && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 300).length; } return 1 + Math.min(0.3, 0.03 * (i._n || 0)); } },
  { id: 'zmarzlina', t: 2, ik: '🧊', n: 'Wieczna Zmarzlina', cd: 10,
    opis: i => 'Co 10 s lodowy stożek w najbliższego wroga: <span class="mag">' + f0((100 + 0.5 * D.ap) * M(i)) + '</span> (100 + 50% ✨) i unieruchomienie na 1 s.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 230); if (!c) return; cdUstaw(i, 10);
      stozek(kat(gracz, c), 240, 0.6, '#cfefff', w => { zadaj(w, (100 + 0.5 * D.ap) * M(i), 'mag', { zr: 'Wieczna Zmarzlina' }); oglusz(w, 1, { zrodlo: 'Zmarzlina' }); }); } },
  { id: 'pasRakietowy', t: 2, ik: '🎇', n: 'Pas Rakietowy Hextech', cd: 12,
    opis: i => 'Co 12 s wystrzeliwuje 7 pocisków w stożku: <span class="mag">' + f0((60 + 0.25 * D.ap) * M(i)) + '</span> (60 + 25% ✨) każdy.',
    tik(i) { if (!cdGotowe(i)) return; const c = najblizszyWrog(gracz.x, gracz.y, 260); if (!c) return; cdUstaw(i, 12); const k0 = kat(gracz, c);
      for (let n = 0; n < 7; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: k0 + (n - 3) * 0.13, predkosc: 520, obr: (60 + 0.25 * D.ap) * M(i), typ: 'mag', kolor: '#ffb04a', ksztalt: 'kula', zr: 'Pas Rakietowy', zycie: 0.7 }); DZ.magia(); } },
  { id: 'pijawka', t: 2, ik: '🧛', n: 'Pijawka Krwi', cd: 9,
    opis: i => 'Co 9 s wir: <span class="fiz">' + f0((80 + 1.0 * D.ad) * M(i)) + '</span> (80 + 100% ⚔️) w promieniu 130; leczy 8% brakującego zdrowia + 2% za każdego trafionego.',
    tik(i) { if (!cdGotowe(i) || policzWrogow(gracz.x, gracz.y, 130) === 0) return; cdUstaw(i, 9); let n = 0;
      aura(130, '#c0392b', w => { n++; zadaj(w, (80 + D.ad) * M(i), 'fiz', { obszar: true, zr: 'Pijawka Krwi' }); }, true);
      leczGracza((D.hpMax - gracz.hp) * 0.08 + D.hpMax * 0.02 * Math.min(n, 8), 'Pijawka Krwi'); } },
  { id: 'midas', t: 2, ik: '🪙', n: 'Monety Midasa',
    opis: i => '<b>' + Math.round(7 * M(i)) + '%</b> szansy, że podniesiona moneta jest warta 5×.',
    mnozMonety(i) { return Math.random() < 0.07 * M(i) ? 5 : 1; } },
  { id: 'mejai', t: 2, ik: '📗', n: 'Księga Mejai',
    opis: i => 'Co 15 zabójstw +1 ładunek: <b>+' + fmt(2.5 * M(i)) + ' ✨</b> na stałe (maks. 100). Przy 40 ładunkach +10% prędkości ruchu. Ładunki: <b>' + Math.min(100, Math.floor((i.zab || 0) / 15)) + '</b>.',
    naZabicie(i) { i.zab = (i.zab || 0) + 1; if (i.zab % 15 === 0 && i.zab <= 1500) przeliczStaty(); },
    statyFlat(i, s) { const n = Math.min(100, Math.floor((i.zab || 0) / 15)); s.ap += 2.5 * n * M(i); if (n >= 40) s.ms += 14; } },

  // ======================= LEGENDARNE (T4) =======================
  { id: 'korona', t: 3, ik: '👸', n: 'Korona Królowej', cd: 10,
    opis: i => 'Osłona: następne obrażenia są mniejsze o <b>' + Math.round(Math.min(90, 75 * M(i))) + '%</b>. Po zużyciu odnawia się po 10 s.',
    modOtrzymanych(i, v, typ, o) { if (cdGotowe(i) && v > 0 && !o.dot) { cdUstaw(i, 10); efektBlysk(gracz.x, gracz.y, '#ffe08a'); return 1 - Math.min(0.9, 0.75 * M(i)); } return 1; } },
  { id: 'wichura', t: 3, ik: '🌬️', n: 'Wichura', cd: 7,
    opis: i => 'Co 7 s 3 naprowadzane pociski w najsłabszego wroga w pobliżu: <span class="fiz">' + f0((50 + 0.2 * D.ad) * M(i)) + '</span> (50 + 20% ⚔️) każdy, do +50% przeciw rannym.',
    tik(i) { if (!cdGotowe(i)) return; const c = najslabszyWrog(gracz.x, gracz.y, 280); if (!c) return; cdUstaw(i, 7);
      for (let n = 0; n < 3; n++) wystrzel({ x: gracz.x, y: gracz.y, kat: kat(gracz, c) + (n - 1) * 0.5, predkosc: 430, naprowadza: 8, cel: c, obr: (50 + 0.2 * D.ad) * M(i) * (1 + 0.5 * (1 - c.hp / c.hpMax)), typ: 'fiz', kolor: '#bff0ff', ksztalt: 'strzala', zr: 'Wichura', zycie: 1.4 }); } },
  { id: 'sunderer', t: 3, ik: '⚜️', n: 'Boski Rozłamywacz', cd: 3,
    opis: i => 'Co 3 s następny atak zadaje <span class="fiz">' + fmt(8 * M(i)) + '%</span> maks. zdrowia celu (bossowie: 3%) i leczy Cię o 60% tej wartości (maks. 6% Twojego zdrowia).',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; cdUstaw(i, 3); const v = zadaj(w, w.hpMax * (w.boss ? 0.03 : 0.08) * M(i), 'fiz', { zr: 'Boski Rozłamywacz' }); leczGracza(Math.min(v * 0.6, D.hpMax * 0.06), 'Boski Rozłamywacz'); efektBlysk(w.x, w.y, '#ffe08a'); } },
  { id: 'zacmienie', t: 3, ik: '🌘', n: 'Zaćmienie', cd: 6,
    opis: i => 'Dwa trafienia tego samego wroga w 1,5 s: <span class="fiz">' + fmt(6 * M(i)) + '%</span> jego maks. zdrowia (bossowie 2,5%) i tarcza <b>' + f0((40 + 0.35 * D.ad) * M(i)) + '</b>. Odnowienie 6 s.',
    naTrafienie(i, w, k) { if (!k.glowny || !cdGotowe(i)) return; if (i.cel === w && czasGry - i.czas < 1.5) { cdUstaw(i, 6); i.cel = null; zadaj(w, w.hpMax * (w.boss ? 0.025 : 0.06) * M(i), 'fiz', { zr: 'Zaćmienie' }); dajTarcze((40 + 0.35 * D.ad) * M(i), 2); efektBlysk(w.x, w.y, '#c9a8ff'); } else { i.cel = w; i.czas = czasGry; } } },
  { id: 'shieldbow', t: 3, ik: '🏹', n: 'Nieśmiertelny Łuk', cd: 55,
    opis: i => 'Gdy zdrowie spadnie poniżej 30%: tarcza <b>' + f0((250 + 0.2 * D.hpMax) * M(i)) + '</b> (250 + 20% maks. zdrowia) na 3 s i +20% kradzieży życia na 6 s. Odnowienie 55 s.',
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp > 0 && gracz.hp < D.hpMax * 0.3) { cdUstaw(i, 55); dajTarcze((250 + 0.2 * D.hpMax) * M(i), 3); dodajBuff('shieldbow', { kradziez: 8 }, 6); } } },
  { id: 'zniwiarz', t: 3, ik: '🌑', n: 'Żniwiarz Nocy',
    opis: i => 'Pierwsze trafienie każdego wroga zadaje dodatkowo <span class="mag">' + f0((100 + 0.2 * D.ap) * M(i)) + '</span> (100 + 20% ✨) obrażeń magicznych.',
    naObrazenia(i, w, v, typ, o) { if (w._zniw || o.zr === 'Żniwiarz Nocy') return; w._zniw = 1; zadaj(w, (100 + 0.2 * D.ap) * M(i), 'mag', { zr: 'Żniwiarz Nocy' }); } },
  { id: 'warmog', t: 3, ik: '🟩', n: 'Kirys Warmoga',
    opis: i => 'Jeśli przez 4 s nie otrzymasz obrażeń, odzyskujesz <b>' + fmt(5 * M(i)) + '%</b> maks. zdrowia na sekundę. +20% maks. zdrowia.',
    statyMnoz(i, s) { s.hpMax *= 1.2; },
    tik(i, dt) { if (czasGry - (gracz.ostTrafienie || -99) > 4 && gracz.hp < D.hpMax) leczGracza(D.hpMax * 0.05 * M(i) * dt, 'Kirys Warmoga', true); } },
  { id: 'lodoweSerce', t: 3, ik: '❄️', n: 'Lodowe Serce',
    opis: i => 'Wrogowie w promieniu 220 atakują o <b>' + Math.round(Math.min(60, 25 * M(i))) + '%</b> wolniej i poruszają się o 15% wolniej.',
    tik(i) { const r = 220 * mnObszaru(); wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < r + w.r) { spowolnij(w, 0.15, 0.2); w.zamarzniecieAtaku = Math.max(w.zamarzniecieAtaku || 0, Math.min(0.6, 0.25 * M(i))); w._zaT = 0.2; } }); } },
  { id: 'esencja', t: 3, ik: '🔷', n: 'Złodziej Esencji',
    opis: i => 'Trafienia krytyczne skracają odnowienia o 0,25 s. Gdy coś się odnowi i aktywuje, następny atak zadaje dodatkowo <span class="fiz">' + f0((20 + 0.6 * D.ad) * M(i)) + '</span> (20 + 60% ⚔️).',
    naKryt(i) { skrocCd(0.25); },
    naAktywacji(i, zrodlo) { if (zrodlo !== i) i.gotowy = 1; },
    naTrafienie(i, w, k) { if (k.glowny && i.gotowy) { i.gotowy = 0; zadaj(w, (20 + 0.6 * D.ad) * M(i), 'fiz', { zr: 'Złodziej Esencji' }); } } },
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
];
const DEF_PRZ = {}; PRZEDMIOTY.forEach(p => { DEF_PRZ[p.id] = p; if (p.unik === undefined) p.unik = true; });

function cenaPrzedmiotu(d) { return Math.round((d.cena || CENY_TIERU[d.t]) * mnCeny()); }
function cenaUlepszenia(inst) { const d = DEF_PRZ[inst.id]; return Math.round((d.cena || CENY_TIERU[d.t]) * (0.55 + 0.35 * (inst.gw || 0)) * mnCeny()); }
function wartoscSprzedazy(inst) { const d = DEF_PRZ[inst.id]; const baza = d.t === 'p' ? 120 : (d.cena || CENY_TIERU[d.t]); return Math.round(baza * mnCeny() * (0.4 + 0.15 * (inst.gw || 0))); }
function nowyPrzedmiot(id) { return { id: id, gw: 0, cd: 0 }; }
function gwiazdki(n) { return n ? '★'.repeat(n) : ''; }

// =====================================================================
//  PRZEDMIOTY PRYZMATYCZNE — tylko z Pryzmatycznego Kowadła
// =====================================================================
const PRYZMATY = [
  { id: 'poglos', ik: '🔔', n: 'Pogłos', s: { pancerz: 40, odpMag: 40, as: 30 },
    opis: i => 'Zyskujesz <b>' + fmt(2 * M(i)) + ' maks. zdrowia</b> za każdy 1% premii do prędkości ataku. '
      + 'Ataki zadają dodatkowo <span class="mag">' + fmt(2 * M(i)) + '% maks. zdrowia</span> obrażeń magicznych przy trafieniu i mają 12% szansy ogłuszyć na 0,5 s. '
      + '<b>Twoje ogłuszenia nakładają efekty przy trafieniu 3 razy.</b>',
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
    opis: i => 'Co 2,5 s trafienie przywołuje 3 runiczne ostrza wokół celu. Po 0,8 s tną wszystkich w promieniu 85: <span class="mag">3 × ' + f0((25 + 0.25 * D.ad + 0.25 * D.ap) * M(i)) + '</span> (25 + 25% ⚔️ + 25% ✨) obrażeń magicznych.',
    naTrafienie(i, w) { if (!cdGotowe(i)) return; cdUstaw(i, 2.5); runyWokol(w, (25 + 0.25 * D.ad + 0.25 * D.ap) * M(i)); } },
  { id: 'hazard', ik: '🎲', n: 'Ostrze Hazardzisty', s: { as: 40, kryt: 10 },
    opis: i => 'Ataki zadają dodatkowo <span class="mag">' + f0((4 + 0.03 * gracz.zloto) * M(i)) + '</span> (4 + 3% Twojego złota, bez limitu) obrażeń magicznych przy trafieniu. '
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
  { id: 'kulaDetonacji', ik: '💣', n: 'Kula Detonacji', s: { ap: 60, hpMax: 150 },
    opis: i => 'Zabici wrogowie <b>wybuchają</b> (r 90): <span class="mag">' + f0((30 + 0.2 * D.ap) * M(i)) + ' + 8% maks. zdrowia ofiary</span> obrażeń magicznych. Wybuchy mogą wywołać reakcję łańcuchową.',
    naZabicie(i, w) { const x = w.x, y = w.y, v = (30 + 0.2 * D.ap + w.hpMax * 0.08) * M(i);
      opoznione(0.08, () => obszarowe(x, y, 90, '#ff9a3c', o => zadaj(o, v, 'mag', { obszar: true, zr: 'Kula Detonacji' }))); } },
  { id: 'podcinacz', ik: '🦵', n: 'Podcinacz Ścięgien', s: { ad: 30, as: 30 },
    opis: i => 'Co 4. atak ogłusza cel na <b>' + fmt(0.75 * M(i)) + ' s</b> i spowalnia wszystkich wokół (r 90) o 40% na 1,5 s.',
    naTrafienie(i, w, k) { if (!k.glowny || k.zOgluszenia) return; i.licz = (i.licz || 0) + 1; if (i.licz % 4) return;
      oglusz(w, 0.75 * M(i), { zrodlo: 'Podcinacz' }); obszarowe(w.x, w.y, 90, '#9fd8ff', o => spowolnij(o, 0.4, 1.5), true); } },
  { id: 'gromochron', ik: '⚡', n: 'Gromochron', s: { hpMax: 300, ap: 50 },
    opis: i => 'Co sekundę piorun uderza w losowego wroga w pobliżu (260): <span class="mag">' + f0((25 + 0.1 * D.ap + 0.01 * D.hpMax) * M(i)) + '</span> (25 + 10% ✨ + 1% maks. zdrowia) obrażeń magicznych.',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t < 1) return; i.t = 0; const c = losowyWrog(gracz.x, gracz.y, 260); if (!c) return;
      dodajBlyskawice(c.x, c.y - 140, c.x, c.y, '#ffe066'); DZ.piorun(); zadaj(c, (25 + 0.1 * D.ap + 0.01 * D.hpMax) * M(i), 'mag', { zr: 'Gromochron' }); } },
  { id: 'piekielnyTopor', ik: '🪓', n: 'Topór Piekielnego Ognia', s: { ad: 60, as: 15 },
    opis: i => 'Ataki podpalają: <span class="fiz">' + fmt(3 * M(i)) + '%</span> maks. zdrowia celu na sekundę przez 3 s (bossowie 1%). Co 3. atak wybucha ogniem wokół celu (r 70): <span class="fiz">60%</span> obrażeń ataku.',
    naTrafienie(i, w, k) { podpal(w, w.hpMax * (w.boss ? 0.01 : 0.03) * M(i), 3, 'fiz', 'Topór Piekielnego Ognia');
      if (!k.glowny || !k.bron) return; i.licz = (i.licz || 0) + 1; if (i.licz % 3) return; const v = (k.zadaneSurowe || 0) * 0.6;
      obszarowe(w.x, w.y, 70, '#ff6a2a', o => { if (o !== w) zadaj(o, v, 'fiz', { obszar: true, zr: 'Topór Piekielnego Ognia' }); }); } },
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
    opis: i => 'Ogłuszeni lub spowolnieni przez Ciebie wrogowie zostają <b>naznaczeni</b> na 4 s: otrzymują <b>+' + Math.round(Math.min(40, 20 * M(i))) + '%</b> obrażeń, a gdy zginą, wybuchają (r 80) za 15% swojego maks. zdrowia.',
    naOgluszenie(i, w) { w.naznaczony = 4; },
    naSpowolnieniu(i, w) { w.naznaczony = 4; },
    modZadanych(i, w) { return w.naznaczony > 0 ? 1 + Math.min(0.4, 0.2 * M(i)) : 1; },
    naZabicie(i, w) { if (!(w.naznaczony > 0)) return; const x = w.x, y = w.y, v = w.hpMax * 0.15;
      opoznione(0.05, () => obszarowe(x, y, 80, '#c0392b', o => zadaj(o, v, 'fiz', { obszar: true, zr: 'Okrucieństwo' }))); } },
  { id: 'pozeracz', ik: '🍖', n: 'Pożeracz Ciał', s: { ad: 40, hpMax: 200 },
    opis: i => 'Każde zabójstwo daje <b>na stałe</b> +0,25 ⚔️ i +1 maks. zdrowia (elita ×3, boss ×10; maks. 5000 ładunków). Zjedzone: <b>' + (i.stos || 0) + '</b>.',
    naZabicie(i, w) { if ((i.stos || 0) >= 5000) return; i.stos = Math.min(5000, (i.stos || 0) + (w.boss ? 10 : (w.elita ? 3 : 1))); if (w.elita || w.boss || i.stos % 5 === 0) oznaczStaty(); },
    statyFlat(i, s) { s.ad += 0.25 * (i.stos || 0) * M(i); s.hpMax += (i.stos || 0) * M(i); } },
  { id: 'hemomanta', ik: '🩸', n: 'Hełm Hemomanty', s: { hpMax: 500, regen: 2 },
    opis: i => 'Co 3 s krwawa fala (r 120): <span class="mag">' + f0(D.hpMax * 0.04 * M(i)) + '</span> (4% maks. zdrowia) obrażeń magicznych. Leczysz się o 30% zadanych (maks. 6% zdrowia).',
    tik(i, dt) { i.t = (i.t || 0) + dt; if (i.t < 3) return; i.t = 0; let suma = 0;
      aura(120, '#c0392b', w => { suma += zadaj(w, D.hpMax * 0.04 * M(i), 'mag', { obszar: true, zr: 'Hełm Hemomanty' }); }, true);
      if (suma > 0) leczGracza(Math.min(suma * 0.3, D.hpMax * 0.06), 'Hełm Hemomanty'); } },
  { id: 'zefir', ik: '🕊️', n: 'Zefir', s: { as: 50, ms: 30, unik: 12, pociski: 1 },
    opis: () => 'Broń główna strzelająca wypuszcza <b>dodatkowy pocisk</b>.' },
  { id: 'lalkarz', ik: '🎭', n: 'Lalkarz', s: { ap: 40, as: 30 },
    opis: i => 'Trafienia oplatają wroga nićmi. Przy <b>4</b> niciach wróg (nie boss) zostaje przejęty na <b>' + fmt(4 * M(i)) + ' s</b> — walczy po Twojej stronie, zadając <span class="mag">3× swój atak + 30% ✨</span> innym wrogom. Bossowie są tylko ogłuszani.',
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
  { id: 'lopatka', ik: '🥄', n: 'Złota Łopatka', s: { ad: 30, ap: 50, as: 30, kryt: 20, hpMax: 250, pancerz: 30, odpMag: 30, haste: 20, ms: 15 },
    opis: () => 'Trochę wszystkiego. Naprawdę wszystkiego.' },
  { id: 'wooglet', ik: '🧙', n: 'Kapelusz Wiedźmy Wooglet', s: { ap: 100, pancerz: 30 }, cd: 60,
    opis: i => 'Moc umiejętności <b>+' + Math.round(40 * M(i)) + '%</b>. Gdy zdrowie spadnie poniżej 25%: zastój na 2,5 s. Odnowienie 60 s.',
    statyMnoz(i, s) { s.ap *= 1 + 0.4 * M(i); },
    naOtrzymanie(i) { if (cdGotowe(i) && gracz.hp > 0 && gracz.hp < D.hpMax * 0.25) { cdUstaw(i, 60); gracz.zastoj = 2.5; gracz.niewr = Math.max(gracz.niewr, 2.5); tekstSwiat(gracz.x, gracz.y - 28, '⏳ Zastój!', '#ffe08a'); } } },
  { id: 'gwiazda', ik: '🌟', n: 'Gwiazda Neutronowa', s: { ap: 60, obszar: 40 },
    opis: i => 'Obrażenia <b>obszarowe</b> zadają <b>+' + Math.round(25 * M(i)) + '%</b>.',
    modZadanych(i, w, typ, o) { return o.obszar ? 1 + 0.25 * M(i) : 1; } },
  { id: 'paktKrwi', ik: '🫀', n: 'Pakt Krwi', s: { hpMax: 600, kradziez: 3 },
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
    opis: () => 'Twoje ataki nakładają efekty przy trafieniu <b>dwukrotnie</b>.', podwojnyOnHit: true },
  { id: 'klingaRezonansu', ik: '🎼', n: 'Klinga Rezonansu', s: { kryt: 20, krytObr: 20 },
    opis: () => 'Trafienia <b>krytyczne</b> nakładają efekty przy trafieniu jeszcze <b>2 razy</b>.', onHitKryt: 2 },
  { id: 'serceGolema', ik: '🗿', n: 'Serce Golema', s: { pancerz: 40 },
    opis: () => 'Każdy punkt pancerza daje <b>3 maks. zdrowia</b>, a ataki zadają <span class="fiz">15% pancerza</span> jako obrażenia fizyczne przy trafieniu (teraz +' + f0(D.pancerz * 3) + ' ❤️, +' + f0(D.pancerz * 0.15) + ' przy trafieniu).',
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
    opis: () => 'Twoje ⚔️ zamieniają się w ✨ (×2), a <b>wszystkie</b> ataki zadają obrażenia <span class="mag">magiczne</span>.',
    wszystkoMag: true, statyPost(i, s) { s.ap += 2 * Math.max(0, s.ad); s.ad = 0; } },
  { id: 'zelaznaDziewica', ik: '⚙️', n: 'Żelazna Dziewica', s: { pancerz: 30, odpMag: 30, hpMax: 150 },
    opis: () => 'Otrzymujesz <b>15% więcej</b> obrażeń, ale każde trafienie odbija <span class="praw">100%</span> obrażeń (przed obroną) jako prawdziwe w napastnika i wrogów w promieniu 80.',
    modOtrzymanych() { return 1.15; },
    naOtrzymanie(i, v, typ, o) { if (!o.wrog || o.dot) return; const x = o.wrog.x, y = o.wrog.y, ob = o.przed || v; obszarowe(x, y, 80, '#d8d8e4', w => zadaj(w, ob, 'praw', { zr: 'Żelazna Dziewica', odbicie: true, obszar: true }), true); } },
  { id: 'rytualKrwi', ik: '🔪', n: 'Rytuał Krwi', s: { hpMax: 400 },
    opis: () => 'Tracisz 1,5% aktualnego zdrowia co sekundę. Każdy 1% brakującego zdrowia daje <b>+1,2%</b> obrażeń i <b>+0,5%</b> kradzieży życia.',
    tik(i, dt) { if (fala.aktywna) gracz.hp = Math.max(1, gracz.hp - gracz.hp * 0.015 * dt); },
    statyDyn(i, s) { s.kradziez += 50 * Math.max(0, 1 - gracz.hp / Math.max(1, s.hpMax)); },
    modZadanych() { return 1 + 1.2 * Math.max(0, 1 - gracz.hp / D.hpMax); } },
  { id: 'wagaSprawiedliwosci', ik: '⚖️', n: 'Waga Sprawiedliwości', s: { ad: 20, ap: 20 },
    opis: () => 'Twoje ⚔️ i ✨ wyrównują się do <b>wyższej</b> z nich.',
    statyPost(i, s) { const m = Math.max(s.ad, s.ap); s.ad = m; s.ap = m; } },
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
    opis: () => 'Co 5 s tarcza <b>5% maks. zdrowia</b>. Gdy masz tarczę, ataki zadają dodatkowo <span class="fiz">12% jej wartości</span>.',
    tik(i) { if (cdGotowe(i) && fala.aktywna) { cdUstaw(i, 5); dajTarcze(D.hpMax * 0.05, 5); } },
    naTrafienie(i, w, k) { const t = tarczaSuma(); if (k.glowny && t > 0) zadaj(w, t * 0.12, 'fiz', { zr: 'Tarcza Tytana' }); } },
  { id: 'czerwonyKsiezyc', ik: '🌕', n: 'Czerwony Księżyc', s: { kradziez: 3, omni: 1 },
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
  { id: 'sakwaAlchemika', ik: '🧉', n: 'Sakwa Alchemika', s: { hpMax: 200 },
    opis: () => '+2 mikstury maks. Mikstury leczą <b>2×</b> mocniej i wypuszczają falę: koledzy w promieniu 180 leczą się o połowę tego, a wrogowie dostają tyle <span class="mag">obrażeń</span>.',
    natychmiast() { gracz.maksMikstur += 2; }, cofnij() { gracz.maksMikstur = Math.max(1, gracz.maksMikstur - 2); gracz.mikstury = Math.min(gracz.mikstury, gracz.maksMikstur); }, mocMikstur() { return 1; },
    naMiksturze() { const v = D.hpMax * 0.2 * gracz.mocMikstur; aura(180, '#7ee87a', w => zadaj(w, v, 'mag', { obszar: true, zr: 'Sakwa Alchemika' }), true); leczDruzyne(gracz.x, gracz.y, 180, v * 0.5, true); } },
  { id: 'bezdennaPaszcza', ik: '👄', n: 'Bezdenna Paszcza', s: { hpMax: 250 },
    opis: i => 'Zabicie wroga leczy o 1% jego maks. zdrowia (maks. 1% Twojego, w limicie wampiryzmu) i daje <b>na stałe</b> 0,5% tej wartości do maks. zdrowia — najwyżej +1 za zwykłego wroga, +4 za elitę, +15 za bossa, łącznie do +6000 (teraz +' + f0(i.stos || 0) + ').',
    naZabicie(i, w) { leczWampirem(Math.min(w.hpMax * 0.01, D.hpMax * 0.01), 'Bezdenna Paszcza'); if ((i.stos || 0) >= 6000) return; i.stos = Math.min(6000, (i.stos || 0) + Math.min(w.boss ? 15 : w.elita ? 4 : 1, w.hpMax * 0.005)); if (w.elita || w.boss || Math.random() < 0.1) oznaczStaty(); },
    statyFlat(i, s) { s.hpMax += i.stos || 0; } },
  { id: 'zegarZaglady', ik: '⏰', n: 'Zegar Zagłady', s: { ad: 40, ap: 40 }, cd: 10,
    opis: () => 'Co 10 s następne trafienie zadaje <span class="praw">20% obrażeń</span> zadanych przez Ciebie w ostatnich 10 s (bossom maks. 12% ich maks. zdrowia).',
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
  { id: 'puszkaPandory', ik: '🎁', n: 'Puszka Pandory', s: { szczescie: 20 },
    opis: () => 'Po każdej fali dostajesz <b>losowy przedmiot</b> (zwykły albo rzadki), jeśli masz wolne miejsce — inaczej 50 złota.',
    naKoniecFali() { if (wolneSlotyPrzedm() <= 0) { dodajZloto(50, true, 'Puszka Pandory'); return; } const pula = PRZEDMIOTY.filter(p => p.t <= 1 && !maPrzedmiot(p.id)); if (!pula.length) return; const d = losZ(pula); gracz.przedmioty.push(nowyPrzedmiot(d.id)); dziennik('🎁 Puszka Pandory: ' + d.ik + ' ' + d.n); przebudujHaki(); oznaczStaty(); } },
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
];
PRYZMATY.forEach(p => { p.t = 'p'; p.unik = true; DEF_PRZ[p.id] = p; });
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
  { id: 'regeneracja', r: 's', ik: '💗', n: 'Regeneracja', s: { regen: 4 } },
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
  { id: 'zapasMikstur', r: 's', ik: '🧪', n: 'Zapas mikstur', opis: () => 'Natychmiast +2 mikstury, mieścisz o 1 więcej, a mikstury leczą o 30% mocniej. Ulepszenie powtarza efekt.',
    natychmiast() { gracz.maksMikstur++; gracz.mocMikstur += 0.3; gracz.mikstury = Math.min(gracz.maksMikstur, gracz.mikstury + 2); },
    naUlepszenie() { gracz.maksMikstur++; gracz.mocMikstur += 0.3; gracz.mikstury = Math.min(gracz.maksMikstur, gracz.mikstury + 2); } },
  { id: 'lodoweDotkniecie', r: 's', ik: '🧊', n: 'Lodowe dotknięcie', opis: a => 'Ataki spowalniają o <b>' + Math.round(Math.min(50, 25 * MA(a))) + '%</b> na 1 s.',
    naTrafienie(a, w) { spowolnij(w, Math.min(0.5, 0.25 * MA(a)), 1); } },
  { id: 'podpalaczka', r: 's', ik: '🔥', n: 'Podpalacz', opis: a => 'Ataki podpalają: <span class="mag">' + f0((14 + 0.15 * D.ad + 0.15 * D.ap) * MA(a)) + '</span> (14 + 15% ⚔️ + 15% ✨) na sekundę przez 3 s.',
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
  { id: 'wampiryzm', r: 'z', ik: '🧛', n: 'Wampiryzm', s: { kradziez: 5 }, opis: a => 'Nadmiar leczenia zamienia się w tarczę (do ' + Math.round(18 * MA(a)) + '% maks. zdrowia).',
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
  { id: 'tytan', r: 'z', ik: '🗿', n: 'Tytan', opis: a => '+' + Math.round(25 * MA(a)) + '% maks. zdrowia, ataki zadają <span class="fiz">' + fmt(2.5 * MA(a)) + '% maks. zdrowia</span> przy trafieniu. Jesteś większy.',
    statyMnoz(a, s) { s.hpMax *= 1 + 0.25 * MA(a); }, statyPost(a, s) { s.onHitFiz += s.hpMax * 0.025 * MA(a); }, rozmiar() { return 1.15; } },
  { id: 'alchemiczka', r: 'z', ik: '⚗️', n: 'Alchemik', opis: a => 'Po każdej fali +1 mikstura. Mikstury leczą o ' + Math.round(50 * MA(a)) + '% mocniej i dają +' + Math.round(35 * MA(a)) + '% prędkości ataku na 5 s.',
    mocMikstur(a) { return 0.5 * MA(a); },
    naKoniecFali() { gracz.mikstury = Math.min(gracz.maksMikstur, gracz.mikstury + 1); },
    naMiksturze(a) { dodajBuff('alchemia', { as: 35 * MA(a) }, 5); } },
  { id: 'inwestorka', r: 'z', ik: '📈', n: 'Inwestor', opis: a => 'Na koniec fali odsetki: ' + Math.round(15 * MA(a)) + '% posiadanego złota (maks. ' + f0(45 * MA(a)) + ').',
    naKoniecFali(a) { const z = Math.min(45 * MA(a), gracz.zloto * 0.15 * MA(a)); if (z >= 1) dodajZloto(Math.floor(z), true, 'Odsetki'); } },
  { id: 'kowal', r: 'z', ik: '⚒️', n: 'Kowal', opis: a => 'Przy każdej wizycie w sklepie ' + (MA(a) > 1.5 ? '2 losowe przedmioty zyskują' : 'losowy przedmiot zyskuje') + ' ★ za darmo.',
    naSklep(a) { for (let n = 0; n < (MA(a) > 1.5 ? 2 : 1); n++) { const kand = gracz.przedmioty.filter(p => p && DEF_PRZ[p.id].t !== 'p' && (p.gw || 0) < MAKS_GWIAZDEK); if (!kand.length) return; const p = losZ(kand); p.gw = (p.gw || 0) + 1; toast('⚒️ ' + DEF_PRZ[p.id].n + ' zyskuje ★'); } oznaczStaty(); } },
  { id: 'ogluszacz', r: 'z', ik: '💫', n: 'Ogłuszacz', opis: a => 'Ataki mają ' + Math.round(Math.min(30, 12 * MA(a))) + '% szansy ogłuszyć na 0,6 s.',
    naTrafienie(a, w, k) { if (!k.zOgluszenia && Math.random() < Math.min(0.3, 0.12 * MA(a))) oglusz(w, 0.6, { zrodlo: 'Ogłuszacz' }); } },
  { id: 'krysztalowaSkora', r: 'z', ik: '💎', n: 'Kryształowa skóra', cd: 7, opis: a => 'Co ' + fmt(7 / MA(a)) + ' s blokuje jedno trafienie.',
    modOtrzymanych(a, v, typ, o) { if (cdGotowe(a) && v > 0 && !o.dot) { cdUstaw(a, 7 / MA(a)); tekstSwiat(gracz.x, gracz.y - 26, '💎', '#bff0ff'); return 0; } return 1; } },
  { id: 'olowiane', r: 'z', ik: '📌', n: 'Ołowiane pociski', s: { przebicie: 2 }, opis: a => 'Pociski zadają +' + Math.round(15 * MA(a)) + '% obrażeń.',
    modZadanych(a, w, typ, o) { return o.pocisk ? 1 + 0.15 * MA(a) : 1; } },
  { id: 'magiczneOstrze', r: 'z', ik: '🔮', n: 'Magiczne ostrze', opis: a => 'Ataki zadają dodatkowo <span class="mag">' + f0((15 + 0.3 * D.ap) * MA(a)) + '</span> (15 + 30% ✨) obrażeń magicznych przy trafieniu.',
    statyPost(a, s) { s.onHitMag += (15 + 0.3 * s.ap) * MA(a); } },
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
  { id: 'ped', r: 'z', ik: '🐎', n: 'Pęd', opis: a => 'Ruch buduje ładunki (do 100). Przy 100 następny atak zadaje dodatkowo <span class="fiz">' + f0((80 + 1.2 * D.ad) * MA(a)) + '</span> (80 + 120% ⚔️) i spowalnia o 50%.',
    tik(a, dt) { if (gracz.wRuchu) a.lad = Math.min(100, (a.lad || 0) + dt * 45); },
    naTrafienie(a, w, k) { if (k.glowny && (a.lad || 0) >= 100) { a.lad = 0; zadaj(w, (80 + 1.2 * D.ad) * MA(a), 'fiz', { zr: 'Pęd' }); spowolnij(w, 0.5, 1.5); efektBlysk(w.x, w.y, '#ffd24a'); } } },
  { id: 'krytycznyRytm', r: 'z', ik: '🥁', n: 'Krytyczny rytm', opis: a => 'Trafienia <b>krytyczne</b> nakładają efekty przy trafieniu jeszcze <b>' + ((a && a.poz) || 1) + '×</b>.', onHitKryt: a => (a.poz || 1) },
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
  { id: 'zamiana', r: 'p', ik: '☯️', n: 'Harmonia', opis: a => 'Twoje ⚔️ zwiększają ✨ o ' + Math.round(60 * MA(a)) + '% swojej wartości — i odwrotnie.',
    statyPost(a, s) { const ad = s.ad, ap = s.ap, m = 0.6 * MA(a); s.ad += ap * m; s.ap += ad * m; } },
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
  { id: 'burzaCiosow', r: 'p', ik: '🥊', n: 'Burza ciosów', s: { as: 25 }, opis: () => 'Twoje ataki nakładają efekty przy trafieniu <b>dwukrotnie</b>.', podwojnyOnHit: true },
  { id: 'arsenalGlowny', r: 'p', ik: '⚜️', n: 'Mistrzostwo broni', opis: a => 'Broń główna natychmiast zyskuje <b>+1 tier</b> i zadaje <b>+' + Math.round(25 * MA(a)) + '%</b> obrażeń.',
    natychmiast() { gracz.bronie.forEach(b => { if (b.tier < MAKS_TIER_BRONI) b.tier++; }); }, mnGlownejAug: a => 0.25 * MA(a) },
  { id: 'perpetuum', r: 'p', ik: '♾️', n: 'Perpetuum mobile', opis: a => 'Każde zabójstwo skraca odnowienia broni, przedmiotów i umiejętności o <b>' + fmt(0.15 * MA(a)) + ' s</b>.',
    naZabicie(a) { skrocCd(0.15 * MA(a)); } },
  { id: 'nadczlowiek', r: 'p', ik: '🦸', n: 'Nadczłowiek', opis: a => 'Umiejętność postaci odnawia się <b>2× szybciej</b>, a po jej użyciu przez 4 s zadajesz +' + Math.round(30 * MA(a)) + '% obrażeń.',
    cdUmi: () => 0.5, naUmiejetnosci(a) { dodajBuff('nadczl', { obrBonus: 30 * MA(a) }, 4); } },
  { id: 'echoBroni', r: 'p', ik: '🔂', n: 'Echo arsenału', opis: a => 'Efekty broni dodatkowych mają <b>' + Math.round(Math.min(60, 30 * MA(a))) + '%</b> szansy odpalić się drugi raz.', echoOreza: a => Math.min(0.6, 0.3 * MA(a)) },
];
const DEF_AUG = {}; AUGMENTY.forEach(a => DEF_AUG[a.id] = a);
function klonujPrzedmiot() { const kand = gracz.przedmioty.filter(p => p && gracz.przedmioty.filter(q => q && q.id === p.id).length < 2); if (!kand.length) { gracz.slotyPrzedm++; return; } const p = losZ(kand); if (czyPryzmat(p)) gracz.slotyPryzm = (gracz.slotyPryzm || 2) + 1; else gracz.slotyPrzedm++; gracz.przedmioty.push({ id: p.id, gw: p.gw || 0, cd: 0 }); toast('🧬 Sklonowano: ' + DEF_PRZ[p.id].n); }
function vaBanque() { gracz.zloto = 0; const pula = PRZEDMIOTY.filter(p => p.t === 3 && !maPrzedmiot(p.id)); for (let n = 0; n < 2 && pula.length; n++) { const d = pula.splice(Math.floor(Math.random() * pula.length), 1)[0]; if (wolneSlotyPrzedm() <= 0) gracz.slotyPrzedm++; gracz.przedmioty.push(nowyPrzedmiot(d.id)); toast('🎰 ' + d.n); } }
function statyAugmentu(a) { const d = DEF_AUG[a.id]; if (!d.s) return null; const s = {}; for (const k in d.s) s[k] = d.s[k] * MA(a); return s; }

// =====================================================================
//  POSTACIE (klasy): broń startowa, rodziny broni, umiejętność aktywna
// =====================================================================
// rodziny: z jakich rodzin sklep częściej oferuje bronie dodatkowe (null = wszystkie po równo)
const KLASY = {
  wiezniarka: {
    n: 'Więźniarka', ik: '⛓️', slotyOreza: 4, slotyPrzedm: 4, start: 'lancuch', rodziny: null,
    staty: { xpBonus: 25 },
    opis: 'Rośnie z każdym poziomem: <b>+1,5% obrażeń za każdy poziom</b> (bez limitu), +25% doświadczenia, co 5 poziomów darmowy wybór statystyk. Na start +1 przerzut augmentów i +1 mikstura.',
    dar() { gracz.przerzutyAug += 1; gracz.mikstury += 1; },
    modZadanych() { return 1 + 0.015 * gracz.poziom; },
    tik(st, dt) { if (!gracz.buffy.kajdany) return; st.tKaj = (st.tKaj || 0) - dt; if (st.tKaj > 0) return; st.tKaj = 0.5;
      aura(150, '#ffd24a', w => zadaj(w, (25 + 0.6 * D.ad + 0.3 * D.ap) * mnUmi(), 'fiz', { obszar: true, zr: 'Zerwane kajdany' })); },
    umi: { n: 'Zerwane kajdany', ik: '⛓️‍💥', cd: 14, opis: m => 'Przez 6 s: <b>+' + f0(70 * m) + '%</b> prędkości ataku, +' + f0(40 * m) + ' prędkości ruchu, a łańcuchy co 0,5 s smagają wszystkich w promieniu 150: <span class="fiz">' + f0((25 + 0.6 * D.ad + 0.3 * D.ap) * m) + '</span> (25 + 60% ⚔️ + 30% ✨).',
      uzyj(m) { dodajBuff('kajdany', { as: 70 * m, ms: 40 * m }, 6); gracz.stanKlasy.tKaj = 0; fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 150, kolor: '#ffd24a' }); DZ.awans(); return true; } },
    kolory: { plaszcz: ['#b3263a', '#6e1424'], tunika: ['#41b097', '#21645a'], wlosy: '#5a3420' },
  },
  rycerz: {
    n: 'Rycerz', ik: '🛡️', slotyOreza: 4, slotyPrzedm: 4, start: 'mieczTarcza', rodziny: ['biala'],
    staty: { pancerz: 30, hpMax: 60 },
    opis: 'Pancerz to siła: <b>+1% obrażeń za każde 3 pancerza</b> (bez limitu) i <b>pancerz ×1,25</b>. Otrzymuje 15% mniej obrażeń, tarcze +30%.',
    statyMnoz(st, s) { s.pancerz *= 1.25; }, statyPost(st, s) { s.obrBonus += Math.max(0, s.pancerz) / 3; },
    modOtrzymanych() { return 0.85; }, mnTarcz: 0.3,
    umi: { n: 'Szarża', ik: '🐎', cd: 8, opis: m => 'Szarżuje 200 px w kierunku ruchu: wrogowie na drodze dostają <span class="fiz">' + f0((60 + 1.5 * D.ad + 1.0 * D.pancerz) * m) + '</span> (60 + 150% ⚔️ + 100% 🛡️) i są ogłuszeni na 1,2 s. Dostajesz tarczę ' + f0((40 + 0.8 * D.pancerz) * m) + '.',
      uzyj(m) { szarza(200, (60 + 1.5 * D.ad + 1.0 * D.pancerz) * m, 1.2, 'Szarża'); dajTarcze((40 + 0.8 * D.pancerz) * m, 3); return true; } },
    kolory: { plaszcz: ['#3a4a8a', '#1a2450'], tunika: ['#c8ccd8', '#7a7e8c'], wlosy: '#c8a060' },
  },
  szczesciara: {
    n: 'Szczęściara', ik: '🍀', slotyOreza: 4, slotyPrzedm: 4, start: 'sztylety', rodziny: null,
    staty: { szczescie: 40, hpMax: -15 },
    opis: '<b>Szczęście ×2</b>, a każde 8 szczęścia daje +1% szansy na kryt. Skrzynie wypadają 2× częściej, 30% z nich ma podwójną zawartość. Mniej zdrowia.',
    statyMnoz(st, s) { s.szczescie *= 2; }, statyPost(st, s) { s.kryt += Math.max(0, s.szczescie) / 8; },
    mnSkrzyn: 2, podwojneSkrzynie: 0.3,
    umi: { n: 'Fart', ik: '🌈', cd: 15, opis: m => 'Przez ' + fmt(5 * m) + ' s <b>każdy atak jest krytyczny</b> i krytyki zadają +50% więcej; monety są warte 2×.',
      uzyj(m) { dodajBuff('fart', { kryt: 300, krytObr: 50 }, 5 * m); gracz.stanKlasy.fart = czasGry + 5 * m; DZ.pryzmat(); return true; } },
    mnozMonety(st) { return st.fart > czasGry ? 2 : 1; },
    kolory: { plaszcz: ['#2e8a3a', '#14501e'], tunika: ['#e6c15c', '#a07a1e'], wlosy: '#c8742a' },
  },
  wieloreka: {
    n: 'Wieloręka', ik: '🦑', slotyOreza: 6, slotyPrzedm: 4, start: 'losowa', rodziny: null,
    staty: {},
    opis: 'Nosi <b>6 broni dodatkowych</b>: ich efekty są o <b>30% mocniejsze</b> i odnawiają się o 15% szybciej, każda daje też +4% prędkości ataku. Broń główna zadaje 35% mniej. Losowa broń główna.',
    mnBroni: () => 0.65, mnOreza: 0.3, cdOreza: 0.15,
    statyFlat(st, s) { s.as += 4 * gracz.oreze.length; },
    umi: { n: 'Burza broni', ik: '🌪️', cd: 14, opis: m => 'Wszystkie bronie dodatkowe <b>odpalają natychmiast, a po 0,6 s jeszcze raz</b>. Przez 5 s +' + f0(60 * m) + '% prędkości ataku.',
      uzyj(m) { gracz.oreze.forEach(o => { o.cd = 0; }); opoznione(0.6, () => gracz.oreze.forEach(o => { o.cd = 0; })); dodajBuff('burzaBroni', { as: 60 * m }, 5); fale.push({ x: gracz.x, y: gracz.y, czas: 0.5, max: 0.5, r: 120, kolor: '#9a6ae0' }); return true; } },
    kolory: { plaszcz: ['#4a5ac4', '#24306e'], tunika: ['#9a6ae0', '#5a3a8a'], wlosy: '#2a2030' },
  },
  jedynaczka: {
    n: 'Mistrzyni Jednej Broni', ik: '🗡️', slotyOreza: 1, slotyPrzedm: 5, start: 'wybor', rodziny: null,
    staty: { as: 20 },
    opis: 'Broń główna zadaje <b>2× obrażeń</b>, zaczyna na II tierze (do wyboru), a jej ulepszanie jest o 50% tańsze. Tylko <b>1 miejsce</b> na broń dodatkową, za to +1 na przedmiot.',
    mnBroni: () => 2, rabatBroni: 0.5,
    umi: { n: 'Cięcie mistrza', ik: '⚔️', cd: 8, opis: m => 'Potężny cios bronią główną we <b>wszystkich</b> wrogów w zasięgu ×2: <b>' + f0(400 * m) + '%</b> obrażeń broni (z efektami przy trafieniu).',
      uzyj(m) { const b = gracz.bronie[0]; if (!b) return false; const zas = zasiegAtaku(b) * 2; ciecia.push({ x: gracz.x, y: gracz.y, kat: 0, luk: Math.PI * 2, r: zas, czas: 0.3, max: 0.3, kolor: '#ffe08a' });
        wrogowie.slice().forEach(w => { if (!w.martwy && !(w.zauroczony > 0) && Math.hypot(w.x - gracz.x, w.y - gracz.y) < zas + w.r) trafienieAtakiem(w, b, { mn: 4 * m, glowny: true }); }); DZ.kryt(); return true; } },
    kolory: { plaszcz: ['#2a2a2a', '#0e0e0e'], tunika: ['#c0c0d0', '#6a6a7a'], wlosy: '#e8e0d0' },
  },
  czarodziejka: {
    n: 'Czarodziejka', ik: '🧙‍♀️', slotyOreza: 4, slotyPrzedm: 4, start: 'rozdzka', rodziny: ['magiczna'],
    staty: { ap: 25, haste: 25 },
    opis: 'Mag: <b>moc umiejętności ×1,4</b> (procentowo, od wszystkiego), +25 przyspieszenia. Obrażenia od ataku ⚔️ tylko ×0,7 — gra się pod ✨. W sklepie częściej różdżki i magiczne bronie.',
    statyMnoz(st, s) { s.ap *= 1.4; s.ad *= 0.7; },
    umi: { n: 'Meteor', ik: '☄️', cd: 10, opis: m => 'Wielki meteor spada na największe skupisko wrogów (r 130): <span class="mag">' + f0((150 + 1.6 * D.ap) * m) + '</span> (150 + 160% ✨), a za nim 3 mniejsze po ' + f0((50 + 0.5 * D.ap) * m) + '.',
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 360, 130) || najblizszyWrog(gracz.x, gracz.y, 360); if (!c) return false; meteoryt(c.x, c.y, 0.7, 130, (150 + 1.6 * D.ap) * m, 'Meteor');
        for (let n = 0; n < 3; n++) meteoryt(c.x + losowo(-110, 110), c.y + losowo(-110, 110), 1 + n * 0.2, 70, (50 + 0.5 * D.ap) * m, 'Meteor'); return true; } },
    kolory: { plaszcz: ['#6a3ac4', '#341a6e'], tunika: ['#3a7ae0', '#1a3a8a'], wlosy: '#e8e0ff' },
  },
  berserkerka: {
    n: 'Berserkerka', ik: '🪓', slotyOreza: 4, slotyPrzedm: 4, start: 'topor', rodziny: ['biala'],
    staty: { as: 15, kradziez: 4 },
    opis: 'Im mniej zdrowia, tym groźniejsza: <b>+1% prędkości ataku i +0,6% obrażeń za każdy 1% brakującego zdrowia</b>. Regeneracja o połowę słabsza.',
    statyMnoz(st, s) { s.regen *= 0.5; },
    statyDyn(st, s) { const b = Math.max(0, 1 - gracz.hp / Math.max(1, s.hpMax)) * 100; s.as += b; s.obrBonus += b * 0.6; },
    umi: { n: 'Szał', ik: '😡', cd: 15, opis: m => 'Tracisz 10% aktualnego zdrowia. Przez 7 s: <b>+' + f0(80 * m) + '%</b> prędkości ataku, +' + f0(12 * m) + '% kradzieży życia, +30 prędkości ruchu i 25% redukcji obrażeń.',
      uzyj(m) { gracz.hp = Math.max(1, gracz.hp * 0.9); dodajBuff('szal', { as: 80 * m, kradziez: 12 * m, ms: 30, redukcja: 25 }, 7); rozbryzg(gracz.x, gracz.y, '#c0392b', 16); DZ.boss(); return true; } },
    kolory: { plaszcz: ['#8a2a1a', '#4a1008'], tunika: ['#7a5a3a', '#4a3020'], wlosy: '#d04020' },
  },
  handlarka: {
    n: 'Handlarka', ik: '💼', slotyOreza: 4, slotyPrzedm: 4, start: 'kusza', rodziny: ['strzelecka', 'alchemia'],
    staty: { chciwosc: 25 },
    opis: 'Złoto to siła: <b>+1% obrażeń za każde 20 złota</b> (bez limitu). Ceny w sklepie −25%. Na koniec fali odsetki: 10% złota (maks. 60). Zaczyna z 60 złota.',
    dar() { gracz.rabat += 25; gracz.zloto += 60; },
    modZadanych() { return 1 + gracz.zloto / 2000; },
    naKoniecFali() { const z = Math.min(60, gracz.zloto * 0.1); if (z >= 1) dodajZloto(Math.floor(z), true, 'Odsetki'); },
    umi: { n: 'Deszcz złota', ik: '🪙', cd: 14, opis: m => 'Deszcz monet wokół Ciebie (r 180): <span class="fiz">' + f0((40 + 0.08 * gracz.zloto + 0.8 * D.ad) * m) + '</span> (40 + 8% złota + 80% ⚔️). Zabici nim wrogowie upuszczają dodatkowe złoto.',
      uzyj(m) { const v = (40 + 0.08 * gracz.zloto + 0.8 * D.ad) * m; aura(180, '#ffd24a', w => { zadaj(w, v, 'fiz', { obszar: true, zr: 'Deszcz złota' }); if (w.martwy) rozsypMonety(w.x, w.y, 3); }, true); for (let n = 0; n < 16; n++) czastki.push({ x: gracz.x + losowo(-170, 170), y: gracz.y + losowo(-170, 170), vx: 0, vy: 60, czas: 0.6, max: 0.6, kolor: '#ffd24a' }); DZ.moneta(); return true; } },
    kolory: { plaszcz: ['#a07a1e', '#5a4008'], tunika: ['#2a6a4a', '#14402a'], wlosy: '#3a2a1a' },
  },
  wampirzyca: {
    n: 'Wampirzyca', ik: '🦇', slotyOreza: 4, slotyPrzedm: 4, start: 'kosa', rodziny: ['biala', 'magiczna'],
    staty: { omni: 8, leczenie: 25 },
    opis: 'Jedyna z <b>prawdziwym wampiryzmem</b>: limit wampiryzmu wyższy o 4% zdrowia/s, +8% wszechwampiryzmu, leczenie +25%. Każde zabójstwo leczy o 0,5% maks. zdrowia. <b>Nie ma regeneracji.</b>',
    statyMnoz(st, s) { s.regen = Math.min(0, s.regen); },
    naZabicie() { leczWampirem(D.hpMax * 0.005, 'Wampirzyca'); }, limitWamp: 0.04,
    umi: { n: 'Uczta krwi', ik: '🩸', cd: 12, opis: m => 'Wysysa krew z wrogów w promieniu 190: <span class="mag">' + f0((60 + 0.08 * D.hpMax + 0.7 * D.ap) * m) + '</span> (60 + 8% maks. zdrowia + 70% ✨) każdemu. Leczysz się o 50% zadanych (maks. 30% zdrowia).',
      uzyj(m) { if (!policzWrogow(gracz.x, gracz.y, 190)) return false; let suma = 0; aura(190, '#c0392b', w => { suma += zadaj(w, (60 + 0.08 * D.hpMax + 0.7 * D.ap) * m, 'mag', { obszar: true, zr: 'Uczta krwi' }); dodajBlyskawice(w.x, w.y, gracz.x, gracz.y, '#e04050'); }, true); leczGracza(Math.min(suma * 0.5, D.hpMax * 0.3), 'Uczta krwi'); return true; } },
    kolory: { plaszcz: ['#3a0a1a', '#1a0008'], tunika: ['#6a0a2a', '#3a0418'], wlosy: '#101010' },
  },
  kolos: {
    n: 'Kolos', ik: '🗿', slotyOreza: 4, slotyPrzedm: 5, start: 'kastety', rodziny: ['biala'],
    staty: { hpMax: 120, pancerz: 25, odpMag: 15, ms: -20, as: -15 },
    opis: 'Góra mięśni: <b>maks. zdrowie ×1,3</b>, ataki zadają <span class="fiz">3% maks. zdrowia</span> przy trafieniu. Wolniejszy, większy. +1 miejsce na przedmiot.',
    statyMnoz(st, s) { s.hpMax *= 1.3; }, statyPost(st, s) { s.onHitFiz += s.hpMax * 0.03; }, rozmiar() { return 1.2; },
    umi: { n: 'Kamienna skóra', ik: '🪨', cd: 18, opis: m => '<b>' + fmt(3.5 * Math.min(1.6, m)) + ' s niewrażliwości</b>, wrogowie w promieniu 260 rzucają się na Ciebie. Na koniec fala uderzeniowa (r 200): <span class="fiz">' + f0(0.12 * D.hpMax * m) + '</span> (12% maks. zdrowia).',
      uzyj(m) { const t = 3.5 * Math.min(1.6, m); gracz.niewr = Math.max(gracz.niewr, t); wrogowie.forEach(w => { if (!w.martwy && Math.hypot(w.x - gracz.x, w.y - gracz.y) < 260) { w.cel = gracz; w.tCelu = t; } });
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#c0b8a0', odwrot: true }); DZ.tarcza();
        const ja = gracz; opoznione(t, () => { if (gracz !== ja || stan !== 'walka') return; aura(200, '#c0b8a0', w => { zadaj(w, 0.12 * D.hpMax * m, 'fiz', { obszar: true, zr: 'Kamienna skóra' }); oglusz(w, 0.8, { zrodlo: 'Kamienna skóra' }); }, true); DZ.wybuch(); }); return true; } },
    kolory: { plaszcz: ['#5a5a6a', '#2a2a34'], tunika: ['#8a7a6a', '#4a4034'], wlosy: '#3a3030' },
  },
  lowczyni: {
    n: 'Łowczyni', ik: '🏹', slotyOreza: 4, slotyPrzedm: 4, start: 'luk', rodziny: ['strzelecka'],
    staty: { zasieg: 25, kryt: 15, krytObr: 50 },
    opis: 'Snajperka: <b>+50% obrażeń krytycznych</b>, +15% kryta, +25% zasięgu i <b>+30% obrażeń</b> wrogom dalej niż 150 px. W sklepie częściej broń strzelecka.',
    modZadanych(st, w) { return Math.hypot(w.x - gracz.x, w.y - gracz.y) > 150 ? 1.3 : 1; },
    umi: { n: 'Deszcz strzał', ik: '🌧️', cd: 10, opis: m => 'Na skupisko wrogów spada ' + f0(20 * m) + ' strzał (r 130): <span class="fiz">' + f0(30 + 0.7 * D.ad) + '</span> (30 + 70% ⚔️) każda, mogą trafić krytycznie.',
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 340, 130) || najblizszyWrog(gracz.x, gracz.y, 340); if (!c) return false; const n = Math.round(20 * m), v = 30 + 0.7 * D.ad, x = c.x, y = c.y;
        for (let s = 0; s < n; s++) opoznione(0.035 * s, () => { const px = x + losowo(-120, 120), py = y + losowo(-120, 120); const kr = Math.random() * 100 < D.kryt; dodajBlyskawice(px - 20, py - 120, px, py, '#e8d8b0'); obszarowe(px, py, 34, '#e8d8b0', w => zadaj(w, v * (kr ? kryt2() : 1), 'fiz', { zr: 'Deszcz strzał', obszar: true, kryt: kr }), true); }); DZ.strzal(); return true; } },
    kolory: { plaszcz: ['#3a6a2a', '#1a3a10'], tunika: ['#8a6a3a', '#4a3a1a'], wlosy: '#e0a040' },
  },
  rewolwerowiec: {
    n: 'Rewolwerowiec', ik: '🤠', slotyOreza: 4, slotyPrzedm: 4, start: 'pistolet', rodziny: ['strzelecka', 'alchemia'],
    staty: { as: 15, kryt: 10, krytObr: 25 },
    opis: 'Co <b>3. strzał</b> broni głównej jest zawsze krytyczny, a krytyki +25%. W sklepie częściej broń strzelecka i alchemia.',
    naAtak(st) { st.licz = (st.licz || 0) + 1; st.pewnyKryt = st.licz % 3 === 0; },
    umi: { n: 'Wachlarz', ik: '💫', cd: 8, opis: m => 'Wystrzeliwuje ' + f0(20 * m) + ' kul dookoła: <span class="fiz">' + f0(30 + 0.9 * D.ad) + '</span> (30 + 90% ⚔️) każda, przebijają 2 wrogów i mogą trafić krytycznie.',
      uzyj(m) { const n = Math.round(20 * m); for (let s = 0; s < n; s++) { const kr = Math.random() * 100 < D.kryt; wystrzel({ x: gracz.x, y: gracz.y, kat: s / n * Math.PI * 2, predkosc: 720, obr: (30 + 0.9 * D.ad) * (kr ? kryt2() : 1), typ: 'fiz', kolor: '#ffe08a', ksztalt: 'kula', zr: 'Wachlarz', zycie: 0.5, przebija: 2 }); } DZ.strzal(); DZ.wybuch(); return true; } },
    kolory: { plaszcz: ['#7a4a2a', '#4a2a14'], tunika: ['#c0a070', '#7a6040'], wlosy: '#2a1a10' },
  },
  bombardierka: {
    n: 'Bombardierka', ik: '💣', slotyOreza: 4, slotyPrzedm: 4, start: 'granatnik', rodziny: ['alchemia'],
    staty: { obszar: 30, hpMax: 20 },
    opis: 'Wybuchy i obszar zadają <b>+40%</b> obrażeń, +30% wielkości obszarów. W sklepie częściej alchemia.',
    modZadanych(st, w, typ, o) { return o.obszar ? 1.4 : 1; },
    umi: { n: 'Wielka bomba', ik: '💥', cd: 12, opis: m => 'Rzuca wielką bombę na skupisko wrogów (r 200, po 1,1 s): <span class="fiz">' + f0((200 + 2 * D.ad + 1.5 * D.ap) * m) + '</span> (200 + 200% ⚔️ + 150% ✨) i ogłuszenie 1,5 s.',
      uzyj(m) { const c = skupisko(gracz.x, gracz.y, 320, 160) || najblizszyWrog(gracz.x, gracz.y, 320); if (!c) return false; granat(gracz.x, gracz.y, c.x, c.y, 200, (200 + 2 * D.ad + 1.5 * D.ap) * m, 'fiz', 'Wielka bomba', 1.1, 1.5); return true; } },
    kolory: { plaszcz: ['#e6743c', '#8a3a14'], tunika: ['#2a2a2a', '#101010'], wlosy: '#ffb050' },
  },
  inzynierka: {
    n: 'Inżynierka', ik: '🔧', slotyOreza: 4, slotyPrzedm: 4, start: 'gwozdziarka', rodziny: ['strzelecka', 'alchemia'],
    staty: { haste: 15, pancerz: 10 },
    opis: 'Działka, wieże i inne stworzenia zadają <b>2× obrażeń</b>. Zaczyna z <b>Małą Wieżyczką</b>.',
    mnStworow: 1, dar() { gracz.przedmioty.push(nowyPrzedmiot('wiezyczka')); },
    umi: { n: 'Wieżyczka bojowa', ik: '🏗️', cd: 14, opis: m => 'Stawia ciężką wieżyczkę na 12 s: co 0,3 s <span class="fiz">' + f0((30 + 0.7 * D.ad + 0.5 * D.ap) * m) + '</span> (30 + 70% ⚔️ + 50% ✨).',
      uzyj(m) { postawDzialko('dzialko', 12, { obr: (30 + 0.7 * D.ad + 0.5 * D.ap) * m, co: 0.3, zr: 'Wieżyczka bojowa' }); return true; } },
    kolory: { plaszcz: ['#e6c15c', '#a07a1e'], tunika: ['#3a6ac4', '#1a3a7a'], wlosy: '#8a4a2a' },
  },
  nekromantka: {
    n: 'Nekromantka', ik: '💀', slotyOreza: 4, slotyPrzedm: 4, start: 'kosturKosci', rodziny: ['magiczna'],
    staty: { ap: 20, hpMax: 10 },
    opis: 'Sojusznicy zadają <b>3× obrażeń</b> i żyją 3× dłużej. Każdy zabity wróg ma 8% szans, że wstanie po Twojej stronie.',
    mnSojusznikow: 2,
    naZabicie(st, w) { if (!w.boss && !w.sojusznik && Math.random() < 0.08) wskrzesSojusznika(w, 8); },
    umi: { n: 'Armia ciemności', ik: '☠️', cd: 16, opis: m => 'Przywołuje ' + f0(7 * m) + ' szkieletów, które walczą po Twojej stronie przez 12 s.',
      uzyj(m) { const n0 = Math.round(7 * m); for (let n = 0; n < n0; n++) { const k = n / n0 * Math.PI * 2; wskrzesSojusznika({ typ: 'szkielet', x: gracz.x + Math.cos(k) * 55, y: gracz.y + Math.sin(k) * 55 }, 12); } DZ.czar(); return true; } },
    kolory: { plaszcz: ['#1a3a2a', '#0a1a10'], tunika: ['#4a4a5a', '#24242e'], wlosy: '#d8e8d0' },
  },
  druidka: {
    n: 'Druidka', ik: '🌿', slotyOreza: 4, slotyPrzedm: 4, start: 'kosturNatury', rodziny: ['magiczna', 'alchemia'],
    staty: { regen: 3, leczenie: 30 },
    opis: 'Natura: <b>regeneracja ×2</b>, leczenie +30%, owoce i stworzenia +50%. Zmęczenie osłabia jej leczenie tylko o połowę. Zaczyna z <b>Krzakiem Jagód</b>.',
    statyMnoz(st, s) { s.regen *= 2; }, mnStworow: 0.5, polZmeczenia: true, dar() { gracz.przedmioty.push(nowyPrzedmiot('krzakJagod')); },
    umi: { n: 'Zarośla', ik: '🌱', cd: 13, opis: m => 'Korzenie unieruchamiają wrogów w promieniu 180 na ' + fmt(1.6 * m) + ' s i zadają <span class="mag">' + f0((60 + 0.9 * D.ap) * m) + '</span> (60 + 90% ✨). Drużyna w promieniu 240 leczy się o ' + f0(20 * m) + '% maks. zdrowia.',
      uzyj(m) { aura(180, '#5ac46a', w => { zadaj(w, (60 + 0.9 * D.ap) * m, 'mag', { obszar: true, zr: 'Zarośla' }); oglusz(w, 1.6 * m, { zrodlo: 'Zarośla' }); }, true); leczDruzyne(gracz.x, gracz.y, 240, 0, true, 0.2 * m); return true; } },
    kolory: { plaszcz: ['#3a7a2a', '#1a4a10'], tunika: ['#8a6a3a', '#5a4020'], wlosy: '#c87a2a' },
  },
  hazardzistka: {
    n: 'Hazardzistka', ik: '🎲', slotyOreza: 4, slotyPrzedm: 4, start: 'kosci', rodziny: null,
    staty: { szczescie: 25 },
    opis: 'Rzuca <b>słabymi kośćmi</b> (losowe obrażenia), ale jej <b>Koło fortuny</b> potrafi wszystko — nawet użyć umiejętności innej postaci. Co falę losuje dużą premię. +3 przerzuty augmentów, darmowy przerzut sklepu.',
    dar() { gracz.przerzutyAug += 3; gracz.darmowePrzerzuty += 1; },
    naStartFali(st) {
      const opcje = [['as', 60, '⚡ +60% prędkości ataku'], ['ad', 50, '⚔️ +50 obrażeń od ataku'], ['ap', 90, '✨ +90 mocy umiejętności'], ['kryt', 40, '🎯 +40% szansy na kryt'],
        ['ms', 60, '👟 +60 prędkości ruchu'], ['pancerz', 80, '🛡️ +80 pancerza'], ['obrBonus', 30, '💥 +30% obrażeń'], ['chciwosc', 100, '💰 +100% złota'], ['haste', 50, '⏱️ +50 przyspieszenia']];
      const o = losZ(opcje); st.premia = { k: o[0], v: o[1] }; oznaczStaty(); dziennik('🎲 Premia fali: ' + o[2]);
    },
    statyFlat(st, s) { if (st.premia && fala && fala.aktywna) s[st.premia.k] += st.premia.v; },
    statyDyn(st, s) { if (st.jackpot > czasGry) { s.obrBonus += 200; s.kryt += 100; } },
    umi: { n: 'Koło fortuny', ik: '🎡', cd: 9, opis: () => 'Kręci kołem: <b>jackpot</b> (6 s: +200% obrażeń i każdy atak krytyczny), <b>joker</b> (używa umiejętności losowej innej postaci), salwa wybuchów, wir, niewrażliwość, szał, leczenie, złoto… albo <b>pech</b> (tracisz 15% zdrowia, ale następny rzut to pewny jackpot).',
      uzyj(m) {
        const st = gracz.stanKlasy;
        const r = st.pewnyJackpot ? 0 : losWazony([[0, 7], [1, 14], [2, 13], [3, 11], [4, 9], [5, 10], [6, 9], [7, 8], [8, 9], [9, 10]]);
        st.pewnyJackpot = false;
        const T = (t) => { toast('🎡 ' + t); tekstSwiat(gracz.x, gracz.y - 40, '🎡 ' + t, '#ffe08a', 1.2, 15); };
        if (r === 0) { st.jackpot = czasGry + 6; oznaczStaty(); DZ.pryzmat(); T('JACKPOT!'); fale.push({ x: gracz.x, y: gracz.y, czas: 0.7, max: 0.7, r: 200, kolor: '#ffd24a' }); }
        else if (r === 1) { const inne = KLUCZE_KLAS.filter(k => k !== 'hazardzistka' && KLASY[k].umi); let ok = false;
          for (let p = 0; p < 4 && !ok; p++) { const k = losZ(inne); try { ok = KLASY[k].umi.uzyj(m) !== false; } catch (e) { ok = false; } if (ok) T('Joker: ' + KLASY[k].umi.ik + ' ' + KLASY[k].umi.n); }
          if (!ok) { gracz.niewr = Math.max(gracz.niewr, 2); T('Joker: unik losu'); } }
        else if (r === 2) { for (let n = 0; n < 10; n++) opoznione(0.06 * n, () => { const x = gracz.x + losowo(-220, 220), y = gracz.y + losowo(-220, 220); obszarowe(x, y, 70, '#ffb070', w => zadaj(w, (80 + 0.8 * D.ad + 0.8 * D.ap) * m, 'mag', { obszar: true, zr: 'Koło fortuny' })); rozbryzg(x, y, '#ffb070', 8); }); DZ.wybuch(); T('Salwa wybuchów!'); }
        else if (r === 3) { wrogowie.forEach(w => { if (w.martwy || w.boss || w.zauroczony > 0) return; const d = Math.hypot(w.x - gracz.x, w.y - gracz.y); if (d < 260 && d > 1) { w.x += (gracz.x - w.x) / d * Math.min(d - 30, 140); w.y += (gracz.y - w.y) / d * Math.min(d - 30, 140); oglusz(w, 1.5, { zrodlo: 'Koło fortuny' }); } }); fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#9a6ae0', odwrot: true }); T('Wir!'); }
        else if (r === 4) { gracz.niewr = Math.max(gracz.niewr, 4); T('4 s niewrażliwości!'); }
        else if (r === 5) { dodajBuff('kolo', { as: 100 * m, ms: 40 }, 6); T('Szał!'); }
        else if (r === 6) { leczGracza(D.hpMax * 0.5, 'Koło fortuny'); T('Leczenie!'); }
        else if (r === 7) { dodajZloto(Math.round((10 + 4 * fala.nr) * m), true, '🎡 Koło fortuny'); T('Złoto!'); }
        else if (r === 8) { gracz.umi.cd = 0; st.natychmiast = true; T('Kręć jeszcze raz!'); return true; }
        else { gracz.hp = Math.max(1, gracz.hp - D.hpMax * 0.15); st.pewnyJackpot = true; T('Pech… następny rzut to JACKPOT'); }
        return true; } },
    kolory: { plaszcz: ['#6a1a6a', '#3a0a3a'], tunika: ['#e0e0e0', '#9a9a9a'], wlosy: '#1a1a1a' },
  },
  kaplanka: {
    n: 'Kapłanka Pryzmatu', ik: '🔮', slotyOreza: 4, slotyPrzedm: 3, slotyPryzm: 3, start: 'kosturPustki', rodziny: ['magiczna'],
    staty: { hpMax: -10 },
    opis: 'Mistrzyni pryzmatów: <b>3 miejsca na pryzmaty</b> i Pryzmatyczne Kowadło na start (za to 3 zwykłe przedmioty). Tarcze i leczenie dla drużyny +50%.',
    dar() { gracz.kowadla = (gracz.kowadla || 0) + 1; }, mnTarcz: 0.5,
    umi: { n: 'Pryzmatyczna tarcza', ik: '💠', cd: 13, opis: m => 'Ty i koledzy w promieniu 260 dostajecie tarczę <b>' + f0(35 * m) + '% maks. zdrowia</b> na 4 s, leczenie ' + f0(15 * m) + '% i +30% obrażeń na 5 s.',
      uzyj(m) { leczDruzyne(gracz.x, gracz.y, 260, 0, true, 0.15 * m, 0.35 * m); const z0 = gracz; gracze.forEach(p => { if (p.powalony || Math.hypot(p.x - z0.x, p.y - z0.y) > 260) return; kontekst(p); dodajBuff('pryzmat', { obrBonus: 30 }, 5); }); kontekst(z0);
        fale.push({ x: gracz.x, y: gracz.y, czas: 0.6, max: 0.6, r: 260, kolor: '#ff9ae0' }); DZ.pryzmat(); return true; } },
    kolory: { plaszcz: ['#e07ac0', '#7a3a8a'], tunika: ['#7ae0ff', '#3a8aa0'], wlosy: '#ffffff' },
  },
};
const KLUCZE_KLAS = Object.keys(KLASY);
function opisRodzinKlasy(K) { return K.rodziny ? K.rodziny.map(r => RODZINY[r].ik + ' ' + RODZINY[r].n).join(', ') : 'wszystkie po równo'; }
function opisBroniStartowej(K) { return K.start === 'losowa' ? '🎲 losowa' : K.start === 'wybor' ? '✋ do wyboru (II tier)' : BRONIE[K.start].ikona + ' ' + BRONIE[K.start].nazwa; }

// =====================================================================
//  WROGOWIE, ELITY, BOSSOWIE i ich zachowanie
// =====================================================================
const TYPY_WROGOW = {
  szczur:   { n: 'Szczur', ik: '🐀', hp: 20, atak: 6, panc: 0, odp: 0, ms: 95, xp: 2, zl: 1, r: 13, kolor: '#8a6a4a' },
  goblin:   { n: 'Goblin', ik: '👺', hp: 28, atak: 8, panc: 6, odp: 0, ms: 110, xp: 2, zl: 1, r: 15, kolor: '#5a9a4a' },
  szkielet: { n: 'Szkielet', ik: '💀', hp: 42, atak: 10, panc: 18, odp: 5, ms: 80, xp: 3, zl: 1, r: 16, kolor: '#d8d0c0' },
  pajak:    { n: 'Pająk', ik: '🕷️', hp: 14, atak: 5, panc: 0, odp: 0, ms: 150, xp: 1, zl: 1, r: 12, kolor: '#4a3a5a' },
  okrazacz: { n: 'Ania', ik: '🦇', obraz: 'ania', hp: 26, atak: 7, panc: 4, odp: 6, ms: 125, xp: 3, zl: 2, r: 15, kolor: '#6a5a8a', dyst: 230, typObr: 'mag', zach: 'okrazajacy' },
  bombiarz: { n: 'Bombiarz', ik: '💣', hp: 34, atak: 16, panc: 3, odp: 0, ms: 160, xp: 3, zl: 2, r: 15, kolor: '#e6743c', wybuchowy: true },
  kusznik:  { n: 'Kusznik', ik: '🏹', hp: 30, atak: 12, panc: 6, odp: 0, ms: 68, xp: 3, zl: 2, r: 15, kolor: '#7a6a4a', dyst: 320, typObr: 'fiz' },
  trujacy:  { n: 'Patryk', ik: '🦨', obraz: 'patryk', hp: 55, atak: 9, panc: 6, odp: 6, ms: 105, xp: 4, zl: 2, r: 16, kolor: '#6a9a4a', zach: 'uciekajacy', typObr: 'mag' },
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
    ms: Math.min(1.3, 1 + 0.01 * x) * T.ms,
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
    if (!w.cel || w.cel.powalony || w.tCelu <= 0 || gracze.indexOf(w.cel) < 0) { w.cel = najblizszyGracz(w.x, w.y); w.tCelu = 0.5; }
    w.wiek += dt;
    if (w.trafiony > 0) w.trafiony -= dt;
    if (w.naznaczony > 0) w.naznaczony -= dt;
    if (w.rany > 0) w.rany -= dt;
    if (w.wzm > 0) { w.wzm -= dt; if (w.wzm <= 0) w.atak /= 1.3; }
    if (w._zaT > 0) { w._zaT -= dt; if (w._zaT <= 0) w.zamarzniecieAtaku = 0; }
    // efekty rozłożone w czasie
    tikEfektowWroga(w, dt); if (w.martwy) continue;
    // afiksy pasywne
    kontekst(w.cel);
    if (w.afiksy.length) aktualizujAfiksy(w, dt);
    if (w.martwy) continue;
    if (w.spowCzas > 0) { w.spowCzas -= dt; if (w.spowCzas <= 0) w.spow = 0; }
    // odrzut
    if (w.kbx || w.kby) { w.x += w.kbx * dt; w.y += w.kby * dt; w.kbx *= Math.pow(0.002, dt); w.kby *= Math.pow(0.002, dt); if (Math.abs(w.kbx) + Math.abs(w.kby) < 5) { w.kbx = 0; w.kby = 0; } }
    if (w.ogl > 0) { w.ogl -= dt; ogranicz(w); continue; }
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

function aiWroga(w, dt, msMn) {
  const dx = gracz.x - w.x, dy = gracz.y - w.y, d = Math.hypot(dx, dy) || 1, kg = Math.atan2(dy, dx);
  const T = TYPY_WROGOW[w.typ] || {};
  w.kier = kg;
  // Upiorny rycerz: namierza (stoi 0,7 s) i szarżuje
  if (T.szarzuje) {
    if (w.dashT > 0) { w.dashT -= dt; w.x += w.dVX * dt; w.y += w.dVY * dt; if (!w.trafilDash && d < w.r + gracz.r * rozmiarGracza() + 6) { w.trafilDash = true; zranGracza(w.atak * 1.6, 'fiz', { wrog: w, wrecz: true }); } return; }
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
  const zasieg = w.dyst || (w.r + gracz.r * rozmiarGracza() + 6);
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
  if (d > zasieg) return;
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
  } else {
    const zad = zranGracza(w.atak, w.typObr || 'fiz', { wrog: w, wrecz: true });
    if (T.wysysa && zad > 0) { w.hp = Math.min(w.hpMax, w.hp + zad * 3); czastkiLeczenia(w.x, w.y); }
    if (w.afiksy.indexOf('lodowy') >= 0) spowolnijGracza(0.35, 1.5);
  }
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
  const mc = w.mnCdBossa || 1, proc = w.hp / w.hpMax;
  w.t1 -= dt; w.t2 -= dt; w.t3 -= dt; w.t4 -= dt;
  // szarża w toku
  if (w.szarza > 0) {
    w.szarza -= dt; w.x += w.szVX * dt; w.y += w.szVY * dt;
    w.cd -= dt; if (d < w.r + gracz.r + 8 && w.cd <= 0) { w.cd = 0.6; zranGracza(w.atak * 1.4, 'fiz', { wrog: w, wrecz: true }); }
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
  const dl = Math.hypot(rx, ry);
  if (dl > 0.001) { w.x += rx / dl * w.ms * msMn * dt; w.y += ry / dl * w.ms * msMn * dt; }
  w.cd -= dt;
  if (d < w.r + gracz.r * rozmiarGracza() + 8 && w.cd <= 0) { w.cd = 1.05; zranGracza(w.atak, 'fiz', { wrog: w, wrecz: true }); }
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
let wrogowie = [], pociski = [], pociskiWrogow = [], kulki = [], monety = [], skrzynieNaZiemi = [], miksturyNaZiemi = [];
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
function najblizszyGracz(x, y) { let naj = null, nd = Infinity; for (const p of gracze) { if (p.powalony || p.martwy) continue; const d = Math.hypot(p.x - x, p.y - y); if (d < nd) { nd = d; naj = p; } } return naj; }
function dlaKazdego(fn) { const z = gracz; for (const p of gracze.slice()) { kontekst(p); fn(p); } kontekst(z); }

// ---------------------------------------------------------------------
//  NOWA POSTAĆ
// ---------------------------------------------------------------------
function xpDoPoziomu(L) { return Math.round(18 + 10 * L + 2.2 * L * L); }
function nowyGracz(klasa) {
  const K = KLASY[klasa];
  return {
    klasa: klasa, x: SRODEK, y: SRODEK, r: 13, hp: 100, poziom: 1, xp: 0, xpNast: xpDoPoziomu(1),
    zloto: 0, mikstury: 1, maksMikstur: 3, mocMikstur: 1, cdMikstury: 0,
    bronie: [], oreze: [], pancerz: { helm: null, zbroja: null, buty: null, amulet: null }, przedmioty: [], augmenty: [],
    ulepszenia: {}, stale: {}, slotyOreza: K.slotyOreza || 4, slotyPrzedm: K.slotyPrzedm, slotyPryzm: K.slotyPryzm || 2, umi: { cd: 0, cdMax: 0 },
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
  'naNadleczenie', 'naAktywacji', 'naSklep', 'naMiksturze', 'mnozMonety', 'rozmiar', 'naAwans', 'naUniku', 'mnSkrzyn', 'odbijPocisk', 'mocMikstur', 'naUmiejetnosci'];
// flagi sumowane ze wszystkich źródeł (liczba albo funkcja od instancji, np. poziomu augmentu)
const FLAGI_SUMA = ['mnPrzedmiotow', 'zasiegWrecz', 'onHitKryt', 'oszczedny', 'mnStworow', 'mnOreza', 'cdOreza', 'cdUmi', 'mnUmi', 'mnGlownejAug', 'echoOreza', 'mnTarcz', 'mnSojusznikow'];
const FLAGI_LOG = ['bezKryt', 'superkryt', 'podwojnyOnHit', 'lepszeAugmenty', 'wszystkoMag', 'krysztalCzasu', 'odpornyNaSpow', 'fabryka'];
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
  gracz._HAKI = HAKI; gracz._FLAGI = FLAGI;
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
  s.hpMax += 5 * (gracz.poziom - 1);
  dodajStaty(s, gracz.ulepszenia);
  dodajStaty(s, gracz.stale);
  const mnP = 1 + FLAGI.mnPrzedmiotow;
  SLOTY_PANCERZA.forEach(sl => { const p = gracz.pancerz[sl]; if (p) dodajStaty(s, statyPancerza(p), mnP); });
  gracz.oreze.forEach(o => { if (o) dodajStaty(s, statyOreza(o), mnP); });
  gracz.przedmioty.forEach(p => { if (p && DEF_PRZ[p.id].s) dodajStaty(s, DEF_PRZ[p.id].s); });   // tylko pryzmaty mają staty
  gracz.augmenty.forEach(a => { const st = statyAugmentu(a); if (st) dodajStaty(s, st); });
  const z = policzZestawy();
  for (const t in z) { const n = poziomZestawu(z[t]); if (n >= 0 && RODZINY[t]) dodajStaty(s, RODZINY[t].staty(n)); }
  for (const id in gracz.buffy) dodajStaty(s, gracz.buffy[id].staty);
  hak('statyFlat', s);
  hak('statyDyn', s);
  if (gracz.stale.hpProc) s.hpMax *= 1 + gracz.stale.hpProc / 100;
  hak('statyMnoz', s);
  hak('statyPost', s);
  if (TRUDNOSCI[run.trudnosc].regenGracza !== undefined) s.regen *= TRUDNOSCI[run.trudnosc].regenGracza;
  s.hpMax = Math.max(1, Math.round(s.hpMax));
  s.ms = Math.max(40, s.ms);
  return s;
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
  if ((o.atak || o.onhit) && D.kradziez > 0) lecz += v * D.kradziez / 100;
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
    const K = KLASY[gracz.klasa];
    const mnS = (1 + D.szczescie / 100) * (K.mnSkrzyn || 1) * mnoznikHakow('mnSkrzyn') * (TRUDNOSCI[run.trudnosc].skrzynie || 1);
    let pSk = w.boss ? 1 : (w.elita ? 0.12 : 0.005) * mnS * mL;
    if (!w.boss && (fala.skrzynie || 0) >= zakresSkrzyn(fala.nr)[1]) pSk = 0;
    if (Math.random() < pSk) { skrzynieNaZiemi.push({ x: w.x, y: w.y, tier: tierSkrzyni(w), faza: Math.random() * 6, boss: !!w.boss }); if (!w.boss) fala.skrzynie = (fala.skrzynie || 0) + 1; }
    const naZiemi = miksturyNaZiemi.length;
    if (gracz.mikstury + naZiemi < gracz.maksMikstur && Math.random() < (w.elita ? 0.25 : 0.006) * mL) miksturyNaZiemi.push({ x: w.x + 10, y: w.y, faza: 0 });
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
  const baz = obrBroni(b) * (o.mn || 1) * (B.mnTrafienia ? B.mnTrafienia(b, w, o) : 1);
  const sz = FLAGI.bezKryt ? 0 : D.kryt + (B.kryt || 0);
  let kryt = Math.random() * 100 < sz || (!!o.pewnyKryt && !FLAGI.bezKryt), mnK = 1;
  if (kryt) {
    mnK = 1.75 + (D.krytObr + (B.krytObr || 0)) / 100;
    if (FLAGI.superkryt && sz > 100 && Math.random() * 100 < sz - 100) { mnK *= 2; tekstSwiat(w.x, w.y - w.r - 16, 'SUPERKRYT', '#ff7ae0', 0.8, 14); }
  }
  const surowe = baz * mnK;
  const zad = zadaj(w, surowe, FLAGI.wszystkoMag ? 'mag' : B.obrTyp, { atak: true, kryt: kryt, bron: b, zr: B.nazwa, pocisk: o.pocisk, przebPanc: B.przebPanc, obszar: o.obszar });
  const k = { bron: b, kryt: kryt, glowny: o.glowny !== false, zadane: zad, zadaneSurowe: surowe, bazowe: baz, licznikCiosu: o.licznikCiosu || 1, zOgluszenia: false };
  if (B.naTrafienie) { try { B.naTrafienie(w, b, k); } catch (e) { zglosBlad(e, 'bron ' + b.rodzaj); } }
  if (kryt) { hak('naKryt', w, k); DZ.kryt(); }
  let razy = 1; if (b._podwojnyOnHit) razy++; if (FLAGI.podwojnyOnHit) razy *= 2;
  if (kryt && FLAGI.onHitKryt) razy += Math.round(FLAGI.onHitKryt);
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
      if (D.onHitFiz > 0) zadaj(w, D.onHitFiz, 'fiz', { onhit: true, zr: 'Przy trafieniu' });
      if (D.onHitMag > 0) zadaj(w, D.onHitMag, 'mag', { onhit: true, zr: 'Przy trafieniu' });
      if (D.onHitPraw > 0) zadaj(w, D.onHitPraw, 'praw', { onhit: true, zr: 'Przy trafieniu' });
      if (w.martwy) break;
      hak('naTrafienie', w, k);
    }
  } finally { glebokoscOnHit--; }
}

function celBroni(b, zas) {
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
  b._podwojnyOnHit = false;
  hak('naAtak', b, cel, o);
  b._pewnyKryt = !!gracz.stanKlasy.pewnyKryt; gracz.stanKlasy.pewnyKryt = false;
  run.ataki++;
  switch (B.atak) {
    case 'wrecz': cios(b, cel); DZ.ciecie(); break;
    case 'pchniecie': pchniecie(b, cel); DZ.ciecie(); break;
    case 'pocisk': strzal(b, cel); if (B.obrTyp === 'mag') DZ.magia(); else DZ.strzal(); break;
    case 'piorun': piorunBroni(b, cel); break;
    case 'bumerang': rzutBumerangiem(b, cel); DZ.strzal(); break;
    case 'granat': rzutGranatu(b, cel); DZ.strzal(); break;
    case 'stozek': strumien(b, cel); break;
  }
  b._pewnyKryt = false;
}
// granatnik: pocisk leci łukiem w miejsce celu i wybucha
function rzutGranatu(b, cel) {
  const B = BRONIE[b.rodzaj], ile = 1 + Math.max(0, Math.round(D.pociski));
  for (let n = 0; n < ile; n++) {
    const tx = cel.x + (n ? losowo(-60, 60) : 0), ty = cel.y + (n ? losowo(-60, 60) : 0);
    const d = Math.hypot(tx - gracz.x, ty - gracz.y), v = 340, k = Math.atan2(ty - gracz.y, tx - gracz.x);
    pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, zycie: Math.max(0.12, d / v), maxZycie: Math.max(0.12, d / v), r: 7, bron: b, mn: n ? 0.6 : 1,
      granat: { r: (B.promien + 6 * b.tier) * mnObszaru() }, trafieni: [], kolor: B.kolor, ksztalt: 'granat', przebija: 0, pewnyKryt: !n && b._pewnyKryt });
  }
}
function wybuchGranatu(p) {
  const r = p.granat.r;
  fale.push({ x: p.x, y: p.y, czas: 0.35, max: 0.35, r: r, kolor: '#ffb070' }); rozbryzg(p.x, p.y, '#ffb070', 14); DZ.wybuch();
  let glowny = true;
  wrogowie.slice().forEach(w => { if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - p.x, w.y - p.y) > r + w.r * 0.5) return; trafienieAtakiem(w, p.bron, { mn: p.mn, glowny: glowny, obszar: true, pewnyKryt: p.pewnyKryt && glowny }); glowny = false; });
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
    if (wzd < -w.r || wzd > zas + w.r || pop > 18 + w.r) continue;
    if (w === cel) trafionyCel = true;
    trafienieAtakiem(w, b, { glowny: w === cel, pewnyKryt: b._pewnyKryt && w === cel });
  }
  if (!trafionyCel && !cel.martwy) trafienieAtakiem(cel, b, { glowny: true, pewnyKryt: b._pewnyKryt });
  b.licznik = (b.licznik || 0) + 1;
  if (b.licznik % (b.tier >= 2 ? 3 : 4) === 0) {
    pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: cx * 470, vy: cy * 470, zycie: 0.9, r: 7, bron: b, mn: 1.5, przebija: 99, trafieni: [], kolor: '#d8d0b0', ksztalt: 'wlocznia' });
    ton(300, 0.08, 'triangle', 0.1);
  }
}
function strzal(b, cel) {
  const B = BRONIE[b.rodzaj];
  let ile = 1 + Math.max(0, Math.round(D.pociski)) + (b.rodzaj === 'luk' && b.tier >= 3 ? 1 : 0) + (B.dodPociskiT ? B.dodPociskiT(b.tier) : 0);
  let rozrzut = B.rozrzut || 0.16;
  if (b.rodzaj === 'pistolet' && b.licznikP % 6 === 0) { ile += 2 + Math.floor(b.tier / 2); rozrzut = 0.1; }
  const zas = zasiegAtaku(b);
  const przebija = (B.przebija || 0) + ((b.rodzaj === 'kusza' || b.rodzaj === 'muszkiet') ? b.tier : 0) + Math.max(0, Math.round(D.przebicie));
  for (let n = 0; n < ile; n++) {
    const off = ile === 1 ? 0 : (n - (ile - 1) / 2) * rozrzut;
    const k = b.kat + off;
    pociski.push({
      wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * B.predkosc, vy: Math.sin(k) * B.predkosc, zycie: zas * 1.25 / B.predkosc, r: 6,
      bron: b, mn: n === 0 || B.pelnePociski ? 1 : (b.rodzaj === 'pistolet' ? 0.7 : 0.6), glowny: n === 0, przebija: przebija, trafieni: [], kolor: B.kolor, ksztalt: B.ksztalt,
      naprowadza: B.naprowadza || 0, cel: cel, odbicia: B.odbicia ? B.odbicia(b.tier) : 0, pewnyKryt: n === 0 && b._pewnyKryt,
    });
  }
}
function strzalPomocniczy(b, w, mn) {
  const B = BRONIE[b.rodzaj], k = kat(gracz, w), v = B.predkosc || 500;
  pociski.push({ wl: gracz, x: gracz.x, y: gracz.y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, zycie: 1, r: 6, bron: b, mn: mn, glowny: false, przebija: 0, trafieni: [],
    kolor: B.kolor || '#e8d8b0', ksztalt: B.ksztalt || 'strzala', naprowadza: 6, cel: w });
}
function piorunBroni(b, cel) {
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
  gracz.oreze.forEach(o => { if (o.cd > 0) o.cd = Math.max(0, o.cd - sek); }); if (gracz.umi && gracz.umi.cd > 0) gracz.umi.cd = Math.max(0, gracz.umi.cd - sek * 0.5);
}
function wystrzel(o) {
  const k = o.kat !== undefined ? o.kat : kat({ x: o.x, y: o.y }, o.cel);
  pociski.push({ wl: gracz, x: o.x, y: o.y, vx: Math.cos(k) * o.predkosc, vy: Math.sin(k) * o.predkosc, zycie: o.zycie || 1.2, r: o.r || 6, obr: o.obr, typ: o.typ,
    kolor: o.kolor, ksztalt: o.ksztalt || 'kula', zr: o.zr, przebija: o.przebija || 0, trafieni: [], naprowadza: o.naprowadza || 0, cel: o.cel, przedmiot: true,
    wybuch: o.wybuch || null, ogluszy: o.ogluszy || 0 });
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
// Limit wampiryzmu (kradzież życia + wszechwampiryzm): ułamek maks. zdrowia na sekundę
function limitWampiryzmu() { const k = KLASY[gracz.klasa].limitWamp || 0; return Math.min(0.08 + k, 0.02 + k + 0.0015 * (Math.max(0, D.kradziez) + Math.max(0, D.omni))); }
// Każde leczenie zależne od zadanych obrażeń / zabójstw idzie przez ten sam limit
// (zapas = 1 sekunda limitu, odnawia się na bieżąco) — inaczej przy ogromnych obrażeniach nie dało się umrzeć.
function leczWampirem(v, zr) {
  if (!(v > 0) || !gracz || !D) return 0;
  const b = gracz._wampB === undefined ? limitWampiryzmu() * D.hpMax : gracz._wampB;
  const x = Math.min(v, b); gracz._wampB = b - x;
  return x > 0 ? leczGracza(x, zr, true) : 0;
}
// Zmęczenie: od 11. fali każde leczenie (poza miksturami) słabnie o 2,5% na falę, maks. o połowę
function zmeczenie(nr) { return Math.min(0.5, Math.max(0, ((nr || 0) - 10) * 0.025)); }
function leczGracza(v, zr, cichy) {
  if (!gracz || gracz.martwy || gracz.powalony || !(v > 0) || stan !== 'walka') return 0;
  if (fala.bezLeczenia) return 0;
  v *= 1 + D.leczenie / 100;
  if (zr !== 'Mikstura') v *= 1 - zmeczenie(fala.nr) * (KLASY[gracz.klasa].polZmeczenia ? 0.5 : 1);
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
//  ŁUPY: doświadczenie, złoto, skrzynie, mikstury
// ---------------------------------------------------------------------
function rozsypKulki(x, y, xp) {
  const n = ogr(Math.round(xp / 1.5), 1, 8), na = xp / n;
  for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), v = losowo(40, 140); kulki.push({ x: x, y: y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, xp: na, faza: losowo(0, 6), opozn: 0.25 }); }
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
  for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), s = losowo(30, 120); monety.push({ x: x, y: y, vx: Math.cos(k) * s, vy: Math.sin(k) * s, v: na, faza: losowo(0, 6), opozn: 0.3 }); }
  while (monety.length > 140) { const a = monety.shift(), b = monety[0]; b.v += a.v; }
}
function dodajXp(v) {
  v *= (1 + D.xpBonus / 100) * (fala.mnXp || 1);
  gracz.xp += v; run.xp += v;
  while (gracz.xp >= gracz.xpNast) {
    gracz.xp -= gracz.xpNast; gracz.poziom++; gracz.doWyboru++;
    gracz.xpNast = xpDoPoziomu(gracz.poziom);
    if (gracz.klasa === 'wiezniarka' && gracz.poziom % 5 === 0) gracz.darmoweWybory++;
    gracz.blysk = 1.2; DZ.awans(); oznaczStaty();
    dziennik('⭐ Poziom ' + gracz.poziom + '! Wybierzesz ulepszenie po fali.');
    if (HAKI.naAwans.length) { zastosujStaty(); hak('naAwans'); }
  }
}
function dodajZloto(v, bezMn, opis) {
  if (!(v > 0)) return;
  if (!bezMn) v *= (1 + D.chciwosc / 100) * (fala.mnZlota || 1);
  gracz.zloto += v; run.zloto += v; run.zlotoFali = (run.zlotoFali || 0) + v;
  if (opis) dziennik('💰 ' + opis + ': +' + Math.floor(v));
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
    if (d < 16) { const xp = k.xp; dlaKazdego(() => dodajXp(xp)); DZ.kulka(); kulki.splice(i, 1); }
  }
  for (let i = monety.length - 1; i >= 0; i--) {
    const m = monety[i]; m.faza += dt * 5; if (m.opozn > 0) m.opozn -= dt;
    const [p, d] = zbieracz(m.x, m.y); if (!p) break;
    const zb = p._D.zbieranie, dx = p.x - m.x, dy = p.y - m.y, dd = d || 1;
    if (m.opozn <= 0 && (d < zb || m.ssij)) { const s = 140 + Math.max(0, zb - d) * 6 + (m.ssij ? 600 : 0); m.vx += dx / dd * s * dt; m.vy += dy / dd * s * dt; }
    m.vx *= 0.92; m.vy *= 0.92; m.x += m.vx * dt; m.y += m.vy * dt;
    if (d < 16) {
      // złoto jest wspólne: każdy dostaje pełną wartość monety razy SWOJE premie (zysk złota, Midas…)
      const v = m.v; dlaKazdego(q => { const mn = mnoznikHakow('mnozMonety'); if (mn > 1) tekstSwiat(q.x, q.y - 28, '🪙 ×' + mn, '#ffd24a', 0.8); dodajZloto(v * mn); });
      DZ.moneta(); monety.splice(i, 1);
    }
  }
  for (let i = skrzynieNaZiemi.length - 1; i >= 0; i--) {
    const s = skrzynieNaZiemi[i]; s.faza += dt;
    const [p, d] = zbieracz(s.x, s.y);
    if (p && d < 30 + p.r) {
      dlaKazdego(q => {
        q.skrzynie.push({ tier: s.tier, boss: s.boss }); run.skrzynieLacznie = (run.skrzynieLacznie || 0) + 1;
        const K = KLASY[q.klasa];
        if (K.podwojneSkrzynie && Math.random() < K.podwojneSkrzynie) { q.skrzynie.push({ tier: s.tier }); dziennik('🍀 Podwójna skrzynia!'); }
        dziennik('📦 Skrzynia (' + TIERY[s.tier].nazwaZ.toLowerCase() + ') — otworzysz ją po fali');
      });
      DZ.skrzynia(); skrzynieNaZiemi.splice(i, 1);
    }
  }
  for (let i = miksturyNaZiemi.length - 1; i >= 0; i--) {
    const m = miksturyNaZiemi[i]; m.faza += dt;
    const [p, d] = zbieracz(m.x, m.y);
    if (p && d < 26 + p.r) {
      const kto = p.mikstury < p.maksMikstur ? p : gracze.find(q => q.mikstury < q.maksMikstur);
      if (kto) { kontekst(kto); kto.mikstury++; dziennik('🧪 Mikstura!'); DZ.mikstura(); miksturyNaZiemi.splice(i, 1); }
    }
  }
  kontekst(z0);
}
function wypijMiksture() {
  if (stan !== 'walka' || !gracz || gracz.martwy || gracz.powalony) return;
  if (gracz.mikstury <= 0) { toast('🧪 Nie masz mikstur'); return; }
  if (gracz.cdMikstury > 0) return;
  if (fala.bezLeczenia) { toast('🚫 W tej fali nie możesz się leczyć'); return; }
  if (gracz.hp >= D.hpMax) { toast('❤️ Masz pełne zdrowie'); return; }
  if (SIEC.rola === 'klient') { siecWyslijHost({ t: 'mik' }); gracz.cdMikstury = 0.6; return; }   // pije gospodarz za mnie
  gracz.mikstury--; gracz.cdMikstury = 2;
  const v = leczGracza(D.hpMax * 0.4 * (gracz.mocMikstur + sumaHakow('mocMikstur')), 'Mikstura');
  tekstSwiat(gracz.x, gracz.y - 26, '+' + Math.round(v) + ' 🧪', '#7ec98a', 1, 14);
  DZ.mikstura(); hak('naMiksturze');
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
  if (gracz.zastoj <= 0 && (mx || my)) {
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
  if (gracz.cdMikstury > 0) gracz.cdMikstury -= dt;
  if (gracz.blysk > 0) gracz.blysk -= dt;
  for (const id in gracz.buffy) { const b = gracz.buffy[id]; b.czas -= dt; if (b.czas <= 0) { delete gracz.buffy[id]; oznaczStaty(); } }
  for (let i = gracz.tarcze.length - 1; i >= 0; i--) { gracz.tarcze[i].czas -= dt; if (gracz.tarcze[i].czas <= 0) gracz.tarcze.splice(i, 1); }
  if (gracz.spowGCzas > 0) { gracz.spowGCzas -= dt; if (gracz.spowGCzas <= 0) gracz.spowG = 0; }
  if (D.regen > 0 && gracz.hp < D.hpMax) leczGracza(D.regen * dt, 'Regeneracja', true);
  else if (D.regen < 0) gracz.hp = Math.max(1, gracz.hp + D.regen * dt);
  // ruch: lokalny gracz steruje sam, zdalnego ustawia sieć
  if (gracz.zdalny) {
    if (gracz.netX !== undefined) {
      gracz.wRuchu = Math.hypot(gracz.netX - gracz.x, gracz.netY - gracz.y) > 0.3;
      gracz.x = ogr(gracz.netX, POD_MIN, POD_MAX); gracz.y = ogr(gracz.netY, POD_MIN, POD_MAX);
      if (gracz.netKX) gracz.kierX = gracz.netKX;
    }
  } else ruszGracza(dt, D.ms, rozmiarGracza());
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
  if (gracz.umi.cd > 0) gracz.umi.cd -= dtCd;
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
function mnUmi() { return 1 + (FLAGI.mnUmi || 0); }
function uzyjUmiejetnosci() {
  if (stan !== 'walka' || !gracz || gracz.martwy || gracz.powalony || gracz.zastoj > 0) return false;
  if (SIEC.rola === 'klient') { if (gracz.umi.cd > 0) return false; siecWyslijHost({ t: 'umi', k: [Math.round((gracz.kierRX || gracz.kierX || 1) * 100) / 100, Math.round((gracz.kierRY || 0) * 100) / 100] }); gracz.umi.cd = 0.5; return true; }
  const U = KLASY[gracz.klasa].umi; if (!U || gracz.umi.cd > 0) return false;
  let ok = false;
  try { ok = U.uzyj(mnUmi()) !== false; } catch (e) { zglosBlad(e, 'umiejetnosc ' + gracz.klasa); }
  if (!ok) { if (!gracz.zdalny) toast(U.ik + ' Brak celu w pobliżu'); return false; }
  gracz.umi.cdMax = U.cd * Math.max(0.25, 1 - (FLAGI.cdUmi || 0)) * 100 / (100 + Math.max(0, D.haste));
  gracz.umi.cd = gracz.umi.cdMax;
  if (gracz.stanKlasy.natychmiast) { gracz.stanKlasy.natychmiast = false; gracz.umi.cd = 0.4; }
  tekstSwiat(gracz.x, gracz.y - 34, U.ik + ' ' + U.n, '#ffe08a', 1, 13);
  hak('naUmiejetnosci');
  return true;
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
      if (p.przedmiot) { zadaj(w, p.obr, p.typ, { zr: p.zr, pocisk: true }); if (p.ogluszy) oglusz(w, p.ogluszy, { zrodlo: p.zr }); }
      else trafienieAtakiem(w, p.bron, { mn: p.mn, glowny: p.glowny !== false, pocisk: true, pewnyKryt: p.pewnyKryt });
      if (p.wl) kontekst(p.wl);
      if (p.wybuch) { const wb = p.wybuch, zr = p.zr; fale.push({ x: p.x, y: p.y, czas: 0.3, max: 0.3, r: wb.r * mnObszaru(), kolor: p.kolor }); obszarowe(p.x, p.y, wb.r, p.kolor, o => { if (o !== w) zadaj(o, wb.obr, p.typ, { obszar: true, zr: zr }); if (wb.podpal) podpal(o, wb.podpal, 3, 'mag', zr); }, true); if (wb.podpal) podpal(w, wb.podpal, 3, 'mag', zr); pociski.splice(i, 1); usun = false; break; }
      if (p.bumerang) continue;
      if (p.odbicia > 0) {
        p.odbicia--; const nast = najblizszyWrog(p.x, p.y, 220, p.trafieni);
        if (nast) { const k = Math.atan2(nast.y - p.y, nast.x - p.x), v = Math.hypot(p.vx, p.vy); p.vx = Math.cos(k) * v; p.vy = Math.sin(k) * v; p.cel = nast; p.zycie = Math.max(p.zycie, 0.8); p.mn = (p.mn || 1) * 0.8; continue; }
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
      if (Math.hypot(p.x - g.x, p.y - g.y) < g.r * rozmiarGracza() + (p.r || 5)) {
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
    for (let j = 0; j < n; j++) { const w = wrogowie[j]; if (w.martwy || w.zauroczony > 0 || Math.hypot(w.x - p.x, w.y - p.y) > p.r + w.r * 0.5) continue; if (p.rodzaj === 'mroz') spowolnij(w, 0.3, 0.4);
      if (rani) { zadaj(w, p.obr, 'mag', { dot: true, obszar: true, zr: p.zr }); if (p.rodzaj === 'kwas') w.krusz = Math.max(w.krusz || 0, 0.15); else if (p.rodzaj === 'ogien') podpal(w, p.obr * 0.3, 1.5, 'mag', p.zr); } }
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
        if (Math.hypot(g.x - u.x, g.y - u.y) <= u.r) { kontekst(g); zranGracza(u.obr, u.typ || 'fiz', { bezUniku: true, wybuch: true, kto: u.kto || 'Uderzenie bossa' }); if (u.mroz) spowolnijGracza(0.5, 2); }
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
function rozbryzg(x, y, kolor, n) { if (SIEC.rola === 'host') siecZdarzenie(['r', x | 0, y | 0, kolor, n]); if (USTAW.efekty === 'oszczedne') n = Math.min(4, Math.ceil(n * 0.3)); for (let i = 0; i < n; i++) { const k = losowo(0, 6.28), v = losowo(40, 140); czastki.push({ x: x, y: y, vx: Math.cos(k) * v, vy: Math.sin(k) * v, czas: 0.45, max: 0.45, kolor: kolor }); } if (czastki.length > 400) czastki.splice(0, czastki.length - 400); }
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
    try { if (T.tik) T.tik(s, dt); } catch (e) { zglosBlad(e, 'stwor ' + s.typ); }
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
  mina: { ik: '⚙️', r: 8,
    tik(s) { const c = najblizszyWrog(s.x, s.y, 24); if (!c) return; s.usun = true; DZ.wybuch(); rozbryzg(s.x, s.y, '#ffb070', 16); fale.push({ x: s.x, y: s.y, czas: 0.35, max: 0.35, r: s.r, kolor: '#ffb070' });
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
  { n: 'Spacerek', ik: '🌱', hp: 0.4, atak: 0.33, tempo: 0.72, spawn: 0.9, ms: 0.95, elity: 0.5, zloto: 1.0, skrzynie: 1.1, hpBoss: 0.8,
    opis: ['Wrogowie mają o 60% mniej zdrowia i biją o 67% słabiej', 'Elity rzadziej', 'Na spokojne poznanie przedmiotów'] },
  { n: 'Normalny', ik: '⚔️', hp: 1, atak: 1, tempo: 1, spawn: 1, ms: 1, elity: 1, zloto: 1.05,
    opis: ['Tak, jak gra ma wyglądać', 'Boss co 5 fal'] },
  { n: 'Trudny', ik: '🔥', hp: 1.3, atak: 1.25, tempo: 1.08, spawn: 1.05, ms: 1.03, elity: 1.5, zloto: 1.1, specjalneOd: 2,
    opis: ['+30% zdrowia, +25% obrażeń wrogów', 'Szybciej rosną w siłę', 'Elity o 50% częściej', 'Fale specjalne już od 2. fali'] },
  { n: 'Koszmar', ik: '💀', hp: 1.65, atak: 1.5, tempo: 1.16, spawn: 1.1, ms: 1.06, elity: 2, zloto: 1.15, specjalneOd: 1, falaStart: 'elitarna', hpBoss: 1.1,
    opis: ['+65% zdrowia, +50% obrażeń wrogów', 'Dwa razy więcej elit', 'Pierwsza fala to fala elit', 'Bossowie +10% zdrowia'] },
  { n: 'Piekło', ik: '👹', hp: 2.1, atak: 1.85, tempo: 1.25, spawn: 1.12, ms: 1.1, elity: 2.6, zloto: 1.2, specjalneOd: 1, falaStart: 'horda', afiksy: 1, hpBoss: 1.25, msWrogow: 1.04,
    opis: ['+110% zdrowia, +85% obrażeń wrogów', 'Elity mają dodatkowy afiks', 'Start od hordy', 'Wrogowie szybsi'] },
  { n: 'Otchłań', ik: '🕳️', hp: 2.75, atak: 2.3, tempo: 1.35, spawn: 1.15, ms: 1.14, elity: 3.2, zloto: 1.25, specjalneOd: 1, falaStart: 'horda', afiksy: 1, hpBoss: 1.45, msWrogow: 1.07, regenGracza: 0.5,
    opis: ['+175% zdrowia, +130% obrażeń wrogów', 'Bardzo szybkie skalowanie', 'Twoja regeneracja o połowę słabsza', 'Dla szaleńców'] },
];

const SPECJALNE = {
  horda:    { n: 'Horda', ik: '🐀', opis: 'Dwa razy więcej słabszych wrogów · +40% złota', ustaw(f) { f.mnSpawn *= 2; f.mnHpWrogow = 0.65; f.mnZlota = 1.4; } },
  elitarna: { n: 'Fala elit', ik: '👑', opis: 'Mniej wrogów, ale co kilka sekund elita', ustaw(f) { f.mnSpawn *= 0.6; f.elityCo = Math.max(4, 8 - f.nr * 0.1); f.tElity = 3; } },
  zacmienie:{ n: 'Zaćmienie', ik: '🌑', opis: 'Widzisz tylko blisko siebie · +50% doświadczenia', ustaw(f) { f.ciemnosc = true; f.mnXp = 1.5; } },
  zlota:    { n: 'Gorączka złota', ik: '💰', opis: 'Złote gobliny uciekają z łupem — złap je!', ustaw(f) { f.zloteGobliny = 5; f.tGoblina = 3; } },
  ania:     { n: 'Nalot Ań', ik: '🦇', opis: 'Ania w dziesiątkach egzemplarzy', ustaw(f) { f.wymuszony = 'okrazacz'; f.mnSpawn *= 1.15; } },
  patryk:   { n: 'Smród Patryka', ik: '🦨', opis: 'Wszędzie trujący gaz', ustaw(f) { f.wymuszony = 'trujacy'; } },
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
  wrogowie = []; pociski = []; pociskiWrogow = []; kulki = []; monety = []; skrzynieNaZiemi = []; miksturyNaZiemi = [];
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
    p.tarcze = []; p.zastoj = 0; p.niewr = 1; p.spowG = 0; p.powalony = false; p.reanim = 0; p.cdMikstury = 0; p.dash = null;
    if (p.umi) p.umi.cd = 0; p.oreze.forEach(o => { o.cd = Math.random() * 0.8; });
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
  if (nr === 11) dziennik('🥀 Zmęczenie: od teraz leczenie słabnie o 2,5% z każdą falą (mikstury działają w pełni).');
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
  // wszystko zostaje zebrane
  wrogowie.forEach(w => { if (!w.martwy) { rozbryzg(w.x, w.y, '#5a4a6a', 6); } });
  wrogowie = []; pociskiWrogow = []; zapowiedzi = []; bomby = []; kaluze = []; uderzeniaBossa = []; stwory = [];
  let xp = 0, zl = 0; kulki.forEach(k => xp += k.xp); monety.forEach(m => zl += m.v);
  const sk = skrzynieNaZiemi.slice(), mik = miksturyNaZiemi.length;
  // minimum skrzyń na falę
  const brakSk = Math.max(0, zakresSkrzyn(fala.nr)[0] - (fala.skrzynie || 0));
  for (let i = 0; i < brakSk; i++) { sk.push({ tier: tierSkrzyni(null), boss: false }); fala.skrzynie = (fala.skrzynie || 0) + 1; }
  kulki = []; monety = []; skrzynieNaZiemi = []; miksturyNaZiemi = [];
  dlaKazdego(p => {
    const bylPowalony = p.powalony;
    if (p.powalony) p.hp = Math.max(1, D.hpMax * 0.35);
    p.powalony = false; p.reanim = 0;
    // wszystko, co zostało na ziemi, zbiera się samo (100%)
    const zl0 = gracz.zloto, xp0 = run.xp;
    if (xp > 0) dodajXp(xp);
    if (zl > 0) dodajZloto(zl);
    if (xp > 0.5 || zl > 0.5) dziennik('🧲 Zebrane z ziemi po fali: +' + Math.floor(gracz.zloto - zl0) + ' 💰 · +' + Math.round(run.xp - xp0) + ' ✨ doświadczenia');
    sk.forEach(s => p.skrzynie.push({ tier: s.tier, boss: s.boss }));
    for (let m = 0; m < mik; m++) if (p.mikstury < p.maksMikstur) p.mikstury++;
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
    run.przerwa = { nr: fala.nr, augment: czyAugmentPo(fala.nr) ? tierAugmentu(fala.nr) : null, sklep: false, proba: false, kowadloPo1: fala.nr === 1 };
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
  if (!p) return;
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
  if (druzyna()) { gotowyDoFali(p.nr + 1); return; }
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
const SPR_KULKA = sprite(12, (c, r) => { c.globalAlpha = 0.4; c.fillStyle = '#7ee87a'; c.beginPath(); c.arc(r, r, r, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1; c.fillStyle = '#b8ffb0'; c.beginPath(); c.arc(r, r, r * 0.42, 0, Math.PI * 2); c.fill(); });
const SPR_MONETA = sprite(8, (c, r) => { c.fillStyle = '#b8860b'; c.beginPath(); c.arc(r, r + 0.6, r - 0.5, 0, Math.PI * 2); c.fill(); c.fillStyle = '#ffd24a'; c.beginPath(); c.arc(r, r, r * 0.78, 0, Math.PI * 2); c.fill(); c.fillStyle = '#fff3b0'; c.fillRect(r - 2, r - 3, 2, 2); });
const OBRAZY_TWARZY = {};
[['ania', '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwQDAwQEBAQFBQQFBwsHBwYGBw4KCggLEA4RERAOEA8SFBoWEhMYEw8QFh8XGBsbHR0dERYgIh8cIhocHRz/2wBDAQUFBQcGBw0HBw0cEhASHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBz/wAARCABgAGADASIAAhEBAxEB/8QAHQAAAgICAwEAAAAAAAAAAAAABggFBwAEAQMJAv/EADoQAAEDAgQDBgQFAgYDAAAAAAECAwQFEQAGEiEHMUETIlFhcYEUMpGhCBUjsdEkUjNCQ0SC4ZLB8P/EABoBAAMBAQEBAAAAAAAAAAAAAAMEBQACAQb/xAAgEQACAwEBAAIDAQAAAAAAAAAAAQIDESESBDETIjJR/9oADAMBAAIRAxEAPwDz/wAZjMZjGMGCCh5LrOYCgxIi+yX8riwQk+m1z7DBDwyya3X3ZlTmoCoEAbIX8rrp5JO/Iczi24tEqVTPwcBx9hoNJS8to2UVHp5ADp54DZb54g1dLn0ran8H1NOaqxPKEAbtR2yFE+GpYAH0OCaLlHKjEZbH5MoyRul595Sirfw2Fj5YIZnDmr0Od8bTHHFxrXdiuFxXaJHPxuetxY4k4ggS2Y4Wx8WtwXaKk3UBfcEna4wB2t90M6fPGgcZp1PWyhr8qgtR4wCWmiyhSSSq6iq43G3UnnbE7Usl5FzMlpUzK4pjbgsahl11QKD/AHKYcJSR5JIPhiSmU5pyOWZTbTDROyUgEgjlyxowM1Jy6w9CXDUtFyttYI0k9Rv064ym/uJlFLjKsz7wIrGVaa7XaLMYzHlhHzzoSSFx/J5o95v13Hnip8N/l7NbESofnMB9LU9AKHIoOpEhBG6FpBspJuQbjFV8deGUCjfB5zymyoZTrY19hzMB+9ltHwSFXt9PDDFdnrjA2VpdiUpjMZjMFAmY+m0FxaUJF1KNgPPHzjkbG/UYxhkqLltVBpsKG0h0Jba1q37i3LXJV479PAYPMvVxnL9PQ3ChuSnV7mVIOlLiuqgOZucV7kipzswZZpwfWt15MZxOonvLOrSCT6DFtZcyxWqw2yWIjcSMAB20g2Fh/aOZ+2JtvXjKdGr+D5mZhrK9BeW2xfvBLSALe/PEPJdjOPtMJbBLmpTlhpANufrfFwUvhZCeUldRmPylAckfpp/nEhUMt5WpaPh2RTo7/gt0Fwn3ucDSz6GXVOX9MowvM1GGGuzdYetvqSCAoY4FNYUhkPR2nlIJOop6+mC/N2SmnoX9I27CkN7tuMBYQ6PE2xWynqjE7Hs3TpSbLsm4VvY++PVIFKholH4VJZkty5FPYZeSe64kaAfYbYO8rR6fmfLGYaBKSmRCTok6Cdi2u7bgt4/Kb+IBxVb9WlOuraeQhxTQuW7WB8+eCfgtmmlT+IApbbxZl1CJIjrjOJsFdzWCk8jujBK290FKDX2hU8/5Qk5GzbUqHIBPwzh7JZ/1GzulXuMDWHN/ExwzXmXLbOZ4LBNTpbP6yEi5dYHzepTsr0JwmWH4vUITj5eGY5GOMcjHRwOtTKJS8o0rIzk8tMtfkMZ9y4J1OkE/KOZurYYtqkZjiS22w01JQdjd5gtjl54D6rVItMGU5bgCm2KJFCCUg2UppJuPPa3vjsYzDVKx2A+DadjvN9oVJcsprvAWUeQNrm3lbEyzrLvx/wBUi2n46ptEKm3yyFKF1INiR1GAkvU3LkgoiU8PS0pUvUlBW5Ybkk8/PHfQ6hIFNaadWVI1KBB9dsd9RgxZDqZXZhStOlYJ3wH0OqG9Oqm8Q0Vt34csSktWGlxSDoVcX2O/jgJ4j0BuBPamsJCotR/xEJ/yu23I9dsWZTEOTXG2EIQ02AANunhiPz/T0Jy++si/w6g4D72OOW1vDWQyPRcqklpp0O6TrV3LnbUT4j6YGuG7gpvHPJ8j5Qai2glPIpXdFj/5EYIc7ymWhJbbKbKBUkFVrEHbFe0Csac9ZWqZKQUT4+sp56g8n6Yap4TbmP27TUuwFpWgEIWUlJFwpJuCPtjzh415HTkHiHVKYwgoguESYoPRte9vY3Htj08hsdsKg0ofI+sDy76v5wqv4v8Ah49U6VDzHDb1yKTqbkAc1MK31f8AE39ifDDVcu4KXw2OiV45GN5NEqa6S5Vk0+WqltuBpUwMq7FKzySV2tfyvjVjsqkSGmk7qcUEj1Jtg4kOpJkKfoGRFBKgF0aIvvDckAC5HtbFl0SHaGhLaRpQnUB47XtgB4uMJypBymtoBLUOKmJ5WQbD7YPeG9fiVqjNPNrBcbOhxJ5pUOYOJVqes+h+M45jN2BTHPytp5bqW0r6qPNR3Jt4YkIbzrzYhOtMvrAKkOs/NbwOI9K47VWktF0tQ21atBOyTz64notepygoR0qW9YkhhvUTYeWANPR6MuaTFEXEYhrCB+t8p1DdOILN6TLy9VWE7qUwoD1tiMrWaYsNKZEht5lYUEhaiApW9raeZ5+GCJjs32Gl/MlxOkpI+ox7JZjOJv1ojWaaoJLbo74cPdVfptb+cA9KkBuqsBWykSmXUeoWkn7YsDiZR/yTN1TihIS24rt2T4pO/wDIwJx8n1iu1VbNDpkic+1GXKWIyCtaEJsNSh0F7AdTh+rMIt2+j02pF/j6mCq6S8q3qbnERniht1Giy9bYcRpuUkXBHUe4JxqcN68nMWXGK20dpzKFqSsWKXAgBabeIUCMHEmMmTAWhZuFpII9cerh246sEO488SmcqZTVw8y2qPGizUpEyGygFDDQOoADklSjYnrYeeF/4a0Y5hz/AJbpo/3M9lJ26agT9hgakSHpT7j77q3XnFFS3HFFSlE8ySeZxaP4cYxf4v5fdAv8KXX+V7FLarfcjBoR/HDBK6389vrMGL/ExUUSqHTWmLWYlrQo223Rf9ycUZw74ovZKzUj4t1Qpc1KQ/ffs1jYL9NrH/rF5cfaeqNlRpCk63Fym3NQ5kjVq/fCd1JBQpm9r2V0vbAlFS1MalNxxofyux2HorOY4jiZUZ5AJYJ/TUbWBuOeJCkVOe7CMf8ATZUrctxG+zTa1um568zhXuE3EuXlhgZarhWKDLZS6045f+n1HurF+aFXHphkaNDblNNq+McLZTbuEDUPDVhScHDjKfx7YW9Z806gmr1lh5xBVEhuB1arWC1J5etjy8/TB6pXYokLHdHze5GOaXHS3H7FptKGk22GwxpVWqIgpDDf6sh1V0toFyq2BS7wZsksFg40Nqm5iiEFJWIpsQPA3/e+B7IGb6lkfMxfZddTAqkbsZrDNrutCy7W56kqBOxHUdcGubKY8cyoXJ7zzCTqAuUjcEp9hfADmqI1BqDim9QCFBbfdsE6wBz6jf74br/nCTN5L0hu8j15t6IJNKmMOQpBKg0N23SeZ23Sr/4jFtor8NbLSJOqI4QB+t8nssbfW2EG4a192jVh5pqUtFiCppPJWk2NhyP78sN/SqrUHaIxUHIpl09wbvx06wkdNSOafuMC2UH/AKNuVd/cxnlnTqPPrD/Y0+DJmO2uW4zSnFfQA4Z78L3Dyu0DOEifXKBLgsSIhbjvSEaSVagSmx3uQPDphr6RlGnUqIWocSPFQqwKY7SWxYdO6BjumU1LYDjACFxrONkdFYdlPVhJro8tNsp/j9HVNy7AHZkqU44Ujr4k4SbMEZLMwtoNwHFgED0w9vFl9L9Ioy1IKTc8twdWElrrQcqUm6bBLiufmTvgcH0NbHht0bPtQo1PXCejMTAlpCYbjw70ZSTsdvmA8Dhl+CleqNeoKlynGpE1t5RW2LNgg2I0/Wx88KgxTFyUaCO+N7DmbeBxZfD6ZUaCiRIpMlQeZspUN0X1gf2/+xjm5bHhvjycJa/obtyp1JT/AMOiOmKFDda1aiPQDniZptPYiJU8Apx9du0kOi6iPAeA8hioMmcYaHmJxqPJdbiVICxbJsFeNgcGOZM+waXSnEsy2X5Ll9IQqwIAvzP39MIP03jRS9prdKp4gVRELNstabEKklBsL32/7xUFaraZWZW0vECO8EMKHRBtYH2NsbdWzK/W2KrPecv2b6VJIHS9sAUxS5kl5dyO0WpST02O2Hqo8J9slvAnRUk0zNiHOi3LK07gXAFx7i+Hl4BZp+Loi4r7neClKQSbabHcXHqcefVLd+Or9KbcJacceS2VJHJWoWNvC5w3/BOpPMVFLh7hdb1rsetgFbeB3+gxpLGjqp8Z/9k='], ['patryk', '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwQDAwQEBAQFBQQFBwsHBwYGBw4KCggLEA4RERAOEA8SFBoWEhMYEw8QFh8XGBsbHR0dERYgIh8cIhocHRz/2wBDAQUFBQcGBw0HBw0cEhASHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBz/wAARCABgAGADASIAAhEBAxEB/8QAHAAAAgIDAQEAAAAAAAAAAAAABwgFBgIDBAkB/8QAORAAAQMCBAQEBAQFBAMAAAAAAQIDBAURAAYSIQcxQVETImFxCBSBkRUjMkIWM6HB0VJisfAXJJL/xAAbAQACAwEBAQAAAAAAAAAAAAAEBQIDBgABB//EACsRAAICAQMEAQMDBQAAAAAAAAECAAMRBBIxBRMhIkEyUWEUFSNCcaGx8P/aAAwDAQACEQMRAD8AdG3pj4dsbLYH3F7iErh7ldUqIhL1WlK8GGyoeUq6qPokb/bDNmCjJiRKy7BRzLPmTMdMytSZFTqklDERhN1KPM+gHU4XHP3xQxZFKej5ejutyF7eNIAUEgnYgA8+vpha8+Z4zDnKqJVWavKmutElLbjnkv6J5AfS+2KMia4zLUlxa1JeARcqJ3G+wPIYCfVMfp8CNqdCq+X8mFGocds7SJzjrtcnvMtrUkLQ8EG452SNjyxL034j88Qyl1usSXUGxtI03v2KVA2+mAi6+qGgNqSoFXiaiD/utcf1xzNJ1pUha1OtEFIKri3+MD9w/eGdoDxgRnIvH7Nk6UJTlXlJC91NJ0o0H0AFj/XBWyr8SRB8KrU6TIYuP/YYSkOJH+5G1/cW9sIdDUuPZKXijbbxDZSSO464nqfmKfTn0KkMK8MeUuoJKD6+n0xHv2IfUyX6aqwYYT1FyvmilZwpoqFJmIktX0rCdlNq/wBKkncH3xN6cIxwa4sN5YzHDfkSVCPJIafCz+pB6kjnbmMPQhaHm0ONqCm1gKSpJuCDyOGOn1HdXJ5ifWaXsN44MwKb4xLfbG4jHy2CQYERPk2XHgR3ZEp5DLDSSta1mwSB1J6DCG8duM8HNGZJjsJ8rhQWvAZWd0oTfcgdVKJ29hgvfFLakUNhiTVJcyrVR0pixlK0xozadyfDGylchqVc9rYQyuSS2sMIIXoWVrWd9a7Wv99vYHvhXq7cntiOun0BV7p5lpamfMJkOBkl5XkSkG+m4ubnqT19scFVgFuMkgfmEagB/q52++OZzMDdOiNx0N6n9atZHtYX+mNiamhxLRcWCUgKKu5INvpv9hgHcRGoQETRKSp9SVq8qtBFhyuNyfvjnffcQ0oNailVio2uEgdh9f8ApxIIeQHkJePlWoBXobeb788dMeMLvqTZWhXK17pUkH+2OL4khXkyD8ZXyCJDjep9PlJQbFy3Ig/83xupOYYC1piFKmSeaFXNz3B5Y+qipYkqQ2QYzoJCVcknp/jGudluNIdada/UUJXYHcEcxfHbgeZ3bYcS4RG4hSHo6vJfcj9p9u3/ABhq+CHHg02DDy9XUl6EyNDMwHzNJ7KHVI79AMJbFZkQxMSJSyoWWgqG5Seh72xc8p1qRHlrS4nUpIJOk7EdSP7++JV2tW25ZXdQty7WE9R21peQlaCClQBBBuCD1GMyMVfhxUkVnJtHmMNJbivRkKbSHNZAtyxayMPAwIyJlXUqxH2iB/E5nN2sZ1fnPK8KntpVDpwKrl0JJQpwDoCsKA72wp7y3EyF6gTZ1JO/qB/jBh450yuUmvU52uFQWpkNRGtNtKEHSkbdep9VHAjkalSFx2klbpIOkbkm9z/30wms+smaWgAVgCTVCpq6i8p5RJKlki37trAf1OJWTllUd9lla1BKPMT1WrskdelzyAxbuGuQsw1ox/lqQ23FdaW4iVUnfl4ukEBRSsi6/wBSf0A88EZPBCnTJINVzzBhXPmTTIK1p9tS1pUrA5qtLZ4EMGpoRQD5MEtDyu7X6qxTG7JjM/mSJHc9va+w74sUDKcQV99KnfFpDZ0eNyQtwAa0hXI6fsbEYvdX4W0HLFCqcmk5x+dQ02XXYzzTjDj4HOygpQ5cgTv6YHlBzPQpdZh0dbwIS6lso3IG/mCdV06rX+uKzp3P9UtXWVAAhMn/AL+82Z0yXSqwRHy8uTKmqP5MeGz4iifZPfEllH4b+LkyKCcoy2f3NrfKWzb1CyNsNBww+IPLdNqlcodPyKzRotNUltqTEeQ+5JBJ/mclA7A81c7c8auI3xq07KsmlCBCcc8GelNRYeYAW5HKVCzaivZV7G5B2xbWir/G2TBbtRZYTYoAi35g4A8RctxpEio5ZliOyNZcYCX/AAk8zs2pSiLX6HFSpsKVRgxPW0l6lydIRIZWFI1FJOnuARYj2I6Yb6V8cGVSzNVWMoV2K2ytsNJAQp5YUDc2JABBF+ZFvthccxZtyjmqTnv+GhIhZbnhT0JMtkNONSlALSEoBNgXddh2UeWChVUV9fBgY1N2728iMF8L3EFUyXJy1suL4PzUYE/pF/NY9rnlhobXF+mPMz4falOXnGm/Ih1xhK0pUhpakrQgnzqBSQdrn7Y9L4MVcaK20t115SRbW6rUo/W2+CdI5KYPxF/UqwtgcfMUz43eFsurUrLuaKTGU9+GyfAkstIuoBywQq3bUkD6jCSUmHqYeU8gIXInxoy1L28hJK0nsDbf2x7PPMNyG1tPNocaWLKQsXBHqMIr8YPCJ/Kk+TnOjRC9QK4623PjMt+aDLTctyEW/arcKHqe4xG1fbfJae/K9oyGqD8mdWEyxKdDaWFR0B5BXpQF6hp6JSLWt2tytgc1vMJy3mF9jMVcmKp08tLiFp3whHUL6goI/byuPrjfT890arwY7s2pMxqi02UOtSHC2oLAsSAdiCOuB1mCTRp9birlKVUmmkgJeS4pzQL/AKdP7vqffA6+OYUF+FhWzRWHaNlOsS2SmQyllQJDpUU69rkm5/dsMWDKfB2mZj4WU2OGW2K0+wmU1LSLLaeI1Ak9d+YwHKnKn50Q1SYUd+NSVLT4viEFx+xuLhOyR9SdsOHkxcCn0uJFbeF47SUX58gMLtdaMDaeJp+g6MkubV8EY8xHvw+qU7OLcwuuxJMWbpmsovrjruNVwNygkXB9RzxeszZZhV6dHqMuppU3HWZbtkC71rEhRsCdhYbbDbBl4mcKqPnyt/icB5MapGyHHUC1z0BsQd+mK3B+HV51QE6ryVpGxSHF8u25xIdRrAG7mVWdBv3EIRiRETPtBzJHU/PjJYuNIQtGpTl97Ib3Jxpb4USKllerznYq6WzUJqExW1j8xlspUA4pP7d1Cw527YMmWuD2XssuJeYjBcpI/mOHUrFyq0NtdDltJSLBPIdxuP64gNeth2oJ5+zmgb7DmUH4QOFrVJzxmORMleI7SUJDLJRpJKzYrPp5eXrh2Cm3LAH4GxA7m+r1MeR6XT2/FCeWtLlr/bB8Iw06dabKAx/MzvX6Fp1hROMD/U2jEZmWjtZgy/U6W+hKm5kdxmxF7EpIB9wd8SQN8fHFEIURe9tsFkZ8RYpwcied+X6EJGWVwZbQ+ahvqbc1p8wPI8/UYzhcJKS+947yCtR3sTtg6cXsqiiZlmVaPHLMSsN+M4NrfMJI1/cWV7k4odPmoSE3UN8ZvWh6ztzxN902yu0dwDmRK8nxKPDUqHFQFp5WFsUzLjGZ4NQqEp6Yt+C67qajFFiykdz2PbfBUnzQ4PCSem5xU386UqhrW06jxUq8q1BSR9r88Ao7bSMZjxUDuCDjE78p5EjZeqb9WhSJaV1Ffjymn3S6kqve463vgvRHGXkJVYBZ5YBf/l+JDWlEeIt1i9khCFrWv/5BAxYoXFamy3GGEx5Tcl02KHGVAoHc7Cw9cVOljeWhTlEUBePxCNPXo1Ht1xHh4vIcQb2VtjSZwlxwvVcEbHvjFtQYbFzfHaf1YQDU+yGF7hXTmKLTarVpITHZUUsgqGlKUovqPtqPPuDgiU6c3VITMtg3ZeTqSruDywlPw507PXFRc2NXMwN/whR5y1OwgDrmuFZKdZ7WF+e/brh32GPBaSgAADYACwA7WxsNIgrqCj4nzfqdhuvaxuT/AIHxMAvGYVjkvjAydGDdmYFiVTifDgVGhORp8YLT+tp1TqGUtLsQFaibnnuADcYUJh4xn1NLVZSFafTbDl5sy9CzfSVxZK5DSxuhxhZSsH0IOFX4j8M1ZEjIlxqiZUXXoWiS6DISSdibm6h07jthT1LTsw3Y4j/o2qWs7CeZUcwJlzmnGYUv5Z1Y/m6dVh7YgqRQMu0pSFVSnJmTR+qU8u61ffkPQYmqVKTMWlGrc8sWJGW4j+hUlCHNXQ9cIWbtjBmz0tvsGUSKgZootOWtmmRo7alk6bJ1qAJ5XxYoYMpsqUypS3NiV8yP7YlYVFpEJKUoiMpRfeyRibjOU+OlQ8ot+k4FazPgRjba9g9jINrVHQhg8k4xlzRfw9XmPXtjlr9ZjxlFYUADyxBxFPSQqW6dLY3AOLEG32aLXO/0WWn4SMyUTI2Ta7DlPOyMyO1J9TsBpxJNgqySAbabgdb4NtNzpmLMhemPt/hVOJIYYSPzVgc1LJ5elrX54WDhTQatmXiPPEdlLWXYZ+amSALFxSuTNxvuQSfQHvhqHJSdKAAQGxchHS3X+2Ndpn3oDMJqtOK7mB+8/9k=']].forEach(p => { const im = new Image(); im.src = 'data:image/jpeg;base64,' + p[1]; OBRAZY_TWARZY[p[0]] = im; });

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
      else if (war === 4 && z % 23 === 0) { ctx.font = '13px sans-serif'; ctx.globalAlpha = 0.35; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(z % 2 ? '🦴' : '💀', ex + 22, ey + 22); ctx.globalAlpha = 1; }
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
    const a = Math.min(1, p.czas / 0.8), g = ctx.createRadialGradient(p.x, p.y, 2, p.x, p.y, p.r);
    const k = KOLORY_POL[p.rodzaj] || KOLORY_POL.mroz;
    g.addColorStop(0, 'rgba(' + k + ',' + 0.32 * a + ')'); g.addColorStop(1, 'rgba(' + k + ',' + 0.06 * a + ')');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
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
      const my = e.y - 220 * (1 - p); ctx.font = '22px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('☄️', e.x + 60 * (1 - p), my);
    } else if (e.rodzaj === 'granat') {
      ctx.strokeStyle = 'rgba(255,160,90,' + (0.4 + 0.4 * p) + ')'; ctx.lineWidth = 2; ctx.setLineDash([6, 5]); ctx.beginPath(); ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      const bx = e.sx + (e.x - e.sx) * p, by = e.sy + (e.y - e.sy) * p - Math.sin(p * Math.PI) * 60;
      ctx.font = (e.r > 150 ? 26 : 18) + 'px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('💣', bx, by);
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
    ctx.font = '22px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('💣', bm.x + (Math.random() - 0.5) * 3 * (1 + post * 2), bm.y);
    ctx.restore();
  });
}

function rysujLupy() {
  const t = Date.now();
  skrzynieNaZiemi.forEach(sk => {
    if (!naEkranie(sk.x, sk.y)) return;
    const kol = TIERY[sk.tier].kolor, ex = sk.x, ey = sk.y + Math.sin(sk.faza * 3) * 1.5;
    ctx.save(); ctx.shadowColor = kol; ctx.shadowBlur = 12 + Math.sin(t / 380 + sk.faza) * 7;
    ctx.fillStyle = '#6b4a2a'; ctx.fillRect(ex - 14, ey - 10, 28, 20);
    ctx.fillStyle = kol; ctx.fillRect(ex - 14, ey - 14, 28, 7); ctx.fillRect(ex - 3, ey - 4, 6, 8);
    ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 1.5; ctx.strokeRect(ex - 14, ey - 14, 28, 24); ctx.restore();
  });
  miksturyNaZiemi.forEach(m => { ctx.save(); ctx.shadowColor = '#e6543c'; ctx.shadowBlur = 10; ctx.font = '18px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('🧪', m.x, m.y + Math.sin(m.faza * 3) * 3); ctx.restore(); });
  monety.forEach(m => {
    if (!naEkranie(m.x, m.y, 20)) return;
    const s2 = 0.55 + 0.45 * Math.abs(Math.cos(m.faza)), r = 4.5 + Math.min(3, m.v * 0.25);
    ctx.drawImage(SPR_MONETA, m.x - r * s2, m.y - r, r * 2 * s2, r * 2);
  });
  kulki.forEach(k => {
    if (!naEkranie(k.x, k.y, 20)) return;
    const r = (8.5 + Math.min(6, k.xp * 0.3)) * (0.85 + Math.sin(k.faza) * 0.15);
    ctx.drawImage(SPR_KULKA, k.x - r, k.y - r, r * 2, r * 2);
  });
}

function rysujWrogow() {
  const t = Date.now();
  for (let i = 0; i < wrogowie.length; i++) {
    const w = wrogowie[i];
    if (w.martwy || !naEkranie(w.x, w.y, w.r + 40)) continue;
    const ey = w.y - (w.wysokosc || 0);
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(w.x, w.y + w.r * 0.8, w.r * 0.9, w.r * 0.35, 0, 0, Math.PI * 2); ctx.fill();
    if (w.trafiony > 0) ctx.globalAlpha = 0.6;
    if (w.duch) ctx.globalAlpha *= 0.65;
    if (w.elita) { ctx.shadowColor = '#ffd24a'; ctx.shadowBlur = 16 + Math.sin(t / 260) * 6; }
    if (w.boss) { ctx.shadowColor = w.poswiata || w.kolor; ctx.shadowBlur = 22 + Math.sin(t / 220) * 8; }
    if (w.zauroczony > 0) { ctx.shadowColor = '#ff7ae0'; ctx.shadowBlur = 18; }
    if (w.przygotowanie > 0) { ctx.shadowColor = '#ffd24a'; ctx.shadowBlur = 28; }
    const tw = w.obraz && OBRAZY_TWARZY[w.obraz];
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    if (tw && tw.complete && tw.naturalWidth) {
      const rr = w.r * 1.12;
      ctx.beginPath(); ctx.arc(w.x, ey, rr + 2.2, 0, Math.PI * 2); ctx.fillStyle = w.elita ? '#ffd24a' : w.kolor; ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.arc(w.x, ey, rr, 0, Math.PI * 2); ctx.clip(); ctx.drawImage(tw, w.x - rr, ey - rr, rr * 2, rr * 2); ctx.restore();
      ctx.font = (w.r * 0.85) + 'px sans-serif'; ctx.fillText(w.ik, w.x + rr * 0.78, ey + rr * 0.72);
    } else {
      ctx.font = (w.r * 1.7) + 'px sans-serif';
      if (w.kolor === '#9a9aaa') { ctx.filter = 'grayscale(1)'; }
      ctx.fillText(w.ik, w.x, ey);
      ctx.filter = 'none';
    }
    ctx.shadowBlur = 0;
    if (w.zauroczony > 0) { ctx.font = '12px sans-serif'; ctx.fillText(w.sojusznik ? '💀' : '💗', w.x, ey - w.r - 14); }
    if (w.spow > 0 && w.spowCzas > 0) { ctx.globalAlpha = 0.85; ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 1.6; ctx.setLineDash([3, 3]); ctx.lineDashOffset = -t / 60; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 4, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; }
    if (w.ogl > 0) { ctx.font = '10px sans-serif'; for (let s = 0; s < 3; s++) { const k = t / 200 + s * 2.1; ctx.fillText('⭐', w.x + Math.cos(k) * w.r * 0.8, ey - w.r - 2 + Math.sin(k) * 3); } }
    if (w.ogien) { ctx.font = '11px sans-serif'; ctx.fillText('🔥', w.x + w.r * 0.7, ey - w.r * 0.7); }
    if (w.krew) { ctx.font = '9px sans-serif'; ctx.fillText('🩸', w.x - w.r * 0.7, ey - w.r * 0.7); }
    if (w.naznaczony > 0) { ctx.strokeStyle = 'rgba(230,60,60,0.8)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 7, 0, Math.PI * 2); ctx.stroke(); }
    if (w.tarcza > 0) { ctx.strokeStyle = 'rgba(230,240,255,0.85)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(w.x, ey, w.r + 3, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * w.tarcza / w.tarczaMax); ctx.stroke(); }
    if (w.pole) { ctx.globalAlpha = 0.12; ctx.fillStyle = '#5aa8ff'; ctx.beginPath(); ctx.arc(w.x, w.y, 190, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 0.5; ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 2; ctx.setLineDash([9, 7]); ctx.lineDashOffset = t / 40; ctx.beginPath(); ctx.arc(w.x, w.y, 190, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1; }
    if (w.elita && (w.afIk || w.afiksy.length)) { ctx.font = '9px sans-serif'; ctx.fillText(w.afIk || w.afiksy.map(a => AFIKSY[a] ? AFIKSY[a].ik : '').join(''), w.x, ey - w.r - 15); }
    ctx.restore();
    if (!w.boss && (w.hp < w.hpMax || w.elita)) {
      const sz = w.r * 2;
      ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(w.x - sz / 2, ey - w.r - 9, sz, 4);
      ctx.fillStyle = w.zauroczony > 0 ? '#ff7ae0' : (w.elita ? '#ffb03c' : '#c0392b'); ctx.fillRect(w.x - sz / 2, ey - w.r - 9, sz * Math.max(0, w.hp / w.hpMax), 4);
    }
  }
}

function rysujGracza(g) {
  const K = KLASY[g.klasa], kol = K.kolory, rozm = g.roz || 1, hpMaxR = g.hpMaxR || 100;
  const gx = g.x, gy = g.y;
  ctx.save();
  if (g.powalony) ctx.globalAlpha = 0.45;
  else if (g.migotanie > 0 || (g.niewr > 0 && Math.floor(Date.now() / 90) % 2)) ctx.globalAlpha = 0.55;
  ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.beginPath(); ctx.ellipse(gx, gy + 11 * rozm, 12 * rozm, 4.5 * rozm, 0, 0, Math.PI * 2); ctx.fill();
  const kier = (g.kierX || 0) < -0.15 ? -1 : 1;
  const ruch = g.wRuchu ? 1 : 0;
  g.faza = (g.faza || 0) + (ruch ? 0.22 : 0);
  const krok = ruch ? Math.sin(g.faza) : 0, odd = Math.sin(Date.now() / 420) * 0.6, fal = Math.sin(Date.now() / 180) * (ruch ? 1.6 : 0.6);
  function zao(x, y, w, h, r, k) { ctx.fillStyle = k; ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); ctx.fill(); }
  ctx.translate(gx, gy + 2); ctx.scale(kier * g.r / 16 * rozm, g.r / 16 * rozm);
  const gPl = ctx.createLinearGradient(0, -6, 0, 14); gPl.addColorStop(0, kol.plaszcz[0]); gPl.addColorStop(1, kol.plaszcz[1]);
  ctx.fillStyle = gPl; ctx.beginPath(); ctx.moveTo(-7, -5); ctx.lineTo(7, -5); ctx.lineTo(9 - fal, 13); ctx.quadraticCurveTo(0, 15.5, -10 - fal, 12); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 1; ctx.stroke();
  ctx.fillStyle = kol.wlosy; ctx.beginPath(); ctx.moveTo(-8, -14); ctx.quadraticCurveTo(-11.5, -3, -8.6 - fal * 0.5, 3.5); ctx.lineTo(8.6 - fal * 0.5, 3.5); ctx.quadraticCurveTo(11.5, -3, 8, -14); ctx.closePath(); ctx.fill();
  zao(-5, 5 + Math.max(0, krok) * 1.5, 4, 8 - Math.max(0, krok) * 1.5, 1.5, '#2f3a4f'); zao(1, 5 + Math.max(0, -krok) * 1.5, 4, 8 - Math.max(0, -krok) * 1.5, 1.5, '#2f3a4f');
  zao(-6 + krok * 1.3, 11, 5.6, 3.6, 1.6, '#4a2c1a'); zao(0.4 - krok * 1.3, 11, 5.6, 3.6, 1.6, '#4a2c1a');
  const gTu = ctx.createLinearGradient(-7, -6, 7, 8); gTu.addColorStop(0, kol.tunika[0]); gTu.addColorStop(1, kol.tunika[1]);
  ctx.fillStyle = gTu; ctx.beginPath(); ctx.moveTo(-6.5, -5 + odd * 0.3); ctx.lineTo(6.5, -5 + odd * 0.3); ctx.lineTo(8.2, 7.5); ctx.lineTo(-8.2, 7.5); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.stroke();
  zao(-7.6, 1.4, 15.2, 2.7, 1, '#5a3a1e'); zao(-1.6, 1.1, 3.2, 3.3, 0.8, '#ffd24a');
  zao(-9.6, -4 - krok * 1.2, 3.4, 8, 1.6, kol.tunika[1]); zao(6.2, -4 + krok * 1.2, 3.4, 8, 1.6, kol.tunika[1]);
  ctx.fillStyle = '#efc39a'; ctx.beginPath(); ctx.arc(-7.9, 4.6 - krok * 1.2, 1.9, 0, Math.PI * 2); ctx.arc(7.9, 4.6 + krok * 1.2, 1.9, 0, Math.PI * 2); ctx.fill();
  const gGl = ctx.createRadialGradient(-2, -15, 1, 0, -13, 9); gGl.addColorStop(0, '#f6d2ae'); gGl.addColorStop(1, '#dca57c');
  ctx.fillStyle = gGl; ctx.beginPath(); ctx.arc(0, -13 + odd * 0.2, 7.6, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 0.9; ctx.stroke();
  ctx.fillStyle = kol.wlosy; ctx.beginPath(); ctx.arc(0, -14.5, 8, Math.PI * 1.02, Math.PI * 1.98); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-7.8, -14); ctx.quadraticCurveTo(-3, -9.6, 1.5, -13.6); ctx.quadraticCurveTo(4.6, -11, 7.8, -14); ctx.lineTo(7.5, -17.5); ctx.lineTo(-7.5, -17.5); ctx.closePath(); ctx.fill();
  const mrug = (Date.now() % 3800) < 120;
  ctx.fillStyle = '#1e1a16';
  if (mrug) { ctx.fillRect(-4, -11.6, 2.8, 0.9); ctx.fillRect(1.7, -11.6, 2.8, 0.9); }
  else { ctx.beginPath(); ctx.ellipse(-2.5, -11.3, 1.25, 1.65, 0, 0, Math.PI * 2); ctx.ellipse(3.1, -11.3, 1.25, 1.65, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(-2.3, -12.3, 0.7, 0.7); ctx.fillRect(3.3, -12.3, 0.7, 0.7); }
  ctx.fillStyle = 'rgba(240,120,110,0.35)'; ctx.beginPath(); ctx.arc(-4.6, -9, 1.3, 0, Math.PI * 2); ctx.arc(5.3, -9, 1.3, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#8a3a2a'; ctx.lineWidth = 0.9; ctx.beginPath(); ctx.arc(0.5, -8.7, 1.8, 0.25, Math.PI - 0.25); ctx.stroke();
  ctx.restore();
  if (g.powalony) { rysujPowalonego(g); return; }
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
  if (g.nick && (gracze.length > 1 || (typeof SIEC !== 'undefined' && SIEC.rola))) {
    ctx.font = '800 9px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineWidth = 3; ctx.strokeText(g.nick, gx, gy - 33 * rozm); ctx.fillStyle = g === lokalnyWidok() ? '#ffe08a' : '#bfe0ff'; ctx.fillText(g.nick, gx, gy - 33 * rozm);
  }
  // bronie wokół postaci
  const n = g.bronie.length;
  g.bronie.forEach((b, i) => {
    let ka = b.kat !== undefined ? b.kat : 0;
    let bx, by;
    if (n === 1) { const w = b.anim > 0 ? 20 : 13; bx = gx + Math.cos(ka) * w; by = gy + Math.sin(ka) * w; }
    else { const ks = -Math.PI / 2 + (i + 0.5) * Math.PI * 2 / n; const r = 22 * rozm; bx = gx + Math.cos(ks) * r; by = gy - 2 + Math.sin(ks) * r * 0.8;
      if (b.anim > 0) { bx += Math.cos(ka) * 7; by += Math.sin(ka) * 7; } }
    ctx.save(); ctx.translate(bx, by); ctx.rotate(ka); rysujKsztaltBroni(ctx, b); ctx.restore();
  });
  if (g.blysk > 0) {
    const p = 1 - g.blysk / 1.2;
    ctx.save(); ctx.globalAlpha = Math.max(0, g.blysk / 1.2) * 0.85; ctx.strokeStyle = '#ffe08a'; ctx.lineWidth = 4 - p * 2.6;
    ctx.beginPath(); ctx.arc(gx, gy, 16 + p * 92, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  }
}
function lokalnyWidok() { return (typeof SIEC !== 'undefined' && SIEC.rola === 'klient') ? SIEC.mojWidok : lokalny; }
function rysujPowalonego(g) {
  const t = Date.now();
  ctx.save(); ctx.font = '18px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('💀', g.x, g.y - 26);
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
      ctx.font = roz + 'px sans-serif';
      if (s.typ === 'wilk' && Math.cos(s.kat || 0) > 0) { ctx.save(); ctx.translate(s.x, s.y + bob); ctx.scale(-1, 1); ctx.fillText(s.ik, 0, 0); ctx.restore(); }
      else ctx.fillText(s.ik, s.x, s.y + bob);
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
    if (p.ksztalt === 'kula' || p.ksztalt === 'pustka' || !p.ksztalt) { ctx.globalAlpha = 0.3; ctx.beginPath(); ctx.arc(0, 0, p.ksztalt === 'pustka' ? 13 : 9, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1; }
    if (p.ksztalt === 'belt' || p.ksztalt === 'strzala') {
      ctx.rotate(k); ctx.fillStyle = '#8a6a3c'; ctx.fillRect(-11, -1.2, 18, 2.4);
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
    } else if (p.ksztalt === 'pustka') {
      ctx.beginPath(); ctx.arc(0, 0, 8, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#1a0a30'; ctx.beginPath(); ctx.arc(0, 0, 4, 0, Math.PI * 2); ctx.fill();
    } else { ctx.beginPath(); ctx.arc(0, 0, 5, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.beginPath(); ctx.arc(-1, -1, 2, 0, Math.PI * 2); ctx.fill(); }
    ctx.restore();
  });
  pociskiWrogow.forEach(p => {
    ctx.save(); ctx.translate(p.x, p.y); ctx.fillStyle = p.kolor;
    if (p.ksztalt !== 'belt' && p.ksztalt !== 'kosc') { ctx.globalAlpha = 0.28; ctx.beginPath(); ctx.arc(0, 0, (p.r || 5) + 4, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1; }
    if (p.ksztalt === 'belt') { ctx.rotate(Math.atan2(p.vy, p.vx)); ctx.fillStyle = '#8a6a3c'; ctx.fillRect(-11, -1.2, 18, 2.4); ctx.fillStyle = '#d8d8e0'; ctx.beginPath(); ctx.moveTo(11, 0); ctx.lineTo(5, -3.6); ctx.lineTo(5, 3.6); ctx.closePath(); ctx.fill(); }
    else if (p.ksztalt === 'kosc') { ctx.rotate(Date.now() / 90); ctx.fillStyle = '#e8f4ff'; ctx.fillRect(-6, -1.6, 12, 3.2); ctx.beginPath(); ctx.arc(-6, 0, 2.6, 0, Math.PI * 2); ctx.arc(6, 0, 2.6, 0, Math.PI * 2); ctx.fill(); }
    else { ctx.beginPath(); ctx.arc(0, 0, p.r || 5, 0, Math.PI * 2); ctx.fill(); if (p.siec) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(6, 0); ctx.moveTo(0, -6); ctx.lineTo(0, 6); ctx.stroke(); } }
    ctx.restore();
  });
}

function rysujEfekty() {
  const t = Date.now();
  ciecia.forEach(c => {
    const p = 1 - c.czas / c.max;
    ctx.save(); ctx.globalAlpha = (1 - p) * 0.75;
    if (c.linia) { ctx.strokeStyle = '#f0e8d0'; ctx.lineWidth = 6 * (1 - p) + 1; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(c.x + Math.cos(c.kat) * 14, c.y + Math.sin(c.kat) * 14); ctx.lineTo(c.x + Math.cos(c.kat) * c.r, c.y + Math.sin(c.kat) * c.r); ctx.stroke(); }
    else {
      const l = Math.min(c.luk, Math.PI * 2), a0 = c.kat - l / 2, a1 = a0 + l * Math.min(1, p * 1.6 + 0.2);
      ctx.fillStyle = 'rgba(255,245,220,0.22)'; ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.arc(c.x, c.y, c.r, a0, a1); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = c.kolor; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(c.x, c.y, c.r * 0.92, a0, a1); ctx.stroke();
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
  czastki.forEach(c => { ctx.globalAlpha = Math.max(0, c.czas / c.max); ctx.fillStyle = c.kolor; ctx.fillRect(c.x - 2, c.y - 2, 4, 4); });
  ctx.globalAlpha = 1;
}

function rysujTeksty() {
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  const L = USTAW.liczby;
  teksty.forEach(t => {
    if (t.o && (L === 'brak' || (L === 'wazne' && t.o === 1))) return;
    ctx.globalAlpha = Math.max(0, Math.min(1, t.czas / t.max * 1.6));
    ctx.font = '900 ' + Math.round(t.rozm * SKALA_TEKSTU) + 'px system-ui, sans-serif';
    ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineWidth = 3; ctx.strokeText(t.t, t.x, t.y); ctx.fillStyle = t.kolor; ctx.fillText(t.t, t.x, t.y);
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
    const napis = b.ik + ' ' + b.n + ' — ' + fmtK(Math.max(0, b.hpBossa !== undefined ? b.hpBossa : b.hp)); ctx.strokeText(napis, WID / 2, y + 22); ctx.fillText(napis, WID / 2, y + 22);
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
  ekranEl.innerHTML = '<div class="ekran-tresc">' + html + '</div>';
  ulozTresc(ekranEl.firstElementChild);
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
  const el = e.target.closest('[data-a]');
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
  if (rodzaj === 'bron') t.push(['oh', '🎯 każde trafienie nakłada Twoje efekty przy trafieniu']);
  else if (d.naTrafienie || /onHit(Fiz|Mag|Praw)/.test(src)) t.push(['oh', '🎯 działa przy trafieniu']);
  if (/zastosujOnHit|trafienieAtakiem/.test(src)) t.push(['oh2', '🔁 dodatkowo nakłada efekty przy trafieniu']);
  if (d.podwojnyOnHit) t.push(['oh2', '×2 wszystkie efekty przy trafieniu']);
  if (d.onHitKryt) t.push(['oh2', '🎯 krytyki nakładają efekty przy trafieniu dodatkowo']);
  if (d.naKryt) t.push(['', '💥 przy krytyku']);
  if (d.naZabicie) t.push(['', '☠️ przy zabójstwie']);
  if (d.naOtrzymanie) t.push(['', '🩹 gdy obrywasz']);
  if (d.naUniku) t.push(['', '💨 przy uniku']);
  if (d.naUmiejetnosci) t.push(['', '✨ po użyciu umiejętności']);
  if (rodzaj === 'ore') { if (d.cd) t.push(['cd', '⏱️ co ' + fmt(d.cd) + ' s (Przyspieszenie skraca)']); else if (d.co) t.push(['cd', '⚔️ co ' + d.co + '. atak broni głównej']); }
  else if (rodzaj !== 'bron' && d.cd) t.push(['cd', '⏱️ odnowienie ' + fmt(d.cd) + ' s (Przyspieszenie skraca)']);
  const sk = SKALE_TAG.filter(([w]) => src.indexOf(w) >= 0).map(([, ik]) => ik);
  if (rodzaj === 'bron') Object.keys(d.skal || {}).forEach(k => { const ik = (IKONY_SKAL[k] || k).split(' ')[0]; if (sk.indexOf(ik) < 0) sk.push(ik); });
  if (sk.length) t.push(['sk', '📈 skaluje się z: ' + sk.join(' ')]);
  return (_tagiCache[klucz] = t);
}
function htmlTagow(t) { return t.length ? '<div class="tagi">' + t.map(([k, s]) => '<span class="tag' + (k ? ' tag-' + k : '') + '">' + s + '</span>').join('') + '</div>' : ''; }
function nazwaTieruPrzedmiotu(d) { return d.t === 'p' ? '<span class="kol-p">Pryzmatyczny przedmiot</span>' : '<span class="kol-t' + d.t + '">' + TIERY[d.t].nazwa + ' przedmiot</span>'; }
function kartaPrzedmiotu(inst, dol, op) {
  op = op || {};
  const d = DEF_PRZ[inst.id], kl = d.t === 'p' ? 'tp' : 't' + d.t;
  let cd = d.cd ? '<span class="cd-tag">⏱️ ' + fmt(d.cd) + ' s</span>' : '';
  return '<div class="karta ' + kl + '">' +
    '<div class="karta-gora"><div class="karta-ik">' + d.ik + (inst.gw ? '<span class="gw">' + gwiazdki(inst.gw) + '</span>' : '') + '</div>' +
    '<div><div class="karta-nazwa">' + esc(d.n) + cd + '</div><div class="karta-tier">' + nazwaTieruPrzedmiotu(d) + (d.t === 'p' ? ' · bez ulepszeń' : '') + '</div></div></div>' +
    (d.s ? '<div class="karta-staty">' + opisStatow(d.s) + '</div>' : '') +
    (d.opis && !op.bezOpisu ? '<div class="karta-opis">' + d.opis(inst) + '</div>' + htmlTagow(tagiDef(d, 'prz')) : '') +
    (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaBroni(b, dol) {
  const B = BRONIE[b.rodzaj];
  return '<div class="karta glowna t' + b.tier + '"><div class="karta-gora"><div class="karta-ik">' + B.ikona + '</div><div><div class="karta-nazwa">' + B.nazwa + ' ' + TIERY[b.tier].rz + '</div>' +
    '<div class="karta-tier"><span class="kol-t' + b.tier + '">⭐ Broń główna · ' + TIERY[b.tier].nazwaZ + '</span> · ' + (B.dystans ? 'dystansowa' : 'wręcz') + '</div></div></div>' +
    '<div class="karta-opis">' + opisBroni(b) + '</div>' + htmlTagow(tagiDef(B, 'bron', b.rodzaj)) + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaOreza(o, dol, op) {
  op = op || {};
  const d = DEF_ORE[o.id], R = RODZINY[d.rodz];
  const cd = d.cd ? '<span class="cd-tag">⏱️ ' + fmt(d.cd) + ' s</span>' : (d.co ? '<span class="cd-tag">⚔️ co ' + d.co + '. atak</span>' : '');
  return '<div class="karta t' + o.tier + '"><div class="karta-gora"><div class="karta-ik">' + d.ik + '</div><div><div class="karta-nazwa">' + esc(d.n) + ' ' + TIERY[o.tier].rz + cd + '</div>' +
    '<div class="karta-tier"><span class="kol-t' + o.tier + '">' + TIERY[o.tier].nazwaZ + ' broń</span> · ' + R.ik + ' ' + R.n + '</div></div></div>' +
    (op.bezOpisu ? '<div class="karta-staty">' + opisStatow(statyOreza(o)) + '</div>' : opisOreza(o) + htmlTagow(tagiDef(d, 'ore'))) +
    (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaPancerza(p, dol, naglowek) {
  const d = DEF_PANC[p.id];
  return '<div class="karta t' + p.tier + '">' + (naglowek ? '<div class="sekcja" style="margin-top:0">' + naglowek + '</div>' : '') +
    '<div class="karta-gora"><div class="karta-ik">' + d.ik + '</div><div><div class="karta-nazwa">' + d.n + '</div><div class="karta-tier"><span class="kol-t' + p.tier + '">' + TIERY[p.tier].nazwa + '</span> · ' + IKONY_SLOTOW[d.slot] + ' ' + NAZWY_SLOTOW[d.slot] + '</div></div></div>' +
    '<div class="karta-staty">' + opisStatow(statyPancerza(p)) + '</div>' + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function kartaAugmentu(a, dol, inst) {
  const T = TIERY_AUG[a.r];
  inst = inst || (gracz && gracz.augmenty.find(x => x.id === a.id)) || { id: a.id, poz: 1 };
  const poz = inst.poz || 1;
  const st = statyAugmentu(inst);
  return '<div class="karta ' + T.klasa + '"><div class="karta-gora"><div class="karta-ik">' + a.ik + '</div><div><div class="karta-nazwa">' + a.n + (poz > 1 ? ' <span style="color:#ffe08a">' + rzymska(poz) + '</span>' : '') + '</div>' +
    '<div class="karta-tier" style="color:' + T.kolor + '">' + (a.r === 'p' ? '<span class="kol-p">' + T.nazwa + '</span>' : T.nazwa) + ' · poziom ' + rzymska(poz) + '/III</div></div></div>' +
    (st ? '<div class="karta-staty">' + opisStatow(st) + '</div>' : '') +
    (a.opis ? '<div class="karta-opis">' + a.opis(inst) + '</div>' : '') + htmlTagow(tagiDef(a, 'aug')) + (dol ? '<div class="karta-dol">' + dol + '</div>' : '') + '</div>';
}
function pasekGorny(tytul) {
  return '<div class="gornypasek"><div class="zloto-duze">💰 ' + Math.floor(gracz.zloto) + '</div><div style="display:flex;gap:6px">' +
    '<button class="btn-maly" data-a="modalStaty">📊 Staty</button><button class="btn-maly" data-a="modalBuild">🎒 Build</button></div></div>' +
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
    '<div style="text-align:center;font-size:60px;margin:6px 0 10px;filter:drop-shadow(0 4px 14px rgba(230,193,92,0.35))">🗝️</div>' +
    kont + '<button class="btn" data-a="nowaGra">⚔️ Nowa gra</button>' +
    '<button class="btn ziel" data-a="online">👥 Gra z przyjaciółmi (online)</button>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="kodeks">📖 Kodeks</button><button class="btn drugi" data-a="rekordy">🏆 Rekordy</button></div>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="jakGrac">❓ Jak grać</button><button class="btn drugi" data-a="dzwiek">' + (dzwiekWlaczony ? '🔊 Dźwięk' : '🔇 Bez dźwięku') + '</button></div>' +
    '<div class="rzad-btn"><button class="btn drugi" data-a="ustawienia">⚙️ Ustawienia</button><button class="btn drugi" data-a="sterowanie">🎮 Sterowanie' + (PAD.podlaczony ? ' <span class="ziel">· pad</span>' : '') + '</button></div>' +
    '<div class="podtytul" style="margin-top:18px;opacity:0.6">' + KLUCZE_KLAS.length + ' postaci · ' + KLUCZE_BRONI.length + ' broni głównych · ' + OREZE.length + ' broni dodatkowych · ' + PRZEDMIOTY.length + ' przedmiotów · ' + PRYZMATY.length + ' pryzmatycznych · ' + AUGMENTY.length + ' augmentów</div></div>');
}
// ---------------------------------------------------------------------
//  USTAWIENIA
// ---------------------------------------------------------------------
const OPCJE_USTAWIEN = [
  { k: 'uklad', n: '🖥️ Układ ekranu', o: [['auto', 'Automatyczny'], ['tel', 'Telefon'], ['pc', 'Komputer']],
    op: 'Automatyczny: na szerokim ekranie z myszką albo padem gra rozkłada się na całe okno.' },
  { k: 'interfejs', n: '🔠 Wielkość napisów', o: [[0.9, 'Mniejsze'], [1, 'Normalne'], [1.15, 'Większe']] },
  { k: 'liczby', n: '💥 Liczby obrażeń', o: [['wszystkie', 'Wszystkie'], ['wazne', 'Tylko ważne'], ['brak', 'Wyłączone']],
    op: '„Tylko ważne” — trafienia krytyczne oraz obrażenia zadane elitom i bossom.' },
  { k: 'efekty', n: '✨ Efekty', o: [['pelne', 'Pełne'], ['oszczedne', 'Oszczędne']], op: 'Oszczędne: dużo mniej iskier i odprysków — czytelniej i lżej dla słabszego sprzętu.' },
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
  h += '<button class="btn" data-a="zamknijModal">Gotowe</button>';
  pokazModal(h, zachowaj);
}
AKCJE.ustawienia = () => pokazUstawienia(false);
AKCJE.ustaw = d => {
  const O = OPCJE_USTAWIEN.find(x => x.k === d.k); if (!O) return;
  const opc = O.o.find(([v]) => String(v) === d.v); if (!opc) return;
  USTAW[d.k] = opc[0]; zapiszUstawienia();
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
function opisKlasyHtml(K) {
  const U = K.umi;
  return '<div style="font-size:16px;font-weight:900;color:#ffe08a">' + K.ik + ' ' + K.n + '</div>' + K.opis +
    (Object.keys(K.staty).length ? '<div style="margin-top:6px">' + opisStatow(K.staty) + '</div>' : '') +
    '<div style="margin-top:6px">⭐ Broń główna: <b>' + opisBroniStartowej(K) + '</b> · 🗡️ broni dodatkowych: <b>' + K.slotyOreza + '</b> · 🎒 przedmiotów: <b>' + K.slotyPrzedm + '</b> + 🔨 pryzmatów: <b>' + (K.slotyPryzm || 2) + '</b></div>' +
    '<div style="margin-top:4px">🏪 Sklep częściej daje: <b>' + opisRodzinKlasy(K) + '</b></div>' +
    (U ? '<div style="margin-top:6px;padding:7px 9px;border-radius:9px;background:rgba(255,224,138,0.08)"><b>' + U.ik + ' ' + U.n + '</b> <span class="cd-tag">⏱️ ' + U.cd + ' s</span><br>' + wKontekscie(() => U.opis(1)) + '</div>' : '');
}
function pokazPostacie() {
  const K0 = KLASY[wyborKlasy];
  let h = '<div class="tytul">Wybierz postać</div><div class="podtytul">' + TRUDNOSCI[wyborTrudnosci].ik + ' ' + TRUDNOSCI[wyborTrudnosci].n + ' · dotknij postaci, żeby zobaczyć szczegóły</div><div class="siatka3">';
  KLUCZE_KLAS.forEach(k => {
    const K = KLASY[k];
    h += '<div class="kafel' + (k === wyborKlasy ? ' wybrany' : '') + '" data-a="wybierzKlase" data-k="' + k + '"><div class="ik">' + K.ik + '</div><div class="n">' + K.n + '</div>' +
      '<div class="o">' + BRONIE_IK(K) + ' ' + (K.umi ? K.umi.ik : '') + '</div></div>';
  });
  h += '</div>';
  h += '<button class="btn" data-a="startRunu" style="margin-top:12px">⚔️ Do lochu jako ' + K0.ik + ' ' + K0.n + '</button><button class="btn drugi" data-a="nowaGraWstecz">◀ Wstecz</button>';
  pokazEkran(h, { zachowaj: true });
}
function BRONIE_IK(K) { return K.start === 'losowa' ? '🎲' : K.start === 'wybor' ? '✋' : BRONIE[K.start].ikona; }
AKCJE.wybierzKlase = d => {
  wyborKlasy = d.k; pokazPostacie();
  pokazModal('<div class="info-pole">' + opisKlasyHtml(KLASY[d.k]) + '</div><button class="btn" data-a="startRunuZModala">⚔️ Do lochu!</button><button class="btn drugi" data-a="zamknijModal">Inna postać</button>');
};
AKCJE.startRunuZModala = () => { zamknijModal(); rozpocznijRun(wyborTrudnosci, wyborKlasy); };
AKCJE.nowaGraWstecz = () => pokazTrudnosc();
AKCJE.startRunu = () => rozpocznijRun(wyborTrudnosci, wyborKlasy);

function bronStartowa(K) { return K.start === 'losowa' ? losZ(KLUCZE_BRONI) : (BRONIE[K.start] ? K.start : 'miecz'); }
function rozpocznijRun(trudnosc, klasa) {
  run = { trudnosc: trudnosc, zabici: 0, zadane: 0, przyjete: 0, leczenie: 0, zloto: 0, xp: 0, ataki: 0, trafienia: 0, zrodla: {}, zlotoFali: 0,
    start: Date.now(), falaMaks: 0, przerzutyStatow: 0 };
  gracz = nowyGracz(klasa); fala = { nr: 0, aktywna: false };
  gracz._run = run; gracz.nick = lStorGet('wiezien_nick', '') || KLASY[klasa].n; gracz.id = (typeof SIEC !== 'undefined' && SIEC.mojeId) || 0;
  gracze = [gracz]; lokalny = gracz;
  const K = KLASY[klasa];
  if (K.start !== 'wybor') gracz.bronie.push(nowaBron(bronStartowa(K), 0));
  przebudujHaki(); zastosujStaty(); gracz.hp = D.hpMax;
  if (K.dar) K.dar(gracz.stanKlasy);
  gracz.darmoweWybory += 2;
  poZmianieBuildu(); gracz.hp = D.hpMax;
  run.przerwa = { start: true, augment: 's', nr: 0 };
  stan = 'przerwa';
  ustawKamere();
  if (K.start === 'wybor') pokazWyborBroniStart(); else kolejkaPrzerwy();
  if (!lStorGet('wiezien_pomoc', false)) { lStorSet('wiezien_pomoc', true); AKCJE.jakGrac(); }
}
function pokazWyborBroniStart() {
  if (!run.ofertaBroni) run.ofertaBroni = tasuj(KLUCZE_BRONI.slice()).slice(0, 3);
  let h = '<div class="tytul">Twoja jedyna broń</div><div class="podtytul">Wybierz broń główną, z którą przejdziesz cały loch. Zaczyna na II tierze.</div>';
  run.ofertaBroni.forEach(r => { h += wKontekscie(() => kartaBroni({ rodzaj: r, tier: 1 }, '<button class="btn-maly zl" data-a="bronStart" data-r="' + r + '">Wybieram</button>')); });
  pokazEkran(h);
}
AKCJE.bronStart = d => { gracz.bronie = [nowaBron(d.r, 1)]; run.ofertaBroni = null; poZmianieBuildu(); DZ.wybor(); kolejkaPrzerwy(); };

AKCJE.jakGrac = () => pokazModal('<div class="tytul">❓ Jak grać</div><div class="info-pole">' +
  '<b>Ruch:</b> na telefonie przeciągnij palcem po dolnym pasku (drążek pojawi się pod palcem). Na komputerze <b>WASD</b> / strzałki albo przytrzymaj <b>lewy przycisk myszy</b> — postać idzie w stronę kursora. Atakujesz <b>automatycznie</b>.<br>' +
  '<b>✨ Umiejętność:</b> każda postać ma swoją — przycisk po prawej, na komputerze <b>E</b>, spacja albo <b>prawy przycisk myszy</b> (w stronę kursora). Mikstura: <b>Q</b>, pauza: <b>Esc</b>. Odnawia się szybciej z Przyspieszeniem.<br>' +
  '<b>🎮 Pad:</b> podłącz kontroler (kabel albo Bluetooth) i naciśnij dowolny przycisk — gra przełączy się na sterowanie padem. Szczegóły w menu „Pad i klawiatura”.<br>' +
  '<b>⭐ Broń główna</b> to Twoja broń z klasy — to ona atakuje. Ulepszasz ją w sklepie (tiery I–V). Skaluje się od kilku statystyk naraz.<br>' +
  '<b>🗡️ Bronie dodatkowe</b> (jak przedmioty w LoL-u) dają <b>statystyki</b> broni głównej i co kilka sekund albo co N-ty atak same coś odpalają. Dwie takie same o tym samym tierze łączą się w wyższy. Ta sama rodzina co broń główna daje <b>premię zestawu</b>.<br>' +
  '<b>🎒 Przedmioty</b> nie dają statystyk — mają pasywki: działka, krzaki z leczącymi owocami, pszczoły, miny... Ulepszasz je gwiazdkami ★.<br>' +
  '<b>🛡️ Pancerz</b> (4 części) daje statystyki obronne. Pryzmaty — tylko z Pryzmatycznego Kowadła, bez ulepszania.<br>' +
  '<b>🧬 Augmenty</b> (szare, złote, pryzmatyczne) ulepszasz w sklepie do poziomu III.<br>' +
  '<b>Sprzedaż:</b> wszystko sprzedasz w sklepie albo w 🎒 Build między falami.<br>' +
  '<b>🎯 Przy trafieniu (on-hit):</b> każde trafienie bronią główną nakłada Twoje efekty „przy trafieniu” (obrażenia przy trafieniu i przedmioty z tym znacznikiem). Znacznik 🔁 / ×2 oznacza, że coś nakłada je <b>dodatkowe razy</b>. 📈 pokazuje, od czego efekt rośnie.<br>' +
  '<b>Miejsca:</b> przedmioty zwykłe i pryzmatyczne mają osobne miejsca (np. 4 + 2).<br>' +
  '<b>⚒️ Kowadło statystyk</b> w sklepie: czyste statystyki za złoto (wybierasz 1 z 3). Każde kolejne w tym samym sklepie jest droższe.<br>' +
  '<b>Drużyna:</b> złoto i doświadczenie są wspólne — każdy dostaje pełną wartość tego, co ktokolwiek podniesie, a potem działają <b>jego własne</b> premie (zysk złota, doświadczenie, Midas…).<br>' +
  '<b>🦇 Wampiryzm</b> (kradzież życia i wszechwampiryzm) leczy najwyżej 2–8% zdrowia na sekundę. Od 11. fali działa <b>🥀 zmęczenie</b>: leczenie słabnie o 2,5% z każdą falą (mikstury nie).<br>' +
  '<b>Fale:</b> przetrwaj do końca czasu. Co 5. fala to <b>boss</b>. Złoto i doświadczenie, których nie zbierzesz, same zbierają się po fali.<br>' +
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
  o.ids.forEach(id => { h += kartaAugmentu(DEF_AUG[id], '<button class="btn-maly zl" data-a="augWybierz" data-id="' + id + '" style="margin-left:auto">Wybieram</button>', { id: id, poz: 1 }); });
  if (!o.ids.length) h += '<div class="slot-pusty">Brak dostępnych augmentów tego rodzaju — dostajesz 50 złota.</div><button class="btn" data-a="augPomin">Dalej</button>';
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
function losTierStatu(min) {
  const L = 1 + D.szczescie / 100, lv = gracz.poziom;
  const p3 = Math.min(0.1, 0.004 * lv) * L, p2 = Math.min(0.28, 0.012 * lv) * L, p1 = Math.min(0.5, 0.12 + 0.02 * lv) * L;
  const r = Math.random(); let t = r < p3 ? 3 : r < p3 + p2 ? 2 : r < p3 + p2 + p1 ? 1 : 0;
  return Math.max(min || 0, t);
}
function losujOpcjeStatow(min) {
  let pula = ULEPSZENIA_STATOW.filter(u => !(gracz.klasa === 'wampirzyca' && u.k === 'regen'));
  return tasuj(pula.slice()).slice(0, 4).map(u => { const t = losTierStatu(min); return { k: u.k, t: t, v: u.w[t] }; });
}
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
  h += '</div><button class="btn drugi" data-a="statPrzerzuc" style="margin-top:12px"' + (gracz.zloto >= kosztPrzerzutuStatow() ? '' : ' disabled') + '>🎲 Przerzuć (' + kosztPrzerzutuStatow() + ' 💰)</button>';
  pokazEkran(h);
}
AKCJE.statWybierz = d => {
  const o = run.opcjeStatow[+d.i]; if (!o) return;
  gracz.ulepszenia[o.k] = (gracz.ulepszenia[o.k] || 0) + o.v;
  if (run.opcjeDarmowe) gracz.darmoweWybory--; else gracz.doWyboru--;
  run.opcjeStatow = null; poZmianieBuildu(); DZ.wybor();
  kolejkaPrzerwy();
};
AKCJE.statPrzerzuc = () => { const k = kosztPrzerzutuStatow(); if (gracz.zloto < k) return; gracz.zloto -= k; run.przerzutyStatow++; run.opcjeStatow = losujOpcjeStatow(run.opcjeDarmowe ? 1 : 0); pokazWyborStatow(run.opcjeDarmowe); };

// ---------------------------------------------------------------------
//  SKRZYNIE
// ---------------------------------------------------------------------
function losujIdOreza() {
  const K = KLASY[gracz.klasa];
  let pula = OREZE;
  if (K.rodziny && Math.random() < 0.75) pula = OREZE.filter(o => K.rodziny.indexOf(o.rodz) >= 0);
  return losZ(pula).id;
}
function generujZawartosc(s) {
  const nr = Math.max(1, fala.nr), t = s.tier;
  if (s.boss) {
    const r = Math.random();
    if (r < 0.3 && gracz.bronie.some(b => b.tier < MAKS_TIER_BRONI)) return { r: 'kamien' };
    return r < 0.65 ? { r: 'oreze', o: nowyOrez(losujIdOreza(), t) } : { r: 'pancerz', p: nowyPancerz(losZ(PANCERZE).id, t) };
  }
  const r = Math.random();
  if (r < 0.12) return { r: 'zloto', ile: Math.round((15 + 5 * nr) * (1 + t * 0.7)) };
  if (r < 0.2 && gracz.mikstury < gracz.maksMikstur) return { r: 'mikstura' };
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
  else if (z.r === 'mikstura') h += '<div class="karta t1" style="text-align:center"><div style="font-size:44px">🧪</div><div class="karta-nazwa">Mikstura zdrowia</div><div class="karta-opis">Leczy ' + Math.round(40 * gracz.mocMikstur) + '% maks. zdrowia.</div></div><button class="btn" data-a="skrzMikstura">Weź</button>';
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
  pokazEkran(h);
}
function nastepnaSkrzynia() { gracz.skrzynie.shift(); run.zawSkrzyni = null; poZmianieBuildu(); kolejkaPrzerwy(); }
AKCJE.skrzZloto = () => { gracz.zloto += run.zawSkrzyni.ile; DZ.moneta(); nastepnaSkrzynia(); };
AKCJE.skrzMikstura = () => { gracz.mikstury = Math.min(gracz.maksMikstur, gracz.mikstury + 1); nastepnaSkrzynia(); };
AKCJE.skrzKamien = () => { const b = gracz.bronie.find(x => x.tier < MAKS_TIER_BRONI); if (b) { b.tier++; toast('💎 ' + nazwaBroni(b)); DZ.pryzmat(); } nastepnaSkrzynia(); };
AKCJE.skrzZaloz = () => { const p = run.zawSkrzyni.p, slot = DEF_PANC[p.id].slot, ob = gracz.pancerz[slot]; if (ob) gracz.zloto += Math.round(cenaPancerza(ob) * 0.5); gracz.pancerz[slot] = p; DZ.zakup(); nastepnaSkrzynia(); };
AKCJE.skrzSprzedaj = () => { const z = run.zawSkrzyni; gracz.zloto += z.r === 'pancerz' ? Math.round(cenaPancerza(z.p) * 0.5) : wartoscSprzedazyOreza(z.o); DZ.moneta(); nastepnaSkrzynia(); };
AKCJE.skrzPolacz = () => { const z = run.zawSkrzyni, para = paraOreza(z.o); if (para) { para.tier++; toast('⬆️ ' + nazwaOreza(para)); DZ.wybor(); } nastepnaSkrzynia(); };
AKCJE.skrzWezOreze = () => { gracz.oreze.push(run.zawSkrzyni.o); DZ.zakup(); nastepnaSkrzynia(); };
AKCJE.skrzZamienOreze = () => wyborZamianyOreza(run.zawSkrzyni.o, () => nastepnaSkrzynia());

function wyborZamianyOreza(nowa, potem) {
  run.oczekOre = { o: nowa, potem: potem };
  let h = '<div class="tytul">Którą broń zamienić?</div><div class="podtytul">Wymieniona broń zostanie sprzedana.</div>';
  gracz.oreze.forEach((o, i) => { h += kartaOreza(o, '<button class="btn-maly zl" data-a="zamienOreze" data-i="' + i + '" style="margin-left:auto">Zamień (+' + wartoscSprzedazyOreza(o) + ' 💰)</button>', { bezOpisu: true }); });
  h += '<button class="btn drugi" data-a="zamknijModal">Anuluj</button>';
  pokazModal(h);
}
AKCJE.zamienOreze = d => { const o = run.oczekOre, i = +d.i, st = gracz.oreze[i]; if (!o || !st) return; gracz.zloto += wartoscSprzedazyOreza(st); gracz.oreze[i] = o.o; run.oczekOre = null; zamknijModal(); poZmianieBuildu(); DZ.zakup(); o.potem(); };

// dodanie przedmiotu, gdy brak miejsca - wybór, co sprzedać
function dodajPrzedmiotZWyborem(inst, potem) {
  const pr = czyPryzmat(inst);
  if (wolneSlotyPrzedm(pr) > 0) { gracz.przedmioty = gracz.przedmioty.filter(p => p); gracz.przedmioty.push(inst); poZmianieBuildu(); potem(); return; }
  run.oczekPrz = { inst: inst, potem: potem };
  let h = '<div class="tytul">Brak miejsca</div><div class="podtytul">Sprzedaj jeden ' + (pr ? 'przedmiot <b>pryzmatyczny</b>' : 'zwykły przedmiot') + ', żeby zrobić miejsce na <b>' + DEF_PRZ[inst.id].ik + ' ' + DEF_PRZ[inst.id].n + '</b>.</div>';
  gracz.przedmioty.forEach((p, i) => { if (p && czyPryzmat(p) === pr) h += kartaPrzedmiotu(p, '<button class="btn-maly czerw" data-a="zamienPrz" data-i="' + i + '" style="margin-left:auto">Sprzedaj (+' + wartoscSprzedazy(p) + ' 💰)</button>', { bezOpisu: true }); });
  h += '<button class="btn drugi" data-a="porzucPrz">Zrezygnuj z nowego (+' + wartoscSprzedazy(inst) + ' 💰)</button>';
  modalEl.dataset.wymuszony = '1';
  pokazModal(h);
}
AKCJE.zamienPrz = d => { const o = run.oczekPrz, i = +d.i; gracz.zloto += wartoscSprzedazy(gracz.przedmioty[i]); cofnijPrzedmiot(gracz.przedmioty[i]); gracz.przedmioty[i] = o.inst; run.oczekPrz = null; delete modalEl.dataset.wymuszony; zamknijModal(); poZmianieBuildu(); DZ.zakup(); o.potem(); };
AKCJE.porzucPrz = () => { const o = run.oczekPrz; gracz.zloto += wartoscSprzedazy(o.inst); run.oczekPrz = null; delete modalEl.dataset.wymuszony; zamknijModal(); poZmianieBuildu(); o.potem(); };

// ---------------------------------------------------------------------
//  KOWADŁO PRYZMATYCZNE
// ---------------------------------------------------------------------
function pokazKowadlo() {
  if (!run.ofertaKow) run.ofertaKow = tasuj(PRYZMATY.filter(p => !maPrzedmiot(p.id)).map(p => p.id)).slice(0, 3);
  let h = pasekGorny() + '<div class="tytul">🔨 <span class="kol-p">Pryzmatyczne Kowadło</span></div><div class="podtytul">Wybierz jeden przedmiot pryzmatyczny. Miejsca na pryzmaty: <b>' + liczPrzedm(true) + '/' + slotyTypu(true) + '</b></div>';
  run.ofertaKow.forEach(id => { h += kartaPrzedmiotu(nowyPrzedmiot(id), '<button class="btn-maly zl" data-a="kowWybierz" data-id="' + id + '" style="margin-left:auto">Wybieram</button>'); });
  if (!run.przerzutKow) h += '<button class="btn drugi" data-a="kowPrzerzuc">🎲 Przerzuć (raz, za darmo)</button>';
  h += '<button class="btn drugi" data-a="kowPomin">Odrzuć kowadło (+60 💰)</button>';
  pokazEkran(h);
}
AKCJE.kowWybierz = d => { gracz.kowadla--; run.ofertaKow = null; run.przerzutKow = false; DZ.pryzmat(); dodajPrzedmiotZWyborem(nowyPrzedmiot(d.id), () => { const def = DEF_PRZ[d.id]; if (def.natychmiast) { try { def.natychmiast(); } catch (e) { zglosBlad(e, 'pryzmat natychmiast'); } poZmianieBuildu(); } kolejkaPrzerwy(); }); };
AKCJE.kowPrzerzuc = () => { run.przerzutKow = true; const st = run.ofertaKow; run.ofertaKow = tasuj(PRYZMATY.filter(p => !maPrzedmiot(p.id) && st.indexOf(p.id) < 0).map(p => p.id)).slice(0, 3); if (run.ofertaKow.length < 3) run.ofertaKow = st; pokazKowadlo(); };
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
  const r = Math.random(), szansaOreza = gracz.slotyOreza <= 2 ? 0.25 : 0.42;
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
function pokazSklep(zachowaj) {
  const sk = run.sklep, nr = fala.nr;
  let h = pasekGorny() + '<div class="tytul">🛒 Sklep</div><div class="podtytul">Przed falą <b>' + (nr + 1) + '</b>' + (czyFalaBossa(nr + 1) ? ' — <span class="czer">BOSS!</span>' : '') + '</div>';
  h += '<button class="btn" data-a="dalejZeSklepu">▶ Fala ' + (nr + 1) + '</button>';
  const kp = sk.darmowe > 0 ? 0 : kosztPrzerzutuSklepu();
  h += '<div class="rzad-btn" style="margin:6px 0 10px"><button class="btn-maly" data-a="przerzucSklep"' + (gracz.zloto >= kp ? '' : ' disabled') + '>🎲 Przerzuć ' + (kp ? '(' + kp + ' 💰)' : '(za darmo)') + '</button>' +
    '<button class="btn-maly" data-a="kupMiksture"' + (gracz.mikstury < gracz.maksMikstur && gracz.zloto >= cenaMikstury() ? '' : ' disabled') + '>🧪 Mikstura (' + cenaMikstury() + ' 💰) ' + gracz.mikstury + '/' + gracz.maksMikstur + '</button></div>';
  const ck = cenaKowadlaStatow();
  h += '<button class="btn-maly zl kowadlo-statow" data-a="kowadloStatow"' + (gracz.zloto >= ck ? '' : ' disabled') + '>⚒️ Kowadło statystyk — ' + ck + ' 💰 <span style="font-weight:700;opacity:0.75">· czyste statystyki do wyboru</span></button>';
  sk.oferty.forEach((o, i) => {
    if (o.kupiona) { h += '<div class="slot-pusty">Kupione ✔</div>'; return; }
    const cena = cenaOferty(o), stac = gracz.zloto >= cena;
    const dol = '<span class="cena"' + (stac ? '' : ' style="color:#a05a4a"') + '>' + cena + ' 💰</span><button class="btn-maly" data-a="zablokuj" data-i="' + i + '">' + (o.zabl ? '🔒' : '🔓') + '</button><button class="btn-maly zl" data-a="kup" data-i="' + i + '"' + (stac ? '' : ' disabled') + '>Kup</button>';
    if (o.rodzaj === 'kowadlo') h += '<div class="karta tp"><div class="karta-gora"><div class="karta-ik">🔨</div><div><div class="karta-nazwa">Pryzmatyczne Kowadło</div><div class="karta-tier"><span class="kol-p">Wybór przedmiotu pryzmatycznego</span></div></div></div><div class="karta-opis">Po zakupie wybierasz jeden z 3 przedmiotów pryzmatycznych.</div><div class="karta-dol">' + dol + '</div></div>';
    else if (o.rodzaj === 'oreze') h += kartaOreza(o.o, (paraOreza(o.o) ? '<span class="tag" style="background:rgba(126,201,138,0.2);color:#7ec98a">⬆️ połączy się</span>' : '') + dol);
    else if (o.rodzaj === 'pancerz') { const ob = gracz.pancerz[DEF_PANC[o.p.id].slot]; h += kartaPancerza(o.p, (ob ? '<span class="tag">zamieni: ' + DEF_PANC[ob.id].ik + ' ' + TIERY[ob.tier].rz + '</span>' : '') + dol); }
    else h += kartaPrzedmiotu(nowyPrzedmiot(o.id), dol);
  });
  h += sekcjeBuildu(true);
  h += '<button class="btn" data-a="dalejZeSklepu" style="margin-top:14px">▶ Fala ' + (nr + 1) + '</button>';
  pokazEkran(h, { zachowaj: zachowaj });
}
function cenaMikstury() { return Math.round(12 * mnCeny()); }

// ---------------------------------------------------------------------
//  KOWADŁO STATYSTYK — czyste statystyki za złoto (jak kowadła w Arenie LoL-a).
//  Kupujesz ile chcesz, ale w jednym sklepie każde kolejne jest droższe o 60%.
// ---------------------------------------------------------------------
function cenaKowadlaStatow() { const k = (run.sklep && run.sklep.kowStat) || 0; return Math.round(40 * mnCeny() * (1 + 0.6 * k)); }
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
AKCJE.kupMiksture = () => { const c = cenaMikstury(); if (gracz.zloto < c || gracz.mikstury >= gracz.maksMikstur) return; gracz.zloto -= c; gracz.mikstury++; DZ.zakup(); pokazSklep(true); };
AKCJE.przerzucSklep = () => {
  const sk = run.sklep; let k = 0;
  if (sk.darmowe > 0) sk.darmowe--; else { k = kosztPrzerzutuSklepu(); if (gracz.zloto < k) return; sk.przerzuty++; }
  gracz.zloto -= k;
  const nowe = sk.oferty.filter(o => o.zabl && !o.kupiona);
  while (nowe.length < 5) nowe.push(losujOferte(nowe));
  sk.oferty = nowe; DZ.klik(); pokazSklep(true);
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
  const inst = nowyPrzedmiot(o.id);
  gracz.zloto -= cena; o.kupiona = true;
  dodajPrzedmiotZWyborem(inst, () => { DZ.zakup(); pokazSklep(true); });
};
function pokazKowadloZeSklepu() { run.przerwa.wrocDoSklepu = true; pokazKowadlo(); }
AKCJE.dalejZeSklepu = () => { run.przerwa.sklep = true; zapiszGre(); kolejkaPrzerwy(); };
// ---- zarządzanie buildem: ulepszanie i sprzedaż (sklep i 🎒 Build między falami) ----
AKCJE.ulepszPrz = d => { const p = gracz.przedmioty[+d.i]; if (!p || DEF_PRZ[p.id].t === 'p' || (p.gw || 0) >= MAKS_GWIAZDEK) return; const c = cenaUlepszenia(p); if (gracz.zloto < c) return; gracz.zloto -= c; p.gw = (p.gw || 0) + 1; poZmianieBuildu(); DZ.wybor(); odswiezEkranPrzerwy(); };
AKCJE.sprzedajPrz = d => { const i = +d.i, p = gracz.przedmioty[i]; if (!p) return; if (d.pewne) { run._zBuildu = !!modalEl.dataset.zBuildu; AKCJE.sprzedajPrzTak(d); return; } run._zBuildu = !!modalEl.dataset.build; pokazModal('<div class="tytul">Sprzedać?</div>' + kartaPrzedmiotu(p, '', { bezOpisu: true }) + '<button class="btn czerw" data-a="sprzedajPrzTak" data-i="' + i + '">Sprzedaj za ' + wartoscSprzedazy(p) + ' 💰</button><button class="btn drugi" data-a="zamknijModal">Anuluj</button>'); };
AKCJE.sprzedajPrzTak = d => { const i = +d.i, p = gracz.przedmioty[i]; if (!p) return; gracz.zloto += wartoscSprzedazy(p); cofnijPrzedmiot(p); gracz.przedmioty.splice(i, 1); zamknijModal(); poZmianieBuildu(); DZ.moneta(); toast('💰 Sprzedano'); if (run._zBuildu) { run._zBuildu = false; AKCJE.modalBuild(); } odswiezEkranPrzerwy(); };
AKCJE.zamknijModal = () => { const zb = run && run._zBuildu; if (run) run._zBuildu = false; zamknijModal(); if (zb) AKCJE.modalBuild(); };
function cofnijPrzedmiot(p) { const d = p && DEF_PRZ[p.id]; if (d && d.cofnij) { try { d.cofnij(); } catch (e) { zglosBlad(e, 'cofnij ' + p.id); } } }
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
function sekcjeBuildu(zarzadzanie) {
  const z = gracz.zloto;
  let h = chipyStatow();
  // broń główna — szeroki kafelek
  h += '<div class="sekcja">⭐ Broń główna</div>';
  gracz.bronie.forEach((b, i) => {
    const B = BRONIE[b.rodzaj];
    const mozna = zarzadzanie && b.tier < MAKS_TIER_BRONI && z >= cenaUlepszeniaBroniGl(b);
    h += '<div class="kfl szeroki" data-a="szczegol" data-r="glowna" data-i="' + i + '" style="--kol:' + TIERY[b.tier].kolor + '"><div class="kfl-ik">' + B.ikona + (mozna ? '<span class="kfl-odz">⬆</span>' : '') + '</div>' +
      '<div style="flex:1;min-width:0"><div class="kfl-n" style="text-align:left;font-size:13px">' + B.nazwa + ' ' + TIERY[b.tier].rz + '</div>' +
      '<div class="kfl-op">' + f0(obrBroni(b)) + ' obrażeń na trafienie · co ' + fmt(odstepAtaku(b)) + ' s · ' + opisSkalowania(B) + '</div></div></div>';
  });
  // bronie dodatkowe
  const zest = policzZestawy(), akt = Object.keys(zest).filter(t => zest[t] >= 2);
  h += '<div class="sekcja">🗡️ Bronie dodatkowe <span class="licz">' + gracz.oreze.length + '/' + gracz.slotyOreza + '</span></div><div class="kafelki">';
  gracz.oreze.forEach((o, i) => {
    const d = DEF_ORE[o.id], mozna = zarzadzanie && (paraOreza(o) || (o.tier < 3 && z >= cenaUlepszeniaOreza(o)));
    h += kafelek('oreze', i, d.ik, d.n + ' ' + TIERY[o.tier].rz, TIERY[o.tier].kolor, '', d.cd ? fmt(d.cd) + 's' : (d.co ? '×' + d.co : ''), mozna ? '⬆' : '');
  });
  for (let i = gracz.oreze.length; i < gracz.slotyOreza; i++) h += kafelekPusty('wolne');
  h += '</div>';
  if (akt.length) h += '<div class="chipy">' + akt.map(t => { const R = RODZINY[t]; return '<span class="chip">' + R.ik + ' ' + R.n + ' ×' + zest[t] + ': ' + opisStatow(R.staty(poziomZestawu(zest[t]))).replace(/<br>/g, ', ') + '</span>'; }).join('') + '</div>';
  // przedmioty zwykłe i pryzmatyczne — osobne miejsca
  [[false, '🎒 Przedmioty'], [true, '🔨 Pryzmaty']].forEach(([pr, tyt]) => {
    h += '<div class="sekcja">' + tyt + ' <span class="licz">' + liczPrzedm(pr) + '/' + slotyTypu(pr) + '</span></div><div class="kafelki">';
    gracz.przedmioty.forEach((p, i) => {
      if (!p || czyPryzmat(p) !== pr) return;
      const d = DEF_PRZ[p.id], mozna = zarzadzanie && !pr && (p.gw || 0) < MAKS_GWIAZDEK && z >= cenaUlepszenia(p);
      h += kafelek('przedm', i, d.ik, d.n, pr ? KOLOR_PRYZMAT : TIERY[d.t].kolor, p.gw ? '★'.repeat(p.gw) : '', d.cd ? fmt(d.cd) + 's' : '', mozna ? '⬆' : '', pr ? 'pryzm' : '');
    });
    for (let i = liczPrzedm(pr); i < slotyTypu(pr); i++) h += kafelekPusty(pr ? 'z kowadła' : 'wolne');
    h += '</div>';
  });
  // pancerz
  h += '<div class="sekcja">🛡️ Pancerz</div><div class="kafelki">';
  SLOTY_PANCERZA.forEach(sl => {
    const p = gracz.pancerz[sl];
    if (p) { const d = DEF_PANC[p.id]; h += kafelek('panc', sl, d.ik, d.n, TIERY[p.tier].kolor, TIERY[p.tier].rz, '', ''); }
    else h += kafelekPusty(IKONY_SLOTOW[sl] + ' ' + NAZWY_SLOTOW[sl]);
  });
  h += '</div>';
  // augmenty
  h += '<div class="sekcja">🧬 Augmenty <span class="licz">' + gracz.augmenty.length + '</span></div><div class="kafelki">';
  if (!gracz.augmenty.length) h += kafelekPusty('brak');
  gracz.augmenty.forEach((a, i) => {
    const d = DEF_AUG[a.id], T = TIERY_AUG[d.r], mozna = zarzadzanie && (a.poz || 1) < MAKS_POZ_AUG && z >= cenaUlepszeniaAug(a);
    h += kafelek('aug', i, d.ik, d.n, d.r === 'p' ? KOLOR_PRYZMAT : T.kolor, rzymska(a.poz || 1), '', mozna ? '⬆' : '', d.r === 'p' ? 'pryzm' : '');
  });
  h += '</div><div class="podtytul" style="margin-top:6px;font-size:11px">Dotknij kafelka, żeby zobaczyć opis' + (zarzadzanie ? ', ulepszyć albo sprzedać. ⬆ = stać Cię na ulepszenie.' : '.') + '</div>';
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
      if (!czyPryzmat(el) && (el.gw || 0) < MAKS_GWIAZDEK) { const c = cenaUlepszenia(el); dol += bt('ulepszPrz', '★ Ulepsz (' + c + ' 💰)', 'zl', z >= c); }
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
    h += '<div class="karta az"><div class="karta-gora"><div class="karta-ik">' + p.ik + '</div><div><div class="karta-nazwa">' + p.n + '</div></div></div>' +
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
  const grupy = { atak: '⚔️ Atak', obrona: '🛡️ Obrona', onhit: '🎯 Przy trafieniu', uzyt: '🧰 Użytkowe' };
  Object.keys(grupy).forEach(g => {
    h += '<div class="sekcja">' + grupy[g] + '</div>';
    DEF_STATOW.filter(d => d.g === g).forEach(d => {
      const v = D[d.k], zero = Math.abs(v) < 0.001 && !d.baza;
      h += '<div class="wiersz-stat" data-a="opisStatu" data-k="' + d.k + '"><span class="ik">' + d.i + '</span><span class="n">' + d.n + '</span><span class="v' + (zero ? ' zero' : '') + '">' + wartoscStatuTekst(d.k, v) + '</span></div>';
    });
  });
  h += '<div class="info-pole">Zdrowie: <b>' + Math.round(gracz.hp) + ' / ' + D.hpMax + '</b> · Poziom <b>' + gracz.poziom + '</b> · Mikstury <b>' + gracz.mikstury + '/' + gracz.maksMikstur + '</b><br>Redukcja: fizyczne <b>−' + Math.round(100 - 100 * 100 / (100 + Math.max(0, D.pancerz))) + '%</b>, magiczne <b>−' + Math.round(100 - 100 * 100 / (100 + Math.max(0, D.odpMag))) + '%</b>' +
    '<br>🦇 Limit wampiryzmu: <b>' + fmt(limitWampiryzmu() * 100) + '% zdrowia/s</b> (' + Math.round(limitWampiryzmu() * D.hpMax) + '/s)' +
    (zmeczenie(fala.nr) > 0 ? '<br>🥀 Zmęczenie: leczenie <b>−' + Math.round(zmeczenie(fala.nr) * 100) + '%</b> (mikstury bez zmian)' : '') + '</div>';
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
  h += '<div class="zakladki">' + [['staty', '📊 Staty'], ['build', '🎒 Build'], ['obr', '💥 Obrażenia']].map(z => '<button class="' + (z[0] === ekwZakladka ? 'akt' : '') + '" data-a="ekwZak" data-z="' + z[0] + '">' + z[1] + '</button>').join('') + '</div>';
  if (ekwZakladka === 'staty') h += htmlStatow();
  else if (ekwZakladka === 'build') h += sekcjeBuildu(false);
  else h += htmlObrazen();
  h += '<div class="rzad-btn" style="margin-top:16px"><button class="btn drugi" data-a="ustawienia">⚙️ Ustawienia</button><button class="btn drugi" data-a="sterowanie">🎮 Sterowanie</button></div>';
  if (!druzyna()) h += '<button class="btn czerw" data-a="poddaj" style="margin-top:6px">🏳️ Zakończ tę grę</button>';
  else h += '<button class="btn czerw" data-a="opuscDruzyne" style="margin-top:6px">🚪 Opuść drużynę</button>';
  pokazEkran(h, { polprzezroczysty: true });
}
AKCJE.ekwZak = d => pokazEkwipunek(d.z);
AKCJE.wznow = () => { zamknijEkran(); if (stan === 'pauza') stan = 'walka'; czasOstatni = null; };
AKCJE.poddaj = () => pokazModal('<div class="tytul">Zakończyć grę?</div><div class="podtytul">Twój wynik zostanie zapisany, a zapis gry usunięty.</div><button class="btn czerw" data-a="poddajTak">Tak, kończę</button><button class="btn drugi" data-a="zamknijModal">Graj dalej</button>');
AKCJE.poddajTak = () => { zamknijModal(); zamknijEkran(); stan = 'walka'; smiercGracza(true); };
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
$('btnMikstura').addEventListener('click', () => wypijMiksture());
$('btnUmi').addEventListener('click', () => uzyjUmiejetnosci());

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
  $('licznikMikstur').textContent = gracz.mikstury;
  $('miksturaCd').style.setProperty('--p', (gracz.cdMikstury > 0 ? gracz.cdMikstury / 2 * 100 : 0) + '%');
  // umiejętność postaci
  const U = KLASY[gracz.klasa].umi, bu = $('btnUmi');
  if (U && bu) {
    if (bu._k !== gracz.klasa) { bu._k = gracz.klasa; $('umiIk').textContent = U.ik; }
    const u = gracz.umi || { cd: 0, cdMax: 1 }, gotowa = !(u.cd > 0);
    $('umiCd').style.setProperty('--p', (gotowa ? 0 : Math.min(100, u.cd / Math.max(0.1, u.cdMax) * 100)) + '%');
    $('umiCzas').textContent = gotowa ? '' : Math.ceil(u.cd);
    bu.classList.toggle('gotowa', gotowa && !gracz.powalony);
  }
  // pasek broni dodatkowych i przedmiotów z odnowieniem
  const pasek = $('pasekPrzedm');
  const elem = gracz.oreze.map(o => ({ i: o, d: DEF_ORE[o.id], kol: TIERY[o.tier].kolor, st: '' }))
    .concat(gracz.przedmioty.filter(p => p).map(p => { const d = DEF_PRZ[p.id]; return { i: p, d: d, kol: d.t === 'p' ? KOLOR_PRYZMAT : TIERY[d.t].kolor, st: p.gw ? p.gw + '★' : '' }; }));
  const sygn = elem.map(e => e.d.id + (e.i.tier || 0) + (e.i.gw || 0)).join(',');
  if (pasek._sygn !== sygn) {
    pasek._sygn = sygn;
    pasek.innerHTML = elem.map(e => '<div class="hud-slot" title="' + esc(e.d.n) + (e.d.cd ? ' · ⏱️ ' + fmt(e.d.cd) + ' s' : '') + '" style="border-color:' + e.kol + '">' + e.d.ik + '<div class="cd"></div><div class="cdn"></div>' + (e.st ? '<span class="st">' + e.st + '</span>' : '') + '</div>').join('');
  }
  const sloty = pasek.children;
  elem.forEach((e, i) => {
    const el = sloty[i]; if (!el) return;
    const p = e.i, proc = p.cd > 0 && p.cdMax ? p.cd / p.cdMax * 100 : 0;
    el.children[0].style.setProperty('--p', proc + '%');
    el.children[1].textContent = p.cd > 0.95 ? Math.ceil(p.cd) : '';
    el.classList.toggle('gotowy', !!e.d.cd && !(p.cd > 0));
  });
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
    lStorSet('wiezien_zapis', { wersja: 2, czas: Date.now(), gracz: g, run: r, falaNr: fala.nr || 0, wznowFale: wznowFale || 0 });
  } catch (e) { zglosBlad(e, 'zapis'); }
}
function wczytajGre() {
  const z = lStorGet('wiezien_zapis', null);
  if (!z || !z.gracz || !z.run || z.wersja !== 2 || !KLASY[z.gracz.klasa]) return false;
  try {
    run = z.run; run.zrodla = run.zrodla || {};
    gracz = nowyGracz(z.gracz.klasa); Object.assign(gracz, z.gracz); gracz._run = run; gracze = [gracz]; lokalny = gracz;
    gracz.tarcze = []; gracz.buffy = {}; gracz.martwy = false; gracz.augmentyDoWyboru = gracz.augmentyDoWyboru || [];
    gracz.przedmioty = (gracz.przedmioty || []).filter(p => p && DEF_PRZ[p.id]);
    gracz.augmenty = (gracz.augmenty || []).filter(a => a && DEF_AUG[a.id]);
    gracz.oreze = (gracz.oreze || []).filter(o => o && DEF_ORE[o.id]).map(o => Object.assign(o, { ore: 1 }));
    gracz.bronie = (gracz.bronie || []).filter(b => b && BRONIE[b.rodzaj]); if (!gracz.bronie.length) gracz.bronie = [nowaBron(bronStartowa(KLASY[gracz.klasa]), 0)];
    gracz.umi = { cd: 0, cdMax: 0 }; if (gracz.slotyOreza === undefined) gracz.slotyOreza = KLASY[gracz.klasa].slotyOreza || 4; if (gracz.slotyPryzm === undefined) gracz.slotyPryzm = KLASY[gracz.klasa].slotyPryzm || 2; gracz.slotyPryzm = Math.max(gracz.slotyPryzm, liczPrzedm(true)); gracz.slotyPrzedm = Math.max(gracz.slotyPrzedm, liczPrzedm(false));
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

// =====================================================================
//  PAD — gra na kontrolerze (Xbox, PlayStation, Switch Pro, 8BitDo…)
//  przez Gamepad API przeglądarki: na komputerze i na telefonie.
//  Walka: lewa gałka / krzyżak = ruch, A/RT = umiejętność, X/LT = mikstura,
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
  $('padSrodek').innerHTML = '🎮 ' + esc(PAD.nazwa) + '<br>' + kl('LT') + ' 🧪 · ' + kl('RT') + ' ✨ · ' + kl('START') + ' ⏸️';
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
    if (nowe(PB.A) || nowe(PB.RT) || nowe(PB.RB)) { if (uzyjUmiejetnosci()) wibruj(0.3, 70); }
    if (nowe(PB.X) || nowe(PB.LT) || nowe(PB.LB)) wypijMiksture();
    if (nowe(PB.Y) || nowe(PB.START)) $('btnEkw').click();
    if (cokolwiek) PAD.fokusWidoczny = true;
    $('padPodp').classList.remove('widoczny');
  } else {
    PAD.mx = PAD.my = 0;
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
  const lista = root.querySelectorAll('[data-a], button, input, textarea');
  const wyn = [];
  for (const el of lista) {
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
const PREF_FOKUSU = ['kowStatWybierz', 'kup', 'augWybierz', 'kowWybierz', 'statWybierz', 'bronStart', 'probaWybierz', 'skrzWezOreze', 'skrzZaloz', 'skrzPolacz', 'skrzZloto', 'skrzMikstura', 'skrzKamien',
  'wznow', 'kontynuuj', 'znowu', 'startRunuZModala', 'lobbyGotowy', 'dalejPrzerwa', 'augPomin', 'zalozDruzyne'];
function wWidoku(root, el) {
  const v = root.getBoundingClientRect(), r = el.getBoundingClientRect();
  return r.bottom > v.top + 4 && r.top < v.bottom - 4;
}
function fokusDomyslny(root, kand) {
  for (const a of PREF_FOKUSU) { const el = kand.find(e => e.dataset.a === a && !e.disabled); if (el) return el; }
  const kup = kand.find(e => e.dataset.a === 'kup'); if (kup) return kup;
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
  if (f.disabled) { f.classList.remove('pad-nie'); void f.offsetWidth; f.classList.add('pad-nie'); return; }
  f.classList.add('pad-wcisniety'); setTimeout(() => f.classList.remove('pad-wcisniety'), 130);
  f.click();
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
  const syg = PAD.typ + w.k + zak + stan;
  if (syg === PAD.sygPodp) return;
  PAD.sygPodp = syg;
  el.innerHTML = kl('A') + ' wybierz · ' + kl('B') + ' wstecz' + (zak ? ' · ' + kl('LB') + kl('RB') + ' zakładki' : '') + ' · 🕹️ przewijanie' +
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
    w('🕹️ Ruch', 'lewa gałka albo krzyżak') + w('✨ Umiejętność postaci', kl('A') + ' albo ' + kl('RT') + ' / ' + kl('RB')) +
    w('🧪 Mikstura', kl('X') + ' albo ' + kl('LT') + ' / ' + kl('LB')) + w('⏸️ Pauza i build', kl('Y') + ' albo ' + kl('START')) +
    '<div class="sekcja">Menu i sklep — pad</div>' +
    w('Przesuwanie', 'krzyżak albo lewa gałka') + w('Wybierz / kup', kl('A')) + w('Wstecz / zamknij', kl('B')) +
    w('Zakładki', kl('LB') + ' ' + kl('RB')) + w('Przewijanie', 'prawa gałka') +
    '<div class="sekcja">Klawiatura i myszka (komputer)</div>' +
    w('Ruch', 'WASD / strzałki') + w('Umiejętność · mikstura', 'E lub spacja · Q') + w('Pauza', 'Esc lub P') +
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
});
const PREFIKS_PEER = 'wiezien-labiryntu-v1-';
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
function wyslij(conn, msg) {
  try { if (conn && conn.open) { conn.send(msg); return true; } } catch (e) { zglosBlad(e, 'wyslij'); }
  return false;
}
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
    '<div class="sekcja">Twoje imię</div><input class="pole" id="poleNick" maxlength="14" placeholder="np. Ewka" value="' + esc(nick) + '">' +
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
  conn.on('data', d => { if (!przyjmij()) return; try { odbierzOdKlienta(conn, d); } catch (e) { zglosBlad(e, 'odbior ' + (d && d.t)); } });
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
    const conn = peer.connect(PREFIKS_PEER + kod, { reliable: true, serialization: 'json' });
    conn.on('open', () => {
      clearTimeout(limit);
      Object.assign(SIEC, { rola: 'klient', host: conn, kod: kod, wGrze: false });
      wyslij(conn, { t: 'witaj', nick: mojNick(), klasa: mojaKlasa() });
    });
    conn.on('data', d => { SIEC.ostOdHosta = Date.now(); try { odbierzOdHosta(d); } catch (e) { zglosBlad(e, 'odbiorH ' + (d && d.t)); } });
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
  KLUCZE_KLAS.forEach(k => { h += '<div class="kafel' + (k === ja.klasa ? ' wybrany' : '') + '" data-a="lobbyKlasa" data-k="' + k + '"><div class="ik">' + KLASY[k].ik + '</div></div>'; });
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
      if (p && stan === 'walka') { p.netX = +d.x || p.x; p.netY = +d.y || p.y; p.netKX = d.kx; }
      break;
    }
    case 'mik': { const p = gracze.find(q => q.id === id); if (p && stan === 'walka') { kontekst(p); wypijMiksture(); kontekst(z0); } break; }
    case 'umi': { const p = gracze.find(q => q.id === id); if (p && stan === 'walka') { kontekst(p); p.umiKier = Array.isArray(d.k) ? [+d.k[0] || 0, +d.k[1] || 0] : null; uzyjUmiejetnosci(); kontekst(z0); } break; }
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
  SIEC.gotowi = {}; SIEC.dane = {};
  zamknijEkran();
  startFali(SIEC.nastepnaFala);
}
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
  p.tarcze = []; p.zastoj = 0; p.niewr = 2; p.spowG = 0; p.powalony = false; p.reanim = 0; p.cdMikstury = 0;
  run.zlotoFali = 0; run.trafFali = 0; run.spoznionyFala = fala.nr; run.falaMaks = Math.max(run.falaMaks || 0, fala.nr);
  zastosujStaty(); p.hp = D.hpMax; hak('naStartFali'); zastosujStaty();
  kontekst(z0);
  gracze.push(p);
  wrogowie.forEach(w => w._w = false);           // nowy gracz musi poznać wszystkich wrogów
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
  p.oreze = (p.oreze || []).filter(o => o && DEF_ORE[o.id]); p.bronie = (p.bronie || []).filter(b => b && BRONIE[b.rodzaj]); p.umi = { cd: 0, cdMax: 0 }; p.dash = null;
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
  SIEC.zdarzenia = []; SIEC.dzwieki = [];
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
    (p.zastoj > 0 ? 1 : 0) | (p.niewr > 0 ? 2 : 0) | (p.migotanie > 0 ? 4 : 0) | (p.powalony ? 8 : 0), r1((p.reanim || 0) * 10), r1((p.roz || 1) * 100), p.klasa, p.nick,
    p.bronie.map(b => [b.rodzaj, b.tier, r1((b.kat || 0) * 100), b.anim > 0 ? 1 : 0]), r1((p.blysk || 0) * 10)]);
  kontekst(z0);
  const W = [], WN = [];
  for (const w of wrogowie) {
    if (w.martwy) continue;
    const fl = (w.elita ? 1 : 0) | (w.boss ? 2 : 0) | (w.zauroczony > 0 ? 4 : 0) | (w.sojusznik ? 8 : 0) | (w.trafiony > 0 ? 16 : 0) | (w.duch ? 32 : 0) |
      (w.przygotowanie > 0 ? 64 : 0) | (w.spow > 0 && w.spowCzas > 0 ? 128 : 0) | (w.ogl > 0 ? 256 : 0) | (w.ogien ? 512 : 0) | (w.krew ? 1024 : 0) |
      (w.naznaczony > 0 ? 2048 : 0) | (w.pole ? 4096 : 0) | (w.czempion ? 8192 : 0);
    W.push([w.id, r1(w.x), r1(w.y), r1(w.hp / w.hpMax * 1000), fl, r1(w.wysokosc || 0), w.tarczaMax ? r1(w.tarcza / w.tarczaMax * 100) : -1, w.boss ? r1(w.hp) : 0]);
    if (!w._w) { w._w = true; WN.push([w.id, r1(w.r), w.ik, w.kolor, w.obraz || '', w.afiksy.map(a => AFIKSY[a].ik).join(''), w.boss ? w.n : '', w.poswiata || '']); }
    else if (w.boss && w._posw !== w.poswiata) { w._posw = w.poswiata; WN.push([w.id, r1(w.r), w.ik, w.kolor, '', '', w.n, w.poswiata || '']); }
  }
  const nowe = (lista, fn) => { const o = []; for (const e of lista) if (!e._w) { e._w = true; o.push(fn(e)); } return o; };
  const stanW = {
    t: 's', n: SIEC.licznikStanu,
    f: [fala.nr, r1(fala.czas * 10), r1(fala.dlugosc), fala.boss ? 1 : 0, fala.specjalna || '', fala.proba ? fala.proba.id : '', fala.ciemnosc ? 1 : 0],
    g: G, w: W, wn: WN,
    p: pociski.map(p => [r1(p.x), r1(p.y), r1(p.vx), r1(p.vy), p.kolor, p.ksztalt || 'kula', r1((p.obrot || 0) * 10)]),
    pw: pociskiWrogow.map(p => [r1(p.x), r1(p.y), r1(p.vx), r1(p.vy), p.kolor, p.ksztalt || '', p.r || 5, p.siec ? 1 : 0]),
    sk: skrzynieNaZiemi.map(s => [r1(s.x), r1(s.y), s.tier]), mk: miksturyNaZiemi.map(m => [r1(m.x), r1(m.y)]),
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
    vf: nowe(fale, f => [r1(f.x), r1(f.y), r1(f.r), f.kolor, f.czas, f.max, f.odwrot ? 1 : 0, f.slaba ? 1 : 0]),
    vt: nowe(teksty, t => [r1(t.x), r1(t.y), t.t, t.kolor, t.czas, t.max, t.rozm, t.o || 0]),
    vb: nowe(blyskawice, b => (b.a || [0, 0, 0, 0]).concat([b.kolor])),
    vc: nowe(ciecia, c => [r1(c.x), r1(c.y), r1(c.kat * 100), r1(c.luk * 100), r1(c.r), c.max, c.kolor, c.linia ? 1 : 0]),
    vs: nowe(stozki, s => [r1(s.x), r1(s.y), r1(s.kat * 100), r1(s.r), r1(s.pol * 100), s.max, s.kolor]),
    e: SIEC.zdarzenia, dz: SIEC.dzwieki,
  };
  if (SIEC.licznikStanu % 3 === 0) {
    stanW.k = []; kulki.forEach(k => stanW.k.push(r1(k.x), r1(k.y)));
    stanW.m = []; monety.forEach(m => stanW.m.push(r1(m.x), r1(m.y)));
  }
  SIEC.zdarzenia = []; SIEC.dzwieki = [];
  for (const id of ids) {
    const conn = SIEC.polaczenia[id];
    const p = gracze.find(q => String(q.id) === String(id));
    if (!conn || !p) continue;
    try { if (conn.dataChannel && conn.dataChannel.bufferedAmount > 400000) continue; } catch (e) {}
    kontekst(p);
    stanW.ja = { hp: r1(p.hp), hpMax: D.hpMax, ts: r1(tarczaSuma()), xp: r1(p.xp), xpNast: p.xpNast, poziom: p.poziom, zloto: Math.floor(p.zloto), mik: p.mikstury, maksMik: p.maksMikstur,
      cdMik: Math.round(p.cdMikstury * 10) / 10, sk: p.skrzynie.length, dw: p.doWyboru, prz: p.przedmioty.map(q => q ? [Math.round((q.cd || 0) * 10) / 10, Math.round((q.cdMax || 0) * 10) / 10] : [0, 0]),
      ms: r1(D.ms), roz: rozmiarGracza(), spowG: p.spowG, zastoj: p.zastoj > 0 ? 1 : 0, pow: p.powalony ? 1 : 0, niewr: p.niewr > 0 ? 1 : 0,
      umi: [Math.round((p.umi.cd || 0) * 10) / 10, Math.round((p.umi.cdMax || 0) * 10) / 10], ore: p.oreze.map(q => [Math.round((q.cd || 0) * 10) / 10, Math.round((q.cdMax || 0) * 10) / 10]) };
    stanW.eg = SIEC.zdarzeniaG[p.id] || []; SIEC.zdarzeniaG[p.id] = [];
    wyslij(conn, stanW);
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
    case 'czekam': SIEC.ostGotowi = d.gotowi || []; if (SIEC.czekam && stan === 'przerwa') pokazCzekanie(); break;
    case 'ping': break;
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
  SIEC.czekam = false;
  fala = { nr: d.nr, aktywna: true, czas: 0, dlugosc: d.dlugosc, boss: !!d.boss, specjalna: d.specjalna || null, proba: d.proba ? DEF_PROB[d.proba] : null };
  [wrogowie, pociski, pociskiWrogow, kulki, monety, skrzynieNaZiemi, miksturyNaZiemi, kaluze, polaEfektow, wiry, scianyMagiczne, bomby, uderzeniaBossa, zapowiedzi,
    efektyCzasowe, czastki, teksty, fale, blyskawice, ciecia, stozki, orbyRys].forEach(l => l.length = 0);
  SIEC.znaneWrogi = {}; SIEC.widokGraczy = []; SIEC.stwory = [];
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
  g.oreze = (g.oreze || []).filter(o => o && DEF_ORE[o.id]); g.umi = { cd: 0, cdMax: 0 }; g.dash = null;
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
    case 'dash': if (gracz && stan === 'walka') gracz.dash = { vx: e[1] / 100 * e[3] / 0.2, vy: e[2] / 100 * e[3] / 0.2, t: 0.2 }; break;
  }
}
function klientStan(d) {
  if (stan !== 'walka') return;
  SIEC.ostStan = d;
  const f = d.f; fala.nr = f[0]; fala.czas = f[1] / 10; fala.dlugosc = f[2]; fala.boss = !!f[3]; fala.specjalna = f[4] || null; fala.ciemnosc = !!f[6];
  // gracze
  const stare = {}; SIEC.widokGraczy.forEach(p => stare[p.id] = p);
  SIEC.widokGraczy = d.g.map(a => {
    const id = a[0], ja = id === SIEC.mojeId;
    const p = stare[id] || { id: id, x: a[1], y: a[2], faza: 0 };
    p.tx = a[1]; p.ty = a[2]; p.hp = a[3]; p.hpMaxR = a[4]; p.ts = a[5]; p.kierX = a[6]; p.wRuchu = !!a[7];
    p.zastoj = a[8] & 1 ? 1 : 0; p.niewr = a[8] & 2 ? 1 : 0; p.migotanie = a[8] & 4 ? 0.1 : 0; p.powalony = !!(a[8] & 8);
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
    w.tx = a[1]; w.ty = a[2]; w.hpMax = 1000; w.hp = a[3]; w.r = st.r; w.ik = st.ik; w.kolor = st.kolor; w.obraz = st.obraz; w.n = st.n || ''; w.poswiata = st.poswiata;
    const fl = a[4];
    w.elita = !!(fl & 1); w.boss = !!(fl & 2); w.zauroczony = fl & 4 ? 1 : 0; w.sojusznik = !!(fl & 8); w.trafiony = fl & 16 ? 0.1 : 0; w.duch = !!(fl & 32);
    w.przygotowanie = fl & 64 ? 1 : 0; w.spow = fl & 128 ? 0.3 : 0; w.spowCzas = fl & 128 ? 1 : 0; w.ogl = fl & 256 ? 1 : 0; w.ogien = !!(fl & 512); w.krew = !!(fl & 1024);
    w.naznaczony = fl & 2048 ? 1 : 0; w.pole = !!(fl & 4096); w.czempion = !!(fl & 8192);
    w.wysokosc = a[5]; w.tarczaMax = a[6] >= 0 ? 100 : 0; w.tarcza = a[6] >= 0 ? a[6] : 0; w.hpBossa = a[7];
    w.afiksy = []; w.afIk = st.afIk || '';
    return w;
  });
  pociski = d.p.map(a => ({ x: a[0], y: a[1], vx: a[2], vy: a[3], kolor: a[4], ksztalt: a[5], obrot: a[6] / 10 }));
  pociskiWrogow = d.pw.map(a => ({ x: a[0], y: a[1], vx: a[2], vy: a[3], kolor: a[4], ksztalt: a[5] || null, r: a[6], siec: !!a[7] }));
  if (d.k) { kulki = []; for (let i = 0; i < d.k.length; i += 2) kulki.push({ x: d.k[i], y: d.k[i + 1], xp: 2, faza: i }); }
  if (d.m) { monety = []; for (let i = 0; i < d.m.length; i += 2) monety.push({ x: d.m[i], y: d.m[i + 1], v: 1, faza: i }); }
  skrzynieNaZiemi = d.sk.map(a => ({ x: a[0], y: a[1], tier: a[2], faza: 0 }));
  miksturyNaZiemi = d.mk.map(a => ({ x: a[0], y: a[1], faza: 0 }));
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
  (d.dz || []).forEach(n => { if (DZ[n]) DZ[n](); });
  // moja postać (HUD)
  const ja = d.ja;
  if (ja) {
    gracz.hp = ja.hp; if (D) { D.hpMax = ja.hpMax; D.ms = ja.ms; } gracz.tarcze = ja.ts > 0 ? [{ v: ja.ts, czas: 1, max: 1 }] : [];
    gracz.xp = ja.xp; gracz.xpNast = ja.xpNast; gracz.poziom = ja.poziom; gracz.zloto = ja.zloto; gracz.mikstury = ja.mik; gracz.maksMikstur = ja.maksMik;
    gracz.cdMikstury = ja.cdMik; gracz.doWyboru = ja.dw; gracz.skrzynie.length = 0; for (let i = 0; i < ja.sk; i++) gracz.skrzynie.push({ tier: 0 });
    (ja.prz || []).forEach((c, i) => { const q = gracz.przedmioty[i]; if (q) { q.cd = c[0]; q.cdMax = c[1]; } });
    (ja.ore || []).forEach((c, i) => { const q = gracz.oreze[i]; if (q) { q.cd = c[0]; q.cdMax = c[1]; } });
    if (ja.umi) { gracz.umi.cd = ja.umi[0]; gracz.umi.cdMax = ja.umi[1]; }
    SIEC.ms = ja.ms; SIEC.roz = ja.roz; gracz.spowG = ja.spowG; gracz.zastoj = ja.zastoj ? 1 : 0; gracz.powalony = !!ja.pow; gracz.niewr = ja.niewr ? 0.1 : 0;
  }
}
// pętla klienta: tylko własny ruch, wygładzanie i efekty wizualne
function krokKlienta(dt) {
  if (stan !== 'walka') { aktualizujWizualne(dt); return; }
  if (!gracz.powalony) ruszGracza(dt, SIEC.ms || (D && D.ms) || 140, SIEC.roz || 1);
  const k = Math.min(1, dt * 14);
  wrogowie.forEach(w => { if (w.tx !== undefined) { w.x += (w.tx - w.x) * k; w.y += (w.ty - w.y) * k; } });
  SIEC.widokGraczy.forEach(p => { if (p === SIEC.mojWidok) { p.x = gracz.x; p.y = gracz.y; p.kierX = gracz.kierX; p.wRuchu = gracz.wRuchu; p.faza = gracz.faza; } else { p.x += (p.tx - p.x) * k; p.y += (p.ty - p.y) * k; } });
  pociski.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; if (p.ksztalt === 'bumerang') p.obrot += dt * 18; });
  pociskiWrogow.forEach(p => { p.x += p.vx * dt; p.y += p.vy * dt; });
  kulki.forEach(q => q.faza += dt * 6); monety.forEach(q => q.faza += dt * 5);
  wiry.forEach(w => { w.faza += dt * 5; if (w.rozruch > 0) w.rozruch -= dt; });
  aktualizujWizualne(dt);
  czasGry += dt;
  // wysyłka pozycji ok. 20 razy na sekundę
  SIEC.tPoz -= dt;
  if (SIEC.tPoz <= 0) { SIEC.tPoz = 0.05; siecWyslijHost({ t: 'poz', x: Math.round(gracz.x), y: Math.round(gracz.y), kx: gracz.kierX < 0 ? -1 : 1 }); }
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
    pokazInfoSieci(SIEC.wGrze && stan !== 'smierc' && cisza > 5000 ? '📡 Gospodarz nie odpowiada… (' + Math.round(cisza / 1000) + ' s)<br><small style="font-weight:700">Niech otworzy grę na ekranie</small>' : '');
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

// Zaproszenie z linku (?pokoj=KOD) - od razu ekran dołączania
function sprawdzZaproszenie() {
  let kod = '';
  try { kod = new URLSearchParams(window.parent.location.search).get('pokoj') || ''; } catch (e) {}
  if (!kod) try { kod = new URLSearchParams(window.location.search).get('pokoj') || ''; } catch (e) {}
  kod = (kod || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4);
  if (kod.length === 4) pokazOnline(kod);
}

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
    uzyjUmiejetnosci(); e.preventDefault(); return;
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
  if (e.code === 'KeyQ') wypijMiksture();
  if (e.code === 'KeyE' || e.code === 'Space') { uzyjUmiejetnosci(); e.preventDefault(); }
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
      if (!p.powalony) aktualizujGracza(dt);
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
  const dt = Math.min(0.05, Math.max(0, (t - czasOstatni) / 1000)); czasOstatni = t;
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
  umi() { return uzyjUmiejetnosci(); },
  startFali(n) { zamknijEkran(); startFali(n); },
  // drużyna lokalna (testy silnika): kolejny gracz sterowany botem na tym samym urządzeniu
  dodajGracza(kl, nick) {
    const z0 = gracz, r0 = run;
    const r = { trudnosc: r0.trudnosc, zabici: 0, zadane: 0, przyjete: 0, leczenie: 0, zloto: 0, xp: 0, ataki: 0, trafienia: 0, zrodla: {}, zlotoFali: 0, start: Date.now(), falaMaks: 0, przerzutyStatow: 0 };
    const p = nowyGracz(kl); p._run = r; p.nick = nick || KLASY[kl].n; p.id = gracze.length + 1;
    const K = KLASY[kl];
    p.bronie.push(nowaBron(K.start === 'wybor' ? losZ(KLUCZE_BRONI) : bronStartowa(K), K.start === 'wybor' ? 1 : 0));
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
