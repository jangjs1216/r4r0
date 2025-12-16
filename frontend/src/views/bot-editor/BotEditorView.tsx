import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { useOrchestratorStore } from '../../orchestrator/store';
import { ArrowLeft, Save, Play, Square, Settings as SettingsIcon } from 'lucide-react';

export default function BotEditorView() {
    const { setView, editingBotId, setEditingBotId } = useOrchestratorStore();

    // Mock Data: Strategies
    const strategies = [
        {
            id: 'grid',
            name: 'Grid Trading',
            description: 'Places orders at regular intervals within a price range',
            params: {
                upperPrice: { type: 'number', label: 'Upper Price', default: 50000 },
                lowerPrice: { type: 'number', label: 'Lower Price', default: 40000 },
                grids: { type: 'number', label: 'Grid Count', default: 10 }
            }
        },
        {
            id: 'rsi',
            name: 'RSI Reversal',
            description: 'Buys when RSI is oversold, Sells when overbought',
            params: {
                period: { type: 'number', label: 'RSI Period', default: 14 },
                overbought: { type: 'number', label: 'Overbought Level', default: 70 },
                oversold: { type: 'number', label: 'Oversold Level', default: 30 }
            }
        },
        {
            id: 'vwap',
            name: 'VWAP Trend',
            description: 'Follows Volume Weighted Average Price trend',
            params: {
                maType: { type: 'select', label: 'MA Type', options: ['SMA', 'EMA'], default: 'SMA' },
                period: { type: 'number', label: 'Lookback', default: 20 }
            }
        }
    ];

    // State
    const [mode] = useState<'create' | 'edit'>(editingBotId ? 'edit' : 'create');
    const [selectedStrategyId, setSelectedStrategyId] = useState<string>('grid');
    const [botName, setBotName] = useState(editingBotId ? 'My Grid Bot #1' : '');
    const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
    const [allocation, setAllocation] = useState(0.2);

    // Dynamic Params State
    const [params, setParams] = useState<Record<string, any>>({});

    const currentStrategy = strategies.find(s => s.id === selectedStrategyId);

    // Init params with defaults when strategy changes
    useEffect(() => {
        if (currentStrategy) {
            const defaults: Record<string, any> = {};
            Object.entries(currentStrategy.params).forEach(([key, conf]) => {
                defaults[key] = conf.default;
            });
            setParams(defaults);
        }
    }, [selectedStrategyId]);

    const handleBack = () => {
        setEditingBotId(null);
        setView('bot-config');
    };

    const handleSave = () => {
        console.log('Saving Bot:', {
            id: editingBotId,
            name: botName,
            strategy: selectedStrategyId,
            symbol: selectedSymbol,
            allocation,
            params
        });
        handleBack();
    };

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleBack}
                        className="p-2 hover:bg-secondary rounded-full transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            {mode === 'create' ? 'Create New Bot' : 'Edit Bot Configuration'}
                        </h1>
                        <p className="text-muted-foreground text-sm">
                            {mode === 'create' ? 'Configure a new automated trading strategy' : `ID: ${editingBotId}`}
                        </p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleBack}
                        className="px-4 py-2 text-sm font-medium hover:bg-secondary rounded-md transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 flex items-center gap-2"
                    >
                        <Save size={16} />
                        Save Configuration
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Left Column: Strategy Selection */}
                <Card className="md:col-span-1 h-fit">
                    <CardHeader>
                        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">Select Strategy</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {strategies.map(strategy => (
                            <div
                                key={strategy.id}
                                onClick={() => setSelectedStrategyId(strategy.id)}
                                className={`p-4 rounded-lg border cursor-pointer transition-all ${selectedStrategyId === strategy.id
                                        ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                                        : 'border-border hover:bg-secondary/50'
                                    }`}
                            >
                                <div className="font-semibold mb-1">{strategy.name}</div>
                                <div className="text-xs text-muted-foreground line-clamp-2">{strategy.description}</div>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                {/* Right Column: Configuration Form */}
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">Bot Parameters</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Basic Info */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-medium text-muted-foreground">Bot Name</label>
                                <input
                                    type="text"
                                    value={botName}
                                    onChange={(e) => setBotName(e.target.value)}
                                    placeholder="e.g. BTC Grid Alpha"
                                    className="w-full bg-secondary/20 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-medium text-muted-foreground">Symbol</label>
                                <select
                                    value={selectedSymbol}
                                    onChange={(e) => setSelectedSymbol(e.target.value)}
                                    className="w-full bg-secondary/20 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary appearance-none"
                                >
                                    <option>BTC/USDT</option>
                                    <option>ETH/USDT</option>
                                    <option>SOL/USDT</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-medium text-muted-foreground flex justify-between">
                                <span>Capital Allocation</span>
                                <span>{(allocation * 100).toFixed(0)}%</span>
                            </label>
                            <input
                                type="range"
                                min="0" max="1" step="0.05"
                                value={allocation}
                                onChange={(e) => setAllocation(parseFloat(e.target.value))}
                                className="w-full"
                            />
                            <div className="text-xs text-muted-foreground text-right">
                                Est. Capital: ~${(allocation * 10000).toLocaleString()} (Mock)
                            </div>
                        </div>

                        <div className="h-px bg-border/50 my-4" />

                        {/* Dynamic Strategy Params */}
                        <div className="space-y-4">
                            <h3 className="text-sm font-semibold flex items-center gap-2 text-primary">
                                <SettingsIcon size={16} />
                                {currentStrategy?.name} Settings
                            </h3>

                            {currentStrategy && Object.entries(currentStrategy.params).map(([key, conf]: [string, any]) => (
                                <div key={key} className="space-y-2">
                                    <label className="text-xs font-medium text-muted-foreground">{conf.label}</label>
                                    {conf.type === 'select' ? (
                                        <select
                                            value={params[key] || conf.default}
                                            onChange={(e) => setParams({ ...params, [key]: e.target.value })}
                                            className="w-full bg-secondary/20 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary appearance-none"
                                        >
                                            {conf.options.map((opt: string) => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            type={conf.type}
                                            value={params[key] || ''}
                                            onChange={(e) => setParams({ ...params, [key]: e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value })}
                                            className="w-full bg-secondary/20 border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
