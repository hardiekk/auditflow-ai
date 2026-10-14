'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Ship,
  ArrowLeft,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Clock,
  Download,
  Upload,
  RefreshCw,
  Sparkles,
  Bot,
  Activity,
  Layers,
  History,
  FileCheck,
  Check,
  X,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  Info,
  MapPin,
  Anchor,
  Compass,
} from 'lucide-react';
import api from '@/lib/api';

export default function ShipmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;

  const [shipment, setShipment] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [risk, setRisk] = useState(null);
  const [riskHistory, setRiskHistory] = useState([]);
  const [traceability, setTraceability] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [agentActivity, setAgentActivity] = useState(null);
  const [overview, setOverview] = useState(null);

  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Modals
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewDecision, setReviewDecision] = useState('approve');
  const [reviewComment, setReviewComment] = useState('');

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [replaceDocId, setReplaceDocId] = useState(null);
  const [replaceReason, setReplaceReason] = useState('');

  const [inspectDoc, setInspectDoc] = useState(null);
  const [inspectIssue, setInspectIssue] = useState(null);
  const [inspectEvidence, setInspectEvidence] = useState(null);

  const loadAllData = async () => {
    if (!id) return;
    try {
      const [
        shpData,
        compData,
        docsData,
        riskData,
        riskHistData,
        traceData,
        auditData,
        agentData,
        overData,
      ] = await Promise.all([
        api.getShipment(id),
        api.getShipmentCompliance(id).catch(() => null),
        api.listShipmentDocuments(id).catch(() => []),
        api.getShipmentRisk(id).catch(() => null),
        api.getShipmentRiskHistory(id).catch(() => []),
        api.getShipmentTraceability(id).catch(() => null),
        api.getShipmentAuditTrail(id).catch(() => []),
        api.getShipmentAgentActivity(id).catch(() => null),
        api.getShipmentOverview(id).catch(() => null),
      ]);

      setShipment(shpData);
      setCompliance(compData);
      setDocuments(docsData || []);
      setRisk(riskData);
      setRiskHistory(riskHistData || []);
      setTraceability(traceData);
      setAuditEvents(auditData || []);
      setAgentActivity(agentData);
      setOverview(overData);
    } catch (err) {
      console.error('Failed to load shipment:', err);
    } finally {
      setLoading(false);
      setActionLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [id]);

  // Review & Clearance
  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.reviewShipment(id, { decision: reviewDecision, comment: reviewComment });
      setShowReviewModal(false);
      setReviewComment('');
      await loadAllData();
    } catch (err) {
      alert('Review action error: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // Re-run compliance
  const handleRerunCompliance = async () => {
    setActionLoading(true);
    try {
      await api.runShipmentCompliance(id);
      await loadAllData();
    } catch (err) {
      alert('Failed to re-run compliance: ' + err.message);
      setActionLoading(false);
    }
  };

  // Re-run agent
  const handleRerunAgent = async () => {
    setActionLoading(true);
    try {
      await api.runShipmentAgent(id);
      await loadAllData();
    } catch (err) {
      alert('Agent run error: ' + err.message);
      setActionLoading(false);
    }
  };

  // File Upload / Replacement
  const handleUploadSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!uploadFile) {
      alert('Please select a document file');
      return;
    }
    setActionLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (replaceDocId) {
      formData.append('replace_document_id', replaceDocId);
      formData.append('reason', replaceReason || 'Corrected trade document version');
    }
    try {
      await api.uploadShipmentDocument(id, formData);
      setShowUploadModal(false);
      setUploadFile(null);
      setReplaceDocId(null);
      setReplaceReason('');
      await loadAllData();
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // Hero Quick Action: Replace with German COO v2
  const handleHeroQuickReplace = async (docId) => {
    setActionLoading(true);
    try {
      // Mock valid PDF bytes
      const sampleBytes = new Blob(
        ['%PDF-1.4 Mock Authentic German Chamber Certificate of Origin v2'],
        { type: 'application/pdf' }
      );
      const file = new File([sampleBytes], 'certificate_of_origin_germany_v2.pdf', {
        type: 'application/pdf',
      });
      const formData = new FormData();
      formData.append('file', file);
      formData.append('replace_document_id', docId);
      formData.append(
        'reason',
        'Official expedited COO re-issue by IHK Hamburg confirming German origin.'
      );

      await api.uploadShipmentDocument(id, formData);
      setShowUploadModal(false);
      await loadAllData();
    } catch (err) {
      alert('Quick replace failed: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // Inspect document
  const handleInspectDocument = async (docId) => {
    try {
      const details = await api.getDocument(docId);
      setInspectDoc(details);
    } catch (err) {
      alert('Could not inspect document: ' + err.message);
    }
  };

  // Inspect issue evidence
  const handleInspectIssue = async (issueId) => {
    try {
      const ev = await api.getIssueEvidence(issueId);
      setInspectEvidence(ev);
    } catch (err) {
      alert('Could not load evidence: ' + err.message);
    }
  };

  // Resolve single issue
  const handleResolveIssue = async (issueId, decision) => {
    const comment = prompt(`Confirm ${decision} for this issue (optional rationale):`, 'Verified by compliance officer.');
    if (comment === null) return;
    setActionLoading(true);
    try {
      await api.resolveIssue(issueId, { decision, comment });
      setInspectEvidence(null);
      await loadAllData();
    } catch (err) {
      alert('Failed to resolve issue: ' + err.message);
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CLEARED':
        return <span className="badge badge-cleared" style={{ fontSize: 12 }}>Cleared</span>;
      case 'BLOCKED':
        return (
          <span className="badge badge-blocked" style={{ fontSize: 12 }}>
            <span className="pulse-dot pulse-red" />
            Customs Blocked
          </span>
        );
      case 'WARNING':
        return <span className="badge badge-warning" style={{ fontSize: 12 }}>Warning</span>;
      case 'READY_FOR_REVIEW':
        return <span className="badge badge-ready" style={{ fontSize: 12 }}>Ready For Clearance</span>;
      case 'UNDER_REVIEW':
        return <span className="badge badge-processing" style={{ fontSize: 12 }}>Under Review</span>;
      default:
        return <span className="badge badge-neutral" style={{ fontSize: 12 }}>{status}</span>;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div className="skeleton" style={{ height: 160, width: '100%' }} />
        <div className="skeleton" style={{ height: 400, width: '100%' }} />
      </div>
    );
  }

  if (!shipment) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
        Shipment not found.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Back Link */}
      <div>
        <Link href="/shipments" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)' }}>
          <ArrowLeft size={15} />
          <span>Back to Shipments Fleet</span>
        </Link>
      </div>

      {/* Main Header Card */}
      <div className="glass-panel" style={{
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 20,
      }}>
        {/* Left: Info */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
              {shipment.reference_number}
            </h1>
            {getStatusBadge(shipment.compliance_status)}
            {shipment.reference_number === 'SHP-2026-0842' && (
              <span style={{ fontSize: 11, backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818CF8', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
                HERO SCENARIO
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={14} color="var(--accent-cyan)" />
              <span><strong>{shipment.origin_country || 'DE'}</strong> ({shipment.origin_port?.split(',')[0] || 'Origin'})</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span><strong>{shipment.destination_country || 'IN'}</strong> ({shipment.destination_port?.split(',')[0] || 'Destination'})</span>
            </div>
            <span>•</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Anchor size={14} color="#818CF8" />
              <span>{shipment.carrier || 'Ocean Carrier'}</span>
            </div>
            <span>•</span>
            <div>ETA: <strong style={{ color: '#FFFFFF' }}>{shipment.estimated_arrival || 'In Transit'}</strong></div>
          </div>
        </div>

        {/* Right: Risk Dial & Primary Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {/* Risk Dial */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 18px',
            borderRadius: 12,
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
          }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Risk Index
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: shipment.risk_score >= 50 ? 'var(--status-blocked)' : shipment.risk_score >= 20 ? 'var(--status-warning)' : 'var(--status-cleared)' }}>
                {shipment.risk_level || 'LOW'}
              </div>
            </div>
            <div style={{
              width: 46,
              height: 46,
              borderRadius: '50%',
              background: `conic-gradient(${shipment.risk_score >= 50 ? 'var(--status-blocked)' : shipment.risk_score >= 20 ? 'var(--status-warning)' : 'var(--status-cleared)'} ${shipment.risk_score * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 4,
            }}>
              <div style={{
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                backgroundColor: 'var(--bg-surface)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: 14,
              }}>
                {shipment.risk_score}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => setShowReviewModal(true)}
              className={shipment.compliance_status === 'BLOCKED' ? 'btn-danger' : 'btn-success'}
              style={{ fontSize: 13 }}
            >
              <FileCheck size={16} />
              <span>Officer Review & Clearance</span>
            </button>

            <button
              onClick={() => {
                setReplaceDocId(null);
                setShowUploadModal(true);
              }}
              className="btn-secondary"
              style={{ fontSize: 13 }}
            >
              <Upload size={15} />
              <span>Upload Doc</span>
            </button>

            <button
              onClick={handleRerunCompliance}
              disabled={actionLoading}
              className="btn-secondary"
              title="Re-run compliance engine"
              style={{ padding: '9px 12px' }}
            >
              <RefreshCw size={15} className={actionLoading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: 8, overflowX: 'auto' }}>
        {[
          { id: 'overview', label: 'Overview & AI Guidance', icon: Bot },
          { id: 'documents', label: `Documents (${documents.length})`, icon: FileText },
          { id: 'compliance', label: `Rules & Issues (${compliance?.issues?.length || 0})`, icon: ShieldAlert },
          { id: 'risk', label: 'Multi-Factor Risk', icon: AlertTriangle },
          { id: 'traceability', label: 'Traceability Journey', icon: Compass },
          { id: 'audit', label: `Audit Trail (${auditEvents.length})`, icon: History },
          { id: 'agent', label: 'Autonomous Agent', icon: Sparkles },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${isActive ? 'active' : ''}`}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: OVERVIEW & AI GUIDANCE */}
      {/* ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Action Card */}
            <div className="glass-panel" style={{
              padding: 24,
              borderLeft: shipment.compliance_status === 'BLOCKED' ? '4px solid var(--status-blocked)' : '4px solid var(--accent-primary)',
              background: shipment.compliance_status === 'BLOCKED' ? 'rgba(244, 63, 94, 0.05)' : 'var(--bg-glass)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 11, fontWeight: 700, textTransform: 'uppercase' }}>
                <Bot size={14} color="var(--accent-cyan)" />
                <span>Next Recommended Action</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#FFFFFF', marginTop: 6 }}>
                {overview?.next_recommended_action || 'Review trade documents and finalize customs declaration.'}
              </div>

              {shipment.compliance_status === 'BLOCKED' && (
                <div style={{ marginTop: 16, padding: '12px 14px', borderRadius: 8, backgroundColor: 'rgba(244, 63, 94, 0.12)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>Origin conflict detected: Commercial Invoice (Germany) contradicts Certificate of Origin (Vietnam).</span>
                  <button
                    onClick={() => {
                      const coo = documents.find((d) => d.type === 'certificate_of_origin');
                      if (coo) handleHeroQuickReplace(coo.id);
                    }}
                    className="btn-primary"
                    style={{ fontSize: 12, padding: '6px 14px', backgroundColor: '#BE123C' }}
                  >
                    Replace with Authentic German COO v2
                  </button>
                </div>
              )}
            </div>

            {/* Regulatory RAG Advice */}
            <div className="glass-panel" style={{ padding: 22 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Sparkles size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF' }}>
                  Regulatory RAG Knowledge Retrieval
                </h3>
              </div>

              {overview?.regulatory?.found ? (
                <div style={{
                  padding: 16,
                  borderRadius: 10,
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: 6 }}>
                    <span>{overview.regulatory.source}</span>
                    <span>Section: {overview.regulatory.section}</span>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    "{overview.regulatory.relevant_requirement}"
                  </p>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
                    {overview.regulatory.disclaimer}
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  Standard customs documentation rules apply.
                </div>
              )}
            </div>
          </div>

          {/* Right Summary Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="glass-panel" style={{ padding: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#FFFFFF', marginBottom: 14 }}>
                Consignment Details
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Supplier:</span>
                  <span style={{ fontWeight: 600 }}>{shipment.supplier_name || 'Acme Industrial Supplies'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Consignee:</span>
                  <span style={{ fontWeight: 600 }}>{shipment.customer_name || 'Meridian Imports Pvt Ltd'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Carrier:</span>
                  <span style={{ fontWeight: 600 }}>{shipment.carrier || 'Maersk'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Shipment Date:</span>
                  <span style={{ fontWeight: 600 }}>{shipment.shipment_date || '2026-08-01'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Estimated Arrival:</span>
                  <span style={{ fontWeight: 600 }}>{shipment.estimated_arrival || '2026-09-02'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Doc Completeness:</span>
                  <span style={{ fontWeight: 600, color: 'var(--status-cleared)' }}>{shipment.document_completeness}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: DOCUMENTS & VERSIONS */}
      {/* ========================================================================= */}
      {activeTab === 'documents' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF' }}>Trade Documents & OCR Evidence</h2>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Immutable version history with OCR extracted fields and automated normalization
              </p>
            </div>
            <button
              onClick={() => {
                setReplaceDocId(null);
                setShowUploadModal(true);
              }}
              className="btn-primary"
              style={{ fontSize: 13 }}
            >
              <Upload size={14} />
              <span>Upload New Document</span>
            </button>
          </div>

          <div className="glass-panel" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px' }}>Document Name</th>
                  <th style={{ padding: '12px 16px' }}>Classification</th>
                  <th style={{ padding: '12px 16px' }}>Version</th>
                  <th style={{ padding: '12px 16px' }}>Status</th>
                  <th style={{ padding: '12px 16px' }}>Confidence</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileText size={16} color="var(--accent-cyan)" />
                        <span>{doc.name}</span>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span className="badge badge-neutral" style={{ textTransform: 'none' }}>
                        {doc.type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span className="mono" style={{ fontSize: 12 }}>v{doc.version}</span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span className="badge badge-cleared" style={{ fontSize: 10 }}>Completed</span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontWeight: 700, color: 'var(--status-cleared)' }}>
                        {doc.confidence ? `${Math.round(doc.confidence * 100)}%` : '98%'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                        <button
                          onClick={() => handleInspectDocument(doc.id)}
                          className="btn-secondary"
                          style={{ padding: '5px 10px', fontSize: 11 }}
                        >
                          Inspect Fields
                        </button>
                        <button
                          onClick={() => {
                            setReplaceDocId(doc.id);
                            setShowUploadModal(true);
                          }}
                          className="btn-secondary"
                          style={{ padding: '5px 10px', fontSize: 11 }}
                        >
                          Replace Version
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              const blob = await api.downloadDocumentFile(doc.id);
                              const url = window.URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = doc.name;
                              a.click();
                            } catch (e) {
                              alert('Download error: ' + e.message);
                            }
                          }}
                          className="btn-secondary"
                          style={{ padding: '5px 8px' }}
                          title="Download document PDF"
                        >
                          <Download size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: COMPLIANCE RULES & ISSUES */}
      {/* ========================================================================= */}
      {activeTab === 'compliance' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Active Issues Section */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', marginBottom: 14 }}>
              Active Rule Violations ({compliance?.issues?.filter((i) => i.status === 'OPEN').length || 0})
            </h3>

            {(!compliance?.issues || compliance.issues.filter((i) => i.status === 'OPEN').length === 0) ? (
              <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
                <CheckCircle2 size={32} color="var(--status-cleared)" style={{ margin: '0 auto 8px' }} />
                <div>All deterministic compliance rules satisfied. No active exceptions.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {compliance.issues.map((issue) => (
                  <div
                    key={issue.id}
                    style={{
                      padding: 16,
                      borderRadius: 10,
                      backgroundColor: issue.status === 'OPEN' ? 'rgba(244, 63, 94, 0.04)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${issue.status === 'OPEN' ? (issue.severity === 'CRITICAL' ? 'rgba(244, 63, 94, 0.35)' : 'rgba(245, 158, 11, 0.35)') : 'var(--border-subtle)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 16,
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span style={{ fontWeight: 800, fontSize: 14, color: '#FFFFFF' }}>{issue.title}</span>
                        <span className={`badge ${issue.severity === 'CRITICAL' ? 'badge-blocked' : 'badge-warning'}`} style={{ fontSize: 10 }}>
                          {issue.severity}
                        </span>
                        <span className={`badge ${issue.status === 'OPEN' ? 'badge-neutral' : 'badge-cleared'}`} style={{ fontSize: 9 }}>
                          {issue.status}
                        </span>
                      </div>
                      <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        {issue.description}
                      </p>
                      {issue.recommended_action && (
                        <div style={{ fontSize: 12, color: 'var(--accent-cyan)', marginTop: 6, fontWeight: 500 }}>
                          <strong>Recommended:</strong> {issue.recommended_action}
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                      <button
                        onClick={() => handleInspectIssue(issue.id)}
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: 12 }}
                      >
                        Inspect Evidence
                      </button>

                      {issue.status === 'OPEN' && (
                        <button
                          onClick={() => handleResolveIssue(issue.id, 'override')}
                          className="btn-primary"
                          style={{ padding: '6px 12px', fontSize: 12 }}
                        >
                          Officer Override
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Evaluations History */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', marginBottom: 14 }}>
              Rule Engine Execution Log
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {compliance?.evaluations?.slice(0, 10).map((ev) => (
                <div
                  key={ev.id}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 8,
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 13,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className={`badge ${ev.result === 'passed' ? 'badge-cleared' : 'badge-blocked'}`} style={{ fontSize: 9 }}>
                      {ev.result}
                    </span>
                    <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{ev.rule || 'RULE'}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{ev.message}</span>
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {ev.evaluated_at ? new Date(ev.evaluated_at).toLocaleTimeString() : 'Recent'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: RISK MODEL */}
      {/* ========================================================================= */}
      {activeTab === 'risk' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Risk Factors */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', marginBottom: 14 }}>
              Contributing Risk Factors
            </h3>
            {risk?.factors?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {risk.factors.map((f, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 8,
                      backgroundColor: 'rgba(255,255,255,0.02)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: '#FFFFFF' }}>{f.label}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Category: {f.category}
                      </div>
                    </div>
                    <span style={{ fontWeight: 800, fontSize: 14, color: 'var(--status-blocked)' }}>
                      +{f.points} pts
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
                No active risk penalties applied.
              </div>
            )}
          </div>

          {/* Risk Timeline */}
          <div className="glass-panel" style={{ padding: 22 }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', marginBottom: 14 }}>
              Risk Assessment Progression
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {riskHistory.slice(-5).map((rh) => (
                <div
                  key={rh.id}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 8,
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>Score: {rh.score} ({rh.level})</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{rh.reason}</div>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {rh.created_at ? new Date(rh.created_at).toLocaleTimeString() : 'Recorded'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: TRACEABILITY GRAPH */}
      {/* ========================================================================= */}
      {activeTab === 'traceability' && (
        <div className="glass-panel" style={{ padding: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF', marginBottom: 4 }}>
            End-to-End Chain of Custody & Logistics Traceability
          </h2>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Geospatial waypoints, modal transfers, and custody transfer verifications
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {traceability?.nodes?.map((node, idx) => (
              <div
                key={node.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 16,
                  position: 'relative',
                }}
              >
                {/* Visual Line connector */}
                {idx < traceability.nodes.length - 1 && (
                  <div style={{
                    position: 'absolute',
                    left: 17,
                    top: 36,
                    bottom: -16,
                    width: 2,
                    backgroundColor: 'var(--border-strong)',
                  }} />
                )}

                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  backgroundColor: node.risk === 'CRITICAL' ? 'var(--status-blocked-bg)' : 'rgba(99, 102, 241, 0.15)',
                  border: `2px solid ${node.risk === 'CRITICAL' ? 'var(--status-blocked)' : 'var(--accent-primary)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: 12,
                  color: '#FFFFFF',
                  zIndex: 2,
                  flexShrink: 0,
                }}>
                  {idx + 1}
                </div>

                <div style={{
                  flex: 1,
                  padding: 14,
                  borderRadius: 10,
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#FFFFFF' }}>{node.label}</div>
                    <span className={`badge ${node.risk === 'CRITICAL' ? 'badge-blocked' : 'badge-neutral'}`} style={{ fontSize: 9 }}>
                      {node.kind}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Location: {node.location || 'Coordinates logged'}
                  </div>
                  {node.details && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                      {Object.entries(node.details).map(([k, v]) => `${k}: ${v}`).join(' • ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 6: AUDIT TRAIL */}
      {/* ========================================================================= */}
      {activeTab === 'audit' && (
        <div className="glass-panel" style={{ padding: 22 }}>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#FFFFFF', marginBottom: 14 }}>
            Immutable Regulatory Audit Ledger
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {auditEvents.map((e) => (
              <div
                key={e.id}
                style={{
                  padding: '12px 14px',
                  borderRadius: 8,
                  backgroundColor: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: 13,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 700, color: '#FFFFFF' }}>{e.event_type}</span>
                    <span className="badge badge-neutral" style={{ fontSize: 9 }}>{e.actor_type}</span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', marginTop: 3 }}>
                    {e.description}
                  </div>
                  {e.previous_state && e.new_state && (
                    <div style={{ fontSize: 11, color: 'var(--accent-cyan)', marginTop: 4 }}>
                      State Transition: <code>{e.previous_state}</code> → <code>{e.new_state}</code>
                    </div>
                  )}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'right' }}>
                  {e.timestamp ? new Date(e.timestamp).toLocaleString() : 'Recorded'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 7: AUTONOMOUS AGENT */}
      {/* ========================================================================= */}
      {activeTab === 'agent' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="glass-panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF' }}>
                  Autonomous Agent Orchestrator Runs
                </h3>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  Event-driven decisions generated upon document extraction & risk threshold triggers
                </p>
              </div>
              <button onClick={handleRerunAgent} disabled={actionLoading} className="btn-primary" style={{ fontSize: 12 }}>
                <Sparkles size={14} />
                <span>Execute Agent Cycle</span>
              </button>
            </div>

            {agentActivity?.runs?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {agentActivity.runs.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      padding: 16,
                      borderRadius: 10,
                      backgroundColor: 'rgba(255,255,255,0.02)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Bot size={16} color="var(--accent-cyan)" />
                        <span style={{ fontWeight: 700, fontSize: 14 }}>Decision: {r.decision}</span>
                        <span className="badge badge-neutral" style={{ fontSize: 9 }}>Trigger: {r.trigger}</span>
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {r.created_at ? new Date(r.created_at).toLocaleTimeString() : 'Recent'}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {r.summary}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
                No automated agent runs recorded.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: OFFICER REVIEW & CLEARANCE */}
      {/* ========================================================================= */}
      {showReviewModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 480, padding: 28, borderRadius: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div style={{ fontSize: 18, fontWeight: 800 }}>Officer Clearance Determination</div>
              <button onClick={() => setShowReviewModal(false)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Decision Verdict
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value)}
                  className="input-field"
                >
                  <option value="approve">Approve & Issue Clearance (CLEARED)</option>
                  <option value="request_more_information">Request Additional Information (UNDER_REVIEW)</option>
                  <option value="reject">Reject Consignment</option>
                  <option value="override">Supervisor Override Exemption</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Regulatory Rationale / Auditor Comment
                </label>
                <textarea
                  rows={4}
                  required
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="State compliance justification for audit trail..."
                  className="input-field"
                  style={{ resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button type="button" onClick={() => setShowReviewModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={actionLoading} className="btn-primary">
                  {actionLoading ? 'Recording Verdict...' : 'Submit Clearance Determination'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: UPLOAD / REPLACE DOCUMENT */}
      {/* ========================================================================= */}
      {showUploadModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 480, padding: 28, borderRadius: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div style={{ fontSize: 18, fontWeight: 800 }}>
                {replaceDocId ? 'Replace Document Version' : 'Upload Consignment Document'}
              </div>
              <button onClick={() => setShowUploadModal(false)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            {/* If replacing COO on hero shipment, offer 1-click shortcut */}
            {replaceDocId && (
              <div style={{
                marginBottom: 18,
                padding: '12px 14px',
                borderRadius: 10,
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#C7D2FE', marginBottom: 6 }}>
                  One-Click Demo Action
                </div>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10 }}>
                  Automatically upload the authentic IHK Hamburg German Certificate of Origin v2 to resolve the origin conflict.
                </p>
                <button
                  type="button"
                  onClick={() => handleHeroQuickReplace(replaceDocId)}
                  disabled={actionLoading}
                  className="btn-primary"
                  style={{ width: '100%', fontSize: 12, padding: '8px 0' }}
                >
                  ⚡ Upload Corrected German COO v2 & Re-Run Audit
                </button>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  Select Trade Document (PDF, TXT, PNG)
                </label>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files?.[0])}
                  className="input-field"
                  style={{ padding: '8px' }}
                />
              </div>

              {replaceDocId && (
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    Reason for Replacement
                  </label>
                  <input
                    type="text"
                    value={replaceReason}
                    onChange={(e) => setReplaceReason(e.target.value)}
                    placeholder="e.g. Corrected country of origin certificate"
                    className="input-field"
                  />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button type="button" onClick={() => setShowUploadModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={actionLoading || !uploadFile} className="btn-primary">
                  {actionLoading ? 'Uploading...' : 'Upload & Process with AI'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: INSPECT DOCUMENT FIELDS */}
      {/* ========================================================================= */}
      {inspectDoc && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 640, maxHeight: '80vh', overflowY: 'auto', padding: 28, borderRadius: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>{inspectDoc.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Type: {inspectDoc.type} • Status: {inspectDoc.processing_status}</div>
              </div>
              <button onClick={() => setInspectDoc(null)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>
              AI Extracted & Normalized Fields
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {inspectDoc.fields?.map((f) => (
                <div
                  key={f.id}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    backgroundColor: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 12,
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{f.field}:</span>{' '}
                    <span style={{ color: '#FFFFFF' }}>{f.raw_value}</span>
                    {f.normalized_value && f.normalized_value !== f.raw_value && (
                      <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>
                        (normalized: <code>{f.normalized_value}</code>)
                      </span>
                    )}
                  </div>
                  <span style={{ fontWeight: 600, color: 'var(--status-cleared)' }}>
                    {f.confidence ? `${Math.round(f.confidence * 100)}%` : '98%'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: INSPECT ISSUE EVIDENCE */}
      {/* ========================================================================= */}
      {inspectEvidence && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 580, padding: 28, borderRadius: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>Audit Rule Evidence Breakdown</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Issue: {inspectEvidence.issue}</div>
              </div>
              <button onClick={() => setInspectEvidence(null)} style={{ color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
              {inspectEvidence.evidence?.map((e) => (
                <div
                  key={e.id}
                  style={{
                    padding: 12,
                    borderRadius: 8,
                    backgroundColor: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                    <span>Source Doc: {e.document_name}</span>
                    <span>Confidence: {e.confidence ? `${Math.round(e.confidence * 100)}%` : '98%'}</span>
                  </div>
                  <div style={{ fontSize: 13 }}>
                    <strong style={{ color: 'var(--accent-cyan)' }}>{e.field}:</strong>{' '}
                    <span style={{ color: '#FFFFFF' }}>{e.raw_value}</span>
                    <span style={{ color: 'var(--text-muted)' }}> (normalized: {e.normalized_value})</span>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setInspectEvidence(null)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
