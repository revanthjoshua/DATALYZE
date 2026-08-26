import React, { useState, useEffect } from 'react';
import {
  User as UserIcon,
  Mail,
  Shield,
  KeyRound,
  Sun,
  Moon,
  Monitor,
  Save,
  CheckCircle2,
  Lock,
  Building,
  Sparkles,
  Phone,
  UserCheck,
  AlertCircle,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTenant } from '../context/TenantContext';
import { useTheme } from '../context/ThemeContext';
import { useToast } from '../context/ToastContext';
import { authApi } from '../api/authApi';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { FormField, Input } from '../components/ui/FormField';

export const AccountPage: React.FC = () => {
  const { user, setUser } = useAuth();
  const { company } = useTenant();
  const { theme, setTheme } = useTheme();
  const toast = useToast();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [username, setUsername] = useState(user?.username || '');
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number || '');
  const [loading, setLoading] = useState(false);
  const [profileErrors, setProfileErrors] = useState<Record<string, string>>({});

  // Password Update State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwErrors, setPwErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      setUsername(user.username || '');
      setPhoneNumber(user.phone_number || '');
    }
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!fullName.trim()) {
      errors.fullName = 'Full name cannot be empty.';
    }
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    }
    if (Object.keys(errors).length > 0) {
      setProfileErrors(errors);
      return;
    }

    try {
      setLoading(true);
      setProfileErrors({});
      const updated = await authApi.updateProfile({
        full_name: fullName.trim(),
        email: email.trim(),
        username: username.trim() || undefined,
        phone_number: phoneNumber.trim() || undefined,
      });
      if (updated && updated.user) {
        setUser(updated.user);
        localStorage.setItem('datalyze_user', JSON.stringify(updated.user));
      }
      toast.success('Your personal account details have been saved to the database.', 'Account Updated');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Could not save profile changes.';
      toast.error(msg, 'Update Failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!newPassword) {
      errors.newPassword = 'Please enter a new password.';
    } else if (newPassword.length < 6) {
      errors.newPassword = 'Password must be at least 6 characters.';
    }
    if (newPassword !== confirmPassword) {
      errors.confirmPassword = 'New passwords do not match.';
    }
    if (Object.keys(errors).length > 0) {
      setPwErrors(errors);
      return;
    }

    try {
      setPwLoading(true);
      setPwErrors({});
      // Persist password hash to the backend database
      await authApi.updateProfile({ password: newPassword });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Account password has been changed and updated in the database.', 'Security Updated');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update password.';
      toast.error(msg, 'Security Error');
    } finally {
      setPwLoading(false);
    }
  };

  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in pb-12 font-sans">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={`${user?.role || 'Company Admin'} • User #${user?.id || 1} • ${company?.name || 'Workspace'}`}
        stageIcon={<UserIcon className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Personal Account"
        description="Manage your personal profile, credentials, appearance theme, and assigned workspace permissions."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: User Identity Card & Appearance */}
        <div className="space-y-6">
          {/* User Profile Avatar Card */}
          <Card className="p-6 text-center space-y-4">
            <div className="w-20 h-20 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] text-white flex items-center justify-center font-bold text-2xl mx-auto shadow-md border-2 border-white dark:border-neutral-800">
              {getInitials(user?.full_name || 'Admin User')}
            </div>

            <div>
              <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 font-sans">
                {user?.full_name || 'Admin User'}
              </h3>
              <p className="text-xs text-neutral-500 font-mono mt-0.5">{user?.email}</p>
              {user?.username && (
                <p className="text-[11px] text-neutral-400 font-mono mt-0.5">@{user.username}</p>
              )}
            </div>

            <div className="flex items-center justify-center space-x-2">
              <Badge variant="brand" size="sm">
                {user?.role?.toUpperCase() || 'ADMIN'}
              </Badge>
              <Badge variant="healthy" size="sm" dot>
                ACTIVE SESSION
              </Badge>
            </div>

            <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 text-left space-y-2 text-xs">
              <div className="flex items-center justify-between text-neutral-500">
                <span>Workspace:</span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-200">
                  {company?.name || 'Enterprise'}
                </span>
              </div>
              <div className="flex items-center justify-between text-neutral-500">
                <span>Tenant ID:</span>
                <span className="font-mono text-neutral-900 dark:text-neutral-200">
                  #{company?.id || 1}
                </span>
              </div>
            </div>
          </Card>

          {/* Theme & Display Mode */}
          <Card className="p-6 space-y-4">
            <div>
              <h4 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                Interface Theme
              </h4>
              <p className="text-xs text-neutral-500 mt-0.5">
                Select your preferred color theme or match system settings.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center space-y-1.5 transition-all cursor-pointer ${
                  theme === 'light'
                    ? 'border-[#6B4226] bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] font-bold shadow-xs'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Sun className="w-5 h-5" />
                <span className="text-xs">Light</span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center space-y-1.5 transition-all cursor-pointer ${
                  theme === 'dark'
                    ? 'border-[#6B4226] dark:border-[#8C5E3C] bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] font-bold shadow-xs'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Moon className="w-5 h-5" />
                <span className="text-xs">Dark</span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('system')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center space-y-1.5 transition-all cursor-pointer ${
                  theme === 'system' || theme === 'auto'
                    ? 'border-[#6B4226] bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] font-bold shadow-xs'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Monitor className="w-5 h-5" />
                <span className="text-xs">Auto</span>
              </button>
            </div>
          </Card>
        </div>

        {/* Right Columns: Profile Edit & Password Change */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information Form */}
          <Card className="p-6">
            <CardHeader className="p-0 pb-4 border-b border-neutral-100 dark:border-neutral-800 mb-5">
              <div className="flex items-center space-x-2">
                <UserCheck className="w-5 h-5 text-[#6B4226] dark:text-[#D5B79F]" />
                <CardTitle className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                  Profile Information
                </CardTitle>
              </div>
              <p className="text-xs text-neutral-500 mt-1">
                Update your personal name, contact email, username handle, and phone number.
              </p>
            </CardHeader>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Full Name" required error={profileErrors.fullName}>
                  <Input
                    type="text"
                    value={fullName}
                    onChange={(e) => {
                      setFullName(e.target.value);
                      if (profileErrors.fullName) setProfileErrors((p) => ({ ...p, fullName: '' }));
                    }}
                    placeholder="Jane Doe"
                    leftIcon={<UserIcon className="w-4 h-4" />}
                  />
                </FormField>

                <FormField label="Username" error={profileErrors.username}>
                  <Input
                    type="text"
                    value={username}
                    onChange={(e) => {
                      setUsername(e.target.value);
                      if (profileErrors.username) setProfileErrors((p) => ({ ...p, username: '' }));
                    }}
                    placeholder="janedoe"
                    leftIcon={<span className="text-xs font-mono font-bold text-neutral-400">@</span>}
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Email Address" required error={profileErrors.email}>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (profileErrors.email) setProfileErrors((p) => ({ ...p, email: '' }));
                    }}
                    placeholder="jane@example.com"
                    leftIcon={<Mail className="w-4 h-4" />}
                  />
                </FormField>

                <FormField label="Phone Number" error={profileErrors.phoneNumber}>
                  <Input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => {
                      setPhoneNumber(e.target.value);
                      if (profileErrors.phoneNumber) setProfileErrors((p) => ({ ...p, phoneNumber: '' }));
                    }}
                    placeholder="+1 555 0199"
                    leftIcon={<Phone className="w-4 h-4" />}
                  />
                </FormField>
              </div>

              <div className="pt-3 flex justify-end">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={loading}
                  leftIcon={<Save className="w-4 h-4" />}
                >
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </Card>

          {/* Change Password Card */}
          <Card className="p-6">
            <CardHeader className="p-0 pb-4 border-b border-neutral-100 dark:border-neutral-800 mb-5">
              <div className="flex items-center space-x-2">
                <KeyRound className="w-5 h-5 text-[#6B4226] dark:text-[#D5B79F]" />
                <CardTitle className="text-base font-bold text-neutral-900 dark:text-neutral-100">
                  Change Password
                </CardTitle>
              </div>
              <p className="text-xs text-neutral-500 mt-1">
                Ensure your account is using a secure password to protect company data.
              </p>
            </CardHeader>

            <form onSubmit={handleUpdatePassword} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="New Password" required error={pwErrors.newPassword}>
                  <Input
                    type={showPw ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                      if (pwErrors.newPassword) setPwErrors((p) => ({ ...p, newPassword: '' }));
                    }}
                    placeholder="Min 6 characters"
                    leftIcon={<Lock className="w-4 h-4" />}
                    rightIcon={
                      <button
                        type="button"
                        onClick={() => setShowPw(!showPw)}
                        className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 cursor-pointer"
                      >
                        {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    }
                  />
                </FormField>

                <FormField label="Confirm New Password" required error={pwErrors.confirmPassword}>
                  <Input
                    type={showPw ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (pwErrors.confirmPassword) setPwErrors((p) => ({ ...p, confirmPassword: '' }));
                    }}
                    placeholder="Re-enter new password"
                    leftIcon={<Lock className="w-4 h-4" />}
                  />
                </FormField>
              </div>

              <div className="pt-3 flex justify-end">
                <Button
                  type="submit"
                  variant="secondary"
                  size="md"
                  isLoading={pwLoading}
                  leftIcon={<Shield className="w-4 h-4 text-emerald-600" />}
                >
                  Update Password
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};
