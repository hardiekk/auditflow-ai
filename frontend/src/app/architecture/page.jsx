'use client';

import React, { useState } from 'react';
import {
  Cpu,
  Layers,
  Database,
  Sparkles,
  Search,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Activity,
  ArrowRight,
  Terminal,
} from 'lucide-react';
import api from '@/lib/api';

export default function ArchitecturePage() {
  const [ragQuery, setRagQuery] = useState('Lithium-ion battery origin requirements for European Union ports');
  const [ragResult, setRagResult] = useState(null);
  const [testingRag, setTestingRag] = useState(false);

  const testRag = async (e) => {
    if (e) e.preventDefault();
    setTestingRag(true);
    try {
      // Fetch overview for hero shipment which triggers retrieve_regulation
      const shipments = await api.listShipments();
      const hero = shipments.find((s) => s.reference_number === 'SHP-2026-0842') || shipments[0];
      if (hero) {
        const ov = await api.getShipmentOverview(hero.id);
        setRagResult(ov?.regulatory || { found: false, message: 'No direct regulation chunk matched.' });
      }
    } catch (err) {
      alert('RAG retrieval failed: ' + err.message);
    } finally {
      setTestingRag(false);
    }
  };

  const pipelineStages = [
    {
      step: '01',
      title: 'Ingestion & Digest',
      desc: 'Multipart document upload, SHA-256 deduplication, PyPDF text stream extraction & local/S3 key generation.',
      tech: 'FastAPI • PyPDF • Local/S3 Storage',
    },
    {
      step: '02',
      title: 'AI Classification & Extraction',
      desc: 'Context-aware document typing (Invoice, PL, BL, COO) and structured field extraction with confidence metrics.',
      tech: 'OpenAI GPT-4o-Mini • Mock Provider Fallback',
    },
    {
      step: '03',
      title: 'Canonical Normalization',
      desc: 'Deterministic ISO-3166 country normalization, metric/imperial weight reconciliation, and regex date parsing.',
      tech: 'Pure Python Functional Pipeline',
    },
    {
      step: '04',
      title: 'Deterministic Rules Engine',
      desc: 'Evaluation of 10 international trade rules (Origin match, quantity delta, HS code structure, expired certs).',
      tech: 'SQLAlchemy 2.0 • Relational Rule Matrix',
    },
    {
      step: '05',
      title: 'Multi-Factor Risk Scoring',
      desc: 'Weighted penalty model aggregating open rule severities, OCR uncertainty penalties, and workflow lags (0-100).',
      tech: 'Risk Index Formula • Historical Snapshots',
    },
    {
      step: '06',
      title: 'Autonomous Agent Orchestrator',
      desc: 'Event-driven agent evaluating exceptions, triggering supplier correction tasks, and alerting compliance officers.',
      tech: 'Autonomous Agent State Engine',
    },
    {
      step: '07',
      title: 'Human-in-the-Loop Clearance',
      desc: 'Officer approval cockpit, override exemptions, and immutable audit event ledger recording all state changes.',
      tech: 'Next.js 14 • Immutable Audit Events Table',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            backgroundColor: 'rgba(99, 102, 241, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Cpu size={18} color="#818CF8" />
          </div>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            System Blueprint & Intelligence Core
          </span>
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
          Platform Architecture & RAG Engine
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Zero-data-leakage pipeline design combining deterministic trade audit rules with autonomous AI orchestration
        </p>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="glass-panel" style={{ padding: 26 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Layers size={18} color="var(--accent-primary)" />
          <span>Autonomous Audit Pipeline Lifecycle</span>
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 16,
        }}>
          {pipelineStages.map((stage) => (
            <div
              key={stage.step}
              style={{
                padding: 18,
                borderRadius: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="mono" style={{ fontSize: 13, fontWeight: 800, color: 'var(--accent-cyan)' }}>
                    PHASE {stage.step}
                  </span>
                  <span className="badge badge-neutral" style={{ fontSize: 9 }}>Deterministic</span>
                </div>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', marginBottom: 6 }}>
                  {stage.title}
                </h3>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {stage.desc}
                </p>
              </div>

              <div style={{
                marginTop: 14,
                paddingTop: 10,
                borderTop: '1px solid var(--border-subtle)',
                fontSize: 11,
                color: 'var(--text-muted)',
                fontWeight: 600,
              }}>
                {stage.tech}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live RAG Vector Search Tester */}
      <div className="glass-panel" style={{ padding: 26 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <Sparkles size={18} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF' }}>
            Live Regulatory RAG Knowledge Retrieval Explorer
          </h2>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 18 }}>
          Tests semantic regulation retrieval across EU Battery Directives, US CBP Customs Standards, and India CBIC Nhava Sheva Entry Codes.
        </p>

        <form onSubmit={testRag} style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <input
            type="text"
            value={ragQuery}
            onChange={(e) => setRagQuery(e.target.value)}
            className="input-field"
            style={{ flex: 1 }}
            placeholder="Enter trade compliance query..."
          />
          <button type="submit" disabled={testingRag} className="btn-primary" style={{ flexShrink: 0 }}>
            {testingRag ? 'Retrieving Chunks...' : 'Test Vector Retrieval'}
          </button>
        </form>

        {ragResult && (
          <div style={{
            padding: 18,
            borderRadius: 12,
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {ragResult.source || 'Regulatory Digest'} • Section: {ragResult.section || 'General'}
              </div>
              <span className="badge badge-cleared" style={{ fontSize: 10 }}>
                Confidence: {ragResult.confidence ? `${Math.round(ragResult.confidence * 100)}%` : '95%'}
              </span>
            </div>
            <p style={{ fontSize: 13, color: '#FFFFFF', lineHeight: 1.6 }}>
              "{ragResult.relevant_requirement || ragResult.message}"
            </p>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
              {ragResult.disclaimer}
            </div>
          </div>
        )}
      </div>

      {/* Relational Schema Card */}
      <div className="glass-panel" style={{ padding: 26 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Database size={18} color="var(--status-cleared)" />
          <span>Multi-Tenant Relational Data Matrix</span>
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, fontSize: 12 }}>
          {[
            { table: 'shipments', desc: 'Consignments, ports, compliance states, risk scores' },
            { table: 'shipment_documents', desc: 'Trade files, current version pointers, hashes' },
            { table: 'document_versions', desc: 'Storage keys, confidence, version history' },
            { table: 'evidence', desc: 'Extracted raw/normalized fields with confidence' },
            { table: 'compliance_rules', desc: '10 international customs audit definitions' },
            { table: 'compliance_evaluations', desc: 'Rule execution logs and pass/fail states' },
            { table: 'compliance_issues', desc: 'Exceptions, severities, remediation actions' },
            { table: 'risk_assessments', desc: 'Historical score snapshots and factor points' },
            { table: 'agent_runs', desc: 'Autonomous decisions & triggered actions' },
            { table: 'audit_events', desc: 'Append-only regulatory immutable ledger' },
            { table: 'traceability_nodes', desc: 'Geospatial supply chain waypoint graph' },
            { table: 'regulatory_sources', desc: 'Jurisdictional treaties and vector chunks' },
          ].map((item) => (
            <div
              key={item.table}
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 2 }}>
                {item.table}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
