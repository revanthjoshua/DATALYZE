import React, { createContext, useContext, useState, useEffect } from 'react';

export type TimeRangeOption = '7D' | '14D' | '30D' | '90D' | 'ALL';

interface DateRangeContextType {
  timeRange: TimeRangeOption;
  setTimeRange: (range: TimeRangeOption) => void;
  getDaysCount: () => number;
}

const DateRangeContext = createContext<DateRangeContextType | undefined>(undefined);

export const DateRangeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [timeRange, setTimeRangeState] = useState<TimeRangeOption>(() => {
    return (localStorage.getItem('datalyze_global_timerange') as TimeRangeOption) || '30D';
  });

  const setTimeRange = (range: TimeRangeOption) => {
    setTimeRangeState(range);
    localStorage.setItem('datalyze_global_timerange', range);
  };

  const getDaysCount = (): number => {
    switch (timeRange) {
      case '7D':
        return 7;
      case '14D':
        return 14;
      case '30D':
        return 30;
      case '90D':
        return 90;
      case 'ALL':
      default:
        return 365;
    }
  };

  return (
    <DateRangeContext.Provider value={{ timeRange, setTimeRange, getDaysCount }}>
      {children}
    </DateRangeContext.Provider>
  );
};

export const useDateRange = (): DateRangeContextType => {
  const context = useContext(DateRangeContext);
  if (!context) {
    throw new Error('useDateRange must be used within a DateRangeProvider');
  }
  return context;
};
