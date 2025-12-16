import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../shared/components/Card';
import { Badge } from '../../shared/components/Badge';
import { Shield, Key, Trash2, Plus, CheckCircle, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

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
    // --- State ---
    const [keys, setKeys] = useState<ExchangeKey[]>([]);
    const [isAdding, setIsAdding] = useState(false);
    const [newKeyForm, setNewKeyForm] = useState({ exchange: 'binance', label: '', pub: '', sec: '' });

    // --- Effects ---
    useEffect(() => {
        fetch(`${API_BASE}/keys`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch keys");
                return res.json();
            })
            .then(data => setKeys(data))
            .catch(err => console.error("Error loading keys:", err));
    }, []);

    // --- Handlers ---
    const handleAddKey = async () => {
        if (!newKeyForm.label || !newKeyForm.pub || !newKeyForm.sec) return;

        try {
            const res = await fetch(`${API_BASE}/keys`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exchange: newKeyForm.exchange,
                    label: newKeyForm.label,
                    publicKey: newKeyForm.pub,
                    secretKey: newKeyForm.sec
                })
            });

            if (res.ok) {
                const newKey: ExchangeKey = await res.json();
                setKeys([...keys, newKey]);
                setIsAdding(false);
                setNewKeyForm({ exchange: 'binance', label: '', pub: '', sec: '' });
            } else {
                console.error("Failed to add key");
                alert("Failed to add key");
            }
        } catch (e) {
            console.error(e);
            alert("Error adding key");
        }
    };

    const handleDeleteKey = async (id: string) => {
        if (!confirm("Are you sure you want to remove this connection?")) return;

        try {
            const res = await fetch(`${API_BASE}/keys/${id}`, { method: 'DELETE' });
            if (res.ok) {
                setKeys(keys.filter(k => k.id !== id));
            } else {
                alert("Failed to delete key");
            }
        } catch (e) {
            console.error(e);
        }
    };

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
                </div>
            </div>

            {/* Add Key Form */}
            {isAdding && (
                <Card className="animate-in fade-in slide-in-from-top-4 border-primary/20 bg-primary/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">New Connection</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                            <div className="md:col-span-2">
                                <label className="text-xs font-medium text-muted-foreground mb-1 block">Secret Key</label>
                                <input
                                    type="password"
                                    autoComplete="new-password"
                                    name="secret-key-field"
                                    className="w-full p-2 rounded-md border border-border bg-background text-sm font-mono"
                                    placeholder="Enter your Secret key"
                                    value={newKeyForm.sec}
                                    onChange={e => setNewKeyForm({ ...newKeyForm, sec: e.target.value })}
                                />
                                <p className="text-[10px] text-muted-foreground mt-1">
                                    * Secret Key is encrypted immediately upon submission and never stored in plain text.
                                </p>
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
                {keys.length === 0 && !isAdding && (
                    <div className="text-center p-12 border border-dashed border-border rounded-xl">
                        <Key className="mx-auto text-muted-foreground mb-2" />
                        <h3 className="text-lg font-medium">No Keys Found</h3>
                        <p className="text-muted-foreground text-sm">Add a connection to start trading</p>
                    </div>
                )}
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
