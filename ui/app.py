"""PISMO — Streamlit UI: upload PDFs, see the document page next to the extracted data.

Talks to the API (API_URL); run with `docker compose up -d` -> http://localhost:8501
"""

import io
import json
import os
import zipfile
from pathlib import Path

import pypdfium2 as pdfium
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 600  # OCR of a long scan can take minutes on a CPU
METHOD_LABELS = {"rule": "reguła", "llm": "AI", "rule+llm": "reguła + AI (zgodne)", None: "—"}

st.set_page_config(page_title="PISMO", page_icon="📄", layout="wide")


@st.cache_data(ttl=30, show_spinner=False)
def api_document_types() -> list[dict] | None:
    try:
        response = requests.get(f"{API_URL}/document-types", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def api_extract(name: str, content: bytes) -> dict:
    response = requests.post(
        f"{API_URL}/extract",
        params={"include_text": "true"},
        files={"file": (name, content, "application/pdf")},
        timeout=TIMEOUT,
    )
    if response.status_code != 200:
        is_json = response.headers.get("content-type", "").startswith("application/json")
        detail = response.json().get("detail", response.text) if is_json else response.text
        raise RuntimeError(f"{response.status_code}: {detail}")
    return response.json()


@st.cache_data(show_spinner=False, max_entries=64)
def render_page(pdf_bytes: bytes, page_number: int) -> bytes | None:
    """PNG of one page (rendered locally in the UI, no extra API call)."""
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
        image = pdf[page_number - 1].render(scale=1.4).to_pil()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        pdf.close()
        return buffer.getvalue()
    except Exception:  # unreadable PDF or page out of range
        return None


def output_json(result: dict) -> str:
    return json.dumps(result["output"], ensure_ascii=False, indent=2)


def zip_outputs(results: dict[str, dict]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, result in results.items():
            archive.writestr(f"{Path(name).stem}.json", output_json(result) + "\n")
    return buffer.getvalue()


def llm_summary(result: dict) -> str:
    info = result.get("llm") or {}
    mode = info.get("mode", "rules")
    if mode == "rules":
        return "tryb: tylko reguły"
    if info.get("used"):
        return f"tryb: {mode} · AI: {info.get('model')}"
    if info.get("error"):
        return f"tryb: {mode} · AI niedostępne ({info['error']}) — wynik z reguł"
    return f"tryb: {mode} · AI nie było potrzebne ({info.get('skipped_reason', '')})"


# --- sidebar ------------------------------------------------------------------------------

with st.sidebar:
    st.header("PISMO")
    st.caption("Parser Inteligentnie Strukturyzujący Materiały Odwoławcze — PDF sprawy KIO → JSON (UZP)")
    types = api_document_types()
    if types is None:
        st.error(f"API niedostępne ({API_URL})")
    else:
        st.success("API działa")
        st.subheader("Typy dokumentów")
        st.caption("Definiowane w `config/document_types/*.yaml` — nowy typ to nowy plik, bez zmian w kodzie.")
        for t in types:
            with st.expander(f"{t['name']} ({len(t['fields'])} pól)"):
                st.caption(t.get("description") or "")
                st.code("\n".join(t["fields"]), language=None)

# --- upload & processing ------------------------------------------------------------------

st.title("PISMO — ekstrakcja danych z dokumentów KIO")
st.write(
    "Wgraj dokumenty sprawy (odwołanie, pełnomocnictwo, potwierdzenie przelewu — PDF cyfrowe lub skany). "
    "Dokumenty spoza obsługiwanych klas dają pusty JSON (`{}`)."
)

uploaded = st.file_uploader("Pliki PDF", type=["pdf"], accept_multiple_files=True)
results: dict[str, dict] = st.session_state.setdefault("results", {})
files: dict[str, bytes] = st.session_state.setdefault("files", {})

if st.button("Przetwórz", type="primary", disabled=not uploaded):
    results.clear()
    files.clear()
    progress = st.progress(0.0, text="Przetwarzanie…")
    for index, file in enumerate(uploaded, start=1):
        progress.progress((index - 1) / len(uploaded), text=f"Przetwarzanie {file.name} ({index}/{len(uploaded)})…")
        content = file.getvalue()
        files[file.name] = content
        try:
            results[file.name] = api_extract(file.name, content)
        except (requests.RequestException, RuntimeError) as exc:
            results[file.name] = {"filename": file.name, "error": str(exc), "output": {}, "document_type": None, "fields": {}}
    progress.empty()

if not results:
    st.stop()

# --- summary --------------------------------------------------------------------------------

st.subheader("Wyniki")
rows = []
for name, r in results.items():
    fields = r.get("fields") or {}
    found = sum(1 for f in fields.values() if f.get("value") is not None)
    ingestion = r.get("ingestion") or {}
    rows.append(
        {
            "plik": name,
            "typ dokumentu": r.get("document_type") or "— nierozpoznany (pusty JSON)",
            "znalezione pola": f"{found}/{len(fields)}" if fields else "—",
            "strony": ingestion.get("page_count"),
            "OCR (strony)": ", ".join(map(str, ingestion.get("ocr_pages") or [])) or "—",
            "AI": "tak" if (r.get("llm") or {}).get("used") else "nie",
            "czas [s]": r.get("seconds"),
            "błąd": r.get("error") or "",
        }
    )
st.dataframe(rows, hide_index=True, width="stretch")
st.download_button("Pobierz wszystkie JSON-y (ZIP)", data=zip_outputs(results), file_name="output.zip", mime="application/zip")

# --- per document: source page | extracted data ---------------------------------------------

for name, r in results.items():
    st.divider()
    doc_type = r.get("document_type")
    st.markdown(f"### {name} — `{doc_type or 'nierozpoznany'}`")
    if r.get("error"):
        st.error(r["error"])
        continue
    st.caption(llm_summary(r))

    fields = r.get("fields") or {}
    pages = r.get("pages_text") or []
    page_count = (r.get("ingestion") or {}).get("page_count") or len(pages) or 1
    ocr_pages = set((r.get("ingestion") or {}).get("ocr_pages") or [])

    left, right = st.columns([1, 1], gap="large")

    with right:
        found_paths = [p for p, f in fields.items() if f.get("value") is not None]
        selected = st.selectbox(
            "Pokaż źródło pola",
            ["—"] + found_paths,
            key=f"field-{name}",
            help="Wybierz pole, aby zobaczyć stronę i fragment dokumentu, z którego pochodzi wartość.",
        )
        trace = fields.get(selected) if selected != "—" else None
        if trace:
            st.info(
                f"**{selected}** = `{json.dumps(trace.get('value'), ensure_ascii=False)}`  \n"
                f"źródło: {METHOD_LABELS.get(trace.get('method'), trace.get('method'))} · "
                f"{trace.get('rule') or ''} · strona {trace.get('page') or '—'}"
            )
            if trace.get("snippet"):
                st.code(trace["snippet"], language=None)
            for warning in trace.get("warnings") or []:
                st.caption(f"⚠ {warning}")

        tab_json, tab_fields, tab_class = st.tabs(["JSON (UZP)", "Wszystkie pola", "Klasyfikacja"])
        with tab_json:
            st.json(r["output"], expanded=True)
            st.download_button(
                "Pobierz JSON", data=output_json(r) + "\n", file_name=f"{Path(name).stem}.json",
                mime="application/json", key=f"dl-{name}",
            )
        with tab_fields:
            if not fields:
                st.info("Brak pól — dokument nierozpoznany.")
            else:
                st.dataframe(
                    [
                        {
                            "pole": path,
                            "wartość": json.dumps(f["value"], ensure_ascii=False) if f.get("value") is not None else "null",
                            "źródło": METHOD_LABELS.get(f.get("method"), f.get("method")),
                            "strona": f.get("page"),
                            "ostrzeżenia": "; ".join(f.get("warnings") or []),
                        }
                        for path, f in fields.items()
                    ],
                    hide_index=True,
                    width="stretch",
                )
                st.caption("`null` = wartość nie została znaleziona (nigdy nie jest zgadywana).")
        with tab_class:
            classification = r.get("classification") or {}
            st.write(f"**Decyzja:** {doc_type or 'nierozpoznany'} — {classification.get('reason', '')}")
            st.dataframe(
                [
                    {
                        "typ": t,
                        "wynik": s["score"],
                        "nagłówek": s.get("title") or "",
                        "słowa kluczowe": ", ".join(s.get("keywords") or []),
                        "wykluczony przez": s.get("excluded_by") or "",
                    }
                    for t, s in sorted((classification.get("scores") or {}).items(), key=lambda kv: -kv[1]["score"])
                ],
                hide_index=True,
                width="stretch",
            )

    with left:
        default_page = (trace or {}).get("page") or 1
        number = st.number_input(
            f"Strona (z {page_count})", min_value=1, max_value=max(page_count, 1),
            value=min(default_page, max(page_count, 1)), key=f"page-{name}-{selected}",
        )
        if number in ocr_pages:
            st.caption("Strona odczytana przez OCR (skan).")
        image = render_page(files[name], int(number)) if name in files else None
        if image:
            st.image(image, width="stretch")
        elif pages:
            st.code(pages[int(number) - 1] or "(brak tekstu)", language=None)
