/**
 * API client for the election simulation backend.
 */
const api = {
  baseUrl: '/api',

  async getConfig() {
    const res = await fetch(`${this.baseUrl}/simulation/config`);
    if (!res.ok) throw new Error(`Config fetch failed: ${res.status}`);
    return res.json();
  },

  async getPolls() {
    const res = await fetch(`${this.baseUrl}/simulation/polls`);
    if (!res.ok) throw new Error(`Polls fetch failed: ${res.status}`);
    return res.json();
  },

  async runSimulation(params) {
    const res = await fetch(`${this.baseUrl}/simulation/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (res.status === 429) {
      throw new Error('A simulation is already running. Please wait.');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Simulation failed: ${res.status}`);
    }
    return res.json();
  },

  async runDefault() {
    const res = await fetch(`${this.baseUrl}/simulation/default`);
    if (res.status === 429) {
      throw new Error('A simulation is already running. Please wait.');
    }
    if (!res.ok) throw new Error(`Default simulation failed: ${res.status}`);
    return res.json();
  },
};
