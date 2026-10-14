'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Ship,
  Search,
  Plus,
  Filter,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  X,
} from 'lucide-react';
import api from '@/lib/api';

export default function ShipmentsListPage() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterState, setFilterState] = useState('ALL');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    reference_number: '',
    origin_country: 'DE',
    destination_country: 'IN',
    origin_port: 'Port of Hamburg',
    destination_port: 'Port of Nhava Sheva',
    carrier: 'Maersk Line',
  });
  const [creating, setCreating] = useState(false);

  const fetchShipments = async (q = '') => {
    try {
      const data = await api.listShipments(q);
      setShipments(data || []);
    } catch (err) {
      console.error('Error fetching shipments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments(search);
  }, [search]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const created = await api.createShipment(createForm);
      setShowCreateModal(false);
      fetchShipments();
      window.location.href = `/shipments/${created.id}`;
    } catch (err) {
      alert('Failed to register shipment: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  const filtered = shipments.filter((s) => {
    if (filterState === 'ALL') return true;
    return s.compliance_status === filterState;
  });

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
            Inbound & Outbound Shipments
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            Monitor consignments across border checkpoints, tariff regimes, and customs audits
          </p>
        </div>

        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus size={16} />
          <span>Register New Consignment</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          backgroundColor: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-strong)',
          borderRadius: 8,
          padding: '8px 14px',
          width: 320,
        }}>
          <Search size={15} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search by reference, port, carrier..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              background: 'none',
              border: 'none',
              outline: 'none',
              fontSize: 13,
              color: '#FFFFFF',
              width: '100%',
            }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          {[
            { id: 'ALL', label: 'All Fleet' },
            { id: 'BLOCKED', label: 'Blocked Holds' },
            { id: 'WARNING', label: 'Warnings' },
            { id: 'READY_FOR_REVIEW', label: 'Review Ready' },
            { id: 'CLEARED', label: 'Cleared' },
          ].map((pill) => (
            <button
              key={pill.id}
              onClick={() => setFilterState(pill.id)}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                color: filterState === pill.id ? '#FFFFFF' : 'var(--text-secondary)',
                backgroundColor: filterState === pill.id ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.04)',
                border: filterState === pill.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                transition: 'all 0.15s ease',
              }}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </div>

      {/* Shipments Data Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading shipments database...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
            No consignments found matching the criteria.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
              <thead>
                <tr style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  color: 'var(--text-muted)',
                  fontSize: 11,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  <th style={{ padding: '14px 18px' }}>Reference Number</th>
                  <th style={{ padding: '14px 18px' }}>Origin → Destination</th>
                  <th style={{ padding: '14px 18px' }}>Carrier & Line</th>
                  <th style={{ padding: '14px 18px' }}>Compliance Status</th>
                  <th style={{ padding: '14px 18px' }}>Risk Score</th>
                  <th style={{ padding: '14px 18px' }}>Doc Completeness</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right' }}>Cockpit</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr
                    key={s.id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'background-color 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '16px 18px' }}>
                      <Link href={`/shipments/${s.id}`} style={{ fontWeight: 700, color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span>{s.reference_number}</span>
                        {s.reference_number === 'SHP-2026-0842' && (
                          <span style={{
                            fontSize: 10,
                            padding: '2px 6px',
                            borderRadius: 4,
                            backgroundColor: 'rgba(99, 102, 241, 0.2)',
                            color: '#818CF8',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                          }}>
                            HERO DEMO
                          </span>
                        )}
                      </Link>
                    </td>

                    <td style={{ padding: '16px 18px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{s.origin_country || 'DE'}</span>
                        <span style={{ color: 'var(--text-muted)' }}>→</span>
                        <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{s.destination_country || 'IN'}</span>
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                        {s.origin_port?.split(',')[0]} → {s.destination_port?.split(',')[0]}
                      </div>
                    </td>

                    <td style={{ padding: '16px 18px', color: 'var(--text-secondary)' }}>
                      <div>{s.carrier || 'Unassigned'}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>ETA: {s.estimated_arrival || 'En route'}</div>
                    </td>

                    <td style={{ padding: '16px 18px' }}>
                      {getStatusBadge(s.compliance_status)}
                    </td>

                    <td style={{ padding: '16px 18px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 60,
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'rgba(255,255,255,0.08)',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${Math.min(s.risk_score, 100)}%`,
                            height: '100%',
                            backgroundColor: s.risk_score >= 50 ? 'var(--status-blocked)' : s.risk_score >= 20 ? 'var(--status-warning)' : 'var(--status-cleared)',
                          }} />
                        </div>
                        <span style={{ fontWeight: 700, fontSize: 13, color: s.risk_score >= 50 ? '#FDA4AF' : '#FFFFFF' }}>
                          {s.risk_score}
                        </span>
                      </div>
                    </td>

                    <td style={{ padding: '16px 18px' }}>
                      <div style={{ fontSize: 12, fontWeight: 600 }}>{s.document_completeness ?? 100}%</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Verified</div>
                    </td>

                    <td style={{ padding: '16px 18px', textAlign: 'right' }}>
                      <Link href={`/shipments/${s.id}`} className="btn-secondary" style={{ padding: '7px 14px', fontSize: 12 }}>
                        <span>Open Cockpit</span>
                        <ArrowRight size={13} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal to Register New Shipment */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: 20,
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 500, padding: 28, borderRadius: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div style={{ fontSize: 18, fontWeight: 800 }}>Register Consignment Manifest</div>
              <button onClick={() => setShowCreateModal(false)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Consignment Reference Number
                </label>
                <input
                  type="text"
                  required
                  value={createForm.reference_number}
                  onChange={(e) => setCreateForm({ ...createForm, reference_number: e.target.value })}
                  placeholder="e.g. SHP-2026-1049"
                  className="input-field"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Origin Country Code
                  </label>
                  <input
                    type="text"
                    required
                    value={createForm.origin_country}
                    onChange={(e) => setCreateForm({ ...createForm, origin_country: e.target.value })}
                    placeholder="DE"
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Destination Country Code
                  </label>
                  <input
                    type="text"
                    required
                    value={createForm.destination_country}
                    onChange={(e) => setCreateForm({ ...createForm, destination_country: e.target.value })}
                    placeholder="IN"
                    className="input-field"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Origin Port
                  </label>
                  <input
                    type="text"
                    value={createForm.origin_port}
                    onChange={(e) => setCreateForm({ ...createForm, origin_port: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Destination Port
                  </label>
                  <input
                    type="text"
                    value={createForm.destination_port}
                    onChange={(e) => setCreateForm({ ...createForm, destination_port: e.target.value })}
                    className="input-field"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Ocean Carrier / Forwarder
                </label>
                <input
                  type="text"
                  value={createForm.carrier}
                  onChange={(e) => setCreateForm({ ...createForm, carrier: e.target.value })}
                  placeholder="Maersk Line"
                  className="input-field"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 10 }}>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={creating} className="btn-primary">
                  {creating ? 'Registering...' : 'Register & Launch Cockpit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
