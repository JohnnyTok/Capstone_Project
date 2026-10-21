import pandas as pd
import numpy as np
import io
import logging
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import translation  # <--- CORRECTED: Matches your filename 'translation.py'
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 1. CACHE THE MODELS ──────────────────────────────────────────────

@st.cache_resource
def get_vader_analyzer():
    """Loads VADER rule-based model into memory."""
    return SentimentIntensityAnalyzer()

@st.cache_resource
def get_roberta_analyzer():
    """
    Loads the RoBERTa model into memory. 
    Using top_k=None forces the model to return scores for all 3 labels 
    (Positive, Negative, Neutral) instead of just the highest one.
    """
    try:
        # This specific model uses LABEL_0 (Neg), LABEL_1 (Neu), LABEL_2 (Pos)
        return pipeline(
            "text-classification", 
            model="cardiffnlp/twitter-roberta-base-sentiment", 
            top_k=None,
            truncation=True, # Prevents crashes if a review is too long
            max_length=512
        )
    except Exception as e:
        logger.error(f"Failed to load RoBERTa: {e}")
        return None

# --- 2. DATA LOADING ---
def load_data(uploaded_file):
    """
    Load data from CSV or Excel file and validate required columns.
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            logger.warning(f"Unsupported file type: {uploaded_file.name}")
            return None

        if 'Review' not in df.columns:
            # Try to find a close match (case-insensitive)
            matches = [c for c in df.columns if c.strip().lower() == 'review']
            if matches:
                df = df.rename(columns={matches[0]: 'Review'})
                logger.info(f"Renamed column '{matches[0]}' to 'Review'")
            else:
                logger.warning("No 'Review' column found in uploaded file.")
                return None

        df = df.dropna(subset=['Review'])
        df = df[df['Review'].astype(str).str.strip() != '']
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

# --- 3. SENTIMENT ANALYSIS CORE (MERGED) ---
def analyze_sentiment_batch(texts, pos_thresh=0.2, neg_thresh=-0.1, engine=None):
    # Use the session state engine if the argument is None
    if engine is None:
        engine = st.session_state.get("engine", "VADER")

    engine_name = "RoBERTa" if "roberta" in str(engine).lower() else "VADER"
    logger.info(f"DEBUG: Analysis running with engine string: '{engine}'")
    engine_name = "RoBERTa" if "RoBERTa" in str(engine) else "VADER"
    logger.info(f"Processing {len(texts)} reviews. Engine: {engine_name}")
    
    # --- TRANSLATION STEP ---
    processed_reviews = translation.batch_translate(texts) 
    
    scores = []
    labels = []

    # --- RoBERTa PATH ---
    if engine_name == "RoBERTa":
        roberta = get_roberta_analyzer()
        
        if roberta is None:
            logger.warning("RoBERTa unavailable, falling back to VADER.")
            # Explicitly call VADER path to avoid recursion issues
            return analyze_sentiment_batch(texts, pos_thresh, neg_thresh, engine="VADER")

        try:
            valid_texts = [str(t) if isinstance(t, str) and t.strip() else "Neutral" for t in processed_reviews]
            results = roberta(valid_texts, batch_size=16)
            
            for res in results:
                p_pos, p_neg = 0.0, 0.0
                for dict_score in res:
                    if dict_score['label'] == 'LABEL_2': p_pos = dict_score['score']
                    elif dict_score['label'] == 'LABEL_0': p_neg = dict_score['score']
                
                compound_score = p_pos - p_neg
                scores.append(compound_score)

                if compound_score >= pos_thresh: labels.append("Positive")
                elif compound_score <= neg_thresh: labels.append("Negative")
                else: labels.append("Neutral")
                
        except Exception as e:
            logger.error(f"RoBERTa analysis error: {e}")
            # Ensure lists match the length of input even on error
            scores = [0] * len(processed_reviews)
            labels = ["Neutral"] * len(processed_reviews)

    # --- VADER PATH ---
    else: 
        vader = get_vader_analyzer()
        for text in processed_reviews:
            if not isinstance(text, str) or not text.strip():
                scores.append(0)
                labels.append("Neutral")
                continue
                
            compound_score = vader.polarity_scores(text)['compound']
            scores.append(compound_score)
            
            if compound_score >= pos_thresh: labels.append("Positive")
            elif compound_score <= neg_thresh: labels.append("Negative")
            else: labels.append("Neutral")

    return scores, labels


# --- 4. METRICS CALCULATION ---
def calculate_metrics(df):
    """
    Calculate summary statistics for the dashboard
    """
    if df is None or 'Sentiment Score' not in df.columns:
        return {}
        
    total = len(df)
    positive = len(df[df['Sentiment Label'] == 'Positive'])
    negative = len(df[df['Sentiment Label'] == 'Negative'])
    neutral = len(df[df['Sentiment Label'] == 'Neutral'])
    
    return {
        'total_reviews': total,
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'positive_percentage': (positive / total * 100) if total > 0 else 0,
        'negative_percentage': (negative / total * 100) if total > 0 else 0,
        'neutral_percentage': (neutral / total * 100) if total > 0 else 0,
        'avg_score': df['Sentiment Score'].mean(),
        'std_deviation': df['Sentiment Score'].std(),
        'min_score': df['Sentiment Score'].min(),
        'max_score': df['Sentiment Score'].max()
    }

# --- 5. VISUALIZATION (PLOTLY) ---
def plot_sentiment_distribution(df):
    """
    Generate an Interactive Plotly Pie Chart (Donut Style)
    """
    if df is None: return None
    
    counts = df['Sentiment Label'].value_counts().reset_index()
    counts.columns = ['Label', 'Count']
    
    # Custom Color Map
    color_map = {'Positive': '#16A34A', 'Negative': '#DC2626', 'Neutral': '#F97316'}
    
    fig = px.pie(
        counts, 
        names='Label', 
        values='Count',
        color='Label',
        color_discrete_map=color_map,
        hole=0.4, # Makes it a Donut chart
        title="Sentiment Distribution"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#CBD5E1",
        margin=dict(t=40, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig

def plot_score_histogram(df, pos_thresh, neg_thresh):
    """
    Generate an Interactive Plotly Histogram
    """
    if df is None: return None
    
    fig = px.histogram(
        df, 
        x='Sentiment Score', 
        nbins=20,
        color_discrete_sequence=['#F97316'],
        title="Score Distribution"
    )
    
    # Add Threshold Lines
    fig.add_vline(x=pos_thresh, line_dash="dash", line_color="#16A34A", annotation_text="Pos")
    fig.add_vline(x=neg_thresh, line_dash="dash", line_color="#DC2626", annotation_text="Neg")
    
    fig.update_layout(
        xaxis_title="Sentiment Score",
        yaxis_title="Count",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#CBD5E1",
        margin=dict(t=40, b=0, l=0, r=0),
        bargap=0.1
    )
    return fig

# --- 6. DATABASE HISTORY ---
def save_analysis_history(user_id: int, filename: str, source: str, metrics: dict) -> None:
    """
    Persist a summary of a completed analysis to the analyses history table.
    """
    try:
        import db
        conn = db.get_conn()
        conn.execute(
            """INSERT INTO analyses
               (user_id, filename, source, total_reviews, positive_pct,
                negative_pct, neutral_pct, avg_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                filename or "link",
                source,
                metrics.get("total_reviews", 0),
                metrics.get("positive_percentage", 0),
                metrics.get("negative_percentage", 0),
                metrics.get("neutral_percentage", 0),
                metrics.get("avg_score", 0),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"Could not save analysis history: {e}")
    # Notice the finally: block is completely deleted from here!

