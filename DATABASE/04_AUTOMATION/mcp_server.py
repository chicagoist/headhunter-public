#!/usr/bin/env python3
"""
HeadHunter MCP Server v1.0
==========================
Экспортирует agent.py как MCP-инструмент для Opencode CLI.
Opencode вызывает этот сервер через JSON-RPC по stdio.

Использование (автоматически через opencode.jsonc):
  python DATABASE/04_AUTOMATION/mcp_server.py

Требования:
  pip install fastmcp
"""

import subprocess
import sys
import uuid
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: fastmcp nicht installiert. Bitte: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Путь к корню проекта (три уровня вверх от этого файла)
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
AGENT_PY  = BASE_DIR / "DATABASE" / "04_AUTOMATION" / "agent.py"
OUTPUT_DIR = BASE_DIR / "OUTPUT" / "Bewerbungen"

mcp = FastMCP(
    name="HeadHunter",
    instructions=(
        "HeadHunter Agent für den deutschen Arbeitsmarkt 2026. "
        "Analysiert Stellenanzeigen, berechnet ATS-Score und erstellt "
        "angepassten Lebenslauf + Anschreiben als Markdown und PDF."
    ),
)


@mcp.tool()
def process_vacancy(
    vacancy_text: str,
    mode: str = "mistral",
    model: str = "",
) -> str:
    """
    Führt den vollständigen 5-Schritt HeadHunter-Workflow für eine Stellenanzeige durch.

    Args:
        vacancy_text: Vollständiger Text der Stellenanzeige (copy-paste aus dem Browser).
        mode: LLM-Backend. Optionen: 'mistral' (Standard), 'openrouter', 'dry-run'.
        model: Optionales Modell für openrouter, z.B. 'google/gemma-4-31b-it:free'.

    Returns:
        Konsolenausgabe von agent.py (ATS Score, Empfehlung, Dateipfade).
    """
    # Temporäre Datei mit eindeutigem Namen
    tmp_file = BASE_DIR / f"tmp_vacancy_{uuid.uuid4().hex[:8]}.txt"
    try:
        tmp_file.write_text(vacancy_text, encoding="utf-8")

        cmd = [
            sys.executable, str(AGENT_PY),
            "--vacancy", str(tmp_file),
            "--mode", mode,
        ]
        if model:
            cmd += ["--model", model]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(BASE_DIR),
            timeout=300,  # 5 минут максимум
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr[:500]}"

        # Возвращаем последние 4000 символов (самое важное в конце)
        return output[-4000:] if len(output) > 4000 else output

    except subprocess.TimeoutExpired:
        return "[FEHLER] Timeout nach 5 Minuten. Versuche --mode dry-run zum Testen."
    except Exception as e:
        return f"[FEHLER] {type(e).__name__}: {e}"
    finally:
        tmp_file.unlink(missing_ok=True)


@mcp.tool()
def list_applications() -> str:
    """
    Listet alle bisher erstellten Bewerbungen aus dem OUTPUT-Verzeichnis auf.

    Returns:
        Liste der Bewerbungsordner mit Datum und Firma.
    """
    if not OUTPUT_DIR.exists():
        return "OUTPUT/Bewerbungen/ existiert noch nicht. Erst eine Bewerbung erstellen."

    folders = sorted(OUTPUT_DIR.iterdir(), reverse=True)
    if not folders:
        return "Noch keine Bewerbungen erstellt."

    lines = [f"Erstellte Bewerbungen ({len(folders)} gesamt):\n"]
    for folder in folders[:20]:  # максимум 20
        files = list(folder.glob("*"))
        has_pdf = any(f.suffix == ".pdf" for f in files)
        pdf_mark = "📄" if has_pdf else "  "
        lines.append(f"  {pdf_mark} {folder.name}")

    return "\n".join(lines)


@mcp.tool()
def get_ats_score(firma: str) -> str:
    """
    Liest den ANALYSE_REPORT.md der neuesten Bewerbung für eine bestimmte Firma.

    Args:
        firma: Firmenname oder Teil davon (z.B. 'Siemens', 'TechNet').

    Returns:
        Inhalt des ANALYSE_REPORT.md oder Fehlermeldung.
    """
    if not OUTPUT_DIR.exists():
        return "Noch keine Bewerbungen erstellt."

    firma_lower = firma.lower().replace(" ", "_")
    matches = [
        f for f in OUTPUT_DIR.iterdir()
        if firma_lower in f.name.lower()
    ]

    if not matches:
        return f"Keine Bewerbung für '{firma}' gefunden."

    # Neueste nehmen
    latest = sorted(matches)[-1]
    report = latest / "ANALYSE_REPORT.md"

    if not report.exists():
        return f"Ordner gefunden: {latest.name}, aber ANALYSE_REPORT.md fehlt."

    content = report.read_text(encoding="utf-8", errors="replace")
    return content[:3000]  # первые 3000 символов


if __name__ == "__main__":
    mcp.run()
