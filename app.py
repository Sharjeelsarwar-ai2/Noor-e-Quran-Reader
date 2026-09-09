import asyncio
import base64
import html
import io
import json
import os
from typing import Dict, List, Optional

import edge_tts
import requests
import streamlit as st
import streamlit.components.v1 as components

BASE_URL = "https://api.alquran.cloud/v1"

st.set_page_config(
    page_title="Noor — Quran Reader",
    page_icon="☾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Theme
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg:#07110e; --panel:rgba(255,255,255,.065); --border:rgba(255,255,255,.11);
        --text:#f5f7f6; --muted:#a8b3af; --accent:#67d7a0; --gold:#d6b36a;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(circle at 7% 0%, rgba(74,190,132,.12), transparent 28%),
          radial-gradient(circle at 95% 7%, rgba(214,179,106,.09), transparent 24%), var(--bg);
        color:var(--text);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    #MainMenu, footer { display:none !important; visibility:hidden !important; }
    .block-container { max-width:1180px; padding-top:.35rem; padding-bottom:5rem; }

    .hero { position:relative; isolation:isolate; overflow:hidden; padding:2.25rem 2.4rem;
        border:1px solid var(--border); border-radius:30px;
        background:linear-gradient(135deg,rgba(255,255,255,.085),rgba(255,255,255,.03));
        backdrop-filter:blur(22px); -webkit-backdrop-filter:blur(22px);
        box-shadow:0 24px 80px rgba(0,0,0,.22); margin-bottom:1.15rem; }
    .hero::before { content:""; position:absolute; inset:0;
        background:radial-gradient(circle at 82% 25%,rgba(103,215,160,.08),transparent 25%),
        linear-gradient(115deg,transparent 40%,rgba(255,255,255,.025),transparent 70%);
        z-index:-2; pointer-events:none; }
    .hero::after { content:"﷽"; position:absolute; right:-1.5rem; top:.6rem;
        font-family:"Amiri","Noto Naskh Arabic",serif; font-size:clamp(5rem,11vw,8.4rem);
        line-height:1; white-space:nowrap; color:rgba(214,179,106,.075);
        text-shadow:0 0 28px rgba(214,179,106,.04); z-index:-1; pointer-events:none;
        user-select:none; transform:rotate(-1deg); }
    .hero-content { position:relative; z-index:2; max-width:820px; }
    .eyebrow { font-size:.76rem; letter-spacing:.16em; text-transform:uppercase; color:var(--accent);
        font-weight:800; margin-bottom:.5rem; }
    .hero h1 { margin:0; font-size:clamp(2.3rem,4.5vw,3.55rem); line-height:1; letter-spacing:-.04em; }
    .hero p { color:var(--muted); margin:.85rem 0 0; max-width:760px; font-size:1rem; line-height:1.7; }
    .glass-card { position:relative; isolation:isolate; overflow:hidden; border:1px solid var(--border); border-radius:24px; background:linear-gradient(135deg,rgba(255,255,255,.075),rgba(255,255,255,.028));
        padding:1.2rem; backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
        box-shadow:0 14px 45px rgba(0,0,0,.14), inset 0 1px 0 rgba(255,255,255,.035); }
    .glass-card::before { content:"۞"; position:absolute; left:-.15rem; top:-1rem; font-family:"Amiri","Noto Naskh Arabic",serif;
        font-size:5.4rem; line-height:1; color:rgba(214,179,106,.034); transform:rotate(-10deg); pointer-events:none; z-index:-1; }
    .glass-card::after { content:"﷽"; position:absolute; right:-2.1rem; bottom:-2.7rem; font-family:"Amiri","Noto Naskh Arabic",serif;
        font-size:5rem; line-height:1; color:rgba(103,215,160,.026); transform:rotate(-3deg); pointer-events:none; z-index:-1; }
    .surah-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:.4rem 0 1rem; }
    .surah-title { font-size:1.55rem; font-weight:800; letter-spacing:-.02em; }
    .surah-sub { color:var(--muted); font-size:.9rem; }

    /* Enhanced Surah selector: more glass, softer glow, subtle Arabic ornament. */
    .stSelectbox { position:relative; }
    .stSelectbox::before { content:"۞"; position:absolute; left:14px; top:50%; transform:translateY(-51%); z-index:3;
        font-family:"Amiri","Noto Naskh Arabic",serif; font-size:1.05rem; color:rgba(214,179,106,.72);
        pointer-events:none; text-shadow:0 0 14px rgba(214,179,106,.12); }
    .stSelectbox::after { content:"القرآن"; position:absolute; right:42px; top:-1.05rem; z-index:3;
        font-family:"Amiri","Noto Naskh Arabic",serif; font-size:.92rem; color:rgba(214,179,106,.42);
        pointer-events:none; letter-spacing:.02em; }
    div[data-baseweb="select"] { filter:drop-shadow(0 14px 28px rgba(0,0,0,.12)); }
    div[data-baseweb="select"] > div { min-height:58px; padding-left:2.2rem !important; padding-right:2.8rem !important;
        background:linear-gradient(135deg,rgba(36,39,53,.94),rgba(28,30,42,.88)) !important;
        border:1px solid rgba(255,255,255,.12) !important; border-radius:18px !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.055), 0 10px 28px rgba(0,0,0,.16) !important;
        backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); transition:all .22s ease; }
    div[data-baseweb="select"] > div:hover { border-color:rgba(103,215,160,.34) !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.07), 0 0 0 1px rgba(103,215,160,.06), 0 14px 32px rgba(0,0,0,.18) !important;
        transform:translateY(-1px); }
    div[data-baseweb="select"] span { font-weight:650 !important; color:#f2f5f4 !important; }
    div[data-baseweb="select"] svg { color:rgba(214,179,106,.9) !important; }
    [data-baseweb="popover"] { background:rgba(17,25,22,.97) !important; border:1px solid rgba(255,255,255,.10) !important;
        border-radius:18px !important; box-shadow:0 24px 60px rgba(0,0,0,.35) !important; backdrop-filter:blur(20px); }
    [role="option"] { color:#e8efec !important; min-height:44px !important; }
    [role="option"]:hover, [aria-selected="true"] { background:rgba(103,215,160,.09) !important; }

    .ayah-card { position:relative; isolation:isolate; overflow:hidden; border:1px solid rgba(255,255,255,.09); border-radius:22px; padding:1.25rem 1.35rem;
        margin:.95rem 0; background:linear-gradient(135deg,rgba(255,255,255,.045),rgba(255,255,255,.02));
        backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); box-shadow:inset 0 1px 0 rgba(255,255,255,.025); }
    .ayah-card::after { content:"۝"; position:absolute; left:-.15rem; bottom:-1.1rem; font-family:"Amiri","Noto Naskh Arabic",serif;
        font-size:4.2rem; color:rgba(103,215,160,.024); transform:rotate(-12deg); pointer-events:none; z-index:-1; }
    .ayah-num { display:inline-flex; align-items:center; justify-content:center; min-width:31px; height:31px;
        border-radius:50%; border:1px solid rgba(214,179,106,.35); color:var(--gold); font-size:.8rem; margin-bottom:.7rem;
        background:rgba(214,179,106,.045); box-shadow:inset 0 1px 0 rgba(255,255,255,.04); }
    .ayah-arabic { font-family:"Amiri","Noto Naskh Arabic",serif; direction:rtl; text-align:right;
        font-size:2rem; line-height:2.05; color:#fbfcfb; }
    .translation-label { color:var(--accent); font-size:.76rem; letter-spacing:.08em;
        text-transform:uppercase; font-weight:800; margin-top:.95rem; margin-bottom:.25rem; }
    .translation { color:#dce4e1; font-size:1rem; line-height:1.75; direction:rtl; text-align:right; }
    .translation.en { direction:ltr; text-align:left; }
    .source { color:#7f8b86; font-size:.78rem; margin-top:1.35rem; text-align:center; }

    /* Give the mode / translation controls the same frosted-glass language. */
    div[data-testid="stRadio"] > div { gap:.55rem; }
    div[data-testid="stRadio"] label { border:1px solid rgba(255,255,255,.075); border-radius:999px;
        padding:.48rem .78rem; background:rgba(255,255,255,.035); backdrop-filter:blur(12px);
        transition:all .2s ease; }
    div[data-testid="stRadio"] label:hover { border-color:rgba(103,215,160,.22); background:rgba(103,215,160,.045); }
    .stButton > button { border-radius:14px; border:1px solid rgba(103,215,160,.22);
        background:rgba(103,215,160,.11); color:#eafcf2; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Quran API
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_json(url: str, timeout: int = 25) -> dict:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Noor-Quran-App/3.0"})
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError(data.get("status", "API request failed"))
    return data


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_list() -> List[dict]:
    return get_json(f"{BASE_URL}/surah", 15)["data"]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_data(surah: int, edition: str) -> List[dict]:
    return get_json(f"{BASE_URL}/surah/{surah}/{edition}", 30)["data"]["ayahs"]


# -----------------------------------------------------------------------------
# Free neural spoken translation — generated inside Streamlit, no backend/API key
# -----------------------------------------------------------------------------
URDU_VOICE = "ur-PK-AsadNeural"
URDU_RATE = "-14%"
URDU_PITCH = "-1Hz"
EN_VOICE = "en-US-GuyNeural"
EN_RATE = "-8%"
EN_PITCH = "-1Hz"


def normalize_for_urdu_speech(text: str) -> str:
    """Create a TTS-only pronunciation layer while keeping displayed Urdu intact."""
    punctuation = {
        "،": "، ", "۔": "۔ ", ":": ": ", "؛": "؛ ",
        "؟": "؟ ", "!": "! ", "  ": " ",
    }

    # Focused pronunciation hints for Arabic-origin words that Urdu neural TTS
    # can flatten, especially long-aa/alif sounds. The on-screen translation
    # is never changed; only the hidden TTS input uses these spellings.
    pronunciation = {
        "اللہ تعالیٰ": "اَللّٰہ تَعَالٰی",
        "سبحان اللہ": "سُبْحَانَ اَللّٰہ",
        "الحمدللہ": "اَلْحَمْدُ لِلّٰہ",
        "ان شاء اللہ": "اِنْ شَاءَ اَللّٰہ",
        "ماشاء اللہ": "مَا شَاءَ اَللّٰہ",
        "بسم اللہ": "بِسْمِ اَللّٰہ",
        "اللّٰہ": "اَللّٰہ",
        "اللّہ": "اَللّٰہ",
        "اللہ": "اَللّٰہ",
        "الله": "اَللّٰه",
        "تعالیٰ": "تَعَالٰی",
        "تعالی": "تَعَالٰی",
        "رحمن": "رَحْمٰن",
        "رحیم": "رَحِیم",
        "قرآن": "قُرْآن",
        "قران": "قُرْآن",
        "آخرت": "آخِرَت",
        "قیامت": "قِیَامَت",
        "رسول": "رَسُول",
        "نبی": "نَبِی",
        "انبیاء": "اَنْبِیَاء",
        "محمد": "مُحَمَّد",
        "مومن": "مُؤْمِن",
        "مومنین": "مُؤْمِنِین",
        "ایمان": "اِیمَان",
        "اسلام": "اِسْلَام",
        "الاسلام": "اَلْاِسْلَام",
        "دعا": "دُعَاء",
        "نماز": "نَمَاز",
        "زکوٰۃ": "زَکٰوۃ",
        "زکات": "زَکَات",
        "جنت": "جَنَّت",
        "جہنم": "جَہَنَّم",
        "آسمان": "آسْمَان",
        "آسمانوں": "آسْمَانوں",
        "دنیا": "دُنْیَا",
        "عذاب": "عَذَاب",
        "ثواب": "ثَوَاب",
        "کتاب": "کِتَاب",
        "حساب": "حِسَاب",
        "عالمین": "عَالَمِین",
        "رحمت": "رَحْمَت",
        "برکت": "بَرَکَت",
    }

    out = text.strip()
    for old_word in sorted(pronunciation, key=len, reverse=True):
        out = out.replace(old_word, pronunciation[old_word])
    for old, new in punctuation.items():
        out = out.replace(old, new)
    return " ".join(out.split())


@st.cache_data(ttl=60 * 60 * 24 * 30, show_spinner=False)
def synthesize_tts(text: str, language: str) -> bytes:
    if not text.strip():
        return b""

    if language == "ur":
        voice, rate, pitch = URDU_VOICE, URDU_RATE, URDU_PITCH
        text = normalize_for_urdu_speech(text)
    else:
        voice, rate, pitch = EN_VOICE, EN_RATE, EN_PITCH

    async def _run() -> bytes:
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    return asyncio.run(_run())


def audio_data_url(audio_bytes: bytes) -> str:
    return "data:audio/mpeg;base64," + base64.b64encode(audio_bytes).decode("ascii")


# -----------------------------------------------------------------------------
# Hero
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-content">
        <div class="eyebrow">Read • Reflect • Listen</div>
        <h1>Noor</h1>
        <p>A calm, distraction-free Quran experience with authentic Arabic recitation and a clearly spoken translation — verse by verse.</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    surahs = get_surah_list()
except Exception as exc:
    st.error("Quran data load nahi ho saka. Internet connection ya API availability check karein.")
    st.caption(f"Technical detail: {exc}")
    st.stop()

left, right = st.columns([2.2, 1], gap="large")
with left:
    labels = [f"{s['number']:02d}  {s['englishName']} — {s['name']}" for s in surahs]
    idx = st.selectbox("Surah", range(len(surahs)), format_func=lambda i: labels[i], label_visibility="collapsed")
    selected = surahs[idx]
with right:
    mode = st.radio("Mode", ["📖 Read", "🔊 Listen"], horizontal=True, label_visibility="collapsed")

surah_number = selected["number"]
surah_name = selected["englishName"]
arabic_name = selected["name"]
ayah_count = selected.get("numberOfAyahs", 0)

st.markdown(
    f"""
    <div class="glass-card surah-head">
      <div><div class="surah-title">{html.escape(surah_name)}</div>
      <div class="surah-sub">{html.escape(arabic_name)} • {ayah_count} Ayahs</div></div>
      <div class="surah-sub">Surah {surah_number}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Read mode
# -----------------------------------------------------------------------------
if mode == "📖 Read":
    choice = st.radio("Translation", ["Arabic only", "Arabic + Urdu", "Arabic + English"], horizontal=True)
    try:
        arabic_ayahs = get_surah_data(surah_number, "quran-uthmani")
        urdu_ayahs = get_surah_data(surah_number, "ur.jalandhry") if "Urdu" in choice else None
        english_ayahs = get_surah_data(surah_number, "en.sahih") if "English" in choice else None
    except Exception as exc:
        st.error("Surah load nahi ho saki.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    for i, ayah in enumerate(arabic_ayahs):
        urdu = urdu_ayahs[i]["text"] if urdu_ayahs and i < len(urdu_ayahs) else None
        eng = english_ayahs[i]["text"] if english_ayahs and i < len(english_ayahs) else None
        parts = ['<div class="ayah-card">', f'<div class="ayah-num">{ayah["numberInSurah"]}</div>',
                 f'<div class="ayah-arabic">{html.escape(ayah["text"])}</div>']
        if urdu:
            parts += ['<div class="translation-label">Urdu</div>', f'<div class="translation">{html.escape(urdu)}</div>']
        if eng:
            parts += ['<div class="translation-label">English</div>', f'<div class="translation en">{html.escape(eng)}</div>']
        parts.append('</div>')
        st.markdown("".join(parts), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Listen mode: the working single-Streamlit architecture.
# All audio is prepared before the player is shown. After that, browser playback
# is completely client-side, so changing from Arabic -> Urdu -> next Ayah doesn't
# require another Python round-trip and does not reset the current position.
# -----------------------------------------------------------------------------
else:
    playback_choice = st.radio(
        "Playback",
        ["Arabic + Urdu spoken meaning", "Arabic + English spoken meaning", "Arabic only"],
        horizontal=True,
    )

    try:
        arabic_ayahs = get_surah_data(surah_number, "ar.alafasy")
        translation_ayahs = None
        language = "none"
        if playback_choice != "Arabic only":
            language = "ur" if "Urdu" in playback_choice else "en"
            edition = "ur.jalandhry" if language == "ur" else "en.sahih"
            translation_ayahs = get_surah_data(surah_number, edition)
    except Exception as exc:
        st.error("Surah audio/text load nahi ho saka.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    tracks = []
    for i, ayah in enumerate(arabic_ayahs):
        translation = ""
        if translation_ayahs and i < len(translation_ayahs):
            translation = translation_ayahs[i].get("text", "")
        tracks.append({
            "ayah": ayah.get("numberInSurah", i + 1),
            "arabic": ayah.get("text", ""),
            "arabic_audio": ayah.get("audio", ""),
            "translation": translation,
            "translation_audio": "",
        })

    # Prepare translation audio only when the user explicitly chose spoken meaning.
    # Cached per Ayah, so revisiting a Surah does not regenerate existing audio.
    if language != "none":
        progress = st.progress(0, text="Preparing spoken translation…")
        for i, track in enumerate(tracks):
            if track["translation"]:
                try:
                    audio_bytes = synthesize_tts(track["translation"], language)
                    track["translation_audio"] = audio_data_url(audio_bytes) if audio_bytes else ""
                except Exception as exc:
                    track["translation_audio"] = ""
                    st.warning(f"Urdu/translation voice unavailable for Ayah {track['ayah']}. Arabic playback will continue.")
                    st.caption(f"Technical detail: {exc}")
            progress.progress((i + 1) / len(tracks), text=f"Preparing spoken translation • Ayah {i + 1}/{len(tracks)}")
        progress.empty()

    payload = json.dumps(tracks, ensure_ascii=False, separators=(",", ":"))
    language_json = json.dumps(language)

    player_html = f"""
    <!doctype html>
    <html><head><meta charset="utf-8"><style>
      * {{ box-sizing:border-box; }}
      body {{ margin:0; font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif; background:transparent; color:#f5f7f6; }}
      .shell {{ border:1px solid rgba(255,255,255,.11); border-radius:24px;
        background:linear-gradient(135deg,rgba(255,255,255,.10),rgba(255,255,255,.045));
        backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); padding:18px;
        box-shadow:0 20px 55px rgba(0,0,0,.18); position:relative; overflow:visible; }}
      .top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
      .brand {{ color:#67d7a0; font-weight:800; font-size:12px; letter-spacing:.12em; text-transform:uppercase; }}
      .status {{ color:#9daaa5; font-size:12px; }}
      .verse {{ font-family:"Amiri","Noto Naskh Arabic",serif; direction:rtl; text-align:right;
        font-size:28px; line-height:1.9; margin:14px 0 8px; }}
      .translation {{ direction:rtl; text-align:right; color:#d8e1dd; font-size:15px; line-height:1.7; min-height:24px; }}
      .translation.en {{ direction:ltr; text-align:left; }}
      .meta {{ color:#8c9893; font-size:12px; margin-top:8px; }}
      .controls {{ display:flex; align-items:center; gap:10px; margin-top:14px; flex-wrap:wrap; }}
      button {{ appearance:none; border:1px solid rgba(103,215,160,.22); background:rgba(103,215,160,.12);
        color:#eafcf2; padding:10px 15px; border-radius:999px; font-weight:800; cursor:pointer; }}
      button.secondary {{ border-color:rgba(255,255,255,.10); background:rgba(255,255,255,.055); color:#d5ddda; }}
      .progress {{ height:5px; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden; margin-top:15px; }}
      .bar {{ height:100%; width:0; background:linear-gradient(90deg,#67d7a0,#d6b36a); transition:width .18s linear; }}
      .popup {{ position:absolute; right:18px; bottom:-18px; display:flex; align-items:center; gap:9px; max-width:calc(100% - 36px);
        padding:9px 13px; border-radius:999px; border:1px solid rgba(255,255,255,.14); background:rgba(10,23,19,.88);
        backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); box-shadow:0 14px 36px rgba(0,0,0,.3);
        color:#ecf6f1; font-size:12px; opacity:0; transform:translateY(8px); pointer-events:none;
        transition:opacity .25s ease,transform .25s ease; z-index:20; }}
      .popup.show {{ opacity:1; transform:translateY(0); }}
      .dot {{ width:8px; height:8px; border-radius:50%; background:#67d7a0; box-shadow:0 0 14px rgba(103,215,160,.75); flex:0 0 auto; }}
      .note {{ color:#77847f; font-size:11px; margin-top:12px; }}
    </style></head>
    <body>
      <div class="shell">
        <div class="top"><div class="brand">Noor • Recitation</div><div class="status" id="counter">Ready</div></div>
        <div class="verse" id="verse">Press Start to begin</div>
        <div class="translation" id="translation"></div>
        <div class="meta" id="meta">Arabic recitation → spoken meaning</div>
        <div class="controls">
          <button id="start">▶ Start / Resume</button>
          <button id="pause" class="secondary">Ⅱ Pause</button>
          <button id="stop" class="secondary">■ Stop</button>
        </div>
        <div class="progress"><div class="bar" id="bar"></div></div>
        <div class="note">The translation is a spoken meaning, not Quranic recitation. It is delivered in a calm, neutral male Urdu voice.</div>
        <div class="popup" id="popup"><span class="dot"></span><span id="popupText">Now playing</span></div>
      </div>
      <audio id="audio" preload="auto"></audio>
      <script>
        const tracks = {payload};
        const language = {language_json};
        const audio = document.getElementById("audio");
        const verse = document.getElementById("verse");
        const translation = document.getElementById("translation");
        const meta = document.getElementById("meta");
        const counter = document.getElementById("counter");
        const bar = document.getElementById("bar");
        const popup = document.getElementById("popup");
        const popupText = document.getElementById("popupText");
        let index = 0;
        let phase = "arabic";
        let running = false;
        let completed = false;
        let retryTimer = null;
        let lastSrc = "";

        function showPopup(text) {{
          popupText.textContent = text;
          popup.classList.add("show");
          clearTimeout(window.popupTimer);
          window.popupTimer = setTimeout(() => popup.classList.remove("show"), 3500);
        }}

        function updateUI(track) {{
          verse.textContent = track.arabic || "";
          translation.textContent = track.translation || "";
          translation.classList.toggle("en", language === "en");
          counter.textContent = `Ayah ${{track.ayah}} / ${{tracks.length}}`;
        }}

        function updateProgress(extra) {{
          const pct = ((index + extra) / Math.max(tracks.length, 1)) * 100;
          bar.style.width = `${{Math.min(pct,100)}}%`;
        }}

        function stopElement() {{
          audio.pause();
          audio.removeAttribute("src");
          audio.load();
          lastSrc = "";
        }}

        function playSource(src, label, onFail) {{
          if (!src) {{ onFail(); return; }}
          stopElement();
          lastSrc = src;
          audio.src = src;
          audio.load();
          showPopup(label);
          const promise = audio.play();
          if (promise) promise.catch(() => {{
            // Do not reset the ayah. A transient browser media error should retry
            // the exact current phase rather than forcing the user to restart.
            clearTimeout(retryTimer);
            retryTimer = setTimeout(() => {{
              if (running && lastSrc === src) {{
                try {{ audio.play().catch(() => onFail()); }} catch (e) {{ onFail(); }}
              }}
            }}, 450);
          }});
        }}

        function playArabic() {{
          if (!running || !tracks[index]) return;
          phase = "arabic";
          const t = tracks[index];
          updateUI(t); updateProgress(0);
          meta.textContent = language === "none" ? "Arabic recitation" : "Arabic recitation • spoken meaning follows";
          playSource(t.arabic_audio, `Ayah ${{t.ayah}} • Arabic recitation`, () => showPopup("Arabic audio could not load"));
        }}

        function playTranslation() {{
          if (!running || !tracks[index]) return;
          if (language === "none") {{ nextAyah(); return; }}
          phase = "translation";
          const t = tracks[index];
          updateUI(t); updateProgress(0.5);
          meta.textContent = language === "ur" ? "Arabic complete • spoken Urdu meaning" : "Arabic complete • spoken English meaning";
          const label = language === "ur" ? `Ayah ${{t.ayah}} • Urdu meaning` : `Ayah ${{t.ayah}} • English meaning`;
          playSource(t.translation_audio, label, () => nextAyah());
        }}

        function nextAyah() {{
          if (!running) return;
          index += 1;
          if (index >= tracks.length) {{
            running = false;
            completed = true;
            phase = "arabic";
            counter.textContent = "Completed";
            bar.style.width = "100%";
            meta.textContent = "Alhamdulillah • Surah completed";
            showPopup("Surah completed");
            return;
          }}
          phase = "arabic";
          // Start the next Ayah from the exact next index; never reset to 0 here.
          playArabic();
        }}

        document.getElementById("start").addEventListener("click", () => {{
          if (completed) {{
            index = 0;
            phase = "arabic";
            completed = false;
            stopElement();
          }}
          running = true;
          if (phase === "translation") playTranslation();
          else playArabic();
        }});

        document.getElementById("pause").addEventListener("click", () => {{
          if (!running) return;
          if (!audio.paused) {{
            audio.pause();
            meta.textContent = phase === "arabic" ? "Arabic paused" : "Translation paused";
            showPopup("Paused");
          }} else {{
            audio.play().then(() => showPopup("Resumed")).catch(() => showPopup("Press Start / Resume once to continue"));
          }}
        }});

        document.getElementById("stop").addEventListener("click", () => {{
          running = false;
          completed = false;
          stopElement();
          index = 0;
          phase = "arabic";
          counter.textContent = "Ready";
          bar.style.width = "0%";
          verse.textContent = "Press Start to begin";
          translation.textContent = "";
          meta.textContent = "Arabic recitation → spoken meaning";
          popup.classList.remove("show");
        }});

        audio.addEventListener("timeupdate", () => {{
          if (!audio.duration || !tracks.length) return;
          const base = (index / tracks.length) * 100;
          const phaseBase = phase === "translation" ? (0.5 / tracks.length) * 100 : 0;
          const inTrack = (audio.currentTime / audio.duration) * (0.5 / tracks.length) * 100;
          bar.style.width = `${{Math.min(base + phaseBase + inTrack, 100)}}%`;
        }});

        audio.addEventListener("ended", () => {{
          if (!running) return;
          if (phase === "arabic") playTranslation();
          else nextAyah();
        }});

        audio.addEventListener("error", () => {{
          if (!running) return;
          // Skip only a broken source. Do not reset the current Surah or index.
          if (phase === "translation") nextAyah();
          else showPopup("Arabic audio could not load");
        }});
      </script>
    </body></html>
    """

    # Extra height prevents the floating pill from being clipped.
    components.html(player_html, height=405)
    st.markdown(
        '<div class="source">Arabic recitation: Alafasy • Quran text & translation: alquran.cloud • Spoken meaning: free Edge neural TTS.</div>',
        unsafe_allow_html=True,
    )
