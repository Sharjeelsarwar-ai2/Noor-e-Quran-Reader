import html
import json

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap');

    :root {
        --bg: #07110e;
        --panel: rgba(255,255,255,.065);
        --panel-strong: rgba(255,255,255,.095);
        --border: rgba(255,255,255,.11);
        --text: #f5f7f6;
        --muted: #a8b3af;
        --accent: #67d7a0;
        --accent-2: #c9f7de;
        --gold: #d6b36a;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 10% 0%, rgba(74, 190, 132, .12), transparent 28%),
            radial-gradient(circle at 92% 8%, rgba(214, 179, 106, .10), transparent 24%),
            var(--bg);
        color: var(--text);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.2rem 2.4rem;
        border: 1px solid var(--border);
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(255,255,255,.09), rgba(255,255,255,.035));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 22px 70px rgba(0,0,0,.20);
        margin-bottom: 1.2rem;
    }

    .hero:after {
        content: "﷽";
        position: absolute;
        right: 2rem;
        top: 0.7rem;
        font-family: "Amiri", serif;
        font-size: 5.5rem;
        color: rgba(255,255,255,.055);
        pointer-events: none;
    }

    .eyebrow {
        font-size: .78rem;
        letter-spacing: .16em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 700;
        margin-bottom: .4rem;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1.05;
    }

    .hero p {
        color: var(--muted);
        margin: .8rem 0 0;
        max-width: 720px;
        font-size: 1rem;
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
        font-weight: 700;
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
        background: rgba(255,255,255,.045);
        transition: .2s ease;
    }

    .ayah-card:hover {
        transform: translateY(-1px);
        border-color: rgba(103,215,160,.24);
        background: rgba(255,255,255,.065);
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
        font-family: "Amiri", serif;
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
        font-weight: 700;
        margin-top: .9rem;
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
        margin-top: 1.4rem;
        text-align: center;
    }

    [data-testid="stSelectbox"] > div,
    [data-testid="stRadio"] > div {
        border-radius: 16px;
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
        font-weight: 600;
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
        headers={"User-Agent": "Noor-Quran-App/1.0"},
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


@st.cache_data(ttl=60 * 60 * 24)
def find_audio_edition(language: str):
    data = get_json(
        f"{BASE_URL}/edition?format=audio&language={language}",
        15,
    )["data"]
    return data[0]["identifier"] if data else None


# ---------- Header ----------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Read • Reflect • Listen</div>
        <h1>Noor</h1>
        <p>A clean, distraction-free Quran experience with Arabic recitation and Urdu translation playback.</p>
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
        urdu_text = urdu_ayahs[i]["text"] if urdu_ayahs else None
        english_text = english_ayahs[i]["text"] if english_ayahs else None

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
        arabic_ayahs = get_surah_data(surah_number, "ar.alafasy")
    except Exception as exc:
        st.error("Arabic recitation load nahi hui.")
        st.caption(f"Technical detail: {exc}")
        st.stop()

    translation_ayahs = None
    translation_language = None

    if playback_choice != "Arabic only":
        translation_language = "ur" if "Urdu" in playback_choice else "en"

        try:
            translation_edition = find_audio_edition(translation_language)
        except Exception:
            translation_edition = None

        if translation_edition:
            try:
                translation_ayahs = get_surah_data(
                    surah_number,
                    translation_edition,
                )
            except Exception:
                translation_ayahs = None

    # Text is always loaded for the live browser translation feature.
    if translation_ayahs is None and playback_choice != "Arabic only":
        try:
            text_edition = (
                "ur.jalandhry"
                if translation_language == "ur"
                else "en.sahih"
            )
            translation_ayahs = get_surah_data(surah_number, text_edition)
        except Exception as exc:
            st.warning("Translation text load nahi ho saki. Arabic recitation phir bhi chalegi.")
            st.caption(f"Technical detail: {exc}")

    tracks = []
    for i, ayah in enumerate(arabic_ayahs):
        track = {
            "audio": ayah["audio"],
            "ayah": ayah["numberInSurah"],
            "arabic": ayah["text"],
            "translation": (
                translation_ayahs[i]["text"]
                if translation_ayahs and i < len(translation_ayahs)
                else ""
            ),
        }
        tracks.append(track)

    payload = json.dumps(tracks, ensure_ascii=False)

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
        }}
        .topline {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }}
        .brand {{
          color: #67d7a0;
          font-weight: 700;
          font-size: 12px;
          letter-spacing: .12em;
          text-transform: uppercase;
        }}
        .status {{
          color: #9daaa5;
          font-size: 12px;
        }}
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
        .translation.en {{
          direction: ltr;
          text-align: left;
        }}
        .meta {{
          color: #8c9893;
          font-size: 12px;
          margin-top: 8px;
        }}
        .controls {{
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 14px;
        }}
        button {{
          appearance: none;
          border: 1px solid rgba(103,215,160,.22);
          background: rgba(103,215,160,.12);
          color: #eafcf2;
          padding: 10px 15px;
          border-radius: 999px;
          font-weight: 700;
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
          transition: width .2s linear;
        }}

        /* Beautiful floating popup pill */
        .popup {{
          position: absolute;
          right: 18px;
          bottom: 18px;
          display: flex;
          align-items: center;
          gap: 9px;
          max-width: calc(100% - 36px);
          padding: 9px 13px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,.13);
          background: rgba(12, 25, 21, .78);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          box-shadow: 0 12px 30px rgba(0,0,0,.25);
          color: #ecf6f1;
          font-size: 12px;
          opacity: 0;
          transform: translateY(8px);
          pointer-events: none;
          transition: .25s ease;
        }}
        .popup.show {{
          opacity: 1;
          transform: translateY(0);
        }}
        .dot {{
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #67d7a0;
          box-shadow: 0 0 14px rgba(103,215,160,.75);
          flex: 0 0 auto;
        }}
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
        <div class="meta" id="meta">Arabic recitation → translation</div>

        <div class="controls">
          <button id="start">▶ Start</button>
          <button id="pause" class="secondary">Ⅱ Pause</button>
          <button id="stop" class="secondary">■ Stop</button>
        </div>

        <div class="progress"><div class="bar" id="bar"></div></div>

        <div class="popup" id="popup">
          <span class="dot"></span>
          <span id="popupText">Now playing</span>
        </div>
      </div>

      <audio id="audio" preload="auto"></audio>

      <script>
        const tracks = {payload};
        const language = {json.dumps(translation_language or "none")};

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

        function showPopup(message) {{
          popupText.textContent = message;
          popup.classList.add("show");
          clearTimeout(window.popupTimer);
          window.popupTimer = setTimeout(() => popup.classList.remove("show"), 3600);
        }}

        function stopSpeech() {{
          if ("speechSynthesis" in window) {{
            speechSynthesis.cancel();
          }}
        }}

        function speakTranslation(text) {{
          if (!text || language === "none") {{
            return;
          }}

          if (!("speechSynthesis" in window)) {{
            showPopup("Browser Urdu/English speech is not supported");
            return;
          }}

          stopSpeech();

          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = language === "ur" ? "ur-PK" : "en-US";
          utterance.rate = language === "ur" ? 0.9 : 0.95;
          utterance.pitch = 1.0;
          utterance.volume = 1.0;

          const voices = speechSynthesis.getVoices();
          const preferred = voices.find(v =>
            v.lang.toLowerCase().startsWith(language === "ur" ? "ur" : "en")
          );

          if (preferred) {{
            utterance.voice = preferred;
          }}

          showPopup(language === "ur" ? "Urdu translation" : "English translation");
          meta.textContent = language === "ur"
            ? "Arabic complete • speaking Urdu translation"
            : "Arabic complete • speaking English translation";

          utterance.onend = () => {{
            index++;
            playTrack();
          }};

          utterance.onerror = () => {{
            index++;
            playTrack();
          }};

          speechSynthesis.speak(utterance);
        }}

        function updateUI(track) {{
          verse.textContent = track.arabic || "";
          translation.textContent = track.translation || "";
          if (language === "en") {{
            translation.classList.add("en");
          }} else {{
            translation.classList.remove("en");
          }}

          counter.textContent = `Ayah ${{track.ayah}} / ${{tracks.length}}`;
          bar.style.width = `${{(index / Math.max(tracks.length, 1)) * 100}}%`;

          showPopup(`Ayah ${{track.ayah}} • Arabic recitation`);
          meta.textContent = language === "none"
            ? "Arabic recitation"
            : "Arabic recitation • translation follows automatically";
        }}

        function playTrack() {{
          if (index >= tracks.length) {{
            running = false;
            counter.textContent = "Completed";
            bar.style.width = "100%";
            showPopup("Surah completed");
            meta.textContent = "Alhamdulillah • Surah completed";
            return;
          }}

          const track = tracks[index];
          updateUI(track);
          audio.src = track.audio;
          audio.currentTime = 0;

          const p = audio.play();
          if (p && p.catch) {{
            p.catch(() => showPopup("Press Start to allow audio playback"));
          }}
        }}

        document.getElementById("start").addEventListener("click", () => {{
          stopSpeech();
          index = 0;
          running = true;
          playTrack();
        }});

        document.getElementById("pause").addEventListener("click", () => {{
          if (!audio.paused) {{
            audio.pause();
            stopSpeech();
            showPopup("Paused");
            meta.textContent = "Playback paused";
          }} else if (running && audio.src) {{
            audio.play();
            showPopup("Resumed");
          }}
        }});

        document.getElementById("stop").addEventListener("click", () => {{
          running = false;
          audio.pause();
          audio.currentTime = 0;
          stopSpeech();
          index = 0;
          bar.style.width = "0%";
          counter.textContent = "Ready";
          verse.textContent = "Press Start to begin";
          translation.textContent = "";
          meta.textContent = "Arabic recitation → translation";
          popup.classList.remove("show");
        }});

        audio.addEventListener("timeupdate", () => {{
          if (!audio.duration) return;
          const start = (index / tracks.length) * 100;
          const width = (audio.currentTime / audio.duration) * (100 / tracks.length);
          bar.style.width = `${{Math.min(start + width, 100)}}%`;
        }});

        audio.addEventListener("ended", () => {{
          if (!running) return;
          if (language === "none") {{
            index++;
            playTrack();
          }} else {{
            speakTranslation(tracks[index].translation || "");
          }}
        }});

        window.speechSynthesis?.addEventListener?.("voiceschanged", () => {{}});
      </script>
    </body>
    </html>
    """

    components.html(component_html, height=360)

    st.markdown(
        '<div class="source">Arabic recitation: Alafasy • Text & translation data: alquran.cloud API • Urdu/English voice uses your browser\'s built-in speech synthesis.</div>',
        unsafe_allow_html=True,
    )
