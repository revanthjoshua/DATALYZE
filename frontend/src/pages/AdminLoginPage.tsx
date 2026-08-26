import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Lock,
  User,
  AlertCircle,
  Eye,
  EyeOff,
  ArrowRight,
  UserCheck,
  UserPlus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FormField, Input } from '../components/ui/FormField';

export const AdminLoginPage: React.FC = () => {
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
      errors.identifier = 'Administrator Email or Username is required.';
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
        portal_type: 'admin',
      });
      toast.success(`Welcome back, ${user.full_name}. Admin privileges active.`, 'Administrator Authenticated');
      navigate('/admin/dashboard');
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        'Failed to authenticate administrator. Please check your credentials or reset your password.';
      setError(msg);
      toast.error(msg, 'Authentication Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] shadow-xs mb-2 text-white font-extrabold text-xl">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] border border-[#6B4226]/20">
            Admin Portal
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Admin Sign In
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          Enterprise workspace management, settings, team access, and analytics controls
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-5 border-t-4 border-t-[#6B4226]">
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
                placeholder="admin@datalyze.com or admin"
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

            <div className="flex items-center justify-between text-xs">
              <span className="text-[11px] text-neutral-400">
                Demo: <code className="font-mono text-neutral-700 dark:text-neutral-300">admin</code> / <code className="font-mono text-neutral-700 dark:text-neutral-300">Admin123!</code>
              </span>
              <Link
                to="/forgot-password/admin"
                className="text-[#6B4226] dark:text-[#8C5E3C] hover:underline font-semibold cursor-pointer shrink-0 ml-2"
              >
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In as Administrator
            </Button>
          </form>

          {/* Sign Up as Admin option */}
          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex flex-col items-center space-y-2.5 text-xs">
            <Link
              to="/register/admin"
              className="font-bold text-[#6B4226] dark:text-[#D5B79F] hover:underline flex items-center space-x-1"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Need an Admin account? <strong>Sign Up / Register as Admin →</strong></span>
            </Link>

            <Link
              to="/login/employee"
              className="font-medium text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 flex items-center space-x-1 transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5 text-blue-500" />
              <span>Are you an Employee? <strong>Sign In to Employee Portal →</strong></span>
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