def get_analysis_history(user_id: int, limit: int = 20) -> list:
    """Return the last `limit` analyses for a user, newest first."""
    try:
        import db
        conn = db.get_conn()
        cursor = conn.execute(
            """SELECT filename, source, total_reviews, positive_pct,
                      negative_pct, avg_score, created_at
               FROM analyses
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"Could not fetch analysis history: {e}")
        return []
    # The finally: block is deleted from here too!

# --- 7. REPORT GENERATION ---
class ReportGenerator:
    """
    Class to handle PDF and Excel export
    """
    
    def generate_excel_report(self, df, metrics):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Raw Data', index=False)
            summary_df = pd.DataFrame([metrics])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        return output.getvalue()

    def generate_pdf_report(self, df, metrics):
        try:
            from fpdf import FPDF
            from datetime import datetime
            
            pdf = FPDF()
            pdf.add_page()
            
            # Fonts & Setup
            pdf.set_font('Arial', '', 12)
            
            # Title
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(190, 10, 'Product Sentiment Analysis Report', 0, 1, 'C')
            pdf.ln(5)
            
            # Date
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(190, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            pdf.ln(5)
            
            # Executive Summary
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(190, 10, 'Executive Summary:', 0, 1)
            pdf.set_font('Arial', '', 11)
            pdf.cell(190, 8, f"Total Reviews Analyzed: {metrics['total_reviews']}", 0, 1)
            pdf.cell(190, 8, f"Average Sentiment Score: {metrics['avg_score']:.3f}", 0, 1)
            pdf.cell(190, 8, f"Positive Feedback: {metrics['positive_percentage']:.1f}%", 0, 1)
            pdf.cell(190, 8, f"Negative Feedback: {metrics['negative_percentage']:.1f}%", 0, 1)
            pdf.cell(190, 8, f"Neutral Feedback: {metrics['neutral_percentage']:.1f}%", 0, 1)
            
            # Conclusion Logic
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(190, 10, 'AI Conclusion:', 0, 1)
            pdf.set_font('Arial', '', 11)
            
            if metrics['avg_score'] > 0.2:
                conclusion = "The product has received generally positive feedback. Customers are satisfied."
            elif metrics['avg_score'] < -0.1:
                conclusion = "The product is facing criticism. Immediate attention to quality is recommended."
            else:
                conclusion = "The product reception is mixed/neutral. Monitoring is advised."
                
            pdf.multi_cell(190, 8, conclusion)
            
            # Sample Reviews
            if 'Review' in df.columns and len(df) > 0:
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(190, 10, 'Sample Reviews (Top 3 Positive & Negative):', 0, 1)
                
                def clean_text(text):
                    return str(text).encode('latin-1', 'replace').decode('latin-1')

                # Positive
                pos_samples = df[df['Sentiment Label'] == 'Positive'].head(3)
                if not pos_samples.empty:
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(190, 8, 'Positive:', 0, 1)
                    pdf.set_font('Arial', '', 9)
                    for _, row in pos_samples.iterrows():
                        txt = clean_text(row['Review'])[:100] + "..."
                        pdf.cell(190, 6, f"- {txt} ({row['Sentiment Score']:.2f})", 0, 1)
                
                pdf.ln(3)

                # Negative
                neg_samples = df[df['Sentiment Label'] == 'Negative'].head(3)
                if not neg_samples.empty:
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(190, 8, 'Negative:', 0, 1)
                    pdf.set_font('Arial', '', 9)
                    for _, row in neg_samples.iterrows():
                        txt = clean_text(row['Review'])[:100] + "..."
                        pdf.cell(190, 6, f"- {txt} ({row['Sentiment Score']:.2f})", 0, 1)

            # Return binary bytes with Latin-1 encoding
            return pdf.output(dest='S').encode('latin-1')
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(190, 10, f"Error generating report: {str(e)}", 0, 1)
            return pdf.output(dest='S').encode('latin-1')