import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2 } from 'lucide-react';
import { sendChat } from '../utils/api';

const STARTER = {
  id: 1,
  role: 'assistant',
  content:
    "Hi! I'm TrashGPT, a sustainability assistant for the Wrapture platform. " +
    'Ask me about packaging materials, recycling, eco-friendly alternatives, or ' +
    'how to interpret your packaging recommendations.',
  timestamp: new Date(),
};

const QUICK_PROMPTS = [
  { label: 'Paper bin question',  text: 'Can clean paper go in the paper recycling bin?' },
  { label: 'Eco shampoo packaging', text: "What's the most eco-friendly packaging for shampoo bottles?" },
  { label: 'Plastic recycling',   text: 'How do I recycle plastic packaging properly?' },
];

const TrashGPT = () => {
  const [messages, setMessages]     = useState([STARTER]);
  const [input, setInput]           = useState('');
  const [loading, setLoading]       = useState(false);
  const [serviceError, setServiceError] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const buildHistory = (msgs) =>
    msgs
      .filter((m) => m.id !== 1)
      .map((m) => ({ role: m.role, content: m.content }));

  const send = async (text) => {
    if (!text.trim() || loading) return;

    const userMsg = { id: Date.now(), role: 'user', content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setServiceError(null);

    try {
      const history = buildHistory([...messages, userMsg]);
      const result  = await sendChat(text, history);

      if (result.status === 'NOT_CONFIGURED') {
        setServiceError(
          "TrashGPT isn't configured yet. Add LLM_API_KEY to the backend .env file to enable AI chat."
        );
        return;
      }

      if (!result.response) {
        setServiceError(result.error || 'The AI provider returned an empty response.');
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: result.response,
          model: result.model,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setServiceError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : err.message,
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">💬 TrashGPT</h1>
        <p className="text-gray-600">
          AI sustainability assistant — powered by{' '}
          <span className="font-medium">Flask + LLM backend</span>
        </p>
      </div>

      {serviceError && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-300 rounded-lg text-yellow-800 text-sm">
          <strong>Service notice:</strong> {serviceError}
        </div>
      )}

      <div className="card h-96 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex items-start space-x-2 max-w-xs lg:max-w-md ${
                  msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === 'user' ? 'bg-green-500' : 'bg-gray-500'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>
                <div
                  className={`px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className="text-xs opacity-60 mt-1">
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {msg.model && (
                      <span className="ml-2 opacity-50">via {msg.model}</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-2 rounded-lg bg-gray-100">
                  <div className="flex space-x-1">
                    {[0, 0.1, 0.2].map((d) => (
                      <div
                        key={d}
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${d}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={handleSubmit} className="border-t p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about packaging, recycling, or sustainability…"
              className="flex-1 input"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn btn-primary"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {QUICK_PROMPTS.map(({ label, text }) => (
          <button
            key={label}
            onClick={() => send(text)}
            disabled={loading}
            className="p-3 text-left bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-5 h-5 text-blue-600 mb-2" />
            <p className="text-sm font-medium text-blue-800">{label}</p>
            <p className="text-xs text-blue-600 truncate">{text}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

export default TrashGPT;
