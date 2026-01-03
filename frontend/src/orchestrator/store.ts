import { create } from 'zustand';

export type ViewId = 'dashboard' | 'market' | 'portfolio' | 'bot-config' | 'bot-editor' | 'bot-trades' | 'backtest' | 'auth';

interface OrchestratorState {
    currentView: ViewId;
    setView: (view: ViewId) => void;
    // Global auth state can live here or in a separate store, 
    // keeping it here for simplicity as per "Orchestrator controls flow"
    isAuthenticated: boolean;
    setAuthenticated: (auth: boolean) => void;

    // Context for Drill-down navigation
    editingBotId: string | null;
    setEditingBotId: (id: string | null) => void;
}

export const useOrchestratorStore = create<OrchestratorState>((set) => ({
    currentView: 'dashboard', // Default to dashboard (No Login)
    setView: (view) => set({ currentView: view }),
    isAuthenticated: true, // Always authenticated
    setAuthenticated: (auth) => set({ isAuthenticated: auth }),
    editingBotId: null,
    setEditingBotId: (id) => set({ editingBotId: id }),
}));
