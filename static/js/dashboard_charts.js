/**
 * Bookify — Dashboard Charts
 * Renders all analytics charts using Chart.js
 */

const DashboardCharts = (() => {

  const COLORS = {
    primary:   '#6366f1',
    secondary: '#8b5cf6',
    accent:    '#06b6d4',
    green:     '#22c55e',
    yellow:    '#f59e0b',
    red:       '#ef4444',
    blue:      '#3b82f6',
    gray:      '#6b7280',
  };

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#e8eaf6', font: { family: 'Inter', size: 12 } },
      },
      tooltip: {
        backgroundColor: '#1a1a2e',
        borderColor: '#2a2a4a',
        borderWidth: 1,
        titleColor: '#e8eaf6',
        bodyColor: '#a5b4fc',
        padding: 12,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: '#7986cb', font: { size: 11 } },
        grid:  { color: 'rgba(42,42,74,0.5)' },
      },
      y: {
        ticks: { color: '#7986cb', font: { size: 11 } },
        grid:  { color: 'rgba(42,42,74,0.5)' },
      },
    },
  };

  // ── Revenue Line Chart ────────────────────────────────────────────────────

  function initRevenueChart(canvasId, rawData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const data = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
    const labels = Object.keys(data).map(d => {
      const dt = new Date(d);
      return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const values = Object.values(data);

    new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Revenue ($)',
          data: values,
          borderColor: COLORS.primary,
          backgroundColor: 'rgba(99,102,241,0.1)',
          borderWidth: 2.5,
          pointBackgroundColor: COLORS.primary,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.4,
        }],
      },
      options: {
        ...defaultOptions,
        plugins: {
          ...defaultOptions.plugins,
          legend: { display: false },
        },
      },
    });
  }

  // ── Bookings by Service Bar Chart ─────────────────────────────────────────

  function initServiceChart(canvasId, rawData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const data = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data.map(d => d.name),
        datasets: [{
          label: 'Bookings',
          data: data.map(d => d.count),
          backgroundColor: [
            COLORS.primary, COLORS.secondary, COLORS.accent,
            COLORS.green, COLORS.yellow, COLORS.red, COLORS.blue, COLORS.gray,
          ],
          borderRadius: 8,
          borderSkipped: false,
        }],
      },
      options: {
        ...defaultOptions,
        plugins: { ...defaultOptions.plugins, legend: { display: false } },
        scales: {
          ...defaultOptions.scales,
          y: { ...defaultOptions.scales.y, beginAtZero: true },
        },
      },
    });
  }

  // ── Status Donut Chart ────────────────────────────────────────────────────

  function initStatusChart(canvasId, rawData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const data = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;

    const statusColors = {
      confirmed:   COLORS.green,
      pending:     COLORS.yellow,
      in_progress: COLORS.blue,
      completed:   COLORS.primary,
      cancelled:   COLORS.red,
      no_show:     '#dc2626',
    };

    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = labels.map(l => statusColors[l] || COLORS.gray);

    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: labels.map(l => l.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())),
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: '#1a1a2e',
          borderWidth: 3,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#e8eaf6', font: { size: 11 }, padding: 16, boxWidth: 12 },
          },
          tooltip: defaultOptions.plugins.tooltip,
        },
      },
    });
  }

  // ── New vs Returning Donut ────────────────────────────────────────────────

  function initCustomerChart(canvasId, newCount, returningCount) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['New Customers', 'Returning'],
        datasets: [{
          data: [newCount, returningCount],
          backgroundColor: [COLORS.accent, COLORS.primary],
          borderColor: '#1a1a2e',
          borderWidth: 3,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#e8eaf6', font: { size: 11 }, padding: 16, boxWidth: 12 },
          },
          tooltip: defaultOptions.plugins.tooltip,
        },
      },
    });
  }

  return { initRevenueChart, initServiceChart, initStatusChart, initCustomerChart };
})();
