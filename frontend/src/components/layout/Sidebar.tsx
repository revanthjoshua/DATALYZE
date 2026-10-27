import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  LineChart,
  Lightbulb,
  Bell,
  FileSpreadsheet,
  Database,
  Building2,
  ShieldCheck,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  X,
  User as UserIcon,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTenant } from '../../context/TenantContext';

interface SidebarProps {
  onOpenNoah: () => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isMobileOpen = false,
  onCloseMobile,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const { user, logout } = useAuth();
  const { company } = useTenant();
  const navigate = useNavigate();
  const location = useLocation();

  const userRole = (user?.role || '').toLowerCase();
  const isAdmin = userRole.includes('admin');

  // Coherent Analyst Journey sequence
  const analystWorkflowItems = [
    { name: 'Analyst Workspace', path: '/analysis', icon: Lightbulb, stage: 'Start', description: 'Define a question, prepare data, analyze evidence and share findings' },
    {
      name: 'Data collection',
      path: '/data',
      icon: Database,
      stage: '1. Ingest',
      description: 'Upload, inspect and edit the active dataset',
    },
    {
      name: 'Metric directory',
      path: '/kpis',
      icon: TrendingUp,
      stage: '2. Measure',
      description: 'Review metric definitions and observed values',
    },
    {
      name: 'Dashboard',
      path: '/',
      icon: LayoutDashboard,
      stage: '3. Overview',
      description: 'Consolidated overview, metric status & triage',
    },
    {
      name: 'Reports',
      path: '/reports',
      icon: FileSpreadsheet,
      stage: '4. Report',
      description: 'Download metric summaries and printable reports',
    },
    {
      name: 'Metric alerts',
      path: '/alerts',
      icon: Bell,
      stage: '5. Monitor',
      description: 'Statistical anomaly & variance alerts',
    },
  ];

  // Separated Workspace & User Administration
  const adminItems = [
    {
      name: 'Company Settings',
      path: '/settings',
      icon: Building2,
      stage: isAdmin ? 'Admin' : 'View',
      description: 'Workspace profile, industry & team access',
    },
    {
      name: 'Personal Account',
      path: '/account',
      icon: UserIcon,
      stage: 'Account',
      description: 'User profile, credentials & appearance',
    },
  ];

