import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Lock,
  User,
  Building2,
  ArrowRight,
  Eye,
  EyeOff,
  Sparkles,
  Mail,
} from 'lucide-react';
import { authApi } from '../api/authApi';
import { InviteVerifyResponse } from '../types/user.types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FormField, Input } from '../components/ui/FormField';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../context/ToastContext';

export const AcceptInvitePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const token = searchParams.get('token') || '';

  const [verifying, setVerifying] = useState<boolean>(true);
  const [inviteDetails, setInviteDetails] = useState<InviteVerifyResponse | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  // Form State
  const [fullName, setFullName] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setVerifyError('Missing invitation token. Please check the link from your email.');
      return;
    }

    const checkToken = async () => {
      setVerifying(true);
      setVerifyError(null);
      try {
        const details = await authApi.verifyInvitation(token);
        setInviteDetails(details);
        if (details.full_name) {
          setFullName(details.full_name);
        }
      } catch (err: any) {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          'This invitation link is invalid or has expired.';
        setVerifyError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      } finally {
        setVerifying(false);
      }
    };

    checkToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!password) {
      setSubmitError('Please enter a password.');
      return;
    }
    if (password.length < 6) {
      setSubmitError('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setSubmitError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await authApi.acceptInvitation({
        token,
        password,
        confirm_password: confirmPassword,
        full_name: fullName.trim() || undefined,
      });

      setIsSuccess(true);
      toast.success('Your account has been activated! Please log in.', 'Welcome to Datalyze');
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to activate account. Please try again.';
      setSubmitError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      toast.error(typeof msg === 'string' ? msg : 'Activation failed', 'Error');
    } finally {
      setSubmitting(false);
    }
  };

  const roleTitle = (inviteDetails?.role || 'employee').toLowerCase();
  const targetLoginUrl = roleTitle === 'admin' ? '/login/admin' : '/login/employee';

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#4A2E1B] to-[#6B4226] shadow-md mb-3">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-black text-neutral-900 dark:text-neutral-100 tracking-tight font-mono uppercase">
          DATALYZE
        </h2>
        <p className="text-xs font-semibold text-[#6B4226] dark:text-[#D5B79F] uppercase tracking-wider mt-0.5">
          Workspace Onboarding
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="p-6 sm:p-8 shadow-xl border border-neutral-200/80 dark:border-neutral-800">
          {/* 1. Loading State */}
          {verifying && (
            <div className="py-12 text-center space-y-3">
              <div className="w-8 h-8 border-3 border-[#6B4226] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-neutral-500 font-mono">Verifying invitation token...</p>
            </div>
          )}

          {/* 2. Error State */}
          {!verifying && verifyError && (
            <div className="py-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/60 flex items-center justify-center text-red-600 dark:text-red-400">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                  Invitation Unavailable
                </h3>
                <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                  {verifyError}
                </p>
              </div>
              <div className="pt-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/login')}
                  leftIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Return to Sign In
                </Button>
              </div>
            </div>
          )}

          {/* 3. Success State */}
          {!verifying && isSuccess && (
            <div className="py-6 text-center space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                  Account Activated!
                </h3>
                <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                  You are now registered as an active team member of{' '}
                  <strong className="text-neutral-900 dark:text-neutral-100">
                    {inviteDetails?.company_name}
                  </strong>
                  .
                </p>
              </div>
              <div className="pt-2">
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => navigate(targetLoginUrl)}
                  leftIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Sign In to Workspace
                </Button>
              </div>
            </div>
          )}

          {/* 4. Active Acceptance Form */}
          {!verifying && !verifyError && !isSuccess && inviteDetails && (
            <div className="space-y-6">
              {/* Workspace Badge Header */}
              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200/80 dark:border-neutral-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs font-bold text-neutral-900 dark:text-neutral-100">
                    <Building2 className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />
                    <span>{inviteDetails.company_name}</span>
                  </div>
                  <Badge variant="brand" size="xs">
                    {inviteDetails.role}
                  </Badge>
                </div>
                <div className="flex items-center space-x-1.5 text-xs text-neutral-500 font-mono">
                  <Mail className="w-3.5 h-3.5 text-neutral-400" />
                  <span>{inviteDetails.email}</span>
                </div>
              </div>

              <div className="space-y-1">
                <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                  Set Your Password
                </h3>
                <p className="text-xs text-neutral-500">
                  Choose a secure password to complete your registration.
                </p>
              </div>

              {submitError && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <FormField label="Full Name" required>
                  <Input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Smith"
                  />
                </FormField>

                <FormField label="Create Password" required helperText="Minimum 6 characters">
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </FormField>

                <FormField label="Confirm Password" required>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                  />
                </FormField>

                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  className="w-full"
                  isLoading={submitting}
                  leftIcon={<Sparkles className="w-4 h-4" />}
                >
                  Join {inviteDetails.company_name}
                </Button>
              </form>
            </div>
          )}
        </Card>

        {/* Footer Link */}
        <p className="text-center text-xs text-neutral-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-[#6B4226] dark:text-[#D5B79F] font-bold hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};
