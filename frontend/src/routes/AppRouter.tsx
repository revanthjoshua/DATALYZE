import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AppLayout } from '../components/layout/AppLayout';
import { LoginPage } from '../pages/LoginPage';
import { AdminLoginPage } from '../pages/AdminLoginPage';
import { EmployeeLoginPage } from '../pages/EmployeeLoginPage';
import { AdminRegisterPage } from '../pages/AdminRegisterPage';
import { EmployeeRegisterPage } from '../pages/EmployeeRegisterPage';
import { AdminForgotPasswordPage } from '../pages/AdminForgotPasswordPage';
import { EmployeeForgotPasswordPage } from '../pages/EmployeeForgotPasswordPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { EmployeeDashboardPage } from '../pages/EmployeeDashboardPage';
import { KpisPage } from '../pages/KpisPage';
import { KpiDetailPage } from '../pages/KpiDetailPage';
import { DataPage } from '../pages/DataPage';
import { CompanySettingsPage } from '../pages/CompanySettingsPage';
import { AccountPage } from '../pages/AccountPage';
import { PredictionsPage } from '../pages/PredictionsPage';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { AlertsPage } from '../pages/AlertsPage';
import { ReportsPage } from '../pages/ReportsPage';
import { SmartInventoryPage } from '../pages/SmartInventoryPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, token, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex items-center justify-center text-[#6B4226] font-mono text-sm">
        Initializing Datalyze Workspace...
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, user, loading } = useAuth();

  if (loading) return null;

  if (token && user) {
    const isEmployee = (user.role || '').toLowerCase() === 'employee';
    return <Navigate to={isEmployee ? '/employee/dashboard' : '/admin/dashboard'} replace />;
  }

  return <>{children}</>;
};

const RootDashboardRoute: React.FC = () => {
  const { user } = useAuth();
  const isEmployee = (user?.role || '').toLowerCase() === 'employee';
  return isEmployee ? <EmployeeDashboardPage /> : <DashboardPage />;
};

const AdminDashboardRoute: React.FC = () => {
  const { user } = useAuth();
  const isEmployee = (user?.role || '').toLowerCase() === 'employee';
  if (isEmployee) {
    return <Navigate to="/employee/dashboard" replace />;
  }
  return <DashboardPage />;
};

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        {/* Public Portal Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/login/admin"
          element={
            <PublicRoute>
              <AdminLoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/login/employee"
          element={
            <PublicRoute>
              <EmployeeLoginPage />
            </PublicRoute>
          }
        />

        {/* Separate Registration Routes */}
        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />
        <Route
          path="/register/admin"
          element={
            <PublicRoute>
              <AdminRegisterPage />
            </PublicRoute>
          }
        />
        <Route
          path="/register/employee"
          element={
            <PublicRoute>
              <EmployeeRegisterPage />
            </PublicRoute>
          }
        />

        {/* Separate Forgot Password Routes */}
        <Route
          path="/forgot-password/admin"
          element={
            <PublicRoute>
              <AdminForgotPasswordPage />
            </PublicRoute>
          }
        />
        <Route
          path="/forgot-password/employee"
          element={
            <PublicRoute>
              <EmployeeForgotPasswordPage />
            </PublicRoute>
          }
        />

        {/* Protected App Routes */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Main Dashboard Router */}
          <Route path="/" element={<RootDashboardRoute />} />
          <Route path="/admin/dashboard" element={<AdminDashboardRoute />} />
          <Route path="/employee/dashboard" element={<EmployeeDashboardPage />} />

          <Route path="/kpis" element={<KpisPage />} />
          <Route path="/kpi" element={<Navigate to="/kpis" replace />} />
          <Route path="/metrics" element={<Navigate to="/kpis" replace />} />
          <Route path="/kpis/:kpiId" element={<KpiDetailPage />} />
          <Route path="/kpi/:kpiId" element={<KpiDetailPage />} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/pipeline" element={<Navigate to="/data" replace />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/inventory" element={<SmartInventoryPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/detections" element={<Navigate to="/alerts" replace />} />
          <Route path="/anomaly-alerts" element={<Navigate to="/alerts" replace />} />
          <Route path="/reports" element={<ReportsPage />} />
          
          {/* Consolidated Settings & Account Pages */}
          <Route path="/settings" element={<CompanySettingsPage />} />
          <Route path="/company" element={<Navigate to="/settings" replace />} />
          <Route path="/company-profile" element={<Navigate to="/settings" replace />} />
          
          <Route path="/account" element={<AccountPage />} />
          <Route path="/profile" element={<Navigate to="/account" replace />} />
          <Route path="/user-profile" element={<Navigate to="/account" replace />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
