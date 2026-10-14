// =========================================================================
// AuditFlow AI - Centralized Frontend API Client
// =========================================================================

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseUrl = BASE_URL;
  }

  getToken() {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auditflow_token');
  }

  setToken(token) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auditflow_token', token);
    }
  }

  removeToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auditflow_token');
      localStorage.removeItem('auditflow_user');
    }
  }

  getCurrentUser() {
    if (typeof window === 'undefined') return null;
    try {
      const u = localStorage.getItem('auditflow_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  }

  setCurrentUser(user) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auditflow_user', JSON.stringify(user));
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = {
      ...(options.headers || {}),
    };

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const res = await fetch(url, {
        ...options,
        headers,
      });

      if (res.status === 401 && !endpoint.includes('/auth/login')) {
        this.removeToken();
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        throw new Error('Session expired. Please log in again.');
      }

      if (!res.ok) {
        let errMsg = `Request failed: ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          errMsg = errData.detail || errMsg;
        } catch {}
        throw new Error(errMsg);
      }

      // Handle raw blobs or json
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
        return res.blob();
      }

      return await res.json();
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  }

  // --- Authentication ---
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) {
      this.setToken(data.access_token);
      const user = await this.getMe();
      this.setCurrentUser(user);
    }
    return data;
  }

  async register(payload) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (data.access_token) {
      this.setToken(data.access_token);
      const user = await this.getMe();
      this.setCurrentUser(user);
    }
    return data;
  }

  async getMe() {
    return await this.request('/auth/me');
  }

  logout() {
    this.removeToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  // --- Dashboard & Analytics ---
  async getDashboardSummary() {
    return await this.request('/dashboard/summary');
  }

  async getQueue(severity = null, status = 'OPEN') {
    const params = new URLSearchParams();
    if (severity) params.set('severity', severity);
    if (status) params.set('status', status);
    return await this.request(`/queue?${params.toString()}`);
  }

  async getNotifications() {
    return await this.request('/notifications');
  }

  async search(query) {
    return await this.request(`/search?q=${encodeURIComponent(query)}`);
  }

  // --- Shipments ---
  async listShipments(search = '') {
    const ep = search ? `/shipments?q=${encodeURIComponent(search)}` : '/shipments';
    return await this.request(ep);
  }

  async getShipment(id) {
    return await this.request(`/shipments/${id}`);
  }

  async createShipment(payload) {
    return await this.request('/shipments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateShipment(id, payload) {
    return await this.request(`/shipments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async getShipmentOverview(id) {
    return await this.request(`/shipments/${id}/overview`);
  }

  // --- Documents ---
  async listShipmentDocuments(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/documents`);
  }

  async uploadShipmentDocument(shipmentId, formData) {
    return await this.request(`/shipments/${shipmentId}/documents`, {
      method: 'POST',
      body: formData,
    });
  }

  async getDocument(docId) {
    return await this.request(`/documents/${docId}`);
  }

  async getDocumentVersions(docId) {
    return await this.request(`/documents/${docId}/versions`);
  }

  async downloadDocumentFile(docId, version = null) {
    const ep = version ? `/documents/${docId}/file?version=${version}` : `/documents/${docId}/file`;
    return await this.request(ep);
  }

  // --- Compliance ---
  async getShipmentCompliance(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/compliance`);
  }

  async runShipmentCompliance(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/compliance/run`, {
      method: 'POST',
    });
  }

  async getIssue(issueId) {
    return await this.request(`/compliance/issues/${issueId}`);
  }

  async getIssueEvidence(issueId) {
    return await this.request(`/compliance/issues/${issueId}/evidence`);
  }

  async resolveIssue(issueId, payload) {
    return await this.request(`/compliance/issues/${issueId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- Risk ---
  async getShipmentRisk(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/risk`);
  }

  async getShipmentRiskHistory(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/risk/history`);
  }

  async recalculateShipmentRisk(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/risk/recalculate`, {
      method: 'POST',
    });
  }

  // --- Agent ---
  async getShipmentAgentActivity(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/agent/activity`);
  }

  async runShipmentAgent(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/agent/run`, {
      method: 'POST',
    });
  }

  // --- Traceability ---
  async getShipmentTraceability(shipmentId) {
    return await this.request(`/shipments/${shipmentId}/traceability`);
  }

  // --- Audit Trail ---
  async getShipmentAuditTrail(shipmentId, category = 'All') {
    const ep = category && category !== 'All' 
      ? `/shipments/${shipmentId}/audit?category=${encodeURIComponent(category)}`
      : `/shipments/${shipmentId}/audit`;
    return await this.request(ep);
  }

  // --- Review & Clearance ---
  async reviewShipment(shipmentId, payload) {
    return await this.request(`/shipments/${shipmentId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- Tasks ---
  async listTasks(shipmentId = null) {
    const ep = shipmentId ? `/tasks?shipment_id=${shipmentId}` : '/tasks';
    return await this.request(ep);
  }

  async createTask(payload) {
    return await this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateTask(taskId, payload) {
    return await this.request(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }
}

export const api = new ApiClient();
export default api;
