import { Activity, ArrowUpRight, DollarSign, Wallet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { cn } from '../../lib/utils';

export default function DashboardView() {
    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                    <p className="text-muted-foreground mt-1">Overview of your automated trading performance.</p>
                </div>
                <div className="flex gap-2">
                    <Badge variant="outline" className="px-3 py-1 text-sm h-9">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                        System Operational
                    </Badge>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">$42,350.21</div>
                        <p className="text-xs text-muted-foreground flex items-center mt-1">
                            <span className="text-emerald-500 flex items-center mr-1">
                                <ArrowUpRight className="h-3 w-3" /> +12.5%
                            </span>
                            from last month
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Bots</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">5</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            3 Scalping, 2 Arbitrage
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">24h PnL</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-emerald-500">+$1,240.50</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            +2.4% daily return
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">8</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Exposure: $12,400 (Leverage 1.2x)
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">

                {/* Chart Area (Mock) */}
                <Card className="lg:col-span-4">
                    <CardHeader>
                        <CardTitle>PnL Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] flex items-end justify-between gap-1 p-4 bg-secondary/10 rounded-lg border border-dashed border-border/50">
                            {/* Mock Chart bars */}
                            {[40, 60, 45, 70, 85, 60, 75, 50, 65, 80, 95, 85, 70, 75, 90, 100, 80, 85, 70, 75, 90, 80, 95, 100].map((h, i) => (
                                <div key={i} className="w-full bg-primary/20 hover:bg-primary/40 transition-colors rounded-sm" style={{ height: `${h}%` }}></div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Activity */}
                <Card className="lg:col-span-3">
                    <CardHeader>
                        <CardTitle>Recent Bot Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[
                                { bot: 'Scalper X', action: 'Bought BTC', time: '2m ago', amount: '+$24.00', type: 'win' },
                                { bot: 'Arb King', action: 'Sold ETH', time: '15m ago', amount: '+$12.50', type: 'win' },
                                { bot: 'Scalper X', action: 'Stop Loss SOL', time: '1h ago', amount: '-$8.20', type: 'loss' },
                                { bot: 'Trend Follower', action: 'Enter Long', time: '2h ago', amount: 'Pending', type: 'neutral' },
                                { bot: 'Scalper X', action: 'Bought BTC', time: '4h ago', amount: '+$32.10', type: 'win' },
                            ].map((item, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 hover:bg-secondary/40 transition-colors border border-transparent hover:border-border/50">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("w-2 h-2 rounded-full", item.type === 'win' ? 'bg-emerald-500' : item.type === 'loss' ? 'bg-red-500' : 'bg-yellow-500')}></div>
                                        <div>
                                            <p className="text-sm font-medium">{item.bot}</p>
                                            <p className="text-xs text-muted-foreground">{item.action}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={cn("text-sm font-bold", item.type === 'win' ? 'text-emerald-500' : item.type === 'loss' ? 'text-red-500' : 'text-foreground')}>{item.amount}</p>
                                        <p className="text-xs text-muted-foreground">{item.time}</p>
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
