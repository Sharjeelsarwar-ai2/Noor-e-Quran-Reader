import asyncio
import base64
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# ---------- Theme ----------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #07110e;
        --panel: rgba(255,255,255,.065);
        --panel-strong: rgba(255,255,255,.09);
        --border: rgba(255,255,255,.11);
        --text: #f5f7f6;
        --muted: #a8b3af;
        --accent: #67d7a0;
        --accent-2: #c9f7de;
        --gold: #d6b36a;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 7% 0%, rgba(74,190,132,.12), transparent 28%),
            radial-gradient(circle at 95% 7%, rgba(214,179,106,.09), transparent 24%),
            var(--bg);
        color: var(--text);
    }

    /* Remove Streamlit's upper chrome so the app starts cleanly at the hero. */
    header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 0.35rem;
        padding-bottom: 5rem;
    }

    /* Hero: watermark is behind the content, never masking the title. */
    .hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        padding: 2.25rem 2.4rem;
        border: 1px solid var(--border);
        border-radius: 30px;
        background: linear-gradient(135deg, rgba(255,255,255,.085), rgba(255,255,255,.03));
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        box-shadow: 0 24px 80px rgba(0,0,0,.22);
        margin-bottom: 1.15rem;
    }

    .hero::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 82% 25%, rgba(103,215,160,.08), transparent 25%),
            linear-gradient(115deg, transparent 40%, rgba(255,255,255,.025), transparent 70%);
        z-index: -2;
        pointer-events: none;
    }

    .hero::after {
        content: "﷽";
        position: absolute;
        right: -1.5rem;
        top: -.9rem;
        font-family: "Amiri", serif;
        font-size: clamp(4.5rem, 11vw, 8.2rem);
        line-height: 1;
        white-space: nowrap;
        color: rgba(255,255,255,.026);
        transform: rotate(-1deg);
        z-index: -1;
        pointer-events: none;
        user-select: none;
    }

    .hero > * {
        position: relative;
        z-index: 1;
    }

    .eyebrow {
        font-size: .76rem;
        letter-spacing: .16em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 800;
        margin-bottom: .5rem;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(2.3rem, 4.5vw, 3.55rem);
        line-height: 1;
        letter-spacing: -.04em;
    }

    .hero p {
        color: var(--muted);
        margin: .85rem 0 0;
        max-width: 760px;
        font-size: 1rem;
        line-height: 1.7;
    }

    .glass-card {
        border: 1px solid var(--border);
        border-radius: 24px;
        background: var(--panel);
        padding: 1.2rem;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow: 0 14px 45px rgba(0,0,0,.14);
    }

    .surah-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: .4rem 0 1rem;
    }

    .surah-title {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -.02em;
    }

    .surah-sub {
        color: var(--muted);
        font-size: .9rem;
    }

    .ayah-card {
        border: 1px solid rgba(255,255,255,.09);
        border-radius: 22px;
        padding: 1.25rem 1.35rem;
        margin: .95rem 0;
        background: rgba(255,255,255,.042);
        transition: transform .2s ease, border-color .2s ease, background .2s ease;
    }

    .ayah-card:hover {
        transform: translateY(-1px);
        border-color: rgba(103,215,160,.24);
        background: rgba(255,255,255,.06);
    }

    .ayah-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 31px;
        height: 31px;
        border-radius: 50%;
        border: 1px solid rgba(214,179,106,.35);
        color: var(--gold);
        font-size: .8rem;
        margin-bottom: .7rem;
    }

    .ayah-arabic {
        font-family: "Amiri", "Noto Naskh Arabic", serif;
        direction: rtl;
        text-align: right;
        font-size: 2rem;
        line-height: 2.05;
        color: #fbfcfb;
    }

    .translation-label {
        color: var(--accent);
        font-size: .76rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        font-weight: 800;
        margin-top: .95rem;
        margin-bottom: .25rem;
    }

    .translation {
        color: #dce4e1;
        font-size: 1rem;
        line-height: 1.75;
        direction: rtl;
        text-align: right;
    }

    .translation.en {
        direction: ltr;
        text-align: left;
    }

    .source {
        color: #7f8b86;
        font-size: .78rem;
        margin-top: 1.35rem;
        text-align: center;
    }

    div[data-baseweb="select"] > div {
        background: rgba(255,255,255,.055);
        border: 1px solid rgba(255,255,255,.10);
        border-radius: 16px;
    }

    .stButton > button {
        border-radius: 14px;
        border: 1px solid rgba(103,215,160,.22);
        background: rgba(103,215,160,.11);
        color: #eafcf2;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Data helpers ----------

@st.cache_data(ttl=60 * 60 * 24)
def get_json(url: str, timeout: int = 20) -> dict:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Noor-Quran-App/1.1"},
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 200:
        raise RuntimeError(data.get("status", "API request failed"))
    return data


@st.cache_data(ttl=60 * 60 * 24)
def get_surah_list():
    return get_json(f"{BASE_URL}/surah", 15)["data"]


@st.cache_data(ttl=60 * 60 * 24)
def get_surah_data(surah: int, edition: str):
    return get_json(f"{BASE_URL}/surah/{surah}/{edition}", 20)["data"]["ayahs"]


def split_for_tts(text: str, max_chars: int = 175):
    """Keep each remote TTS request short enough to be reliable."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    # Prefer sentence/punctuation boundaries, then words.
    pieces = re.split(r"(?<=[۔!?؛:])\s+", text)
    if len(pieces) == 1:
        pieces = text.split()

    for piece in pieces:
        if not piece:
            continue
        candidate = piece if not current else f"{current} {piece}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(piece) <= max_chars:
                current = piece
            else:
                words = piece.split()
                current = ""
                for word in words:
                    candidate = word if not current else f"{current} {word}"
                    if len(candidate) <= max_chars:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        current = word
    if current:
        chunks.append(current)
    return chunks


@st.cache_data(ttl=60 * 60 * 24 * 30, show_spinner=False)
def make_tts_data_url(text: str, lang: str) -> str:
    """Generate a calm neural spoken translation and cache it per ayah/chunk.

    Uses Microsoft Edge's free neural TTS endpoint through edge-tts.
    No API key is required. Urdu uses a mature male Pakistan voice.
    """
    if not text:
        return ""

    voice = "ur-PK-AsadNeural" if lang == "ur" else "en-US-GuyNeural"
    rate = "-10%" if lang == "ur" else "-6%"
    pitch = "-2Hz" if lang == "ur" else "-1Hz"

    async def synthesize() -> bytes:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        data = bytearray()
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                data.extend(chunk["data"])
        return bytes(data)

    audio_bytes = asyncio.run(synthesize())
    if not audio_bytes:
        return ""

    encoded = base64.b64encode(audio_bytes).decode("ascii")
    return f"data:audio/mpeg;base64,{encoded}"


def make_tts_batch(texts: list[str], lang: str, workers: int = 8) -> list[str]:
    """Generate translation audio concurrently; cached items return immediately."""
    if not texts:
        return []

    results = [""] * len(texts)
    jobs = [(i, t) for i, t in enumerate(texts) if t]
    if not jobs:
        return results

    with ThreadPoolExecutor(max_workers=min(workers, len(jobs))) as executor:
        future_map = {
            executor.submit(make_tts_data_url, text, lang): i
            for i, text in jobs
        }
        for future in as_completed(future_map):
            i = future_map[future]
            try:
                results[i] = future.result()
            except Exception:
                results[i] = ""
    return results


# ---------- Header ----------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Read • Reflect • Listen</div>
        <h1>Noor</h1>
        <p>A clean, distraction-free Quran experience with Arabic recitation and spoken Urdu translation — verse by verse.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- Load surahs ----------

try:
    surahs = get_surah_list()
except Exception as exc:
    st.error("Quran data load nahi ho saka. Internet connection ya API availability check karein.")
    st.caption(f"Technical detail: {exc}")
    st.stop()

left, right = st.columns([2.2, 1], gap="large")

with left:
    surah_labels = [
        f"{s['number']:02d}  {s['englishName']} — {s['name']}"
        for s in surahs
    ]
    idx = st.selectbox(
        "Surah",
        range(len(surahs)),
        format_func=lambda i: surah_labels[i],
        label_visibility="collapsed",
    )
    selected_surah = surahs[idx]

with right:
    mode = st.radio(
        "Mode",
        ["📖 Read", "🔊 Listen"],
        horizontal=True,
        label_visibility="collapsed",
    )

surah_number = selected_surah["number"]
surah_name = selected_surah["englishName"]
arabic_name = selected_surah["name"]
ayah_count = selected_surah.get("numberOfAyahs", 0)

st.markdown(
    f"""
    <div class="glass-card surah-head">
        <div>
            <div class="surah-title">{html.escape(surah_name)}</div>
            <div class="surah-sub">{html.escape(arabic_name)} • {ayah_count} Ayahs</div>
        </div>
        <div class="surah-sub">Surah {surah_number}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- Read mode ----------

if mode == "📖 Read":
    translation_choice = st.radio(
        "Translation",
        ["Arabic only", "Arabic + Urdu", "Arabic + English"],
        horizontal=True,
    )

    try:
        arabic_ayahs = get_surah_data(surah_number, "quran-uthmani")
        urdu_ayahs = (
            get_surah_data(surah_number, "ur.jalandhry")
            if "Urdu" in translation_choice
            else None
        )
        english_ayahs = (
            get_surah_data(surah_number, "en.sahih")
            if "English" in translation_choice
            else None
        )
    except Exception as exc:
        st.error("Surah load nahi ho saki.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    for i, ayah in enumerate(arabic_ayahs):
        urdu_text = urdu_ayahs[i]["text"] if urdu_ayahs and i < len(urdu_ayahs) else None
        english_text = english_ayahs[i]["text"] if english_ayahs and i < len(english_ayahs) else None

        card_parts = [
            '<div class="ayah-card">',
            f'<div class="ayah-num">{ayah["numberInSurah"]}</div>',
            f'<div class="ayah-arabic">{html.escape(ayah["text"])}</div>',
        ]

        if urdu_text:
            card_parts += [
                '<div class="translation-label">Urdu</div>',
                f'<div class="translation">{html.escape(urdu_text)}</div>',
            ]

        if english_text:
            card_parts += [
                '<div class="translation-label">English</div>',
                f'<div class="translation en">{html.escape(english_text)}</div>',
            ]

        card_parts.append("</div>")
        st.markdown("".join(card_parts), unsafe_allow_html=True)


# ---------- Listen mode ----------

else:
    playback_choice = st.radio(
        "Playback",
        ["Arabic + Urdu live translation", "Arabic + English live translation", "Arabic only"],
        horizontal=True,
    )

    try:
        # Arabic recitation is always the authentic recorded audio.
        arabic_ayahs = get_surah_data(surah_number, "ar.alafasy")
    except Exception as exc:
        st.error("Arabic recitation load nahi hui.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    translation_language = None
    translation_ayahs = None

    if playback_choice != "Arabic only":
        translation_language = "ur" if "Urdu" in playback_choice else "en"
        translation_edition = "ur.jalandhry" if translation_language == "ur" else "en.sahih"
        try:
            translation_ayahs = get_surah_data(surah_number, translation_edition)
        except Exception as exc:
            st.warning("Translation text load nahi ho saki. Arabic recitation phir bhi chalegi.")
            st.caption(f"Technical detail: {exc}")

    # Build all text tracks first. This is fast: only two API calls for a full Surah.
    # Urdu/English voice is generated concurrently and cached per ayah/chunk.
    translation_texts = []
    for i, ayah in enumerate(arabic_ayahs):
        text = ""
        if translation_ayahs and i < len(translation_ayahs):
            text = translation_ayahs[i].get("text", "")
        translation_texts.append(text)

    tts_by_ayah = [[] for _ in arabic_ayahs]
    if translation_language and any(translation_texts):
        chunk_records = []
        for i, text in enumerate(translation_texts):
            if not text:
                continue
            for chunk in split_for_tts(text):
                chunk_records.append((i, chunk))

        if chunk_records:
            with st.spinner("Preparing translation voice…"):
                urls = make_tts_batch(
                    [chunk for _, chunk in chunk_records],
                    translation_language,
                    workers=10,
                )
            for (ayah_index, chunk), url in zip(chunk_records, urls):
                if url:
                    tts_by_ayah[ayah_index].append({"text": chunk, "url": url})

    tracks = []
    for i, ayah in enumerate(arabic_ayahs):
        tracks.append(
            {
                "audio": ayah.get("audio", ""),
                "ayah": ayah.get("numberInSurah", i + 1),
                "arabic": ayah.get("text", ""),
                "translation": translation_texts[i],
                "tts": tts_by_ayah[i],
            }
        )

    payload = json.dumps(tracks, ensure_ascii=False)
    language_json = json.dumps(translation_language or "none")

    component_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: transparent;
          color: #f5f7f6;
        }}
        .player-shell {{
          border: 1px solid rgba(255,255,255,.11);
          border-radius: 24px;
          background: linear-gradient(135deg, rgba(255,255,255,.10), rgba(255,255,255,.045));
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
          padding: 18px;
          box-shadow: 0 20px 55px rgba(0,0,0,.18);
          position: relative;
          overflow: visible;
        }}
        .topline {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }}
        .brand {{
          color: #67d7a0;
          font-weight: 800;
          font-size: 12px;
          letter-spacing: .12em;
          text-transform: uppercase;
        }}
        .status {{ color: #9daaa5; font-size: 12px; }}
        .verse {{
          font-family: "Amiri", "Noto Naskh Arabic", serif;
          direction: rtl;
          text-align: right;
          font-size: 28px;
          line-height: 1.9;
          margin: 14px 0 8px;
        }}
        .translation {{
          direction: rtl;
          text-align: right;
          color: #d8e1dd;
          font-size: 15px;
          line-height: 1.7;
          min-height: 24px;
        }}
        .translation.en {{ direction: ltr; text-align: left; }}
        .meta {{ color: #8c9893; font-size: 12px; margin-top: 8px; }}
        .controls {{
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 14px;
          flex-wrap: wrap;
        }}
        button {{
          appearance: none;
          border: 1px solid rgba(103,215,160,.22);
          background: rgba(103,215,160,.12);
          color: #eafcf2;
          padding: 10px 15px;
          border-radius: 999px;
          font-weight: 800;
          cursor: pointer;
        }}
        button.secondary {{
          border-color: rgba(255,255,255,.10);
          background: rgba(255,255,255,.055);
          color: #d5ddda;
        }}
        .progress {{
          height: 5px;
          border-radius: 999px;
          background: rgba(255,255,255,.08);
          overflow: hidden;
          margin-top: 15px;
        }}
        .bar {{
          height: 100%;
          width: 0%;
          background: linear-gradient(90deg, #67d7a0, #d6b36a);
          transition: width .18s linear;
        }}
        .popup {{
          position: absolute;
          right: 18px;
          bottom: -18px;
          display: flex;
          align-items: center;
          gap: 9px;
          max-width: calc(100% - 36px);
          padding: 9px 13px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,.14);
          background: rgba(10, 23, 19, .88);
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
          box-shadow: 0 14px 36px rgba(0,0,0,.3);
          color: #ecf6f1;
          font-size: 12px;
          opacity: 0;
          transform: translateY(8px);
          pointer-events: none;
          transition: opacity .25s ease, transform .25s ease;
          z-index: 20;
        }}
        .popup.show {{ opacity: 1; transform: translateY(0); }}
        .dot {{
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #67d7a0;
          box-shadow: 0 0 14px rgba(103,215,160,.75);
          flex: 0 0 auto;
        }}
        .small-note {{ color:#77847f; font-size:11px; margin-top:12px; }}
      </style>
    </head>
    <body>
      <div class="player-shell">
        <div class="topline">
          <div class="brand">Noor • Recitation</div>
          <div class="status" id="counter">Ready</div>
        </div>

        <div class="verse" id="verse">Press Start to begin</div>
        <div class="translation" id="translation"></div>
        <div class="meta" id="meta">Arabic recitation → spoken translation</div>

        <div class="controls">
          <button id="start">▶ Start</button>
          <button id="pause" class="secondary">Ⅱ Pause</button>
          <button id="stop" class="secondary">■ Stop</button>
        </div>

        <div class="progress"><div class="bar" id="bar"></div></div>
        <div class="small-note">Arabic recitation is followed automatically by a calm male spoken translation of the same ayah.</div>

        <div class="popup" id="popup">
          <span class="dot"></span>
          <span id="popupText">Now playing</span>
        </div>
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
        let running = false;
        let phase = "arabic";
        let ttsIndex = 0;
        let ttsRequest = 0;

        function showPopup(message) {{
          popupText.textContent = message;
          popup.classList.add("show");
          clearTimeout(window.popupTimer);
          window.popupTimer = setTimeout(() => popup.classList.remove("show"), 4200);
        }}

        function updateUI(track) {{
          verse.textContent = track.arabic || "";
          translation.textContent = track.translation || "";
          if (language === "en") translation.classList.add("en");
          else translation.classList.remove("en");
          counter.textContent = `Ayah ${{track.ayah}} / ${{tracks.length}}`;
          const base = (index / Math.max(tracks.length, 1)) * 100;
          bar.style.width = `${{base}}%`;
        }}

        function resetAudio() {{
          audio.pause();
          audio.removeAttribute("src");
          audio.load();
        }}

        function nextAyah() {{
          if (!running) return;
          index += 1;
          ttsIndex = 0;
          phase = "arabic";
          if (index >= tracks.length) {{
            running = false;
            counter.textContent = "Completed";
            bar.style.width = "100%";
            showPopup("Surah completed");
            meta.textContent = "Alhamdulillah • Surah completed";
            return;
          }}
          playArabic();
        }}

        function playArabic() {{
          if (!running) return;
          phase = "arabic";
          const track = tracks[index];
          updateUI(track);
          resetAudio();
          audio.src = track.audio;
          audio.load();
          meta.textContent = language === "none"
            ? "Arabic recitation"
            : "Arabic recitation • Urdu meaning follows automatically";
          showPopup(`Ayah ${{track.ayah}} • Arabic recitation`);
          const p = audio.play();
          if (p && p.catch) p.catch(() => showPopup("Press Start to allow audio playback"));
        }}

        function playTranslationChunk() {{
          if (!running) return;
          const track = tracks[index];
          const chunks = track.tts || [];

          if (language === "none" || !chunks.length) {{
            nextAyah();
            return;
          }}

          if (ttsIndex >= chunks.length) {{
            nextAyah();
            return;
          }}

          phase = "translation";
          const requestId = ++ttsRequest;
          const chunk = chunks[ttsIndex];
          resetAudio();
          audio.src = chunk.url;
          audio.load();
          meta.textContent = language === "ur"
            ? "Arabic complete • speaking Urdu meaning"
            : "Arabic complete • speaking English meaning";
          showPopup(language === "ur" ? `Ayah ${{track.ayah}} • Urdu meaning` : `Ayah ${{track.ayah}} • English meaning`);

          const p = audio.play();
          if (p && p.catch) p.catch(() => {{
            // Some browsers block remote TTS autoplay after a failed media load.
            // Try the same request once more while the user gesture/session is active.
            if (requestId === ttsRequest && running) {{
              setTimeout(() => audio.play().catch(() => showPopup("Translation voice could not start")), 80);
            }}
          }});
        }}

        document.getElementById("start").addEventListener("click", () => {{
          running = true;
          index = 0;
          ttsIndex = 0;
          ttsRequest++;
          playArabic();
        }});

        document.getElementById("pause").addEventListener("click", () => {{
          if (!running) return;
          if (!audio.paused) {{
            audio.pause();
            showPopup("Paused");
            meta.textContent = "Playback paused";
          }} else {{
            audio.play().then(() => showPopup(phase === "arabic" ? "Arabic resumed" : "Translation resumed")).catch(() => showPopup("Press Start to resume audio"));
          }}
        }});

        document.getElementById("stop").addEventListener("click", () => {{
          running = false;
          ttsRequest++;
          resetAudio();
          index = 0;
          ttsIndex = 0;
          phase = "arabic";
          bar.style.width = "0%";
          counter.textContent = "Ready";
          verse.textContent = "Press Start to begin";
          translation.textContent = "";
          meta.textContent = "Arabic recitation → spoken translation";
          popup.classList.remove("show");
        }});

        audio.addEventListener("timeupdate", () => {{
          if (!audio.duration || !tracks.length) return;
          const completed = (index / tracks.length) * 100;
          const inTrack = (audio.currentTime / audio.duration) * (100 / tracks.length);
          bar.style.width = `${{Math.min(completed + inTrack, 100)}}%`;
        }});

        audio.addEventListener("ended", () => {{
          if (!running) return;
          if (phase === "arabic") {{
            ttsIndex = 0;
            playTranslationChunk();
          }} else {{
            ttsIndex += 1;
            playTranslationChunk();
          }}
        }});

        audio.addEventListener("error", () => {{
          if (!running) return;
          if (phase === "translation") {{
            // Skip a failed TTS chunk rather than getting stuck.
            ttsIndex += 1;
            playTranslationChunk();
          }} else {{
            showPopup("Arabic audio could not load");
          }}
        }});
      </script>
    </body>
    </html>
    """

    components.html(component_html, height=410)

    st.markdown(
        '<div class="source">Arabic recitation: Alafasy • Quran text & translation: alquran.cloud • Spoken translation: Edge neural TTS (cached per ayah).</div>',
        unsafe_allow_html=True,
    )
