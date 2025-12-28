import axios from 'axios';

// --- Type Definitions (aligned with Schema) ---

export interface StrategyDefinition {
    id: string;
    name: string;
    description: string;
    version: string;
    schema: any; // JSON Schema object
}

export interface BotConfig {
    id?: string;
    name: string;
    status: 'STOPPED' | 'RUNNING' | 'PAUSED' | 'ERROR';
    global_settings: {
        exchange: string;
        symbol: string;
        mode: 'REAL' | 'PAPER' | 'BACKTEST';
        account_allocation?: string | number;
    };
    pipeline: {
        strategy: {
            id: string;
            params: Record<string, any>;
        };
        [key: string]: any; // Other pipeline steps
    };
}

// --- API Client ---

// In real app, these base URLs specific to docker-compose networking or reverse proxy
const BOT_SERVICE_URL = '/api/bots'; // Assuming Nginx proxy setup or direct call
const STRATEGY_SERVICE_URL = '/api/strategies';

export interface ExchangeCredential {
    id: string;
    exchange: string;
    label: string;
    publicKey: string;
}

export const BotService = {
    async getExchanges(): Promise<ExchangeCredential[]> {
        try {
            const res = await axios.get('/api/keys');
            // The auth service returns list of keys (credentials)
            return res.data;
        } catch (e) {
            console.warn("Failed to fetch keys", e);
            return [];
        }
    },

    async getStrategies(): Promise<StrategyDefinition[]> {
        try {
            // Use relative path to go through Nginx proxy
            const res = await axios.get('/api/strategies');
            return res.data;
        } catch (e) {
            console.warn("Using Mock Strategies due to API error", e);
            // Fallback for demo if backend isn't ready
            return [
                {
                    id: "grid_v1",
                    name: "Mock Grid",
                    description: "Mock",
                    version: "1",
                    schema: {
                        type: "object",
                        properties: {
                            grid_count: { type: "integer", title: "Grid Count", default: 10 },
                            upper_price: { type: "number", title: "Upper Price" },
                            lower_price: { type: "number", title: "Lower Price" }
                        }
                    }
                }
            ];
        }
    },

    async getAllBots(): Promise<BotConfig[]> {
        try {
            const res = await axios.get('/api/bots');
            return res.data;
        } catch (e) {
            console.warn("Failed to fetch bots list", e);
            return [];
        }
    },

    async getBot(id: string): Promise<BotConfig> {
        const res = await axios.get(`/api/bots/${id}`);
        return res.data;
    },

    async createBot(bot: BotConfig): Promise<BotConfig> {
        const res = await axios.post('/api/bots', bot);
        return res.data;
    },

    async updateBot(id: string, bot: BotConfig): Promise<BotConfig> {
        const res = await axios.put(`/api/bots/${id}`, bot);
        return res.data;
    }
};
