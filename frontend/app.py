import io
import requests
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth as _stringWidth

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Codebase Genius",
    page_icon="🧠",
    layout="wide",
)

API_ENDPOINT = "http://localhost:8000/walker/api_generate_docs"
API_TOKEN = "REPLACE_THIS_WITH_TOKEN_IF_REQUIRED"  # optional / unused for now


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def wrap_text_for_pdf(text_line, font_name, font_size, max_width):
    words = text_line.split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if _stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def make_pdf_bytes(full_text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
    left_margin = 40
    right_margin = 40
    top_margin = 40
    bottom_margin = 40

    font_name = "Helvetica"
    font_size = 10
    line_height = 14

    max_text_width = width - left_margin - right_margin
    cursor_y = height - top_margin

    pdf.setFont(font_name, font_size)

    for raw_line in full_text.splitlines():
        wrapped_lines = wrap_text_for_pdf(
            raw_line, font_name, font_size, max_text_width
        )
        for seg in wrapped_lines:
            if cursor_y < bottom_margin:
                pdf.showPage()
                pdf.setFont(font_name, font_size)
                cursor_y = height - top_margin
            pdf.drawString(left_margin, cursor_y, seg)
            cursor_y -= line_height

        cursor_y -= int(line_height * 0.5)
        if cursor_y < bottom_margin:
            pdf.showPage()
            pdf.setFont(font_name, font_size)
            cursor_y = height - top_margin

    pdf.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def mermaid_to_ascii_flow(mermaid_code: str) -> str:
    """
    Convert Mermaid edges like A-->B into a vertical ASCII sequence.
    (Still used internally for PDF.)
    """
    edges = []
    lines = mermaid_code.strip().splitlines()
    for ln in lines:
        ln = ln.strip().rstrip(";")
        if "-->" in ln and "graph" not in ln:
            parts = ln.split("-->")
            if len(parts) == 2:
                src = parts[0].strip().replace(";", "")
                dst = parts[1].strip().replace(";", "")
                if src and dst:
                    edges.append((src, dst))

    if not edges:
        return "[no recognizable flow edges]"

    all_srcs = [s for (s, _) in edges]
    all_dsts = [d for (_, d) in edges]
    possible_starts = [s for s in all_srcs if s not in all_dsts]
    start = possible_starts[0] if possible_starts else edges[0][0]

    ordered = [start]
    used = set()
    current = start
    while True:
        nxt = None
        for (s, d) in edges:
            if s == current and (s, d) not in used:
                nxt = d
                used.add((s, d))
                break
        if nxt is None:
            break
        ordered.append(nxt)
        current = nxt

    ascii_lines = []
    for idx, node in enumerate(ordered):
        ascii_lines.append(node)
        if idx < len(ordered) - 1:
            ascii_lines.append("   |")
            ascii_lines.append("   v")

    return "\n".join(ascii_lines) if ascii_lines else "[flow did not linearize]"


# -------------------------------------------------
# STYLE
# -------------------------------------------------
st.markdown(
    """
    <style>
    /* Hide Streamlit default chrome */
    header[data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .stDeployButton {display: none !important;}
    footer {display: none !important;}

    /* Lock viewport and shift hero content a tiny bit up */
    html, body, [data-testid="stAppViewContainer"], .block-container {
        height: 100vh !important;
        max-height: 100vh !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        overscroll-behavior: none;
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont,
                     'Segoe UI', Roboto, sans-serif;
        color: #fff;
        background:
            radial-gradient(circle at 20% 20%, rgba(73,0,128,0.7) 0%, rgba(0,0,0,0) 60%),
            radial-gradient(circle at 80% 30%, rgba(0,255,255,0.2) 0%, rgba(0,0,0,0) 60%),
            radial-gradient(circle at 50% 80%, rgba(255,0,128,0.15) 0%, rgba(0,0,0,0) 60%),
            radial-gradient(circle at 50% 50%, #050510 0%, #000000 70%);
        background-color: #000;
    }

    .screen-wrap {
        position: relative;
        z-index: 1;
        height: 100%;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        box-sizing: border-box;
        padding: 1rem;
        transform: translateY(-2vh);
    }

    .screen-grid {
        width: 100%;
        max-width: 950px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        align-items: center;
        row-gap: 1rem;
    }

    .hero-card {
        width: 100%;
        max-width: 780px;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .hero-card:before {
        display: none !important;
        content: none !important;
    }

    .hero-inner {
        width: 100%;
        max-width: 780px;
        display: flex;
        flex-direction: column;
        align-items: center;
        row-gap: 1rem;
        z-index: 2;
    }

    /*********************************
     BRAND BLOCK (first visible thing)
    **********************************/
    .brand-block {
        display:flex;
        flex-direction:column;
        align-items:center;
        row-gap:.4rem;
        margin-bottom: 0.25rem;
    }

    .logo-row {
        display:flex;
        flex-direction: row;
        align-items:center;
        column-gap:.5rem;
        flex-wrap:wrap;
        justify-content:center;
    }

    .logo-mark {
        width: 46px;
        height: 46px;
        border-radius: 10px;
        background: radial-gradient(circle at 30% 30%, #00ff99 0%, #003300 60%);
        box-shadow:
            0 0 20px #00ff99aa,
            0 0 40px #00ffcc55,
            0 0 80px rgba(0,255,255,0.4);
        font-size: 1.5rem;
        font-weight: 900;
        color:#000;
        display:flex;
        align-items:center;
        justify-content:center;
        border:1px solid #00ff99;
        text-shadow:0 0 4px #00ff99;
    }

    .brand-lines {
        display:flex;
        flex-direction:column;
        align-items:center;
        line-height:1.3;
    }

    .brand-main {
        font-size: 1.5rem;
        font-weight: 900;
        color:#fff;
        letter-spacing:.03em;
        text-shadow:
            0 0 10px rgba(0,255,255,0.6),
            0 0 30px rgba(255,0,187,0.5);
    }

    .brand-sub {
        font-size: .9rem;
        font-weight: 600;
        color:rgba(255,255,255,0.6);
        text-shadow:0 0 6px rgba(0,0,0,0.8);
    }

    /*********************************
     WAVY NAME (animated, color-cycling)
    **********************************/
    .name-wave {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        font-size: 1.4rem;
        font-weight: 700;
        line-height: 1.2;
        text-align: center;
        background: radial-gradient(circle at 10% 0%, #ffffff 0%, #a1ffce 30%, #ff6ee7 60%, #6affff 100%);
        -webkit-background-clip: text;
        color: transparent;
        text-shadow:
            0 0 12px rgba(0,255,255,0.7),
            0 0 30px rgba(255,0,187,0.5),
            0 0 60px rgba(0,255,153,0.4);
        letter-spacing: .04em;
        margin-top: .25rem;
        filter: hue-rotate(0deg);
        animation: hueShift 4s linear infinite;
    }

    @keyframes hueShift {
        0%   { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }

    .wave-letter {
        display: inline-block;
        animation: waveFloat 2s infinite;
        animation-timing-function: ease-in-out;
    }

    /* gentle wave motion */
    @keyframes waveFloat {
        0%   { transform: translateY(0px)   rotate(0deg);   }
        25%  { transform: translateY(-4px)  rotate(-1deg);  }
        50%  { transform: translateY(0px)   rotate(0deg);   }
        75%  { transform: translateY(4px)   rotate(1deg);   }
        100% { transform: translateY(0px)   rotate(0deg);   }
    }

    .wave-letter[data-i="0"]  { animation-delay: 0.00s; }
    .wave-letter[data-i="1"]  { animation-delay: 0.04s; }
    .wave-letter[data-i="2"]  { animation-delay: 0.08s; }
    .wave-letter[data-i="3"]  { animation-delay: 0.12s; }
    .wave-letter[data-i="4"]  { animation-delay: 0.16s; }
    .wave-letter[data-i="5"]  { animation-delay: 0.20s; }
    .wave-letter[data-i="6"]  { animation-delay: 0.24s; }
    .wave-letter[data-i="7"]  { animation-delay: 0.28s; }
    .wave-letter[data-i="8"]  { animation-delay: 0.32s; }
    .wave-letter[data-i="9"]  { animation-delay: 0.36s; }
    .wave-letter[data-i="10"] { animation-delay: 0.40s; }
    .wave-letter[data-i="11"] { animation-delay: 0.44s; }
    .wave-letter[data-i="12"] { animation-delay: 0.48s; }
    .wave-letter[data-i="13"] { animation-delay: 0.52s; }
    .wave-letter[data-i="14"] { animation-delay: 0.56s; }
    .wave-letter[data-i="15"] { animation-delay: 0.60s; }
    .wave-letter[data-i="16"] { animation-delay: 0.64s; }
    .wave-letter[data-i="17"] { animation-delay: 0.68s; }
    .wave-letter[data-i="18"] { animation-delay: 0.72s; }
    .wave-letter[data-i="19"] { animation-delay: 0.76s; }
    .wave-letter[data-i="20"] { animation-delay: 0.80s; }
    .wave-letter[data-i="21"] { animation-delay: 0.84s; }
    .wave-letter[data-i="22"] { animation-delay: 0.88s; }
    .wave-letter[data-i="23"] { animation-delay: 0.92s; }

    /*********************************
     URL INPUT AREA
    **********************************/
    .url-wrapper {
        width: 60%;
        max-width: 560px;
        min-width: 320px;
        margin: 1rem auto 0 auto;
        display: flex;
        flex-direction: column;
        align-items: stretch;
    }

    .form-block {
        width: 100%;
        background: transparent;
        border: none;
        border-radius: 0;
        box-shadow: none;
        padding: 0;
        text-align: left;
    }

    .field-label {
        font-size: 1.0rem;
        font-weight: 900;
        color: #fff;
        margin-bottom: .4rem;
        text-align: left;
        text-shadow: 0 0 8px rgba(0,0,0,0.8);
        transform: translateX(40px);
    }

    .field-hint {
        font-size:.8rem;
        font-weight: 600;
        line-height:1.4;
        color:rgba(255,255,255,0.55);
        text-align:left;
        transform: translateX(5px);
    }

    /* Force Streamlit's text_input width / radius */
    .stTextInput {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-start;
    }

    .stTextInput > div {
        width: 75% !important;
        max-width: 770px !important;
        min-width: 320px !important;
        border-radius: 200px !important;
    }

    .stTextInput input {
        border-radius: 20px !important;
    }

    /*********************************
     STATUS + RUN
    **********************************/
    .mini-status {
        font-size:.7rem;
        line-height:1.4;
        color:rgba(255,255,255,0.75);
        text-shadow:
            0 0 8px rgba(0,0,0,0.8),
            0 0 16px rgba(0,255,153,0.4);
    }

    /* Run Analysis button */
    div.stButton > button {
        border-radius: 32px;
        background: radial-gradient(circle at 0% 0%, #00fff2 0%, #ff00ff 60%);
        color: #000;
        border: none;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        font-size:.9rem;
        cursor: pointer;
        box-shadow:
            0 0 20px #00fff2,
            0 0 40px #ff00ff,
            0 0 80px rgba(0,255,153,0.4);
        animation: pulseButton 2.5s infinite;
        animation-timing-function: ease-in-out;
    }
    div.stButton > button:hover {
        transform: scale(1.07);
        box-shadow:
            0 0 25px #00fff2,
            0 0 55px #ff00ff,
            0 0 90px rgba(0,255,153,0.6);
    }
    @keyframes pulseButton {
        0%   { box-shadow:0 0 20px #00fff2,0 0 40px #ff00ff,0 0 80px rgba(0,255,153,0.4); }
        50%  { box-shadow:0 0 30px #00fff2,0 0 60px #ff00ff,0 0 110px rgba(0,255,153,0.6); }
        100% { box-shadow:0 0 20px #00fff2,0 0 40px #ff00ff,0 0 80px rgba(0,255,153,0.4); }
    }

    /*********************************
     PREVIEW PANEL
    **********************************/
    .export-panel-wrap {
        margin-top: 1.5rem;
        width:100%;
        max-width:560px;

        background: transparent;
        border: none;
        border-radius: 0;
        box-shadow: none;
        backdrop-filter: none;

        padding: 0;
        display:flex;
        flex-direction:column;
        row-gap:.75rem;
    }

    .export-headline {
        font-size: 1.0rem;
        font-weight: 700;
        color: #fff;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-evenly;
        gap: 55.5rem;
        align-items: baseline;
        line-height: 1.4;
        letter-spacing: .08em;
        text-transform: uppercase;
        text-shadow:
            0 0 10px rgba(0,255,255,0.8),
            0 0 25px rgba(255,0,187,0.5),
            0 0 45px rgba(0,255,153,0.4);
    }

    .scroll-box-preview {
        background:rgba(255,255,255,0.05);
        border:1px solid rgba(255,255,255,0.25);
        border-radius:10px;
        box-shadow:
            0 10px 24px rgba(0,0,0,0.9),
            0 0 40px rgba(0,255,255,0.3) inset;
        font-family:monospace;
        font-size:.75rem;
        line-height:1.4;
        color:#d2fff6;
        padding:.75rem .75rem;
        overflow-y:auto;
        white-space:pre-wrap;
        word-break:break-word;
        max-height:22vh;
    }

    /*********************************
     FOOTER (MO glowing badge + copyright)
     PINNED TO BOTTOM NOW
    **********************************/
    .footer-line {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0.2rem;

        width:100%;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;

        /* remove large margins so it doesn't "jump" */
        margin-top:0;
        margin-bottom:0;
        pointer-events: none; /* footer shouldn't block clicks above it */
    }

    .footer-mark {
        width: 30px;
        height: 30px;
        border-radius: 12px;
        background: radial-gradient(circle at 30% 30%, #00fff2 0%, #240024 60%);
        border:2px solid rgba(0,255,255,0.6);
        box-shadow:
            0 0 20px rgba(0,255,255,0.9),
            0 0 50px rgba(255,0,0,0.6),
            0 0 90px rgba(255,0,255,0.4);
        font-size:.8rem;
        font-weight:700;
        color:#000;
        display:flex;
        align-items:center;
        justify-content:center;
        text-shadow:0 0 4px rgba(0,0,0,0.8);
        animation: footerPulse 3s infinite;
    }

    @keyframes footerPulse {
        0%   { box-shadow:0 0 20px rgba(0,255,255,0.9),0 0 50px rgba(255,0,0,0.6),0 0 90px rgba(255,0,255,0.4); }
        50%  { box-shadow:0 0 30px rgba(0,255,255,1),0 0 70px rgba(255,0,128,0.7),0 0 120px rgba(255,0,255,0.6); }
        100% { box-shadow:0 0 20px rgba(0,255,255,0.9),0 0 50px rgba(255,0,0,0.6),0 0 90px rgba(255,0,255,0.4); }
    }

    .footer-copy {
        font-size:.7rem;
        color:rgba(255,255,255,0.6);
        text-align:center;
        letter-spacing:.05em;
        text-shadow:
            0 0 8px rgba(0,0,0,0.8),
            0 0 16px rgba(0,255,255,0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------
# Session state init
# -------------------------------------------------
if "repo_name_val" not in st.session_state:
    st.session_state.update(
        {
            "repo_name_val": "—",
            "files_scanned_val": "-",
            "symbols_found_val": "-",
            "relations_found_val": "-",
            "preview_md_val": "",
            "server_path_val": "",
            "mod_graph": "",
            "inh_graph": "",
            "req_graph": "",
            "ascii_mod": "",
            "ascii_inh": "",
            "ascii_req": "",
            "pdf_bytes_val": b"",
            "status_msg": "Idle. Ready.",
        }
    )


# -------------------------------------------------
# HERO CONTENT (center column UI)
# -------------------------------------------------
st.markdown('<div class="screen-wrap"><div class="screen-grid">', unsafe_allow_html=True)
st.markdown('<div class="hero-card"><div class="hero-inner">', unsafe_allow_html=True)

# BRAND BLOCK (FIRST THING, nothing above it)
st.markdown(
    """
    <div class="brand-block">
        <div class="logo-row">
            <div class="logo-mark">AI</div>
            <div class="brand-lines">
                <div class="brand-main">Codebase&nbsp;Genius</div>
                <div class="brand-sub">Jac Autonomous Suite</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# WAVY NAME (animated glow cycling colors)
st.markdown(
    """
    <div class="name-wave" aria-label="MOHAMED • CODE ARCHITECT">
        <span class="wave-letter" data-i="0">M</span>
        <span class="wave-letter" data-i="1">O</span>
        <span class="wave-letter" data-i="2">H</span>
        <span class="wave-letter" data-i="3">A</span>
        <span class="wave-letter" data-i="4">M</span>
        <span class="wave-letter" data-i="5">E</span>
        <span class="wave-letter" data-i="6">D</span>
        <span class="wave-letter" data-i="7">&nbsp;</span>
        <span class="wave-letter" data-i="8">•</span>
        <span class="wave-letter" data-i="9">&nbsp;</span>
        <span class="wave-letter" data-i="10">C</span>
        <span class="wave-letter" data-i="11">O</span>
        <span class="wave-letter" data-i="12">D</span>
        <span class="wave-letter" data-i="13">E</span>
        <span class="wave-letter" data-i="14">&nbsp;</span>
        <span class="wave-letter" data-i="15">A</span>
        <span class="wave-letter" data-i="16">R</span>
        <span class="wave-letter" data-i="17">C</span>
        <span class="wave-letter" data-i="18">H</span>
        <span class="wave-letter" data-i="19">I</span>
        <span class="wave-letter" data-i="20">T</span>
        <span class="wave-letter" data-i="21">E</span>
        <span class="wave-letter" data-i="22">C</span>
        <span class="wave-letter" data-i="23">T</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# URL INPUT CARD
st.markdown('<div class="url-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="form-block">', unsafe_allow_html=True)

st.markdown(
    '<div class="field-label">GitHub Repository URL</div>',
    unsafe_allow_html=True,
)

repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/psf/requests",
    label_visibility="collapsed",
)

st.markdown(
    """
    <div class="field-hint">
        URL must be public / cloneable. Private repos will fail at clone.
        We'll prioritise entrypoints, build the Code Context Graph,
        and draft docs.md.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)  # end .form-block
st.markdown("</div>", unsafe_allow_html=True)  # end .url-wrapper

# STATUS + RUN row
st.markdown(
    '<div class="hero-bottom-row" style="width:60%;max-width:560px;min-width:320px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;margin-top:1rem;row-gap:.5rem;">',
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([3, 1])

with left_col:
    st.markdown(
        f"""
        <div class="mini-status">
            {st.session_state["status_msg"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    run_btn = st.button(
        "▶ Run Analysis",
        help="Run RepoMapper → CodeAnalyzer → DocGenie",
    )

st.markdown("</div>", unsafe_allow_html=True)  # hero-bottom-row

# PREVIEW PANEL (docs.md preview / results or placeholder)
preview_html = (
    st.session_state["preview_md_val"]
    or "[Run analysis to generate documentation preview…]"
)
safe_preview_html = preview_html.replace("<", "&lt;").replace(">", "&gt;")

st.markdown('<div class="export-panel-wrap">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="export-headline">
        <div>docs.md preview &amp; export</div>
        <div>ready to submit</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="scroll-box-preview">{safe_preview_html}</div>
    """,
    unsafe_allow_html=True,
)

# FOOTER with glowing MO + copyright (now fixed at bottom)
st.markdown(
    """
    <div class="footer-line">
        <div class="footer-mark">MO</div>
        <div class="footer-copy">© Mohamed · All rights reserved</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)  # /export-panel-wrap

# close wrappers
st.markdown("</div></div>", unsafe_allow_html=True)  # hero-inner / hero-card
st.markdown("</div></div>", unsafe_allow_html=True)  # screen-grid / screen-wrap


# -------------------------------------------------
# BACKEND CALL
# -------------------------------------------------
if "run_btn" not in locals():
    run_btn = False

if run_btn:
    if not repo_url.strip():
        st.session_state["status_msg"] = "❌ Please provide a valid GitHub URL."
    else:
        st.session_state["status_msg"] = "⏳ Running multi-agent pipeline..."

        try:
            headers = {"Content-Type": "application/json"}
            if API_TOKEN != "REPLACE_THIS_WITH_TOKEN_IF_REQUIRED":
                headers["Authorization"] = f"Bearer {API_TOKEN}"

            resp = requests.post(
                API_ENDPOINT,
                json={"repo_url": repo_url.strip()},
                timeout=200,
                headers=headers,
            )

            if resp.status_code != 200:
                st.session_state["status_msg"] = (
                    f"❌ Backend HTTP {resp.status_code}"
                )
            else:
                raw = resp.json()
                payload_list = raw.get("returns") or raw.get("reports") or []
                payload = payload_list[0] if payload_list else {}

                if not payload:
                    st.session_state["status_msg"] = "❌ Empty response"
                elif not payload.get("ok"):
                    st.session_state["status_msg"] = (
                        "❌ " + payload.get("error", "Pipeline failed")
                    )
                else:
                    repo_name_val = payload.get("repo_name", "unknown")
                    ccg_stats = payload.get("ccg_stats", {})

                    files_scanned_val = ccg_stats.get("files_scanned", "-")
                    symbols_found_val = ccg_stats.get("symbols_found", "-")
                    relations_found_val = ccg_stats.get("relations_found", "-")

                    preview_md_val = payload.get("preview", "")
                    server_path_val = payload.get("docs_path", "")

                    diagrams = payload.get("diagrams", {})
                    mod_graph = diagrams.get("module_dependency", "") if isinstance(diagrams, dict) else ""
                    inh_graph = diagrams.get("class_inheritance", "") if isinstance(diagrams, dict) else ""
                    req_graph = diagrams.get("request_flow", "") if isinstance(diagrams, dict) else ""

                    ascii_mod = mermaid_to_ascii_flow(mod_graph) if mod_graph else ""
                    ascii_inh = mermaid_to_ascii_flow(inh_graph) if inh_graph else ""
                    ascii_req = mermaid_to_ascii_flow(req_graph) if req_graph else ""

                    pdf_lines = []
                    pdf_lines.append("Codebase Genius Report")
                    pdf_lines.append(f"Repository: {repo_name_val}")
                    pdf_lines.append("")
                    pdf_lines.append("Stats:")
                    pdf_lines.append(f"  Files scanned:   {files_scanned_val}")
                    pdf_lines.append(f"  Symbols found:   {symbols_found_val}")
                    pdf_lines.append(f"  Relations found: {relations_found_val}")
                    pdf_lines.append("")
                    pdf_lines.append("---- Generated docs.md ----")
                    pdf_lines.append(preview_md_val)
                    pdf_lines.append("")
                    pdf_lines.append("---- Architecture Diagrams ----")
                    if mod_graph:
                        pdf_lines.append("")
                        pdf_lines.append("[Module Dependency Graph / Mermaid]")
                        pdf_lines.append(mod_graph)
                        pdf_lines.append("[Module Dependency (ASCII for print)]")
                        pdf_lines.append(ascii_mod or "[n/a]")
                    if inh_graph:
                        pdf_lines.append("")
                        pdf_lines.append("[Class Inheritance Graph / Mermaid]")
                        pdf_lines.append(inh_graph)
                        pdf_lines.append("[Class Inheritance (ASCII for print)]")
                        pdf_lines.append(ascii_inh or "[n/a]")
                    if req_graph:
                        pdf_lines.append("")
                        pdf_lines.append("[Request / Call Flow Graph / Mermaid]")
                        pdf_lines.append(req_graph)
                        pdf_lines.append("[Request / Call Flow (ASCII for print)]")
                        pdf_lines.append(ascii_req or "[n/a]")

                    pdf_bytes_val = make_pdf_bytes("\n".join(pdf_lines))

                    # update UI state
                    st.session_state.update(
                        {
                            "repo_name_val": repo_name_val,
                            "files_scanned_val": files_scanned_val,
                            "symbols_found_val": symbols_found_val,
                            "relations_found_val": relations_found_val,
                            "preview_md_val": preview_md_val,
                            "server_path_val": server_path_val,
                            "mod_graph": mod_graph,
                            "inh_graph": inh_graph,
                            "req_graph": req_graph,
                            "ascii_mod": ascii_mod,
                            "ascii_inh": ascii_inh,
                            "ascii_req": ascii_req,
                            "pdf_bytes_val": pdf_bytes_val,
                            "status_msg": "✅ Documentation generated successfully.",
                        }
                    )

                    # force refresh so the preview updates
                    st.rerun()

        except Exception as e:
            st.session_state["status_msg"] = (
                "❌ Request failed: " + str(e)
            )
