import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Layout, Sidebar, Search, Activity, TrendingUp, DollarSign, Clock, Calendar } from 'lucide-react';
import { format } from 'date-fns';

// --- Types & API ---
interface Bot { id: string; name: string; status: string; }
interface BotStats {
    total_pnl: number; win_rate: number; total_trades: number; profit_factor: number; average_pnl: number;
}
interface LocalOrderResponse {
    id: string; status: string; session_id?: string;
    symbol: string; side: string; quantity: number; reason?: string; timestamp: string;
}
interface BotSession {
    id: string; bot_id: string; start_time: string; end_time?: string; status: string;
    summary: { total_pnl?: number; win_rate?: number; trade_count?: number;[key: string]: any };
    // populated by detail API if needed, or we fetch orders separately
    orders?: LocalOrderResponse[];
}

const fetchBots = async () => (await axios.get<Bot[]>('http://localhost:8001/bots')).data;
// const fetchBotStats = async (botId: string) => (await axios.get<BotStats>(`http://localhost:8001/bots/${botId}/stats`)).data;
const fetchSessions = async (botId: string) => (await axios.get<BotSession[]>(`http://localhost:8001/bots/${botId}/sessions`)).data;
const fetchSessionDetail = async (sessionId: string) => (await axios.get<BotSession & { orders: LocalOrderResponse[] }>(`http://localhost:8001/sessions/${sessionId}`)).data;

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

