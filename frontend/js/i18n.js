const i18n = {
  currentLang: localStorage.getItem("lang") || "hu",

  init() {
    this.applyAll();
    document.getElementById("lang-toggle").addEventListener("click", () => {
      this.currentLang = this.currentLang === "hu" ? "en" : "hu";
      localStorage.setItem("lang", this.currentLang);
      this.applyAll();
    });
  },

  t(key) {
    return translations[this.currentLang][key] || key;
  },

  applyAll() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const text = this.t(key);
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = text;
      } else {
        el.textContent = text;
      }
    });
    // Update html lang attribute
    document.documentElement.lang = this.currentLang;
  },
};
