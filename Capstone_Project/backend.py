import pandas as pd
import numpy as np
import io
import logging
import plotly.express as px
import plotly.graph_objects as go
import translation  # <--- CORRECTED: Matches your filename 'translation.py'

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. DATA LOADING ---
def load_data(uploaded_file):
    """
    Load data from CSV or Excel file
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            return None
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

# --- 2. SENTIMENT ANALYSIS CORE ---
def analyze_sentiment_batch(reviews, pos_threshold=0.2, neg_threshold=-0.1):
    """
    Analyze a list of reviews using VADER, with Auto-Translation.
    """
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
    
    # Download VADER lexicon if not present
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon')
        
    sid = SentimentIntensityAnalyzer()
    
    # --- TRANSLATION STEP (UPDATED) ---
    logger.info(f"Processing {len(reviews)} reviews with auto-translation...")
    
    # We now call 'translation' instead of 'translator'
    processed_reviews = translation.batch_translate(reviews) 
    # ----------------------------------
    
    scores = []
    labels = []
    
    for text in processed_reviews:
        if not isinstance(text, str):
            scores.append(0)
            labels.append("Neutral")
            continue
            
        # Get compound score
        score = sid.polarity_scores(text)['compound']
        scores.append(score)
        
        # Labeling
        if score > pos_threshold:
            labels.append("Positive")
        elif score < neg_threshold:
            labels.append("Negative")
        else:
            labels.append("Neutral")
            
    return scores, labels

# --- 3. METRICS CALCULATION ---
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

# --- 4. VISUALIZATION (PLOTLY) ---
def plot_sentiment_distribution(df):
    """
    Generate an Interactive Plotly Pie Chart (Donut Style)
    """
    if df is None: return None
    
    counts = df['Sentiment Label'].value_counts().reset_index()
    counts.columns = ['Label', 'Count']
    
    # Custom Color Map
    color_map = {'Positive': '#4CAF50', 'Negative': '#F44336', 'Neutral': '#FF9800'}
    
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
        font_color="white",
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
        color_discrete_sequence=['#5d5fef'],
        title="Score Distribution"
    )
    
    # Add Threshold Lines
    fig.add_vline(x=pos_thresh, line_dash="dash", line_color="#4CAF50", annotation_text="Pos")
    fig.add_vline(x=neg_thresh, line_dash="dash", line_color="#F44336", annotation_text="Neg")
    
    fig.update_layout(
        xaxis_title="Sentiment Score",
        yaxis_title="Count",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white",
        margin=dict(t=40, b=0, l=0, r=0),
        bargap=0.1
    )
    return fig

# --- 5. REPORT GENERATION ---
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
