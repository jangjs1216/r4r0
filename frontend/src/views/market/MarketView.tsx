import { Card, CardContent, CardHeader, CardTitle } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';

export default function MarketView() {
    const bids = Array.from({ length: 15 }).map((_, i) => ({
        price: 42000 - i * 10,
        amount: (Math.random() * 2).toFixed(4),
        total: (Math.random() * 10).toFixed(4)
    }));

    const asks = Array.from({ length: 15 }).map((_, i) => ({
        price: 42050 + i * 10,
        amount: (Math.random() * 2).toFixed(4),
        total: (Math.random() * 10).toFixed(4)
    }));

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Market: BTC/USDT</h2>
                <div className="flex gap-4">
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground">Last Price</p>
                        <p className="text-xl font-bold text-emerald-500">$42,045.22</p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground">24h Vol</p>
                        <p className="font-mono">1,240 BTC</p>
                    </div>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
                {/* Chart Placeholder */}
                <Card className="lg:col-span-2 flex flex-col">
                    <CardHeader className="py-3 px-4 border-b border-border/50">
                        <div className="flex gap-2">
                            <Badge variant="secondary" className="cursor-pointer">15m</Badge>
                            <Badge variant="default" className="cursor-pointer">1H</Badge>
                            <Badge variant="secondary" className="cursor-pointer">4H</Badge>
                            <Badge variant="secondary" className="cursor-pointer">1D</Badge>
                        </div>
                    </CardHeader>
                    <CardContent className="flex-1 flex items-center justify-center bg-secondary/5 relative overflow-hidden p-0">
                        {/* Grid lines */}
                        <div className="absolute inset-0 grid grid-cols-6 grid-rows-4">
                            {Array.from({ length: 24 }).map((_, i) => (
                                <div key={i} className="border-r border-b border-border/10"></div>
                            ))}
                        </div>
                        <p className="text-muted-foreground z-10 font-mono text-sm">TradingView Chart Integration Area</p>
                    </CardContent>
                </Card>

                {/* Order Book */}
                <Card className="flex flex-col min-h-0">
                    <CardHeader className="py-3 px-4 border-b border-border/50">
                        <CardTitle className="text-sm">Order Book</CardTitle>
                    </CardHeader>
                    <div className="flex-1 overflow-auto p-0 font-mono text-xs">
                        {/* Asks */}
                        <div className="flex flex-col-reverse">
                            {asks.map((ask, i) => (
                                <div key={i} className="grid grid-cols-3 px-4 py-0.5 hover:bg-secondary/20 cursor-pointer relative group">
                                    <span className="text-red-400">{ask.price}</span>
                                    <span className="text-right text-muted-foreground">{ask.amount}</span>
                                    <span className="text-right text-muted-foreground opacity-50">{ask.total}</span>
                                    <div className="absolute top-0 right-0 bottom-0 bg-red-500/10" style={{ width: `${Math.random() * 40}%` }}></div>
                                </div>
                            ))}
                        </div>

                        <div className="py-2 border-y border-border/50 text-center text-lg font-bold my-1 sticky top-0 bg-card z-10 backdrop-blur">
                            42,045.50
                        </div>

                        {/* Bids */}
                        <div>
                            {bids.map((bid, i) => (
                                <div key={i} className="grid grid-cols-3 px-4 py-0.5 hover:bg-secondary/20 cursor-pointer relative group">
                                    <span className="text-emerald-400">{bid.price}</span>
                                    <span className="text-right text-muted-foreground">{bid.amount}</span>
                                    <span className="text-right text-muted-foreground opacity-50">{bid.total}</span>
                                    <div className="absolute top-0 right-0 bottom-0 bg-emerald-500/10" style={{ width: `${Math.random() * 40}%` }}></div>
                                </div>
                            ))}
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
