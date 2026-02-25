/**
 * Chart.js visualization helpers for election simulation results.
 */

const PARTY_COLORS = {
  fidesz: '#FD8100',
  tisza: '#00A3E0',
  mi_hazank: '#2E8B57',
  dk: '#0044AA',
  mkkp: '#888888',
  other: '#BBBBBB',
  opposition: '#1E90FF',
};

function getPartyColor(party) {
  return PARTY_COLORS[party] || '#999999';
}

let seatChart = null;
let histogramChart = null;

function renderSeatChart(result) {
  const ctx = document.getElementById('seat-chart');
  if (!ctx) return;

  if (seatChart) seatChart.destroy();

  const parties = Object.keys(result.parties).sort(
    (a, b) => result.parties[b].mean_seats - result.parties[a].mean_seats
  );

  const data = {
    labels: parties,
    datasets: [
      {
        label: i18n.t('smd'),
        data: parties.map(p => result.parties[p].smd_seats_mean),
        backgroundColor: parties.map(p => getPartyColor(p) + 'CC'),
        borderWidth: 0,
      },
      {
        label: i18n.t('list'),
        data: parties.map(p => result.parties[p].list_seats_mean),
        backgroundColor: parties.map(p => getPartyColor(p) + '77'),
        borderWidth: 0,
      },
    ],
  };

  seatChart = new Chart(ctx, {
    type: 'bar',
    data,
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          max: 199,
          grid: { color: '#eee' },
        },
        y: {
          stacked: true,
          grid: { display: false },
        },
      },
      plugins: {
        legend: { position: 'bottom' },
        annotation: {
          annotations: {
            majority: {
              type: 'line',
              xMin: 100,
              xMax: 100,
              borderColor: '#e74c3c',
              borderWidth: 2,
              borderDash: [6, 3],
              label: {
                display: true,
                content: '100',
                position: 'start',
                backgroundColor: '#e74c3c',
                color: '#fff',
                font: { size: 10 },
              },
            },
            supermajority: {
              type: 'line',
              xMin: 133,
              xMax: 133,
              borderColor: '#8e44ad',
              borderWidth: 2,
              borderDash: [6, 3],
              label: {
                display: true,
                content: '133',
                position: 'start',
                backgroundColor: '#8e44ad',
                color: '#fff',
                font: { size: 10 },
              },
            },
          },
        },
      },
    },
  });
}

function renderHistogram(result, party) {
  const ctx = document.getElementById('histogram-chart');
  if (!ctx) return;
  if (histogramChart) histogramChart.destroy();

  if (party === '__all__') {
    renderAllPartiesHistogram(result);
    return;
  }

  const pr = result.parties[party];
  if (!pr) return;

  const dist = pr.seat_distribution;
  const min = Math.min(...dist);
  const max = Math.max(...dist);
  const binSize = 2;
  const bins = [];
  const counts = [];

  for (let b = min; b <= max; b += binSize) {
    bins.push(b);
    counts.push(dist.filter(v => v >= b && v < b + binSize).length);
  }

  histogramChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: bins.map(b => `${b}-${b + binSize - 1}`),
      datasets: [{
        label: `${party} seats`,
        data: counts,
        backgroundColor: getPartyColor(party) + '99',
        borderColor: getPartyColor(party),
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: 'Seats' },
          ticks: { maxTicksLimit: 20 },
        },
        y: {
          title: { display: true, text: 'Frequency' },
        },
      },
      plugins: {
        legend: { display: false },
        annotation: {
          annotations: {
            majority: {
              type: 'line',
              xMin: bins.indexOf(bins.find(b => b >= 100 && b < 100 + binSize)),
              xMax: bins.indexOf(bins.find(b => b >= 100 && b < 100 + binSize)),
              borderColor: '#e74c3c',
              borderWidth: 2,
              borderDash: [4, 4],
            },
            supermajority: {
              type: 'line',
              xMin: bins.indexOf(bins.find(b => b >= 133 && b < 133 + binSize)),
              xMax: bins.indexOf(bins.find(b => b >= 133 && b < 133 + binSize)),
              borderColor: '#8e44ad',
              borderWidth: 2,
              borderDash: [4, 4],
            },
          },
        },
      },
    },
  });
}

function renderAllPartiesHistogram(result) {
  const ctx = document.getElementById('histogram-chart');
  if (!ctx) return;

  const binSize = 3;
  const globalMin = 0;
  const globalMax = 199;
  const bins = [];
  for (let b = globalMin; b <= globalMax; b += binSize) bins.push(b);
  const labels = bins.map(b => `${b}`);

  const parties = Object.entries(result.parties)
    .filter(([, pr]) => pr.mean_seats >= 1)
    .sort((a, b) => b[1].mean_seats - a[1].mean_seats);

  const datasets = parties.map(([name, pr]) => {
    const dist = pr.seat_distribution;
    const counts = bins.map(b => dist.filter(v => v >= b && v < b + binSize).length);
    return {
      label: name,
      data: counts,
      backgroundColor: getPartyColor(name) + '55',
      borderColor: getPartyColor(name),
      borderWidth: 1.5,
    };
  });

  histogramChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: 'Seats' },
          ticks: { maxTicksLimit: 25 },
        },
        y: {
          title: { display: true, text: 'Frequency' },
        },
      },
      plugins: {
        legend: { position: 'bottom' },
        annotation: {
          annotations: {
            majority: {
              type: 'line',
              xMin: Math.floor(100 / binSize),
              xMax: Math.floor(100 / binSize),
              borderColor: '#e74c3c',
              borderWidth: 2,
              borderDash: [6, 3],
              label: { display: true, content: '100', backgroundColor: '#e74c3c', color: '#fff', font: { size: 10 } },
            },
            supermajority: {
              type: 'line',
              xMin: Math.floor(133 / binSize),
              xMax: Math.floor(133 / binSize),
              borderColor: '#8e44ad',
              borderWidth: 2,
              borderDash: [6, 3],
              label: { display: true, content: '133', backgroundColor: '#8e44ad', color: '#fff', font: { size: 10 } },
            },
          },
        },
      },
    },
  });
}
