const API_BASE = "/api";

const api = {
  async signup(data) {
    const res = await fetch(`${API_BASE}/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const error = new Error(err.detail || "Signup failed");
      error.status = res.status;
      throw error;
    }
    return res.json();
  },

  async contact(data) {
    const res = await fetch(`${API_BASE}/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Contact submission failed");
    }
    return res.json();
  },

  async helpRequest(data) {
    const res = await fetch(`${API_BASE}/help-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Help request failed");
    }
    return res.json();
  },

  async carpool(data) {
    const res = await fetch(`${API_BASE}/carpool`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Carpool submission failed");
    }
    return res.json();
  },
};
