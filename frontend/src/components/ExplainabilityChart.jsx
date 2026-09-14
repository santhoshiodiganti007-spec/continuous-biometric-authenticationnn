import React from 'react';
import { Cpu, HelpCircle, Layers } from 'lucide-react';

export const ExplainabilityChart = ({ features = [], attentionWeights = [] }) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          Explainable AI (XAI) Feature Attribution
        </h3>
        <span className="text-xs text-slate-500 flex items-center gap-1">
          <HelpCircle className="w-3.5 h-3.5" />
          Sensitivity & SHAP Analysis
        </span>
      </div>

      <div className="space-y-4">
        {features && features.length > 0 ? (
          features.map((item, index) => {
            const importancePct = Math.round(item.importance * 100);
            return (
              <div key={index} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-300">
                    {item.description || item.feature}
                  </span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {importancePct}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(4, Math.min(100, importancePct))}%` }}
                  />
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-6 text-slate-500 text-xs">
            Awaiting sufficient behavioral interaction window for attribution analysis...
          </div>
        )}
      </div>

      {attentionWeights && attentionWeights.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-800/80">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <h4 className="text-xs font-semibold uppercase text-slate-400">
              Transformer Self-Attention Distribution
            </h4>
          </div>
          <div className="flex items-end gap-1.5 h-12 pt-2">
            {attentionWeights.map((w, idx) => {
              const heightPct = Math.max(15, Math.min(100, Math.round(w * 100 * 3)));
              return (
                <div
                  key={idx}
                  title={`Step ${idx + 1}: ${Math.round(w * 100)}% attention`}
                  className="flex-1 bg-cyan-500/40 hover:bg-cyan-400 rounded-t transition-all duration-300 cursor-pointer"
                  style={{ height: `${heightPct}%` }}
                />
              );
            })}
          </div>
          <p className="text-[10px] text-slate-500 mt-1 text-right">
            Sequential Attention over temporal tokens
          </p>
        </div>
      )}
    </div>
  );
};
