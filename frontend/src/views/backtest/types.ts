export interface BacktestResult {
    jobId: string;
    metrics: {
        totalPnl: number;
        cagr: number;
        mdd: number;
        sharpeRatio: number;
        winRate: number;
        profitFactor: number;
        alpha: number;
        totalCost: number;
    };
    equityCurve: {
        time: string;
        value: number;
        buyHoldValue?: number;
    }[];
    costBreakdown: {
        spread: number;
        slippage: number;
        fees: number;
        funding: number;
    };
    trades: any[];
}

export const mockBacktestResult: BacktestResult = {
    jobId: "job-123",
    metrics: {
        totalPnl: 3500,
        cagr: 45.2,
        mdd: -12.5,
        sharpeRatio: 1.8,
        winRate: 0.65,
        profitFactor: 2.1,
        alpha: 4200,
        totalCost: 700
    },
    equityCurve: Array.from({ length: 30 }, (_, i) => ({
        time: `2024-01-${i + 1}`,
        value: 10000 + (Math.random() * 500 * (i + 1)) - (Math.random() * 200 * i),
        buyHoldValue: 10000 + (Math.random() * 300 * (i + 1))
    })),
    costBreakdown: {
        spread: 200,
        slippage: 300,
        fees: 150,
        funding: 50
    },
    trades: []
};
