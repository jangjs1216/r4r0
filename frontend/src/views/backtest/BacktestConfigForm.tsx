import React, { useEffect, useState } from 'react';
import { Play, Loader2, Calendar, DollarSign, Settings2, Bot } from 'lucide-react';
import { BotService, type BotConfig } from '../bot-editor/api';
import { BacktestAPI, type BacktestResponse } from './api';

interface Props {
    onRun?: (result: BacktestResponse) => void;
    isRunning?: boolean;
    setIsRunning?: (running: boolean) => void;
}

export const BacktestConfigForm: React.FC<Props> = ({ onRun, isRunning = false, setIsRunning }) => {
    const [bots, setBots] = useState<BotConfig[]>([]);
    const [selectedBotId, setSelectedBotId] = useState<string>('');
    const [startDate, setStartDate] = useState('2024-01-01');
    const [endDate, setEndDate] = useState('2024-02-01');
    const [capital, setCapital] = useState(10000);
    const [slippage, setSlippage] = useState<'NONE' | 'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM');

    useEffect(() => {
        // Fetch bots on mount
        const fetchBots = async () => {
            const allBots = await BotService.getAllBots();
            setBots(allBots);
            if (allBots.length > 0) {
                setSelectedBotId(allBots[0].id || '');
            }
        };
        fetchBots();
    }, []);

    const handleRun = async () => {
        if (!selectedBotId) return;
        const bot = bots.find(b => b.id === selectedBotId);
        if (!bot) return;

        if (setIsRunning) setIsRunning(true);

        try {
            const request = {
                bot_config: bot,
                time_range: {
                    start_date: new Date(startDate).toISOString(),
                    end_date: new Date(endDate).toISOString()
                },
                initial_capital: Number(capital),
                slippage_model: slippage
            };

            // Call actual API
            const result = await BacktestAPI.runBacktest(request);

            if (onRun) onRun(result);

        } catch (e) {
            console.error(e);
            alert("Backtest Failed. Ensure backend is running and data is available.");
        } finally {
            if (setIsRunning) setIsRunning(false);
        }
    };

    return (
        <div className="flex flex-col gap-6">
            <div className="space-y-4">
                {/* Bot Selection */}
                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <Bot size={12} />
                        Select Bot
                    </label>
                    <select
                        value={selectedBotId}
                        onChange={(e) => setSelectedBotId(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all appearance-none cursor-pointer hover:border-gray-700"
                    >
                        {bots.map(bot => (
                            <option key={bot.id} value={bot.id}>
                                {bot.name} ({bot.global_settings.symbol})
                            </option>
                        ))}
                        {bots.length === 0 && <option>No Bots Available</option>}
                    </select>
                </div>

                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <Calendar size={12} />
                        Period
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        <input
                            type="date"
                            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                            value={startDate}
                            onChange={e => setStartDate(e.target.value)}
                        />
                        <input
                            type="date"
                            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                            value={endDate}
                            onChange={e => setEndDate(e.target.value)}
                        />
                    </div>
                </div>

                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <DollarSign size={12} />
                        Capital
                    </label>
                    <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
                        <input
                            type="number"
                            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-8 pr-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                            value={capital}
                            onChange={e => setCapital(Number(e.target.value))}
                        />
                    </div>
                </div>

                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <Settings2 size={12} />
                        Slippage Model
                    </label>
                    <select
                        value={slippage}
                        onChange={(e) => setSlippage(e.target.value as any)}
                        className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all appearance-none cursor-pointer hover:border-gray-700"
                    >
                        <option value="NONE">B-Book Simulator (No Slippage)</option>
                        <option value="LOW">High Liquidity (0.05%)</option>
                        <option value="MEDIUM">Standard Market (0.1%)</option>
                        <option value="HIGH">Stress Test (0.2%)</option>
                    </select>
                </div>
            </div>

            <button
                onClick={handleRun}
                disabled={isRunning || bots.length === 0}
                className={`
                    w-full relative overflow-hidden rounded-xl font-bold py-3 text-sm tracking-wide shadow-lg transition-all
                    ${(isRunning || bots.length === 0)
                        ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white hover:scale-[1.02] active:scale-[0.98] shadow-blue-500/20'
                    }
                `}
            >
                <div className="flex items-center justify-center gap-2 relative z-10">
                    {isRunning ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} fill="currentColor" />}
                    {isRunning ? 'RUNNING SIMULATION...' : 'START BACKTEST'}
                </div>
            </button>
        </div>
    );
};
