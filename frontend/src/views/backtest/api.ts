import axios from 'axios';
import type { BotConfig } from '../bot-editor/api';
import type { BacktestResult } from './types';

export interface RunBacktestRequest {
    bot_config: BotConfig;
    time_range: {
        start_date: string; // ISO 8601
        end_date: string;   // ISO 8601
    };
    initial_capital: number;
    slippage_model: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
}

export type BacktestResponse = BacktestResult;

export const BacktestAPI = {
    async runBacktest(request: RunBacktestRequest): Promise<BacktestResponse> {
        // The rewrites in nginx: /api/backtest/run -> http://backtest-service:8000/run
        const res = await axios.post('/api/backtest/run', request);
        return res.data;
    }
};
