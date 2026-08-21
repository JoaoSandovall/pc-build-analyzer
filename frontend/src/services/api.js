export const api = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',

  async request(endpoint, options = {}) {
    const res = await fetch(`${this.baseURL}${endpoint}`, options);
    
    if (!res.ok) {
      if (res.status === 401 && !endpoint.includes('/auth/login')) {
        window.dispatchEvent(new CustomEvent('session-expired'));
        throw new Error('Sessão expirada. Faça login novamente.');
      }
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Ocorreu um erro inesperado no servidor.');
    }
    
    if (res.status === 204) return null;
    return res.json();
  },

  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const res = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    if (!res.ok) throw new Error('Credenciais inválidas.');
    return res.json();
  },

  async register(email, password) {
    return this.request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha: password }),
    });
  },

  async getUploadUrl(fileName, token) {
    return this.request('/budgets/upload-url', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ nome_arquivo: fileName }),
    });
  },

  async uploadToS3(urlUpload, s3Fields, file) {
    const formData = new FormData();
    Object.entries(s3Fields).forEach(([key, value]) => formData.append(key, value));
    formData.append('file', file);
    const res = await fetch(urlUpload, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Falha no upload para a nuvem. Tente novamente.');
    return res;
  },

  async processBudget(budgetId, token) {
    return this.request('/budgets/process', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ budget_id: budgetId }),
    });
  },

  async getBudgets(token) {
    return this.request('/budgets', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
  },

  async getComparison(budgetId, token) {
    return this.request(`/budgets/${budgetId}/comparison`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
  },

  async findPrice(budgetId, itemId, token) {
    return this.request(`/budgets/${budgetId}/items/${itemId}/find-price`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
  },

  async deleteBudget(budgetId, token) {
    return this.request(`/budgets/${budgetId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
  }
};