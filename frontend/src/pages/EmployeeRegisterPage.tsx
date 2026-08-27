import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UserCheck,
  User,
  Phone,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  Building2,
  AtSign,
} from 'lucide-react';
import { authApi } from '../api/authApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FormField, Input } from '../components/ui/FormField';

export const EmployeeRegisterPage: React.FC = () => {
  const toast = useToast();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    email: '',
    username: '',
    company_name: '',
    password: '',
    confirm_password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formData.full_name.trim()) errs.full_name = 'Full name is required.';
    
    const phoneClean = formData.phone_number.trim().replace(/[\s-]/g, '');
    if (!phoneClean) {
      errs.phone_number = 'Phone number is required.';
    } else if (phoneClean.length < 7) {
      errs.phone_number = 'Please enter a valid phone number.';
    }

    if (!formData.email.trim()) {
      errs.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errs.email = 'Please enter a valid email address.';
    }

    if (!formData.username.trim()) {
      errs.username = 'Username is required.';
    } else if (!/^[a-zA-Z0-9_.-]{3,30}$/.test(formData.username.trim())) {
      errs.username = 'Username must be 3-30 chars (letters, numbers, _, -, .).';
    }

    if (!formData.password) {
      errs.password = 'Password is required.';
    } else if (formData.password.length < 6) {
      errs.password = 'Password must be at least 6 characters.';
    }

    if (!formData.confirm_password) {
      errs.confirm_password = 'Confirm password is required.';
    } else if (formData.password !== formData.confirm_password) {
      errs.confirm_password = 'Passwords do not match.';
    }

    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setError(null);
    setLoading(true);

    try {
      await authApi.registerEmployee({
        full_name: formData.full_name.trim(),
        phone_number: formData.phone_number.trim(),
        email: formData.email.trim().toLowerCase(),
        username: formData.username.trim().toLowerCase(),
        company_name: formData.company_name.trim() || undefined,
        password: formData.password,
        confirm_password: formData.confirm_password,
      });

      toast.success('Employee account created successfully! Please sign in with your credentials.', 'Registration Complete');
      navigate('/login/employee');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to register employee account. Please check your details.';
      setError(msg);
      toast.error(msg, 'Registration Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-blue-600 dark:bg-blue-700 shadow-xs mb-1 text-white font-extrabold text-xl">
          <UserCheck className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Employee Portal Registration
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Create Employee Account
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          Join your company workspace to access daily metrics, actionable tasks, alerts, and stock intelligence
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-5 border-t-4 border-t-blue-600">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center space-x-2 text-red-600 dark:text-red-400 text-xs animate-fade-in font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Full Name" required error={fieldErrors.full_name}>
                <Input
                  type="text"
                  required
                  leftIcon={<User className="w-4 h-4" />}
                  value={formData.full_name}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, full_name: e.target.value }));
                    if (fieldErrors.full_name) setFieldErrors((p) => ({ ...p, full_name: '' }));
                  }}
                  placeholder="e.g. Jordan Reed"
                />
              </FormField>

              <FormField label="Phone Number" required error={fieldErrors.phone_number}>
                <Input
                  type="tel"
                  required
                  leftIcon={<Phone className="w-4 h-4" />}
                  value={formData.phone_number}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, phone_number: e.target.value }));
                    if (fieldErrors.phone_number) setFieldErrors((p) => ({ ...p, phone_number: '' }));
                  }}
                  placeholder="+1 (555) 098-7654"
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Email Address" required error={fieldErrors.email}>
                <Input
                  type="email"
                  required
                  leftIcon={<Mail className="w-4 h-4" />}
                  value={formData.email}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, email: e.target.value }));
                    if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: '' }));
                  }}
                  placeholder="employee@company.com"
                />
              </FormField>

              <FormField label="Username" required error={fieldErrors.username}>
                <Input
                  type="text"
                  required
                  leftIcon={<AtSign className="w-4 h-4" />}
                  value={formData.username}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, username: e.target.value }));
                    if (fieldErrors.username) setFieldErrors((p) => ({ ...p, username: '' }));
                  }}
                  placeholder="jordan_reed"
                />
              </FormField>
            </div>

            <FormField 
              label="Company / Workspace Name" 
              helperText="Enter your company workspace name or leave blank if using company domain email"
            >
              <Input
                type="text"
                leftIcon={<Building2 className="w-4 h-4" />}
                value={formData.company_name}
                onChange={(e) => {
                  setFormData((p) => ({ ...p, company_name: e.target.value }));
                }}
                placeholder="e.g. Apex Analytics (Optional)"
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Password" required error={fieldErrors.password}>
                <Input
                  type={showPassword ? 'text' : 'password'}
                  required
                  leftIcon={<Lock className="w-4 h-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  }
                  value={formData.password}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, password: e.target.value }));
                    if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: '' }));
                  }}
                  placeholder="Min 6 characters"
                />
              </FormField>

              <FormField label="Confirm Password" required error={fieldErrors.confirm_password}>
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  leftIcon={<Lock className="w-4 h-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  }
                  value={formData.confirm_password}
                  onChange={(e) => {
                    setFormData((p) => ({ ...p, confirm_password: e.target.value }));
                    if (fieldErrors.confirm_password) setFieldErrors((p) => ({ ...p, confirm_password: '' }));
                  }}
                  placeholder="Re-enter password"
                />
              </FormField>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full mt-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Join Workspace as Employee
            </Button>
          </form>

          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex flex-col items-center space-y-2 text-xs">
            <span className="text-neutral-500">
              Already have an Employee account?{' '}
              <Link to="/login/employee" className="font-bold text-blue-600 dark:text-blue-400 hover:underline">
                Sign In as Employee →
              </Link>
            </span>

            <Link to="/login" className="text-[11px] text-neutral-400 hover:underline">
              ← Back to Portal Selection
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
