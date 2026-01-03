import { useOrchestratorStore } from './orchestrator/store';
import { Sidebar } from './orchestrator/Sidebar';
import DashboardView from './views/dashboard/DashboardView';
import MarketView from './views/market/MarketView';
import PortfolioView from './views/portfolio/PortfolioView';
import BotConfigView from './views/bot-config/BotConfigView';
import BotEditorView from './views/bot-editor/BotEditorView';
import BotTradesView from './views/bot-trades/BotTradesView';
import { BacktestView } from './views/backtest/BacktestView';
import AuthView from './views/auth/AuthView';

export default function App() {
  const { currentView } = useOrchestratorStore();

  const renderView = () => {
    switch (currentView) {
      case 'dashboard': return <DashboardView />;
      case 'market': return <MarketView />;
      case 'portfolio': return <PortfolioView />;
      case 'bot-config': return <BotConfigView />;
      case 'bot-editor': return <BotEditorView />;
      case 'bot-trades': return <BotTradesView />;
      case 'backtest': return <BacktestView />;
      case 'auth': return <AuthView />;
      default: return <DashboardView />;
    }
  };



  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/20">
      <Sidebar />
      <main className="flex-1 overflow-auto relative">
        <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-card/30 backdrop-blur sticky top-0 z-10 text-sm">
          <div className="font-medium text-muted-foreground">
            r4r0 / <span className="text-foreground">{currentView}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-bold ring-2 ring-border">OA</div>
          </div>
        </header>
        <div className="min-h-[calc(100vh-4rem)]">
          {renderView()}
        </div>
      </main>
    </div>
  );
}
