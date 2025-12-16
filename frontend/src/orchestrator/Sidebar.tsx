import React from 'react';
import { LayoutDashboard, LineChart, Wallet, Settings, ShieldCheck, Activity } from 'lucide-react';
import type { ViewId } from './store';
import { useOrchestratorStore } from './store';
import { cn } from '../lib/utils';

// View Registry for Navigation
const NAV_ITEMS: { id: ViewId; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { id: 'market', label: 'Market', icon: <LineChart size={20} /> },
    { id: 'portfolio', label: 'Portfolio', icon: <Wallet size={20} /> },
    { id: 'bot-config', label: 'Bot Config', icon: <Settings size={20} /> },
    { id: 'bot-trades', label: 'Bot Trades', icon: <Activity size={20} /> },
    { id: 'auth', label: 'Auth', icon: <ShieldCheck size={20} /> },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const { currentView, setView } = useOrchestratorStore();

    return (
        <aside className={cn("w-64 border-r border-border bg-card/50 backdrop-blur flex flex-col", className)}>
            <div className="p-6 border-b border-border">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    r4r0 Console
                </h1>
                <p className="text-xs text-muted-foreground mt-1">Orchestrator Active</p>
            </div>

            <nav className="flex-1 p-4 space-y-1">
                <div className="text-xs font-semibold text-muted-foreground mb-4 px-2 uppercase tracking-wider">
                    Microservices
                </div>
                {NAV_ITEMS.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setView(item.id)}
                        className={cn(
                            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200",
                            currentView === item.id
                                ? "bg-primary/10 text-primary border-r-2 border-primary"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                        )}
                    >
                        {item.icon}
                        <span>{item.label}</span>
                        {currentView === item.id && (
                            <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_hsl(var(--primary))]" />
                        )}
                    </button>
                ))}
            </nav>

            <div className="p-4 border-t border-border">
                <div className="bg-secondary/30 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span className="text-xs font-medium">System Healthy</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground font-mono">
                        v2.1.0-alpha
                    </div>
                </div>
            </div>
        </aside>
    );
}
