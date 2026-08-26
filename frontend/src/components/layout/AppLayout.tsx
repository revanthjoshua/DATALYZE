import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Bot } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { CommandPalette } from './CommandPalette';
import { NoahChatWidget } from '../noah/NoahChatWidget';

export const AppLayout: React.FC = () => {
  const [isNoahOpen, setIsNoahOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem('datalyze_sidebar_collapsed') === 'true';
  });

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('datalyze_sidebar_collapsed', String(next));
      return next;
    });
  };

  // Global Keyboard Shortcuts (Ctrl+K or Cmd+K for Command Palette, Ctrl+/ for Noah)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      } else if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setIsNoahOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#FAF8F5] dark:bg-[#0C0D10] text-neutral-900 dark:text-neutral-100 font-sans transition-colors duration-150">
      {/* Left Navigation Sidebar */}
      <Sidebar
        onOpenNoah={() => setIsNoahOpen(true)}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        <Topbar
          onOpenNoah={() => setIsNoahOpen(true)}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onOpenMobileMenu={() => setIsMobileSidebarOpen(true)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 scroll-smooth pb-20 sm:pb-8">
          <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Persistent Floating Action Trigger for Noah AI */}
      <button
        onClick={() => setIsNoahOpen(true)}
        className="fixed bottom-5 right-5 z-30 flex items-center space-x-2 px-4 py-2.5 rounded-full bg-[#6B4226] hover:bg-[#55331C] dark:bg-[#7A4B2C] dark:hover:bg-[#6B4226] text-white shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-150 cursor-pointer border border-white/20"
        title="Open Noah AI Companion (⌘ / / Ctrl+/)"
        aria-label="Open Noah AI Companion"
      >
        <div className="relative">
          <Bot className="w-4 h-4 text-white" />
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 border border-white dark:border-neutral-900" />
        </div>
        <span className="font-semibold text-xs tracking-wide">Ask Noah</span>
        <kbd className="hidden sm:inline text-[9px] px-1.5 py-0.5 bg-white/20 text-white rounded font-mono">
          ⌘/
        </kbd>
      </button>

      {/* Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onOpenNoah={() => setIsNoahOpen(true)}
      />

      {/* Global Persistent Noah AI Assistant */}
      <NoahChatWidget isOpen={isNoahOpen} onClose={() => setIsNoahOpen(false)} />
    </div>
  );
};
