import { useState, useEffect } from 'react';
import { Activity, DollarSign, BarChart3, ArrowUpRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../shared/components/Card';
import { useOrchestratorStore } from '../../orchestrator/store';
import { cn } from '../../lib/utils';

export default function DashboardView() {
    const { setView } = useOrchestratorStore();

    // State for real data
    const [netWorth, setNetWorth] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    // Mock PnL data (Backend endpoint for PnL not ready yet)
    const pnl = 1250.50; // +12.5%
    const pnlPercent = 12.5;

    useEffect(() => {
        const fetchTotalBalance = async () => {
            try {
                // 1. Fetch Keys
                // In dev mode (Vite), we might need full URL if proxy isn't set up for localhost:5173 -> localhost:8000/8001
                // Assuming relative path works via Vite proxy or Nginx.

                const keysRes = await fetch('/api/keys');
                if (!keysRes.ok) throw new Error('Failed to fetch keys');
                const keys = await keysRes.json();

                if (keys.length === 0) {
                    setNetWorth(0);
                    setLoading(false);
                    return;
                }

                // 2. Fetch Balance for each key
                let total = 0;
                await Promise.all(keys.map(async (key: any) => {
                    try {
                        const balRes = await fetch(`/api/adapter/balance/${key.id}`);
                        if (balRes.ok) {
                            const balData = await balRes.json();
                            total += balData.totalUsdtValue || 0;
                        }
                    } catch (err) {
                        console.error(`Failed to fetch balance for key ${key.id}`, err);
                    }
                }));

                setNetWorth(total);
            } catch (err) {
                console.error("Dashboard Error:", err);
                // Fallback to 0 if error, or keep as null to show error state
                setNetWorth(0);
            } finally {
                setLoading(false);
            }
        };

        fetchTotalBalance();
    }, []);

    return (
        <div className="p-6 h-[calc(100vh-4rem)] overflow-y-auto">
            <h1 className="text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400">
                Dashboard
            </h1>

            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <Card className="hover:border-primary/50 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Net Worth</CardTitle>
                        <DollarSign className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {loading ? (
                                <div className="h-8 w-24 bg-secondary/50 animate-pulse rounded" />
                            ) : (
                                `$${netWorth?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {loading ? "Loading..." : "+2.5% from last month"}
                        </p>
                    </CardContent>
                </Card>

                <Card className="hover:border-primary/50 transition-colors">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total PnL (24h)</CardTitle>
                        <Activity className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-500">
                            +${pnl.toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            +{pnlPercent}% today
                        </p>
                    </CardContent>
                </Card>

                <Card
                    className="hover:border-primary/50 transition-colors cursor-pointer group"
                    onClick={() => setView('bot-config')}
                >
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors">Active Bots</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            2 Grid, 1 RSI
                        </p>
                    </CardContent>
                </Card>

                <Card
                    className="hover:border-primary/50 transition-colors cursor-pointer group"
                    onClick={() => setView('market')}
                >
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors">Market Status</CardTitle>
                        <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-500">Bullish</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            BTC Dominance: 52%
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Areas */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart Area */}
                <Card className="col-span-1 lg:col-span-2 min-h-[400px]">
                    <CardHeader>
                        <CardTitle>Portfolio Performance</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center h-[300px]">
                        <p className="text-muted-foreground">Chart Component Placeholder</p>
                    </CardContent>
                </Card>

                {/* Recent Activity / Logs */}
                <Card className="col-span-1 min-h-[400px]">
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="flex items-center justify-between border-b border-border/50 pb-2 last:border-0">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("w-2 h-2 rounded-full", i % 2 === 0 ? 'bg-green-500' : 'bg-red-500')} />
                                        <div>
                                            <p className="text-sm font-medium">{i % 2 === 0 ? 'Buy BTC' : 'Sell ETH'}</p>
                                            <p className="text-xs text-muted-foreground">10:2{i} AM</p>
                                        </div>
                                    </div>
                                    <div className="text-sm font-medium">
                                        ${(1000 * i).toLocaleString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
