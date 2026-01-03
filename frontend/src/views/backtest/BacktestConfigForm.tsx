import React from 'react';
import { Play, Loader2, Calendar, DollarSign, Settings2 } from 'lucide-react';

interface Props {
    onRun?: () => void;
    isRunning?: boolean;
}

export const BacktestConfigForm: React.FC<Props> = ({ onRun, isRunning = false }) => {
    return (
        <div className="flex flex-col gap-6">
            <div className="space-y-4">
                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <Calendar size={12} />
                        Period
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        <input
                            type="date"
                            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                            defaultValue="2024-01-01"
                        />
                        <input
                            type="date"
                            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                            defaultValue="2024-12-31"
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
                            defaultValue="10000"
                        />
                    </div>
                </div>

                <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                        <Settings2 size={12} />
                        Execution Model
                    </label>
                    <select className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all appearance-none cursor-pointer hover:border-gray-700">
                        <option>B-Book Simulator (No Slippage)</option>
                        <option>Live Market (Standard Slippage)</option>
                        <option>Stress Test (High Slippage)</option>
                    </select>
                </div>
            </div>

            <button
                onClick={onRun}
                disabled={isRunning}
                className={`
                    w-full relative overflow-hidden rounded-xl font-bold py-3 text-sm tracking-wide shadow-lg transition-all
                    ${isRunning
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
