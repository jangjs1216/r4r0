import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge'; // Fixed path
import { ArrowLeft, TrendingUp, Activity, DollarSign } from 'lucide-react';

// --- Types ---
interface Bot {
    id: string;
    name: string;
    status: string;
}

interface BotStats {
    total_pnl: number;
    win_rate: number;
    total_trades: number;
    profit_factor: number;
    average_pnl: number;
}

// --- API ---
const fetchBots = async () => {
    const res = await axios.get<Bot[]>('http://localhost:8001/bots');
    return res.data;
};

const fetchBotStats = async (botId: string) => {
    const res = await axios.get<BotStats>(`http://localhost:8001/bots/${botId}/stats`);
    return res.data;
};

// --- Components ---

function BotSummaryCard({ bot, onClick }: { bot: Bot; onClick: () => void }) {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['bot-stats', bot.id],
        queryFn: () => fetchBotStats(bot.id)
    });

    if (isLoading) return (
        <Card className="animate-pulse h-40">
            <CardContent className="h-full flex items-center justify-center text-muted-foreground/20">
                Loading...
            </CardContent>
        </Card>
    );

    return (
        <Card className="hover:border-primary/50 cursor-pointer transition-all" onClick={onClick}>
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{bot.name}</CardTitle>
                    <Badge variant={bot.status === 'RUNNING' ? 'success' : 'secondary'}>{bot.status}</Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 gap-4 mt-2">
                    <div>
                        <p className="text-xs text-muted-foreground">Total PnL</p>
                        <p className={`text-xl font-bold ${stats?.total_pnl && stats.total_pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                            {stats?.total_pnl?.toFixed(2) ?? '0.00'} USDT
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground">Win Rate</p>
                        <div className="flex items-center gap-1">
                            <TrendingUp className="w-4 h-4 text-primary" />
                            <span className="text-lg font-bold">{((stats?.win_rate ?? 0) * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground">Trades</p>
                        <p className="font-mono">{stats?.total_trades ?? 0}</p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground">PF</p>
                        <p className="font-mono">{stats?.profit_factor === Infinity ? 'Inf' : stats?.profit_factor?.toFixed(2) ?? '0.00'}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function BotDetailView({ botId, onBack }: { botId: string; onBack: () => void }) {
    // Placeholder for Drill-Down Level 2 & 3
    return (
        <div className="space-y-6">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="w-4 h-4" /> Back to Dashboard
            </button>
            <h2 className="text-2xl font-bold">Bot Session History: {botId}</h2>

            <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                    <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Detailed Session & Trade History will appear here.</p>
                    <p className="text-xs">(To be implemented in Level 2 & 3)</p>
                </CardContent>
            </Card>
        </div>
    );
}

// --- Main View (Drill-Down Orchestrator) ---
export default function BotTradesView() {
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const { data: bots, isLoading } = useQuery({
        queryKey: ['bots'],
        queryFn: fetchBots
    });

    if (selectedBotId) {
        return <BotDetailView botId={selectedBotId} onBack={() => setSelectedBotId(null)} />;
    }

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold flex items-center gap-2">
                <DollarSign className="w-6 h-6 text-primary" />
                Performance Dashboard
            </h2>

            {isLoading ? (
                <div className="text-center py-20">Loading Bots...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {bots?.map(bot => (
                        <BotSummaryCard key={bot.id} bot={bot} onClick={() => setSelectedBotId(bot.id)} />
                    ))}
                </div>
            )}
        </div>
    );
}

