import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Lock,
  Mail,
  Building,
  User as UserIcon,
  AlertCircle,
  Eye,
  EyeOff,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FormField, Input, Select } from '../components/ui/FormField';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('Retail/E-commerce');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Form Validation Errors
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const industries = [
    { value: 'Retail/E-commerce', label: 'Retail & E-commerce (Revenue, Orders, AOV, Conversion)' },
    { value: 'SaaS/Software', label: 'SaaS & Cloud Software (MRR, ARR, Churn Rate, CAC, NPS)' },
    { value: 'Restaurants/F&B', label: 'Restaurants & Food Services (Food Sales, Covers, Table Turn, Avg Ticket)' },
    { value: 'Healthcare/MedTech', label: 'Healthcare & Pharmaceuticals (Patient Encounters, Occupancy, Unit Cost)' },
    { value: 'Manufacturing/Supply Chain', label: 'Manufacturing & Industrial (OEE, Output, Defect Rate, Downtime)' },
    { value: 'Supply Chain/Logistics', label: 'Supply Chain & Logistics (Fulfillment SLA, Stockout, Capacity)' },
    { value: 'FinTech/Finance', label: 'Banking & FinTech (TPV, Transaction Count, Take Rate, Fraud BPS)' },
    { value: 'Hospitality/Travel', label: 'Hospitality & Tourism (RevPAR, Occupancy, ADR, Direct Bookings)' },
    { value: 'Education/EdTech', label: 'Education & EdTech (Active Learners, Completion, Retention)' },
    { value: 'Real Estate/PropTech', label: 'Real Estate & Construction (Occupancy, NOI, Days on Market)' },
    { value: 'Automotive/Mobility', label: 'Automotive & Mobility (Deliveries, Service Rev, Inventory Days)' },
    { value: 'Energy & Utilities', label: 'Energy, Oil & Utilities (Generation MWh, Grid Efficiency, Outages)' },
    { value: 'Professional Services/Consulting', label: 'Professional Services & Consulting (Utilization, Billables, Margins)' },
    { value: 'General Enterprise', label: 'General Enterprise (Cross-departmental KPIs & Operations)' },
  ];

  // Calculate Password Strength Score (0 to 4)
  const getPasswordStrength = () => {
    if (!password) return 0;
    let score = 0;
    if (password.length >= 6) score += 1;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
    if (/[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password)) score += 1;
    return score;
  };

  const strengthScore = getPasswordStrength();
  const strengthLabels = ['Too Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-neutral-300', 'bg-red-500', 'bg-amber-500', 'bg-blue-500', 'bg-emerald-500'];

  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!fullName.trim()) errors.fullName = 'Full name is required.';
    if (!companyName.trim()) errors.companyName = 'Company name is required.';
    if (!email.trim()) {
      errors.email = 'Work email is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!password.trim()) {
      errors.password = 'Password is required.';
    } else if (password.length < 4) {
      errors.password = 'Password must be at least 4 characters.';
    }
    if (!confirmPassword.trim()) {
      errors.confirmPassword = 'Confirm password is required.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
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
      await register({
        full_name: fullName.trim(),
        company_name: companyName.trim(),
        industry,
        email: email.trim().toLowerCase(),
        password: password.trim(),
      });
      toast.success('Company workspace created! Initializing intelligence template...', 'Welcome to DATALYZE');
      navigate('/');
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        'Registration failed. Please check your details or sign in if you already have an account.';
      setError(msg);
      toast.error(msg, 'Registration Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] shadow-xs mb-2 text-white font-extrabold text-xl">
          D
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Create Company Workspace
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          Automated KPI telemetry, plain-language Noah AI, and multi-tenant data isolation
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex flex-col space-y-1 text-red-600 dark:text-red-400 text-xs animate-fade-in font-medium">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
              <div className="pl-6 pt-0.5">
                <Link to="/login" className="font-semibold underline">
                  Go to Sign In →
                </Link>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Your Full Name" required error={fieldErrors.fullName}>
                <Input
                  type="text"
                  hasError={!!fieldErrors.fullName}
                  leftIcon={<UserIcon className="w-4 h-4" />}
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (fieldErrors.fullName) setFieldErrors((p) => ({ ...p, fullName: '' }));
                  }}
                  placeholder="e.g. Alex Morgan"
                />
              </FormField>

              <FormField label="Company Name" required error={fieldErrors.companyName}>
                <Input
                  type="text"
                  hasError={!!fieldErrors.companyName}
                  leftIcon={<Building className="w-4 h-4" />}
                  value={companyName}
                  onChange={(e) => {
                    setCompanyName(e.target.value);
                    if (fieldErrors.companyName) setFieldErrors((p) => ({ ...p, companyName: '' }));
                  }}
                  placeholder="e.g. Acme Corporation"
                />
              </FormField>
            </div>

            <FormField
              label="Primary Business Sector / Industry"
              helperText="Pre-configures domain metrics, benchmarks, and Noah intelligence rules"
            >
              <Select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="font-medium text-xs"
              >
                {industries.map((ind) => (
                  <option key={ind.value} value={ind.value}>
                    {ind.label}
                  </option>
                ))}
              </Select>
            </FormField>

            <FormField label="Work Email Address" required error={fieldErrors.email}>
              <Input
                type="email"
                hasError={!!fieldErrors.email}
                leftIcon={<Mail className="w-4 h-4" />}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: '' }));
                }}
                placeholder="name@company.com"
                autoComplete="email"
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <FormField label="Password" required error={fieldErrors.password}>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      hasError={!!fieldErrors.password}
                      leftIcon={<Lock className="w-4 h-4" />}
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: '' }));
                      }}
                      placeholder="••••••••"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </FormField>

                {/* Password Strength Indicator */}
                {password && (
                  <div className="mt-1.5 space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-neutral-400">Strength:</span>
                      <span className="font-semibold text-neutral-700 dark:text-neutral-300">
                        {strengthLabels[strengthScore]}
                      </span>
                    </div>
                    <div className="w-full bg-neutral-200 dark:bg-neutral-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${strengthColors[strengthScore]} transition-all duration-300`}
                        style={{ width: `${(strengthScore / 4) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <FormField label="Confirm Password" required error={fieldErrors.confirmPassword}>
                <div className="relative">
                  <Input
                    type={showConfirmPassword ? 'text' : 'password'}
                    hasError={!!fieldErrors.confirmPassword}
                    leftIcon={<Lock className="w-4 h-4" />}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (fieldErrors.confirmPassword) setFieldErrors((p) => ({ ...p, confirmPassword: '' }));
                    }}
                    placeholder="••••••••"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </FormField>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full mt-2"
              isLoading={loading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Create Workspace & Continue
            </Button>
          </form>

          <div className="text-center pt-2">
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Already have an enterprise account?{' '}
              <Link
                to="/login"
                className="font-bold text-[#6B4226] dark:text-[#D5B79F] hover:underline"
              >
                Sign In
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
