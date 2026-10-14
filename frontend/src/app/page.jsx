'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const token = api.getToken();
    if (token) {
      router.replace('/dashboard');
    } else {
      router.replace('/login');
    }
  }, [router]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '70vh',
      flexDirection: 'column',
      gap: 16,
    }}>
      <div className="skeleton" style={{ width: 48, height: 48, borderRadius: 12 }} />
      <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>Connecting to AuditFlow AI Platform...</div>
    </div>
  );
}
