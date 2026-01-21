from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from datetime import datetime
import backend as bk  # Reuse your existing backend logic
import logging
from enum import Enum

# Initialize API
app = FastAPI(
    title="Product Sentiment API",
    description="API for the New Product Evaluation System Capstone",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ENUMS ---
class SentimentLabel(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"

# --- DATA MODELS ---
class ReviewRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="The review text to analyze")
    product_id: str = Field(..., min_length=1, description="Unique identifier for the product")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class BatchReviewRequest(BaseModel):
    # FIXED: Changed min_items to min_length to stop the Pydantic warnings
    reviews: List[ReviewRequest] = Field(..., min_length=1, max_length=1000, description="List of reviews to analyze")

class SentimentResponse(BaseModel):
    product_id: str
    text: str
    sentiment_score: float
    sentiment_label: SentimentLabel
    timestamp: str

class BatchResponse(BaseModel):
    status: str
    total_analyzed: int
    results: List[SentimentResponse]

# --- ENDPOINTS ---

@app.get("/")
def home():
    """Root endpoint to check API status"""
    return {
        "status": "online", 
        "message": "Welcome to the Sentiment Analysis API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze/single", response_model=SentimentResponse)
async def analyze_single(review: ReviewRequest):
    """Analyze a single review"""
    try:
        logger.info(f"Received single analysis request for product {review.product_id}")
        
        if not review.text.strip():
            raise HTTPException(status_code=400, detail="Review text cannot be empty")
        
        # Call Backend Logic
        scores, labels = bk.analyze_sentiment_batch([review.text])
        
        return SentimentResponse(
            product_id=review.product_id,
            text=review.text,
            sentiment_score=scores[0],
            sentiment_label=labels[0],
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in single analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/batch", response_model=BatchResponse)
async def analyze_batch(batch: BatchReviewRequest):
    """Analyze a batch of reviews"""
    try:
        logger.info(f"Received batch analysis request with {len(batch.reviews)} reviews")
        
        texts = [r.text for r in batch.reviews]
        for i, text in enumerate(texts):
            if not text.strip():
                raise HTTPException(status_code=400, detail=f"Review {i+1} text cannot be empty")
        
        scores, labels = bk.analyze_sentiment_batch(texts)
        
        results = []
        for i, review in enumerate(batch.reviews):
            results.append(SentimentResponse(
                product_id=review.product_id,
                text=review.text,
                sentiment_score=scores[i],
                sentiment_label=labels[i],
                timestamp=datetime.now().isoformat()
            ))
            
        return BatchResponse(
            status="success",
            total_analyzed=len(results),
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@app.post("/analyze/text")
async def analyze_text_only(text: str = Body(..., min_length=1, max_length=10000, embed=True)):
    """
    Simple endpoint to analyze text without product context.
    FIXED: Used Body() instead of Field() here to prevent the AssertionError
    """
    try:
        logger.info("Received simple text analysis request")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        scores, labels = bk.analyze_sentiment_batch([text])
        
        return {
            "text": text,
            "sentiment_score": scores[0],
            "sentiment_label": labels[0],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple text analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/info")
def get_api_info():
    """Get API information"""
    return {
        "title": "Product Sentiment API",
        "version": "1.0.0",
        "description": "API for the New Product Evaluation System Capstone",
        "endpoints": ["/", "/health", "/analyze/single", "/analyze/batch", "/analyze/text"],
        "timestamp": datetime.now().isoformat()
    }

# Allow running this file directly
if __name__ == "__main__":
    logger.info("Starting Product Sentiment API server...")
    uvicorn.run(
        "api:app", 
        host="127.0.0.1", 
        port=8000,
        log_level="info",
        reload=True
    )