from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import webbrowser
from pathlib import Path

from .api import QuranAPI
from .azkar import MORNING_AZKAR, NIGHT_AZKAR
from .rendering import normalize_azkar_text

HTML_VERSION = "3"


def open_browser_fallback(api: QuranAPI, view: str = "quran", surah_number: int = 1, azkar_kind: str = "morning") -> Path:
    path = build_browser_fallback(api, view=view, surah_number=surah_number, azkar_kind=azkar_kind)
    _open_path(path)
    return path


def _open_path(path: Path) -> None:
    uri = path.as_uri()
    launchers: list[list[str]] = []

    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        if shutil.which("xdg-open"):
            launchers.append(["xdg-open", uri])
        if shutil.which("gio"):
            launchers.append(["gio", "open", uri])
        if shutil.which("firefox"):
            launchers.append(["firefox", uri])

    for command in launchers:
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError:
            continue

    if webbrowser.open(uri):
        return

    raise RuntimeError("No working browser launcher was found.")


def build_browser_fallback(
    api: QuranAPI,
    view: str = "quran",
    surah_number: int = 1,
    azkar_kind: str = "morning",
) -> Path:
    surah_payload = json.loads((api.data_dir / "surahs.json").read_text(encoding="utf-8"))
    quran_payload = json.loads((api.data_dir / "quran-uthmani.json").read_text(encoding="utf-8"))

    browser_surahs = [
        {
            "number": item["number"],
            "arabic_name": item["name"],
            "english_name": item["englishName"],
            "revelation_type": item["revelationType"],
            "number_of_ayahs": item["numberOfAyahs"],
        }
        for item in surah_payload["data"]
    ]
    quran_surahs = {
        str(item["number"]): [ayah["text"] for ayah in item["ayahs"]]
        for item in quran_payload["data"]["surahs"]
    }
    morning = [{"text": normalize_azkar_text(item.text), "repeat": item.repeat, "note": item.note} for item in MORNING_AZKAR]
    night = [{"text": normalize_azkar_text(item.text), "repeat": item.repeat, "note": item.note} for item in NIGHT_AZKAR]

    output_dir = Path(tempfile.gettempdir()) / "quran-tui-browser"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"fallback-{HTML_VERSION}.html"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DuaTerm</title>
  <style>
    :root {{
      --bg: #171916;
      --panel: #20241f;
      --panel-2: #262b25;
      --text: #f3f2eb;
      --muted: #b7b8ad;
      --accent: #d9c78d;
      --border: rgba(255,255,255,0.16);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Noto Sans", system-ui, sans-serif;
      background:
        radial-gradient(circle at bottom, rgba(155, 53, 53, 0.15), transparent 30%),
        radial-gradient(circle at center, rgba(255,255,255,0.05), transparent 35%),
        var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}
    .app {{
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 18px;
      padding: 24px;
      min-height: 100vh;
    }}
    .panel {{
      background: rgba(0,0,0,0.12);
      border: 1px solid var(--border);
      border-radius: 18px;
      backdrop-filter: blur(4px);
    }}
    .sidebar {{
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .brand {{
      font-size: 1.15rem;
      font-weight: 700;
    }}
    .brand-tagline {{
      color: var(--muted);
      font-size: 0.92rem;
      margin-top: -8px;
      margin-bottom: 4px;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
    }}
    .tabs button, .surah-list button {{
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 12px;
      cursor: pointer;
    }}
    .tabs button {{
      padding: 10px 12px;
      font-size: 0.95rem;
    }}
    .tabs button.active, .surah-list button.active {{
      background: var(--accent);
      color: #1e1e18;
      border-color: transparent;
    }}
    .surah-list {{
      display: grid;
      gap: 6px;
      overflow: auto;
      max-height: calc(100vh - 180px);
      padding-right: 4px;
    }}
    .surah-list button {{
      padding: 10px 12px;
      text-align: left;
      font-size: 0.95rem;
    }}
    .content {{
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .page {{
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 28px 34px 42px;
      background: rgba(255,255,255,0.03);
      min-height: calc(100vh - 104px);
    }}
    .meta {{
      color: var(--muted);
      font-size: 1rem;
      margin-bottom: 8px;
    }}
    .title-ar {{
      direction: rtl;
      text-align: center;
      font-family: "Noto Naskh Arabic", "Amiri", serif;
      font-size: 2.2rem;
      margin: 10px 0 4px;
    }}
    .ornament {{
      text-align: center;
      color: var(--accent);
      letter-spacing: 0.18em;
      margin: 2px 0;
    }}
    .basmala {{
      direction: rtl;
      text-align: center;
      font-family: "Noto Naskh Arabic", "Amiri", serif;
      font-size: 2.1rem;
      margin: 18px 0 24px;
    }}
    .quran-body {{
      direction: rtl;
      text-align: right;
      font-family: "Noto Naskh Arabic", "Amiri", serif;
      font-size: 2rem;
      line-height: 2.1;
      max-width: 980px;
      margin: 0 auto;
    }}
    .ayah-marker {{
      font-family: "Noto Sans", system-ui, sans-serif;
      font-size: 0.7em;
      color: var(--muted);
      white-space: nowrap;
      unicode-bidi: bidi-override;
      direction: ltr;
    }}
    .ayah-sep {{
      display: inline-block;
      margin: 0 0.38em;
      color: var(--muted);
      font-family: "Noto Naskh Arabic", "Amiri", serif;
      transform: translateY(-0.02em);
    }}
    .azkar-title {{
      text-align: center;
      font-size: 2rem;
      margin-bottom: 20px;
    }}
    .zikr {{
      display: grid;
      gap: 8px;
      padding: 16px 0;
      border-bottom: 1px solid var(--border);
    }}
    .zikr:last-child {{ border-bottom: 0; }}
    .zikr-head {{
      color: var(--muted);
      font-weight: 700;
    }}
    .zikr-text {{
      direction: rtl;
      text-align: right;
      font-family: "Noto Naskh Arabic", "Amiri", serif;
      font-size: 1.85rem;
      line-height: 2;
    }}
    .zikr-note {{
      color: var(--muted);
    }}
    @media (max-width: 980px) {{
      .app {{ grid-template-columns: 1fr; }}
      .surah-list {{ max-height: 280px; }}
      .page {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="panel sidebar">
      <div class="brand">DuaTerm</div>
      <div class="brand-tagline">Prayer in your Terminal</div>
      <div class="tabs">
        <button id="tab-quran">Quran</button>
        <button id="tab-morning">Morning Azkar</button>
        <button id="tab-night">Night Azkar</button>
      </div>
      <div id="surah-list" class="surah-list"></div>
    </aside>
    <main class="panel content">
      <div id="page" class="page"></div>
    </main>
  </div>
  <script>
    const initialView = {json.dumps(view)};
    const initialSurah = {int(surah_number)};
    const initialAzkarKind = {json.dumps(azkar_kind)};
    const surahs = {json.dumps(browser_surahs, ensure_ascii=False)};
    const quran = {json.dumps(quran_surahs, ensure_ascii=False)};
    const morning = {json.dumps(morning, ensure_ascii=False)};
    const night = {json.dumps(night, ensure_ascii=False)};

    let currentView = initialView;
    let currentSurah = initialSurah;

    const page = document.getElementById("page");
    const surahList = document.getElementById("surah-list");
    const quranTab = document.getElementById("tab-quran");
    const morningTab = document.getElementById("tab-morning");
    const nightTab = document.getElementById("tab-night");

    function ayahLabel(n) {{
      return `<span class="ayah-marker">(${{n}})</span>`;
    }}

    function escapeHtml(s) {{
      return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    }}

    function formatArabicText(s) {{
      return escapeHtml(s).replaceAll("۝", `<span class="ayah-sep">۝</span>`);
    }}

    function renderTabs() {{
      quranTab.classList.toggle("active", currentView === "quran");
      morningTab.classList.toggle("active", currentView === "morning");
      nightTab.classList.toggle("active", currentView === "night");
    }}

    function renderSidebar() {{
      surahList.innerHTML = "";
      surahList.style.display = currentView === "quran" ? "grid" : "none";
      if (currentView !== "quran") return;
      for (const surah of surahs) {{
        const button = document.createElement("button");
        button.textContent = `${{surah.number}}. ${{surah.english_name}}`;
        button.classList.toggle("active", surah.number === currentSurah);
        button.onclick = () => {{
          currentSurah = surah.number;
          render();
        }};
        surahList.appendChild(button);
      }}
    }}

    function splitBasmala(text) {{
      const prefixes = [
        "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
      ];
      for (const prefix of prefixes) {{
        if (text.startsWith(prefix)) {{
          return [prefix, text.slice(prefix.length).trim()];
        }}
      }}
      return [null, text];
    }}

    function renderQuran() {{
      const summary = surahs.find((item) => item.number === currentSurah);
      const ayahs = quran[String(currentSurah)] || [];
      let basmala = null;
      let startIndex = 0;
      let firstAyah = ayahs[0] || "";
      const split = splitBasmala(firstAyah);
      if (split[0]) {{
        basmala = split[0];
        if (split[1]) {{
          ayahs[0] = split[1];
        }} else {{
          startIndex = 1;
        }}
      }}
      const renderedAyahs = ayahs.slice(startIndex).map((text, i) => `${{formatArabicText(text)}} ${{ayahLabel(i + 1 + startIndex)}}`);
      page.innerHTML = `
        <div class="meta">${{summary.number}}. ${{summary.english_name}} | ${{summary.number_of_ayahs}} ayahs | ${{summary.revelation_type}}</div>
        <div class="ornament">۞ ۞ ۞</div>
        <div class="title-ar">${{summary.arabic_name}}</div>
        <div class="ornament">۞ ۞ ۞</div>
        ${{basmala ? `<div class="ornament">۞ ۞ ۞ ۞ ۞</div><div class="basmala">${{basmala}}</div>` : ""}}
        <div class="quran-body">${{renderedAyahs.join(" ")}}</div>
      `;
    }}

    function renderAzkar(kind) {{
      const items = kind === "morning" ? morning : night;
      const title = kind === "morning" ? "Morning Azkar" : "Night Azkar";
      page.innerHTML = `
        <div class="azkar-title">${{title}}</div>
        ${{items.map((item, index) => `
          <section class="zikr">
            <div class="zikr-head">${{index + 1}}. ${{item.repeat}}</div>
            <div class="zikr-text">${{formatArabicText(item.text)}}</div>
            ${{item.note ? `<div class="zikr-note">${{escapeHtml(item.note)}}</div>` : ""}}
          </section>
        `).join("")}}
      `;
    }}

    function render() {{
      renderTabs();
      renderSidebar();
      if (currentView === "quran") {{
        renderQuran();
      }} else if (currentView === "morning") {{
        renderAzkar("morning");
      }} else {{
        renderAzkar("night");
      }}
    }}

    quranTab.onclick = () => {{ currentView = "quran"; render(); }};
    morningTab.onclick = () => {{ currentView = "morning"; render(); }};
    nightTab.onclick = () => {{ currentView = "night"; render(); }};

    if (initialView === "morning") currentView = "morning";
    if (initialView === "night") currentView = "night";
    render();
  </script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
