import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UserCheck,
  Mail,
  KeyRound,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FormField, Input } from '../components/ui/FormField';

export const EmployeeRegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [inviteToken, setInviteToken] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let cleanToken = inviteToken.trim();
    if (!cleanToken) {
      setError('Please enter your invitation token or paste your invite link.');
      return;
    }

    // Extract token if user pasted a full URL
    if (cleanToken.includes('token=')) {
      const match = cleanToken.match(/token=([a-zA-Z0-9_-]+)/);
      if (match) {
        cleanToken = match[1];
      }
    }

    navigate(`/accept-invite?token=${encodeURIComponent(cleanToken)}`);
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg text-center relative z-10 space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-blue-600 dark:bg-blue-700 shadow-xs mb-1 text-white font-extrabold text-xl">
          <UserCheck className="w-6 h-6" />
        </div>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            Employee Workspace Access
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100">
          Join via Team Invitation
        </h2>
        <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 max-w-md mx-auto font-normal">
          For company security and tenant isolation, employee accounts are created through verified invitations from workspace administrators.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg px-2 sm:px-0 relative z-10">
        <Card className="py-6 px-5 sm:px-8 shadow-md space-y-5 border-t-4 border-t-blue-600">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center space-x-2 text-red-600 dark:text-red-400 text-xs animate-fade-in font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/60 space-y-2.5 text-xs text-blue-950 dark:text-blue-200">
              <div className="flex items-center space-x-2 font-bold text-sm text-blue-900 dark:text-blue-100">
                <Mail className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Check Your Email Inbox</span>
              </div>
              <p className="leading-relaxed">
                If your company administrator invited you, you received an email with a direct link to set your password and join your workspace.
              </p>
              <div className="flex items-center space-x-1.5 text-[11px] text-blue-700 dark:text-blue-300 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Click the link in your email, or paste the invitation code below.</span>
              </div>
            </div>

            <form onSubmit={handleTokenSubmit} className="space-y-4 pt-1">
              <FormField 
                label="Have an Invitation Token or Link?" 
                helperText="Paste the token or full invitation link from your email"
              >
                <Input
                  type="text"
                  required
                  leftIcon={<KeyRound className="w-4 h-4" />}
                  value={inviteToken}
                  onChange={(e) => {
                    setInviteToken(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="e.g. inv_8f9a2b1c... or paste link"
                />
              </FormField>

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white"
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Continue to Accept Invitation
              </Button>
            </form>
          </div>

          <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 flex flex-col items-center space-y-2.5 text-xs">
            <span className="text-neutral-500">
              Already accepted an invitation?{' '}
              <Link to="/login/employee" className="font-bold text-blue-600 dark:text-blue-400 hover:underline">
                Sign In as Employee →
              </Link>
            </span>

            <Link
              to="/register/admin"
              className="font-medium text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 flex items-center space-x-1 transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#D5B79F]" />
              <span>Registering a new company? <strong>Create Company Admin Workspace →</strong></span>
            </Link>

            <Link to="/login" className="text-[11px] text-neutral-400 hover:underline pt-1">
              ← Back to Portal Selection
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

