import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Send,
  Bot,
  Sparkles,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import { noahApi } from '../../api/noahApi';
import { NoahDataReference } from '../../types/noah.types';
import { useTenant } from '../../context/TenantContext';

interface NoahChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  contextKpiId?: number;
}

interface Message {
  sender: 'user' | 'noah';
  text: string;
  timestamp: string;
  references?: NoahDataReference[];
  suggestedActions?: string[];
}

export const NoahChatWidget: React.FC<NoahChatWidgetProps> = ({
  isOpen,
  onClose,
  contextKpiId,
}) => {
  const { company } = useTenant();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'noah',
      text: `Hello! I am Noah, your business intelligence and web knowledge copilot for ${company?.name || 'your business'}. Ask me any question in plain language about your uploaded numbers, tracked metrics, anomaly alerts, 7-day predictions, recommended actions, or modern web technologies.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestedActions: [
        'How is our business tracking overall?',
        'What are the key insights from my uploaded data?',
        'Show 7-day predictions',
        'What actions should we take today?',
        'What is an API?',
      ],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim()) return;

    const userMsg: Message = {
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await noahApi.askNoah({
        question: textToSend,
        kpi_id: contextKpiId,
      });

      const noahMsg: Message = {
        sender: 'noah',
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        references: res.references,
        suggestedActions: res.suggested_actions,
      };
      setMessages((prev) => [...prev, noahMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        sender: 'noah',
        text: 'I encountered an error retrieving data. Please ensure data has been uploaded to the pipeline or try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end sm:justify-center sm:items-end sm:p-6 bg-neutral-900/60 backdrop-blur-xs animate-fade-in chat-widget">
      <div className="w-full h-[100dvh] sm:h-[90vh] sm:max-h-[840px] sm:max-w-xl bg-white dark:bg-[#15171C] border-0 sm:border sm:border-neutral-200 dark:sm:border-neutral-800 shadow-2xl rounded-none sm:rounded-2xl flex flex-col overflow-hidden animate-slide-up font-sans">
        {/* Top Header */}
        <div className="p-3.5 sm:p-4 bg-white dark:bg-[#15171C] border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-[#6B4226] dark:bg-[#7A4B2C] flex items-center justify-center text-white shrink-0 shadow-xs">
              <Bot className="w-5 h-5 animate-pulse" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center space-x-2">
                <h3 className="font-bold text-neutral-900 dark:text-neutral-100 text-sm sm:text-base tracking-tight truncate">
                  Noah AI Companion
                </h3>
                <span className="text-[10px] px-2 py-0.2 rounded-full bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] font-semibold border border-[#E8D6C7] dark:border-[#55331C] shrink-0">
                  Decision Intelligence
                </span>
              </div>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400 font-normal truncate">
                Intelligence copilot for {company?.name || 'Workspace'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
            title="Close Noah"
            aria-label="Close Noah"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 flex flex-col min-h-0 bg-neutral-50/50 dark:bg-neutral-950/40">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                } space-y-1`}
              >
                <div
                  className={`max-w-[88%] p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-[#6B4226] dark:bg-[#7A4B2C] text-white rounded-tr-none shadow-xs'
                      : 'bg-white dark:bg-[#15171C] text-neutral-800 dark:text-neutral-200 rounded-tl-none border border-neutral-200 dark:border-neutral-800 shadow-xs'
                  }`}
                >
                  <div className="whitespace-pre-wrap font-sans">{msg.text}</div>

                  {/* Data References & Citations */}
                  {msg.references && msg.references.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-neutral-100 dark:border-neutral-800/80 space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-neutral-400 font-mono tracking-wider block">
                        Referenced Data Points:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.references.map((ref, rIdx) => (
                          <div
                            key={rIdx}
                            className="inline-flex items-center px-2 py-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 text-[11px] font-mono text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700"
                          >
                            <span className="font-semibold text-[#6B4226] dark:text-[#D5B79F] mr-1">
                              {ref.title}:
                            </span>
                            <span>{ref.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 px-1 text-[10px] text-neutral-400">
                  <span>{msg.timestamp}</span>
                  {msg.sender === 'noah' && (
                    <button
                      onClick={() => handleCopyText(msg.text, idx)}
                      className="hover:text-neutral-600 dark:hover:text-neutral-200 flex items-center space-x-1 cursor-pointer transition-colors"
                      title="Copy response text"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-500" />
                          <span className="text-emerald-500 font-medium">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Suggested Action Prompts from Noah */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="pt-2 flex flex-wrap gap-1.5 max-w-[90%]">
                    {msg.suggestedActions.map((action, aIdx) => (
                      <button
                        key={aIdx}
                        onClick={() => handleSend(action)}
                        className="text-left text-[11px] px-2.5 py-1 rounded-full bg-white dark:bg-[#15171C] text-[#6B4226] dark:text-[#D5B79F] border border-neutral-200 dark:border-neutral-800 hover:border-[#6B4226]/50 hover:bg-[#F4ECE4]/30 dark:hover:bg-[#271910]/40 transition-colors shadow-2xs cursor-pointer font-medium"
                      >
                        {action} →
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-start space-x-2">
                <div className="p-3 rounded-2xl bg-white dark:bg-[#15171C] border border-neutral-200 dark:border-neutral-800 shadow-xs flex items-center space-x-2 text-xs text-neutral-500 font-medium">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#6B4226] dark:text-[#D5B79F]" />
                  <span>Noah is analyzing your data...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Box */}
          <div className="p-3 sm:p-4 bg-white dark:bg-[#15171C] border-t border-neutral-200 dark:border-neutral-800 shrink-0">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask Noah about your data, metrics, predictions, or web tech..."
                className="flex-1 px-3.5 py-2 text-xs sm:text-sm font-medium bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B4226] text-neutral-900 dark:text-neutral-100 placeholder-neutral-400"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="p-2 sm:px-4 sm:py-2 text-xs bg-[#6B4226] hover:bg-[#55331C] text-white font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
