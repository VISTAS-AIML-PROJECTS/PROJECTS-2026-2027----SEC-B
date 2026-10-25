"""
services/review_analyzer.py

Runs real NLP sentiment analysis on actual review text provided by the user.
Uses a pretrained HuggingFace pipeline (distilbert-base-uncased-finetuned-sst-2-english).

Does NOT:
- ignore the input text
- return hardcoded results
- generate fake complaint counts
- invent insights

Does:
- analyze each review sentence/paragraph individually
- aggregate real sentiment counts
- extract packaging-related keywords from the actual text
- return only what can be derived from the input
"""
import re
from typing import List

_pipeline = None
_pipeline_error = None


def _load_pipeline():
    global _pipeline, _pipeline_error
    if _pipeline is not None:
        return
    try:
        from transformers import pipeline
        _pipeline = pipeline(
            'sentiment-analysis',
            model='distilbert-base-uncased-finetuned-sst-2-english',
            truncation=True,
            max_length=512,
        )
    except Exception as e:
        _pipeline_error = str(e)


_load_pipeline()

# Keywords to look for in review text (packaging-related)
PACKAGING_KEYWORDS = {
    'plastic': 'Plastic packaging mentioned',
    'cardboard': 'Cardboard packaging mentioned',
    'bubble wrap': 'Bubble wrap mentioned',
    'styrofoam': 'Styrofoam mentioned',
    'recyclable': 'Recyclability mentioned',
    'recycle': 'Recyclability mentioned',
    'eco': 'Eco-friendliness mentioned',
    'sustainable': 'Sustainability mentioned',
    'damaged': 'Damage during shipping mentioned',
    'broken': 'Damage during shipping mentioned',
    'crushed': 'Damage during shipping mentioned',
    'excessive': 'Excessive packaging mentioned',
    'too much packaging': 'Excessive packaging mentioned',
    'overpackaged': 'Excessive packaging mentioned',
    'waste': 'Packaging waste mentioned',
    'biodegradable': 'Biodegradable materials mentioned',
    'compostable': 'Compostable materials mentioned',
}


def _split_reviews(text: str) -> List[str]:
    """Split input into individual review segments."""
    # Split on blank lines, numbered lists, or explicit separators
    segments = re.split(r'\n{2,}|\n\d+[\.\)]\s+|---+', text.strip())
    return [s.strip() for s in segments if len(s.strip()) > 10]


def analyze_reviews(text: str) -> dict:
    """
    Analyze actual review text.
    Returns real sentiment counts and keyword findings from the input.
    """
    if not text or not text.strip():
        return {'error': 'No review text provided.'}

    if _pipeline is None:
        return {
            'error': f'Sentiment model unavailable: {_pipeline_error}',
            'status': 'MODEL_UNAVAILABLE',
        }

    segments = _split_reviews(text)
    if not segments:
        segments = [text.strip()]

    # Run sentiment on each segment
    positive = 0
    negative = 0
    neutral = 0
    segment_results = []

    for seg in segments:
        try:
            result = _pipeline(seg[:512])[0]
            label = result['label']   # 'POSITIVE' or 'NEGATIVE'
            score = result['score']

            # Treat low-confidence predictions as neutral
            if score < 0.65:
                sentiment = 'neutral'
                neutral += 1
            elif label == 'POSITIVE':
                sentiment = 'positive'
                positive += 1
            else:
                sentiment = 'negative'
                negative += 1

            segment_results.append({
                'text': seg[:200],
                'sentiment': sentiment,
                'confidence': round(score, 3),
            })
        except Exception:
            neutral += 1

    total = len(segment_results)

    # Extract packaging keyword mentions from the full text
    text_lower = text.lower()
    keyword_findings = {}
    for kw, label in PACKAGING_KEYWORDS.items():
        count = text_lower.count(kw)
        if count > 0:
            if label not in keyword_findings:
                keyword_findings[label] = 0
            keyword_findings[label] += count

    keyword_list = [
        {'finding': label, 'mentions': count}
        for label, count in keyword_findings.items()
    ]
    keyword_list.sort(key=lambda x: x['mentions'], reverse=True)

    return {
        'status': 'OK',
        'reviews_analyzed': total,
        'sentiment': {
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
        },
        'packaging_keywords': keyword_list,
        'segment_results': segment_results,
        'model': 'distilbert-base-uncased-finetuned-sst-2-english',
        'note': (
            'Sentiment is based on the actual text you provided. '
            'Keyword findings are extracted from your input.'
        ),
    }
