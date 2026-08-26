import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  TrendingUp,
  LineChart,
  Lightbulb,
  Bell,
  FileSpreadsheet,
  Database,
  Boxes,
  Settings,
  Sparkles,
  Sun,
  Moon,
  UploadCloud,
  FileText,
  Bot,
  ArrowRight,
  User,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useToast } from '../../context/ToastContext';
import { dataApi } from '../../api/dataApi';

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenNoah: () => void;
}

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  category: 'Navigation' | 'Quick Actions' | 'System';
  icon: React.ReactNode;
  shortcut?: string;
  onSelect: () => void | Promise<void>;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onOpenNoah,
}) => {
  const navigate = useNavigate();
  const { toggleTheme, isDark } = useTheme();
  const toast = useToast();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commandItems: CommandItem[] = [
    // Navigation
    {
      id: 'nav-dashboard',
      title: 'Executive Cockpit',
      subtitle: 'Overview of business metrics & triage',
      category: 'Navigation',
      icon: <LayoutDashboard className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />,
      shortcut: 'G D',
      onSelect: () => {
        navigate('/');
        onClose();
      },
    },
    {
      id: 'nav-kpis',
      title: 'KPIs & Custom Formulas',
      subtitle: 'Track metrics, baselines & formulas',
      category: 'Navigation',
      icon: <TrendingUp className="w-4 h-4 text-emerald-500" />,
      shortcut: 'G K',
      onSelect: () => {
        navigate('/kpis');
        onClose();
      },
    },
    {
      id: 'nav-alerts',
      title: 'Anomaly & Variance Alerts',
      subtitle: 'Review active z-score divergences',
      category: 'Navigation',
      icon: <Bell className="w-4 h-4 text-amber-500" />,
      shortcut: 'G A',
      onSelect: () => {
        navigate('/alerts');
        onClose();
      },
    },
    {
      id: 'nav-predictions',
      title: '7-Day Statistical Forecasts',
      subtitle: 'Bounded projections with confidence bands',
      category: 'Navigation',
      icon: <LineChart className="w-4 h-4 text-blue-500" />,
      shortcut: 'G P',
      onSelect: () => {
        navigate('/predictions');
        onClose();
      },
    },
    {
      id: 'nav-recommendations',
      title: 'Actionable Prescriptions',
      subtitle: 'AI-generated operational directives',
      category: 'Navigation',
      icon: <Lightbulb className="w-4 h-4 text-purple-500" />,
      shortcut: 'G R',
      onSelect: () => {
        navigate('/recommendations');
        onClose();
      },
    },
    {
      id: 'nav-inventory',
      title: 'Smart Inventory & Rebalancing',
      subtitle: 'Stockout risk triage & reorder points',
      category: 'Navigation',
      icon: <Boxes className="w-4 h-4 text-orange-500" />,
      shortcut: 'G I',
      onSelect: () => {
        navigate('/inventory');
        onClose();
      },
    },
    {
      id: 'nav-data',
      title: 'Data Ingestion Pipeline',
      subtitle: 'Upload CSV, Excel, or query active tables',
      category: 'Navigation',
      icon: <Database className="w-4 h-4 text-cyan-500" />,
      shortcut: 'G U',
      onSelect: () => {
        navigate('/data');
        onClose();
      },
    },
    {
      id: 'nav-reports',
      title: 'Executive Decision Briefs',
      subtitle: 'Print PDF briefs & download CSV summaries',
      category: 'Navigation',
      icon: <FileSpreadsheet className="w-4 h-4 text-emerald-600" />,
      shortcut: 'G B',
      onSelect: () => {
        navigate('/reports');
        onClose();
      },
    },
    {
      id: 'nav-settings',
      title: 'Company Settings & Team',
      subtitle: 'Configure company profile, currency, industry & invite members',
      category: 'Navigation',
      icon: <Settings className="w-4 h-4 text-neutral-500" />,
      shortcut: 'G S',
      onSelect: () => {
        navigate('/settings');
        onClose();
      },
    },
    {
      id: 'nav-account',
      title: 'Personal Account & Theme',
      subtitle: 'Manage personal profile, password, appearance & permissions',
      category: 'Navigation',
      icon: <User className="w-4 h-4 text-[#6B4226] dark:text-[#D5B79F]" />,
      shortcut: 'G A',
      onSelect: () => {
        navigate('/account');
        onClose();
      },
    },

    // Quick Actions
    {
      id: 'action-ask-noah',
      title: 'Ask Noah AI Intelligence',
      subtitle: 'Query business data with plain conversational language',
      category: 'Quick Actions',
      icon: <Bot className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C]" />,
      shortcut: '⌘ /',
      onSelect: () => {
        onClose();
        onOpenNoah();
      },
    },
    {
      id: 'action-load-sample',
      title: 'Load 30-Day Industry Dataset',
      subtitle: 'Populate workspace with realistic sample records',
      category: 'Quick Actions',
      icon: <Sparkles className="w-4 h-4 text-amber-500" />,
      onSelect: async () => {
        onClose();
        toast.info('Loading 30-day realistic sample dataset into workspace...', 'Data Ingestion');
        try {
          await dataApi.loadSampleDataset();
          toast.success('Successfully loaded sample dataset! Refreshing workspace analytics.', 'Data Pipeline');
          window.location.reload();
        } catch {
          toast.error('Failed to load sample dataset. Please try again.', 'Pipeline Error');
        }
      },
    },
    {
      id: 'action-upload-data',
      title: 'Upload Tabular File (.csv / .xlsx)',
      subtitle: 'Open data ingestion uploader',
      category: 'Quick Actions',
      icon: <UploadCloud className="w-4 h-4 text-cyan-500" />,
      onSelect: () => {
        navigate('/data');
        onClose();
      },
    },
    {
      id: 'action-export-report',
      title: 'Export Executive Decision Brief (Print/PDF)',
      subtitle: 'Generate print-formatted PDF summary report',
      category: 'Quick Actions',
      icon: <FileText className="w-4 h-4 text-emerald-500" />,
      onSelect: () => {
        navigate('/reports');
        onClose();
      },
    },

    // System
    {
      id: 'system-toggle-theme',
      title: `Switch to ${isDark ? 'Light' : 'Dark'} Mode`,
      subtitle: 'Toggle user interface color palette',
      category: 'System',
      icon: isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />,
      onSelect: () => {
        toggleTheme();
        onClose();
      },
    },
  ];

  const filteredItems = commandItems.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.subtitle?.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + (filteredItems.length || 1)) % (filteredItems.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredItems[selectedIndex]) {
          filteredItems[selectedIndex].onSelect();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-neutral-950/60 backdrop-blur-xs animate-fade-in">
      <div
        className="w-full max-w-xl bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 shadow-2xl rounded-2xl overflow-hidden animate-slide-up flex flex-col max-h-[80vh]"
      >
        {/* Search Bar Input */}
        <div className="p-3.5 border-b border-neutral-100 dark:border-neutral-800/80 flex items-center space-x-3 bg-neutral-50/50 dark:bg-neutral-900/30">
          <Search className="w-4 h-4 text-[#6B4226] dark:text-[#8C5E3C] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or jump to page... (e.g. Ingest, Forecasts, Dark Mode)"
            className="w-full bg-transparent text-xs sm:text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none font-medium"
          />
          <kbd className="text-[10px] px-1.5 py-0.5 bg-neutral-200/70 dark:bg-neutral-800 text-neutral-500 rounded font-mono">
            ESC
          </kbd>
        </div>

        {/* Command Items List */}
        <div className="p-2 overflow-y-auto divide-y divide-neutral-100 dark:divide-neutral-800/40 flex-1">
          {filteredItems.length === 0 ? (
            <div className="p-8 text-center text-xs text-neutral-500">
              No matching commands or destinations found.
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => item.onSelect()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-neutral-100 dark:bg-neutral-800/80 text-neutral-900 dark:text-neutral-50'
                      : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800/40'
                  }`}
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="p-2 rounded-lg bg-neutral-50 dark:bg-neutral-900 border border-neutral-200/80 dark:border-neutral-800 shrink-0">
                      {item.icon}
                    </div>
                    <div className="overflow-hidden">
                      <p className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 truncate">
                        {item.title}
                      </p>
                      {item.subtitle && (
                        <p className="text-[11px] text-neutral-500 dark:text-neutral-400 truncate">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0 ml-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-500 font-mono font-medium border border-neutral-200/60 dark:border-neutral-700">
                      {item.category}
                    </span>
                    {item.shortcut && (
                      <kbd className="hidden sm:inline text-[9px] px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-400 rounded font-mono">
                        {item.shortcut}
                      </kbd>
                    )}
                    {isSelected && (
                      <ArrowRight className="w-3.5 h-3.5 text-[#6B4226] dark:text-[#8C5E3C]" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-neutral-50/80 dark:bg-neutral-900/50 border-t border-neutral-100 dark:border-neutral-800/80 text-[11px] text-neutral-500 flex items-center justify-between font-sans">
          <div className="flex items-center space-x-3 text-[10px] font-mono text-neutral-400">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <button
            onClick={() => {
              onClose();
              onOpenNoah();
            }}
            className="text-[#6B4226] dark:text-[#8C5E3C] hover:underline font-semibold flex items-center space-x-1 cursor-pointer text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Noah in Plain Language</span>
          </button>
        </div>
      </div>
    </div>
  );
};
