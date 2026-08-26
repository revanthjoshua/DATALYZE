import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building,
  Users,
  ShieldCheck,
  Save,
  CheckCircle2,
  Lock,
  UserPlus,
  Sun,
  Moon,
  Laptop,
  Sparkles,
  RefreshCw,
  FileSpreadsheet,
  Check,
  AlertTriangle,
} from 'lucide-react';
import { companyApi, DetectedBusinessProfile } from '../api/companyApi';
import { User } from '../types/user.types';
import { useTenant } from '../context/TenantContext';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Modal } from '../components/ui/Modal';
import { FormField, Input, Select } from '../components/ui/FormField';

export const CompanySettingsPage: React.FC = () => {
  const { company, updateCompany } = useTenant();
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const toast = useToast();
  const navigate = useNavigate();

  const userRole = (user?.role || '').toLowerCase();
  const isAdmin = userRole.includes('admin');

  const [name, setName] = useState(company?.name || '');
  const [industry, setIndustry] = useState(company?.industry || 'Retail/E-commerce');
  const [currency, setCurrency] = useState(company?.currency || 'USD');
  const [timezone, setTimezone] = useState(company?.timezone || 'UTC');

  const [detectedProfile, setDetectedProfile] = useState<DetectedBusinessProfile | null>(null);
  const [adaptLoading, setAdaptLoading] = useState<boolean>(false);
  const [team, setTeam] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Form Validation Errors
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Invite modal state
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Employee');
  const [inviteErrors, setInviteErrors] = useState<Record<string, string>>({});
  const [inviteLoading, setInviteLoading] = useState(false);

  const fetchDetectedProfile = async () => {
    try {
      const prof = await companyApi.getDetectedProfile();
      if (prof && prof.industry) {
        setDetectedProfile(prof);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (company) {
      setName(company.name);
      setIndustry(company.industry);
      setCurrency(company.currency);
      setTimezone(company.timezone);
    }
    const loadTeam = async () => {
      try {
        const users = await companyApi.getUsers();
        setTeam(users);
      } catch (err) {
        console.error('Failed to load team', err);
      }
    };
    loadTeam();
    fetchDetectedProfile();
  }, [company]);

  const handleAutoAdapt = async () => {
    if (!isAdmin) {
      toast.error('Only Company Admins can auto-adapt workspace settings.', 'Permission Denied');
      return;
    }
    setAdaptLoading(true);
    try {
      const updated = await companyApi.autoAdaptCompany();
      setName(updated.name);
      setIndustry(updated.industry);
      setCurrency(updated.currency);
      setTimezone(updated.timezone);
      await updateCompany({
        name: updated.name,
        industry: updated.industry,
        currency: updated.currency,
        timezone: updated.timezone,
      });
      toast.success(
        `Applied settings from "${detectedProfile?.source_file || 'uploaded file'}": Industry set to ${updated.industry}, Currency set to ${updated.currency}.`,
        'Settings Auto-Adapted'
      );
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to auto-adapt settings from file.';
      toast.error(msg, 'Error');
    } finally {
      setAdaptLoading(false);
    }
  };

  const validateCompanyForm = () => {
    const errors: Record<string, string> = {};
    if (!name.trim()) {
      errors.name = 'Company name is required.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) {
      toast.error('Company Admin privileges required to modify settings.', 'Access Restricted');
      return;
    }
    if (!validateCompanyForm()) return;

    setLoading(true);
    try {
      await updateCompany({ name: name.trim(), industry, currency, timezone });
      toast.success('Your company settings have been saved! Redirecting to Dashboard...', 'Saved');
      setTimeout(() => {
        navigate('/');
      }, 600);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to save company settings.';
      toast.error(msg, 'Save Failed');
    } finally {
      setLoading(false);
    }
  };

  const validateInviteForm = () => {
    const errors: Record<string, string> = {};
    if (!inviteEmail.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail)) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!inviteName.trim()) {
      errors.name = 'Full name is required.';
    }
    setInviteErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) {
      toast.error('Only Company Admins can invite team members.', 'Access Restricted');
      return;
    }
    if (!validateInviteForm()) return;

    setInviteLoading(true);
    try {
      const newMember = await companyApi.inviteUser({
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole,
        full_name: inviteName.trim(),
      });
      setTeam((prev) => [...prev, newMember]);
      toast.success(`Invitation sent to ${inviteEmail}.`, 'Member Added');
      setIsInviteOpen(false);
      setInviteName('');
      setInviteEmail('');
      setInviteErrors({});
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to send invitation.';
      setInviteErrors({ email: msg });
      toast.error(msg, 'Invite Error');
    } finally {
      setInviteLoading(false);
    }
  };

  const industries = [
    'Restaurant & Food Service',
    'Retail & E-Commerce',
    'SaaS & Tech',
    'Supply Chain & Logistics',
    'Healthcare',
    'Finance & Banking',
    'Manufacturing',
    'Universal Services',
  ];

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in font-sans">
      {/* Header with Dynamic Contextual Eyebrow */}
      <PageHeader
        stage={`${company?.industry || 'Enterprise'} • ${company?.currency || 'USD'} Reporting Currency`}
        stageIcon={<Building className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Company Settings"
        description="View and manage your company name, industry type, currency, and team members."
        actions={
          isAdmin ? (
            <Button
              variant="primary"
              size="sm"
              isLoading={loading}
              onClick={handleSave}
              leftIcon={<Save className="w-3.5 h-3.5" />}
            >
              Save Changes & Go to Dashboard
            </Button>
          ) : (
            <Badge variant="neutral" size="md">
              <Lock className="w-3.5 h-3.5 mr-1 inline" /> Read-Only Mode (Employee)
            </Badge>
          )
        }
      />

      {/* Role Notice for Employee Users */}
      {!isAdmin && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 text-xs flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
          <div className="space-y-1">
            <h4 className="font-bold">Employee Account — View-Only Access</h4>
            <p className="leading-relaxed">
              You are signed in with the <strong>Employee</strong> role. You can view company metrics, reports, alerts, and operational data, but company workspace settings and team management are restricted to Company Administrators.
            </p>
          </div>
        </div>
      )}

      {/* AUTO-DETECTED FROM UPLOADED FILE BANNER */}
      {detectedProfile && detectedProfile.industry && (
        <div className="bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 rounded-2xl p-4 sm:p-5 border-l-4 border-l-[#6B4226] dark:border-l-[#8C5E3C] shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <div className="p-2.5 rounded-xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] shrink-0 mt-0.5">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2 flex-wrap">
                <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
                  Auto-Detected from Your Uploaded File
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300">
                  {detectedProfile.source_file || 'Data File'}
                </span>
              </div>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1 leading-relaxed">
                Detected Business: <strong className="text-neutral-900 dark:text-neutral-100">{detectedProfile.company_name || 'Business'}</strong> •{' '}
                Industry: <strong className="text-neutral-900 dark:text-neutral-100">{detectedProfile.industry}</strong> •{' '}
                Currency: <strong className="text-neutral-900 dark:text-neutral-100">{detectedProfile.currency}</strong> •{' '}
                Type: {detectedProfile.business_type || 'Operations'}
              </p>
            </div>
          </div>

          {isAdmin && (
            <div className="shrink-0">
              <Button
                variant="outline"
                size="sm"
                isLoading={adaptLoading}
                onClick={handleAutoAdapt}
                leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${adaptLoading ? 'animate-spin' : ''}`} />}
              >
                Sync with Uploaded File
              </Button>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Company Settings */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6">
            <CardHeader className="px-0 pt-0">
              <div className="flex items-center space-x-2">
                <Building className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
                <CardTitle>Your Company Details</CardTitle>
              </div>
            </CardHeader>

            <form onSubmit={handleSave} className="space-y-4 pt-2">
              <FormField
                label="Company / Business Name"
                required
                error={formErrors.name}
                helperText="This name appears across your dashboard and generated reports"
              >
                <Input
                  type="text"
                  disabled={!isAdmin}
                  hasError={!!formErrors.name}
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (formErrors.name) setFormErrors((prev) => ({ ...prev, name: '' }));
                  }}
                  placeholder="e.g. Royal Spice Dine"
                />
              </FormField>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField
                  label="Business Type / Industry"
                  helperText="Helps Noah tailor recommendations to your specific business"
                >
                  <Select
                    disabled={!isAdmin}
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                  >
                    {industries.map((ind) => (
                      <option key={ind} value={ind}>
                        {ind}
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField
                  label="Currency for Your Numbers"
                  helperText="The currency symbol used across all your charts and numbers"
                >
                  <Select
                    disabled={!isAdmin}
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                  >
                    <option value="INR">INR (₹ - Indian Rupee)</option>
                    <option value="USD">USD ($ - US Dollar)</option>
                    <option value="EUR">EUR (€ - Euro)</option>
                    <option value="GBP">GBP (£ - British Pound)</option>
                    <option value="JPY">JPY (¥ - Japanese Yen)</option>
                    <option value="CAD">CAD ($ - Canadian Dollar)</option>
                    <option value="AUD">AUD ($ - Australian Dollar)</option>
                    <option value="SGD">SGD ($ - Singapore Dollar)</option>
                    <option value="AED">AED (د.إ - UAE Dirham)</option>
                  </Select>
                </FormField>
              </div>

              <FormField
                label="Timezone"
                helperText="Used to organize daily and weekly prediction summaries"
              >
                <Select
                  disabled={!isAdmin}
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST - India)</option>
                  <option value="America/New_York">America/New_York (EST / EDT)</option>
                  <option value="America/Los_Angeles">America/Los_Angeles (PST / PDT)</option>
                  <option value="America/Chicago">America/Chicago (CST / CDT)</option>
                  <option value="Europe/London">Europe/London (GMT / BST)</option>
                  <option value="Europe/Paris">Europe/Paris (CET / CEST)</option>
                  <option value="Asia/Dubai">Asia/Dubai (GST - UAE)</option>
                  <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                  <option value="UTC">UTC (Coordinated Universal Time)</option>
                </Select>
              </FormField>

              {isAdmin && (
                <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex justify-end">
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    isLoading={loading}
                    leftIcon={<Save className="w-3.5 h-3.5" />}
                  >
                    Save Changes & Go to Dashboard
                  </Button>
                </div>
              )}
            </form>
          </Card>

          {/* Team Members List */}
          <Card className="p-6">
            <CardHeader className="px-0 pt-0">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />
                <CardTitle>Team Members ({team.length})</CardTitle>
              </div>
              {isAdmin && (
                <Button
                  variant="secondary"
                  size="xs"
                  onClick={() => setIsInviteOpen(true)}
                  leftIcon={<UserPlus className="w-3.5 h-3.5" />}
                >
                  Invite New Member
                </Button>
              )}
            </CardHeader>

            <div className="divide-y divide-neutral-100 dark:divide-neutral-800/80 pt-2">
              {team.map((member) => (
                <div
                  key={member.id}
                  className="py-3 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center font-bold text-[#6B4226] dark:text-[#8C5E3C] shrink-0">
                      {member.full_name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="overflow-hidden">
                      <p className="font-bold text-neutral-900 dark:text-neutral-100 truncate">
                        {member.full_name}
                      </p>
                      <p className="text-neutral-500 truncate text-[11px]">{member.email}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <Badge variant={member.role?.toLowerCase().includes('admin') ? 'brand' : 'neutral'}>
                      {member.role}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Col: Theme & Security */}
        <div className="space-y-6">
          <Card className="p-5">
            <CardHeader className="px-0 pt-0">
              <CardTitle>Appearance & Theme</CardTitle>
            </CardHeader>
            <p className="text-xs text-neutral-500 mb-3">
              Choose your preferred visual theme.
            </p>

            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setTheme('light')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-2 text-xs font-semibold transition-all cursor-pointer ${
                  theme === 'light'
                    ? 'border-[#6B4226] dark:border-[#8C5E3C] bg-[#F4ECE4]/40 dark:bg-[#271910]/40 text-[#6B4226] dark:text-[#D5B79F]'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Sun className="w-4 h-4" />
                <span>Light</span>
              </button>

              <button
                onClick={() => setTheme('dark')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-2 text-xs font-semibold transition-all cursor-pointer ${
                  theme === 'dark'
                    ? 'border-[#6B4226] dark:border-[#8C5E3C] bg-[#F4ECE4]/40 dark:bg-[#271910]/40 text-[#6B4226] dark:text-[#D5B79F]'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Moon className="w-4 h-4" />
                <span>Dark</span>
              </button>

              <button
                onClick={() => setTheme('system')}
                className={`p-3 rounded-xl border flex flex-col items-center justify-center gap-2 text-xs font-semibold transition-all cursor-pointer ${
                  theme === 'system'
                    ? 'border-[#6B4226] dark:border-[#8C5E3C] bg-[#F4ECE4]/40 dark:bg-[#271910]/40 text-[#6B4226] dark:text-[#D5B79F]'
                    : 'border-neutral-200 dark:border-neutral-800 text-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                }`}
              >
                <Laptop className="w-4 h-4" />
                <span>Auto</span>
              </button>
            </div>
          </Card>

          <Card className="p-5 border-l-4 border-l-emerald-500">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <CardTitle>Data Privacy & Security</CardTitle>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2 leading-relaxed">
              Your business records and metrics are private, isolated, and encrypted. No other company or workspace has access to your data.
            </p>
            <div className="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs text-emerald-600 font-medium">
              <span>● Workspace Secured</span>
              <span className="font-mono text-[11px] text-neutral-400">ID #{company?.id || 1}</span>
            </div>
          </Card>
        </div>
      </div>

      {/* Invite Member Modal */}
      {isAdmin && (
        <Modal
          isOpen={isInviteOpen}
          onClose={() => setIsInviteOpen(false)}
          title="Invite Team Member"
          description="Add a colleague to your workspace with specific role permissions."
          icon={<UserPlus className="w-5 h-5 text-[#6B4226]" />}
        >
          <form onSubmit={handleInviteSubmit} className="space-y-4">
            <FormField
              label="Full Name"
              required
              error={inviteErrors.name}
              helperText="Your team member's name"
            >
              <Input
                type="text"
                hasError={!!inviteErrors.name}
                value={inviteName}
                onChange={(e) => {
                  setInviteName(e.target.value);
                  if (inviteErrors.name) setInviteErrors((prev) => ({ ...prev, name: '' }));
                }}
                placeholder="e.g. Alex Johnson"
              />
            </FormField>

            <FormField
              label="Email Address"
              required
              error={inviteErrors.email}
              helperText="Where the invitation will be sent"
            >
              <Input
                type="email"
                hasError={!!inviteErrors.email}
                value={inviteEmail}
                onChange={(e) => {
                  setInviteEmail(e.target.value);
                  if (inviteErrors.email) setInviteErrors((prev) => ({ ...prev, email: '' }));
                }}
                placeholder="alex@company.com"
              />
            </FormField>

            <FormField
              label="Role & Access Level"
              helperText="Choose what this member can view and manage"
            >
              <Select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
              >
                <option value="Employee">Employee (View metrics, predictions, reports, perform operational tasks)</option>
                <option value="Analyst">Analyst (Upload data, query files, manage custom metrics)</option>
                <option value="Admin">Admin (Full settings, invite members, configure workspace)</option>
              </Select>
            </FormField>

            <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-neutral-100 dark:border-neutral-800">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsInviteOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={inviteLoading}
                leftIcon={<UserPlus className="w-3.5 h-3.5" />}
              >
                Send Invitation
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
