import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Play, Settings, Plus, Square, Trash2 } from 'lucide-react';
import { useOrchestratorStore } from '../../orchestrator/store';
import { BotService, type BotConfig } from '../bot-editor/api'; // Ensure api.ts exports BotConfig and BotService

export default function BotConfigView() {
    const { setView, setEditingBotId } = useOrchestratorStore();

    const handleCreate = () => {
        setEditingBotId(null);
        setView('bot-editor');
    };

    const handleEdit = (botId: string) => {
        setEditingBotId(botId);
        setView('bot-editor');
    };

    const [bots, setBots] = useState<BotConfig[]>([]);

    const [processingBots, setProcessingBots] = useState<Set<string>>(new Set());
    const [elapsedTimes, setElapsedTimes] = useState<Record<string, number>>({});

    useEffect(() => {
        const fetchBots = async () => {
            try {
                const latestBots = await BotService.getAllBots();
                setBots(prev => {
                    // Only update bots that are NOT currently being processed locally
                    // This prevents the global poll from overwriting "BOOTING/STOPPING" optimistic states
                    // with stale "STOPPED/RUNNING" states from the server.

                    // Create a map of latest data
                    const latestMap = new Map(latestBots.map(b => [b.id, b]));

                    // Filter out bots that are no longer present in latestBots
                    const filteredPrev = prev.filter(prevBot => prevBot.id && latestMap.has(prevBot.id));

                    const updatedBots = filteredPrev.map(prevBot => {
                        // If this bot is being processed (button clicked), keep local state
                        if (prevBot.id && processingBots.has(prevBot.id)) {
                            return prevBot;
                        }
                        // Otherwise, accept server state
                        return latestMap.get(prevBot.id!) || prevBot; // Should always find if filteredPrev
                    });

                    // Add new bots that weren't in prev
                    const newBots = latestBots.filter(lb => !prev.some(pb => pb.id === lb.id));

                    return [...updatedBots, ...newBots];
                });
            } catch (err) {
                console.error(err);
            }
        };

        fetchBots();
        const interval = setInterval(fetchBots, 5000);
        return () => clearInterval(interval);
    }, [processingBots]); // Re-create poll function if processing set changes (or use ref)

    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    const showToast = (message: string, type: 'success' | 'error' = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const toggleBotStatus = async (bot: BotConfig) => {
        if (!bot.id) return;

        if (bot.status === 'BOOTING' || bot.status === 'STOPPING') return;

        // Mark as processing to block global poller
        setProcessingBots(prev => {
            const next = new Set(prev);
            next.add(bot.id!);
            return next;
        });

        // Init elapsed time
        setElapsedTimes(prev => ({ ...prev, [bot.id!]: 0 }));

        const isStarting = bot.status === 'STOPPED';
        const intermediateState = isStarting ? 'BOOTING' : 'STOPPING';
        const targetState = isStarting ? 'RUNNING' : 'STOPPED';

        // 1. Optimistic UI update
        setBots(prev => prev.map(b => b.id === bot.id ? { ...b, status: intermediateState } : b));

        try {
            // 2. Call API
            await BotService.updateBot(bot.id, { ...bot, status: intermediateState });

            // 3. Verification Loop
            let success = false;
            const TIMEOUT_SEC = 30;
            const POLL_INTERVAL_MS = 1000;
            let seconds = 0;

            // Loop until success or timeout
            while (seconds < TIMEOUT_SEC) {
                await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
                seconds++;
                setElapsedTimes(prev => ({ ...prev, [bot.id!]: seconds }));

                // Poll backend every 2 seconds (roughly 0, 2, 4...)
                if (seconds % 2 === 0) {
                    try {
                        const latest = await BotService.getBot(bot.id);

                        // Update our view of this specific bot
                        if (latest.status === targetState) {
                            setBots(prev => prev.map(b => b.id === bot.id ? latest : b));
                            showToast(`Bot "${bot.name}" is now ${targetState}!`, 'success');
                            success = true;
                            break;
                        }

                        // If error or unexpected state
                        if (latest.status !== intermediateState) {
                            setBots(prev => prev.map(b => b.id === bot.id ? latest : b));
                            const errorMsg = latest.status_message ? `Error: ${latest.status_message}` : `Unexpected status change: ${latest.status}`;
                            showToast(errorMsg, 'error');
                            success = true; // Exit loop (as failed)
                            break;
                        }
                    } catch (e) {
                        console.warn("Polling check failed", e);
                    }
                }
            }

            if (!success) {
                showToast(`Timed out waiting for ${intermediateState} -> ${targetState} (30s)`, 'error');
                // One last check
                try {
                    const finalBot = await BotService.getBot(bot.id);
                    setBots(prev => prev.map(b => b.id === bot.id ? finalBot : b));
                } catch { }
            }

        } catch (error) {
            console.error("Failed to toggle status:", error);
            setBots(prev => prev.map(b => b.id === bot.id ? bot : b)); // Revert
            showToast("Failed to initiate bot status update.", 'error');
        } finally {
            // Release lock
            setProcessingBots(prev => {
                const next = new Set(prev);
                next.delete(bot.id!);
                return next;
            });
            // Cleanup elapsed time
            setElapsedTimes(prev => {
                const next = { ...prev };
                delete next[bot.id!];
                return next;
            });
        }
    };

    const handleDelete = async (bot: BotConfig) => {
        if (!bot.id) return;
        if (bot.status === 'RUNNING') {
            showToast("Cannot delete a running bot. Stop it first.", 'error');
            return;
        }

        if (!window.confirm(`Are you sure you want to delete bot "${bot.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await BotService.deleteBot(bot.id);
            setBots(prev => prev.filter(b => b.id !== bot.id));
            showToast(`Bot "${bot.name}" deleted successfully.`, 'success');
        } catch (error) {
            console.error("Failed to delete bot:", error);
            showToast("Failed to delete bot.", 'error');
        }
    };

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6 relative">
            {/* Simple Toast Notification */}
            {toast && (
                <div className={`fixed top-6 right-6 px-6 py-4 rounded-lg shadow-xl border flex items-center gap-3 animate-in slide-in-from-right-10 fade-in duration-300 z-50 ${toast.type === 'success'
                    ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-100'
                    : 'bg-red-950/90 border-red-500/50 text-red-100'
                    }`}>
                    <div className={`w-2 h-2 rounded-full ${toast.type === 'success' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Bot Configuration</h2>
                    <p className="text-muted-foreground">Manage your automated trading instances</p>
                </div>
                <button
                    onClick={handleCreate}
                    className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md font-medium flex items-center gap-2 transition-colors"
                >
                    <Plus size={18} />
                    New Bot
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {bots.map(bot => (
                    <Card key={bot.id} className="group hover:border-primary/50 transition-all duration-300">
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-lg font-bold flex items-center gap-2">
                                {bot.name}
                            </CardTitle>
                            <div className="flex items-center gap-3">
                                <Badge variant={bot.status === 'RUNNING' ? 'default' : 'secondary'} className="capitalize">
                                    {bot.status}
                                </Badge>
                                <button
                                    onClick={() => handleDelete(bot)}
                                    className="text-muted-foreground hover:text-red-500 transition-colors p-1 rounded-md hover:bg-secondary"
                                    title="Delete Bot"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="text-muted-foreground">Mode</div>
                                    <div className="font-medium text-right">{bot.global_settings?.mode || 'N/A'}</div>

                                    <div className="text-muted-foreground">Allocation</div>
                                    <div className="font-medium text-right">{bot.global_settings?.account_allocation || 0} USDT</div>

                                    <div className="text-muted-foreground">Strategy</div>
                                    <div className="font-medium text-right truncate">
                                        {bot.pipeline?.strategy?.id || 'None'}
                                    </div>
                                </div>

                                {bot.status_message && (
                                    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded p-2 flex items-start gap-2 text-xs text-yellow-200">
                                        <div className="mt-0.5 min-w-fit">⚠️</div>
                                        <span>{bot.status_message}</span>
                                    </div>
                                )}

                                <div className="border-t border-border pt-4 flex items-center justify-between gap-3">
                                    <button
                                        onClick={() => toggleBotStatus(bot)}
                                        disabled={bot.status === 'BOOTING' || bot.status === 'STOPPING'}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all duration-200 ${bot.status === 'RUNNING' || bot.status === 'STOPPING'
                                            ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20'
                                            : bot.status === 'BOOTING'
                                                ? 'bg-yellow-500/10 text-yellow-500 cursor-wait'
                                                : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20'
                                            } ${bot.status === 'BOOTING' || bot.status === 'STOPPING' ? 'opacity-80' : ''}`}
                                    >
                                        {(bot.status === 'BOOTING' || bot.status === 'STOPPING') ? (
                                            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                        ) : (
                                            bot.status === 'RUNNING' ? <Square size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />
                                        )}
                                        {bot.status === 'RUNNING' ? 'Stop'
                                            : bot.status === 'BOOTING' ? `Booting... (${elapsedTimes[bot.id!] || 0}s)`
                                                : bot.status === 'STOPPING' ? `Stopping... (${elapsedTimes[bot.id!] || 0}s)`
                                                    : 'Start'}
                                    </button>
                                    <button
                                        onClick={() => bot.id && handleEdit(bot.id)}
                                        className="flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium bg-secondary hover:bg-secondary/80 transition-colors"
                                    >
                                        <Settings size={16} />
                                        Configure
                                    </button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {/* Empty State / Add Placeholder */}
                <button
                    onClick={handleCreate}
                    className="border-2 border-dashed border-border rounded-lg flex flex-col items-center justify-center gap-4 text-muted-foreground hover:text-primary hover:border-primary/50 hover:bg-primary/50 transition-all min-h-[250px]"
                >
                    <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                        <Plus size={24} />
                    </div>
                    <span className="font-medium">Create New Bot</span>
                </button>
            </div>
        </div>
    );
}
