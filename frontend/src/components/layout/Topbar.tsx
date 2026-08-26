import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Sparkles,
  Database,
  Search,
  Menu,
  Sun,
  Moon,
  Calendar,
} from 'lucide-react';
import { useTenant } from '../../context/TenantContext';
import { useTheme } from '../../context/ThemeContext';
import { useDateRange, TimeRangeOption } from '../../context/DateRangeContext';

interface TopbarProps {
  onOpenNoah: () => void;
  onOpenCommandPalette: () => void;
  onOpenMobileMenu?: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({
  onOpenNoah,
  onOpenCommandPalette,
  onOpenMobileMenu,
}) => {
  const { company } = useTenant();
  const { isDark, toggleTheme } = useTheme();
  const { timeRange, setTimeRange } = useDateRange();
  const navigate = useNavigate();

  return (
    <header className="h-14 bg-white dark:bg-[#15171C] border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30 transition-colors">
      {/* Left Side: Mobile Hamburger & Context Badge */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenMobileMenu}
          className="p-1.5 rounded-lg text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 md:hidden transition-colors"
          title="Open Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div
          onClick={() => navigate('/settings')}
          title="Click to manage Company Workspace Settings"
          className="flex items-center space-x-2 text-xs cursor-pointer hover:opacity-80 transition-opacity"
        >
          <span className="font-bold text-neutral-900 dark:text-neutral-100 text-xs sm:text-sm tracking-tight truncate max-w-[140px] sm:max-w-none">
            {company?.name || 'DATALYZE'}
          </span>
          <span className="text-neutral-400 hidden sm:inline">/</span>
          <span className="hidden sm:inline px-2 py-0.5 rounded-md text-[11px] font-semibold bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
            {company?.industry || 'Enterprise'}
          </span>
        </div>

        {/* Engine Pipeline Status Pill */}
        <div className="hidden xl:flex items-center space-x-2 px-3 py-1 rounded-full bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-[10px] text-neutral-600 dark:text-neutral-400 font-mono">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-neutral-900 dark:text-neutral-100 font-bold">Engine:</span>
          <span className="text-[#6B4226] dark:text-[#8C5E3C] font-medium">
            Measure → Detect → Explain → Predict → Recommend
          </span>
        </div>
      </div>

      {/* Right Side: Global Time-Range Picker, Quick Search, Ingest, Theme Toggle, Notifications */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Global Date / Time-Range Selector */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-xl bg-neutral-100 dark:bg-neutral-800/80 border border-neutral-200/80 dark:border-neutral-700/80 text-xs">
          <Calendar className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#D5B79F]" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRangeOption)}
            className="bg-transparent text-xs font-semibold text-neutral-800 dark:text-neutral-200 focus:outline-none cursor-pointer pr-1"
            title="Global Dashboard Time Horizon"
          >
            <option value="7D" className="bg-white dark:bg-neutral-900">Last 7 Days</option>
            <option value="14D" className="bg-white dark:bg-neutral-900">Last 14 Days</option>
            <option value="30D" className="bg-white dark:bg-neutral-900">Last 30 Days</option>
            <option value="90D" className="bg-white dark:bg-neutral-900">Last 90 Days</option>
            <option value="ALL" className="bg-white dark:bg-neutral-900">All Records</option>
          </select>
        </div>

        {/* Command Palette Shortcut Button */}
        <button
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs bg-neutral-100 dark:bg-neutral-800/80 hover:bg-neutral-200/70 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200/80 dark:border-neutral-700/80 transition-colors cursor-pointer"
        >
          <Search className="w-3.5 h-3.5 text-neutral-400" />
          <span className="font-medium">Command Palette</span>
          <kbd className="text-[9px] px-1.5 py-0.5 bg-white dark:bg-neutral-900 text-neutral-500 rounded border border-neutral-200 dark:border-neutral-700 font-mono">
            ⌘K
          </kbd>
        </button>

        {/* Upload Data Button */}
        <button
          onClick={() => navigate('/data')}
          className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-[#15171C] text-neutral-900 dark:text-neutral-100 border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors"
        >
          <Database className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />
          <span>Ingest Data</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-xl text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/60 dark:border-neutral-800 transition-colors cursor-pointer"
          title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-neutral-600" />}
        </button>

        {/* Notifications Bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="p-1.5 rounded-xl text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200/60 dark:border-neutral-800 transition-colors relative cursor-pointer"
          title="Active Anomaly Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        </button>
      </div>
    </header>
  );
};
