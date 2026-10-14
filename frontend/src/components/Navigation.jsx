'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  ShieldAlert,
  Ship,
  CheckSquare,
  Cpu,
  Settings,
  LayoutDashboard,
  Search,
  Bell,
  LogOut,
  User,
  ChevronDown,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import api from '@/lib/api';

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const searchRef = useRef(null);
  const notifRef = useRef(null);

  // Skip rendering navigation on auth pages
  const isAuthPage = pathname === '/login' || pathname === '/register';

  useEffect(() => {
    if (isAuthPage) return;

    const user = api.getCurrentUser();
    if (user) {
      setCurrentUser(user);
    } else {
      api.getMe()
        .then((u) => {
          setCurrentUser(u);
          api.setCurrentUser(u);
        })
        .catch(() => {
          // unauthenticated
        });
    }

    // Fetch notifications
    api.getNotifications()
      .then((data) => setNotifications(data || []))
      .catch(() => {});

    // Close popups on click outside
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setSearchResults(null);
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [pathname, isAuthPage]);

  // Search handler
  const handleSearch = async (val) => {
    setSearchQuery(val);
    if (!val || val.length < 2) {
      setSearchResults(null);
      return;
    }
    setIsSearching(true);
    try {
      const res = await api.search(val);
      setSearchResults(res);
    } catch {
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleQuickSwitch = async (email, password) => {
    try {
      await api.login(email, password);
      const user = await api.getMe();
      setCurrentUser(user);
      setShowUserMenu(false);
      window.location.reload();
    } catch (e) {
      alert('Failed to switch user: ' + e.message);
    }
  };

  if (isAuthPage) return null;

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/shipments', label: 'Shipments', icon: Ship },
    { href: '/tasks', label: 'Tasks', icon: CheckSquare },
    { href: '/architecture', label: 'Architecture & AI', icon: Cpu },
    { href: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backgroundColor: 'rgba(9, 13, 22, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
    }}>
      <div style={{
        maxWidth: 1440,
        margin: '0 auto',
        padding: '0 24px',
        height: 68,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 20,
      }}>
        {/* Brand & Organization */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)',
            }}>
              <ShieldAlert size={22} color="#FFFFFF" />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: 6 }}>
                AuditFlow <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
                Autonomous Trade Audit
              </div>
            </div>
          </Link>

          {/* Org Pill & Mode Badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <div style={{
              display: 'flex',
              padding: '4px 12px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 9999,
              alignItems: 'center',
              gap: 8,
              fontSize: 12,
              color: 'var(--text-secondary)',
            }}>
              <span style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: (currentUser?.is_demo || currentUser?.organization_name === 'Northwind Logistics') ? '#F59E0B' : '#10B981',
              }} />
              <span style={{ fontWeight: 600 }}>{currentUser?.organization_name || 'Northwind Logistics'}</span>
            </div>

            {(currentUser?.is_demo || currentUser?.organization_name === 'Northwind Logistics') ? (
              <span style={{
                fontSize: 10,
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 4,
                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                color: '#FBBF24',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}>
                Demo Workspace
              </span>
            ) : (
              <span style={{
                fontSize: 10,
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 4,
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                color: '#34D399',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}>
                Live Enterprise
              </span>
            )}
          </div>
        </div>

        {/* Center Nav Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || pathname.startsWith(link.href + '/');
            return (
              <Link
                key={link.href}
                href={link.href}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 14px',
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: 600,
                  color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.25)' : '1px solid transparent',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={16} color={isActive ? '#818CF8' : 'currentColor'} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Search, Notifications & User Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {/* Global Search Bar */}
          <div ref={searchRef} style={{ position: 'relative' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-strong)',
              borderRadius: 8,
              padding: '6px 12px',
              width: 220,
              gap: 8,
            }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search shipments, docs..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                style={{
                  background: 'none',
                  border: 'none',
                  outline: 'none',
                  fontSize: 12,
                  color: '#FFFFFF',
                  width: '100%',
                }}
              />
            </div>

            {/* Instant Search Dropdown */}
            {searchResults && (
              <div style={{
                position: 'absolute',
                top: 40,
                right: 0,
                width: 320,
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                borderRadius: 10,
                padding: 12,
                boxShadow: '0 15px 35px rgba(0,0,0,0.5)',
                zIndex: 100,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                  Search Results
                </div>
                {searchResults.shipments?.length > 0 ? (
                  searchResults.shipments.map((s) => (
                    <Link
                      key={s.id}
                      href={`/shipments/${s.id}`}
                      onClick={() => setSearchResults(null)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '6px 8px',
                        borderRadius: 6,
                        fontSize: 13,
                        marginBottom: 4,
                        backgroundColor: 'rgba(255,255,255,0.03)',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{s.reference_number}</span>
                      <ExternalLink size={12} color="var(--text-muted)" />
                    </Link>
                  ))
                ) : (
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '6px 0' }}>No matching records found.</div>
                )}
              </div>
            )}
          </div>

          {/* Notifications Dropdown */}
          <div ref={notifRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              style={{
                position: 'relative',
                width: 36,
                height: 36,
                borderRadius: 8,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Bell size={17} color="var(--text-secondary)" />
              {notifications.length > 0 && (
                <span style={{
                  position: 'absolute',
                  top: 6,
                  right: 6,
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: 'var(--status-blocked)',
                  boxShadow: '0 0 8px var(--status-blocked)',
                }} />
              )}
            </button>

            {showNotifications && (
              <div style={{
                position: 'absolute',
                top: 44,
                right: 0,
                width: 350,
                maxHeight: 420,
                overflowY: 'auto',
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                borderRadius: 12,
                padding: 14,
                boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
                zIndex: 100,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>System Notifications</div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{notifications.length} alerts</span>
                </div>

                {notifications.length === 0 ? (
                  <div style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
                    No unread notifications.
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 8,
                        backgroundColor: 'rgba(255,255,255,0.03)',
                        borderLeft: `3px solid ${n.kind === 'critical_issue' ? 'var(--status-blocked)' : 'var(--accent-primary)'}`,
                        marginBottom: 8,
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: 13, color: '#FFFFFF', marginBottom: 3 }}>
                        {n.title}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        {n.body}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* User Profile Pill & Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '5px 12px 5px 6px',
                borderRadius: 9999,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-strong)',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: 12,
              }}>
                {currentUser?.full_name ? currentUser.full_name[0] : 'E'}
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 12, fontWeight: 700, lineHeight: 1.2 }}>
                  {currentUser?.full_name?.split(' ')[0] || 'Elena'}
                </div>
                <div style={{ fontSize: 10, color: 'var(--accent-cyan)', fontWeight: 600 }}>
                  {currentUser?.role || 'Admin'}
                </div>
              </div>
              <ChevronDown size={14} color="var(--text-muted)" />
            </button>

            {showUserMenu && (
              <div style={{
                position: 'absolute',
                top: 44,
                right: 0,
                width: 260,
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-strong)',
                borderRadius: 12,
                padding: 12,
                boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
                zIndex: 100,
              }}>
                <div style={{ padding: '4px 8px 10px 8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{currentUser?.full_name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{currentUser?.email}</div>
                  <div style={{ marginTop: 4 }}>
                    <span className="badge badge-cleared" style={{ fontSize: 9 }}>
                      {currentUser?.role}
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '4px 8px' }}>
                  Demo Persona Switcher
                </div>
                <button
                  onClick={() => handleQuickSwitch('admin@auditflow.demo', 'AuditFlow!demo')}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '8px 10px',
                    fontSize: 12,
                    color: 'var(--text-secondary)',
                    borderRadius: 6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <Sparkles size={14} color="#818CF8" />
                  <span>Elena Vance (Admin)</span>
                </button>
                <button
                  onClick={() => handleQuickSwitch('reviewer@auditflow.demo', 'AuditFlow!demo')}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '8px 10px',
                    fontSize: 12,
                    color: 'var(--text-secondary)',
                    borderRadius: 6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <Sparkles size={14} color="#38BDF8" />
                  <span>Marcus Chen (Reviewer)</span>
                </button>

                <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: 8, paddingTop: 8 }}>
                  <button
                    onClick={() => api.logout()}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '8px 10px',
                      fontSize: 12,
                      color: 'var(--status-blocked)',
                      borderRadius: 6,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <LogOut size={14} color="var(--status-blocked)" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
