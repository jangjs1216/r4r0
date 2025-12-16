import { useState } from 'react';
import { useOrchestratorStore } from '../../orchestrator/store';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Shield, Key, Trash2, Plus, CheckCircle, AlertCircle, LogOut } from 'lucide-react';

// Mock Data Types based on schema
interface ExchangeKey {
    id: string;
    exchange: 'binance' | 'upbit' | 'okx' | 'bybit';
    label: string;
    publicKeyMasked: string;
    status: 'active' | 'expired' | 'invalid';
    permissions: string[];
    createdAt: string;
}

export default function AuthView() {
    const { isAuthenticated, setAuthenticated, setView } = useOrchestratorStore();

    // --- State ---
    const [keys, setKeys] = useState<ExchangeKey[]>([
        {
            id: 'k1', exchange: 'binance', label: 'Main Trading',
            publicKeyMasked: 'vmPU...9d2A', status: 'active',
            permissions: ['read', 'trade'], createdAt: '2025-11-10T10:00:00Z'
        },
        {
            id: 'k2', exchange: 'upbit', label: 'Backup Account',
            publicKeyMasked: 'Wz9L...k8s2', status: 'expired',
            permissions: ['read'], createdAt: '2025-01-15T09:30:00Z'
        }
    ]);
    const [isAdding, setIsAdding] = useState(false);
    const [newKeyForm, setNewKeyForm] = useState({ exchange: 'binance', label: '', pub: '', sec: '' });

    // --- Handlers ---
    const handleLogin = () => {
        setAuthenticated(true);
        // We stay on this view to let user manage keys, or redirect?
        // Usually login -> dashboard. But if user clicks 'Auth' tab later, they see Key Mgr.
        // For first login, let's redirect to dashboard.
        setView('dashboard');
    };

    const handleAddKey = () => {
        if (!newKeyForm.label || !newKeyForm.pub) return;
        const newKey: ExchangeKey = {
            id: Math.random().toString(36).substr(2, 9),
            exchange: newKeyForm.exchange as any,
            label: newKeyForm.label,
            publicKeyMasked: newKeyForm.pub.substring(0, 4) + '...' + newKeyForm.pub.substring(newKeyForm.pub.length - 4),
            status: 'active',
            permissions: ['read', 'trade'],
            createdAt: new Date().toISOString()
        };
        setKeys([...keys, newKey]);
        setIsAdding(false);
        setNewKeyForm({ exchange: 'binance', label: '', pub: '', sec: '' });
    };

    const handleDeleteKey = (id: string) => {
        setKeys(keys.filter(k => k.id !== id));
    };

    // --- Render: Login Screen ---
    if (!isAuthenticated) {
        return (
            <div className="p-6 flex items-center justify-center h-full min-h-[calc(100vh-4rem)]">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center space-y-2">
                        <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Shield size={32} />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight">Welcome Back</h2>
                        <p className="text-muted-foreground">Sign in to access your trading bots</p>
                    </div>

                    <Card className="border-border/50 shadow-lg bg-card/50 backdrop-blur">
                        <CardContent className="pt-6 space-y-4">
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground ml-1">EMAIL</label>
                                <input
                                    type="email"
                                    className="w-full px-4 py-3 bg-secondary/30 rounded-lg border border-border/50 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                    placeholder="trader@example.com"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground ml-1">PASSWORD</label>
                                <input
                                    type="password"
                                    className="w-full px-4 py-3 bg-secondary/30 rounded-lg border border-border/50 focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                            <button
                                onClick={handleLogin}
                                className="w-full py-3 bg-primary text-primary-foreground font-bold rounded-lg hover:bg-primary/90 transition-all shadow-[0_4px_12px_rgba(0,0,0,0.1)] active:scale-[0.98]"
                            >
                                Sign In
                            </button>

                            <div className="relative my-4">
                                <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border/50"></span></div>
                                <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">Or</span></div>
                            </div>

                            <div className="text-center text-xs text-muted-foreground">
                                <p>Mock Mode: Auto-login enabled</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // --- Render: Key Management Hub ---
    return (
        <div className="p-6 h-[calc(100vh-4rem)] flex flex-col gap-6 max-w-5xl mx-auto w-full">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <Key className="text-primary" size={24} />
                        Key Management
                    </h2>
                    <p className="text-muted-foreground">Manage your exchange connections securely</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setIsAdding(!isAdding)}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm font-medium transition-colors"
                    >
                        <Plus size={16} />
                        Add Connection
                    </button>
                    {/* Sign Out removed as per requirement */}
                </div>
            </div>

            {/* Add Key Form */}
            {isAdding && (
                <Card className="animate-in fade-in slide-in-from-top-4 border-primary/20 bg-primary/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">New Connection</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-1 block">Exchange</label>
                                <select
                                    className="w-full p-2 rounded-md border border-border bg-background text-sm"
                                    value={newKeyForm.exchange}
                                    onChange={e => setNewKeyForm({ ...newKeyForm, exchange: e.target.value })}
                                >
                                    <option value="binance">Binance</option>
                                    <option value="upbit">Upbit</option>
                                    <option value="okx">OKX</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-1 block">Label</label>
                                <input
                                    type="text"
                                    className="w-full p-2 rounded-md border border-border bg-background text-sm"
                                    placeholder="My Account"
                                    value={newKeyForm.label}
                                    onChange={e => setNewKeyForm({ ...newKeyForm, label: e.target.value })}
                                />
                            </div>
                            <div className="md:col-span-2">
                                <label className="text-xs font-medium text-muted-foreground mb-1 block">API Key (Public)</label>
                                <input
                                    type="text"
                                    className="w-full p-2 rounded-md border border-border bg-background text-sm"
                                    placeholder="Enter your API key"
                                    value={newKeyForm.pub}
                                    onChange={e => setNewKeyForm({ ...newKeyForm, pub: e.target.value })}
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setIsAdding(false)} className="px-3 py-1.5 text-xs font-medium hover:bg-secondary rounded-md">Cancel</button>
                            <button onClick={handleAddKey} className="px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md">Save Connection</button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Key List */}
            <div className="grid gap-4">
                {keys.map(key => (
                    <Card key={key.id} className="group hover:border-primary/50 transition-colors">
                        <CardContent className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center text-lg font-bold text-muted-foreground">
                                    {key.exchange[0].toUpperCase()}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-bold">{key.label}</h3>
                                        <Badge variant="outline" className="text-[10px] uppercase">{key.exchange}</Badge>
                                        {key.status === 'active'
                                            ? <CheckCircle size={14} className="text-emerald-500" />
                                            : <AlertCircle size={14} className="text-yellow-500" />
                                        }
                                    </div>
                                    <div className="text-sm font-mono text-muted-foreground mt-0.5">
                                        {key.publicKeyMasked}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end">
                                <div className="flex gap-2">
                                    {key.permissions.map(p => (
                                        <Badge key={p} variant="secondary" className="text-xs capitalize">{p}</Badge>
                                    ))}
                                </div>

                                <div className="h-8 w-px bg-border hidden md:block"></div>

                                <button
                                    onClick={() => handleDeleteKey(key.id)}
                                    className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                                    title="Remove Connection"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="mt-auto bg-blue-500/5 border border-blue-500/20 rounded-lg p-4 flex gap-3 text-sm text-blue-400">
                <Shield size={20} className="shrink-0" />
                <p>
                    Your keys are encrypted using AES-256 before being stored.
                    We never display the private key again after initial registration.
                    Enable IP Whistlisting on your exchange for maximum security.
                </p>
            </div>
        </div>
    );
}
