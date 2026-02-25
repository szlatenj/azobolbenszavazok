/**
 * Bilingual translation system (HU/EN).
 */
const translations = {
  // Header
  'title': {
    hu: 'Magyar Valasztasi Szimulator',
    en: 'Hungarian Election Simulator',
  },
  'subtitle': {
    hu: 'Monte Carlo valasztasi elorejelzes - 2026',
    en: 'Monte Carlo Election Forecast - 2026',
  },
  'run_simulation': { hu: 'Szimulacio futtatasa', en: 'Run Simulation' },
  'running': { hu: 'Fut...', en: 'Running...' },

  // Tabs
  'tab_results': { hu: 'Eredmenyek', en: 'Results' },
  'tab_polling': { hu: 'Kozvelemenykutatasok', en: 'Polling & Votes' },
  'tab_params': { hu: 'Modell parameterek', en: 'Model Parameters' },
  'tab_pollsters': { hu: 'Kutatok sulyozasa', en: 'Pollster Weights' },
  'tab_methodology': { hu: 'Modszertan', en: 'Methodology' },

  // Results tab
  'results_headline': { hu: 'Elorejelzes osszefoglalo', en: 'Forecast Summary' },
  'win_probability': { hu: 'Gyozelmi eselye', en: 'Win Probability' },
  'supermajority': { hu: 'Ketharmad eselye', en: 'Supermajority' },
  'no_majority': { hu: 'Nincs tobbseg', en: 'No Majority' },
  'most_likely': { hu: 'Legvaloszinubb kimenetel', en: 'Most Likely Outcome' },
  'seat_distribution': { hu: 'Mandatummegoszlas', en: 'Seat Distribution' },
  'seat_breakdown': { hu: 'Mandatum reszletezese', en: 'Seat Breakdown' },
  'party': { hu: 'Part', en: 'Party' },
  'mean_seats': { hu: 'Atlag', en: 'Mean' },
  'median': { hu: 'Median', en: 'Median' },
  'ci_90': { hu: '90% CI', en: '90% CI' },
  'smd': { hu: 'OEVK', en: 'SMD' },
  'list': { hu: 'Lista', en: 'List' },
  'total': { hu: 'Ossz.', en: 'Total' },
  'simulations': { hu: 'szimulacio', en: 'simulations' },
  'elapsed': { hu: 'Ido', en: 'Time' },
  'majority_line': { hu: 'Tobbseg (100)', en: 'Majority (100)' },
  'supermajority_line': { hu: 'Ketharmad (133)', en: 'Supermajority (133)' },
  'input_shares': { hu: 'Bemeneti szavazataranyok', en: 'Input Vote Shares' },
  'seats_label': { hu: 'mandatum', en: 'seats' },

  // Polling tab
  'polling_title': { hu: 'Szavazataranyok es partok', en: 'Vote Shares & Parties' },
  'use_polls': { hu: 'Kozvelemenykutatasok hasznalata', en: 'Use Poll Data' },
  'use_custom': { hu: 'Egyeni aranyok', en: 'Custom Shares' },
  'party_toggles': { hu: 'Partok ki/be kapcsolasa', en: 'Party Toggles' },
  'enabled': { hu: 'Aktiv', en: 'Enabled' },
  'disabled': { hu: 'Inaktiv', en: 'Disabled' },
  'total_shares': { hu: 'Osszes', en: 'Total' },
  'poll_average': { hu: 'Kozvelemenykutatasi atlag', en: 'Poll Average' },

  // Params tab
  'params_title': { hu: 'Modell parameterek', en: 'Model Parameters' },
  'poll_aggregation': { hu: 'Kozvelemenykutatas sulyozas', en: 'Poll Aggregation' },
  'poll_halflife': { hu: 'Felezesi ido (nap)', en: 'Poll Half-life (days)' },
  'floor_uncertainty': { hu: 'Minimalis bizonytalansag', en: 'Floor Uncertainty' },
  'error_structure': { hu: 'Hibastruktura (Nate Silver-modell)', en: 'Error Structure (Nate Silver-style)' },
  'national_error': { hu: 'Orszagos kozvelemenykutatasi hiba (sigma)', en: 'National Polling Error (sigma)' },
  'regional_swing': { hu: 'Regionalis elteres (sigma)', en: 'Regional Swing (sigma)' },
  'district_noise': { hu: 'Keruleti zaj (sigma)', en: 'District Noise (sigma)' },
  'turnout_var': { hu: 'Reszveteli valtozas (sigma)', en: 'Turnout Variation (sigma)' },
  'correlations': { hu: 'Korrelaciok', en: 'Correlations' },
  'fidesz_opp_corr': { hu: 'Fidesz-Ellenzek korrelacio', en: 'Fidesz-Opposition Correlation' },
  'small_party_corr': { hu: 'Kispartok kozotti korrelacio', en: 'Small Party Correlation' },
  'sim_settings': { hu: 'Szimulacio beallitasok', en: 'Simulation Settings' },
  'n_simulations': { hu: 'Szimulacok szama', en: 'Number of Simulations' },
  'random_seed': { hu: 'Random seed (opcionalis)', en: 'Random Seed (optional)' },
  'reset_defaults': { hu: 'Alapertelmezes visszaallitasa', en: 'Reset to Defaults' },

  // Voter behavior change
  'voter_behavior': { hu: 'Szavazoi viselkedes valtozas', en: 'Voter Behavior Change' },
  'urban_swing_fidesz': { hu: 'Fidesz varosi swing (vs. videk)', en: 'Fidesz Urban Swing (vs. rural)' },
  'urban_swing_tisza': { hu: 'Tisza varosi swing (vs. videk)', en: 'Tisza Urban Swing (vs. rural)' },
  'urban_swing_mi_hazank': { hu: 'Mi Hazank varosi swing (vs. videk)', en: 'Mi Hazank Urban Swing (vs. rural)' },
  'urban_turnout_shift': { hu: 'Varosi reszveteli eltolas', en: 'Urban Turnout Shift' },
  'rural_turnout_shift': { hu: 'Videki reszveteli eltolas', en: 'Rural Turnout Shift' },
  'budapest_extra_swing': { hu: 'Budapest extra ellenzeki swing', en: 'Budapest Extra Opposition Swing' },

  // Pollster tab
  'pollster_title': { hu: 'Kozvelemenykutatok sulyozasa', en: 'Pollster Weights & House Effects' },
  'pollster_name': { hu: 'Kutato', en: 'Pollster' },
  'pollster_lean': { hu: 'Besorolas', en: 'Lean' },
  'quality_weight': { hu: 'Minosegi suly', en: 'Quality Weight' },
  'house_fidesz': { hu: 'Fidesz hatasertek', en: 'Fidesz House Effect' },
  'house_tisza': { hu: 'Tisza hatasertek', en: 'Tisza House Effect' },
  'preset_equal': { hu: 'Egyenlo sulyozas', en: 'Trust All Equally' },
  'preset_default': { hu: 'Alapertelmezett', en: 'Default (Adjusted)' },
  'preset_independent': { hu: 'Csak fuggetlen', en: 'Independent Only' },
  'independent': { hu: 'Fuggetlen', en: 'Independent' },
  'government_aligned': { hu: 'Kormanykozeli', en: 'Gov-aligned' },
};

