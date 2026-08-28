import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UserCheck,
  Lock,
  User,
  AlertCircle,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  UserPlus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FormField, Input } from '../components/ui/FormField';

export const EmployeeLoginPage: React.FC = () => {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!identifier.trim()) {
      errors.identifier = 'Employee Email or Username is required.';
    }
    if (!password.trim()) {
      errors.password = 'Password is required.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setError(null);
    setLoading(true);

    try {
      const user = await login({
        identifier: identifier.trim(),
        password: password.trim(),
        portal_type: 'employee',
      });
      toast.success(`Welcome, ${user.full_name}. Employee workspace active.`, 'Employee Authenticated');
      navigate('/employee/dashboard');
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        'Failed to authenticate employee. Please check your credentials or reset your password.';
      setError(msg);
      toast.error(msg, 'Authentication Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-blue-600 dark:bg-blue-700 shadow-xs mb-2 text-white font-extrabold text-xl">
          <UserCheck className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Employee Portal
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Employee Sign In
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          Access operational telemetry, execute assigned action items, monitor anomaly alerts, and stock data
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-5 border-t-4 border-t-blue-600">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center space-x-2 text-red-600 dark:text-red-400 text-xs animate-fade-in font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <FormField label="Email or Username" required error={fieldErrors.identifier}>
              <Input
                type="text"
                autoComplete="username"
                hasError={!!fieldErrors.identifier}
                leftIcon={<User className="w-4 h-4" />}
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  if (fieldErrors.identifier) setFieldErrors((p) => ({ ...p, identifier: '' }));
                }}
                placeholder="employee@company.com or username"
              />
            </FormField>

            <FormField label="Password" required error={fieldErrors.password}>
              <Input
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                hasError={!!fieldErrors.password}
                leftIcon={<Lock className="w-4 h-4" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: '' }));
                }}
                placeholder="••••••••"
              />
            </FormField>

            <div className="flex items-center justify-end text-xs">
              <Link
                to="/forgot-password/employee"
                className="text-blue-600 dark:text-blue-400 hover:underline font-semibold cursor-pointer shrink-0"
              >
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In as Employee
            </Button>
          </form>

          {/* Employee invitation info */}
          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex flex-col items-center space-y-2.5 text-xs">
            <p className="text-neutral-500 dark:text-neutral-400 text-center">
              New team member? Employees join via team invitation links sent by their workspace administrator.
            </p>

            <Link
              to="/login/admin"
              className="font-medium text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 flex items-center space-x-1 transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#D5B79F]" />
              <span>Need workspace administration? <strong>Sign In to Admin Portal →</strong></span>
            </Link>

            <Link
              to="/login"
              className="text-[11px] text-neutral-400 hover:underline pt-1"
            >
              ← Back to Portal Selection
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