  // Helper to ensure role-specific dashboard URLs highlight the same Dashboard navigation item
  const isItemActive = (itemPath: string): boolean => {
    if (itemPath === '/') {
      return (
        location.pathname === '/' ||
        location.pathname === '/dashboard' ||
        location.pathname === '/admin/dashboard' ||
        location.pathname === '/employee/dashboard'
      );
    }
    return location.pathname === itemPath || location.pathname.startsWith(itemPath + '/');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderNavGroup = (
    items: typeof analystWorkflowItems,
    sectionTitle?: string
  ) => (
    <div className="space-y-1">
      {sectionTitle && (
        <div className="px-3 pt-2 pb-1">
          {!isCollapsed ? (
            <p className="text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-wider font-mono">
              {sectionTitle}
            </p>
          ) : (
            <hr className="border-neutral-200 dark:border-neutral-800 my-1" />
          )}
        </div>
      )}
      {items.map((item) => {
        const Icon = item.icon;
        const active = isItemActive(item.path);

        return (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onCloseMobile}
            title={isCollapsed ? `${item.name} (${item.stage}): ${item.description}` : item.description}
            aria-label={item.name}
            aria-current={active ? 'page' : undefined}
            className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors group relative ${
              active
                ? 'bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] font-semibold border-l-2 border-[#6B4226] dark:border-[#8C5E3C]'
                : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100/80 dark:hover:bg-neutral-800/60'
            }`}
          >
            <div className="flex items-center space-x-2.5 min-w-0">
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  active
                    ? 'text-[#6B4226] dark:text-[#8C5E3C]'
                    : 'text-neutral-400 group-hover:text-neutral-600 dark:group-hover:text-neutral-200'
                }`}
              />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
            </div>

            {!isCollapsed && item.stage && (
              <span
                className={`text-[9px] px-1.5 py-0.2 rounded font-mono transition-colors shrink-0 ${
                  active
                    ? 'bg-[#6B4226]/15 dark:bg-[#8C5E3C]/25 text-[#6B4226] dark:text-[#D5B79F] font-semibold'
                    : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-300'
                }`}
              >
                {item.stage}
              </span>
            )}
          </NavLink>
        );
      })}
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-neutral-950/60 backdrop-blur-xs md:hidden animate-fade-in"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col bg-[#FAF8F5] dark:bg-[#0C0D10] border-r border-neutral-200 dark:border-neutral-800 transition-all duration-300 ease-in-out ${
          isMobileOpen ? 'translate-x-0 w-64 shadow-2xl' : '-translate-x-full md:translate-x-0'
        } ${isCollapsed ? 'md:w-20' : 'md:w-64'}`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
          {/* Logo & Brand Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-neutral-200 dark:border-neutral-800 shrink-0">
            <div
              onClick={() => {
                onCloseMobile?.();
                navigate('/');
              }}
              className="flex items-center space-x-3 cursor-pointer group"
            >
              <div className="h-9 w-9 rounded-xl bg-[#6B4226] dark:bg-[#7A4B2C] flex items-center justify-center text-white font-bold text-base shadow-xs shrink-0">
                D
              </div>
              {!isCollapsed && (
                <div className="overflow-hidden">
                  <div className="flex items-center space-x-1.5">
                    <h1 className="font-bold text-sm text-neutral-900 dark:text-neutral-50 tracking-tight">DATALYZE</h1>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-mono font-semibold border border-neutral-200 dark:border-neutral-700">
                      PRO
                    </span>
                  </div>
                  <p className="text-[11px] text-neutral-500 dark:text-neutral-400 font-normal truncate">
                    Data Analyst Platform
                  </p>
                </div>
              )}
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={onCloseMobile}
              className="p-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 md:hidden transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Desktop Collapse Toggle */}
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="hidden md:flex p-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
                title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
                aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              >
                {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
              </button>
            )}
          </div>

          {/* Tenant Badge (Clickable to redirect to Company Settings) */}
          {!isCollapsed && company && (
            <div
              onClick={() => {
                onCloseMobile?.();
                navigate('/settings');
              }}
              title="Click to manage Company Workspace Settings"
              className="px-3.5 py-2 mx-3 mt-3 bg-white dark:bg-[#15171C] rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-[#6B4226]/50 dark:hover:border-[#8C5E3C]/50 hover:bg-[#F4ECE4]/30 dark:hover:bg-[#271910]/30 shadow-xs flex items-center justify-between cursor-pointer transition-all group"
            >
              <div className="overflow-hidden pr-2">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <p className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-[#6B4226] dark:group-hover:text-[#D5B79F] truncate transition-colors">
                    {company.name}
                  </p>
                </div>
                <p className="text-[10px] text-neutral-500 dark:text-neutral-400 truncate mt-0.5 font-medium">
                  {company.industry}
                </p>
              </div>
              <Building2 className="w-3.5 h-3.5 text-neutral-400 group-hover:text-[#6B4226] dark:group-hover:text-[#D5B79F] shrink-0 transition-colors" />
            </div>
          )}

          {/* Navigation Items Organized by Analyst Workflow & Administration */}
          <nav className="px-2 py-3 space-y-3 flex-1">
            {renderNavGroup(analystWorkflowItems, 'Analyst Journey')}
            {renderNavGroup(adminItems, 'Administration')}
          </nav>
        </div>

        {/* User Footer with Role Badge */}
        <div className="p-3 border-t border-neutral-200 dark:border-neutral-800 bg-white/50 dark:bg-[#15171C]/50">
          <div
            className={`flex items-center justify-between p-2 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 hover:border-[#6B4226]/40 dark:hover:border-[#8C5E3C]/50 hover:bg-[#F4ECE4]/20 dark:hover:bg-[#271910]/20 transition-all ${
              isCollapsed ? 'flex-col gap-2' : ''
            }`}
          >
            <div
              onClick={() => {
                onCloseMobile?.();
                navigate('/account');
              }}
              title="Click to view Personal Account Settings"
              className="overflow-hidden pr-2 min-w-0 flex-1 cursor-pointer group"
            >
              {!isCollapsed && (
                <>
                  <p className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-[#6B4226] dark:group-hover:text-[#D5B79F] truncate transition-colors">
                    {user?.full_name || 'Business Leader'}
                  </p>
                  <p className="text-[10px] text-neutral-500 dark:text-neutral-400 flex items-center space-x-1 truncate mt-0.5 font-normal">
                    {isAdmin ? (
                      <ShieldCheck className="w-3 h-3 text-emerald-500 inline shrink-0" />
                    ) : (
                      <UserCheck className="w-3 h-3 text-blue-500 inline shrink-0" />
                    )}
                    <span>{user?.role || 'Company Admin'}</span>
                  </p>
                </>
              )}
            </div>
            <button
              onClick={handleLogout}
              title="Log Out"
              aria-label="Log Out"
              className="p-1.5 rounded-lg text-neutral-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors cursor-pointer shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
