'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ShieldCheck, ArrowRight, Sparkles, Lock, Mail, AlertCircle } from 'lucide-react';
import api from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@auditflow.demo');
  const [password, setPassword] = useState('AuditFlow!demo');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.login(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const setDemoUser = (userEmail, userPass) => {
    setEmail(userEmail);
    setPassword(userPass);
    setError('');
  };

  return (
    <div style={{
      minHeight: '85vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px 0',
    }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56,
            height: 56,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
            marginBottom: 16,
          }}>
            <ShieldCheck size={32} color="#FFFFFF" />
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.03em', color: '#FFFFFF', marginBottom: 8 }}>
            AuditFlow <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
            Autonomous Trade Compliance & Audit Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel" style={{ padding: 32, borderRadius: 16 }}>
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 14px',
              borderRadius: 10,
              backgroundColor: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.4)',
              color: '#FDA4AF',
              fontSize: 13,
              marginBottom: 20,
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Business Email
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  style={{ paddingLeft: 40 }}
                  placeholder="admin@auditflow.demo"
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field"
                  style={{ paddingLeft: 40 }}
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{ width: '100%', padding: '12px 0', marginTop: 4, fontSize: 15 }}
            >
              {loading ? 'Authenticating...' : (
                <>
                  <span>Sign In to Command Center</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Logins Preset */}
          <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{
              fontSize: 11,
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 10,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}>
              <Sparkles size={13} color="#818CF8" />
              <span>Instant Demo Credentials</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <button
                type="button"
                onClick={() => setDemoUser('admin@auditflow.demo', 'AuditFlow!demo')}
                style={{
                  padding: '9px 10px',
                  borderRadius: 8,
                  backgroundColor: 'rgba(99, 102, 241, 0.1)',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  color: '#C7D2FE',
                  fontSize: 12,
                  fontWeight: 600,
                  textAlign: 'center',
                }}
              >
                Elena Vance (Admin)
              </button>

              <button
                type="button"
                onClick={() => setDemoUser('reviewer@auditflow.demo', 'AuditFlow!demo')}
                style={{
                  padding: '9px 10px',
                  borderRadius: 8,
                  backgroundColor: 'rgba(6, 182, 212, 0.1)',
                  border: '1px solid rgba(6, 182, 212, 0.25)',
                  color: '#A5F3FC',
                  fontSize: 12,
                  fontWeight: 600,
                  textAlign: 'center',
                }}
              >
                Marcus Chen (Auditor)
              </button>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
          Don't have an enterprise workspace?{' '}
          <Link href="/register" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
            Register Organization
          </Link>
        </div>
      </div>
    </div>
  );
}
