import React, { useState, useEffect } from 'react';
import { Navbar, NavTab } from './components/Navbar';
import { SearchBarModal } from './components/SearchBarModal';
import { AllStocksTable } from './components/AllStocksTable';
import { OptionChainView } from './components/OptionChainView';
import { FuturesDashboard } from './components/FuturesDashboard';
import { PredictionView } from './components/PredictionView';
import { SyncManagerView } from './components/SyncManagerView';
import { UniverseManagerView } from './components/UniverseManagerView';
import { ModelLabView } from './components/ModelLabView';
import { InstrumentDetailModal } from './components/InstrumentDetailModal';
import { BrokerSettingsModal } from './components/BrokerSettingsModal';
import { StockAiModal } from './components/StockAiModal';
import { FloatingAiButton } from './components/FloatingAiButton';
import { api } from './api/client';
import { Instrument, SyncStatus } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('ALL_STOCKS');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isBrokerSettingsOpen, setIsBrokerSettingsOpen] = useState(false);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [aiSelectedSymbol, setAiSelectedSymbol] = useState<string>('TCS');
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(null);
  const [selectedSymbolForOptions, setSelectedSymbolForOptions] = useState<string>('NIFTY');
  const [selectedSymbolForFutures, setSelectedSymbolForFutures] = useState<string>('NIFTY');
  const [selectedSymbolForPrediction, setSelectedSymbolForPrediction] = useState<string>('NIFTY');
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const s = await api.getSyncStatus();
        setSyncStatus(s);
      } catch (err) {
        console.error('Failed to fetch sync status in App:', err);
      }
    };
    fetchStatus();
    const timer = setInterval(fetchStatus, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleOpenOptionChain = (symbol: string) => {
    setSelectedSymbolForOptions(symbol);
    setActiveTab('OPTIONS');
  };

  const handleOpenFutures = (symbol: string) => {
    setSelectedSymbolForFutures(symbol);
    setActiveTab('FUTURES');
  };

  const handleOpenPrediction = (symbol: string) => {
    setSelectedSymbolForPrediction(symbol);
    setActiveTab('PREDICTION');
  };

  const handleOpenAiCopilot = (symbol: string) => {
    setAiSelectedSymbol(symbol);
    setIsAiModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* Global Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenBrokerSettings={() => setIsBrokerSettingsOpen(true)}
        syncStatus={syncStatus}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'ALL_STOCKS' && (
          <AllStocksTable
            onSelectInstrument={setSelectedInstrument}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenPrediction={handleOpenPrediction}
          />
        )}

        {activeTab === 'PREDICTION' && (
          <PredictionView
            initialSymbol={selectedSymbolForPrediction}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenAiCopilot={handleOpenAiCopilot}
          />
        )}

        {activeTab === 'NSE' && (
          <AllStocksTable
            initialExchange="NSE"
            onSelectInstrument={setSelectedInstrument}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenPrediction={handleOpenPrediction}
          />
        )}

        {activeTab === 'BSE' && (
          <AllStocksTable
            initialExchange="BSE"
            onSelectInstrument={setSelectedInstrument}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenPrediction={handleOpenPrediction}
          />
        )}

        {activeTab === 'FNO' && (
          <AllStocksTable
            initialHasFno={true}
            onSelectInstrument={setSelectedInstrument}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenPrediction={handleOpenPrediction}
          />
        )}

        {activeTab === 'INDICES' && (
          <AllStocksTable
            initialSegment="INDEX"
            onSelectInstrument={setSelectedInstrument}
            onOpenOptionChain={handleOpenOptionChain}
            onOpenFutures={handleOpenFutures}
            onOpenPrediction={handleOpenPrediction}
          />
        )}

        {activeTab === 'OPTIONS' && (
          <OptionChainView
            initialSymbol={selectedSymbolForOptions}
            onOpenFutures={handleOpenFutures}
          />
        )}

        {activeTab === 'FUTURES' && (
          <FuturesDashboard
            initialSymbol={selectedSymbolForFutures}
            onOpenOptionChain={handleOpenOptionChain}
          />
        )}

        {activeTab === 'WATCHLIST' && (
          <div className="space-y-6">
            <AllStocksTable
              initialUniverseId="CUSTOM_WATCHLIST"
              onSelectInstrument={setSelectedInstrument}
              onOpenOptionChain={handleOpenOptionChain}
              onOpenFutures={handleOpenFutures}
              onOpenPrediction={handleOpenPrediction}
            />
            <UniverseManagerView
              onSelectInstrument={setSelectedInstrument}
              onOpenOptionChain={handleOpenOptionChain}
              onOpenFutures={handleOpenFutures}
            />
          </div>
        )}

        {activeTab === 'SYNC' && <SyncManagerView />}

        {activeTab === 'MODEL_LAB' && <ModelLabView />}
      </main>

      {/* Global Search Modal */}
      <SearchBarModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectInstrument={setSelectedInstrument}
        onOpenOptionChain={handleOpenOptionChain}
        onOpenFutures={handleOpenFutures}
      />

      {/* Instrument Detail Modal */}
      <InstrumentDetailModal
        instrument={selectedInstrument}
        onClose={() => setSelectedInstrument(null)}
        onOpenOptionChain={handleOpenOptionChain}
        onOpenFutures={handleOpenFutures}
        onOpenPrediction={handleOpenPrediction}
        onOpenAiCopilot={handleOpenAiCopilot}
      />

      {/* Broker Credentials & Live Feed Modal */}
      <BrokerSettingsModal
        isOpen={isBrokerSettingsOpen}
        onClose={() => setIsBrokerSettingsOpen(false)}
      />

      {/* Stock AI Copilot Pop-up Modal */}
      <StockAiModal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        defaultSymbol={aiSelectedSymbol}
        onOpenOptionChain={handleOpenOptionChain}
        onOpenFutures={handleOpenFutures}
      />

      {/* Floating AI Copilot Trigger */}
      <FloatingAiButton
        onClick={() => handleOpenAiCopilot(selectedInstrument?.trading_symbol || selectedSymbolForPrediction || 'TCS')}
        currentSymbol={selectedInstrument?.trading_symbol || selectedSymbolForPrediction || 'TCS'}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 bg-[#0d1322] text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-400">NSE & BSE Full Market Coverage Platform</span>
            <span>•</span>
            <span>Active Universe: {syncStatus?.total_active_instruments.toLocaleString() || '62,798'} instruments</span>
          </div>
          <div>
            Built with FastAPI, SQLite FTS5, React & Tailwind CSS. Powered by Kotak Neo live feed & genuine exchange masters.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
