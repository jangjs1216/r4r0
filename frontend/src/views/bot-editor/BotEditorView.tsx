import React, { useEffect, useState } from 'react';
import { BotService } from './api';
import type { StrategyDefinition, BotConfig, ExchangeCredential } from './api';
import { ChevronRight, CheckCircle, AlertCircle, Save, ArrowLeft, Activity, ShieldCheck, Settings2, Wallet } from 'lucide-react';
import { useOrchestratorStore } from '../../orchestrator/store';

// --- Components ---

const SectionCard = ({ title, icon: Icon, children, step }: { title: string, icon: any, children: React.ReactNode, step: number }) => (
    <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl opacity-30 group-hover:opacity-60 transition duration-500 blur"></div>
        <div className="relative bg-gray-900/90 backdrop-blur-xl rounded-xl border border-gray-800 p-6 shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 font-bold text-sm ring-1 ring-blue-500/50">
                    {step}
                </div>
                <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                    {Icon && <Icon size={20} className="text-gray-400" />}
                    {title}
                </h2>
            </div>
            {children}
        </div>
    </div>
);

const InputGroup = ({ label, children }: { label: string, children: React.ReactNode }) => (
    <div className="mb-4">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 ml-1">
            {label}
        </label>
        {children}
    </div>
);

const StyledInput = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <input
        {...props}
        className="w-full bg-gray-950/50 border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all font-mono text-sm"
    />
);

const StyledSelect = (props: React.SelectHTMLAttributes<HTMLSelectElement>) => (
    <div className="relative">
        <select
            {...props}
            className="w-full appearance-none bg-gray-950/50 border border-gray-700/50 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all font-mono text-sm"
        />
        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
            <ChevronRight className="rotate-90" size={16} />
        </div>
    </div>
);

// Minimal Schema Form Renderer
const SchemaObjectRenderer = ({ schema, value, onChange }: { schema: any, value: any, onChange: (v: any) => void }) => {
    if (!schema?.properties) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.keys(schema.properties).map(key => {
                const field = schema.properties[key];
                const fieldValue = value?.[key] ?? field.default ?? '';

                return (
                    <div key={key} className="col-span-1">
                        <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">
                            {field.title || key}
                        </label>
                        <StyledInput
                            type={field.type === 'number' || field.type === 'integer' ? 'number' : 'text'}
                            value={fieldValue}
                            onChange={e => {
                                const val = e.target.value;
                                const parsed = field.type === 'number' || field.type === 'integer' ? parseFloat(val) : val;
                                onChange({ ...value, [key]: parsed });
                            }}
                            placeholder={field.title}
                        />
                        {field.description && <p className="text-xs text-gray-500 mt-1">{field.description}</p>}
                    </div>
                );
            })}
        </div>
    );
};


