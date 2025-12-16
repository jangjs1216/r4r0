import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { ArrowUpRight } from 'lucide-react';

export default function PortfolioView() {
    const assets = [
        { coin: 'USDT', balance: '24,350.50', value: '$24,350.50', alloc: '57.5%', pnl: '+0.0%' },
        { coin: 'BTC', balance: '0.421500', value: '$17,725.20', alloc: '41.8%', pnl: '+12.5%' },
        { coin: 'ETH', balance: '1.250000', value: '$2,850.50', alloc: '0.6%', pnl: '-2.4%' },
        { coin: 'SOL', balance: '45.00000', value: '$450.00', alloc: '0.1%', pnl: '+5.2%' },
    ];

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold">Portfolio Management</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>Asset Allocation</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-muted-foreground uppercase bg-secondary/30">
                                    <tr>
                                        <th className="px-4 py-3 rounded-l-lg">Asset</th>
                                        <th className="px-4 py-3">Balance</th>
                                        <th className="px-4 py-3">Value (USDT)</th>
                                        <th className="px-4 py-3">Allocation</th>
                                        <th className="px-4 py-3 rounded-r-lg text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {assets.map((asset, i) => (
                                        <tr key={i} className="border-b border-border/50 hover:bg-secondary/10 transition-colors">
                                            <td className="px-4 py-4 font-medium flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs">{asset.coin[0]}</div>
                                                {asset.coin}
                                            </td>
                                            <td className="px-4 py-4 font-mono text-muted-foreground">{asset.balance}</td>
                                            <td className="px-4 py-4 font-bold">{asset.value}</td>
                                            <td className="px-4 py-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                                                        <div className="h-full bg-primary" style={{ width: asset.alloc }}></div>
                                                    </div>
                                                    <span className="text-xs text-muted-foreground">{asset.alloc}</span>
                                                </div>
                                            </td>
                                            <td className={`px-4 py-4 text-right font-bold ${asset.pnl.startsWith('+') ? 'text-emerald-500' : 'text-red-500'}`}>
                                                {asset.pnl}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Total Balance</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-6">
                        <div>
                            <p className="text-3xl font-bold">$45,376.20</p>
                            <p className="text-sm text-emerald-500 flex items-center mt-1">
                                <ArrowUpRight size={16} className="mr-1" /> +$1,240.50 (2.4%)
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Available Margin</span>
                                <span className="font-mono">$24,350.50</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">In Positions</span>
                                <span className="font-mono">$21,025.70</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Unrealized PnL</span>
                                <span className="font-mono text-emerald-500">+$450.20</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 mt-auto">
                            <button className="bg-primary text-primary-foreground py-2 rounded-lg font-medium hover:opacity-90">Deposit</button>
                            <button className="bg-secondary text-secondary-foreground py-2 rounded-lg font-medium hover:bg-secondary/80">Withdraw</button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