const i18n = {
  lang: 'hu',

  t(key) {
    const entry = translations[key];
    if (!entry) return key;
    return entry[this.lang] || entry['en'] || key;
  },

  toggle() {
    this.lang = this.lang === 'hu' ? 'en' : 'hu';
    this.applyAll();
    localStorage.setItem('sim-lang', this.lang);
  },

  applyAll() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = this.t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = this.t(el.dataset.i18nPlaceholder);
    });
    const btn = document.getElementById('lang-toggle');
    if (btn) btn.textContent = this.lang === 'hu' ? 'EN' : 'HU';

    // Update methodology content
    const methuBlock = document.getElementById('methodology-hu');
    const metenBlock = document.getElementById('methodology-en');
    if (methuBlock && metenBlock) {
      methuBlock.style.display = this.lang === 'hu' ? 'block' : 'none';
      metenBlock.style.display = this.lang === 'en' ? 'block' : 'none';
      // Re-render KaTeX in the newly visible block
      if (typeof renderMathInElement === 'function') {
        const visible = this.lang === 'hu' ? methuBlock : metenBlock;
        renderMathInElement(visible, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
          ],
        });
      }
    }
  },

  init() {
    const saved = localStorage.getItem('sim-lang');
    if (saved) this.lang = saved;
    this.applyAll();
  },
};
