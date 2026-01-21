import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import io
import sys
from pathlib import Path

# Add the project root to the path to import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# IMPORTANT: Import from 'backend', not 'app'
from backend import (
    analyze_sentiment_batch, 
    calculate_metrics,
    load_data,
    plot_sentiment_distribution,
    plot_score_histogram,
    ReportGenerator
)

def test_sentiment_analysis_basic():
    """Test if the AI correctly identifies Positive/Negative/Neutral text"""
    reviews = [
        "This product is amazing!",               # Should be Positive
        "Terrible experience, would not recommend.", # Should be Negative
        "It's okay, nothing special."             # Should be Neutral
    ]
    
    # Run the function
    scores, labels = analyze_sentiment_batch(reviews)
    
    # Assertions (The "Test" part)
    assert len(scores) == len(reviews)
    assert len(labels) == len(reviews)
    
    # Check if labels match expected outcomes
    assert labels[0] == "Positive"
    assert labels[1] == "Negative"
    assert labels[2] == "Neutral"
    
    # Check if scores are valid floats between -1 and 1
    assert all(-1.0 <= score <= 1.0 for score in scores)
    
    # Positive review should have positive score
    assert scores[0] > 0
    # Negative review should have negative score
    assert scores[1] < 0
    # Neutral review should be near zero
    assert -0.1 <= scores[2] <= 0.1

def test_sentiment_analysis_edge_cases():
    """Test sentiment analysis with edge cases"""
    # Test with empty strings
    reviews = ["", "   ", None]
    scores, labels = analyze_sentiment_batch(reviews)
    assert scores == [0.0, 0.0, 0.0]
    assert labels == ["Neutral", "Neutral", "Neutral"]
    
    # Test with very short reviews
    reviews = ["ok", "bad", "good"]
    scores, labels = analyze_sentiment_batch(reviews)
    assert len(scores) == 3
    assert len(labels) == 3
    
    # Test with special characters
    reviews = ["Great! 😊", "Awful... 😞", "Meh 🤷"]
    scores, labels = analyze_sentiment_batch(reviews)
    assert len(scores) == 3
    assert len(labels) == 3

def test_sentiment_analysis_with_thresholds():
    """Test sentiment analysis with custom thresholds"""
    reviews = [
        "This is quite good",      # Score around 0.1-0.2
        "This is quite bad",       # Score around -0.1 to -0.2
        "This is average"          # Score around 0
    ]
    
    # Use custom thresholds
    scores, labels = analyze_sentiment_batch(reviews, positive_thresh=0.15, negative_thresh=-0.15)
    
    # With these thresholds, first should be positive, second negative, third neutral
    assert labels[0] == "Positive"
    assert labels[1] == "Negative"
    assert labels[2] == "Neutral"

def test_metrics_calculation():
    """Test if the math for counting reviews is correct"""
    # Create a fake dataframe
    df = pd.DataFrame({
        'Review': ['Great', 'Bad', 'Okay', 'Excellent', 'Terrible'],
        'Sentiment Score': [0.8, -0.7, 0.1, 0.9, -0.8],
        'Sentiment Label': ['Positive', 'Negative', 'Neutral', 'Positive', 'Negative']
    })
    
    # Run the calculation function
    metrics = calculate_metrics(df)
    
    # Check the math
    assert metrics['total_reviews'] == 5
    assert metrics['positive_count'] == 2
    assert metrics['negative_count'] == 2
    assert metrics['neutral_count'] == 1
    
    # Check percentages
    assert metrics['positive_percentage'] == 40.0
    assert metrics['negative_percentage'] == 40.0
    assert metrics['neutral_percentage'] == 20.0
    
    # Check Average Score calculation
    # (0.8 - 0.7 + 0.1 + 0.9 - 0.8) / 5 = 0.06
    assert round(metrics['avg_score'], 2) == 0.06
    
    # Check additional metrics
    assert metrics['median_score'] == 0.1  # Median of [0.8, -0.7, 0.1, 0.9, -0.8]
    assert metrics['min_score'] == -0.8
    assert metrics['max_score'] == 0.9
    assert metrics['std_deviation'] > 0  # Should have some variance

