import React, { useState } from 'react';
import { Search, AlertTriangle, CheckCircle, MessageSquare } from 'lucide-react';
import { analyzeReviews } from '../utils/api';

const ReviewAnalyzer = () => {
  const [inputText, setInputText]       = useState('');
  const [result, setResult]             = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await analyzeReviews(inputText);

      if (data.status === 'MODEL_UNAVAILABLE') {
        setError(`Sentiment model unavailable: ${data.error}`);
        return;
      }
      if (data.error) {
        setError(data.error);
        return;
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : err.message,
      );
    } finally {
      setLoading(false);
    }
  };

  const total = result
    ? result.sentiment.positive + result.sentiment.negative + result.sentiment.neutral
    : 0;

  const pct = (n) => (total > 0 ? Math.round((n / total) * 100) : 0);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">🔍 Seller Review Analyzer</h1>
        <p className="text-gray-600">
          Paste real customer reviews — sentiment is analyzed by a pretrained NLP model
          (DistilBERT SST-2).
        </p>
      </div>

      {/* Input */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">Paste Review Text</h2>
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Customer reviews (separate multiple reviews with a blank line)
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="input h-40 resize-none"
              placeholder={
                'The packaging was completely crushed when it arrived.\n\n' +
                'Great product, arrived in eco-friendly cardboard — very impressed!\n\n' +
                'Way too much plastic bubble wrap, very wasteful.'
              }
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary">
            <Search className="mr-2 w-4 h-4" />
            {loading ? 'Analyzing…' : 'Analyze Reviews'}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-8">
          {/* Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <MessageSquare className="h-10 w-10 text-blue-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-blue-600">{result.reviews_analyzed}</div>
              <div className="text-sm text-gray-600">Segments Analyzed</div>
            </div>
            <div className="card text-center">
              <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-green-600">{result.sentiment.positive}</div>
              <div className="text-sm text-gray-600">Positive</div>
            </div>
            <div className="card text-center">
              <AlertTriangle className="h-10 w-10 text-red-500 mx-auto mb-3" />
              <div className="text-3xl font-bold text-red-600">{result.sentiment.negative}</div>
              <div className="text-sm text-gray-600">Negative</div>
            </div>
          </div>

          {/* Sentiment bars */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Sentiment Breakdown</h2>
            {[
              { label: 'Positive', count: result.sentiment.positive, color: 'bg-green-500' },
              { label: 'Negative', count: result.sentiment.negative, color: 'bg-red-500' },
              { label: 'Neutral',  count: result.sentiment.neutral,  color: 'bg-gray-400' },
            ].map(({ label, count, color }) => (
              <div key={label} className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span>{label}</span>
                  <span>{count} ({pct(count)}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${color} h-2 rounded-full transition-all`}
                    style={{ width: `${pct(count)}%` }}
                  />
                </div>
              </div>
            ))}
            <p className="text-xs text-gray-500 mt-3">
              Model: {result.model} · Segments with confidence &lt; 65% are classified as neutral.
            </p>
          </div>

          {/* Packaging keyword findings */}
          {result.packaging_keywords && result.packaging_keywords.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Packaging Keyword Findings</h2>
              <p className="text-sm text-gray-500 mb-4">
                Extracted from your input text. Counts reflect actual occurrences.
              </p>
              <div className="space-y-2">
                {result.packaging_keywords.map(({ finding, mentions }) => (
                  <div
                    key={finding}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="text-gray-800 text-sm">{finding}</span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {mentions} mention{mentions !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Per-segment results */}
          {result.segment_results && result.segment_results.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Per-Segment Results</h2>
              <div className="space-y-3">
                {result.segment_results.map((seg, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded ${
                          seg.sentiment === 'positive'
                            ? 'bg-green-100 text-green-700'
                            : seg.sentiment === 'negative'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-gray-200 text-gray-600'
                        }`}
                      >
                        {seg.sentiment} ({(seg.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{seg.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400 text-center">{result.note}</p>
        </div>
      )}
    </div>
  );
};

export default ReviewAnalyzer;
