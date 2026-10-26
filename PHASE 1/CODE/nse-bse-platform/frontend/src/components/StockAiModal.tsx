import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  X,
  Send,
  Key,
  Bot,
  User,
  Zap,
  CheckCircle2,
  AlertCircle,
  Copy,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Sliders,
  Shield,
  Target,
  Layers,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { AiConfigResponse, AiChatMessage, PredictionResponse } from '../types';

interface StockAiModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSymbol?: string;
  onOpenOptionChain?: (symbol: string) => void;
  onOpenFutures?: (symbol: string) => void;
}

const QUICK_PROMPTS = [
  { label: '🎯 Full Trade Setup', prompt: 'Give me the complete actionable trade setup with exact Entry, Targets, Stop Loss, and Risk:Reward.' },
  { label: '📊 3-Month Forecast & History', prompt: 'Provide a comprehensive 3-month (90-day) future forecast and historical price trend analysis (1M, 3M, 6M, 1Y) with quarterly price targets and catalysts.' },
  { label: '📈 Best Options Strategy', prompt: 'What is the optimal options trading strategy (Calls, Puts, Spreads) based on current PCR and Open Interest?' },
  { label: '🛡️ Support & Resistance Pivots', prompt: 'Where are the critical Classical and Fibonacci pivot points (P, R1, R2, S1, S2)?' },
  { label: '⚠️ Risk & Max Drawdown', prompt: 'What is the risk assessment, volatility ATR, and Supertrend trailing stop loss for this stock?' },
  { label: '🔮 5-Day Swing Projection', prompt: 'Provide a 5-day swing trading forecast and institutional volume accumulation analysis.' }
];

