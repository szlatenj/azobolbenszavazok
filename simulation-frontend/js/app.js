/**
 * Main application logic for the election simulator dashboard.
 */

const state = {
  config: null,
  polls: null,
  result: null,
  useCustomShares: false,
  customShares: {},
  activeParties: {},
  params: {},
  pollsterWeights: {},
  pollsterHouseEffects: {},
};

// ── Initialization ──────────────────────────────────────────────────

async function init() {
  i18n.init();
  setupTabs();
  setupEventListeners();

  try {
    const [config, polls] = await Promise.all([
      api.getConfig(),
      api.getPolls(),
    ]);
    state.config = config;
    state.polls = polls;
    initFromConfig(config);
    renderPollsTable(polls);
    await runSim();
  } catch (err) {
    showError('Failed to load config: ' + err.message);
  }
}

function initFromConfig(config) {
  // Init params
  state.params = {
    n_simulations: config.n_simulations,
    sigma_polling_error: config.sigma_polling_error,
    sigma_regional: config.sigma_regional,
    sigma_district: config.sigma_district,
    sigma_turnout: config.sigma_turnout,
    poll_halflife_days: config.poll_halflife_days,
    floor_uncertainty: config.floor_uncertainty,
    fidesz_opposition_correlation: config.fidesz_opposition_correlation,
    small_party_correlation: config.small_party_correlation,
    urban_swing_fidesz: config.urban_swing_fidesz,
    urban_swing_tisza: config.urban_swing_tisza,
    urban_swing_mi_hazank: config.urban_swing_mi_hazank,
    urban_turnout_shift: config.urban_turnout_shift,
    rural_turnout_shift: config.rural_turnout_shift,
    budapest_extra_swing: config.budapest_extra_swing,
  };

  // Init party toggles and shares
  config.parties.forEach(p => {
    state.activeParties[p.short] = true;
    state.customShares[p.short] = 0;
  });

  // Init pollster weights
  Object.entries(config.pollsters).forEach(([name, info]) => {
    state.pollsterWeights[name] = info.quality_weight;
    state.pollsterHouseEffects[name] = { ...info.house_effects };
  });

  renderPartyControls(config.parties);
  renderParamControls();
  renderPollsterControls(config.pollsters);
}

// ── Tab Navigation ──────────────────────────────────────────────────

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    });
  });
}

function setupEventListeners() {
  document.getElementById('run-btn').addEventListener('click', runSim);
  document.getElementById('lang-toggle').addEventListener('click', () => i18n.toggle());
  document.getElementById('reset-defaults-btn').addEventListener('click', resetDefaults);

  document.getElementById('share-mode-polls').addEventListener('change', () => {
    state.useCustomShares = false;
    document.getElementById('custom-sliders').classList.add('dimmed');
  });
  document.getElementById('share-mode-custom').addEventListener('change', () => {
    state.useCustomShares = true;
    document.getElementById('custom-sliders').classList.remove('dimmed');
  });

  // Pollster presets
  document.getElementById('preset-equal').addEventListener('click', () => applyPollsterPreset('equal'));
  document.getElementById('preset-default').addEventListener('click', () => applyPollsterPreset('default'));
  document.getElementById('preset-independent').addEventListener('click', () => applyPollsterPreset('independent'));

  // Histogram party selector
  document.getElementById('histogram-party')?.addEventListener('change', (e) => {
    if (state.result) renderHistogram(state.result, e.target.value);
  });
}

// ── Run Simulation ──────────────────────────────────────────────────

async function runSim() {
  const btn = document.getElementById('run-btn');
  const spinner = document.getElementById('run-spinner');
  btn.disabled = true;
  spinner.style.display = 'inline-block';
  btn.querySelector('span').textContent = i18n.t('running');

  try {
    const params = buildSimParams();
    const result = await api.runSimulation(params);
    state.result = result;
    renderResults(result);
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    spinner.style.display = 'none';
    btn.querySelector('span').textContent = i18n.t('run_simulation');
  }
}

function buildSimParams() {
  const params = {
    n_simulations: state.params.n_simulations,
    sigma_polling_error: state.params.sigma_polling_error,
    sigma_regional: state.params.sigma_regional,
    sigma_district: state.params.sigma_district,
    sigma_turnout: state.params.sigma_turnout,
    poll_halflife_days: state.params.poll_halflife_days,
    floor_uncertainty: state.params.floor_uncertainty,
    fidesz_opposition_correlation: state.params.fidesz_opposition_correlation,
    small_party_correlation: state.params.small_party_correlation,
    urban_swing_fidesz: state.params.urban_swing_fidesz,
    urban_swing_tisza: state.params.urban_swing_tisza,
    urban_swing_mi_hazank: state.params.urban_swing_mi_hazank,
    urban_turnout_shift: state.params.urban_turnout_shift,
    rural_turnout_shift: state.params.rural_turnout_shift,
    budapest_extra_swing: state.params.budapest_extra_swing,
    active_parties: { ...state.activeParties },
    pollster_weights: { ...state.pollsterWeights },
    pollster_house_effects: { ...state.pollsterHouseEffects },
  };

  const seed = document.getElementById('random-seed')?.value;
  if (seed) params.random_seed = parseInt(seed);

  if (state.useCustomShares) {
    params.custom_shares = { ...state.customShares };
  }

  return params;
}

