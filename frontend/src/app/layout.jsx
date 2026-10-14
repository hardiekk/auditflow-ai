import './globals.css';
import Navigation from '@/components/Navigation';

export const metadata = {
  title: 'AuditFlow AI — Autonomous Trade Compliance & Cross-Border Audit Intelligence',
  description: 'AI-driven trade document processing, automated compliance verification, and multi-factor risk intelligence platform.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Navigation />
        <main style={{ maxWidth: 1440, margin: '0 auto', padding: '24px' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
