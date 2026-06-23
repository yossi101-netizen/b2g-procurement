"""
dashboard.py — B2G Tender Review Dashboard
Visual interface for analyst review of matched tenders.
Connect to tenders.db, mark tenders as KEEP/DROP, and download PDFs.

Usage:
  streamlit run T-tools/dashboard.py
"""
import streamlit as st
import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Optional, List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "tenders.db")

# ══════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════

def get_db_connection():
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_disposition_column():
    """Add analyst_disposition column if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(tenders)")
    columns = [row[1] for row in cursor.fetchall()]

    if "analyst_disposition" not in columns:
        cursor.execute("""
            ALTER TABLE tenders
            ADD COLUMN analyst_disposition TEXT DEFAULT NULL
        """)
        conn.commit()

    conn.close()

def get_matched_tenders(filter_disposition: str = "UNMARKED") -> List[dict]:
    """
    Fetch matched tenders from database.

    Args:
        filter_disposition: "UNMARKED" (None or not set), "KEEP", "DROP", or "ALL"
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if filter_disposition == "ALL":
        where = "WHERE keyword_verdict='MATCH'"
    elif filter_disposition == "UNMARKED":
        where = "WHERE keyword_verdict='MATCH' AND (analyst_disposition IS NULL OR analyst_disposition='')"
    else:
        where = f"WHERE keyword_verdict='MATCH' AND analyst_disposition='{filter_disposition}'"

    cursor.execute(f"""
        SELECT tender_id, title, category, deadline, publisher, status,
               pub_date, url, attachments, first_seen, analyst_disposition
        FROM tenders {where}
        ORDER BY deadline ASC NULLS LAST
    """)

    tenders = []
    for row in cursor.fetchall():
        tenders.append({
            "tender_id": row[0],
            "title": row[1],
            "category": row[2],
            "deadline": row[3],
            "publisher": row[4],
            "status": row[5],
            "pub_date": row[6],
            "url": row[7],
            "attachments": json.loads(row[8]) if row[8] else [],
            "first_seen": row[9],
            "analyst_disposition": row[10],
        })

    conn.close()
    return tenders

def update_disposition(tender_id: str, disposition: str):
    """Update the analyst_disposition for a tender."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        UPDATE tenders
        SET analyst_disposition=?, last_updated=?
        WHERE tender_id=?
    """, (disposition, now, tender_id))

    conn.commit()
    conn.close()

def get_summary_stats() -> dict:
    """Get summary statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tenders WHERE keyword_verdict='MATCH'")
    total_match = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tenders WHERE keyword_verdict='MATCH' AND (analyst_disposition IS NULL OR analyst_disposition='')")
    unmarked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tenders WHERE keyword_verdict='MATCH' AND analyst_disposition='KEEP'")
    kept = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tenders WHERE keyword_verdict='MATCH' AND analyst_disposition='DROP'")
    dropped = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tenders WHERE keyword_verdict='MATCH' AND deadline IS NOT NULL AND deadline >= DATE('now')")
    active = cursor.fetchone()[0]

    conn.close()

    return {
        "total_match": total_match,
        "unmarked": unmarked,
        "kept": kept,
        "dropped": dropped,
        "active": active,
    }

# ══════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════

def render_tender_card(tender: dict, col):
    """Render a single tender card."""
    with col:
        # Header
        with st.container(border=True):
            # Title and category
            st.markdown(f"**[{tender['tender_id']}] {tender['title']}**")

            # Metadata row
            col1, col2, col3 = st.columns(3)
            with col1:
                if tender['category']:
                    st.caption(f"📂 {tender['category']}")
                else:
                    st.caption("📂 uncategorized")

            with col2:
                if tender['deadline']:
                    st.caption(f"📅 {tender['deadline']}")
                else:
                    st.caption("📅 N/A")

            with col3:
                if tender['publisher']:
                    st.caption(f"🏢 {tender['publisher'][:20]}")
                else:
                    st.caption("🏢 —")

            # URL
            st.markdown(f"🔗 [View Tender]({tender['url']})")

            # Attachments
            if tender['attachments']:
                st.markdown(f"📄 **{len(tender['attachments'])} documents**")
                for i, att in enumerate(tender['attachments'][:3]):
                    label = att.get('label', 'download')
                    url = att['url']
                    st.markdown(f"  - [{label}]({url})")
                if len(tender['attachments']) > 3:
                    st.caption(f"  ... and {len(tender['attachments']) - 3} more")

            # Current disposition
            disp = tender['analyst_disposition'] or "UNMARKED"
            status_color = {"KEEP": "🟢", "DROP": "🔴", "UNMARKED": "⚪"}.get(disp, "⚪")
            st.caption(f"Status: {status_color} {disp}")

            # Buttons
            b1, b2, b3 = st.columns(3)

            with b1:
                if st.button("✅ KEEP", key=f"keep_{tender['tender_id']}", use_container_width=True):
                    update_disposition(tender['tender_id'], "KEEP")
                    st.rerun()

            with b2:
                if st.button("❌ DROP", key=f"drop_{tender['tender_id']}", use_container_width=True):
                    update_disposition(tender['tender_id'], "DROP")
                    st.rerun()

            with b3:
                if disp != "UNMARKED":
                    if st.button("🔄 RESET", key=f"reset_{tender['tender_id']}", use_container_width=True):
                        update_disposition(tender['tender_id'], "")
                        st.rerun()

def main():
    st.set_page_config(page_title="B2G Tender Dashboard", layout="wide")

    # Initialize database
    ensure_disposition_column()

    # Title
    st.title("🎯 B2G Israeli Tender Review Dashboard")
    st.markdown("Review and mark matched tenders as KEEP or DROP for bid evaluation.")

    # Summary stats
    stats = get_summary_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Matched", stats['total_match'])
    with col2:
        st.metric("Active", stats['active'])
    with col3:
        st.metric("Unmarked", stats['unmarked'], delta=-1 if stats['unmarked'] > 0 else None)
    with col4:
        st.metric("Kept", stats['kept'], delta=1 if stats['kept'] > 0 else None)
    with col5:
        st.metric("Dropped", stats['dropped'])

    st.divider()

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")

        filter_disposition = st.radio(
            "Show tenders:",
            options=["UNMARKED", "KEEP", "DROP", "ALL"],
            horizontal=True
        )

        filter_category = st.multiselect(
            "Filter by category:",
            options=["leather_slg", "uniforms", "footwear", "tactical", "promotional", "bags_cases", "_uncategorized"],
            default=None
        )

        show_active_only = st.checkbox("Active tenders only (deadline not passed)", value=True)

    # Fetch tenders
    tenders = get_matched_tenders(filter_disposition)

    # Apply additional filters
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if filter_category:
        tenders = [t for t in tenders if t['category'] in filter_category]

    if show_active_only:
        tenders = [t for t in tenders if t['deadline'] is None or t['deadline'] >= today]

    # Display tenders
    if not tenders:
        st.info(f"No tenders matching filters. Try adjusting your selection.")
    else:
        st.subheader(f"📋 Showing {len(tenders)} tender(s)")

        # Display as cards in a grid (2 columns)
        cols = st.columns(2)
        for i, tender in enumerate(tenders):
            col = cols[i % 2]
            render_tender_card(tender, col)

if __name__ == "__main__":
    main()
