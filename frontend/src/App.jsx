import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  LayoutDashboard,
  Database,
  LogOut,
  UserCheck,
  Terminal,
  Cpu
} from 'lucide-react';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { DataCollection } from './pages/DataCollection';
import { useBehaviorTracking } from './hooks/useBehaviorTracking';
import { sessionAPI } from './services/api';

export function App() {
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'collection'
  const [session, setSession] = useState(null);

  // Check existing session/token on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('auth_user');
    const token = localStorage.getItem('auth_token');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.clear();
      }
    }
  }, []);

  // Continuous behavioral tracking hook
  const {
    isTracking,
    keystrokeCount,
    mouseEventCount,
    startTracking,
    stopTracking
  } = useBehaviorTracking(session?.id);

  // Start new tracking session
  const handleStartSession = useCallback(async () => {
    try {
      const newSession = await sessionAPI.startSession();
      setSession(newSession);
      startTracking();
    } catch (err) {
      console.error('Failed to start tracking session:', err);
      alert('Could not start tracking session. Ensure the backend is running.');
    }
  }, [startTracking]);

  // Stop tracking session
  const handleStopSession = useCallback(async () => {
    if (session?.id) {
      try {
        await stopTracking();
        await sessionAPI.stopSession(session.id);
        setSession((prev) => (prev ? { ...prev, is_active: false } : null));
      } catch (err) {
        console.error('Failed to stop session:', err);
      }
    }
  }, [session?.id, stopTracking]);

  const handleLogout = () => {
    if (isTracking) {
      handleStopSession();
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
    setSession(null);
  };

  // If unauthenticated, render Login or Register
  if (!user) {
    if (authView === 'register') {
      return (
        <Register
          onRegisterSuccess={(newUser) => {
            setUser(newUser);
          }}
          onNavigateToLogin={() => setAuthView('login')}
        />
      );
    }
    return (
      <Login
        onLoginSuccess={(loggedInUser) => {
          setUser(loggedInUser);
        }}
        onNavigateToRegister={() => setAuthView('register')}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Cyber Navigation Bar */}
      <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-black tracking-tight text-white">Continuous Biometric Auth</span>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono">
                XAI Transformer
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">
              Continuous Behavioral Biometrics Research Project
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <nav className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1 gap-1">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'dashboard'
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('collection')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              activeTab === 'collection'
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            Data Collection
          </button>
        </nav>

        {/* User Status & Sign Out */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-xs font-bold text-slate-200">{user.username}</p>
            <span className="text-[10px] text-emerald-400 flex items-center justify-end gap-1">
              <UserCheck className="w-3 h-3" /> Authenticated
            </span>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 border border-slate-700 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'dashboard' ? (
          <Dashboard
            session={session}
            isTracking={isTracking}
            keystrokeCount={keystrokeCount}
            mouseEventCount={mouseEventCount}
            onStartSession={handleStartSession}
            onStopSession={handleStopSession}
            user={user}
          />
        ) : (
          <DataCollection
            session={session}
            isTracking={isTracking}
            keystrokeCount={keystrokeCount}
            mouseEventCount={mouseEventCount}
            onStartSession={handleStartSession}
            onStopSession={handleStopSession}
          />
        )}
      </main>

      {/* Research Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        AI-Driven Continuous Authentication Using Explainable Transformers and Behavioral Biometrics &bull; M.Tech Research Project
      </footer>
    </div>
  );
}

export default App;
