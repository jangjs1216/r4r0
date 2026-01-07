import React from 'react';
import type { BacktestResult } from './types';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    ReferenceLine
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign, Percent, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Props {
    result: BacktestResult;
}

// --- Sub-components ---

const MetricCard = ({ label, value, subValue, icon: Icon, trend, colorClass }: any) => (
    <div className="relative group overflow-hidden rounded-2xl bg-gray-900/50 border border-gray-800/50 p-5 hover:border-gray-700/50 transition-all duration-300">
        <div className={cn("absolute top-0 right-0 p-3 opacity-20", colorClass)}>
            <Icon size={48} />
        </div>
        <div className="relative z-10">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">{label}</p>
            <div className="flex items-baseline gap-2">
                <h3 className={cn("text-2xl font-bold font-mono tracking-tight", colorClass)}>
                    {value}
                </h3>
                {subValue && (
                    <span className="text-xs text-gray-400 font-medium">
                        {subValue}
                    </span>
                )}
            </div>
            {trend && (
                <div className={cn("flex items-center gap-1 mt-2 text-xs font-medium",
                    trend === 'up' ? "text-green-500" : "text-red-500"
                )}>
                    {trend === 'up' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    <span>{trend === 'up' ? 'Positive' : 'Negative'} Outlook</span>
                </div>
            )}
        </div>
        {/* Glow Effect */}
        <div className={cn("absolute -bottom-10 -left-10 w-32 h-32 bg-gradient-to-tr rounded-full blur-[60px] opacity-10 pointer-events-none",
            colorClass.includes('green') ? 'from-green-500' :
                colorClass.includes('red') ? 'from-red-500' :
                    colorClass.includes('blue') ? 'from-blue-500' : 'from-gray-500'
        )} />
    </div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-gray-900/90 backdrop-blur-xl border border-gray-800 p-4 rounded-xl shadow-2xl">
                <p className="text-gray-400 text-xs mb-2">{label}</p>
                <div className="space-y-1">
                    <p className="text-sm font-bold text-blue-400 flex justify-between gap-4">
                        <span>Strategy:</span>
                        <span className="font-mono">${payload[0].value.toFixed(2)}</span>
                    </p>
                    {payload[1] && (
                        <p className="text-sm font-bold text-gray-500 flex justify-between gap-4">
                            <span>Hold:</span>
                            <span className="font-mono">${payload[1].value.toFixed(2)}</span>
                        </p>
                    )}
                </div>
            </div>
        );
    }
    return null;
};

// --- Main Component ---

export const BacktestResultDashboard: React.FC<Props> = ({ result }) => {
    return (
        <div className="flex flex-col h-full gap-6 animate-in fade-in duration-500">

            {/* 1. Main Chart Section */}
            <div className="flex-grow min-h-[450px] bg-gray-950/50 rounded-3xl border border-gray-800/80 p-6 shadow-2xl relative overflow-hidden group flex flex-col">
                <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none" />

                <div className="flex-none flex items-center justify-between mb-6 relative z-10">
                    <div>
                        <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                            <Activity className="text-blue-500" size={20} />
                            Equity Curve
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">Strategy Performance vs Benchmark</p>
                    </div>
                    <div className="flex gap-2">
                        <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20">
                            Strategy
                        </span>
                        <span className="px-3 py-1 rounded-full bg-gray-800 text-gray-400 text-xs font-medium border border-gray-700">
                            Buy & Hold
                        </span>
                    </div>
                </div>

                <div className="flex-grow w-full relative min-h-0">
                    <div className="absolute inset-0">
                        {result.equity_curve && result.equity_curve.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                <AreaChart data={result.equity_curve} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorHold" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#6B7280" stopOpacity={0.1} />
                                            <stop offset="95%" stopColor="#6B7280" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                                    <XAxis
                                        dataKey="timestamp"
                                        stroke="#4B5563"
                                        tick={{ fontSize: 11, fill: '#6B7280' }}
                                        tickLine={false}
                                        axisLine={false}
                                        dy={10}
                                        tickFormatter={(unixTime) => new Date(unixTime).toLocaleDateString()}
                                    />
                                    <YAxis
                                        stroke="#4B5563"
                                        tick={{ fontSize: 11, fill: '#6B7280' }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(val) => `$${val / 1000}k`}
                                        dx={-10}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#374151', strokeWidth: 1, strokeDasharray: '4 4' }} />
                                    <Area
                                        type="monotone"
                                        dataKey="balance"
                                        stroke="#3B82F6"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorValue)"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="buy_hold_price"
                                        stroke="#4B5563"
                                        strokeWidth={2}
                                        strokeDasharray="4 4"
                                        fillOpacity={1}
                                        fill="url(#colorHold)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                No equity data available
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* 2. Metrics Grid (Bottom) */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard
                    label="Net Profit"
                    value={`+$${result.metrics.total_pnl.toLocaleString()}`}
                    subValue=""
                    icon={DollarSign}
                    trend="up"
                    colorClass="text-green-400"
                />
                <MetricCard
                    label="CAGR"
                    value={`${result.metrics.cagr}%`}
                    subValue="Annualized"
                    icon={TrendingUp}
                    trend="up"
                    colorClass="text-blue-400"
                />
                <MetricCard
                    label="Max Drawdown"
                    value={`${result.metrics.mdd}%`}
                    subValue="Peak to Valley"
                    icon={AlertTriangle}
                    trend="down"
                    colorClass="text-red-400"
                />
                <MetricCard
                    label="Win Rate"
                    value={`${(result.metrics.win_rate * 100).toFixed(1)}%`}
                    subValue={`${result.metrics.total_cost > 500 ? 'High Activity' : 'Low Activity'}`}
                    icon={Percent}
                    trend="up"
                    colorClass="text-purple-400"
                />
                <MetricCard
                    label="Sharpe Ratio"
                    value={result.metrics.sharpe_ratio.toFixed(2)}
                    subValue="Risk Adjusted"
                    icon={Activity}
                    trend="up"
                    colorClass="text-orange-400"
                />
            </div>

            {/* 3. Cost Strip (Integrated) */}
            <div className="bg-gray-900/30 border border-gray-800 rounded-xl p-4 flex items-center justify-between text-sm text-gray-400">
                <div className="flex gap-6">
                    <div>
                        <span className="block text-xs uppercase text-gray-600 font-semibold mb-1">Gross Alpha</span>
                        <span className="font-mono text-gray-200">+${result.metrics.alpha_gross.toLocaleString()}</span>
                    </div>
                    <div className="h-8 w-px bg-gray-800"></div>
                    <div>
                        <span className="block text-xs uppercase text-gray-600 font-semibold mb-1">Total Cost</span>
                        <span className="font-mono text-red-400">-${result.metrics.total_cost.toLocaleString()}</span>
                    </div>
                </div>
                <div className="flex gap-4 opacity-70">
                    <span className="text-xs">Fees: <b>${result.cost_breakdown.commission}</b></span>
                    <span className="text-xs">Slippage: <b>${result.cost_breakdown.slippage_cost}</b></span>
                    <span className="text-xs">Funding: <b>${result.cost_breakdown.funding_fee}</b></span>
                </div>
            </div>

        </div>
    );
};