const BotEditorView: React.FC = () => {
    const { setView } = useOrchestratorStore();
    const [strategies, setStrategies] = useState<StrategyDefinition[]>([]);
    const [exchanges, setExchanges] = useState<ExchangeCredential[]>([]);
    const [loading, setLoading] = useState(true);

    const [formData, setFormData] = useState<BotConfig>({
        name: '',
        status: 'STOPPED',
        global_settings: { exchange: '', symbol: 'BTC/USDT', mode: 'PAPER', account_allocation: 1000 },
        pipeline: {
            strategy: { id: '', params: {} },
            risk_management: { stop_loss: 5.0, max_drawdown: 10.0 }, // default values
            execution: { type: 'MAKER_ONLY' }
        }
    });

    useEffect(() => {
        Promise.all([
            BotService.getStrategies(),
            BotService.getExchanges()
        ]).then(([strats, exchs]) => {
            setStrategies(strats);
            setExchanges(exchs);
            // Set default exchange if available
            if (exchs.length > 0 && !formData.global_settings.exchange) {
                setFormData(prev => ({
                    ...prev,
                    global_settings: { ...prev.global_settings, exchange: exchs[0].id }
                }));
            }
            setLoading(false);
        }).catch(console.error);
    }, []);

    const handleSave = async () => {
        if (!formData.name) return alert("Please enter a bot name");
        if (!formData.pipeline.strategy.id) return alert("Please select a strategy");

        try {
            const saved = await BotService.createBot(formData);
            alert(`Bot Created Successfully!\nID: ${saved.id}`);
            setView('bot-config'); // Go back to list
        } catch (e) {
            alert('Failed to save bot. Check console for details.');
            console.error(e);
        }
    };

    const selectedStrategy = strategies.find(s => s.id === formData.pipeline.strategy.id);

    if (loading) return (
        <div className="h-full flex items-center justify-center bg-gray-950 text-blue-400">
            <div className="animate-spin mr-2"><Activity /></div> Loading Editor...
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-950 text-gray-200 pb-20">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button onClick={() => setView('bot-config')} className="p-2 hover:bg-gray-800 rounded-full transition">
                        <ArrowLeft size={20} />
                    </button>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                        Configure Bot Pipeline
                    </h1>
                </div>
                <div className="flex gap-3">
                    <button className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition">Reset</button>
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-lg text-white font-semibold shadow-lg shadow-purple-900/20 transition-all hover:scale-105 active:scale-95"
                    >
                        <Save size={18} />
                        Save Pipeline
                    </button>
                </div>
            </header>

            <div className="max-w-5xl mx-auto p-8 space-y-8">

                {/* 1. General Info */}
                <SectionCard title="General & Exchange" icon={Settings2} step={1}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <InputGroup label="Bot Name">
                            <StyledInput
                                placeholder="e.g. My Alpha Grid Bot"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                            />
                        </InputGroup>

                        <InputGroup label="Trading Mode">
                            <div className="grid grid-cols-3 gap-2 bg-gray-950/50 p-1 rounded-lg border border-gray-700/50">
                                {['PAPER', 'REAL', 'BACKTEST'].map(m => (
                                    <button
                                        key={m}
                                        onClick={() => setFormData({ ...formData, global_settings: { ...formData.global_settings, mode: m as any } })}
                                        className={`py-2 text-sm font-medium rounded-md transition-all ${formData.global_settings.mode === m
                                            ? 'bg-blue-600 text-white shadow-lg'
                                            : 'text-gray-500 hover:text-gray-300'
                                            }`}
                                    >
                                        {m}
                                    </button>
                                ))}
                            </div>
                        </InputGroup>

                        <InputGroup label="Connect Exchange">
                            <StyledSelect
                                value={formData.global_settings.exchange}
                                onChange={e => setFormData({ ...formData, global_settings: { ...formData.global_settings, exchange: e.target.value } })}
                            >
                                {exchanges.map(ex => (
                                    <option key={ex.id} value={ex.id}>{ex.label} ({ex.exchange})</option>
                                ))}
                                {exchanges.length === 0 && <option value="">No Keys Found (Add in Auth)</option>}
                            </StyledSelect>
                        </InputGroup>

                        <InputGroup label="Target Symbol">
                            <StyledSelect
                                value={formData.global_settings.symbol}
                                onChange={e => setFormData({ ...formData, global_settings: { ...formData.global_settings, symbol: e.target.value } })}
                            >
                                {/* Hardcoded for now as per plan */}
                                {['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT', 'DOGE/USDT'].map(s => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </StyledSelect>
                        </InputGroup>
                    </div>
                </SectionCard>

                {/* 2. Strategy Logic */}
                <SectionCard title="Strategy Logic" icon={Activity} step={2}>
                    <InputGroup label="Select Strategy Template">
                        <StyledSelect
                            value={formData.pipeline.strategy.id}
                            onChange={e => {
                                setFormData({
                                    ...formData,
                                    pipeline: { ...formData.pipeline, strategy: { id: e.target.value, params: {} } }
                                });
                            }}
                        >
                            <option value="">-- Choose Strategy --</option>
                            {strategies.map(s => (
                                <option key={s.id} value={s.id}>{s.name} (v{s.version})</option>
                            ))}
                        </StyledSelect>
                    </InputGroup>

                    {selectedStrategy ? (
                        <div className="mt-6 pt-6 border-t border-gray-800 animate-in fade-in slide-in-from-top-4 duration-500">
                            <div className="bg-gray-800/50 rounded-lg p-4 mb-4 text-sm text-gray-400 border border-gray-700/50">
                                {selectedStrategy.description}
                            </div>
                            {/* Dynamic Form */}
                            <SchemaObjectRenderer
                                schema={selectedStrategy.schema}
                                value={formData.pipeline.strategy.params}
                                onChange={newParams => setFormData({
                                    ...formData,
                                    pipeline: { ...formData.pipeline, strategy: { ...formData.pipeline.strategy, params: newParams } }
                                })}
                            />
                        </div>
                    ) : (
                        <div className="h-32 flex items-center justify-center text-gray-600 border-2 border-dashed border-gray-800 rounded-lg">
                            Select a strategy to configure parameters
                        </div>
                    )}
                </SectionCard>

                {/* 3. Risk & Capital */}
                <SectionCard title="Risk & Capital Management" icon={ShieldCheck} step={3}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <InputGroup label="Account Allocation">
                            <div className="relative">
                                <StyledInput
                                    type="number"
                                    value={formData.global_settings.account_allocation}
                                    onChange={e => setFormData({
                                        ...formData,
                                        global_settings: { ...formData.global_settings, account_allocation: parseFloat(e.target.value) }
                                    })}
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm">USDT</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">Amount of capital dedicated to this bot.</p>
                        </InputGroup>

                        <InputGroup label="Stop Loss (%)">
                            <StyledInput
                                type="number"
                                value={formData.pipeline.risk_management?.stop_loss}
                                onChange={e => setFormData({
                                    ...formData,
                                    pipeline: {
                                        ...formData.pipeline,
                                        risk_management: { ...formData.pipeline.risk_management, stop_loss: parseFloat(e.target.value) }
                                    }
                                })}
                            />
                        </InputGroup>
                    </div>
                </SectionCard>

            </div>
        </div>
    );
};

export default BotEditorView;
