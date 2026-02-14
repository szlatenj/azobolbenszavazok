const wizard = {
  currentCard: "landing",
  history: [],
  votingMethod: null, // 'consulate' or 'mail'

  cards: {
    landing: { next: "question" },
    question: {},
    consulate1: { next: "consulate2" },
    consulate2: { next: "menu" },
    mail1: { next: "mail2" },
    mail2: { next: "menu" },
    menu: {},
    signup: { next: "confirmSignup" },
    helprequest: { next: "confirmHelp" },
    carpool: { next: "confirmCarpool" },
    confirmSignup: {},
    confirmHelp: {},
    confirmCarpool: {},
    contact: {},
  },

  init() {
    this.showCard("landing");
    this.bindNavigation();
    this.bindForms();
    this.bindCarpoolToggle();
  },

  showCard(id) {
    document.querySelectorAll(".card").forEach((card) => {
      card.classList.remove("active", "slide-in");
      card.classList.add("hidden");
    });

    const target = document.getElementById(`card-${id}`);
    if (target) {
      target.classList.remove("hidden");
      void target.offsetWidth;
      target.classList.add("active", "slide-in");
      this.currentCard = id;
      target.scrollIntoView({ behavior: "smooth", block: "start" });

      // Show/hide back button
      const backBtn = target.querySelector(".btn-back");
      if (backBtn) {
        backBtn.style.display = this.history.length > 0 ? "" : "none";
      }
    }
  },

  goTo(id) {
    this.history.push(this.currentCard);
    this.showCard(id);
  },

  goBack() {
    if (this.history.length === 0) return;
    const prev = this.history.pop();
    this.showCard(prev);
  },

  goToMenu() {
    // Navigate to menu, clearing history up to menu level
    this.history = this.history.filter(
      (c) => !["signup", "helprequest", "carpool", "contact", "confirmSignup", "confirmHelp", "confirmCarpool"].includes(c)
    );
    if (!this.history.includes("menu")) {
      this.history.push(this.currentCard);
    }
    this.showCard("menu");
  },

  restart() {
    this.votingMethod = null;
    this.history = [];
    this.showCard("landing");
  },

  bindNavigation() {
    // All back buttons
    document.querySelectorAll(".btn-back").forEach((btn) => {
      btn.addEventListener("click", () => this.goBack());
    });

    // Landing start button
    document.getElementById("btn-start").addEventListener("click", () => {
      this.goTo("question");
    });

    // Question: Yes (consulate)
    document.getElementById("btn-yes").addEventListener("click", () => {
      this.votingMethod = "consulate";
      this.goTo("consulate1");
    });

    // Question: No (mail)
    document.getElementById("btn-no").addEventListener("click", () => {
      this.votingMethod = "mail";
      this.goTo("mail1");
    });

    // Consulate path navigation
    document.getElementById("btn-consulate1-next").addEventListener("click", () => {
      this.goTo("consulate2");
    });
    document.getElementById("btn-consulate2-next").addEventListener("click", () => {
      this.goTo("menu");
    });

    // Mail path navigation
    document.getElementById("btn-mail1-next").addEventListener("click", () => {
      this.goTo("mail2");
    });
    document.getElementById("btn-mail2-next").addEventListener("click", () => {
      this.goTo("menu");
    });

    // Menu buttons
    document.getElementById("btn-menu-signup").addEventListener("click", () => {
      this.goTo("signup");
    });
    document.getElementById("btn-menu-helprequest").addEventListener("click", () => {
      this.goTo("helprequest");
    });
    document.getElementById("btn-menu-carpool").addEventListener("click", () => {
      this.goTo("carpool");
    });
    document.getElementById("btn-menu-contact").addEventListener("click", () => {
      this.goTo("contact");
    });

    // Confirmation cards: "Back to menu" and "Restart" buttons
    document.querySelectorAll(".btn-back-to-menu").forEach((btn) => {
      btn.addEventListener("click", () => this.goToMenu());
    });
    document.querySelectorAll(".btn-restart").forEach((btn) => {
      btn.addEventListener("click", () => this.restart());
    });
  },

  bindCarpoolToggle() {
    const carpoolForm = document.getElementById("carpool-form");
    const seatsGroup = document.getElementById("seats-group");
    const radios = carpoolForm.querySelectorAll('input[name="carpool_type"]');

    const updateSeatsVisibility = () => {
      const selected = carpoolForm.querySelector('input[name="carpool_type"]:checked');
      seatsGroup.style.display = selected && selected.value === "offer" ? "" : "none";
    };

    radios.forEach((radio) => {
      radio.addEventListener("change", updateSeatsVisibility);
    });

    // Initial state
    updateSeatsVisibility();
  },

  bindForms() {
    // Signup form
    const signupForm = document.getElementById("signup-form");
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = signupForm.querySelector("button[type=submit]");
      const msg = document.getElementById("signup-msg");

      btn.disabled = true;
      btn.textContent = i18n.t("signup.submitting");
      msg.textContent = "";
      msg.className = "form-message";

      try {
        await api.signup({
          name: signupForm.name.value.trim(),
          email: signupForm.email.value.trim(),
          phone: signupForm.phone.value.trim() || null,
          voting_method: this.votingMethod,
          language_pref: i18n.currentLang,
        });
        msg.textContent = i18n.t("signup.success");
        msg.classList.add("success");
        setTimeout(() => this.goTo("confirmSignup"), 1500);
      } catch (err) {
        if (err.status === 409) {
          msg.textContent = i18n.t("signup.error.duplicate");
        } else {
          msg.textContent = i18n.t("signup.error.generic");
        }
        msg.classList.add("error");
      } finally {
        btn.disabled = false;
        btn.textContent = i18n.t("signup.submit");
      }
    });

    // Help request form
    const helpForm = document.getElementById("helprequest-form");
    helpForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = helpForm.querySelector("button[type=submit]");
      const msg = document.getElementById("helprequest-msg");

      btn.disabled = true;
      btn.textContent = i18n.t("helprequest.submitting");
      msg.textContent = "";
      msg.className = "form-message";

      try {
        await api.helpRequest({
          name: helpForm.name.value.trim(),
          email: helpForm.email.value.trim(),
          phone: helpForm.phone.value.trim() || null,
          message: helpForm.message.value.trim(),
          voting_method: this.votingMethod,
          language_pref: i18n.currentLang,
        });
        msg.textContent = i18n.t("helprequest.success");
        msg.classList.add("success");
        setTimeout(() => this.goTo("confirmHelp"), 1500);
      } catch {
        msg.textContent = i18n.t("helprequest.error");
        msg.classList.add("error");
      } finally {
        btn.disabled = false;
        btn.textContent = i18n.t("helprequest.submit");
      }
    });

    // Carpool form
    const carpoolForm = document.getElementById("carpool-form");
    carpoolForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = carpoolForm.querySelector("button[type=submit]");
      const msg = document.getElementById("carpool-msg");

      btn.disabled = true;
      btn.textContent = i18n.t("carpool.submitting");
      msg.textContent = "";
      msg.className = "form-message";

      const carpoolType = carpoolForm.querySelector('input[name="carpool_type"]:checked').value;

      try {
        await api.carpool({
          carpool_type: carpoolType,
          name: carpoolForm.name.value.trim(),
          email: carpoolForm.email.value.trim(),
          phone: carpoolForm.phone.value.trim() || null,
          starting_location: carpoolForm.starting_location.value.trim(),
          seats: carpoolType === "offer" ? parseInt(carpoolForm.seats.value) : null,
          voting_method: this.votingMethod,
          language_pref: i18n.currentLang,
        });
        msg.textContent = i18n.t("carpool.success");
        msg.classList.add("success");
        setTimeout(() => this.goTo("confirmCarpool"), 1500);
      } catch {
        msg.textContent = i18n.t("carpool.error");
        msg.classList.add("error");
      } finally {
        btn.disabled = false;
        btn.textContent = i18n.t("carpool.submit");
      }
    });

    // Contact form
    const contactForm = document.getElementById("contact-form");
    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = contactForm.querySelector("button[type=submit]");
      const msg = document.getElementById("contact-msg");

      btn.disabled = true;
      btn.textContent = i18n.t("contact.submitting");
      msg.textContent = "";
      msg.className = "form-message";

      try {
        await api.contact({
          name: contactForm.name.value.trim(),
          email: contactForm.email.value.trim(),
          message: contactForm.message.value.trim(),
          language_pref: i18n.currentLang,
        });
        msg.textContent = i18n.t("contact.success");
        msg.classList.add("success");
        contactForm.reset();
      } catch {
        msg.textContent = i18n.t("contact.error");
        msg.classList.add("error");
      } finally {
        btn.disabled = false;
        btn.textContent = i18n.t("contact.submit");
      }
    });
  },
};

// Boot
document.addEventListener("DOMContentLoaded", () => {
  i18n.init();
  wizard.init();
});
