export interface BacktestResult {
    job_id: string;
    metrics: {
        total_pnl: number;
        cagr: number;
        mdd: number;
        sharpe_ratio: number;
        win_rate: number;
        profit_factor: number;
        alpha_gross: number;
        total_cost: number;
    };
    equity_curve: {
        timestamp: number;
        balance: number;
        buy_hold_price?: number;
    }[];
    cost_breakdown: {
        spread_cost: number;
        slippage_cost: number;
        commission: number;
        funding_fee: number;
    };
    trades: any[];
}

// Mock data updated to snake_case
export const mockBacktestResult: BacktestResult = {
    job_id: "job-123",
    metrics: {
        total_pnl: 3500,
        cagr: 45.2,
        mdd: -12.5,
        sharpe_ratio: 1.8,
        win_rate: 0.65,
        profit_factor: 2.1,
        alpha_gross: 4200,
        total_cost: 700
    },
    equity_curve: Array.from({ length: 30 }, (_, i) => ({
        timestamp: new Date(`2024-01-${i + 1}`).getTime(),
        balance: 10000 + (Math.random() * 500 * (i + 1)) - (Math.random() * 200 * i),
        buy_hold_price: 10000 + (Math.random() * 300 * (i + 1))
    })),
    cost_breakdown: {
        spread_cost: 200,
        slippage_cost: 300,
        commission: 150,
        funding_fee: 50
    },
    trades: []
};
