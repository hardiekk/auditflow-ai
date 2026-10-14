'use client';

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Building,
  Shield,
  Cpu,
  Database,
  Lock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import api from '@/lib/api';

export default function SettingsPage() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeRules, setActiveRules] = useState([
    { code: 'RULE-001', name: 'Mandatory Trade Documents Completeness', severity: 'CRITICAL', status: 'ACTIVE', source: 'WCO Revised Kyoto Convention' },
    { code: 'RULE-002', name: 'Country of Origin Cross-Verification', severity: 'CRITICAL', status: 'ACTIVE', source: 'WTO Agreement on Rules of Origin' },
    { code: 'RULE-003', name: 'Quantity Reconciliation', severity: 'MEDIUM', status: 'ACTIVE', source: 'Customs Audit Standard Protocol' },
    { code: 'RULE-004', name: 'Gross Weight Reconciliation (SOLAS)', severity: 'MEDIUM', status: 'ACTIVE', source: 'SOLAS Container Weight Verification' },
    { code: 'RULE-005', name: 'Certificate Validity & Expiration Check', severity: 'HIGH', status: 'ACTIVE', source: 'ISO/IEC 17025 Conformity Standards' },
    { code: 'RULE-006', name: 'HS Tariff Code Presence', severity: 'HIGH', status: 'ACTIVE', source: 'WCO HS 2026 Nomenclature' },
    { code: 'RULE-007', name: 'HS Tariff Code Digit Format Validation', severity: 'LOW', status: 'ACTIVE', source: 'Customs Tariff Classification Guide' },
    { code: 'RULE-008', name: 'Regulated Goods Safety Conformity Mandate', severity: 'MEDIUM', status: 'ACTIVE', source: 'UN Transport of Dangerous Goods' },
    { code: 'RULE-009', name: 'Supplier Legal Entity Identity Consistency', severity: 'HIGH', status: 'ACTIVE', source: 'OECD Due Diligence Guidance' },
    { code: 'RULE-010', name: 'Chronological Invoice & Transit Timeline Check', severity: 'LOW', status: 'ACTIVE', source: 'Incoterms 2020 Rules' },
  ]);

  useEffect(() => {
    const user = api.getCurrentUser();
    if (user) setCurrentUser(user);
    else api.getMe().then(setCurrentUser).catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
          Organization & Compliance Settings
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Enterprise tenancy configuration, AI provider models, and customs rule thresholds
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Organization & User Profile */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Building size={18} color="var(--accent-primary)" />
            <h2 style={{ fontSize: 15, fontWeight: 700, color: '#FFFFFF' }}>
              Enterprise Organization Workspace
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Organization Legal Entity:</span>
              <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{currentUser?.organization_name || 'Northwind Logistics'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Current Officer:</span>
              <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{currentUser?.full_name || 'Elena Vance'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>System Role:</span>
              <span className="badge badge-cleared">{currentUser?.role || 'Admin'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Deployment Tenancy:</span>
              <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>Single-Tenant Isolated DB</span>
            </div>
          </div>
        </div>

        {/* AI Engine & Storage */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Cpu size={18} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: 15, fontWeight: 700, color: '#FFFFFF' }}>
              AI Intelligence & Storage Engine
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>AI Provider Mode:</span>
              <span style={{ fontWeight: 700, color: '#FFFFFF' }}>Auto (OpenAI with Mock Fallback)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Extraction Model:</span>
              <span className="mono" style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>gpt-4o-mini</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Storage Layer:</span>
              <span style={{ fontWeight: 600 }}>Local File Storage (/data/storage)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.02)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Confidence Threshold:</span>
              <span style={{ fontWeight: 700, color: 'var(--status-warning)' }}>0.80 (80%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Rules Table */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF' }}>
              Active International Customs Compliance Matrix (10 Rules)
            </h2>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Deterministic audit checks evaluated across multi-modal trade evidence
            </p>
          </div>
          <span className="badge badge-cleared">10 / 10 Enforced</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>
                <th style={{ padding: '10px 12px' }}>Rule Code</th>
                <th style={{ padding: '10px 12px' }}>Check Name</th>
                <th style={{ padding: '10px 12px' }}>Severity</th>
                <th style={{ padding: '10px 12px' }}>Standard Source</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {activeRules.map((r) => (
                <tr key={r.code} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '12px 12px' }}>
                    <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{r.code}</span>
                  </td>
                  <td style={{ padding: '12px 12px', fontWeight: 600, color: '#FFFFFF' }}>
                    {r.name}
                  </td>
                  <td style={{ padding: '12px 12px' }}>
                    <span className={`badge ${r.severity === 'CRITICAL' ? 'badge-blocked' : r.severity === 'HIGH' ? 'badge-warning' : 'badge-neutral'}`} style={{ fontSize: 9 }}>
                      {r.severity}
                    </span>
                  </td>
                  <td style={{ padding: '12px 12px', color: 'var(--text-secondary)', fontSize: 12 }}>
                    {r.source}
                  </td>
                  <td style={{ padding: '12px 12px', textAlign: 'right' }}>
                    <span className="badge badge-cleared" style={{ fontSize: 9 }}>Enforced</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
