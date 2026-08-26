import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  UserCheck,
  ArrowRight,
  Sparkles,
  Building2,
  Lock,
  Layers,
  TrendingUp,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#0C0D10] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden font-sans text-neutral-900 dark:text-neutral-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center relative z-10 space-y-3">
        <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-[#6B4226] dark:bg-[#7A4B2C] shadow-sm mb-1 text-white font-extrabold text-2xl">
          D
        </div>
        <h2 className="text-3xl font-black tracking-tight text-neutral-900 dark:text-neutral-50">
          DATALYZE Intelligence Portal
        </h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 max-w-md mx-auto leading-relaxed">
          Select your organization portal to authenticate with role-based workspace permissions.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-2xl px-2 sm:px-0 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Company Administrator Portal */}
          <Card className="p-6 sm:p-7 flex flex-col justify-between hover:shadow-lg transition-all border-t-4 border-t-[#6B4226] group bg-white dark:bg-[#15171C]">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] flex items-center justify-center shadow-xs">
                <ShieldCheck className="w-6 h-6" />
              </div>

              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
                    Administrator
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-[#F4ECE4] dark:bg-[#271910] text-[#6B4226] dark:text-[#D5B79F] border border-[#6B4226]/20">
                    Full Control
                  </span>
                </div>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                  Workspace settings, team management, file ingestion, metric configuration, and predictive modeling.
                </p>
              </div>

              <ul className="space-y-2 text-xs text-neutral-600 dark:text-neutral-400 pt-2 border-t border-neutral-100 dark:border-neutral-800">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span>Company settings & team invites</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span>Data uploads & custom KPI schemas</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span>Executive dashboards & Noah AI</span>
                </li>
              </ul>
            </div>

            <div className="pt-6">
              <Button
                variant="primary"
                size="md"
                className="w-full justify-center"
                onClick={() => navigate('/login/admin')}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Sign In as Admin
              </Button>
            </div>
          </Card>

          {/* Card 2: Employee Workspace Portal */}
          <Card className="p-6 sm:p-7 flex flex-col justify-between hover:shadow-lg transition-all border-t-4 border-t-blue-600 group bg-white dark:bg-[#15171C]">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shadow-xs">
                <UserCheck className="w-6 h-6" />
              </div>

              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
                    Employee
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                    Operational Access
                  </span>
                </div>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 leading-relaxed">
                  Daily business metrics, operational alerts, actionable recommendations, inventory stock, and reports.
                </p>
              </div>

              <ul className="space-y-2 text-xs text-neutral-600 dark:text-neutral-400 pt-2 border-t border-neutral-100 dark:border-neutral-800">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  <span>Execute assigned recommendations</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  <span>Monitor anomaly alerts & stock</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  <span>View metrics & 7-day predictions</span>
                </li>
              </ul>
            </div>

            <div className="pt-6">
              <Button
                variant="primary"
                size="md"
                className="w-full justify-center bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white"
                onClick={() => navigate('/login/employee')}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Sign In as Employee
              </Button>
            </div>
          </Card>
        </div>

        {/* Footer Registration Link */}
        <div className="mt-8 text-center text-xs text-neutral-500 dark:text-neutral-400">
          <span>Need a new organization workspace? </span>
          <Link
            to="/register"
            className="font-bold text-[#6B4226] dark:text-[#8C5E3C] hover:underline"
          >
            Register new company account
          </Link>
        </div>
      </div>
    </div>
  );
};
