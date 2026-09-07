from html import escape

import streamlit as st

from dndnd.models import Campaign


def render_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #20251f;
            --muted-ink: #697066;
            --parchment: #f7f3e8;
            --paper: #fffdf7;
            --sage: #e4e8d8;
            --brass: #a9782f;
            --ember: #b4472d;
            --line: rgba(32, 37, 31, 0.14);
        }
        .block-container { max-width: 1440px; padding-top: 2rem; }
        [data-testid="stSidebar"] { border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        h1, h2, h3, h4 { letter-spacing: 0; color: var(--ink); }
        p, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
        .campaign-hero {
            position: relative; overflow: hidden; padding: 2rem 2.2rem 1.8rem;
            margin: 0 0 1.5rem; border: 1px solid var(--line); border-radius: 8px;
            background: linear-gradient(115deg, var(--paper) 0%, var(--sage) 100%);
            box-shadow: 0 12px 30px rgba(32, 37, 31, 0.06);
        }
        .campaign-hero::after {
            content: "✦"; position: absolute; right: 5%; top: 12%; color: var(--brass);
            font-size: 7rem; line-height: 1; opacity: .14; transform: rotate(18deg);
        }
        .campaign-hero .eyebrow, .brief-card .eyebrow {
            color: var(--ember); font-size: .72rem; font-weight: 700; letter-spacing: .12em;
            text-transform: uppercase;
        }
        .campaign-hero h1 { margin: .35rem 0 .5rem; font-size: clamp(2rem, 4vw, 3.4rem); }
        .campaign-hero p {
            max-width: 58rem; margin: 0; color: var(--muted-ink); font-size: 1.05rem;
        }
        .hero-meta { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.2rem; }
        .hero-meta span {
            padding: .35rem .7rem; border: 1px solid var(--line); border-radius: 999px;
            background: rgba(255, 253, 247, .7); color: var(--muted-ink); font-size: .82rem;
        }
        .brief-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .brief-card {
            min-height: 9rem; padding: 1.15rem 1.25rem; border-top: 3px solid var(--brass);
            background: var(--paper); box-shadow: 0 6px 18px rgba(32, 37, 31, .05);
        }
        .brief-card h3 { margin: .45rem 0 .35rem; font-size: 1.2rem; }
        .brief-card p { margin: 0; color: var(--muted-ink); font-size: .92rem; line-height: 1.5; }
        .empty-callout {
            padding: 1rem 1.2rem; border-left: 4px solid var(--ember); background: var(--paper);
            color: var(--muted-ink); font-size: .95rem;
        }
        @media (max-width: 800px) {
            .block-container { padding: 1rem .8rem 2rem; }
            .campaign-hero { padding: 1.35rem; }
            .brief-grid { grid-template-columns: 1fr; }
            .campaign-hero::after { font-size: 4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_campaign_briefing(campaign: Campaign) -> None:
    name = escape(campaign.name)
    summary = escape(
        campaign.summary or "A new campaign waits for its first mark in the chronicle."
    )
    st.markdown(
        f"""
        <section class="campaign-hero">
            <div class="eyebrow">Campaign briefing · D&D 5e (2024)</div>
            <h1>{name}</h1>
            <p>{summary}</p>
            <div class="hero-meta">
                <span>⌖ Local campaign desk</span>
                <span>✦ Player-facing stories</span>
                <span>◈ DM-only state</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
