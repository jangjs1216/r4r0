import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Play, Settings, Plus, Square } from 'lucide-react';
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

    useEffect(() => {
        BotService.getAllBots().then(setBots).catch(console.error);

        // Optional: Poll every 5s
        const interval = setInterval(() => {
            BotService.getAllBots().then(setBots).catch(console.error);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6">
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
                            <Badge variant={bot.status === 'RUNNING' ? 'default' : 'secondary'} className="capitalize">
                                {bot.status}
                            </Badge>
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

                                <div className="border-t border-border pt-4 flex items-center justify-between gap-3">
                                    <button
                                        className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-colors ${bot.status === 'RUNNING'
                                            ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20'
                                            : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20'
                                            }`}
                                    >
                                        {bot.status === 'RUNNING' ? <Square size={16} /> : <Play size={16} />}
                                        {bot.status === 'RUNNING' ? 'Stop' : 'Start'}
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
                    className="border-2 border-dashed border-border rounded-lg flex flex-col items-center justify-center gap-4 text-muted-foreground hover:text-primary hover:border-primary/50 hover:bg-primary/5 transition-all min-h-[250px]"
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
