import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="PaperMind", layout="wide")
st.title("PaperMind")
st.caption("Ask questions across your research papers, grounded in what the papers actually say.")

# --- Sidebar: upload + paper selection ---
with st.sidebar:
    st.header("Papers")

    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded and st.button("Ingest"):
        with st.spinner("Parsing and embedding..."):
            res = requests.post(
                f"{API_URL}/papers/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
            )
        if res.ok:
            data = res.json()
            st.success(f"Done — {data['chunks']} chunks indexed")
        else:
            st.error(res.text)

    st.divider()

    try:
        papers_res = requests.get(f"{API_URL}/papers", timeout=3)
        papers = papers_res.json().get("papers", []) if papers_res.ok else []
    except requests.exceptions.ConnectionError:
        st.warning("API is not reachable. Run `make dev-all` to start the backend.")
        papers = []
    selected = st.multiselect("Search in (leave empty for all)", papers)

# --- Chat interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg:
            with st.expander(f"{len(msg['citations'])} source(s)"):
                for c in msg["citations"]:
                    st.markdown(f"**{c['filename']}** — Page {c['page_number']}, Paragraph {c['paragraph_number']} (score: {c['score']})")
                    st.caption(c["excerpt"])

if question := st.chat_input("Ask a question about your papers..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving and generating..."):
            res = requests.post(
                f"{API_URL}/query",
                json={"question": question, "paper_ids": selected or None, "top_k": 5},
            )

        if res.ok:
            data = res.json()
            st.markdown(data["answer"])
            with st.expander(f"{len(data['citations'])} source(s)"):
                for c in data["citations"]:
                    st.markdown(f"**{c['filename']}** — Page {c['page_number']}, Paragraph {c['paragraph_number']} (score: {c['score']})")
                    st.caption(c["excerpt"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": data["answer"],
                "citations": data["citations"],
            })
        else:
            st.error(f"Error: {res.text}")