export const StockAiModal: React.FC<StockAiModalProps> = ({
  isOpen,
  onClose,
  defaultSymbol = 'TCS',
  onOpenOptionChain,
  onOpenFutures
}) => {
  const [activeTab, setActiveTab] = useState<'analysis' | 'chat' | 'settings'>('analysis');
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [symbolInput, setSymbolInput] = useState(defaultSymbol);
  
  // Forecast & Analysis
  const [forecast, setForecast] = useState<PredictionResponse | null>(null);
  const [analysisText, setAnalysisText] = useState<string>('');
  const [analysisLoading, setAnalysisLoading] = useState(false);
  
  // Chat
  const [messages, setMessages] = useState<AiChatMessage[]>([
    {
      id: 'init',
      role: 'assistant',
      content: `Hello! I am your **AI Stock Analyst & Trading Copilot**. I have access to real-time NSE & BSE quotes, pivot points, technical indicators, and derivatives open interest. Ask me anything about **${defaultSymbol}** or select a quick trade prompt below!`,
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Settings & API Key
  const [config, setConfig] = useState<AiConfigResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('gemini');
  const [geminiKey, setGeminiKey] = useState<string>(() => localStorage.getItem('stock_ai_gemini_key') || '');
  const [openaiKey, setOpenaiKey] = useState<string>(() => localStorage.getItem('stock_ai_openai_key') || '');
  const [groqKey, setGroqKey] = useState<string>(() => localStorage.getItem('stock_ai_groq_key') || '');
  const [keySavedToast, setKeySavedToast] = useState(false);
  const [copiedToast, setCopiedToast] = useState(false);

  useEffect(() => {
    if (defaultSymbol) {
      setSymbol(defaultSymbol);
      setSymbolInput(defaultSymbol);
    }
  }, [defaultSymbol]);

  useEffect(() => {
    if (isOpen) {
      loadConfig();
      fetchStockAnalysis(symbol);
    }
  }, [isOpen, symbol]);

  useEffect(() => {
    if (activeTab === 'chat') {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, activeTab]);

  const loadConfig = async () => {
    try {
      const cfg = await api.getAiConfig();
      setConfig(cfg);
      if (cfg.active_provider) {
        setSelectedProvider(cfg.active_provider);
      }
    } catch (e) {
      console.warn('Could not load AI config:', e);
    }
  };

  const fetchStockAnalysis = async (sym: string) => {
    setAnalysisLoading(true);
    try {
      // First get fresh quote and quantitative forecast
      const fc = await api.getForecast(sym).catch(() => null);
      setForecast(fc);

      const activeKey = selectedProvider === 'gemini' ? geminiKey : (selectedProvider === 'openai' ? openaiKey : groqKey);
      const res = await api.analyzeStock(sym, undefined, selectedProvider, activeKey || undefined);
      setAnalysisText(res.content || 'Analysis generated successfully.');
    } catch (err: any) {
      setAnalysisText(`Failed to generate AI analysis: ${err.message || err}`);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || chatInput;
    if (!query.trim() || chatLoading) return;

    const userMsg: AiChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query.trim(),
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    try {
      const activeKey = selectedProvider === 'gemini' ? geminiKey : (selectedProvider === 'openai' ? openaiKey : groqKey);
      const history = [...messages, userMsg].map((m) => ({ role: m.role, content: m.content }));
      const res = await api.chatWithAi(history, symbol, selectedProvider, activeKey || undefined);
      
      const aiReply: AiChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.reply || 'Analysis complete.',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, aiReply]);
    } catch (err: any) {
      const errorReply: AiChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error contacting AI service: ${err.message || 'Please check your connection or API key.'}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, errorReply]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSaveApiKeys = async () => {
    try {
      if (geminiKey) localStorage.setItem('stock_ai_gemini_key', geminiKey);
      if (openaiKey) localStorage.setItem('stock_ai_openai_key', openaiKey);
      if (groqKey) localStorage.setItem('stock_ai_groq_key', groqKey);

      await api.updateAiConfig({
        provider: selectedProvider,
        gemini_key: geminiKey || undefined,
        openai_key: openaiKey || undefined,
        groq_key: groqKey || undefined
      });

      setKeySavedToast(true);
      setTimeout(() => setKeySavedToast(false), 3000);
      loadConfig();
    } catch (e) {
      console.error('Failed to save API keys:', e);
    }
  };

  const handleCopyAnalysis = () => {
    navigator.clipboard.writeText(analysisText);
    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 2000);
  };

  if (!isOpen) return null;

  const isBullish = forecast ? forecast.direction?.includes('BULLISH') : true;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-[#111827] border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 sm:px-6 bg-[#0d1322] border-b border-slate-800 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-1.5">
                  Stock AI Copilot
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    Live NSE & BSE
                  </span>
                </h2>
              </div>
              <p className="text-xs text-slate-400">Institutional quantitative price analysis, pivot grids & interactive AI trading</p>
            </div>
          </div>

          {/* Active Stock Search / Switcher */}
          <div className="flex items-center space-x-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (symbolInput.trim()) {
                  setSymbol(symbolInput.trim().toUpperCase());
                }
              }}
              className="flex items-center"
            >
              <input
                type="text"
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
                placeholder="Stock (e.g. TCS)"
                className="w-24 sm:w-32 bg-slate-900 border border-slate-700 rounded-l-lg px-2.5 py-1 text-xs text-white uppercase font-mono font-bold focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 text-xs font-semibold rounded-r-lg transition-colors"
              >
                Scan
              </button>
            </form>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Live Stock Header Pill & Navigation Tabs */}
        <div className="bg-[#0b101d] px-4 sm:px-6 py-2.5 border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
          {forecast && (
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="font-bold text-white text-sm">{forecast.symbol}</span>
              <span className="text-slate-100 font-bold">
                ₹{forecast.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                (forecast.change_percent || 0) >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
              }`}>
                {(forecast.change_percent || 0) >= 0 ? '+' : ''}{forecast.change_percent?.toFixed(2)}%
              </span>
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                isBullish ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}>
                {forecast.direction?.replace('_', ' ')}
              </span>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-1 bg-slate-900/80 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeTab === 'analysis' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Deep Analysis
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeTab === 'chat' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Interactive Chat
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center space-x-1 ${
                activeTab === 'settings' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Key className="w-3 h-3" />
              <span>AI API Key</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          
          {/* TAB 1: AI DEEP ANALYSIS */}
          {activeTab === 'analysis' && (
            <div className="space-y-4">
              {/* Quick Actions Row */}
              <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                <span className="text-slate-400 font-medium">Quick Prompts:</span>
                <div className="flex items-center space-x-2 flex-wrap gap-1">
                  {QUICK_PROMPTS.slice(0, 3).map((qp, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setActiveTab('chat');
                        handleSendMessage(qp.prompt);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-blue-600/30 text-slate-300 hover:text-blue-300 border border-slate-700 transition-all font-medium"
                    >
                      {qp.label}
                    </button>
                  ))}
                  <button
                    onClick={() => fetchStockAnalysis(symbol)}
                    disabled={analysisLoading}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center space-x-1"
                    title="Refresh AI Analysis"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${analysisLoading ? 'animate-spin text-blue-400' : ''}`} />
                    <span>Refresh</span>
                  </button>
                  <button
                    onClick={handleCopyAnalysis}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center space-x-1"
                    title="Copy Report"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>{copiedToast ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
              </div>

              {/* Analysis Content Box */}
              {analysisLoading ? (
                <div className="py-20 flex flex-col items-center justify-center space-y-3">
                  <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-xs text-slate-400 animate-pulse">
                    Synthesizing real-time order flow, Classical Pivots, ATR Volatility & Open Interest for {symbol}...
                  </p>
                </div>
              ) : (
                <div className="p-4 sm:p-6 rounded-xl bg-[#0d1322] border border-slate-800 text-slate-200 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans space-y-2">
                  {analysisText}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: INTERACTIVE CHAT */}
          {activeTab === 'chat' && (
            <div className="flex flex-col h-[52vh]">
              {/* Chat Thread */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {messages.map((m, idx) => (
                  <div
                    key={m.id || idx}
                    className={`flex items-start space-x-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {m.role === 'assistant' && (
                      <div className="w-7 h-7 rounded-lg bg-blue-600/30 text-blue-400 border border-blue-500/40 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed whitespace-pre-wrap ${
                        m.role === 'user'
                          ? 'bg-blue-600 text-white rounded-tr-none'
                          : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                      }`}
                    >
                      {m.content}
                      {m.timestamp && (
                        <div className={`text-[9px] mt-1 text-right ${m.role === 'user' ? 'text-blue-200' : 'text-slate-500'}`}>
                          {m.timestamp}
                        </div>
                      )}
                    </div>
                    {m.role === 'user' && (
                      <div className="w-7 h-7 rounded-lg bg-indigo-600/40 text-indigo-300 border border-indigo-500/40 flex items-center justify-center shrink-0 mt-0.5">
                        <User className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex items-center space-x-2 text-slate-400 text-xs pl-9">
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="italic">AI Copilot is analyzing {symbol}...</span>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Quick Prompts Carousel */}
              <div className="py-2 flex items-center space-x-2 overflow-x-auto no-scrollbar border-t border-slate-800/80 mt-2">
                {QUICK_PROMPTS.map((qp, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(qp.prompt)}
                    className="shrink-0 px-2.5 py-1 text-[11px] rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                  >
                    {qp.label}
                  </button>
                ))}
              </div>

              {/* Chat Input Bar */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center space-x-2 pt-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={`Ask anything about ${symbol} (e.g. Is it good to buy at current price? What are key pivots?)...`}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:border-blue-500 transition-all placeholder:text-slate-500"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim() || chatLoading}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold text-xs sm:text-sm flex items-center space-x-1.5 transition-all shadow-md shadow-blue-500/20"
                >
                  <span>Send</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          )}

          {/* TAB 3: AI API KEY & SETTINGS */}
          {activeTab === 'settings' && (
            <div className="space-y-6 max-w-2xl mx-auto py-2">
              <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/30 flex items-start space-x-3">
                <Sparkles className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                <div className="text-xs text-slate-300 space-y-1">
                  <p className="font-bold text-white text-sm">Bring Your Own AI API Key</p>
                  <p>
                    You can connect your own <strong>Google Gemini</strong>, <strong>OpenAI</strong>, or <strong>Groq</strong> API key.
                    If you don't provide a key, the system automatically uses the <strong>Built-in Quantitative AI Engine</strong> for all analysis!
                  </p>
                </div>
              </div>

              {/* Provider Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Select Active AI Provider:</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div
                    onClick={() => setSelectedProvider('gemini')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedProvider === 'gemini'
                        ? 'bg-blue-600/20 border-blue-500 text-white'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold">
                      <span>Google Gemini</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Recommended (Free)
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">Ultra-fast models (gemini-1.5-flash) with high Indian stock comprehension.</p>
                  </div>

                  <div
                    onClick={() => setSelectedProvider('openai')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedProvider === 'openai'
                        ? 'bg-blue-600/20 border-blue-500 text-white'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold">OpenAI ChatGPT</div>
                    <p className="text-[11px] text-slate-400 mt-1">GPT-4o / GPT-4o-mini models for reasoning.</p>
                  </div>

                  <div
                    onClick={() => setSelectedProvider('groq')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedProvider === 'groq'
                        ? 'bg-blue-600/20 border-blue-500 text-white'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold">Groq Cloud</div>
                    <p className="text-[11px] text-slate-400 mt-1">LLaMA 3.3 70B Versatile for millisecond inference.</p>
                  </div>

                  <div
                    onClick={() => setSelectedProvider('builtin')}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedProvider === 'builtin'
                        ? 'bg-blue-600/20 border-blue-500 text-white'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold">Built-In Quant Engine</div>
                    <p className="text-[11px] text-slate-400 mt-1">Zero external API keys required; 100% offline & instant.</p>
                  </div>
                </div>
              </div>

              {/* API Key Inputs */}
              {selectedProvider === 'gemini' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <label className="font-semibold text-slate-300">Google Gemini API Key:</label>
                    <a
                      href="https://aistudio.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline flex items-center space-x-1"
                    >
                      <span>Get Free Gemini Key</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    placeholder="AIzaSy..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {selectedProvider === 'openai' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <label className="font-semibold text-slate-300">OpenAI API Key:</label>
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline flex items-center space-x-1"
                    >
                      <span>Get OpenAI Key</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder="sk-proj-..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {selectedProvider === 'groq' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <label className="font-semibold text-slate-300">Groq API Key:</label>
                    <a
                      href="https://console.groq.com/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline flex items-center space-x-1"
                    >
                      <span>Get Groq Key</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <input
                    type="password"
                    value={groqKey}
                    onChange={(e) => setGroqKey(e.target.value)}
                    placeholder="gsk_..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {/* Save Button */}
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={handleSaveApiKeys}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center space-x-2 transition-all shadow-md shadow-blue-500/20"
                >
                  <Key className="w-4 h-4" />
                  <span>Save AI Configuration</span>
                </button>
                {keySavedToast && (
                  <span className="text-xs text-emerald-400 flex items-center space-x-1 font-semibold animate-fadeIn">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Configuration & API Key Saved Successfully!</span>
                  </span>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-3 sm:px-6 bg-[#0d1322] border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span>Active Provider: <strong className="text-slate-300 uppercase">{selectedProvider}</strong></span>
            <span>•</span>
            <span>Analyzed Stock: <strong className="text-blue-400 font-mono">{symbol}</strong></span>
          </div>
          {forecast?.has_derivatives && (
            <div className="flex items-center space-x-2">
              {onOpenOptionChain && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenOptionChain(symbol);
                  }}
                  className="text-blue-400 hover:underline"
                >
                  View Options Chain
                </button>
              )}
              {onOpenFutures && (
                <>
                  <span>•</span>
                  <button
                    onClick={() => {
                      onClose();
                      onOpenFutures(symbol);
                    }}
                    className="text-indigo-400 hover:underline"
                  >
                    View Futures
                  </button>
                </>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
