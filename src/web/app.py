from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Endometriosis Evidence Dashboard", layout="wide")

st.title("🔬 Endometriosis Treatment Evidence Landscape")
st.caption("Powered by PubMed + Gemini · mama health AI Data Engineer Challenge")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "View",
    [
        "Treatment-Outcome Matrix",
        "Publication Trends",
        "MeSH Network",
        "Research Geography",
        "Knowledge Graph",
        "Population Profile",
        "Funding Landscape",
    ],
)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    st.error("DATABASE_URL not set. Make sure the environment variable is configured.")
    st.stop()

engine = create_engine(DATABASE_URL)


def load_analytics(name: str) -> list | dict | None:
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT payload FROM analytics_result WHERE name = :name"), {"name": name}
            ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


if page == "Treatment-Outcome Matrix":
    st.header("Treatment-Outcome Matrix")
    data = load_analytics("treatment_outcome_matrix")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        df = pd.DataFrame(data)
        pivot = df.pivot_table(
            index="treatment", columns="outcome", values="frequency", fill_value=0
        )
        top_treatments = df.groupby("treatment")["frequency"].sum().nlargest(20).index
        pivot = pivot.loc[pivot.index.isin(top_treatments)]
        fig = px.imshow(
            pivot,
            color_continuous_scale="Blues",
            title="Treatment × Outcome Co-occurrence",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.head(50))

elif page == "Publication Trends":
    import plotly.express as px

    st.header("Publication Trends Over Time")
    data = load_analytics("publication_trend_analysis")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        df = pd.DataFrame(data)
        fig = px.line(df, x="year", y="article_count", title="Endometriosis Publications Per Year")
        st.plotly_chart(fig, use_container_width=True)
        fig2 = px.bar(df, x="year", y=["rct_count", "review_count", "case_report_count"],
                      title="Study Design Breakdown Per Year", barmode="stack")
        st.plotly_chart(fig2, use_container_width=True)

elif page == "MeSH Network":
    import streamlit.components.v1 as components
    from pyvis.network import Network

    st.header("MeSH Term Co-occurrence Network")
    data = load_analytics("mesh_cooccurrence_network")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        df = pd.DataFrame(data).head(100)
        net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="white")
        for _, row in df.iterrows():
            net.add_node(row["term_a"], label=row["term_a"])
            net.add_node(row["term_b"], label=row["term_b"])
            net.add_edge(row["term_a"], row["term_b"], value=row["co_occurrence_count"])
        net.save_graph("/tmp/mesh_net.html")
        with open("/tmp/mesh_net.html") as f:
            components.html(f.read(), height=620)

elif page == "Research Geography":
    import plotly.express as px

    st.header("Research Geography")
    data = load_analytics("research_geography_analysis")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        df = pd.DataFrame(data)
        fig = px.choropleth(df, locations="country", locationmode="country names",
                            color="article_count", title="Article Count by Country",
                            color_continuous_scale="Viridis")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.head(30))

elif page == "Knowledge Graph":
    st.header("Treatment-Outcome Knowledge Graph")
    data = load_analytics("knowledge_graph_data")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        if isinstance(data, dict):
            nodes = data.get("nodes", [])
            links = data.get("links", data.get("edges", []))
        else:
            nodes = []
            links = []
        st.metric("Nodes", len(nodes))
        st.metric("Edges", len(links))
        df_links = pd.DataFrame(links)
        if not df_links.empty:
            st.dataframe(df_links[["source", "target", "effect_direction"]].head(50))

elif page == "Population Profile":
    st.header("Patient Population Profile")
    data = load_analytics("patient_population_profiling")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        for dimension in data:
            label = dimension["dimension"].replace("_", " ").title()
            values = dimension["values"]
            if values:
                df = pd.DataFrame(values)
                fig = px.bar(df, x="label", y="count", title=label)
                st.plotly_chart(fig, use_container_width=True)

elif page == "Funding Landscape":
    st.header("Funding Landscape")
    data = load_analytics("funding_landscape_analysis")
    if not data:
        st.warning("No data yet — run the pipeline first.")
    else:
        df = pd.DataFrame(data)
        fig = px.bar(
            df.head(30),
            x="article_count",
            y="agency",
            orientation="h",
            title="Top 30 Funding Agencies by Article Count",
            color="country",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.head(50))
