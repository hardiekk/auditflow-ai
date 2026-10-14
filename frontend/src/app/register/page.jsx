'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ShieldAlert, ArrowRight, Building, User, Mail, Lock, AlertCircle } from 'lucide-react';
import api from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    organization_name: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.register(formData);
      router.push('/dashboard');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '85vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px 0',
    }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)',
            marginBottom: 14,
          }}>
            <ShieldAlert size={28} color="#FFFFFF" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#FFFFFF', marginBottom: 6 }}>
            Deploy New Organization
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Initialize isolated enterprise compliance workspace
          </p>
        </div>

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
              marginBottom: 18,
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Organization Legal Entity Name
              </label>
              <div style={{ position: 'relative' }}>
                <Building size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="text"
                  required
                  name="organization_name"
                  value={formData.organization_name}
                  onChange={handleChange}
                  className="input-field"
                  style={{ paddingLeft: 40 }}
                  placeholder="e.g. Apex Global Logistics Ltd"
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Admin Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="text"
                  required
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="input-field"
                  style={{ paddingLeft: 40 }}
                  placeholder="e.g. Sarah Jenkins"
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Work Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="email"
                  required
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="input-field"
                  style={{ paddingLeft: 40 }}
                  placeholder="sarah@apexlogistics.com"
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                Password (min. 8 chars)
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 14, top: 13 }} />
                <input
                  type="password"
                  required
                  minLength={8}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
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
              style={{ width: '100%', padding: '12px 0', marginTop: 8 }}
            >
              {loading ? 'Setting up Workspace...' : (
                <>
                  <span>Create Workspace & Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        </div>

        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 12, color: 'var(--text-muted)' }}>
          Already configured?{' '}
          <Link href="/login" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