// ── Render Results ──────────────────────────────────────────────────

function renderResults(result) {
  // Headline cards
  const parties = result.parties;
  const sorted = Object.entries(parties).sort((a, b) => b[1].mean_seats - a[1].mean_seats);

  let headlineHtml = '';
  sorted.forEach(([name, pr]) => {
    if (pr.mean_seats < 1) return;
    const color = getPartyColor(name);
    headlineHtml += `
      <div class="headline-card" style="border-left: 4px solid ${color}">
        <div class="headline-party">${name}</div>
        <div class="headline-seats">${pr.median_seats}</div>
        <div class="headline-label">${i18n.t('seats_label')} (90% CI: ${pr.percentile_5}–${pr.percentile_95})</div>
        <div class="headline-prob">${(pr.win_probability * 100).toFixed(1)}% ${i18n.t('win_probability')}</div>
        <div class="headline-super">${(pr.supermajority_probability * 100).toFixed(1)}% ${i18n.t('supermajority')}</div>
      </div>`;
  });
  document.getElementById('headline-cards').innerHTML = headlineHtml;

  // Meta info
  document.getElementById('result-meta').innerHTML =
    `${result.n_simulations.toLocaleString()} ${i18n.t('simulations')} | ${result.elapsed_seconds}s | ${result.most_likely_government}`;

  // Seat breakdown table
  let tableHtml = `<tr>
    <th>${i18n.t('party')}</th><th>${i18n.t('mean_seats')}</th><th>${i18n.t('median')}</th>
    <th>${i18n.t('ci_90')}</th><th>${i18n.t('smd')}</th><th>${i18n.t('list')}</th>
    <th>${i18n.t('win_probability')}</th><th>${i18n.t('supermajority')}</th>
  </tr>`;
  sorted.forEach(([name, pr]) => {
    const color = getPartyColor(name);
    tableHtml += `<tr>
      <td><span class="color-dot" style="background:${color}"></span>${name}</td>
      <td><strong>${Math.round(pr.mean_seats)}</strong></td>
      <td>${pr.median_seats}</td>
      <td>${pr.percentile_5}–${pr.percentile_95}</td>
      <td>${Math.round(pr.smd_seats_mean)}</td>
      <td>${Math.round(pr.list_seats_mean)}</td>
      <td>${(pr.win_probability * 100).toFixed(1)}%</td>
      <td>${(pr.supermajority_probability * 100).toFixed(1)}%</td>
    </tr>`;
  });
  document.getElementById('seat-table').innerHTML = tableHtml;

  // Input shares
  let sharesHtml = '';
  Object.entries(result.national_shares_input).sort((a, b) => b[1] - a[1]).forEach(([p, s]) => {
    const color = getPartyColor(p);
    sharesHtml += `<span class="share-badge" style="background:${color}">${p}: ${(s * 100).toFixed(1)}%</span> `;
  });
  document.getElementById('input-shares').innerHTML = sharesHtml;

  // Sync custom share sliders with poll-based values (so they're not all zeros)
  if (!state.useCustomShares) {
    syncSlidersFromShares(result.national_shares_input);
  }

  // Charts
  renderSeatChart(result);

  // Histogram party selector
  const histSelect = document.getElementById('histogram-party');
  if (histSelect) {
    const allLabel = i18n.lang === 'hu' ? 'Osszes part' : 'All Parties';
    histSelect.innerHTML = `<option value="__all__">${allLabel}</option>` +
      sorted.filter(([, pr]) => pr.mean_seats >= 1)
        .map(([name]) => `<option value="${name}">${name}</option>`).join('');
    renderHistogram(result, '__all__');
  }
}

// ── Party Controls (Tab 2) ──────────────────────────────────────────

