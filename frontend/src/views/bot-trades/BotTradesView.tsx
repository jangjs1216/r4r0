import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Layout, Sidebar, Search, Activity, TrendingUp, DollarSign } from 'lucide-react';

// --- Types & API (Same as Option A) ---
interface Bot { id: string; name: string; status: string; }
interface BotStats {
    total_pnl: number; win_rate: number; total_trades: number; profit_factor: number; average_pnl: number;
}
const fetchBots = async () => (await axios.get<Bot[]>('http://localhost:8001/bots')).data;
const fetchBotStats = async (botId: string) => (await axios.get<BotStats>(`http://localhost:8001/bots/${botId}/stats`)).data;

// --- Components ---

function BotListItem({ bot, isSelected, onClick }: { bot: Bot, isSelected: boolean, onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer transition-colors flex justify-between items-center ${isSelected ? 'bg-primary/10 border border-primary/20' : 'hover:bg-secondary/50'}`}
        >
            <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${bot.status === 'RUNNING' ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                <span className={`font-medium ${isSelected ? 'text-primary' : ''}`}>{bot.name}</span>
            </div>
            {isSelected && <Activity className="w-4 h-4 text-primary opacity-50" />}
        </div>
    );
}

function StatsPanel({ botId }: { botId: string }) {
    const { data: stats, isLoading } = useQuery({ queryKey: ['bot-stats', botId], queryFn: () => fetchBotStats(botId) });

    if (isLoading) return <div className="animate-pulse h-32 bg-secondary/20 rounded-xl" />;

    return (
        <div className="grid grid-cols-4 gap-4 mb-6">
            <Card>
                <CardContent className="pt-6">
                    <p className="text-xs text-muted-foreground uppercase">Net PnL</p>
                    <p className={`text-2xl font-bold ${stats?.total_pnl && stats.total_pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                        ${stats?.total_pnl?.toFixed(2)}
                    </p>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="pt-6">
                    <p className="text-xs text-muted-foreground uppercase">Win Rate</p>
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary" />
                        <span className="text-2xl font-bold">{((stats?.win_rate ?? 0) * 100).toFixed(1)}%</span>
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="pt-6">
                    <p className="text-xs text-muted-foreground uppercase">Trades</p>
                    <p className="text-2xl font-bold font-mono">{stats?.total_trades}</p>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="pt-6">
                    <p className="text-xs text-muted-foreground uppercase">Profit Factor</p>
                    <p className="text-2xl font-bold font-mono">{stats?.profit_factor === Infinity ? 'Inf' : stats?.profit_factor?.toFixed(2)}</p>
                </CardContent>
            </Card>
        </div>
    );
}

// --- Main Split-View ---
export default function BotTradesView() {
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const { data: bots, isLoading } = useQuery({ queryKey: ['bots'], queryFn: fetchBots });

    // Auto-select first bot
    if (!selectedBotId && bots && bots.length > 0) {
        setSelectedBotId(bots[0].id);
    }

    const selectedBot = bots?.find(b => b.id === selectedBotId);

    return (
        <div className="flex h-[calc(100vh-100px)] gap-6 p-6">
            {/* Left Sidebar */}
            <Card className="w-1/4 min-w-[250px] flex flex-col">
                <CardHeader className="border-b pb-4">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Layout className="w-5 h-5" /> Bot Browser
                    </CardTitle>
                    <div className="relative mt-2">
                        <Search className="absolute left-2 top-2.5 w-4 h-4 text-muted-foreground" />
                        <input className="w-full bg-secondary/30 rounded px-8 py-2 text-sm" placeholder="Filter bots..." />
                    </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto pt-4 space-y-2">
                    {isLoading ? <div>Loading...</div> : bots?.map(bot => (
                        <BotListItem
                            key={bot.id}
                            bot={bot}
                            isSelected={selectedBotId === bot.id}
                            onClick={() => setSelectedBotId(bot.id)}
                        />
                    ))}
                </CardContent>
            </Card>

            {/* Right Main Panel */}
            <div className="flex-1 flex flex-col space-y-6 overflow-hidden">
                {selectedBot ? (
                    <>
                        <div className="flex justify-between items-center">
                            <h2 className="text-3xl font-bold flex items-center gap-3">
                                {selectedBot.name}
                                <Badge variant={selectedBot.status === 'RUNNING' ? 'success' : 'secondary'}>{selectedBot.status}</Badge>
                            </h2>
                            <button className="text-sm bg-primary/10 text-primary px-4 py-2 rounded hover:bg-primary/20">
                                View Full History
                            </button>
                        </div>

                        {/* Stats Strip */}
                        <StatsPanel botId={selectedBot.id} />

                        {/* Trade Table Container */}
                        <Card className="flex-1">
                            <CardHeader>
                                <CardTitle className="text-lg">Recent Sessions & Trades</CardTitle>
                            </CardHeader>
                            <CardContent className="flex flex-col items-center justify-center p-12 text-muted-foreground h-[400px]">
                                <Activity className="w-12 h-12 mb-4 opacity-30" />
                                <p>Select a Session to drill down (Not implemented yet)</p>
                            </CardContent>
                        </Card>
                    </>
                ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                        Select a bot to view details
                    </div>
                )}
            </div>
        </div>
    );
}
