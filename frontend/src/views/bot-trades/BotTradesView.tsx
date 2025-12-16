import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';

export default function BotTradesView() {
    const trades = [
        { id: 'TX-9921', bot: 'Scalper Alpha', pair: 'BTC/USDT', side: 'buy', price: '42,150.00', size: '0.25', time: '12:04:45', pnl: '+0.00' },
        { id: 'TX-9920', bot: 'Scalper Alpha', pair: 'BTC/USDT', side: 'sell', price: '42,320.00', size: '0.25', time: '11:58:20', pnl: '+$42.50' },
        { id: 'TX-9919', bot: 'ETH Arb', pair: 'ETH/USDT', side: 'sell', price: '2,890.50', size: '1.5', time: '11:45:10', pnl: '+$12.40' },
        { id: 'TX-9918', bot: 'Solana Trend', pair: 'SOL/USDT', side: 'buy', price: '44.20', size: '15.0', time: '10:30:15', pnl: '-$8.50' },
        { id: 'TX-9917', bot: 'Scalper Alpha', pair: 'BTC/USDT', side: 'buy', price: '42,050.00', size: '0.25', time: '09:12:00', pnl: '+$25.00' },
        { id: 'TX-9916', bot: 'Scalper Alpha', pair: 'BTC/USDT', side: 'sell', price: '42,150.00', size: '0.25', time: '09:05:00', pnl: '+$25.00' },
    ];

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-bold">Bot Trade History</h2>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Recent Executions</CardTitle>
                        <div className="flex gap-2">
                            <button className="text-xs bg-secondary px-2 py-1 rounded hover:bg-secondary/80">Export CSV</button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-muted-foreground uppercase bg-secondary/30">
                            <tr>
                                <th className="px-4 py-3 rounded-l-lg">Time</th>
                                <th className="px-4 py-3">Bot</th>
                                <th className="px-4 py-3">Pair</th>
                                <th className="px-4 py-3">Side</th>
                                <th className="px-4 py-3">Price</th>
                                <th className="px-4 py-3">Size</th>
                                <th className="px-4 py-3 rounded-r-lg text-right">Realized PnL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade) => (
                                <tr key={trade.id} className="border-b border-border/50 hover:bg-secondary/10 transition-colors">
                                    <td className="px-4 py-3 font-mono text-muted-foreground">{trade.time}</td>
                                    <td className="px-4 py-3 font-medium">{trade.bot}</td>
                                    <td className="px-4 py-3">{trade.pair}</td>
                                    <td className="px-4 py-3">
                                        <Badge variant={trade.side === 'buy' ? 'success' : 'destructive'} className="uppercase text-[10px]">
                                            {trade.side}
                                        </Badge>
                                    </td>
                                    <td className="px-4 py-3 font-mono">{trade.price}</td>
                                    <td className="px-4 py-3 font-mono">{trade.size}</td>
                                    <td className={`px-4 py-3 text-right font-medium ${trade.pnl.startsWith('+') ? 'text-emerald-500' : 'text-red-500'}`}>
                                        {trade.pnl}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    );
}
