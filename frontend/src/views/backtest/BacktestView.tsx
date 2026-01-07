import React, { useState } from 'react';
import { BacktestConfigForm } from './BacktestConfigForm';
import { mockBacktestResult } from './types';
import { BacktestResultDashboard } from './BacktestResultDashboard';
import { ArrowLeftIcon } from '@heroicons/react/24/solid';
import { useOrchestratorStore } from '../../orchestrator/store';
import { FlaskConical } from 'lucide-react';
import type { BacktestResponse } from './api';

export const BacktestView: React.FC = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [result, setResult] = useState<any>(mockBacktestResult); // Initialize with mock or null
    const { setView } = useOrchestratorStore();

    const handleRunComplete = (data: BacktestResponse) => {
        // Data is already in correct format (snake_case) matching types.ts
        setResult(data);
    };

    return (
        <div className="flex flex-col h-screen bg-black text-gray-100 overflow-hidden font-sans selection:bg-blue-500/30">
            {/* Header / Toolbar */}
            <div className="h-14 border-b border-gray-800/80 flex items-center px-4 justify-between bg-black/50 backdrop-blur-xl z-20">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setView('bot-editor')}
                        className="group p-2 hover:bg-gray-800 rounded-full text-gray-400 transition-all hover:text-white"
                        title="Return to Editor"
                    >
                        <ArrowLeftIcon className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-blue-500/10 rounded-lg">
                            <FlaskConical className="w-5 h-5 text-blue-500" />
                        </div>
                        <h1 className="font-bold text-lg tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-gray-100 to-gray-400">
                            Backtest Lab
                        </h1>
                    </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 rounded-full border border-gray-800">
                        <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`} />
                        <span className="text-xs font-mono text-gray-400">
                            {isRunning ? 'SIMULATION RUNNING...' : 'SYSTEM READY'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-grow flex overflow-hidden relative">

                {/* Background Grid Pattern */}
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-5 pointer-events-none"></div>

                {/* Left Config Panel */}
                <div className="w-96 border-r border-gray-800/80 p-0 bg-gray-950/30 backdrop-blur-sm overflow-y-auto flex flex-col z-10">
                    <div className="p-6 space-y-8">
                        <div>
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Configuration</h3>
                            <BacktestConfigForm
                                onRun={handleRunComplete}
                                isRunning={isRunning}
                                setIsRunning={setIsRunning}
                            />
                        </div>

                        {/* History Section */}
                        <div>
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Run History</h3>
                            <div className="space-y-2">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="group flex items-center justify-between p-3 rounded-xl bg-gray-900/40 border border-gray-800/50 hover:bg-gray-800 hover:border-gray-700 cursor-pointer transition-all">
                                        <div>
                                            <div className="text-sm font-medium text-gray-300 group-hover:text-white">Grid Experiment #{i}</div>
                                            <div className="text-xs text-gray-600">2 mins ago</div>
                                        </div>
                                        <div className={`text-xs font-mono font-bold ${i === 1 ? 'text-green-400' : 'text-gray-500'}`}>
                                            {i === 1 ? '+12.5%' : '-1.2%'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Result Panel */}
                <div className="flex-grow p-8 overflow-y-auto bg-gradient-to-b from-gray-950 to-black z-0">
                    <div className="max-w-7xl mx-auto">
                        <BacktestResultDashboard result={result} />
                    </div>
                </div>
            </div>
        </div>
    );
};

