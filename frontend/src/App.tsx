import React from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { TenantProvider } from './context/TenantContext';
import { ToastProvider } from './context/ToastContext';
import { DateRangeProvider } from './context/DateRangeContext';
import { AppRouter } from './routes/AppRouter';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <TenantProvider>
          <DateRangeProvider>
            <ToastProvider>
              <AppRouter />
            </ToastProvider>
          </DateRangeProvider>
        </TenantProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
