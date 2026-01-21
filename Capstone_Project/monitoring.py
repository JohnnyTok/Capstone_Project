import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Union
import logging
from collections import deque
import threading
from dataclasses import dataclass

@dataclass
class SentimentReading:
    """
    Data class to represent a sentiment reading
    """
    timestamp: datetime
    score: float
    label: str = ""
    
    def __post_init__(self):
        # Validate score is within expected range
        if not -1.0 <= self.score <= 1.0:
            raise ValueError(f"Sentiment score must be between -1.0 and 1.0, got {self.score}")

class RealTimeMonitor:
    """
    Advanced real-time monitoring system for sentiment analysis
    """
    def __init__(self, 
                 max_history: int = 100,
                 update_interval: int = 10,
                 threshold_positive: float = 0.2,
                 threshold_negative: float = -0.1):
        """
        Initialize the real-time monitor
        
        Args:
            max_history: Maximum number of readings to keep in history
            update_interval: Number of readings before triggering an update event
            threshold_positive: Threshold for positive sentiment
            threshold_negative: Threshold for negative sentiment
        """
        self.max_history = max_history
        self.update_interval = update_interval
        self.threshold_positive = threshold_positive
        self.threshold_negative = threshold_negative
        self.logger = logging.getLogger(__name__)
        
        # Use deque for efficient append/pop operations
        self.sentiment_history = deque(maxlen=max_history)
        self.timestamp_history = deque(maxlen=max_history)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'total_readings': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'avg_sentiment': 0.0,
            'min_sentiment': 0.0,
            'max_sentiment': 0.0,
            'std_deviation': 0.0
        }
        
        # Alerts
        self.alerts = []
        self.alert_thresholds = {
            'positive_spikes': 0.8,  # Alert when sentiment goes above this
            'negative_spikes': -0.8,  # Alert when sentiment goes below this
            'volatility_threshold': 0.5  # Alert when volatility is above this
        }
    
    def update(self, sentiment_score: float, label: str = "") -> None:
        """
        Add a new sentiment score to the history.
        
        Args:
            sentiment_score: The sentiment score (between -1 and 1)
            label: Optional sentiment label (Positive/Negative/Neutral)
        """
        with self._lock:
            try:
                # Validate input
                if not isinstance(sentiment_score, (int, float)) or not -1.0 <= sentiment_score <= 1.0:
                    raise ValueError(f"Sentiment score must be a number between -1.0 and 1.0, got {sentiment_score}")
                
                timestamp = datetime.now()
                
                # Create reading object
                reading = SentimentReading(timestamp, sentiment_score, label)
                
                # Add to history
                self.sentiment_history.append(sentiment_score)
                self.timestamp_history.append(timestamp)
                
                # Update statistics
                self._update_statistics(sentiment_score)
                
                # Check for alerts
                self._check_alerts(sentiment_score, timestamp)
                
                # Log the update
                self.logger.debug(f"Updated monitor: score={sentiment_score}, label={label}")
                
            except Exception as e:
                self.logger.error(f"Error updating monitor: {e}")
                raise
    
    def _update_statistics(self, new_score: float) -> None:
        """
        Update running statistics with the new score
        
        Args:
            new_score: The new sentiment score to include in statistics
        """
        self._stats['total_readings'] += 1
        
        # Update counts based on thresholds
        if new_score > self.threshold_positive:
            self._stats['positive_count'] += 1
        elif new_score < self.threshold_negative:
            self._stats['negative_count'] += 1
        else:
            self._stats['neutral_count'] += 1
        
        # Update min/max
        if self._stats['total_readings'] == 1:
            self._stats['min_sentiment'] = new_score
            self._stats['max_sentiment'] = new_score
        else:
            self._stats['min_sentiment'] = min(self._stats['min_sentiment'], new_score)
            self._stats['max_sentiment'] = max(self._stats['max_sentiment'], new_score)
        
        # Update average
        self._stats['avg_sentiment'] = (
            (self._stats['avg_sentiment'] * (self._stats['total_readings'] - 1) + new_score) 
            / self._stats['total_readings']
        )
    
    def _check_alerts(self, score: float, timestamp: datetime) -> None:
        """
        Check if any alerts should be triggered based on the new reading
        
        Args:
            score: The new sentiment score
            timestamp: The timestamp of the reading
        """
        # Check for positive spikes
        if score > self.alert_thresholds['positive_spikes']:
            alert = {
                'timestamp': timestamp,
                'type': 'positive_spike',
                'score': score,
                'message': f'Positive sentiment spike detected: {score:.3f}'
            }
            self.alerts.append(alert)
            self.logger.warning(f"Positive spike alert: {alert['message']}")
        
        # Check for negative spikes
        if score < self.alert_thresholds['negative_spikes']:
            alert = {
                'timestamp': timestamp,
                'type': 'negative_spike',
                'score': score,
                'message': f'Negative sentiment spike detected: {score:.3f}'
            }
            self.alerts.append(alert)
            self.logger.warning(f"Negative spike alert: {alert['message']}")
        
        # Check for high volatility (if we have enough data)
        if len(self.sentiment_history) >= 3:
            recent_scores = list(self.sentiment_history)[-3:]  # Last 3 readings
            volatility = np.std(recent_scores)
            if volatility > self.alert_thresholds['volatility_threshold']:
                alert = {
                    'timestamp': timestamp,
                    'type': 'high_volatility',
                    'volatility': volatility,
                    'message': f'High sentiment volatility detected: {volatility:.3f}'
                }
                self.alerts.append(alert)
                self.logger.warning(f"Volatility alert: {alert['message']}")
    
    def create_live_chart(self, 
                         chart_type: str = 'line',
                         show_stats: bool = True,
                         time_window: Optional[int] = None) -> go.Figure:
        """
        Generate the Plotly chart with customizable options
        
        Args:
            chart_type: Type of chart ('line', 'bar', 'scatter')
            show_stats: Whether to show statistical annotations
            time_window: Time window in minutes to show (None for all data)
            
        Returns:
            Plotly figure object
        """
        with self._lock:
            # Convert to lists for processing
            scores = list(self.sentiment_history)
            timestamps = list(self.timestamp_history)
            
            # Apply time window filter if specified
            if time_window and timestamps:
                cutoff_time = datetime.now() - timedelta(minutes=time_window)
                filtered_data = [
                    (t, s) for t, s in zip(timestamps, scores) 
                    if t >= cutoff_time
                ]
                if filtered_data:
                    timestamps, scores = zip(*filtered_data)
                    timestamps = list(timestamps)
                    scores = list(scores)
            
            # Create figure based on chart type
            if chart_type == 'bar':
                fig = go.Figure(data=[
                    go.Bar(
                        x=timestamps,
                        y=scores,
                        name='Sentiment Score',
                        marker_color=[
                            '#4CAF50' if s > self.threshold_positive 
                            else '#F44336' if s < self.threshold_negative 
                            else '#FFD93D' for s in scores
                        ]
                    )
                ])
            elif chart_type == 'scatter':
                fig = go.Figure(data=[
                    go.Scatter(
                        x=timestamps,
                        y=scores,
                        mode='markers',
                        name='Sentiment Score',
                        marker=dict(
                            color=[
                                '#4CAF50' if s > self.threshold_positive 
                                else '#F44336' if s < self.threshold_negative 
                                else '#FFD93D' for s in scores
                            ],
                            size=8
                        )
                    )
                ])
            else:  # Default to line chart
                fig = go.Figure()
                
                # Add main sentiment line
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=scores,
                    mode='lines+markers',
                    name='Sentiment Score',
                    line=dict(color='#4CAF50', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>Time:</b> %{x}<br>' +
                                 '<b>Sentiment:</b> %{y:.3f}<br>' +
                                 '<extra></extra>'
                ))
                
                # Add threshold lines
                if timestamps:
                    fig.add_hline(
                        y=self.threshold_positive,
                        line_dash="dash",
                        line_color="#4CAF50",
                        annotation_text="Positive Threshold",
                        annotation_position="top left"
                    )
                    fig.add_hline(
                        y=self.threshold_negative,
                        line_dash="dash",
                        line_color="#F44336",
                        annotation_text="Negative Threshold",
                        annotation_position="bottom left"
                    )
                    fig.add_hline(
                        y=0,
                        line_dash="solid",
                        line_color="#888888",
                        annotation_text="Neutral Line",
                        annotation_position="bottom right"
                    )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Real-Time Sentiment Monitoring Dashboard',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Time',
            yaxis_title='Sentiment Score',
            template='plotly_dark',
            yaxis=dict(range=[-1.1, 1.1]),
            hovermode='x unified',
            showlegend=False,
            font=dict(size=12),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Add statistical annotations if requested
        if show_stats and scores:
            current_avg = sum(scores) / len(scores)
            fig.add_annotation(
                x=timestamps[-1] if timestamps else datetime.now(),
                y=max(scores) + 0.1 if scores else 0,
                text=f'Current Avg: {current_avg:.3f}',
                showarrow=False,
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(color='white')
            )
        
        return fig
    
    def create_summary_chart(self) -> go.Figure:
        """
        Create a summary chart showing sentiment distribution
        
        Returns:
            Plotly figure object showing sentiment distribution
        """
        with self._lock:
            if not self.sentiment_history:
                # Return empty chart if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=20)
                )
                return fig
            
            # Calculate sentiment distribution
            positive_count = sum(1 for s in self.sentiment_history if s > self.threshold_positive)
            negative_count = sum(1 for s in self.sentiment_history if s < self.threshold_negative)
            neutral_count = len(self.sentiment_history) - positive_count - negative_count
            
            labels = ['Positive', 'Negative', 'Neutral']
            values = [positive_count, negative_count, neutral_count]
            colors = ['#4CAF50', '#F44336', '#FFD93D']
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    marker_colors=colors,
                    textinfo='label+percent',
                    textfont_size=12
                )
            ])
            
            fig.update_layout(
                title='Sentiment Distribution',
                template='plotly_dark',
                font=dict(size=12)
            )
            
            return fig
    
    def get_current_stats(self) -> Dict[str, Union[float, int]]:
        """
        Get current statistics
        
        Returns:
            Dictionary containing current statistics
        """
        with self._lock:
            if not self.sentiment_history:
                return {
                    'total_readings': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'positive_percentage': 0.0,
                    'negative_percentage': 0.0,
                    'neutral_percentage': 0.0,
                    'current_sentiment': 0.0,
                    'avg_sentiment': 0.0,
                    'min_sentiment': 0.0,
                    'max_sentiment': 0.0,
                    'std_deviation': 0.0
                }
            
            total = len(self.sentiment_history)
            positive_count = sum(1 for s in self.sentiment_history if s > self.threshold_positive)
            negative_count = sum(1 for s in self.sentiment_history if s < self.threshold_negative)
            neutral_count = total - positive_count - negative_count
            
            current_sentiment = self.sentiment_history[-1] if self.sentiment_history else 0.0
            avg_sentiment = sum(self.sentiment_history) / total if total > 0 else 0.0
            min_sentiment = min(self.sentiment_history) if self.sentiment_history else 0.0
            max_sentiment = max(self.sentiment_history) if self.sentiment_history else 0.0
            std_deviation = np.std(list(self.sentiment_history)) if self.sentiment_history else 0.0
            
            return {
                'total_readings': total,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_percentage': (positive_count / total) * 100 if total > 0 else 0.0,
                'negative_percentage': (negative_count / total) * 100 if total > 0 else 0.0,
                'neutral_percentage': (neutral_count / total) * 100 if total > 0 else 0.0,
                'current_sentiment': current_sentiment,
                'avg_sentiment': avg_sentiment,
                'min_sentiment': min_sentiment,
                'max_sentiment': max_sentiment,
                'std_deviation': std_deviation
            }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """
        Get recent alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        with self._lock:
            return list(self.alerts)[-limit:]
    
    def clear_history(self) -> None:
        """
        Clear all history and reset the monitor
        """
        with self._lock:
            self.sentiment_history.clear()
            self.timestamp_history.clear()
            self.alerts.clear()
            self._stats = {
                'total_readings': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'avg_sentiment': 0.0,
                'min_sentiment': 0.0,
                'max_sentiment': 0.0,
                'std_deviation': 0.0
            }
            self.logger.info("Monitor history cleared")
    
    def get_data_for_export(self) -> pd.DataFrame:
        """
        Get all monitoring data as a pandas DataFrame for export
        
        Returns:
            DataFrame containing all monitoring data
        """
        with self._lock:
            if not self.sentiment_history or not self.timestamp_history:
                return pd.DataFrame(columns=['timestamp', 'sentiment_score'])
            
            df = pd.DataFrame({
                'timestamp': list(self.timestamp_history),
                'sentiment_score': list(self.sentiment_history)
            })
            return df
    
    def set_alert_thresholds(self, 
                           positive_spike: float = None,
                           negative_spike: float = None,
                           volatility: float = None) -> None:
        """
        Update alert thresholds
        
        Args:
            positive_spike: New threshold for positive spikes
            negative_spike: New threshold for negative spikes
            volatility: New threshold for volatility alerts
        """
        with self._lock:
            if positive_spike is not None:
                self.alert_thresholds['positive_spikes'] = positive_spike
            if negative_spike is not None:
                self.alert_thresholds['negative_spikes'] = negative_spike
            if volatility is not None:
                self.alert_thresholds['volatility_threshold'] = volatility
            self.logger.info(f"Alert thresholds updated: {self.alert_thresholds}")

# Global monitor instance for convenience
default_monitor = RealTimeMonitor()

def create_live_chart() -> go.Figure:
    """
    Convenience function to create a live chart using the default monitor
    
    Returns:
        Plotly figure object
    """
    return default_monitor.create_live_chart()

def update_monitor(sentiment_score: float) -> None:
    """
    Convenience function to update the default monitor
    
    Args:
        sentiment_score: The sentiment score to add
    """
    default_monitor.update(sentiment_score)

def get_current_stats() -> Dict[str, Union[float, int]]:
    """
    Convenience function to get current stats from the default monitor
    
    Returns:
        Dictionary containing current statistics
    """
    return default_monitor.get_current_stats()