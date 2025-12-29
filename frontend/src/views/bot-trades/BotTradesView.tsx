import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';

// --- TypeScript Interfaces ---
interface ExecutionDetail {
    exchange_trade_id: string;
    side: string;
    price: number;
    quantity: number;
    fee: number;
    fee_currency: string | null;
    realized_pnl: number | null;
    timestamp: string;
}

interface Trade {
    local_order_id: string;
    bot_id: string;
    bot_name: string;
    symbol: string;
    side: string;
    intent_quantity: number;
    intent_time: string;
    status: string;
    reason: string | null;
    execution: ExecutionDetail | null;
}

interface BotPerformance {
    bot_id: string;
    bot_name: string;
    total_trades: number;
    filled_trades: number;
    total_pnl: number;
    total_fees: number;
    win_count: number;
    loss_count: number;
    win_rate: number;
}

interface TradesResponse {
    trades: Trade[];
    bot_performances: BotPerformance[];
    summary: {
        total_trades: number;
        total_pnl: number;
        total_fees: number;
        bot_count: number;
    };
}

interface Bot {
    id: string;
    name: string;
}

// --- Bot Performance Card ---
function BotCard({ perf, isSelected, onSelect }: {
    perf: BotPerformance;
    isSelected: boolean;
    onSelect: () => void;
}) {
    const pnlColor = perf.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400';
    const winRateColor = perf.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400';

    return (
        <div
            onClick={onSelect}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${isSelected
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-border/50 bg-secondary/20 hover:bg-secondary/40'
                }`}
        >
            <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-lg">🤖 {perf.bot_name}</span>
                <Badge variant={perf.total_pnl >= 0 ? 'success' : 'destructive'}>
                    {perf.total_pnl >= 0 ? '+' : ''}{perf.total_pnl.toFixed(2)}
                </Badge>
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                    <p className="text-muted-foreground text-xs">Trades</p>
                    <p className="font-bold">{perf.filled_trades}/{perf.total_trades}</p>
                </div>
                <div>
                    <p className="text-muted-foreground text-xs">Win Rate</p>
                    <p className={`font-bold ${winRateColor}`}>{perf.win_rate.toFixed(1)}%</p>
                </div>
                <div>
                    <p className="text-muted-foreground text-xs">Fees</p>
                    <p className="font-bold text-muted-foreground">-${perf.total_fees.toFixed(4)}</p>
                </div>
            </div>

            {/* Win/Loss Bar */}
            <div className="mt-3 flex h-2 rounded-full overflow-hidden bg-secondary">
                <div
                    className="bg-emerald-500 transition-all"
                    style={{ width: `${perf.win_rate}%` }}
                />
                <div
                    className="bg-red-500 transition-all"
                    style={{ width: `${100 - perf.win_rate}%` }}
                />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>{perf.win_count}W</span>
                <span>{perf.loss_count}L</span>
            </div>
        </div>
    );
}

// --- Main Component ---
export default function BotTradesView() {
    const [data, setData] = useState<TradesResponse | null>(null);
    const [bots, setBots] = useState<Bot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [selectedBotId, setSelectedBotId] = useState<string>('');
    const [dateRange, setDateRange] = useState<string>('7d');

    const BOT_SERVICE_URL = import.meta.env.VITE_BOT_SERVICE_URL || 'http://localhost:8001';

    // Fetch bots
    useEffect(() => {
        async function fetchBots() {
            try {
                const res = await fetch(`${BOT_SERVICE_URL}/bots`);
                if (res.ok) setBots(await res.json());
            } catch (err) {
                console.error('Failed to fetch bots:', err);
            }
        }
        fetchBots();
    }, [BOT_SERVICE_URL]);

    // Fetch trades
    useEffect(() => {
        async function fetchTrades() {
            setLoading(true);
            setError(null);
            try {
                const params = new URLSearchParams();
                if (selectedBotId) params.append('bot_id', selectedBotId);

                const now = new Date();
                let fromDate: Date | null = null;
                if (dateRange === '1d') fromDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                else if (dateRange === '7d') fromDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                else if (dateRange === '30d') fromDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

                if (fromDate) params.append('from', fromDate.toISOString());

                const res = await fetch(`${BOT_SERVICE_URL}/trades?${params.toString()}`);
                if (!res.ok) throw new Error('Failed to fetch trades');

                const result: TradesResponse = await res.json();
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        }
        fetchTrades();
    }, [selectedBotId, dateRange, BOT_SERVICE_URL]);

    const formatTime = (iso: string) => {
        return new Date(iso).toLocaleString('ko-KR', {
            month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
        });
    };

    const formatPnL = (val: number | null) => {
        if (val === null) return '-';
        const sign = val >= 0 ? '+' : '';
        return `${sign}$${val.toFixed(4)}`;
    };

    // Filter trades by selected bot
    const filteredTrades = selectedBotId
        ? data?.trades.filter(t => t.bot_id === selectedBotId)
        : data?.trades;

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <h2 className="text-2xl font-bold">Bot Performance</h2>
                <div className="flex gap-3">
                    <select
                        className="bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value)}
                    >
                        <option value="1d">Last 24h</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="all">All Time</option>
                    </select>
                </div>
            </div>

            {/* Global Summary */}
            {data?.summary && (
                <div className="grid grid-cols-4 gap-4">
                    <div className="bg-secondary/30 rounded-xl p-4 border border-border/50">
                        <p className="text-xs text-muted-foreground uppercase">Total Bots</p>
                        <p className="text-2xl font-bold">{data.summary.bot_count}</p>
                    </div>
                    <div className="bg-secondary/30 rounded-xl p-4 border border-border/50">
                        <p className="text-xs text-muted-foreground uppercase">Total Trades</p>
                        <p className="text-2xl font-bold">{data.summary.total_trades}</p>
                    </div>
                    <div className="bg-secondary/30 rounded-xl p-4 border border-border/50">
                        <p className="text-xs text-muted-foreground uppercase">Net PnL</p>
                        <p className={`text-2xl font-bold ${data.summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {formatPnL(data.summary.total_pnl)}
                        </p>
                    </div>
                    <div className="bg-secondary/30 rounded-xl p-4 border border-border/50">
                        <p className="text-xs text-muted-foreground uppercase">Total Fees</p>
                        <p className="text-2xl font-bold text-muted-foreground">
                            -${data.summary.total_fees.toFixed(4)}
                        </p>
                    </div>
                </div>
            )}

            {/* Bot Performance Cards */}
            <div>
                <h3 className="text-lg font-semibold mb-4">Bot Performance</h3>
                {loading ? (
                    <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : error ? (
                    <div className="text-center text-red-400 py-8">{error}</div>
                ) : data?.bot_performances.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">No bots with trades</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {data?.bot_performances.map((perf) => (
                            <BotCard
                                key={perf.bot_id}
                                perf={perf}
                                isSelected={selectedBotId === perf.bot_id}
                                onSelect={() => setSelectedBotId(
                                    selectedBotId === perf.bot_id ? '' : perf.bot_id
                                )}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Trade History Table */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>
                            Trade History
                            {selectedBotId && <span className="text-sm font-normal text-muted-foreground ml-2">(Filtered)</span>}
                        </CardTitle>
                        {selectedBotId && (
                            <button
                                onClick={() => setSelectedBotId('')}
                                className="text-xs bg-secondary px-2 py-1 rounded hover:bg-secondary/80"
                            >
                                Clear Filter
                            </button>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    {!filteredTrades || filteredTrades.length === 0 ? (
                        <div className="py-8 text-center text-muted-foreground">No trades</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-muted-foreground uppercase bg-secondary/30">
                                    <tr>
                                        <th className="px-4 py-3">Time</th>
                                        <th className="px-4 py-3">Bot</th>
                                        <th className="px-4 py-3">Symbol</th>
                                        <th className="px-4 py-3">Side</th>
                                        <th className="px-4 py-3">Price</th>
                                        <th className="px-4 py-3">Qty</th>
                                        <th className="px-4 py-3">Fee</th>
                                        <th className="px-4 py-3">PnL</th>
                                        <th className="px-4 py-3">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredTrades.map((trade) => (
                                        <tr
                                            key={trade.local_order_id}
                                            className="border-b border-border/50 hover:bg-secondary/10"
                                        >
                                            <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                                                {formatTime(trade.intent_time)}
                                            </td>
                                            <td className="px-4 py-3 font-medium">{trade.bot_name}</td>
                                            <td className="px-4 py-3">{trade.symbol}</td>
                                            <td className="px-4 py-3">
                                                <Badge
                                                    variant={trade.side === 'BUY' ? 'success' : 'destructive'}
                                                    className="uppercase text-[10px]"
                                                >
                                                    {trade.side}
                                                </Badge>
                                            </td>
                                            <td className="px-4 py-3 font-mono">
                                                {trade.execution?.price.toLocaleString() || '-'}
                                            </td>
                                            <td className="px-4 py-3 font-mono">
                                                {trade.execution?.quantity || trade.intent_quantity}
                                            </td>
                                            <td className="px-4 py-3 font-mono text-muted-foreground">
                                                {trade.execution ? `$${trade.execution.fee.toFixed(4)}` : '-'}
                                            </td>
                                            <td className={`px-4 py-3 font-mono ${trade.execution?.realized_pnl && trade.execution.realized_pnl >= 0
                                                    ? 'text-emerald-400'
                                                    : 'text-red-400'
                                                }`}>
                                                {formatPnL(trade.execution?.realized_pnl ?? null)}
                                            </td>
                                            <td className="px-4 py-3">
                                                <Badge
                                                    variant={
                                                        trade.status === 'FILLED' ? 'success'
                                                            : trade.status === 'FAILED' ? 'destructive'
                                                                : 'outline'
                                                    }
                                                    className="text-[10px]"
                                                >
                                                    {trade.status}
                                                </Badge>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