function SessionCard({ session, isSelected, onClick }: { session: BotSession, isSelected: boolean, onClick: () => void }) {
    const pnl = session.summary.total_pnl || 0;
    const isPositive = pnl >= 0;
    const durationStr = session.end_time
        ? `${Math.round((new Date(session.end_time).getTime() - new Date(session.start_time).getTime()) / 60000)}m`
        : 'Running';

    return (
        <div
            onClick={onClick}
            className={`p-4 rounded-lg border cursor-pointer transition-all ${isSelected ? 'bg-primary/5 border-primary shadow-sm' : 'bg-background hover:bg-secondary/20 border-border'}`}
        >
            <div className="flex justify-between items-start mb-2">
                <div className="flex flex-col">
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(session.start_time), 'MM/dd HH:mm')}
                    </span>
                    <Badge variant={session.status === 'ACTIVE' ? 'success' : 'secondary'} className="mt-1 w-fit text-[10px]">
                        {session.status}
                    </Badge>
                </div>
                <div className="text-right">
                    <span className={`block font-bold ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                        ${pnl.toFixed(2)}
                    </span>
                    <span className="text-xs text-muted-foreground">{session.summary.trade_count || 0} Trades</span>
                </div>
            </div>
            <div className="text-xs text-muted-foreground flex justify-between border-t pt-2 mt-2">
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {durationStr}</span>
                <span>ID: {session.id.slice(0, 6)}</span>
            </div>
        </div>
    )
}

function TradeTable({ orders }: { orders: LocalOrderResponse[] }) {
    if (!orders || orders.length === 0) return <div className="p-8 text-center text-muted-foreground">No trades in this session.</div>;
    return (
        <div className="overflow-auto max-h-[500px]">
            <table className="w-full text-sm">
                <thead className="text-xs text-muted-foreground bg-secondary/20 sticky top-0">
                    <tr>
                        <th className="p-2 text-left">Time</th>
                        <th className="p-2 text-left">Symbol</th>
                        <th className="p-2 text-left">Side</th>
                        <th className="p-2 text-right">Qty</th>
                        <th className="p-2 text-left">Reason</th>
                        <th className="p-2 text-left">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {orders.map(order => (
                        <tr key={order.id} className="border-b border-border/50 hover:bg-secondary/10">
                            <td className="p-2 font-mono text-muted-foreground">{format(new Date(order.timestamp), 'HH:mm:ss')}</td>
                            <td className="p-2 font-medium">{order.symbol}</td>
                            <td className={`p-2 font-bold ${order.side === 'BUY' ? 'text-emerald-500' : 'text-red-500'}`}>{order.side}</td>
                            <td className="p-2 text-right font-mono">{order.quantity}</td>
                            <td className="p-2 text-muted-foreground truncate max-w-[150px]">{order.reason}</td>
                            <td className="p-2"><Badge variant="outline">{order.status}</Badge></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default function BotTradesView() {
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

    const { data: bots, isLoading } = useQuery({ queryKey: ['bots'], queryFn: fetchBots });

    // Auto-select first bot
    useEffect(() => {
        if (!selectedBotId && bots && bots.length > 0) setSelectedBotId(bots[0].id);
    }, [bots, selectedBotId]);

    const { data: sessions } = useQuery({
        queryKey: ['sessions', selectedBotId],
        queryFn: () => selectedBotId ? fetchSessions(selectedBotId) : Promise.resolve([]),
        enabled: !!selectedBotId
    });

    // Auto-select first session
    useEffect(() => {
        if (!selectedSessionId && sessions && sessions.length > 0) setSelectedSessionId(sessions[0].id);
    }, [sessions, selectedSessionId]);

    const { data: sessionDetail } = useQuery({
        queryKey: ['session-detail', selectedSessionId],
        queryFn: () => selectedSessionId ? fetchSessionDetail(selectedSessionId) : Promise.resolve(null),
        enabled: !!selectedSessionId
    });

    const selectedBot = bots?.find(b => b.id === selectedBotId);

    return (
        <div className="flex h-[calc(100vh-100px)] gap-4 p-4">
            {/* Sidebar 1: Bot List */}
            <Card className="w-[240px] flex flex-col">
                <CardHeader className="py-4 border-b">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Layout className="w-4 h-4" /> Bots
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-2 space-y-1">
                    {isLoading ? <div>Loading...</div> : bots?.map(bot => (
                        <BotListItem key={bot.id} bot={bot} isSelected={selectedBotId === bot.id} onClick={() => { setSelectedBotId(bot.id); setSelectedSessionId(null); }} />
                    ))}
                </CardContent>
            </Card>

            {/* Middle: Session List */}
            {selectedBot && (
                <div className="w-[300px] flex flex-col gap-4">
                    <Card className="flex-1 flex flex-col">
                        <CardHeader className="py-4 border-b">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Activity className="w-4 h-4" /> Sessions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-y-auto p-3 space-y-3">
                            {sessions?.map(session => (
                                <SessionCard
                                    key={session.id}
                                    session={session}
                                    isSelected={selectedSessionId === session.id}
                                    onClick={() => setSelectedSessionId(session.id)}
                                />
                            ))}
                            {!sessions?.length && <div className="text-center text-muted-foreground p-4">No sessions found.</div>}
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Right: Detail */}
            {selectedBot && sessionDetail && (
                <div className="flex-1 flex flex-col gap-4 overflow-hidden">
                    {/* Summary Header */}
                    <Card>
                        <CardContent className="p-4 flex justify-between items-center">
                            <div>
                                <h3 className="font-bold text-lg flex items-center gap-2">Session Detail <Badge>{sessionDetail.status}</Badge></h3>
                                <div className="text-xs text-muted-foreground mt-1">
                                    Started: {format(new Date(sessionDetail.start_time), 'yyyy-MM-dd HH:mm:ss')}
                                </div>
                            </div>
                            <div className="flex gap-6 text-right">
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase">Total PnL</p>
                                    <p className={`text-xl font-bold ${sessionDetail.summary.total_pnl && sessionDetail.summary.total_pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                        ${sessionDetail.summary.total_pnl?.toFixed(2) || '0.00'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground uppercase">Win Rate</p>
                                    <p className="text-xl font-bold">
                                        {((sessionDetail.summary.win_rate || 0) * 100).toFixed(0)}%
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Trade Table */}
                    <Card className="flex-1 flex flex-col">
                        <CardHeader className="py-4 border-b">
                            <CardTitle className="text-base">Trade History</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 flex-1 overflow-auto">
                            <TradeTable orders={sessionDetail.orders?.filter(o => o.symbol) || []} />
                            {/* Filter orders to ensure they are valid orders if needed */}
                        </CardContent>
                    </Card>
                </div>
            )}

            {selectedBot && !sessionDetail && (
                <div className="flex-1 flex items-center justify-center text-muted-foreground">Select a session to view details</div>
            )}
        </div>
    );
}
