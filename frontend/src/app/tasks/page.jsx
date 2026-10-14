'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  CheckSquare,
  Plus,
  Clock,
  AlertCircle,
  CheckCircle2,
  Ship,
  User,
  ArrowRight,
  X,
  Sparkles,
} from 'lucide-react';
import api from '@/lib/api';

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM',
    shipment_id: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchTasks = async () => {
    try {
      const data = await api.listTasks();
      setTasks(data || []);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await api.updateTask(taskId, { status: newStatus });
      await fetchTasks();
    } catch (err) {
      alert('Failed to update task: ' + err.message);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.createTask(createForm);
      setShowCreateModal(false);
      setCreateForm({ title: '', description: '', priority: 'MEDIUM', shipment_id: '' });
      await fetchTasks();
    } catch (err) {
      alert('Failed to create task: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (filterStatus === 'ALL') return true;
    return t.status === filterStatus;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
            Compliance & Supplier Action Tasks
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            Remediation workflows, supplier requests, and document correction action items
          </p>
        </div>

        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus size={16} />
          <span>New Remediation Task</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        {[
          { id: 'ALL', label: `All Tasks (${tasks.length})` },
          { id: 'WAITING_FOR_SUPPLIER', label: 'Waiting For Supplier' },
          { id: 'OPEN', label: 'Open' },
          { id: 'IN_PROGRESS', label: 'In Progress' },
          { id: 'COMPLETED', label: 'Completed' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterStatus(tab.id)}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 600,
              color: filterStatus === tab.id ? '#FFFFFF' : 'var(--text-secondary)',
              backgroundColor: filterStatus === tab.id ? 'var(--accent-primary)' : 'rgba(255, 255, 255, 0.04)',
              border: filterStatus === tab.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
              transition: 'all 0.15s ease',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading active compliance tasks...
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="glass-panel" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            <CheckCircle2 size={32} color="var(--status-cleared)" style={{ margin: '0 auto 8px' }} />
            <div>No tasks found under selected filter.</div>
          </div>
        ) : (
          filteredTasks.map((t) => (
            <div
              key={t.id}
              className="glass-panel glass-panel-hover"
              style={{
                padding: '18px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 16,
                borderLeft: `4px solid ${
                  t.priority === 'CRITICAL' ? 'var(--status-blocked)' : t.priority === 'HIGH' ? 'var(--status-warning)' : 'var(--accent-primary)'
                }`,
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontWeight: 800, fontSize: 14, color: '#FFFFFF' }}>{t.title}</span>
                  <span className={`badge ${t.priority === 'CRITICAL' ? 'badge-blocked' : t.priority === 'HIGH' ? 'badge-warning' : 'badge-neutral'}`} style={{ fontSize: 9 }}>
                    {t.priority}
                  </span>
                  <span className="badge badge-neutral" style={{ fontSize: 9 }}>
                    {t.status}
                  </span>
                </div>

                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {t.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                  {t.shipment_id && (
                    <Link href={`/shipments/${t.shipment_id}`} style={{ color: 'var(--accent-cyan)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Ship size={12} />
                      <span>View Linked Shipment</span>
                    </Link>
                  )}
                  <span>Due: {t.due_date ? new Date(t.due_date).toLocaleDateString() : 'Immediate'}</span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                {t.status !== 'COMPLETED' ? (
                  <button
                    onClick={() => handleStatusChange(t.id, 'COMPLETED')}
                    className="btn-success"
                    style={{ padding: '6px 12px', fontSize: 12 }}
                  >
                    <CheckCircle2 size={14} />
                    <span>Mark Done</span>
                  </button>
                ) : (
                  <span className="badge badge-cleared" style={{ fontSize: 11 }}>
                    ✓ Completed
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 460, padding: 26, borderRadius: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div style={{ fontSize: 18, fontWeight: 800 }}>Create Remediation Task</div>
              <button onClick={() => setShowCreateModal(false)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Task Title
                </label>
                <input
                  type="text"
                  required
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  placeholder="e.g. Request updated scale ticket from carrier"
                  className="input-field"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Description / Action Required
                </label>
                <textarea
                  rows={3}
                  required
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Instructions for supplier or logistics coordinator..."
                  className="input-field"
                  style={{ resize: 'vertical' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Priority Level
                </label>
                <select
                  value={createForm.priority}
                  onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                  className="input-field"
                >
                  <option value="CRITICAL">CRITICAL (Immediate Hold)</option>
                  <option value="HIGH">HIGH (Expedite Response)</option>
                  <option value="MEDIUM">MEDIUM (Standard Review)</option>
                  <option value="LOW">LOW (Informational)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="btn-primary">
                  {submitting ? 'Creating...' : 'Create Action Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
