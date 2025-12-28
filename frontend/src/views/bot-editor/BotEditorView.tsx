import { useState } from 'react';
import { Card, CardContent } from '../../shared/components/Card';
import { useOrchestratorStore } from '../../orchestrator/store';
import { Save, ArrowLeft, Plus, Trash2, ArrowDown, Settings2, PlayCircle, StopCircle, ShieldAlert } from 'lucide-react';

// Mock Pipeline Nodes
const initialNodes = [
    { id: '1', type: 'trigger', title: 'Entry Trigger', desc: 'RSI < 30 (Oversold)', icon: PlayCircle },
    { id: '2', type: 'filter', title: 'Trend Filter', desc: 'Price > EMA(200)', icon: Settings2 },
    { id: '3', type: 'risk', title: 'Risk Management', desc: 'Stop Loss 2%, TP 5%', icon: ShieldAlert },
    { id: '4', type: 'action', title: 'Execution', desc: 'Market Buy Order', icon: StopCircle },
];

export default function BotEditorView() {
    const { setView, editingBotId, setEditingBotId } = useOrchestratorStore();
    const [nodes, setNodes] = useState(initialNodes);

    const handleBack = () => {
        setEditingBotId(null);
        setView('bot-config');
    };

    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6 max-w-3xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button onClick={handleBack} className="p-2 hover:bg-secondary rounded-full transition-colors">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            Pipeline Editor <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">v1.0</span>
                        </h1>
                        <p className="text-muted-foreground text-sm">Design your strategy logic flow</p>
                    </div>
                </div>
                <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md flex items-center gap-2 font-medium hover:bg-primary/90">
                    <Save size={16} /> Save Pipeline
                </button>
            </div>

            {/* Pipeline Canvas */}
            <div className="flex-1 overflow-y-auto pr-2 relative">
                {/* Central Line */}
                <div className="absolute left-[2rem] top-4 bottom-4 w-0.5 bg-border -z-10" />

                <div className="space-y-2">
                    {nodes.map((node, idx) => (
                        <div key={node.id} className="relative group">
                            {/* Node Connector (Visual) */}
                            {idx > 0 && (
                                <div className="absolute left-[2rem] -top-3 -translate-x-1/2 text-border bg-background p-0.5">
                                    <ArrowDown size={14} />
                                </div>
                            )}

                            <div className="flex items-start gap-4">
                                {/* Icon/Node Marker */}
                                <div className="w-16 h-16 flex-shrink-0 flex items-center justify-center bg-background border-2 border-primary/20 rounded-full z-10 hover:border-primary hover:shadow-[0_0_15px_rgba(var(--primary),0.3)] transition-all cursor-pointer">
                                    <node.icon size={24} className="text-primary" />
                                </div>

                                {/* Content Card */}
                                <Card className="flex-1 hover:border-primary/50 transition-colors group-hover:bg-secondary/5 cursor-pointer">
                                    <CardContent className="p-4 flex justify-between items-center">
                                        <div>
                                            <div className="text-xs uppercase font-bold text-muted-foreground mb-0.5">{node.type}</div>
                                            <div className="font-semibold text-lg">{node.title}</div>
                                            <div className="text-sm text-muted-foreground">{node.desc}</div>
                                        </div>
                                        <div className="opacity-0 group-hover:opacity-100 flex gap-2 transition-opacity">
                                            <button className="p-2 hover:bg-background rounded-md border border-transparent hover:border-border text-muted-foreground hover:text-foreground">
                                                <Settings2 size={16} />
                                            </button>
                                            <button className="p-2 hover:bg-red-500/10 rounded-md border border-transparent hover:border-red-500/20 text-muted-foreground hover:text-red-500">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Add Button (Inter-node) */}
                            <div className="h-8 flex items-center justify-start pl-[1.15rem] my-1 opacity-10 hover:opacity-100 transition-opacity">
                                <button className="w-7 h-7 rounded-full bg-secondary border border-border flex items-center justify-center hover:bg-primary hover:text-primary-foreground hover:scale-110 transition-all">
                                    <Plus size={14} />
                                </button>

                            </div>
                        </div>
                    ))}

                    {/* End Node */}
                    <div className="flex items-center gap-4 opacity-50">
                        <div className="w-16 h-16 flex items-center justify-center border-2 border-dashed border-muted rounded-full ml-0">
                            <div className="w-3 h-3 bg-muted rounded-full" />
                        </div>
                        <div className="text-sm text-muted-foreground italic">
                            End of Pipeline
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
