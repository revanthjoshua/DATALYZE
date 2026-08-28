import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Mail,
  KeyRound,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  Smartphone,
} from 'lucide-react';
import { authApi } from '../api/authApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FormField, Input } from '../components/ui/FormField';

export const AdminForgotPasswordPage: React.FC = () => {
  const toast = useToast();
  const navigate = useNavigate();

  // Wizard Steps: 1 = Request, 2 = Verify Code, 3 = New Password, 4 = Success
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  const [identifier, setIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [targetMasked, setTargetMasked] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Step 1: Request Code
  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setFieldErrors({ identifier: 'Please enter your registered Email or Phone Number.' });
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await authApi.forgotPasswordRequest({
        identifier: identifier.trim(),
        portal_type: 'admin',
      });
      setTargetMasked(res.target || identifier);
      setStep(2);
      toast.success(res.message, 'Verification Code Sent');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Account not found. Please verify your administrator email or phone.';
      setError(msg);
      toast.error(msg, 'Error');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify Code
  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || code.trim().length !== 6) {
      setFieldErrors({ code: 'Please enter the 6-digit verification code.' });
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await authApi.forgotPasswordVerify({
        identifier: identifier.trim(),
        code: code.trim(),
        portal_type: 'admin',
      });
      setStep(3);
      toast.success(res.message, 'Code Verified');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid or expired verification code.';
      setError(msg);
      toast.error(msg, 'Verification Failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set New Password
  const handleConfirmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};

    if (!newPassword) {
      errs.newPassword = 'New password is required.';
    } else if (newPassword.length < 6) {
      errs.newPassword = 'Password must be at least 6 characters long.';
    }

    if (!confirmPassword) {
      errs.confirmPassword = 'Please confirm your new password.';
    } else if (newPassword !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match.';
    }

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await authApi.forgotPasswordConfirm({
        identifier: identifier.trim(),
        code: code.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
        portal_type: 'admin',
      });
      setStep(4);
      toast.success(res.message, 'Password Reset Successful');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update password. Please try again.';
      setError(msg);
      toast.error(msg, 'Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] shadow-xs mb-1 text-white font-extrabold text-xl">
          <KeyRound className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] border border-[#6B4226]/20">
            Admin Password Reset
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          {step === 4 ? 'Password Changed!' : 'Reset Admin Password'}
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-sm mx-auto font-normal">
          {step === 1 && 'Enter your registered administrator email or phone to receive a verification code'}
          {step === 2 && `Enter the 6-digit verification code sent to ${targetMasked}`}
          {step === 3 && 'Create a new secure password for your administrator account'}
          {step === 4 && 'Your administrator password has been updated in the database'}
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

          {/* STEP 1: Request Code */}
          {step === 1 && (
            <form onSubmit={handleRequestSubmit} className="space-y-4">
              <FormField label="Administrator Email or Phone" required error={fieldErrors.identifier}>
                <Input
                  type="text"
                  required
                  leftIcon={<Mail className="w-4 h-4" />}
                  value={identifier}
                  onChange={(e) => {
                    setIdentifier(e.target.value);
                    if (fieldErrors.identifier) setFieldErrors({});
                  }}
                  placeholder="admin@company.com or +15550100"
                />
              </FormField>

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full"
                isLoading={loading}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Send Verification Code
              </Button>
            </form>
          )}

          {/* STEP 2: Verify Code */}
          {step === 2 && (
            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <FormField label="6-Digit Verification Code" required error={fieldErrors.code}>
                <Input
                  type="text"
                  required
                  maxLength={6}
                  leftIcon={<KeyRound className="w-4 h-4" />}
                  className="font-mono text-center tracking-widest text-lg font-bold"
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value.replace(/\D/g, ''));
                    if (fieldErrors.code) setFieldErrors({});
                  }}
                  placeholder="123456"
                />
              </FormField>

              <div className="flex items-center space-x-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="md"
                  onClick={() => setStep(1)}
                  leftIcon={<ArrowLeft className="w-4 h-4" />}
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  className="flex-1"
                  isLoading={loading}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Verify Code
                </Button>
              </div>
            </form>
          )}

          {/* STEP 3: Set New Password */}
          {step === 3 && (
            <form onSubmit={handleConfirmSubmit} className="space-y-4">
              <FormField label="New Password" required error={fieldErrors.newPassword}>
                <Input
                  type={showPassword ? 'text' : 'password'}
                  required
                  leftIcon={<Lock className="w-4 h-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="p-1 text-neutral-400 hover:text-neutral-600"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  }
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value);
                    if (fieldErrors.newPassword) setFieldErrors((p) => ({ ...p, newPassword: '' }));
                  }}
                  placeholder="Min 6 characters"
                />
              </FormField>

              <FormField label="Confirm New Password" required error={fieldErrors.confirmPassword}>
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  leftIcon={<Lock className="w-4 h-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="p-1 text-neutral-400 hover:text-neutral-600"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  }
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (fieldErrors.confirmPassword) setFieldErrors((p) => ({ ...p, confirmPassword: '' }));
                  }}
                  placeholder="Re-enter new password"
                />
              </FormField>

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full"
                isLoading={loading}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Set New Password & Confirm
              </Button>
            </form>
          )}

          {/* STEP 4: Success */}
          {step === 4 && (
            <div className="text-center py-4 space-y-4 animate-fade-in">
              <div className="w-14 h-14 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
                Your administrator password has been updated in the database. You may now sign in using your new credentials.
              </p>
              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => navigate('/login/admin')}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Return to Admin Sign In
              </Button>
            </div>
          )}

          {step !== 4 && (
            <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 text-center text-xs">
              <Link to="/login/admin" className="font-semibold text-[#6B4226] dark:text-[#D5B79F] hover:underline">
                ← Return to Admin Sign In
              </Link>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
