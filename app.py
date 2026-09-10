import asyncio
import base64
import html
import io
import json
import os
import re
import time
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
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Amiri:wght@400;700&family=Reem+Kufi:wght@400;500;600;700&family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700;800;900&display=swap');

    :root {
        --bg:#050d0b; --bg2:#081613;
        --panel:rgba(255,255,255,.055); --panel-strong:rgba(18,35,29,.72);
        --border:rgba(255,255,255,.11); --border-soft:rgba(255,255,255,.075);
        --text:#f7faf8; --muted:#a9b5b0; --accent:#68d9a2; --accent2:#3fb886;
        --gold:#e3c07f; --gold-dim:#d7b66b;
        --radius-lg:28px; --radius-md:22px; --radius-sm:14px;
    }

    * { scrollbar-width:thin; scrollbar-color:rgba(104,217,162,.35) transparent; }
    ::-webkit-scrollbar { width:9px; height:9px; }
    ::-webkit-scrollbar-track { background:transparent; }
    ::-webkit-scrollbar-thumb { background:linear-gradient(180deg,rgba(104,217,162,.45),rgba(215,182,107,.3)); border-radius:99px; }

    html, body, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse 900px 500px at 12% -5%, rgba(75,202,141,.14), transparent 60%),
          radial-gradient(ellipse 700px 420px at 92% 2%, rgba(226,192,127,.11), transparent 55%),
          radial-gradient(ellipse 1000px 650px at 50% 120%, rgba(63,184,134,.08), transparent 60%),
          linear-gradient(180deg, var(--bg2), var(--bg) 55%, #040a08);
        color:var(--text);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {
        display:none !important; visibility:hidden !important; height:0 !important;
    }
    .block-container { max-width:1180px; padding-top:1.1rem; padding-bottom:5.5rem; }

    /* ============================================================
       HERO — single coherent decorative system: one geometric
       lattice texture + one calligraphic focal point, layered
       with real depth instead of four competing effects.
       ============================================================ */
    .hero {
        position:relative; isolation:isolate; overflow:hidden;
        min-height:360px; display:flex; align-items:flex-end;
        padding:3.1rem 2.75rem 2.9rem; margin-bottom:1.6rem;
        border:1px solid rgba(255,255,255,.13); border-radius:36px;
        background:
          linear-gradient(150deg, rgba(255,255,255,.09), rgba(255,255,255,.022) 55%, rgba(104,217,162,.035)),
          linear-gradient(180deg, rgba(9,20,17,.55), rgba(6,14,12,.75));
        backdrop-filter:blur(28px); -webkit-backdrop-filter:blur(28px);
        box-shadow:
          0 32px 100px rgba(0,0,0,.34),
          0 1px 0 rgba(255,255,255,.06) inset,
          0 0 0 1px rgba(215,182,107,.04) inset;
    }
    /* Islamic geometric lattice — one subtle repeating texture across the whole hero */
    .hero::before {
        content:""; position:absolute; inset:0; z-index:0; pointer-events:none;
        opacity:.5;
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='84' height='84' viewBox='0 0 84 84'%3E%3Cg fill='none' stroke='%23d7b66b' stroke-width='0.6' opacity='0.35'%3E%3Cpath d='M42 2 L74 22 L74 62 L42 82 L10 62 L10 22 Z'/%3E%3Cpath d='M42 2 L42 82 M10 22 L74 62 M74 22 L10 62'/%3E%3Ccircle cx='42' cy='42' r='13'/%3E%3C/g%3E%3C/svg%3E");
        background-size:84px 84px;
        mask-image:radial-gradient(ellipse 100% 100% at 50% 0%, black 0%, transparent 78%);
        -webkit-mask-image:radial-gradient(ellipse 100% 100% at 50% 0%, black 0%, transparent 78%);
    }
    .hero::after {
        content:""; position:absolute; inset:0; z-index:0; pointer-events:none;
        background:
          radial-gradient(circle at 88% 15%, rgba(104,217,162,.14), transparent 32%),
          radial-gradient(circle at 4% 95%, rgba(226,192,127,.09), transparent 30%);
    }

    .hero-art { position:absolute; inset:0; overflow:hidden; pointer-events:none; user-select:none; z-index:1; }

    /* Full Bismillah — now the dominant focal artwork, filling the hero as a
       large luminous watermark behind the heading, gold-to-jade gradient. */
    .hero-calligraphy {
        position:absolute; left:50%; top:48%; transform:translate(-50%,-52%) rotate(-.4deg);
        width:108%; text-align:center; direction:rtl; white-space:nowrap;
        font-family:"Aref Ruqaa","Amiri","Noto Naskh Arabic",serif; font-weight:700;
        font-size:clamp(5.2rem,12vw,10rem); line-height:1;
        background:linear-gradient(100deg, rgba(215,182,107,.6) 8%, rgba(244,225,177,.95) 40%, rgba(104,217,162,.55) 66%, rgba(215,182,107,.6) 94%);
        -webkit-background-clip:text; background-clip:text; color:transparent;
        filter:drop-shadow(0 16px 60px rgba(215,182,107,.22));
        opacity:.42;
    }
    .hero-calligraphy-sub {
        position:absolute; left:50%; bottom:1.15rem; transform:translateX(-50%);
        width:90%; text-align:center; direction:rtl; white-space:nowrap;
        font-family:"Amiri",serif; font-weight:400; font-size:clamp(1rem,1.7vw,1.35rem);
        color:rgba(233,240,236,.22); letter-spacing:.02em;
    }
    .hero-crescent {
        position:absolute; right:6.5%; top:12%; width:46px; height:46px; z-index:2;
        border-radius:50%; border:1.5px solid rgba(215,182,107,.55);
        box-shadow:0 0 26px rgba(215,182,107,.18), inset -10px -3px 0 -6px rgba(215,182,107,.55);
        opacity:.75;
    }
    .hero-orbit {
        position:absolute; right:6%; top:8%; width:38%; height:58%;
        border:1px solid rgba(215,182,107,.06); border-radius:50%; transform:rotate(-9deg);
    }

    .hero-content { position:relative; z-index:3; max-width:820px; }
    .eyebrow {
        display:inline-flex; align-items:center; gap:.5rem;
        font-size:.72rem; letter-spacing:.2em; text-transform:uppercase; color:var(--accent); font-weight:800;
        margin-bottom:.8rem; padding:.3rem .85rem; border-radius:99px;
        border:1px solid rgba(104,217,162,.28); background:rgba(104,217,162,.07);
    }
    .eyebrow::before { content:"✦"; color:var(--gold); font-size:.7rem; }
    .hero h1 {
        margin:0; font-size:clamp(2.7rem,5.4vw,4.1rem); line-height:1; letter-spacing:-.045em;
        font-family:Inter,sans-serif; font-weight:900;
        background:linear-gradient(120deg,#ffffff 0%,#eef4f0 45%,var(--gold) 130%);
        -webkit-background-clip:text; background-clip:text; color:transparent;
    }
    .hero p { color:var(--muted); margin:1.05rem 0 0; max-width:760px; font-size:1.02rem; line-height:1.85; }

    /* ============================================================
       GLASS CARDS — single soft gradient border, no competing
       watermark clutter, refined layered shadow.
       ============================================================ */
    .glass-card {
        position:relative; isolation:isolate; overflow:hidden;
        border-radius:var(--radius-lg); padding:1.3rem 1.45rem; margin-bottom:0;
        background:linear-gradient(135deg,rgba(255,255,255,.075),rgba(255,255,255,.022));
        backdrop-filter:blur(22px); -webkit-backdrop-filter:blur(22px);
        box-shadow:
          0 20px 54px rgba(0,0,0,.16),
          0 1px 0 rgba(255,255,255,.045) inset;
        border:1px solid rgba(255,255,255,.11);
    }
    .glass-card::before {
        content:""; position:absolute; inset:0; border-radius:inherit; padding:1px; z-index:-1;
        background:linear-gradient(135deg, rgba(215,182,107,.32), rgba(255,255,255,.02) 40%, rgba(104,217,162,.24));
        -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;
    }
    .surah-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
    .surah-title { font-size:1.6rem; font-weight:800; letter-spacing:-.025em; }
    .surah-sub { color:var(--muted); font-size:.9rem; margin-top:.15rem; }
    .surah-number {
        color:var(--gold); font-family:"Cormorant Garamond",serif; font-weight:700; font-size:1.05rem;
        padding:.4rem .95rem; border-radius:99px; border:1px solid rgba(215,182,107,.3);
        background:rgba(215,182,107,.06);
    }

    /* ============================================================
       SURAH SELECTOR
       ============================================================ */
    [data-testid="stSelectbox"] { position:relative; z-index:20; }
    [data-testid="stSelectbox"] label { display:none !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] { width:100%; }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        position:relative !important; min-height:66px; padding:0 4.5rem 0 3.4rem !important;
        border:1px solid rgba(104,217,162,.22) !important; border-radius:22px !important;
        background:
          radial-gradient(circle at 12% 50%, rgba(104,217,162,.12), transparent 26%),
          linear-gradient(135deg, rgba(27,48,40,.94), rgba(9,20,17,.9)) !important;
        box-shadow:
          inset 0 1px 0 rgba(255,255,255,.09),
          inset 0 0 0 1px rgba(215,182,107,.03),
          0 18px 42px rgba(0,0,0,.26) !important;
        backdrop-filter:blur(26px); -webkit-backdrop-filter:blur(26px);
        transition:transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div::before {
        content:"۞"; position:absolute; left:1rem; top:50%; transform:translateY(-52%);
        font-family:"Amiri",serif; font-size:1.5rem; color:rgba(215,182,107,.68);
        pointer-events:none; z-index:3; text-shadow:0 0 18px rgba(215,182,107,.14);
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div::after {
        content:"القرآن الكريم"; position:absolute; right:3.1rem; top:50%; transform:translateY(-54%);
        font-family:"Amiri",serif; font-size:.88rem; color:rgba(215,182,107,.4);
        pointer-events:none; z-index:3;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
        transform:translateY(-2px); border-color:rgba(104,217,162,.48) !important;
        box-shadow:
          inset 0 1px 0 rgba(255,255,255,.1),
          0 24px 50px rgba(0,0,0,.3),
          0 0 34px rgba(104,217,162,.1) !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] span { color:#f4f8f6 !important; font-weight:650 !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] svg { color:var(--gold) !important; width:21px; height:21px; }
    [data-testid="stSelectbox"] [role="combobox"] { color:#f4f8f6 !important; }
    [data-baseweb="popover"] {
        background:rgba(8,18,15,.98) !important; border:1px solid rgba(104,217,162,.18) !important;
        border-radius:20px !important; box-shadow:0 34px 90px rgba(0,0,0,.5) !important;
        backdrop-filter:blur(30px); -webkit-backdrop-filter:blur(30px); padding:6px !important;
    }
    [role="listbox"] { background:transparent !important; }
    [role="option"] { color:#e8f0ec !important; min-height:48px !important; border-radius:13px !important; margin:2px 0 !important; }
    [role="option"]:hover, [role="option"][aria-selected="true"] { background:rgba(104,217,162,.13) !important; }

    /* ============================================================
       MODE / SEGMENTED CONTROLS
       ============================================================ */
    div[data-testid="stRadio"] > div {
        gap:.4rem; flex-wrap:wrap; padding:.3rem; border-radius:999px;
        background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.08);
    }
    div[data-testid="stRadio"] label {
        border:1px solid transparent; border-radius:999px;
        padding:.55rem .95rem; background:transparent;
        transition:all .2s ease; font-weight:600;
    }
    div[data-testid="stRadio"] label:hover {
        border-color:rgba(104,217,162,.28); background:rgba(104,217,162,.09); transform:translateY(-1px);
    }
    div[data-testid="stRadio"]:has(input:checked) label:has(input:checked) {
        background:linear-gradient(135deg, rgba(104,217,162,.22), rgba(215,182,107,.14)) !important;
        border-color:rgba(104,217,162,.45) !important;
        box-shadow:0 6px 18px rgba(104,217,162,.12);
    }

    /* ============================================================
       AYAH CARDS — one restrained watermark, cleaner rhythm
       ============================================================ */
    .ayah-card {
        position:relative; isolation:isolate; overflow:hidden;
        border-radius:24px; padding:1.5rem 1.6rem; margin:1.05rem 0;
        background:linear-gradient(135deg,rgba(255,255,255,.05),rgba(255,255,255,.016));
        backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
        border:1px solid rgba(255,255,255,.09);
        box-shadow:0 1px 0 rgba(255,255,255,.03) inset, 0 14px 40px rgba(0,0,0,.1);
        transition:border-color .25s ease, box-shadow .25s ease;
    }
    .ayah-card:hover {
        border-color:rgba(104,217,162,.22);
        box-shadow:0 1px 0 rgba(255,255,255,.04) inset, 0 18px 48px rgba(0,0,0,.16), 0 0 0 1px rgba(215,182,107,.05);
    }
    .ayah-card::after {
        content:"۞"; position:absolute; left:-.6rem; bottom:-1.3rem; font-family:"Amiri",serif;
        font-size:4.6rem; color:rgba(215,182,107,.03); pointer-events:none; z-index:-1;
    }
    .ayah-num {
        display:inline-flex; align-items:center; justify-content:center; min-width:32px; height:32px;
        border-radius:50%; color:var(--gold); font-size:.8rem; font-weight:700; margin-bottom:.85rem;
        background:linear-gradient(135deg,rgba(215,182,107,.14),rgba(215,182,107,.03));
        border:1px solid rgba(215,182,107,.4);
        box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 0 14px rgba(215,182,107,.08);
    }
    .ayah-arabic {
        font-family:"Amiri","Noto Naskh Arabic",serif; direction:rtl; text-align:right;
        font-size:2.05rem; line-height:2.15; color:#fbfcfb;
    }
    .translation-label {
        color:var(--accent); font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:800;
        margin-top:1.1rem; margin-bottom:.3rem; display:flex; align-items:center; gap:.4rem;
    }
    .translation-label::before { content:""; width:14px; height:1px; background:var(--accent); opacity:.5; }
    .translation { color:#dce5e1; font-size:1rem; line-height:1.8; direction:rtl; text-align:right; }
    .translation.en { direction:ltr; text-align:left; }
    .source { color:#7f8d87; font-size:.78rem; margin-top:1.5rem; text-align:center; letter-spacing:.01em; }
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
    return get_json(f"{BASE_URL}/surah")["data"]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_surah_data(surah: int, edition: str) -> List[dict]:
    return get_json(f"{BASE_URL}/surah/{surah}/{edition}")["data"]["ayahs"]


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def find_audio_edition(language: str) -> Optional[str]:
    """Find a real, professionally-recorded per-ayah audio edition for a
    translation language (e.g. a Qari reciting the Urdu or English meaning),
    if alquran.cloud has one. Restricted to type=versebyverse so we only ever
    get back an edition with one audio file per ayah — matching how the
    player below steps through ayahs — rather than a single whole-surah file.
    Returns None if no such recording exists for that language, so the
    caller can fall back to synthesized speech.
    """
    try:
        data = get_json(f"{BASE_URL}/edition?format=audio&language={language}&type=versebyverse")["data"]
    except Exception:
        return None
    return data[0]["identifier"] if data else None


# Friendly reciter names for the known recorded-translation editions, for the
# on-screen credit line. Falls back to a generic label for anything else.
AUDIO_EDITION_NAMES = {
    "ur.khan": "Shamshad Ali Khan",
    "en.walk": "Ibrahim Walk",
}


# -----------------------------------------------------------------------------
# Free neural spoken translation — generated inside Streamlit, no backend/API key
# -----------------------------------------------------------------------------
# edge-tts ships exactly four Urdu voices (ur-IN-SalmanNeural, ur-IN-GulNeural,
# ur-PK-AsadNeural, ur-PK-UzmaNeural) and, as of edge-tts 5+, Microsoft removed
# support for custom SSML — so there is no way to ask a single Urdu voice to
# pronounce one embedded word using different phonetics. No Urdu voice reliably
# nails Arabic-origin sacred proper nouns like اللہ, محمد and قرآن, because
# they're genuinely Arabic words, not Urdu ones.
#
# The real fix: synthesize those specific words/phrases with an actual Arabic
# voice, and everything else with the Urdu voice, then stitch the audio
# together. That is the only way to get correct pronunciation for the sacred
# terms without breaking the natural, correct Urdu pronunciation everything
# else already has.
URDU_VOICE = "ur-PK-AsadNeural"
URDU_VOICE_FALLBACK = "ur-IN-SalmanNeural"
URDU_RATE = "-10%"
URDU_PITCH = "-1Hz"
ARABIC_VOICE = "ar-SA-HamedNeural"
ARABIC_VOICE_FALLBACK = "ar-EG-ShakirNeural"
ARABIC_RATE = "-8%"
ARABIC_PITCH = "-1Hz"
EN_VOICE = "en-US-GuyNeural"
EN_RATE = "-8%"
EN_PITCH = "-1Hz"

# Arabic-origin sacred proper nouns / phrases, longest first so the regex
# below prefers the fuller phrase (e.g. "اللہ تعالیٰ" over bare "اللہ").
SACRED_ARABIC_TERMS = sorted(
    [
        "صلی اللہ علیہ وآلہ وسلم",
        "صلی اللہ علیہ وسلم",
        "رسول اللہ",
        "سبحان اللہ",
        "الحمد للہ",
        "ان شاء اللہ",
        "انشاء اللہ",
        "ماشاء اللہ",
        "استغفر اللہ",
        "بسم اللہ",
        "اللہ تعالیٰ",
        "اللہ تعالی",
        "اللہ کے",
        "اللہ کا",
        "اللہ کی",
        "اللہ سے",
        "اللہ نے",
        "اللہ کو",
        "اللہ ہی",
        "اللہ",
        "الله",
        "محمد مصطفیٰ",
        "محمد مصطفی",
        "حضرت محمد",
        "محمد",
        "قرآن",
        "قران",
        "ایمان",
        "کتاب",
        "آسمان",
    ],
    key=len,
    reverse=True,
)
_SACRED_PATTERN = re.compile("(" + "|".join(re.escape(t) for t in SACRED_ARABIC_TERMS) + ")")


def normalize_for_urdu_speech(text: str) -> str:
    """Create a TTS-only pronunciation layer while keeping displayed Urdu intact.

    The visible translation is never changed here — only the hidden copy sent
    to the speech engine. This only expands things that have no pronunciation
    of their own as written (the ﷺ glyph) and splits a couple of run-together
    spellings so word-boundary detection doesn't stumble. Ordinary words are
    left completely untouched, since they're already spelled unambiguously in
    plain Urdu.
    """
    replacements = {
        "ﷺ": "صلی اللہ علیہ وسلم",
        "ﷻ": "سبحانہ وتعالی",
        "الحمدللہ": "الحمد للہ",
        "ماشاءاللہ": "ماشاء اللہ",
        "انشاءاللہ": "انشاء اللہ",
        "استغفراللہ": "استغفر اللہ",
    }

    out = text.strip()
    for old, new in replacements.items():
        out = out.replace(old, new)

    # Normalize the rare "dagger alif" (superscript alef, U+0670) to a plain
    # alif, since this voice's text front-end doesn't reliably expand it.
    out = out.replace("\u0670", "ا")

    # Deliberate pauses at Urdu sentence boundaries.
    for mark in ["۔", "؟", "!", "؛", ":"]:
        out = out.replace(mark, mark + " ")
    out = out.replace("،", "، ")
    return " ".join(out.split())


def split_mixed_voice_segments(text: str) -> List[tuple]:
    """Split normalized Urdu text into ordered (segment, is_sacred_arabic) runs."""
    parts = [p for p in _SACRED_PATTERN.split(text) if p]
    return [(p, bool(_SACRED_PATTERN.fullmatch(p))) for p in parts]


async def _synthesize_once(text: str, voice: str, rate: str, pitch: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    data = buf.getvalue()
    if not data:
        raise RuntimeError(f"No audio returned by {voice}")
    return data


def _synthesize_with_fallback(text: str, voices: List[str], rate: str, pitch: str, attempts_per_voice: int = 3) -> bytes:
    # "No audio was received" from edge-tts is almost always a transient
    # network/rate-limit hiccup, not a real problem with the text — it shows
    # up more often now that a translation gets split into several separate
    # synthesis calls per ayah (one per Urdu run, one per Arabic-origin term).
    # Retrying the same voice a couple of times with a short backoff clears
    # it in the large majority of cases, before ever falling back to a
    # different voice or giving up.
    last_error: Optional[Exception] = None
    for voice in voices:
        for attempt in range(attempts_per_voice):
            try:
                return asyncio.run(_synthesize_once(text, voice, rate, pitch))
            except Exception as exc:
                last_error = exc
                if attempt < attempts_per_voice - 1:
                    time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"TTS failed for all configured voices: {last_error}")


@st.cache_data(ttl=60 * 60 * 24 * 30, show_spinner=False)
def synthesize_tts(text: str, language: str) -> bytes:
    if not text.strip():
        return b""

    if language != "ur":
        return _synthesize_with_fallback(text, [EN_VOICE], EN_RATE, EN_PITCH)

    normalized = normalize_for_urdu_speech(text)
    audio_chunks = []
    for segment, is_sacred in split_mixed_voice_segments(normalized):
        if not segment.strip():
            continue
        if is_sacred:
            audio_chunks.append(
                _synthesize_with_fallback(segment, [ARABIC_VOICE, ARABIC_VOICE_FALLBACK], ARABIC_RATE, ARABIC_PITCH)
            )
        else:
            audio_chunks.append(
                _synthesize_with_fallback(segment, [URDU_VOICE, URDU_VOICE_FALLBACK], URDU_RATE, URDU_PITCH)
            )
    return b"".join(audio_chunks)


def audio_data_url(audio_bytes: bytes) -> str:
    return "data:audio/mpeg;base64," + base64.b64encode(audio_bytes).decode("ascii")


# -----------------------------------------------------------------------------
# Hero
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-art" aria-hidden="true">
        <div class="hero-calligraphy">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
        <div class="hero-calligraphy-sub">وَقُل رَّبِّ زِدْنِي عِلْمًا</div>
        <div class="hero-orbit"></div>
        <div class="hero-crescent"></div>
      </div>
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
    <div class="glass-card surah-head" style="margin: 0.9rem 0 1.1rem;">
      <div><div class="surah-title">{html.escape(surah_name)}</div>
      <div class="surah-sub">{html.escape(arabic_name)} • {ayah_count} Ayahs</div></div>
      <div class="surah-number">Surah {surah_number}</div>
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
        translation_text_ayahs = None
        translation_audio_ayahs = None
        language = "none"
        audio_edition = None
        if playback_choice != "Arabic only":
            language = "ur" if "Urdu" in playback_choice else "en"
            # Translation TEXT always comes from a proper text edition. Audio
            # editions on alquran.cloud return the Arabic verse text in their
            # own "text" field (they're built as recitation audio, not a
            # translation-text source) — using it directly showed Arabic
            # under the Arabic instead of the Urdu/English meaning.
            text_edition = "ur.jalandhry" if language == "ur" else "en.sahih"
            translation_text_ayahs = get_surah_data(surah_number, text_edition)
            # Translation AUDIO: prefer a real, professionally-recorded
            # recitation over synthesized speech whenever alquran.cloud has one.
            audio_edition = find_audio_edition(language)
            if audio_edition:
                translation_audio_ayahs = get_surah_data(surah_number, audio_edition)
    except Exception as exc:
        st.error("Surah audio/text load nahi ho saka.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    tracks = []
    for i, ayah in enumerate(arabic_ayahs):
        translation = ""
        recorded_audio = ""
        if translation_text_ayahs and i < len(translation_text_ayahs):
            translation = translation_text_ayahs[i].get("text", "")
        if translation_audio_ayahs and i < len(translation_audio_ayahs):
            recorded_audio = translation_audio_ayahs[i].get("audio", "") or ""
        tracks.append({
            "ayah": ayah.get("numberInSurah", i + 1),
            "arabic": ayah.get("text", ""),
            "arabic_audio": ayah.get("audio", ""),
            "translation": translation,
            "translation_audio": recorded_audio,
        })

    # Fall back to neural TTS only for ayahs that still have no translation
    # audio (either this language has no recorded reciter at all, or the
    # recorded edition is missing a specific ayah). Ayahs that already got a
    # recorded URL above are left untouched — no synthesis, no wait, and no
    # pronunciation guesswork, since that's an actual Qari reading the meaning.
    missing = [t for t in tracks if t["translation"] and not t["translation_audio"]]
    if language != "none" and missing:
        progress = st.progress(0, text="Preparing spoken translation…")
        for i, track in enumerate(missing):
            try:
                audio_bytes = synthesize_tts(track["translation"], language)
                track["translation_audio"] = audio_data_url(audio_bytes) if audio_bytes else ""
            except Exception as exc:
                track["translation_audio"] = ""
                st.warning(f"Urdu/translation voice unavailable for Ayah {track['ayah']}. Arabic playback will continue.")
                st.caption(f"Technical detail: {exc}")
            progress.progress((i + 1) / len(missing), text=f"Preparing spoken translation • Ayah {i + 1}/{len(missing)}")
        progress.empty()

    if language == "none":
        translation_note = "Arabic recitation only."
    elif audio_edition and not missing:
        reciter = AUDIO_EDITION_NAMES.get(audio_edition, "a professional reciter")
        translation_note = f"Translation audio is a recorded recitation by {reciter}, not synthesized speech."
    elif audio_edition:
        reciter = AUDIO_EDITION_NAMES.get(audio_edition, "a professional reciter")
        translation_note = f"Translation audio is mostly a recorded recitation by {reciter}; a few ayahs use synthesized speech instead."
    else:
        translation_note = (
            "No recorded translation reciter is available for this language, so the translation is "
            "synthesized speech, with Arabic-origin sacred words read in a native Arabic voice."
        )

    payload = json.dumps(tracks, ensure_ascii=False, separators=(",", ":"))
    language_json = json.dumps(language)

    player_html = f"""
    <!doctype html>
    <html><head><meta charset="utf-8"><style>
      * {{ box-sizing:border-box; }}
      body {{ margin:0; font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif; background:transparent; color:#f5f7f6; }}
      .shell {{
        border-radius:26px; padding:20px 20px 18px; position:relative; overflow:visible;
        background:linear-gradient(135deg,rgba(255,255,255,.11),rgba(255,255,255,.04));
        backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
        box-shadow:0 24px 64px rgba(0,0,0,.22), 0 1px 0 rgba(255,255,255,.06) inset;
        border:1px solid rgba(255,255,255,.12);
      }}
      .shell::before {{
        content:""; position:absolute; inset:0; border-radius:inherit; padding:1px; z-index:-1;
        background:linear-gradient(135deg, rgba(215,182,107,.35), rgba(255,255,255,.02) 45%, rgba(104,217,162,.28));
        -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite:xor; mask-composite:exclude; pointer-events:none;
      }}
      .top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
      .brand {{ display:flex; align-items:center; gap:6px; color:#67d7a0; font-weight:800; font-size:11.5px; letter-spacing:.14em; text-transform:uppercase; }}
      .brand::before {{ content:"☾"; font-size:13px; color:#e3c07f; }}
      .status {{
        color:#bfe9d4; font-size:11.5px; font-weight:700; padding:5px 12px; border-radius:999px;
        background:rgba(104,217,162,.1); border:1px solid rgba(104,217,162,.22);
      }}
      .verse {{
        font-family:"Amiri","Noto Naskh Arabic",serif; direction:rtl; text-align:right;
        font-size:29px; line-height:1.95; margin:18px 0 10px; color:#fbfcfb;
      }}
      .translation {{ direction:rtl; text-align:right; color:#d8e1dd; font-size:15px; line-height:1.75; min-height:24px; }}
      .translation.en {{ direction:ltr; text-align:left; }}
      .meta {{ color:#8c9893; font-size:12px; margin-top:10px; }}
      .controls {{ display:flex; align-items:center; gap:10px; margin-top:16px; flex-wrap:wrap; }}
      button {{
        appearance:none; border:1px solid rgba(103,215,160,.28);
        background:linear-gradient(135deg, rgba(103,215,160,.2), rgba(215,182,107,.1));
        color:#eafcf2; padding:11px 18px; border-radius:999px; font-weight:800; font-size:13.5px; cursor:pointer;
        transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
      }}
      button:hover {{ transform:translateY(-1px); border-color:rgba(103,215,160,.5); box-shadow:0 8px 22px rgba(103,215,160,.14); }}
      button:active {{ transform:translateY(0); }}
      button.secondary {{ border-color:rgba(255,255,255,.12); background:rgba(255,255,255,.06); color:#d5ddda; }}
      .progress {{ height:6px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; margin-top:18px; }}
      .bar {{ height:100%; width:0; background:linear-gradient(90deg,#67d7a0,#e3c07f); transition:width .18s linear; box-shadow:0 0 12px rgba(103,215,160,.4); }}
      .popup {{
        position:absolute; right:18px; bottom:-18px; display:flex; align-items:center; gap:9px; max-width:calc(100% - 36px);
        padding:9px 14px; border-radius:999px; border:1px solid rgba(255,255,255,.15); background:rgba(7,18,15,.92);
        backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); box-shadow:0 16px 40px rgba(0,0,0,.34);
        color:#ecf6f1; font-size:12px; font-weight:600; opacity:0; transform:translateY(8px); pointer-events:none;
        transition:opacity .25s ease,transform .25s ease; z-index:20;
      }}
      .popup.show {{ opacity:1; transform:translateY(0); }}
      .dot {{ width:8px; height:8px; border-radius:50%; background:#67d7a0; box-shadow:0 0 14px rgba(103,215,160,.75); flex:0 0 auto; }}
      .note {{ color:#77847f; font-size:11px; margin-top:14px; line-height:1.5; }}
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
        <div class="note">{html.escape(translation_note)}</div>
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
    components.html(player_html, height=415)
    if language != "none" and audio_edition:
        source_line = (
            f"Arabic recitation: Alafasy • Quran text & translation: alquran.cloud • "
            f"Translation audio: {html.escape(AUDIO_EDITION_NAMES.get(audio_edition, audio_edition))} (recorded recitation)."
        )
    elif language != "none":
        source_line = (
            "Arabic recitation: Alafasy • Quran text & translation: alquran.cloud • "
            "Translation audio: free Edge neural TTS, with sacred Arabic-origin terms voiced in Arabic."
        )
    else:
        source_line = "Arabic recitation: Alafasy • Quran text: alquran.cloud."
    st.markdown(f'<div class="source">{source_line}</div>', unsafe_allow_html=True)
