import React, { useState } from 'react';
import { Shield, Lock, User as UserIcon, ArrowRight, AlertCircle } from 'lucide-react';
import { authAPI } from '../services/api';

export const Login = ({ onLoginSuccess, onNavigateToRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 text-slate-100">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-cyan-950/40 relative">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl text-cyan-400 mb-3 shadow-lg shadow-cyan-500/20">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white">Biometric Continuous Auth</h1>
          <p className="text-xs text-slate-400 mt-1">Explainable Transformers & Behavioral Dynamics</p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-2.5 text-xs text-rose-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Username</label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="researcher_id"
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-500 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-600 focus:outline-none transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-500 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-600 focus:outline-none transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-xl font-bold text-xs uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 transition shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Secure Login'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          New participant or researcher?{' '}
          <button
            onClick={onNavigateToRegister}
            className="text-cyan-400 hover:underline font-medium"
          >
            Create Research Account
          </button>
        </div>
      </div>
    </div>
  );
};
