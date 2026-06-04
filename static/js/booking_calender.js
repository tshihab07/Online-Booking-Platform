/**
 * Bookify — Public Booking Engine
 * Handles the 4-step booking flow: Service → Date/Time → Staff → Checkout
 */

const Booking = (() => {
  let state = {
    step: 1,
    service: null,
    date: null,
    time: null,
    staff: null,
    slug: document.body.dataset.slug || '',
  };

  // ── Step Navigation ──────────────────────────────────────────────────────

  function goToStep(n) {
    document.querySelectorAll('.booking-step').forEach(el => {
      el.classList.toggle('hidden', parseInt(el.dataset.step) !== n);
    });
    document.querySelectorAll('.step').forEach(el => {
      const s = parseInt(el.dataset.step);
      el.classList.remove('active', 'done');
      if (s === n) el.classList.add('active');
      if (s < n)  el.classList.add('done');
    });
    state.step = n;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ── Step 1: Service Selection ─────────────────────────────────────────────

  function selectService(card) {
    document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.service = {
      id: card.dataset.serviceId,
      name: card.dataset.serviceName,
      price: card.dataset.servicePrice,
      duration: card.dataset.serviceDuration,
    };
    document.getElementById('btn-to-step2').disabled = false;
    document.getElementById('btn-to-step2').classList.remove('opacity-50');
  }

  // ── Step 2: Calendar Heatmap ──────────────────────────────────────────────

  let currentYear, currentMonth;

  async function loadHeatmap(year, month) {
    currentYear = year;
    currentMonth = month;
    const res = await fetch(
      `/b/${state.slug}/api/heatmap/?service_id=${state.service.id}&year=${year}&month=${month}`
    );
    const data = await res.json();
    renderCalendar(year, month, data.heatmap || {});
  }

  function renderCalendar(year, month, heatmap) {
    const grid = document.getElementById('cal-grid');
    const title = document.getElementById('cal-title');
    if (!grid) return;

    const months = ['January','February','March','April','May','June',
                    'July','August','September','October','November','December'];
    title.textContent = `${months[month - 1]} ${year}`;

    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const today = new Date();

    let html = '';
    // Day headers
    ['Su','Mo','Tu','We','Th','Fr','Sa'].forEach(d => {
      html += `<div class="text-center text-xs text-gray-500 font-semibold py-1">${d}</div>`;
    });
    // Empty cells
    for (let i = 0; i < firstDay; i++) html += '<div></div>';

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const status = heatmap[dateStr] || 'closed';
      const isPast = new Date(year, month - 1, d) < new Date(today.getFullYear(), today.getMonth(), today.getDate());
      const dotColor = { green: '#22c55e', orange: '#f59e0b', red: '#ef4444', closed: '#374151' }[status] || '#374151';

      html += `
        <div class="cal-day ${isPast ? 'cal-past' : ''} ${status === 'closed' ? 'cal-closed' : ''}"
             data-date="${dateStr}" data-status="${status}"
             onclick="Booking.selectDate(this)">
          <span>${d}</span>
          <span class="cal-dot" style="background:${dotColor}"></span>
        </div>`;
    }
    grid.innerHTML = html;
  }

  function selectDate(el) {
    if (el.classList.contains('cal-past') || el.classList.contains('cal-closed')) return;
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected'));
    el.classList.add('selected');
    state.date = el.dataset.date;
    loadTimeSlots(state.date);
  }

  async function loadTimeSlots(date) {
    const container = document.getElementById('time-slots');
    if (!container) return;
    container.innerHTML = '<p class="text-gray-400 text-sm">Loading slots…</p>';

    const staffParam = state.staff ? `&staff_id=${state.staff.id}` : '';
    const res = await fetch(
      `/b/${state.slug}/api/availability/?service_id=${state.service.id}&date=${date}${staffParam}`
    );
    const data = await res.json();
    const slots = data.slots || [];

    if (!slots.length) {
      container.innerHTML = '<p class="text-gray-400 text-sm">No available slots for this day.</p>';
      return;
    }

    container.innerHTML = slots.map(s => `
      <button class="time-pill ${!s.available ? 'unavailable' : ''}"
              data-start="${s.start}" data-end="${s.end}"
              ${!s.available ? 'disabled' : ''}
              onclick="Booking.selectTime(this)">
        ${s.start}
      </button>
    `).join('');
  }

  function selectTime(pill) {
    document.querySelectorAll('.time-pill').forEach(p => p.classList.remove('selected'));
    pill.classList.add('selected');
    state.time = { start: pill.dataset.start, end: pill.dataset.end };
    document.getElementById('btn-to-step3').disabled = false;
    document.getElementById('btn-to-step3').classList.remove('opacity-50');
  }

  // ── Step 3: Staff Selection ───────────────────────────────────────────────

  function selectStaff(card) {
    document.querySelectorAll('.staff-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.staff = { id: card.dataset.staffId, name: card.dataset.staffName };
    // Reload time slots with staff filter
    if (state.date) loadTimeSlots(state.date);
    document.getElementById('btn-to-step4').disabled = false;
    document.getElementById('btn-to-step4').classList.remove('opacity-50');
  }

  function skipStaff() {
    state.staff = null;
    document.querySelectorAll('.staff-card').forEach(c => c.classList.remove('selected'));
    document.getElementById('btn-to-step4').disabled = false;
    document.getElementById('btn-to-step4').classList.remove('opacity-50');
  }

  // ── Step 4: Checkout ──────────────────────────────────────────────────────

  function openCheckout() {
    // Populate order summary
    document.getElementById('summary-service').textContent = state.service.name;
    document.getElementById('summary-date').textContent = state.date;
    document.getElementById('summary-time').textContent = state.time.start;
    document.getElementById('summary-staff').textContent = state.staff ? state.staff.name : 'Any available';
    document.getElementById('summary-price').textContent = `$${parseFloat(state.service.price).toFixed(2)}`;
    document.getElementById('summary-duration').textContent = `${state.service.duration} min`;

    document.getElementById('checkout-panel').classList.add('open');
    document.getElementById('checkout-overlay').classList.add('open');
  }

  function closeCheckout() {
    document.getElementById('checkout-panel').classList.remove('open');
    document.getElementById('checkout-overlay').classList.remove('open');
  }

  async function submitBooking(e) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('[type=submit]');
    btn.disabled = true;
    btn.textContent = 'Confirming…';

    const body = new FormData(form);
    body.append('service_id', state.service.id);
    body.append('date', state.date);
    body.append('start_time', state.time.start);
    if (state.staff) body.append('staff_id', state.staff.id);

    try {
      const res = await fetch(`/b/${state.slug}/book/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body,
      });
      const data = await res.json();
      if (data.success) {
        window.location.href = data.redirect;
      } else {
        showError(data.error || 'Something went wrong. Please try again.');
        btn.disabled = false;
        btn.textContent = 'Confirm Booking';
      }
    } catch {
      showError('Network error. Please try again.');
      btn.disabled = false;
      btn.textContent = 'Confirm Booking';
    }
  }

  function showError(msg) {
    let el = document.getElementById('booking-error');
    if (!el) {
      el = document.createElement('div');
      el.id = 'booking-error';
      el.className = 'mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm';
      document.getElementById('checkout-form').prepend(el);
    }
    el.textContent = msg;
  }

  // ── Social Proof Ticker ───────────────────────────────────────────────────

  function initTicker(feedJson) {
    const feed = JSON.parse(feedJson || '[]');
    if (!feed.length) return;
    const ticker = document.getElementById('ticker-content');
    if (!ticker) return;
    const items = feed.map(f =>
      `<span class="inline-flex items-center gap-2 mx-8 text-sm opacity-80">
        <span class="w-2 h-2 rounded-full bg-green-400 inline-block"></span>
        <strong>${f.name}</strong> just booked <em>${f.service}</em> — ${f.time_ago}
      </span>`
    ).join('');
    ticker.innerHTML = items + items; // duplicate for seamless loop
  }

  // ── Utility ───────────────────────────────────────────────────────────────

  function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
  }

  // ── Init ──────────────────────────────────────────────────────────────────

  function init() {
    const today = new Date();
    currentYear = today.getFullYear();
    currentMonth = today.getMonth() + 1;

    // Prev/Next month buttons
    const prevBtn = document.getElementById('cal-prev');
    const nextBtn = document.getElementById('cal-next');
    if (prevBtn) prevBtn.addEventListener('click', () => {
      currentMonth--;
      if (currentMonth < 1) { currentMonth = 12; currentYear--; }
      if (state.service) loadHeatmap(currentYear, currentMonth);
    });
    if (nextBtn) nextBtn.addEventListener('click', () => {
      currentMonth++;
      if (currentMonth > 12) { currentMonth = 1; currentYear++; }
      if (state.service) loadHeatmap(currentYear, currentMonth);
    });

    // Checkout form
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) checkoutForm.addEventListener('submit', submitBooking);

    // Overlay close
    const overlay = document.getElementById('checkout-overlay');
    if (overlay) overlay.addEventListener('click', closeCheckout);

    // Ticker
    const tickerData = document.getElementById('ticker-data');
    if (tickerData) initTicker(tickerData.textContent);
  }

  return {
    init, goToStep, selectService, selectDate, selectTime,
    selectStaff, skipStaff, openCheckout, closeCheckout,
    loadHeatmap, loadTimeSlots,
  };
})();

document.addEventListener('DOMContentLoaded', Booking.init);