def test_metrics_calculation_empty():
    """Test metrics calculation with empty dataframe"""
    df = pd.DataFrame(columns=['Review', 'Sentiment Score', 'Sentiment Label'])
    
    metrics = calculate_metrics(df)
    
    # All metrics should be zero for empty dataframe
    assert metrics['total_reviews'] == 0
    assert metrics['positive_count'] == 0
    assert metrics['negative_count'] == 0
    assert metrics['neutral_count'] == 0
    assert metrics['positive_percentage'] == 0
    assert metrics['negative_percentage'] == 0
    assert metrics['neutral_percentage'] == 0
    assert metrics['avg_score'] == 0.0
    assert metrics['median_score'] == 0.0
    assert metrics['std_deviation'] == 0.0
    assert metrics['min_score'] == 0.0
    assert metrics['max_score'] == 0.0

def test_metrics_calculation_single_review():
    """Test metrics calculation with single review"""
    df = pd.DataFrame({
        'Review': ['Great'],
        'Sentiment Score': [0.8],
        'Sentiment Label': ['Positive']
    })
    
    metrics = calculate_metrics(df)
    
    assert metrics['total_reviews'] == 1
    assert metrics['positive_count'] == 1
    assert metrics['negative_count'] == 0
    assert metrics['neutral_count'] == 0
    assert metrics['positive_percentage'] == 100.0
    assert metrics['avg_score'] == 0.8

def test_data_loading():
    """Test data loading functionality"""
    # Create a mock CSV file in memory
    csv_content = "Review\nGreat product\nTerrible experience\nIt's okay"
    csv_file = io.BytesIO(csv_content.encode())
    csv_file.name = "test.csv"
    
    df = load_data(csv_file)
    
    assert df is not None
    assert len(df) == 3
    assert 'Review' in df.columns
    assert list(df['Review']) == ['Great product', 'Terrible experience', "It's okay"]

def test_data_loading_missing_review_column():
    """Test data loading with missing Review column"""
    # Create a mock CSV file without Review column
    csv_content = "Comment\nGreat product\nTerrible experience"
    csv_file = io.BytesIO(csv_content.encode())
    csv_file.name = "test.csv"
    
    df = load_data(csv_file)
    
    # Should return None because 'Review' column is missing
    assert df is None

def test_data_loading_invalid_file():
    """Test data loading with invalid file"""
    # Create an invalid file-like object
    invalid_file = io.BytesIO(b"invalid\x00\x01\x02file")
    invalid_file.name = "invalid.csv"
    
    df = load_data(invalid_file)
    
    # Should handle the error gracefully
    assert df is None

def test_plot_sentiment_distribution():
    """Test sentiment distribution plot generation"""
    df = pd.DataFrame({
        'Review': ['Great', 'Bad', 'Okay'],
        'Sentiment Score': [0.8, -0.7, 0.1],
        'Sentiment Label': ['Positive', 'Negative', 'Neutral']
    })
    
    # This should not raise an exception
    fig = plot_sentiment_distribution(df)
    assert fig is not None
    
    # Test with empty dataframe
    empty_df = pd.DataFrame(columns=['Review', 'Sentiment Score', 'Sentiment Label'])
    fig_empty = plot_sentiment_distribution(empty_df)
    assert fig_empty is not None

def test_plot_score_histogram():
    """Test score histogram plot generation"""
    df = pd.DataFrame({
        'Review': ['Great', 'Bad', 'Okay'],
        'Sentiment Score': [0.8, -0.7, 0.1],
        'Sentiment Label': ['Positive', 'Negative', 'Neutral']
    })
    
    # This should not raise an exception
    fig = plot_score_histogram(df, pos_thresh=0.2, neg_thresh=-0.1)
    assert fig is not None
    
    # Test with empty dataframe
    empty_df = pd.DataFrame(columns=['Review', 'Sentiment Score', 'Sentiment Label'])
    fig_empty = plot_score_histogram(empty_df, pos_thresh=0.2, neg_thresh=-0.1)
    assert fig_empty is not None

def test_report_generator_pdf():
    """Test PDF report generation"""
    df = pd.DataFrame({
        'Review': ['Great product', 'Not good'],
        'Sentiment Score': [0.8, -0.7],
        'Sentiment Label': ['Positive', 'Negative']
    })
    
    metrics = calculate_metrics(df)
    generator = ReportGenerator()
    
    # This should not raise an exception
    pdf_bytes = generator.generate_pdf_report(df, metrics)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