function renderPartyControls(parties) {
  // Party on/off toggles (always active)
  const toggleContainer = document.getElementById('party-toggles-container');
  let toggleHtml = '';
  parties.forEach(p => {
    const color = getPartyColor(p.short);
    toggleHtml += `
      <div class="party-row" data-party="${p.short}">
        <div class="party-toggle">
          <input type="checkbox" id="toggle-${p.short}" checked
            onchange="toggleParty('${p.short}', this.checked)">
          <label for="toggle-${p.short}" class="party-label">
            <span class="color-dot" style="background:${color}"></span>
            <strong>${p.short}</strong>
            <span class="party-fullname">${p.name}</span>
          </label>
        </div>
      </div>`;
  });
  toggleContainer.innerHTML = toggleHtml;

  // Custom vote share sliders (dimmed unless custom mode)
  const sliderContainer = document.getElementById('party-sliders-container');
  let sliderHtml = '';
  parties.forEach(p => {
    const color = getPartyColor(p.short);
    sliderHtml += `
      <div class="party-row" data-party-slider="${p.short}">
        <div class="party-toggle">
          <span class="color-dot" style="background:${color}"></span>
          <strong>${p.short}</strong>
        </div>
        <div class="party-slider">
          <input type="range" id="slider-${p.short}" min="0" max="60" step="0.5" value="0"
            oninput="updateShare('${p.short}', this.value)">
          <span id="val-${p.short}" class="slider-val">0%</span>
        </div>
      </div>`;
  });
  sliderHtml += `<div class="shares-total">
    <strong data-i18n="total_shares">${i18n.t('total_shares')}</strong>:
    <span id="shares-total-val">0%</span>
  </div>`;
  sliderContainer.innerHTML = sliderHtml;
}

function toggleParty(party, enabled) {
  state.activeParties[party] = enabled;
  const row = document.querySelector(`.party-row[data-party="${party}"]`);
  if (row) row.classList.toggle('disabled-party', !enabled);
}

function updateShare(party, val) {
  state.customShares[party] = parseFloat(val) / 100;
  document.getElementById(`val-${party}`).textContent = val + '%';
  updateTotalShares();
}

function updateTotalShares() {
  const total = Object.values(state.customShares).reduce((a, b) => a + b, 0);
  const el = document.getElementById('shares-total-val');
  if (el) {
    el.textContent = (total * 100).toFixed(1) + '%';
    el.style.color = Math.abs(total - 1.0) < 0.01 ? '#27ae60' : '#e74c3c';
  }
}

function syncSlidersFromShares(shares) {
  Object.entries(shares).forEach(([party, share]) => {
    const pct = (share * 100).toFixed(1);
    state.customShares[party] = share;
    const slider = document.getElementById(`slider-${party}`);
    if (slider) slider.value = pct;
    const valEl = document.getElementById(`val-${party}`);
    if (valEl) valEl.textContent = pct + '%';
  });
  updateTotalShares();
}

// ── Model Parameters (Tab 3) ────────────────────────────────────────

function renderParamControls() {
  const sliders = document.querySelectorAll('.param-slider');
  sliders.forEach(slider => {
    const param = slider.dataset.param;
    if (state.params[param] !== undefined) {
      slider.value = state.params[param];
      const valEl = document.getElementById(`pval-${param}`);
      if (valEl) valEl.textContent = formatParamVal(param, state.params[param]);
    }
    slider.addEventListener('input', () => {
      state.params[param] = parseFloat(slider.value);
      const valEl = document.getElementById(`pval-${param}`);
      if (valEl) valEl.textContent = formatParamVal(param, slider.value);
    });
  });

  // N simulations dropdown
  const nSimSelect = document.getElementById('n-simulations');
  if (nSimSelect) {
    nSimSelect.value = state.params.n_simulations;
    nSimSelect.addEventListener('change', () => {
      state.params.n_simulations = parseInt(nSimSelect.value);
    });
  }
}

function formatParamVal(param, val) {
  if (param.startsWith('urban_swing_') || param.includes('turnout_shift') || param.startsWith('budapest_extra')) {
    const v = parseFloat(val) * 100;
    return (v > 0 ? '+' : '') + v.toFixed(0) + '%';
  }
  if (param.startsWith('sigma_') || param === 'floor_uncertainty') {
    return (parseFloat(val) * 100).toFixed(1) + '%';
  }
  if (param.includes('correlation')) return parseFloat(val).toFixed(2);
  if (param === 'poll_halflife_days') return parseFloat(val).toFixed(0) + 'd';
  return val;
}

function resetDefaults() {
  if (!state.config) return;
  state.params = {
    n_simulations: state.config.n_simulations,
    sigma_polling_error: state.config.sigma_polling_error,
    sigma_regional: state.config.sigma_regional,
    sigma_district: state.config.sigma_district,
    sigma_turnout: state.config.sigma_turnout,
    poll_halflife_days: state.config.poll_halflife_days,
    floor_uncertainty: state.config.floor_uncertainty,
    fidesz_opposition_correlation: state.config.fidesz_opposition_correlation,
    small_party_correlation: state.config.small_party_correlation,
    urban_swing_fidesz: state.config.urban_swing_fidesz,
    urban_swing_tisza: state.config.urban_swing_tisza,
    urban_swing_mi_hazank: state.config.urban_swing_mi_hazank,
    urban_turnout_shift: state.config.urban_turnout_shift,
    rural_turnout_shift: state.config.rural_turnout_shift,
    budapest_extra_swing: state.config.budapest_extra_swing,
  };
  renderParamControls();

  // Reset pollster weights
  Object.entries(state.config.pollsters).forEach(([name, info]) => {
    state.pollsterWeights[name] = info.quality_weight;
    state.pollsterHouseEffects[name] = { ...info.house_effects };
  });
  renderPollsterControls(state.config.pollsters);
}

