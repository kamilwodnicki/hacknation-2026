"""Streamlit UI: upload PDFs, see the UZP JSON and how every value was obtained.

Talks to the API (API_URL); run with `docker compose up -d` -> http://localhost:8501
"""

import io
import json
import os
import zipfile
from pathlib import Path

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 600  # OCR of a long scan can take minutes on a CPU

st.set_page_config(page_title="Odwołania2json", page_icon="📄", layout="wide")


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
        detail = response.json().get("detail", response.text) if response.headers.get("content-type", "").startswith("application/json") else response.text
        raise RuntimeError(f"{response.status_code}: {detail}")
    return response.json()


def output_json(result: dict) -> str:
    return json.dumps(result["output"], ensure_ascii=False, indent=2)


def zip_outputs(results: dict[str, dict]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, result in results.items():
            archive.writestr(f"{Path(name).stem}.json", output_json(result) + "\n")
    return buffer.getvalue()


# --- sidebar ------------------------------------------------------------------------------

with st.sidebar:
    st.header("Odwołania2json")
    st.caption("PDF ze sprawy odwoławczej KIO → JSON w formacie UZP")
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

st.title("Ekstrakcja danych z dokumentów KIO")
st.write(
    "Wgraj dokumenty sprawy (odwołanie, pełnomocnictwo, potwierdzenie przelewu — PDF cyfrowe lub skany). "
    "Dokumenty spoza obsługiwanych klas dają pusty JSON."
)

uploaded = st.file_uploader("Pliki PDF", type=["pdf"], accept_multiple_files=True)
results: dict[str, dict] = st.session_state.setdefault("results", {})

if st.button("Przetwórz", type="primary", disabled=not uploaded):
    results.clear()
    progress = st.progress(0.0, text="Przetwarzanie…")
    for index, file in enumerate(uploaded, start=1):
        progress.progress((index - 1) / len(uploaded), text=f"Przetwarzanie {file.name} ({index}/{len(uploaded)})…")
        try:
            results[file.name] = api_extract(file.name, file.getvalue())
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
            "czas [s]": r.get("seconds"),
            "błąd": r.get("error") or "",
        }
    )
st.dataframe(rows, hide_index=True, use_container_width=True)
st.download_button(
    "Pobierz wszystkie JSON-y (ZIP)",
    data=zip_outputs(results),
    file_name="output.zip",
    mime="application/zip",
)

# --- per document -------------------------------------------------------------------------

for name, r in results.items():
    st.divider()
    doc_type = r.get("document_type")
    st.markdown(f"### {name} — `{doc_type or 'nierozpoznany'}`")
    if r.get("error"):
        st.error(r["error"])
        continue

    tab_json, tab_fields, tab_class, tab_text = st.tabs(
        ["JSON (UZP)", "Pochodzenie wartości", "Klasyfikacja", "Tekst dokumentu"]
    )

    with tab_json:
        st.json(r["output"], expanded=True)
        st.download_button(
            "Pobierz JSON",
            data=output_json(r) + "\n",
            file_name=f"{Path(name).stem}.json",
            mime="application/json",
            key=f"dl-{name}",
        )

    with tab_fields:
        fields = r.get("fields") or {}
        if not fields:
            st.info("Brak pól — dokument nierozpoznany.")
        else:
            only_found = st.toggle("Tylko znalezione wartości", value=False, key=f"found-{name}")
            table = [
                {
                    "pole": path,
                    "wartość": json.dumps(f["value"], ensure_ascii=False) if f.get("value") is not None else "null",
                    "metoda": f.get("method") or "—",
                    "reguła": f.get("rule") or "",
                    "strona": f.get("page"),
                    "fragment źródłowy": (f.get("snippet") or "").replace("\n", " ⏎ "),
                    "ostrzeżenia": "; ".join(f.get("warnings") or []),
                }
                for path, f in fields.items()
                if not only_found or f.get("value") is not None
            ]
            st.dataframe(
                table,
                hide_index=True,
                use_container_width=True,
                column_config={"fragment źródłowy": st.column_config.TextColumn(width="large")},
            )
            st.caption(
                "Każda wartość ma wskazaną regułę z pliku YAML, numer strony i fragment tekstu, z którego pochodzi. "
                "`null` = wartość nie została znaleziona (nigdy nie jest zgadywana)."
            )

    with tab_class:
        classification = r.get("classification") or {}
        st.write(f"**Decyzja:** {doc_type or 'nierozpoznany'} — {classification.get('reason', '')}")
        scores = classification.get("scores") or {}
        st.dataframe(
            [
                {
                    "typ": t,
                    "wynik": s["score"],
                    "nagłówek": s.get("title") or "",
                    "słowa kluczowe": ", ".join(s.get("keywords") or []),
                    "wykluczony przez": s.get("excluded_by") or "",
                }
                for t, s in sorted(scores.items(), key=lambda kv: -kv[1]["score"])
            ],
            hide_index=True,
            use_container_width=True,
        )

    with tab_text:
        pages = r.get("pages_text") or []
        ocr_pages = set((r.get("ingestion") or {}).get("ocr_pages") or [])
        if pages:
            number = st.selectbox(
                "Strona",
                range(1, len(pages) + 1),
                format_func=lambda n: f"{n}" + (" (OCR)" if n in ocr_pages else ""),
                key=f"page-{name}",
            )
            st.code(pages[number - 1] or "(brak tekstu)", language=None)
