import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  User,
  Phone,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  Sparkles,
  Building,
  AtSign,
} from 'lucide-react';
import { authApi } from '../api/authApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FormField, Input } from '../components/ui/FormField';

export const AdminRegisterPage: React.FC = () => {
  const toast = useToast();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    company_name: '',
    industry: 'Retail/E-commerce',
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
      errs.username = 'Username must be 3-30 characters (letters, numbers, underscores).';
    }

    if (!formData.password) {
      errs.password = 'Password is required.';
    } else if (formData.password.length < 6) {
      errs.password = 'Password must be at least 6 characters long.';
    }

    if (!formData.confirm_password) {
      errs.confirm_password = 'Please confirm your password.';
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
      await authApi.registerAdmin({
        full_name: formData.full_name.trim(),
        phone_number: formData.phone_number.trim(),
        email: formData.email.trim().toLowerCase(),
        username: formData.username.trim().toLowerCase(),
        password: formData.password,
        confirm_password: formData.confirm_password,
        company_name: formData.company_name.trim() || undefined,
        industry: formData.industry,
      });

      toast.success('Admin account created successfully! Please sign in with your credentials.', 'Registration Complete');
      navigate('/login/admin');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to register administrator account. Please check your details.';
      setError(msg);
      toast.error(msg, 'Registration Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] shadow-xs mb-1 text-white font-extrabold text-xl">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] border border-[#6B4226]/20">
            Admin Portal Registration
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Create Admin Account
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          Register enterprise workspace administrator credentials to manage your team and company data
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-5 border-t-4 border-t-[#6B4226]">
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
                  placeholder="e.g. Jane Doe"
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
                  placeholder="+1 (555) 012-3456"
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
                  placeholder="admin@yourcompany.com"
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
                  placeholder="jane_admin"
                />
              </FormField>
            </div>

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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Company Workspace Name">
                <Input
                  type="text"
                  leftIcon={<Building className="w-4 h-4" />}
                  value={formData.company_name}
                  onChange={(e) => setFormData((p) => ({ ...p, company_name: e.target.value }))}
                  placeholder="e.g. Acme Corp"
                />
              </FormField>

              <FormField label="Industry">
                <select
                  value={formData.industry}
                  onChange={(e) => setFormData((p) => ({ ...p, industry: e.target.value }))}
                  className="w-full h-9 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 text-xs text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-[#6B4226]"
                >
                  <option value="Retail/E-commerce">Retail / E-commerce</option>
                  <option value="SaaS/Subscription">SaaS / Subscription</option>
                  <option value="Healthcare/Clinics">Healthcare / Clinics</option>
                  <option value="Restaurant/F&B">Restaurant / Hospitality</option>
                  <option value="Manufacturing/Supply">Manufacturing & Supply</option>
                  <option value="Financial Services">Financial Services</option>
                  <option value="General/Other">General Business</option>
                </select>
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
              Create Admin Account
            </Button>
          </form>

          <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex flex-col items-center space-y-2 text-xs">
            <span className="text-neutral-500">
              Already have an Admin account?{' '}
              <Link to="/login/admin" className="font-bold text-[#6B4226] dark:text-[#D5B79F] hover:underline">
                Sign In as Administrator →
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