// ── Pollster Controls (Tab 4) ───────────────────────────────────────

function renderPollsterControls(pollsters) {
  const tbody = document.getElementById('pollster-tbody');
  if (!tbody) return;

  let html = '';
  Object.entries(pollsters).forEach(([name, info]) => {
    const leanClass = info.lean === 'government-aligned' ? 'lean-gov' : 'lean-ind';
    const leanLabel = info.lean === 'government-aligned' ? i18n.t('government_aligned') : i18n.t('independent');
    const weight = state.pollsterWeights[name] ?? info.quality_weight;
    const heFidesz = (state.pollsterHouseEffects[name]?.fidesz ?? info.house_effects?.fidesz ?? 0);
    const heTisza = (state.pollsterHouseEffects[name]?.tisza ?? info.house_effects?.tisza ?? 0);

    html += `<tr>
      <td>${name}</td>
      <td><span class="lean-badge ${leanClass}">${leanLabel}</span></td>
      <td>
        <input type="range" class="pollster-weight" min="0" max="1" step="0.05" value="${weight}"
          data-pollster="${name}" oninput="updatePollsterWeight('${name}', this.value)">
        <span id="pw-${name}">${weight.toFixed(2)}</span>
      </td>
      <td>
        <input type="range" class="pollster-he" min="-10" max="10" step="0.5" value="${heFidesz}"
          oninput="updateHouseEffect('${name}', 'fidesz', this.value)">
        <span id="he-f-${name}">${heFidesz > 0 ? '+' : ''}${heFidesz.toFixed(1)}</span>
      </td>
      <td>
        <input type="range" class="pollster-he" min="-10" max="10" step="0.5" value="${heTisza}"
          oninput="updateHouseEffect('${name}', 'tisza', this.value)">
        <span id="he-t-${name}">${heTisza > 0 ? '+' : ''}${heTisza.toFixed(1)}</span>
      </td>
    </tr>`;
  });
  tbody.innerHTML = html;
}

function updatePollsterWeight(name, val) {
  state.pollsterWeights[name] = parseFloat(val);
  document.getElementById(`pw-${name}`).textContent = parseFloat(val).toFixed(2);
}

function updateHouseEffect(name, party, val) {
  if (!state.pollsterHouseEffects[name]) state.pollsterHouseEffects[name] = {};
  state.pollsterHouseEffects[name][party] = parseFloat(val);
  const prefix = party === 'fidesz' ? 'he-f-' : 'he-t-';
  const el = document.getElementById(prefix + name);
  if (el) el.textContent = (parseFloat(val) > 0 ? '+' : '') + parseFloat(val).toFixed(1);
}

function applyPollsterPreset(preset) {
  if (!state.config) return;
  Object.entries(state.config.pollsters).forEach(([name, info]) => {
    if (preset === 'equal') {
      state.pollsterWeights[name] = 1.0;
      state.pollsterHouseEffects[name] = {};
    } else if (preset === 'default') {
      state.pollsterWeights[name] = info.quality_weight;
      state.pollsterHouseEffects[name] = { ...info.house_effects };
    } else if (preset === 'independent') {
      state.pollsterWeights[name] = info.lean === 'independent' ? 1.0 : 0.0;
      state.pollsterHouseEffects[name] = {};
    }
  });
  renderPollsterControls(state.config.pollsters);
}

// ── Polls Table (Tab 2) ─────────────────────────────────────────────

function renderPollsTable(polls) {
  const tbody = document.getElementById('polls-tbody');
  if (!tbody) return;
  let html = '';
  polls.slice().reverse().forEach(p => {
    html += `<tr>
      <td>${p.date}</td>
      <td>${p.pollster}</td>
      <td>${p.sample_size}</td>
      <td>${(p.fidesz * 100).toFixed(0)}%</td>
      <td>${(p.tisza * 100).toFixed(0)}%</td>
      <td>${(p.mi_hazank * 100).toFixed(0)}%</td>
      <td>${(p.dk * 100).toFixed(0)}%</td>
      <td>${(p.mkkp * 100).toFixed(0)}%</td>
    </tr>`;
  });
  tbody.innerHTML = html;
}

// ── Helpers ──────────────────────────────────────────────────────────

function showError(msg) {
  const el = document.getElementById('error-msg');
  if (el) {
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 8000);
  }
}

// ── Start ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
