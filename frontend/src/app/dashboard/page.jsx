'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Ship,
  Sparkles,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Filter,
} from 'lucide-react';
import api from '@/lib/api';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [queue, setQueue] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [sumData, queueData, shpData] = await Promise.all([
        api.getDashboardSummary(),
        api.getQueue(),
        api.listShipments(),
      ]);
      setSummary(sumData);
      setQueue(queueData);
      setShipments(shpData || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CLEARED':
        return <span className="badge badge-cleared">Cleared</span>;
      case 'BLOCKED':
        return (
          <span className="badge badge-blocked">
            <span className="pulse-dot pulse-red" />
            Blocked
          </span>
        );
      case 'WARNING':
        return <span className="badge badge-warning">Warning</span>;
      case 'READY_FOR_REVIEW':
        return <span className="badge badge-ready">Review Ready</span>;
      case 'UNDER_REVIEW':
        return <span className="badge badge-processing">Under Review</span>;
      default:
        return <span className="badge badge-neutral">{status}</span>;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div className="skeleton" style={{ height: 120, width: '100%' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton" style={{ height: 110 }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: 350, width: '100%' }} />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Top Banner */}
      <div className="glass-panel" style={{
        padding: '24px 28px',
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span className="badge badge-cleared" style={{ textTransform: 'none', fontSize: 12 }}>
              <Sparkles size={13} /> Active Autonomous AI Auditor
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Engine: Deterministic Customs Audit + GPT-4o-Mini Fallback
            </span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', color: '#FFFFFF' }}>
            Cross-Border Trade Compliance Cockpit
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            Real-time multi-jurisdiction trade document extraction, origin reconciliation, and border clearance risk routing.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={handleRefresh}
            className="btn-secondary"
            disabled={refreshing}
            style={{ fontSize: 13 }}
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Syncing...' : 'Sync Live Data'}</span>
          </button>
          <Link href="/shipments" className="btn-primary" style={{ fontSize: 13 }}>
            <Ship size={15} />
            <span>Register Shipment</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 16,
      }}>
        {/* KPI 1: Blocked (Customs Hold) */}
        <div className="glass-panel" style={{
          padding: '20px 22px',
          borderLeft: '4px solid var(--status-blocked)',
          background: summary?.blocked > 0 ? 'rgba(244, 63, 94, 0.06)' : 'var(--bg-glass)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Customs Blocked
            </span>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: 'var(--status-blocked-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <ShieldAlert size={18} color="var(--status-blocked)" />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 32, fontWeight: 800, color: summary?.blocked > 0 ? 'var(--status-blocked)' : '#FFFFFF' }}>
              {summary?.blocked ?? 0}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>critical holds</span>
          </div>
          <div style={{ fontSize: 11, color: summary?.blocked > 0 ? '#FDA4AF' : 'var(--text-muted)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
            {summary?.blocked > 0 && <span className="pulse-dot pulse-red" />}
            {summary?.blocked > 0 ? 'Immediate origin/doc conflict' : 'No shipments currently detained'}
          </div>
        </div>

        {/* KPI 2: Needs Review */}
        <div className="glass-panel" style={{
          padding: '20px 22px',
          borderLeft: '4px solid var(--status-ready)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Pending Review
            </span>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: 'var(--status-ready-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Clock size={18} color="var(--status-ready)" />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 32, fontWeight: 800, color: '#FFFFFF' }}>
              {summary?.needs_review ?? 0}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>shipments</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--status-ready)', marginTop: 6 }}>
            Ready for human officer clearance
          </div>
        </div>

        {/* KPI 3: High Risk */}
        <div className="glass-panel" style={{
          padding: '20px 22px',
          borderLeft: '4px solid var(--status-warning)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Elevated Risk Score
            </span>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: 'var(--status-warning-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <AlertTriangle size={18} color="var(--status-warning)" />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 32, fontWeight: 800, color: '#FFFFFF' }}>
              {summary?.high_risk ?? 0}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>above score 50</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
            Multi-factor weighted assessment
          </div>
        </div>

        {/* KPI 4: Documents Processed */}
        <div className="glass-panel" style={{
          padding: '20px 22px',
          borderLeft: '4px solid var(--accent-cyan)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Extracted Docs
            </span>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: 'var(--accent-cyan-glow)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <FileText size={18} color="var(--accent-cyan)" />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 32, fontWeight: 800, color: '#FFFFFF' }}>
              {summary?.documents_processed ?? 0}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>OCR verified</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--accent-cyan)', marginTop: 6 }}>
            Invoices, Packing Lists, BLs, COOs
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Left Column: Priority Exception Queue & Recent Shipments */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Priority Exception Queue */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF' }}>
                  Critical Exceptions & Compliance Queue
                </h2>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  Unresolved rule discrepancies requiring officer determination or supplier correction
                </p>
              </div>
              <span className="badge badge-blocked">
                {queue?.items?.length ?? 0} Active
              </span>
            </div>

            {queue?.items?.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={32} color="var(--status-cleared)" style={{ margin: '0 auto 8px' }} />
                <div>All compliance exceptions resolved. Zero open blocks.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {queue?.items?.slice(0, 4).map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: 14,
                      borderRadius: 10,
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 16,
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{
                        marginTop: 2,
                        width: 24,
                        height: 24,
                        borderRadius: 6,
                        backgroundColor: item.severity === 'CRITICAL' ? 'var(--status-blocked-bg)' : 'var(--status-warning-bg)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}>
                        <ShieldAlert size={14} color={item.severity === 'CRITICAL' ? 'var(--status-blocked)' : 'var(--status-warning)'} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 700, fontSize: 14, color: '#FFFFFF' }}>{item.title}</span>
                          <span className={`badge ${item.severity === 'CRITICAL' ? 'badge-blocked' : 'badge-warning'}`} style={{ fontSize: 9 }}>
                            {item.severity}
                          </span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                          Shipment: <strong style={{ color: '#FFFFFF' }}>{item.shipment_ref}</strong> • Dest: {item.destination}
                        </div>
                        {item.recommended_action && (
                          <div style={{ fontSize: 11, color: 'var(--accent-cyan)', marginTop: 4 }}>
                            → {item.recommended_action}
                          </div>
                        )}
                      </div>
                    </div>

                    <Link
                      href={`/shipments/${item.shipment_id}`}
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: 12, flexShrink: 0 }}
                    >
                      <span>Resolve</span>
                      <ChevronRight size={14} />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Shipments Table */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF' }}>
                  Monitored Inbound Shipments
                </h2>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  Real-time customs tracking and automated risk indices
                </p>
              </div>
              <Link href="/shipments" style={{ fontSize: 12, color: 'var(--accent-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                <span>View All ({shipments.length})</span>
                <ChevronRight size={14} />
              </Link>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '10px 12px' }}>Reference</th>
                    <th style={{ padding: '10px 12px' }}>Origin / Destination</th>
                    <th style={{ padding: '10px 12px' }}>Carrier</th>
                    <th style={{ padding: '10px 12px' }}>Compliance Status</th>
                    <th style={{ padding: '10px 12px' }}>Risk Score</th>
                    <th style={{ padding: '10px 12px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {shipments.slice(0, 5).map((s) => (
                    <tr
                      key={s.id}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.04)',
                        transition: 'background-color 0.15s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '12px 12px', fontWeight: 700 }}>
                        <Link href={`/shipments/${s.id}`} style={{ color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span>{s.reference_number}</span>
                          {s.reference_number === 'SHP-2026-0842' && (
                            <span style={{ fontSize: 10, backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818CF8', padding: '1px 6px', borderRadius: 4 }}>
                              HERO
                            </span>
                          )}
                        </Link>
                      </td>
                      <td style={{ padding: '12px 12px', color: 'var(--text-secondary)' }}>
                        <span style={{ fontWeight: 600, color: '#FFFFFF' }}>{s.origin_country || '—'}</span>
                        <span style={{ margin: '0 6px', color: 'var(--text-muted)' }}>→</span>
                        <span style={{ fontWeight: 600, color: '#FFFFFF' }}>{s.destination_country || '—'}</span>
                      </td>
                      <td style={{ padding: '12px 12px', color: 'var(--text-secondary)' }}>
                        {s.carrier || 'Unassigned'}
                      </td>
                      <td style={{ padding: '12px 12px' }}>
                        {getStatusBadge(s.compliance_status)}
                      </td>
                      <td style={{ padding: '12px 12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 60,
                            height: 6,
                            borderRadius: 3,
                            backgroundColor: 'rgba(255,255,255,0.1)',
                            overflow: 'hidden',
                          }}>
                            <div style={{
                              width: `${Math.min(s.risk_score, 100)}%`,
                              height: '100%',
                              backgroundColor: s.risk_score >= 50 ? 'var(--status-blocked)' : s.risk_score >= 20 ? 'var(--status-warning)' : 'var(--status-cleared)',
                            }} />
                          </div>
                          <span style={{ fontWeight: 700, fontSize: 12 }}>{s.risk_score}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px 12px', textAlign: 'right' }}>
                        <Link href={`/shipments/${s.id}`} className="btn-secondary" style={{ padding: '5px 10px', fontSize: 11 }}>
                          Inspect
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Analytics & Rule Distribution */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Compliance Status Distribution */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', marginBottom: 14 }}>
              Fleet Compliance Breakdown
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {summary?.state_distribution && Object.entries(summary.state_distribution).map(([state, count]) => {
                const total = summary.total_shipments || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={state}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600 }}>{state}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{count} ({pct}%)</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                      <div style={{
                        width: `${pct}%`,
                        height: '100%',
                        backgroundColor: state === 'CLEARED' ? 'var(--status-cleared)' : state === 'BLOCKED' ? 'var(--status-blocked)' : state === 'WARNING' ? 'var(--status-warning)' : 'var(--status-ready)',
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Issue Categories */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', marginBottom: 14 }}>
              Active Rule Violations
            </h3>
            {summary?.issue_categories && Object.keys(summary.issue_categories).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(summary.issue_categories).map(([cat, count]) => (
                  <div key={cat} style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{cat}</span>
                    <span className="badge badge-blocked" style={{ fontSize: 10 }}>{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '16px 0' }}>
                No active rule violations detected.
              </div>
            )}
          </div>

          {/* Quick Demo Guidance Card */}
          <div className="glass-panel" style={{
            padding: 20,
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 13, color: '#A5F3FC', marginBottom: 6 }}>
              <Sparkles size={16} />
              <span>Hero Demonstration Scenario</span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Inspect shipment <strong style={{ color: '#FFFFFF' }}>SHP-2026-0842</strong>. It is currently blocked due to a Country of Origin contradiction (Invoice says Germany, COO says Vietnam).
            </p>
            <div style={{ marginTop: 12 }}>
              <Link href="/shipments" className="btn-primary" style={{ width: '100%', fontSize: 12, padding: '8px 0' }}>
                Inspect Blocked Shipment →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
