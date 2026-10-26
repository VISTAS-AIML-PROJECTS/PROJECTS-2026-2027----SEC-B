import React from 'react';
import { Sparkles } from 'lucide-react';

interface FloatingAiButtonProps {
  onClick: () => void;
  currentSymbol?: string;
}

export const FloatingAiButton: React.FC<FloatingAiButtonProps> = ({
  onClick,
  currentSymbol
}) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 flex items-center space-x-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white font-bold text-xs sm:text-sm shadow-2xl shadow-blue-500/40 hover:shadow-blue-500/60 hover:scale-105 active:scale-95 transition-all duration-200 border border-blue-400/30 group"
      title="Open Stock AI Copilot & Price Prediction"
    >
      <div className="relative">
        <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-amber-300 animate-pulse group-hover:rotate-12 transition-transform" />
        <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-500"></span>
      </div>
      <div className="flex flex-col items-start leading-none">
        <span className="tracking-wide">AI Stock Analyst</span>
        {currentSymbol && (
          <span className="text-[10px] text-blue-200 font-mono mt-0.5 font-normal">
            Analyze {currentSymbol}
          </span>
        )}
      </div>
    </button>
  );
};
