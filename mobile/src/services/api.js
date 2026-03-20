import AsyncStorage from '@react-native-async-storage/async-storage';

// Change this to your computer's IP when testing on a physical device
const BASE_URL = 'http://172.26.97.46:5001';

class ApiService {
  async getToken() { return await AsyncStorage.getItem('token'); }

  async request(endpoint, options = {}) {
    const token = await this.getToken();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Something went wrong');
    return data;
  }

  async login(email, password) {
    const data = await this.request('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    await AsyncStorage.setItem('token', data.token);
    await AsyncStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async register(userData) {
    const data = await this.request('/api/auth/register', { method: 'POST', body: JSON.stringify(userData) });
    await AsyncStorage.setItem('token', data.token);
    await AsyncStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async getMe() { return await this.request('/api/auth/me'); }
  async logout() { await AsyncStorage.removeItem('token'); await AsyncStorage.removeItem('user'); }
  async getDashboard() { return await this.request('/api/dashboard'); }

  async analyzeImage(imageUri) {
    const token = await this.getToken();
    const formData = new FormData();
    formData.append('image', { uri: imageUri, type: 'image/jpeg', name: 'scan.jpg' });
    const response = await fetch(`${BASE_URL}/api/analyze`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis failed');
    return data;
  }

  async analyzeSymptoms(symptoms, plantType) {
    return await this.request('/api/analyze_symptoms', { method: 'POST', body: JSON.stringify({ symptoms, plant_type: plantType }) });
  }

  async getHistory() { return await this.request('/api/history'); }
  async updateProfile(d) { return await this.request('/api/profile', { method: 'PUT', body: JSON.stringify(d) }); }
  async updatePreferences(d) { return await this.request('/api/preferences', { method: 'PUT', body: JSON.stringify(d) }); }
  async changePassword(cur, nw, conf) { return await this.request('/api/security', { method: 'PUT', body: JSON.stringify({ current_password: cur, new_password: nw, confirm_password: conf }) }); }
  async submitFeedback(d) { return await this.request('/api/feedback', { method: 'POST', body: JSON.stringify(d) }); }
  async getPests(lang = 'en') { return await this.request(`/api/pests?lang=${lang}`); }
  async getStats() { return await this.request('/api/stats'); }
  async getTranslations(lang) { return await this.request(`/api/translations/${lang}`); }
  async exportScans() { return await this.request('/api/export/scans'); }
  async exportProfile() { return await this.request('/api/export/profile'); }
}

export default new ApiService();