def test_report_generator_excel():
    """Test Excel report generation"""
    df = pd.DataFrame({
        'Review': ['Great product', 'Not good'],
        'Sentiment Score': [0.8, -0.7],
        'Sentiment Label': ['Positive', 'Negative']
    })
    
    metrics = calculate_metrics(df)
    generator = ReportGenerator()
    
    # This should not raise an exception
    excel_bytes = generator.generate_excel_report(df, metrics)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

def test_empty_input():
    """Test how the system handles empty data (Edge Case)"""
    reviews = []
    scores, labels = analyze_sentiment_batch(reviews)
    assert scores == []
    assert labels == []

def test_bad_input():
    """Test how the system handles None/Empty strings"""
    reviews = [None, ""]
    scores, labels = analyze_sentiment_batch(reviews)
    # Backend is designed to return Neutral (0.0) for bad input
    assert labels == ["Neutral", "Neutral"]
    assert scores == [0.0, 0.0]

def test_analyze_sentiment_batch_with_nan():
    """Test sentiment analysis with NaN values"""
    reviews = [float('nan'), "Great product", "Bad experience"]
    scores, labels = analyze_sentiment_batch(reviews)
    assert len(scores) == 3
    assert len(labels) == 3
    # NaN should be treated as empty string, so Neutral
    assert labels[0] == "Neutral"
    assert scores[0] == 0.0
    assert labels[1] == "Positive"
    assert labels[2] == "Negative"

def test_analyze_sentiment_batch_large_input():
    """Test sentiment analysis with large input to check performance"""
    reviews = ["This is great"] * 100  # Large batch
    scores, labels = analyze_sentiment_batch(reviews)
    assert len(scores) == 100
    assert len(labels) == 100
    assert all(label == "Positive" for label in labels)
    assert all(score > 0 for score in scores)

def test_calculate_metrics_with_all_same_sentiment():
    """Test metrics calculation when all reviews have same sentiment"""
    df = pd.DataFrame({
        'Review': ['Great', 'Excellent', 'Wonderful'],
        'Sentiment Score': [0.8, 0.9, 0.7],
        'Sentiment Label': ['Positive', 'Positive', 'Positive']
    })
    
    metrics = calculate_metrics(df)
    assert metrics['total_reviews'] == 3
    assert metrics['positive_count'] == 3
    assert metrics['negative_count'] == 0
    assert metrics['neutral_count'] == 0
    assert metrics['positive_percentage'] == 100.0
    assert metrics['negative_percentage'] == 0.0
    assert metrics['neutral_percentage'] == 0.0

def test_calculate_metrics_with_zero_variance():
    """Test metrics calculation with identical scores"""
    df = pd.DataFrame({
        'Review': ['Review1', 'Review2', 'Review3'],
        'Sentiment Score': [0.5, 0.5, 0.5],
        'Sentiment Label': ['Positive', 'Positive', 'Positive']
    })
    
    metrics = calculate_metrics(df)
    assert metrics['avg_score'] == 0.5
    assert metrics['std_deviation'] == 0.0  # No variance
    assert metrics['min_score'] == 0.5
    assert metrics['max_score'] == 0.5

# Mock test for translation functionality (if translation module is available)
@patch('backend.translator')
def test_analyze_sentiment_with_translation(mock_translator):
    """Test sentiment analysis with translation"""
    # Mock the translation to return the same text
    mock_translator.translate_to_english.return_value = "This is a test review"
    
    reviews = ["C'est un test", "Das ist ein Test"]
    scores, labels = analyze_sentiment_batch(reviews)
    
    # Should not raise an exception and should return results
    assert len(scores) == 2
    assert len(labels) == 2

# Parametrized test for different threshold combinations
@pytest.mark.parametrize("pos_thresh,neg_thresh,review,expected_label", [
    (0.2, -0.1, "This is amazing", "Positive"),
    (-0.1, -0.2, "This is okay", "Positive"),  # With different thresholds
    (0.2, -0.1, "This is terrible", "Negative"),
    (0.3, -0.3, "This is okay", "Neutral"),
])
def test_sentiment_with_different_thresholds(pos_thresh, neg_thresh, review, expected_label):
    """Test sentiment analysis with different threshold combinations"""
    scores, labels = analyze_sentiment_batch([review], pos_thresh, neg_thresh)
    assert labels[0] == expected_label