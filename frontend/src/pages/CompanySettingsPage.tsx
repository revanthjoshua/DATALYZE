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
  UserMinus,
  Sun,
  Moon,
  Laptop,
  Sparkles,
  RefreshCw,
  FileSpreadsheet,
  Check,
  AlertTriangle,
  Mail,
  Send,
  Clock,
  Trash2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { companyApi, DetectedBusinessProfile } from '../api/companyApi';
import { User, Invitation } from '../types/user.types';
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
  const { user, logout } = useAuth();
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
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [teamTab, setTeamTab] = useState<'active' | 'pending'>('active');
  const [loading, setLoading] = useState<boolean>(false);
  const [invitesLoading, setInvitesLoading] = useState<boolean>(false);
  const [resendingId, setResendingId] = useState<number | null>(null);
  const [revokingId, setRevokingId] = useState<number | null>(null);

  // Remove Member Modal State
  const [userToRemove, setUserToRemove] = useState<User | null>(null);
  const [removeLoading, setRemoveLoading] = useState<boolean>(false);

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

  const loadTeamAndInvites = async () => {
    try {
      const users = await companyApi.getUsers();
      setTeam(users);
      if (isAdmin) {
        setInvitesLoading(true);
        const invites = await companyApi.getInvitations();
        setInvitations(invites);
      }
    } catch (err) {
      console.error('Failed to load team data', err);
    } finally {
      setInvitesLoading(false);
    }
  };

  useEffect(() => {
    if (company) {
      setName(company.name);
      setIndustry(company.industry);
      setCurrency(company.currency);
      setTimezone(company.timezone);
    }
    loadTeamAndInvites();
    fetchDetectedProfile();
  }, [company, isAdmin]);

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

  const validateSettingsForm = () => {
    const errors: Record<string, string> = {};
    if (!name.trim()) {
      errors.name = 'Company name cannot be empty.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) {
      toast.error('Only Company Admins can modify workspace settings.', 'Permission Denied');
      return;
    }
    if (!validateSettingsForm()) return;

    setLoading(true);
    try {
      await updateCompany({
        name: name.trim(),
        industry,
        currency,
        timezone,
      });
      toast.success('Workspace profile and default parameters updated.', 'Settings Saved');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update company settings.';
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
      const newInvite = await companyApi.inviteUser({
        email: inviteEmail.trim().toLowerCase(),
        role: inviteRole,
        full_name: inviteName.trim(),
      });
      setInvitations((prev) => [newInvite, ...prev.filter((i) => i.id !== newInvite.id)]);
      setTeamTab('pending');
      toast.success(`Invitation email sent to ${inviteEmail}.`, 'Invitation Dispatched');
      setIsInviteOpen(false);
      setInviteName('');
      setInviteEmail('');
      setInviteErrors({});
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to send invitation.';
      setInviteErrors({ email: msg });
      toast.error(msg, 'Invite Error');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleResendInvite = async (id: number, email: string) => {
    setResendingId(id);
    try {
      const updated = await companyApi.resendInvitation(id);
      setInvitations((prev) => prev.map((i) => (i.id === id ? updated : i)));
      toast.success(`Invitation email resent to ${email}.`, 'Invitation Resent');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to resend invitation.';
      toast.error(msg, 'Resend Failed');
    } finally {
      setResendingId(null);
    }
  };

  const handleRevokeInvite = async (id: number, email: string) => {
    setRevokingId(id);
    try {
      const updated = await companyApi.revokeInvitation(id);
      setInvitations((prev) => prev.map((i) => (i.id === id ? updated : i)));
      toast.success(`Invitation for ${email} has been revoked.`, 'Invitation Revoked');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to revoke invitation.';
      toast.error(msg, 'Revoke Failed');
    } finally {
      setRevokingId(null);
    }
  };

  const handleConfirmRemove = async () => {
    if (!userToRemove) return;
    setRemoveLoading(true);
    try {
      await companyApi.removeUser(userToRemove.id);
      if (userToRemove.id === user?.id) {
        toast.success('Your account has been removed. You have been logged out.', 'Account Removed');
        setUserToRemove(null);
        logout();
        navigate('/login');
      } else {
        setTeam((prev) => prev.filter((m) => m.id !== userToRemove.id));
        toast.success(
          `Member ${userToRemove.full_name || userToRemove.email} has been removed from the workspace.`,
          'Member Removed'
        );
        setUserToRemove(null);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to remove member.';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg), 'Removal Failed');
    } finally {
      setRemoveLoading(false);
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

  const currencies = [
    { code: 'USD', symbol: '$', label: 'US Dollar ($)' },
    { code: 'EUR', symbol: '€', label: 'Euro (€)' },
    { code: 'GBP', symbol: '£', label: 'British Pound (£)' },
    { code: 'INR', symbol: '₹', label: 'Indian Rupee (₹)' },
    { code: 'CAD', symbol: 'C$', label: 'Canadian Dollar (C$)' },
    { code: 'AUD', symbol: 'A$', label: 'Australian Dollar (A$)' },
    { code: 'JPY', symbol: '¥', label: 'Japanese Yen (¥)' },
  ];

  const timezones = [
    { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
    { value: 'America/New_York', label: 'America/New_York (EST/EDT)' },
    { value: 'America/Chicago', label: 'America/Chicago (CST/CDT)' },
    { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT)' },
    { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
    { value: 'Europe/Paris', label: 'Europe/Paris (CET/CEST)' },
    { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST)' },
    { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST)' },
    { value: 'Australia/Sydney', label: 'Australia/Sydney (AEST/AEDT)' },
  ];

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="warning" dot pulse>Pending Invite</Badge>;
      case 'accepted':
        return <Badge variant="healthy">Accepted</Badge>;
      case 'revoked':
        return <Badge variant="critical">Revoked</Badge>;
      case 'expired':
      default:
        return <Badge variant="neutral">Expired</Badge>;
    }
  };

  const pendingCount = invitations.filter((i) => i.status === 'pending').length;
  const activeAdminCount = team.filter((m) => (m.role || '').toLowerCase().includes('admin')).length;
  const isTargetAdmin = (userToRemove?.role || '').toLowerCase().includes('admin');
  const isLastAdmin = isTargetAdmin && activeAdminCount <= 1;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      <PageHeader
        stage="Company Administration • Multi-Tenant Configuration"
        stageIcon={<Building className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />}
        title="Company Settings"
        description="Manage workspace parameters, industry KPI models, currency formats, and team member access."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Form + Team Management */}
        <div className="lg:col-span-2 space-y-6">
          {/* Workspace Parameters Form */}
          <Card className="p-6">
            <CardHeader className="px-0 pt-0">
              <CardTitle>Workspace Profile & Preferences</CardTitle>
            </CardHeader>

            <form onSubmit={handleSubmit} className="space-y-5">
              <FormField
                label="Company / Workspace Name"
                required
                error={formErrors.name}
                helperText="Appears on intelligence summaries and operational reports"
              >
                <Input
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (formErrors.name) setFormErrors((prev) => ({ ...prev, name: '' }));
                  }}
                  disabled={!isAdmin}
                  hasError={!!formErrors.name}
                  placeholder="Acme Global Corp"
                />
              </FormField>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField
                  label="Industry / Domain"
                  required
                  helperText="Controls KPI presets & predictive models"
                >
                  <Select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    disabled={!isAdmin}
                  >
                    {industries.map((ind) => (
                      <option key={ind} value={ind}>
                        {ind}
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField
                  label="Primary Currency"
                  required
                  helperText="Applied to financial metrics & sparklines"
                >
                  <Select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    disabled={!isAdmin}
                  >
                    {currencies.map((curr) => (
                      <option key={curr.code} value={curr.code}>
                        {curr.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
              </div>

              <FormField
                label="Operational Timezone"
                required
                helperText="Used for daily snapshot rollups and anomaly timestamps"
              >
                <Select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  disabled={!isAdmin}
                >
                  {timezones.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </Select>
              </FormField>

              {isAdmin && (
                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-neutral-100 dark:border-neutral-800">
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    isLoading={loading}
                    leftIcon={<Save className="w-3.5 h-3.5" />}
                  >
                    Save Changes
                  </Button>
                </div>
              )}
            </form>
          </Card>

          {/* Auto-Adapt from Uploaded Data Card */}
          {detectedProfile && detectedProfile.industry && (
            <Card className="p-5 border-l-4 border-l-[#6B4226] bg-[#FAF8F5]/50 dark:bg-[#15171C]/50">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100 font-mono">
                      Data Pipeline Detected Profile
                    </h4>
                  </div>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400">
                    Source: <strong className="text-neutral-900 dark:text-neutral-100">{detectedProfile.source_file || 'Uploaded File'}</strong> • Industry: <span className="font-semibold text-[#6B4226] dark:text-[#D5B79F]">{detectedProfile.industry}</span> • Currency: <span className="font-semibold">{detectedProfile.currency || 'USD'}</span>
                  </p>
                </div>
                {isAdmin && (
                  <Button
                    variant="secondary"
                    size="xs"
                    isLoading={adaptLoading}
                    onClick={handleAutoAdapt}
                    leftIcon={<RefreshCw className="w-3 h-3 text-[#6B4226]" />}
                  >
                    Auto-Adapt Settings
                  </Button>
                )}
              </div>
            </Card>
          )}

          {/* Team Members & Pending Invitations Section */}
          <Card className="p-6">
            <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-4 mb-4 flex-wrap gap-3">
              {/* Tab Selector */}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setTeamTab('active')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer flex items-center space-x-1.5 ${
                    teamTab === 'active'
                      ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                      : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  }`}
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>Active Members ({team.length})</span>
                </button>
                {isAdmin && (
                  <button
                    type="button"
                    onClick={() => setTeamTab('pending')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer flex items-center space-x-1.5 ${
                      teamTab === 'pending'
                        ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white shadow-xs'
                        : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                    }`}
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>Pending Invitations ({invitations.length})</span>
                    {pendingCount > 0 && (
                      <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-amber-200 text-amber-900">
                        {pendingCount}
                      </span>
                    )}
                  </button>
                )}
              </div>

              {isAdmin && (
                <Button
                  variant="primary"
                  size="xs"
                  onClick={() => setIsInviteOpen(true)}
                  leftIcon={<UserPlus className="w-3.5 h-3.5" />}
                >
                  Invite New Member
                </Button>
              )}
            </div>

            {/* TAB 1: ACTIVE TEAM MEMBERS */}
            {teamTab === 'active' && (
              <div className="divide-y divide-neutral-100 dark:divide-neutral-800/80">
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
                          {member.full_name} {member.id === user?.id && <span className="text-[11px] text-[#6B4226] dark:text-[#D5B79F] font-normal">(You)</span>}
                        </p>
                        <p className="text-neutral-500 truncate text-[11px] font-mono">{member.email}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <Badge variant={member.role?.toLowerCase().includes('admin') ? 'brand' : 'neutral'}>
                        {member.role}
                      </Badge>

                      {/* Visible Remove Action for Admins */}
                      {isAdmin && (
                        <Button
                          variant="ghost"
                          size="xs"
                          onClick={() => setUserToRemove(member)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40 text-[11px] px-2 py-1 h-auto"
                          title={`Remove ${member.full_name || member.email} from workspace`}
                          leftIcon={<UserMinus className="w-3.5 h-3.5 text-red-500" />}
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* TAB 2: PENDING & HISTORICAL INVITATIONS */}
            {teamTab === 'pending' && (
              <div className="space-y-3">
                {invitesLoading ? (
                  <div className="py-8 text-center text-xs text-neutral-400 font-mono">
                    Loading invitations...
                  </div>
                ) : invitations.length === 0 ? (
                  <div className="py-8 text-center space-y-2">
                    <Mail className="w-8 h-8 text-neutral-300 dark:text-neutral-700 mx-auto" />
                    <p className="text-xs font-bold text-neutral-700 dark:text-neutral-300">
                      No pending invitations
                    </p>
                    <p className="text-[11px] text-neutral-400 max-w-sm mx-auto">
                      Click "Invite New Member" above to send a real email invitation via Resend.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-neutral-100 dark:divide-neutral-800/80">
                    {invitations.map((inv) => (
                      <div
                        key={inv.id}
                        className="py-3 flex items-center justify-between gap-3 text-xs flex-wrap sm:flex-nowrap"
                      >
                        <div className="flex items-center space-x-3 overflow-hidden min-w-[180px]">
                          <div className="w-8 h-8 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 flex items-center justify-center font-bold shrink-0">
                            <Mail className="w-4 h-4" />
                          </div>
                          <div className="overflow-hidden">
                            <p className="font-bold text-neutral-900 dark:text-neutral-100 truncate">
                              {inv.full_name || inv.email.split('@')[0]}
                            </p>
                            <p className="text-neutral-500 truncate text-[11px] font-mono">{inv.email}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          <Badge variant={inv.role.toLowerCase().includes('admin') ? 'brand' : 'neutral'}>
                            {inv.role}
                          </Badge>
                          {renderStatusBadge(inv.status)}
                        </div>

                        {/* Actions for Pending/Expired invites */}
                        <div className="flex items-center space-x-1.5 shrink-0 ml-auto">
                          {inv.status === 'pending' || inv.status === 'expired' ? (
                            <>
                              <Button
                                variant="outline"
                                size="xs"
                                isLoading={resendingId === inv.id}
                                onClick={() => handleResendInvite(inv.id, inv.email)}
                                leftIcon={<Send className="w-3 h-3 text-[#6B4226]" />}
                                title="Resend email via Resend"
                              >
                                Resend
                              </Button>
                              <Button
                                variant="ghost"
                                size="xs"
                                isLoading={revokingId === inv.id}
                                onClick={() => handleRevokeInvite(inv.id, inv.email)}
                                leftIcon={<XCircle className="w-3 h-3 text-red-500" />}
                                className="text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                                title="Revoke invitation"
                              >
                                Revoke
                              </Button>
                            </>
                          ) : (
                            <span className="text-[11px] text-neutral-400 font-mono">
                              {inv.status === 'accepted' ? 'Joined workspace' : 'Revoked'}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
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
          description="Send a branded invitation email via Resend with specific role permissions."
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
              helperText="A real invitation link will be sent to this email via Resend"
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
                leftIcon={<Send className="w-3.5 h-3.5" />}
              >
                Send Invitation via Resend
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Remove Member Confirmation Modal */}
      {userToRemove && (
        <Modal
          isOpen={!!userToRemove}
          onClose={() => !removeLoading && setUserToRemove(null)}
          title="Remove Team Member"
          description="Revoke workspace access for this team member."
          icon={<UserMinus className="w-5 h-5 text-red-600" />}
        >
          <div className="space-y-4">
            {/* Member Details Card */}
            <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900/60 border border-neutral-200/80 dark:border-neutral-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-neutral-900 dark:text-neutral-100">
                  {userToRemove.full_name || 'Team Member'}
                </span>
                <Badge variant={userToRemove.role?.toLowerCase().includes('admin') ? 'brand' : 'neutral'}>
                  {userToRemove.role}
                </Badge>
              </div>
              <div className="text-xs text-neutral-500 font-mono">
                {userToRemove.email}
              </div>
            </div>

            {/* Warnings & Consequences */}
            <div className="space-y-2 text-xs text-neutral-600 dark:text-neutral-400">
              <p>
                Are you sure you want to remove <strong>{userToRemove.full_name || userToRemove.email}</strong> from <strong>{company?.name || 'this workspace'}</strong>?
              </p>
              <ul className="list-disc list-inside space-y-1 text-neutral-500">
                <li>The member will immediately lose access to the workspace.</li>
                <li>Their active sessions and authentication tokens will be immediately invalidated.</li>
                <li>Company datasets, analytics, KPIs, and reports will remain safe and unaffected.</li>
              </ul>
            </div>

            {/* Self-Removal Warning */}
            {userToRemove.id === user?.id && (
              <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-200 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span>
                  <strong>Warning:</strong> You are removing your own account. If you confirm, you will be immediately logged out of this workspace.
                </span>
              </div>
            )}

            {/* Last Admin Blocking Notice */}
            {isLastAdmin && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-xs text-red-700 dark:text-red-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>
                  <strong>Action Blocked:</strong> You cannot remove the only remaining Company Admin in this workspace. Please invite or assign another Admin before removing this account.
                </span>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-neutral-100 dark:border-neutral-800">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={removeLoading}
                onClick={() => setUserToRemove(null)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                isLoading={removeLoading}
                disabled={isLastAdmin}
                onClick={handleConfirmRemove}
                leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              >
                {userToRemove.id === user?.id ? 'Remove My Account' : 'Confirm & Remove Member'}
              </Button>

            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
