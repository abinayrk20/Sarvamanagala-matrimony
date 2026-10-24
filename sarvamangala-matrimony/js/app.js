/**
 * Sarvamangala Matrimony – Kanchipuram
 * Full-Stack Matrimonial Web Application Client Logic
 */

class SarvamangalaApp {
  constructor() {
    this.currentUser = null;
    this.token = localStorage.getItem("sm_auth_token") || "";
    this.currentLanguage = localStorage.getItem("sm_lang") || "en";
    this.activeFilter = "all";
    this.profiles = [];
    this.currentPage = 1;
    this.totalPages = 1;
    this.activeProfile = null;
    this.regData = {};
    this.regPaymentId = null;
    this.pollInterval = null;
    this.init();
  }

  async init() {
    this.bindEvents();
    this.initScrollEffects();
    await this.checkAuthSession();
    await this.loadMatches();
    await this.loadTestimonials();
    await this.loadPlans();
    this.setupRouteHandling();
  }

  // --------------------------------------------------------------------------
  // Authentication & Session Management
  // --------------------------------------------------------------------------
  async checkAuthSession() {
    if (!this.token) {
      this.updateHeaderAuthUI(null);
      return;
    }
    try {
      const res = await fetch("/api/auth/me", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      if (data.authenticated && data.user) {
        this.currentUser = data.user;
        this.updateHeaderAuthUI(this.currentUser);
        this.loadUserNotifications();
      } else {
        this.logout(false);
      }
    } catch (e) {
      console.warn("Auth check error:", e);
    }
  }

  updateHeaderAuthUI(user) {
    const guestNav = document.getElementById("header-guest-actions");
    const userNav = document.getElementById("header-user-actions");
    const userNameSpan = document.getElementById("header-user-name");
    const userAvatar = document.getElementById("header-user-avatar");

    if (user && userNav && guestNav) {
      guestNav.classList.add("hidden");
      userNav.classList.remove("hidden");
      if (userNameSpan) userNameSpan.textContent = user.name || "Member";
      if (userAvatar && user.profile && user.profile.photo_url) {
        userAvatar.src = user.profile.photo_url;
      }
    } else if (guestNav && userNav) {
      guestNav.classList.remove("hidden");
      userNav.classList.add("hidden");
    }
  }

  async handleLogin(e) {
    e.preventDefault();
    const identifier = document.getElementById("login-identifier").value.trim();
    const password = document.getElementById("login-password").value;
    const alertBox = document.getElementById("login-alert");
    const alertMsg = document.getElementById("login-alert-msg");

    if (alertBox) alertBox.classList.add("hidden");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, password })
      });
      const data = await res.json();

      if (data.success) {
        if (data.is_admin) {
          window.location.href = "/sm-admin";
          return;
        }
        this.token = data.token;
        localStorage.setItem("sm_auth_token", data.token);
        this.currentUser = data.user;
        this.currentUser.profile = data.profile;
        this.updateHeaderAuthUI(this.currentUser);
        this.closeLoginModal();
        this.showToast(`Welcome back, ${data.user.name}!`, "success");
        this.openDashboardModal();
        this.loadMatches();
      } else if (data.payment_required) {
        // GPay payment pending
        this.closeLoginModal();
        this.showToast(data.error, "info");
        this.openGPayPaymentStep(data.registration_id);
      } else if (data.payment_pending_verification) {
        this.closeLoginModal();
        this.showToast(data.error, "info");
        this.openPaymentVerificationStatusStep(data.registration_id);
      } else {
        if (alertBox && alertMsg) {
          alertMsg.textContent = data.error || "Invalid login credentials.";
          alertBox.classList.remove("hidden");
        } else {
          this.showToast(data.error || "Login failed", "error");
        }
      }
    } catch (err) {
      this.showToast("Network error. Please try again.", "error");
    }
  }

  async logout(notify = true) {
    if (this.token) {
      try {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: { "Authorization": `Bearer ${this.token}` }
        });
      } catch (e) {}
    }
    this.token = "";
    this.currentUser = null;
    localStorage.removeItem("sm_auth_token");
    this.updateHeaderAuthUI(null);
    this.closeDashboardModal();
    if (notify) this.showToast("Logged out successfully.", "info");
    this.loadMatches();
  }

  // --------------------------------------------------------------------------
  // Registration & Mandatory ₹2,000 GPay Payment Workflow
  // --------------------------------------------------------------------------
  openRegistrationModal() {
    const modal = document.getElementById("register-modal");
    if (modal) {
      this.resetRegSteps();
      modal.showModal();
    }
  }

  closeRegistrationModal() {
    const modal = document.getElementById("register-modal");
    if (modal) modal.close();
    if (this.pollInterval) clearInterval(this.pollInterval);
  }

  resetRegSteps() {
    document.getElementById("reg-step-1")?.classList.remove("hidden");
    document.getElementById("reg-step-2")?.classList.add("hidden");
    document.getElementById("reg-step-3")?.classList.add("hidden");
    const form = document.getElementById("registration-form");
    if (form) form.reset();
  }

  async handleRegistrationSubmit(e) {
    e.preventDefault();
    const name = document.getElementById("reg-name")?.value.trim();
    const dob = document.getElementById("reg-dob")?.value;
    const gender = document.getElementById("reg-gender")?.value;
    const email = document.getElementById("reg-email")?.value.trim();
    const phone = document.getElementById("reg-phone")?.value.trim();
    const password = document.getElementById("reg-password")?.value;
    const confirm = document.getElementById("reg-confirm-password")?.value;
    const caste = document.getElementById("reg-caste")?.value;
    const district = document.getElementById("reg-district")?.value;
    const education = document.getElementById("reg-education")?.value.trim();
    const occupation = document.getElementById("reg-occupation")?.value.trim();

    if (password !== confirm) {
      this.showToast("Passwords do not match!", "error");
      return;
    }

    const payload = { name, dob, gender, email, phone, password, caste, district, education, occupation };
    this.regData = payload;

    const submitBtn = document.getElementById("btn-submit-reg");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = "Creating Profile...";
    }

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Proceed to GPay Payment (₹2,000)</span> <span>→</span>`;
      }

      if (data.success) {
        this.regPaymentId = data.registration_id;
        this.openGPayPaymentStep(data.registration_id, data.payment);
      } else {
        this.showToast(data.error || "Registration error", "error");
      }
    } catch (err) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Proceed to GPay Payment (₹2,000)</span> <span>→</span>`;
      }
      this.showToast("Failed to connect to server. Please try again.", "error");
    }
  }

  openGPayPaymentStep(regId, paymentInfo) {
    const step1 = document.getElementById("reg-step-1");
    const step2 = document.getElementById("reg-step-2");
    const step3 = document.getElementById("reg-step-3");
    if (step1) step1.classList.add("hidden");
    if (step3) step3.classList.add("hidden");
    if (step2) step2.classList.remove("hidden");

    this.regPaymentId = regId;
    document.getElementById("gpay-reg-id-display").textContent = regId;

    const upiLink = paymentInfo?.upi_intent || `upi://pay?pa=9942006877@upi&pn=Sarvamangala%20Matrimony&am=2000&cu=INR&tn=${regId}`;
    const btnUpi = document.getElementById("btn-gpay-intent");
    if (btnUpi) btnUpi.href = upiLink;

    // Generate QR Code via reliable SVG/image API
    const qrImg = document.getElementById("gpay-qr-code");
    if (qrImg) {
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(upiLink)}`;
    }
  }

  async handleGPayPaymentSubmission(e) {
    e.preventDefault();
    const txnRef = document.getElementById("gpay-txn-ref")?.value.trim();
    if (!txnRef) {
      this.showToast("Please enter the 12-digit UPI Transaction / UTR Reference number.", "error");
      return;
    }

    try {
      const res = await fetch("/api/auth/submit-payment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ registration_id: this.regPaymentId, txn_ref: txnRef })
      });
      const data = await res.json();
      if (data.success) {
        this.openPaymentVerificationStatusStep(this.regPaymentId, txnRef);
      } else {
        this.showToast(data.error || "Submission failed", "error");
      }
    } catch (err) {
      this.showToast("Network error submitting reference", "error");
    }
  }

  openPaymentVerificationStatusStep(regId, txnRef = "") {
    const step2 = document.getElementById("reg-step-2");
    const step3 = document.getElementById("reg-step-3");
    if (step2) step2.classList.add("hidden");
    if (step3) step3.classList.remove("hidden");

    this.regPaymentId = regId;
    document.getElementById("verif-reg-id").textContent = regId;
    if (txnRef) document.getElementById("verif-txn-ref").textContent = txnRef;

    // Start polling status
    if (this.pollInterval) clearInterval(this.pollInterval);
    this.checkPaymentStatus(regId);
    this.pollInterval = setInterval(() => this.checkPaymentStatus(regId), 5000);
  }

  async checkPaymentStatus(regId) {
    try {
      const res = await fetch(`/api/auth/payment-status?reg_id=${regId}`);
      const data = await res.json();
      if (data.status === "PAID") {
        clearInterval(this.pollInterval);
        this.renderPaymentVerifiedSuccess(data);
      } else if (data.status === "FAILED") {
        clearInterval(this.pollInterval);
        document.getElementById("verif-status-badge").className = "bg-rose-100 text-rose-800 text-xs font-bold px-3 py-1 rounded-full border border-rose-300";
        document.getElementById("verif-status-badge").textContent = "Payment Verification Rejected";
        document.getElementById("verif-status-desc").textContent = "The submitted transaction reference could not be verified in our GPay statement. Please re-check or contact 8248853928.";
      }
    } catch (e) {}
  }

  renderPaymentVerifiedSuccess(data) {
    const container = document.getElementById("verif-status-container");
    if (!container) return;

    container.innerHTML = `
      <div class="text-center space-y-4">
        <div class="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-3xl mx-auto border-2 border-emerald-400 animate-bounce">
          ✓
        </div>
        <div>
          <span class="bg-emerald-100 text-emerald-800 text-xs font-extrabold px-3 py-1 rounded-full border border-emerald-300">
            Payment Verified & Account Active
          </span>
          <h3 class="font-heading text-xl font-bold text-maroon-950 mt-2">Registration Successful!</h3>
          <p class="text-xs text-gray-600 mt-1">Your ₹2,000 registration fee has been confirmed via Google Pay. Your matrimonial profile is now active across Tamil Nadu.</p>
        </div>

        <!-- Official Payment Receipt -->
        <div class="bg-white p-5 rounded-2xl border-2 border-gold-400 text-left space-y-2 text-xs shadow-md">
          <div class="flex items-center justify-between border-b border-sandal-200 pb-2">
            <span class="font-heading font-bold text-maroon-900">Sarvamangala Matrimony</span>
            <span class="text-[10px] text-gray-500 font-mono">Receipt: ${data.receipt_number || "RCP-2026-LIVE"}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-gray-700">
            <div><span class="text-gray-400 block text-[10px]">Candidate Name</span><strong>${data.applicant_name}</strong></div>
            <div><span class="text-gray-400 block text-[10px]">Registration ID</span><strong class="font-mono text-maroon-900">${data.registration_id}</strong></div>
            <div><span class="text-gray-400 block text-[10px]">Payment Method</span><strong>Google Pay (UPI)</strong></div>
            <div><span class="text-gray-400 block text-[10px]">Amount Paid</span><strong class="text-emerald-700 font-bold">₹2,000.00 (PAID)</strong></div>
            <div class="col-span-2"><span class="text-gray-400 block text-[10px]">UPI Reference</span><strong class="font-mono">${data.txn_ref || "-"}</strong></div>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button onclick="window.print()" class="text-xs font-bold py-2.5 px-4 rounded-xl border border-gray-300 bg-white hover:bg-gray-50 flex items-center gap-1.5 shadow-sm">
            <span>🖨️</span> Print Official Receipt
          </button>
          <button onclick="window.smApp.closeRegistrationModal(); window.smApp.openLoginModal()" class="text-xs font-bold py-2.5 px-6 rounded-xl bg-maroon-900 text-gold-300 hover:bg-maroon-800 flex items-center gap-1.5 shadow">
            <span>🔑</span> Proceed to Member Login
          </button>
        </div>
      </div>
    `;
    this.showToast("Registration payment verified! Profile activated.", "success");
  }

  // --------------------------------------------------------------------------
  // Matches Directory & Filtering
  // --------------------------------------------------------------------------
  async loadMatches(page = 1) {
    this.currentPage = page;
    const gender = this.activeFilter;
    const ageMin = document.getElementById("filter-age-min")?.value || 18;
    const ageMax = document.getElementById("filter-age-max")?.value || 60;
    const district = document.getElementById("filter-district")?.value || "all";
    const caste = document.getElementById("filter-caste")?.value || "all";
    const timeline = document.getElementById("filter-timeline")?.value || "all";
    const search = document.getElementById("search-input")?.value || "";

    const grid = document.getElementById("profiles-grid");
    if (!grid) return;

    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-gray-500">
        <div class="inline-block w-8 h-8 border-4 border-gold-400 border-t-maroon-800 rounded-full animate-spin mb-3"></div>
        <p class="text-xs font-semibold">Loading verified Tamil Hindu profiles...</p>
      </div>
    `;

    try {
      const url = `/api/matches?gender=${gender}&age_min=${ageMin}&age_max=${ageMax}&district=${encodeURIComponent(district)}&caste=${encodeURIComponent(caste)}&timeline=${encodeURIComponent(timeline)}&q=${encodeURIComponent(search)}&page=${page}&limit=8`;
      const res = await fetch(url, {
        headers: this.token ? { "Authorization": `Bearer ${this.token}` } : {}
      });
      const data = await res.json();
      this.profiles = data.profiles || [];
      this.totalPages = data.total_pages || 1;

      const countEl = document.getElementById("matches-count-badge");
      if (countEl) countEl.textContent = `${data.total || 0} Verified Profiles`;

      this.renderProfiles(this.profiles);
      this.renderPagination(data.total, page, this.totalPages);
    } catch (err) {
      grid.innerHTML = `<div class="col-span-full py-12 text-center text-rose-700 text-xs">Failed to load profiles. Please refresh page.</div>`;
    }
  }

  renderProfiles(profiles) {
    const grid = document.getElementById("profiles-grid");
    if (!grid) return;

    if (!profiles.length) {
      grid.innerHTML = `
        <div class="col-span-full py-16 text-center bg-white rounded-3xl p-8 border border-sandal-300">
          <div class="text-4xl mb-3">🪔</div>
          <h3 class="font-heading font-bold text-maroon-950 text-base">No Profiles Match Current Filters</h3>
          <p class="text-xs text-gray-500 mt-1 max-w-sm mx-auto">Try widening your age or district filters to discover more verified alliances.</p>
          <button onclick="window.smApp.resetFilters()" class="mt-4 px-4 py-2 bg-sandal-200 text-maroon-900 rounded-xl text-xs font-bold hover:bg-sandal-300 transition-colors">
            Clear All Filters
          </button>
        </div>
      `;
      return;
    }

    grid.innerHTML = profiles.map(p => `
      <div class="bg-white rounded-3xl border border-sandal-300 overflow-hidden shadow-sm hover:shadow-xl hover:border-gold-400 transition-all flex flex-col group relative">
        <!-- Top Photo / Banner -->
        <div class="relative h-60 w-full overflow-hidden bg-sandal-100">
          <img src="${p.photo_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80'}"
               alt="${p.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
          
          <!-- Badges -->
          <div class="absolute top-3 left-3 flex flex-wrap gap-1.5 max-w-[70%]">
            <span class="bg-maroon-950/90 backdrop-blur-xs text-gold-300 text-[10px] font-bold px-2.5 py-0.5 rounded-full border border-gold-400/40">
              ${p.id}
            </span>
            ${p.trust_badge_status === 'verified' ? `
              <span class="bg-gradient-to-r from-gold-500 to-amber-500 text-maroon-950 text-[10px] font-black px-2 py-0.5 rounded-full shadow border border-gold-200 flex items-center gap-1">
                🪔 Kanchi Silk Trust
              </span>
            ` : `
              <span class="bg-emerald-600/90 backdrop-blur-xs text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                ✓ Verified
              </span>
            `}
            ${p.marriage_timeline ? `
              <span class="bg-maroon-900/80 backdrop-blur-xs text-gold-200 text-[9px] font-semibold px-2 py-0.5 rounded-full">
                ⏳ ${p.marriage_timeline}
              </span>
            ` : ''}
          </div>

          <!-- Compatibility Score Pill -->
          <div class="absolute top-3 right-3 bg-white/90 backdrop-blur-xs text-maroon-950 text-[11px] font-extrabold px-2.5 py-0.5 rounded-full shadow border border-gold-400 flex items-center gap-1">
            <span>✨</span> ${p.compatibility || 90}% Match
          </div>

          <!-- Bottom Photo Overlay Name -->
          <div class="absolute bottom-3 left-3 right-3 text-white">
            <h3 class="font-heading font-bold text-lg leading-tight drop-shadow-sm flex items-center justify-between">
              <span>${p.name}</span>
              <span class="text-xs font-normal text-gold-300">${p.age} Yrs • ${p.height || '5 ft 4 in'}</span>
            </h3>
            <p class="text-[11px] text-gray-200">${p.caste} ${p.subcaste ? '• ' + p.subcaste : ''}</p>
          </div>
        </div>

        <!-- Details Body -->
        <div class="p-4 flex-1 flex flex-col justify-between space-y-3 bg-white">
          <div class="space-y-1.5 text-xs text-gray-700">
            <div class="flex items-center gap-2">
              <span class="text-gray-400">🎓</span>
              <span class="font-semibold text-gray-900 truncate">${p.education || 'Graduate'}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-gray-400">💼</span>
              <span class="font-medium text-gray-800 truncate">${p.occupation || 'Professional'}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-gray-400">📍</span>
              <span class="text-gray-600">${p.district}, Tamil Nadu</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-gray-400">🪐</span>
              <span class="text-gray-600 font-tamil">${p.rasi || 'Rishabam'} • ${p.nakshatra || 'Rohini'}</span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="pt-2 border-t border-sandal-200 flex items-center gap-1.5">
            <button onclick="window.smApp.openProfileModal('${p.id}')"
                    class="flex-1 bg-maroon-900 hover:bg-maroon-800 text-gold-300 font-bold py-2 px-2.5 rounded-xl text-xs transition-colors shadow-xs flex items-center justify-center gap-1 cursor-pointer">
              <span>👁️</span> <span>View</span>
            </button>
            <button onclick="window.smApp.toggleSecretLike('${p.id}', this)"
                    title="Secret Like (Private - only disclosed if mutual)"
                    class="w-8 h-8 rounded-xl border border-rose-200 hover:border-rose-400 flex items-center justify-center text-sm transition-all ${p.is_secret_liked ? 'bg-rose-100 text-rose-600 border-rose-300' : 'bg-rose-50/60 text-gray-400'}">
              ❤️
            </button>
            <button onclick="window.smApp.openIceBreakerModal('${p.id}', '${p.name.replace("'", "\\'")}', '${p.photo_url || ''}', '${p.district || ''}')"
                    title="Break the Ice (Curated Question)"
                    class="w-8 h-8 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 flex items-center justify-center text-xs font-bold transition-all">
              💬
            </button>
            <button onclick="window.smApp.toggleShortlist('${p.id}', this)"
                    title="Wishlist / Favourite"
                    class="w-8 h-8 rounded-xl border border-sandal-300 hover:border-gold-400 flex items-center justify-center text-sm transition-all ${p.is_shortlisted ? 'bg-gold-50 text-gold-600 border-gold-300' : 'bg-sandal-50 text-gray-400'}">
              ⭐
            </button>
          </div>
        </div>
      </div>
    `).join("");
  }

  renderPagination(total, current, maxPages) {
    const pag = document.getElementById("matches-pagination");
    if (!pag) return;

    if (maxPages <= 1) {
      pag.innerHTML = "";
      return;
    }

    pag.innerHTML = `
      <div class="flex items-center justify-center gap-2 pt-6">
        <button onclick="window.smApp.loadMatches(${current - 1})" ${current <= 1 ? 'disabled class="opacity-40 cursor-not-allowed"' : 'class="hover:bg-maroon-900 hover:text-white"'}
                class="px-3.5 py-1.5 rounded-xl border border-sandal-300 text-xs font-bold transition-all bg-white text-maroon-900">
          ← Previous
        </button>
        <span class="text-xs text-gray-600 font-medium px-2">Page ${current} of ${maxPages}</span>
        <button onclick="window.smApp.loadMatches(${current + 1})" ${current >= maxPages ? 'disabled class="opacity-40 cursor-not-allowed"' : 'class="hover:bg-maroon-900 hover:text-white"'}
                class="px-3.5 py-1.5 rounded-xl border border-sandal-300 text-xs font-bold transition-all bg-white text-maroon-900">
          Next →
        </button>
      </div>
    `;
  }

  setGenderFilter(val) {
    this.activeFilter = val;
    document.querySelectorAll(".tab-gender-btn").forEach(b => {
      b.classList.remove("active-gender-tab", "bg-maroon-900", "text-gold-300");
      b.classList.add("bg-white", "text-gray-700");
    });
    const activeBtn = document.getElementById(`tab-gender-${val}`);
    if (activeBtn) {
      activeBtn.classList.add("active-gender-tab", "bg-maroon-900", "text-gold-300");
      activeBtn.classList.remove("bg-white", "text-gray-700");
    }
    this.loadMatches(1);
  }

  resetFilters() {
    this.activeFilter = "all";
    if (document.getElementById("filter-age-min")) document.getElementById("filter-age-min").value = 18;
    if (document.getElementById("filter-age-max")) document.getElementById("filter-age-max").value = 60;
    if (document.getElementById("filter-district")) document.getElementById("filter-district").value = "all";
    if (document.getElementById("filter-caste")) document.getElementById("filter-caste").value = "all";
    if (document.getElementById("filter-timeline")) document.getElementById("filter-timeline").value = "all";
    if (document.getElementById("search-input")) document.getElementById("search-input").value = "";
    this.setGenderFilter("all");
  }

  // --------------------------------------------------------------------------
  // Profile Details Modal
  // --------------------------------------------------------------------------
  async openProfileModal(pid) {
    const modal = document.getElementById("profile-modal");
    const container = document.getElementById("profile-modal-content");
    if (!modal || !container) return;

    container.innerHTML = `<div class="p-12 text-center text-xs text-gray-500"><div class="inline-block w-8 h-8 border-4 border-gold-400 border-t-maroon-800 rounded-full animate-spin mb-2"></div><p>Fetching verified biodata...</p></div>`;
    modal.showModal();

    try {
      const res = await fetch(`/api/profile/${pid}`, {
        headers: this.token ? { "Authorization": `Bearer ${this.token}` } : {}
      });
      const data = await res.json();
      if (data.error) {
        container.innerHTML = `<div class="p-8 text-center text-rose-700 text-xs">${data.error}</div>`;
        return;
      }

      const p = data.profile;
      this.activeProfile = p;
      const canSee = data.can_see_contact;

      container.innerHTML = `
        <div class="relative">
          <!-- Top Banner -->
          <div class="bg-gradient-to-r from-maroon-950 via-maroon-900 to-maroon-950 p-6 text-white rounded-t-3xl flex flex-col md:flex-row items-center gap-6">
            <div class="w-28 h-28 sm:w-32 sm:h-32 rounded-full p-1 bg-gradient-to-tr from-gold-500 to-maroon-800 shadow-xl border-2 border-gold-400 overflow-hidden flex-shrink-0 bg-white">
              <img src="${p.photo_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80'}"
                   alt="${p.name}" class="w-full h-full object-cover rounded-full">
            </div>
            <div class="space-y-1 text-center md:text-left flex-1">
              <div class="flex flex-wrap items-center justify-center md:justify-start gap-2">
                <h2 class="font-heading text-2xl font-bold text-gold-300">${p.name}</h2>
                ${p.trust_badge_status === 'verified' ? `
                  <span class="bg-gradient-to-r from-gold-500 to-amber-500 text-maroon-950 text-[11px] font-black px-3 py-0.5 rounded-full shadow border border-gold-200 flex items-center gap-1">
                    🪔 Kanchi Silk Trust Verified
                  </span>
                ` : `
                  <span class="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">✓ Verified</span>
                `}
              </div>
              <p class="text-xs text-gray-200 font-mono tracking-wide text-gold-200 font-bold">${p.id}</p>
              <p class="text-xs text-gray-200">${p.age} Yrs • ${p.height || '5 ft 4 in'} • ${p.marital_status || 'Never Married'} • <span class="bg-maroon-800 px-2 py-0.5 rounded-full text-[10px] font-semibold text-gold-300">⏳ Timeline: ${p.marriage_timeline || 'Within 6 months'}</span></p>
              <p class="text-xs text-gold-400 font-semibold">${p.caste} ${p.subcaste ? '• ' + p.subcaste : ''}</p>
              <p class="text-[11px] text-gray-300">📍 ${p.district}, Tamil Nadu</p>
            </div>
            <button onclick="document.getElementById('profile-modal').close()" class="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-sm cursor-pointer">
              ✕
            </button>
          </div>

          <!-- Body Tabs / Details -->
          <div class="p-6 space-y-6 bg-sandal-50 max-h-[70vh] overflow-y-auto">
            <!-- Professional & Educational Biodata -->
            <div class="bg-white p-5 rounded-2xl border border-sandal-300 shadow-2xs space-y-3">
              <h4 class="font-heading font-bold text-sm text-maroon-900 flex items-center gap-2 border-b border-sandal-200 pb-2">
                <span>🎓</span> Professional & Educational Background
              </h4>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div><span class="text-gray-400 block text-[10px]">Education</span><strong class="text-gray-800">${p.education || 'Not specified'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Occupation</span><strong class="text-gray-800">${p.occupation || 'Not specified'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Annual Income</span><strong class="text-gray-800">${p.income || 'Undisclosed'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Mother Tongue</span><strong class="text-gray-800">${p.mother_tongue || 'Tamil'}</strong></div>
              </div>
            </div>

            <!-- Jathagam & Horoscope Compatibility -->
            <div class="bg-white p-5 rounded-2xl border border-sandal-300 shadow-2xs space-y-3">
              <h4 class="font-heading font-bold text-sm text-maroon-900 flex items-center gap-2 border-b border-sandal-200 pb-2">
                <span>🪐</span> Horoscope & Jathagam Details (10 Porutham)
              </h4>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div><span class="text-gray-400 block text-[10px]">Rasi</span><strong class="text-gray-800 font-tamil">${p.rasi || 'Rishabam'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Nakshatra</span><strong class="text-gray-800 font-tamil">${p.nakshatra || 'Rohini'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Lagnam</span><strong class="text-gray-800 font-tamil">${p.lagnam || 'Simmam'}</strong></div>
                <div><span class="text-gray-400 block text-[10px]">Dosham</span><strong class="text-gray-800">${p.dosham || 'None'}</strong></div>
              </div>
            </div>

            <!-- Partner Preferences -->
            <div class="bg-white p-5 rounded-2xl border border-sandal-300 shadow-2xs space-y-2">
              <h4 class="font-heading font-bold text-sm text-maroon-900 flex items-center gap-2 border-b border-sandal-200 pb-2">
                <span>💍</span> Expected Partner Preferences
              </h4>
              <p class="text-xs text-gray-700 leading-relaxed">${p.partner_pref || 'Looking for traditional Tamil Hindu partner with family values.'}</p>
            </div>

            <!-- Contact & Privacy Details -->
            <div class="bg-white p-5 rounded-2xl border-2 ${canSee ? 'border-emerald-400 bg-emerald-50/20' : 'border-gold-400 bg-gold-50/20'} shadow-2xs space-y-3">
              <div class="flex items-center justify-between">
                <h4 class="font-heading font-bold text-sm text-maroon-900 flex items-center gap-2">
                  <span>🔒</span> Confidential Contact Information
                </h4>
                ${canSee ? '<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full">Contact Revealed</span>' : '<span class="bg-gold-100 text-maroon-900 text-[10px] font-bold px-2 py-0.5 rounded-full">Privacy Protected</span>'}
              </div>
              <p class="text-xs text-gray-600">
                ${canSee ? 'You have mutually approved contact access with this family.' : 'Phone numbers and family home address are protected by privacy policy. Request contact below to exchange direct numbers.'}
              </p>
              <div class="p-3 bg-white rounded-xl border border-sandal-300 text-xs font-semibold text-gray-800">
                📞 Contact Phone: <span class="font-mono ${canSee ? 'text-emerald-700 font-bold' : 'text-gray-500'}">${p.phone}</span>
              </div>
            </div>

            <!-- Modal Action Buttons -->
            <div class="pt-2 flex flex-wrap items-center justify-between gap-2.5">
              <div class="flex flex-wrap items-center gap-2">
                <button onclick="window.smApp.toggleSecretLike('${p.id}', this)" class="px-4 py-2.5 rounded-xl border border-rose-300 ${p.is_secret_liked ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'} font-bold text-xs flex items-center gap-1.5 shadow-xs transition-all">
                  <span>❤️</span> <span>${p.is_secret_liked ? 'Secretly Liked' : 'Secret Like'}</span>
                </button>
                <button onclick="window.smApp.openIceBreakerModal('${p.id}', '${p.name.replace("'", "\\'")}', '${p.photo_url || ''}', '${p.district || ''}')" class="px-4 py-2.5 rounded-xl bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 font-bold text-xs flex items-center gap-1.5 shadow-xs transition-all">
                  <span>💬</span> <span>Break the Ice</span>
                </button>
                <button onclick="window.smApp.sendInterest('${p.id}')" class="px-4 py-2.5 rounded-xl bg-gold-400 hover:bg-gold-500 text-maroon-950 font-bold text-xs flex items-center gap-1.5 shadow transition-all">
                  <span>✨</span> Send Interest
                </button>
                <button onclick="window.smApp.requestContact('${p.id}')" class="px-4 py-2.5 rounded-xl bg-maroon-900 hover:bg-maroon-800 text-gold-300 font-bold text-xs flex items-center gap-1.5 shadow transition-all">
                  <span>📞</span> Request Contact
                </button>
                <button onclick="window.smApp.toggleShortlist('${p.id}', null)" class="px-3.5 py-2.5 rounded-xl border border-sandal-300 bg-white hover:bg-sandal-100 text-gray-700 font-bold text-xs flex items-center gap-1 shadow-xs transition-all">
                  <span>⭐</span> Shortlist
                </button>
              </div>
              <button onclick="window.smApp.openReportProfileModal('${p.id}')" class="text-[11px] text-gray-400 hover:text-rose-600 transition-colors">
                🚩 Report
              </button>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="p-8 text-center text-rose-700 text-xs">Error opening profile.</div>`;
    }
  }

  // --------------------------------------------------------------------------
  // User Actions: Interests, Shortlists, Contact Requests
  // --------------------------------------------------------------------------
  async sendInterest(receiverId) {
    if (!this.currentUser) {
      this.showToast("Please login or register to send interest.", "info");
      this.openLoginModal();
      return;
    }
    try {
      const res = await fetch("/api/interests/send", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ receiver_id: receiverId })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Interest sent to candidate and family! ✨", "success");
      } else {
        this.showToast(data.error || "Unable to send interest", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  async toggleShortlist(pid, btnEl) {
    if (!this.currentUser) {
      this.showToast("Please login to save favourites.", "info");
      this.openLoginModal();
      return;
    }
    try {
      const res = await fetch("/api/shortlist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ profile_id: pid })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(data.message, "success");
        if (btnEl) {
          btnEl.innerHTML = data.shortlisted ? "❤️" : "🤍";
          btnEl.className = `w-8 h-8 rounded-xl border border-sandal-300 flex items-center justify-center text-sm transition-all ${data.shortlisted ? 'bg-rose-50 text-rose-600 border-rose-300' : 'bg-sandal-50 text-gray-400'}`;
        }
      }
    } catch (e) {
      this.showToast("Error updating shortlist", "error");
    }
  }

  async requestContact(targetId) {
    if (!this.currentUser) {
      this.showToast("Please login to request contact details.", "info");
      this.openLoginModal();
      return;
    }
    try {
      const res = await fetch("/api/contact-requests/request", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ target_id: targetId })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Contact request submitted to candidate's family! 📞", "success");
      } else {
        this.showToast(data.error || "Request failed", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  // --------------------------------------------------------------------------
  // Member Dashboard Modal
  // --------------------------------------------------------------------------
  openDashboardModal() {
    if (!this.currentUser) {
      this.openLoginModal();
      return;
    }
    const modal = document.getElementById("dashboard-modal");
    if (!modal) return;
    this.renderDashboardOverview();
    modal.showModal();
  }

  closeDashboardModal() {
    const modal = document.getElementById("dashboard-modal");
    if (modal) modal.close();
  }

  switchDashboardTab(tabName) {
    document.querySelectorAll(".dash-tab-btn").forEach(b => {
      b.classList.remove("text-maroon-900", "border-b-2", "border-maroon-900", "font-bold");
      b.classList.add("text-gray-500", "font-medium");
    });
    document.getElementById(`dash-tab-btn-${tabName}`)?.classList.add("text-maroon-900", "border-b-2", "border-maroon-900", "font-bold");
    document.getElementById(`dash-tab-btn-${tabName}`)?.classList.remove("text-gray-500", "font-medium");

    document.querySelectorAll(".dash-tab-panel").forEach(p => p.classList.add("hidden"));
    document.getElementById(`dash-panel-${tabName}`)?.classList.remove("hidden");

    if (tabName === "interests") this.loadUserInterests();
    if (tabName === "shortlist") this.loadUserShortlist();
    if (tabName === "secret-likes") this.loadSecretLikesAndMutual();
    if (tabName === "icebreakers") this.loadIceBreakers();
    if (tabName === "trust-badge") this.loadTrustBadgeInfo();
    if (tabName === "privacy-settings") this.loadPrivacySettings();
    if (tabName === "contacts") this.loadUserContactRequests();
    if (tabName === "notifications") this.loadUserNotifications();
  }

  renderDashboardOverview() {
    const u = this.currentUser;
    const p = u.profile || {};
    const planName = u.membership_plan || "Free Plan";
    const expiry = u.membership_expiry || "30 Days from activation";
    const status = u.membership_status || (u.status === "active" ? "active" : "pending_verification");

    if (document.getElementById("dash-user-name")) document.getElementById("dash-user-name").textContent = u.name;
    if (document.getElementById("dash-user-plan")) document.getElementById("dash-user-plan").textContent = planName;
    if (document.getElementById("dash-user-expiry")) document.getElementById("dash-user-expiry").textContent = `Expires: ${expiry}`;
    if (document.getElementById("dash-user-status-pill")) {
      const isPending = status === "pending_verification";
      document.getElementById("dash-user-status-pill").textContent = isPending ? "Pending Verification" : "Active";
      document.getElementById("dash-user-status-pill").className = isPending
        ? "ml-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/80 text-white border border-amber-300"
        : "ml-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-600/80 text-white border border-emerald-400";
    }

    if (document.getElementById("dash-card-plan-name")) document.getElementById("dash-card-plan-name").textContent = planName;
    if (document.getElementById("dash-card-expiry")) document.getElementById("dash-card-expiry").textContent = expiry;
    if (document.getElementById("dash-card-status-badge")) {
      const isPending = status === "pending_verification";
      document.getElementById("dash-card-status-badge").textContent = isPending ? "Pending Verification" : "Active";
      document.getElementById("dash-card-status-badge").className = isPending
        ? "px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300"
        : "px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300";
    }
    if (document.getElementById("dash-card-duration")) {
      document.getElementById("dash-card-duration").textContent = planName.includes("Diamond") ? "365 Days (1 Year)" : planName.includes("Gold") ? "180 Days (6 Months)" : "30 Days";
    }
    if (document.getElementById("dash-card-contacts")) {
      document.getElementById("dash-card-contacts").textContent = planName.includes("Diamond") ? "80 Profiles" : planName.includes("Gold") ? "35 Profiles" : "2 Profiles";
    }

    if (document.getElementById("dash-completion-bar")) document.getElementById("dash-completion-bar").style.width = `${p.completion_percentage || 85}%`;
    if (document.getElementById("dash-completion-pct")) document.getElementById("dash-completion-pct").textContent = `${p.completion_percentage || 85}% Completed`;
  }

  async loadUserInterests() {
    const container = document.getElementById("dash-interests-list");
    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-xs text-gray-500">Loading interests...</div>`;

    try {
      const res = await fetch("/api/interests", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const sent = data.sent || [];
      const received = data.received || [];

      let html = `<div class="space-y-4">`;
      html += `<h4 class="font-bold text-xs text-maroon-950 uppercase tracking-wider">Interests Received (${received.length})</h4>`;
      if (!received.length) {
        html += `<p class="text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200">No new incoming interests yet.</p>`;
      } else {
        html += received.map(i => `
          <div class="bg-white p-4 rounded-2xl border border-sandal-300 shadow-2xs flex items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-3">
              <img src="${i.photo_url || 'assets/circle-logo.png'}" class="w-12 h-12 rounded-full object-cover">
              <div>
                <h5 class="font-bold text-gray-900">${i.name} (${i.age} Yrs)</h5>
                <p class="text-gray-500">${i.caste} • ${i.district}</p>
                <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${i.status === 'accepted' ? 'bg-emerald-100 text-emerald-800' : 'bg-gold-100 text-maroon-900'}">${i.status}</span>
              </div>
            </div>
            ${i.status === 'pending' ? `
              <div class="flex items-center gap-2">
                <button onclick="window.smApp.respondInterest(${i.id}, 'accept')" class="px-3 py-1.5 bg-emerald-600 text-white font-bold rounded-xl text-xs hover:bg-emerald-700">Accept</button>
                <button onclick="window.smApp.respondInterest(${i.id}, 'decline')" class="px-3 py-1.5 bg-gray-200 text-gray-700 font-bold rounded-xl text-xs hover:bg-gray-300">Decline</button>
              </div>
            ` : ''}
          </div>
        `).join("");
      }

      html += `<h4 class="font-bold text-xs text-maroon-950 uppercase tracking-wider pt-3">Interests Sent (${sent.length})</h4>`;
      if (!sent.length) {
        html += `<p class="text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200">You haven't sent any interests yet.</p>`;
      } else {
        html += sent.map(i => `
          <div class="bg-white p-4 rounded-2xl border border-sandal-300 shadow-2xs flex items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-3">
              <img src="${i.photo_url || 'assets/circle-logo.png'}" class="w-12 h-12 rounded-full object-cover">
              <div>
                <h5 class="font-bold text-gray-900">${i.name} (${i.age} Yrs)</h5>
                <p class="text-gray-500">${i.district} • Status: <span class="font-bold capitalize">${i.status}</span></p>
              </div>
            </div>
            ${i.status === 'pending' ? `
              <button onclick="window.smApp.withdrawInterest(${i.id})" class="text-xs text-rose-600 hover:underline">Withdraw</button>
            ` : ''}
          </div>
        `).join("");
      }
      html += `</div>`;
      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = `<div class="p-6 text-center text-rose-600 text-xs">Error loading interests.</div>`;
    }
  }

  async respondInterest(id, action) {
    try {
      const res = await fetch("/api/interests/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ interest_id: id, action })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Interest ${action}ed!`, "success");
        this.loadUserInterests();
      }
    } catch (e) {}
  }

  async withdrawInterest(id) {
    try {
      const res = await fetch("/api/interests/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ interest_id: id })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Interest withdrawn.", "info");
        this.loadUserInterests();
      }
    } catch (e) {}
  }

  async loadUserShortlist() {
    const container = document.getElementById("dash-shortlist-list");
    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-xs text-gray-500">Loading shortlisted profiles...</div>`;
    try {
      const res = await fetch("/api/shortlist", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const list = data.shortlist || [];
      if (!list.length) {
        container.innerHTML = `<p class="text-xs text-gray-400 bg-white p-6 rounded-2xl border border-sandal-200 text-center">No profiles saved in your favourites yet.</p>`;
        return;
      }
      container.innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          ${list.map(p => `
            <div class="bg-white p-3.5 rounded-2xl border border-sandal-300 flex items-center justify-between gap-3 text-xs">
              <div class="flex items-center gap-2.5">
                <img src="${p.photo_url || 'assets/circle-logo.png'}" class="w-12 h-12 rounded-full object-cover">
                <div>
                  <h5 class="font-bold text-gray-900">${p.name} (${p.age})</h5>
                  <p class="text-gray-500 text-[11px]">${p.caste} • ${p.district}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button onclick="window.smApp.openProfileModal('${p.id}')" class="px-2.5 py-1 bg-maroon-900 text-gold-300 rounded-lg font-bold text-xs">View</button>
                <button onclick="window.smApp.toggleShortlist('${p.id}', null); window.smApp.loadUserShortlist();" class="text-gray-400 hover:text-rose-600">✕</button>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    } catch (e) {}
  }

  async loadUserContactRequests() {
    const container = document.getElementById("dash-contacts-list");
    if (!container) return;
    container.innerHTML = `<div class="p-8 text-center text-xs text-gray-500">Loading contact requests...</div>`;
    try {
      const res = await fetch("/api/contact-requests", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const incoming = data.incoming || [];
      const outgoing = data.outgoing || [];

      let html = `<div class="space-y-4">`;
      html += `<h4 class="font-bold text-xs text-maroon-950 uppercase tracking-wider">Incoming Contact Requests (${incoming.length})</h4>`;
      if (!incoming.length) {
        html += `<p class="text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200">No incoming contact requests.</p>`;
      } else {
        html += incoming.map(r => `
          <div class="bg-white p-4 rounded-2xl border border-sandal-300 shadow-2xs flex items-center justify-between gap-3 text-xs">
            <div>
              <h5 class="font-bold text-gray-900">${r.name} (${r.age} Yrs)</h5>
              <p class="text-gray-500">Requested to view family phone number</p>
              <span class="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${r.status === 'approved' ? 'bg-emerald-100 text-emerald-800' : 'bg-gold-100 text-maroon-900'}">${r.status}</span>
            </div>
            ${r.status === 'pending' ? `
              <div class="flex items-center gap-2">
                <button onclick="window.smApp.respondContactRequest(${r.id}, 'approve')" class="px-3 py-1.5 bg-emerald-600 text-white font-bold rounded-xl text-xs hover:bg-emerald-700">Share Contact</button>
                <button onclick="window.smApp.respondContactRequest(${r.id}, 'reject')" class="px-3 py-1.5 bg-gray-200 text-gray-700 font-bold rounded-xl text-xs hover:bg-gray-300">Decline</button>
              </div>
            ` : ''}
          </div>
        `).join("");
      }

      html += `<h4 class="font-bold text-xs text-maroon-950 uppercase tracking-wider pt-3">Outgoing Contact Requests (${outgoing.length})</h4>`;
      if (!outgoing.length) {
        html += `<p class="text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200">No outgoing contact requests.</p>`;
      } else {
        html += outgoing.map(r => `
          <div class="bg-white p-4 rounded-2xl border border-sandal-300 shadow-2xs flex items-center justify-between gap-3 text-xs">
            <div>
              <h5 class="font-bold text-gray-900">${r.name} (${r.age} Yrs)</h5>
              <p class="text-gray-500">Status: <span class="font-bold capitalize">${r.status}</span></p>
              ${r.status === 'approved' ? `<p class="text-emerald-700 font-bold mt-1">📞 Contact: ${r.contact_phone}</p>` : ''}
            </div>
            <button onclick="window.smApp.openProfileModal('${r.profile_id}')" class="px-3 py-1.5 bg-maroon-900 text-gold-300 rounded-xl font-bold text-xs">View</button>
          </div>
        `).join("");
      }
      html += `</div>`;
      container.innerHTML = html;
    } catch (e) {}
  }

  async respondContactRequest(id, action) {
    try {
      const res = await fetch("/api/contact-requests/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ request_id: id, action })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`Contact request ${action}d!`, "success");
        this.loadUserContactRequests();
      }
    } catch (e) {}
  }

  async loadUserNotifications() {
    const container = document.getElementById("dash-notifications-list");
    const badge = document.getElementById("header-notif-badge");
    try {
      const res = await fetch("/api/notifications", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const notifs = data.notifications || [];
      const unreadCount = notifs.filter(n => !n.is_read).length;

      if (badge) {
        if (unreadCount > 0) {
          badge.textContent = unreadCount;
          badge.classList.remove("hidden");
        } else {
          badge.classList.add("hidden");
        }
      }

      if (container) {
        if (!notifs.length) {
          container.innerHTML = `<p class="text-xs text-gray-400 bg-white p-6 rounded-2xl border border-sandal-200 text-center">No notifications.</p>`;
          return;
        }
        container.innerHTML = notifs.map(n => `
          <div class="bg-white p-3.5 rounded-2xl border ${n.is_read ? 'border-sandal-200' : 'border-gold-400 bg-gold-50/20'} flex items-start justify-between gap-3 text-xs">
            <div class="space-y-0.5">
              <h5 class="font-bold text-gray-900 flex items-center gap-1.5">
                ${!n.is_read ? '<span class="w-2 h-2 rounded-full bg-maroon-800"></span>' : ''}
                ${n.title}
              </h5>
              <p class="text-gray-600">${n.message}</p>
              <span class="text-[10px] text-gray-400">${n.created_at}</span>
            </div>
            ${!n.is_read ? `
              <button onclick="window.smApp.markNotificationRead(${n.id})" class="text-[10px] text-maroon-800 font-bold hover:underline">Mark Read</button>
            ` : ''}
          </div>
        `).join("");
      }
    } catch (e) {}
  }

  async markNotificationRead(id) {
    try {
      await fetch("/api/notifications/read", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ notification_id: id })
      });
      this.loadUserNotifications();
    } catch (e) {}
  }

  // --------------------------------------------------------------------------
  // Public Testimonials & Membership Plans
  // --------------------------------------------------------------------------
  async loadTestimonials() {
    const storiesGrid = document.getElementById("success-stories-grid");
    const reviewsGrid = document.getElementById("testimonials-reviews-grid");
    try {
      const res = await fetch("/api/public/testimonials");
      const data = await res.json();
      const list = data.testimonials || [];

      if (storiesGrid && list.length) {
        storiesGrid.innerHTML = list.map(t => `
          <div class="bg-white rounded-3xl p-6 border border-sandal-300 shadow-sm hover:border-gold-400 hover:shadow-md transition-all flex flex-col justify-between space-y-4">
            <div class="flex items-center gap-4">
              <img src="${t.photo_url}" alt="${t.couple_name}" class="w-16 h-16 rounded-full object-cover border-2 border-gold-400 shadow">
              <div>
                <h4 class="font-heading font-bold text-base text-maroon-950">${t.couple_name}</h4>
                <p class="text-xs text-gold-600 font-semibold">📍 ${t.district} • Married: ${t.marriage_date}</p>
                <div class="text-xs text-amber-500 mt-0.5">⭐⭐⭐⭐⭐</div>
              </div>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed italic bg-sandal-50 p-4 rounded-2xl border border-sandal-200">
              "${t.story}"
            </p>
            <div class="text-[11px] text-gray-400 font-medium flex items-center justify-between border-t border-sandal-200 pt-2">
              <span>✓ Verified Matrimonial Alliance</span>
              <span class="text-emerald-700 font-bold">10 Porutham Matched</span>
            </div>
          </div>
        `).join("");
      }
    } catch (e) {}
  }

  async loadPlans() {
    const grid = document.getElementById("membership-plans-grid");
    if (!grid) return;
    try {
      const res = await fetch("/api/public/plans");
      const data = await res.json();
      const plans = data.plans || [];
      if (!plans.length) return;

      grid.innerHTML = plans.map(p => `
        <div class="bg-white rounded-3xl p-6 sm:p-8 border-2 ${p.is_popular ? 'border-gold-500 shadow-xl relative' : 'border-sandal-300 shadow-sm'} flex flex-col justify-between space-y-6">
          ${p.is_popular ? '<div class="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-gold-500 to-amber-500 text-maroon-950 text-[10px] font-extrabold uppercase px-4 py-1 rounded-full shadow">Most Auspicious Choice</div>' : ''}
          
          <div class="space-y-3 text-center">
            <span class="inline-block px-3 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${p.price === 0 ? 'bg-sandal-200 text-maroon-950' : p.is_popular ? 'bg-gold-100 text-maroon-900 border border-gold-300' : 'bg-maroon-950 text-gold-300'}">
              ${p.price === 0 ? 'Basic Starter' : p.is_popular ? 'Recommended Alliances' : 'VIP Matchmaking'}
            </span>
            <h3 class="font-heading font-bold text-xl sm:text-2xl text-maroon-950">${p.name}</h3>
            <div class="flex items-baseline justify-center gap-1.5 pt-1">
              <span class="font-heading text-3xl sm:text-4xl font-extrabold text-maroon-900">${p.price === 0 ? '₹0' : '₹' + p.price.toLocaleString()}</span>
              <span class="text-xs text-gray-500 font-semibold">/ ${p.validity_days} Days</span>
            </div>
            <p class="text-xs text-emerald-700 font-bold bg-emerald-50 py-1 px-3 rounded-lg border border-emerald-200">
              Contact Access: ${p.contact_limit} Profiles
            </p>
          </div>

          <div class="border-t border-b border-sandal-200 py-4 space-y-2">
            <span class="text-[10px] uppercase font-bold text-gray-500 tracking-wider block mb-2">Key Benefits:</span>
            <ul class="space-y-2.5 text-xs text-gray-700">
              ${(p.features || []).map(f => `
                <li class="flex items-start gap-2">
                  <span class="text-emerald-600 font-bold text-sm leading-none flex-shrink-0">✓</span>
                  <span class="leading-snug">${f}</span>
                </li>
              `).join("")}
            </ul>
          </div>

          <!-- Action Buttons: Choose Plan and View Benefits -->
          <div class="space-y-2.5 pt-2">
            <button onclick="window.smApp.choosePlan('${p.id}')"
                    class="w-full py-3 rounded-xl font-bold text-xs sm:text-sm shadow transition-all cursor-pointer flex items-center justify-center gap-1.5 ${p.is_popular ? 'bg-gradient-to-r from-maroon-900 via-maroon-800 to-maroon-950 text-gold-300 hover:scale-[1.02] hover:shadow-lg' : 'bg-maroon-900 hover:bg-maroon-800 text-gold-300'}">
              <span>💎</span>
              <span>Choose Plan</span>
            </button>

            <a href="/membership-details?plan=${p.id}"
               class="w-full py-2.5 rounded-xl font-bold text-xs text-center border border-sandal-300 bg-sandal-50 hover:bg-sandal-200 text-maroon-950 transition-colors block cursor-pointer">
              View Benefits & Details →
            </a>
          </div>
        </div>
      `).join("");
    } catch (e) {
      console.error("Error loading membership plans:", e);
    }
  }

  async choosePlan(planId) {
    if (!this.currentUser) {
      this.showToast("Please sign in or register to choose a membership plan.", "info");
      setTimeout(() => {
        window.location.href = `/login?redirect=${encodeURIComponent('/membership-details?plan=' + planId)}`;
      }, 1000);
      return;
    }

    if (planId === "free") {
      try {
        const res = await fetch("/api/membership/select", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${this.token}`
          },
          body: JSON.stringify({ plan_id: "free" })
        });
        const data = await res.json();
        if (data.success) {
          this.showToast(data.message || "Free Plan activated immediately!", "success");
          this.currentUser.membership_plan = data.plan_name || "Free Plan";
          this.currentUser.membership_expiry = data.expiry_date;
          this.currentUser.membership_status = "active";
          this.renderDashboardOverview();
          this.openDashboardModal();
        } else {
          this.showToast(data.error || "Failed to activate Free Plan", "error");
        }
      } catch (e) {
        this.showToast("Network error activating Free Plan", "error");
      }
    } else {
      window.location.href = `/membership-details?plan=${planId}`;
    }
  }

  // --------------------------------------------------------------------------
  // Modals & Navigation Helpers
  // --------------------------------------------------------------------------
  openLoginModal() {
    document.getElementById("login-modal")?.showModal();
  }

  closeLoginModal() {
    document.getElementById("login-modal")?.close();
  }

  openReportProfileModal(pid) {
    const reason = prompt("Please enter the reason for reporting this profile (e.g. Inaccurate details, photo mismatch):");
    if (reason) {
      fetch("/api/public/report-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": this.token ? `Bearer ${this.token}` : "" },
        body: JSON.stringify({ profile_id: pid, reason })
      }).then(() => this.showToast("Report submitted to trust & safety team.", "info"));
    }
  }

  // Toast Notification
  showToast(message, type = "info") {
    const toast = document.getElementById("toast-notification");
    const toastMsg = document.getElementById("toast-message");
    if (!toast || !toastMsg) return;

    toastMsg.textContent = message;
    toast.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-2.5 text-xs font-bold transition-all duration-300 ${
      type === 'success' ? 'bg-emerald-950 text-emerald-200 border border-emerald-400' :
      type === 'error' ? 'bg-rose-950 text-rose-200 border border-rose-400' :
      'bg-maroon-950 text-gold-300 border border-gold-400'
    }`;
    toast.classList.remove("translate-y-24", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    clearTimeout(this.toastTimeout);
    this.toastTimeout = setTimeout(() => {
      toast.classList.remove("translate-y-0", "opacity-100");
      toast.classList.add("translate-y-24", "opacity-0");
    }, 4000);
  }

  // Scroll Effects
  initScrollEffects() {
    const header = document.querySelector("header");
    window.addEventListener("scroll", () => {
      if (window.scrollY > 80) {
        header?.classList.add("header-scrolled");
        header?.classList.remove("header-transparent");
      } else {
        header?.classList.remove("header-scrolled");
        header?.classList.add("header-transparent");
      }
    });
  }

  setupRouteHandling() {
    const path = window.location.pathname;
    const hash = window.location.hash;
    if (path === "/matches") {
      document.getElementById("matches-section")?.scrollIntoView({ behavior: "smooth" });
    } else if (path === "/dashboard" || hash === "#dashboard") {
      if (this.currentUser) {
        this.openDashboardModal();
      }
    }
  }

  bindEvents() {
    // Contact Enquiry form
    const contactForm = document.getElementById("family-contact-form");
    if (contactForm) {
      contactForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("cf-name")?.value.trim();
        const phone = document.getElementById("cf-phone")?.value.trim();
        const email = document.getElementById("cf-email")?.value.trim();
        const subject = document.getElementById("cf-subject")?.value.trim() || "General Enquiry";
        const message = document.getElementById("cf-msg")?.value.trim();

        try {
          const res = await fetch("/api/public/enquiry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, phone, email, subject, message })
          });
          const data = await res.json();
          if (data.success) {
            this.showToast(data.message, "success");
            contactForm.reset();
          } else {
            this.showToast(data.error || "Submission failed", "error");
          }
        } catch (err) {
          this.showToast("Network error submitting enquiry", "error");
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // Phase 1 Features: Secret Likes & Mutual Matches
  // --------------------------------------------------------------------------
  async toggleSecretLike(targetProfileId, btnEl) {
    if (!this.currentUser) {
      this.showToast("Please sign in to secretly like this profile.", "info");
      this.openLoginModal();
      return;
    }
    try {
      const res = await fetch("/api/secret-likes/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ target_profile_id: targetProfileId })
      });
      const data = await res.json();
      if (data.success) {
        if (data.is_mutual) {
          this.showToast("🎉 Auspicious Match! You both liked each other secretly!", "success");
        } else {
          this.showToast(data.message, "success");
        }
        if (btnEl) {
          if (btnEl.textContent.includes("Secret")) {
            btnEl.className = `px-4 py-2.5 rounded-xl border border-rose-300 ${data.liked ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'} font-bold text-xs flex items-center gap-1.5 shadow-xs transition-all`;
            btnEl.innerHTML = `<span>❤️</span> <span>${data.liked ? 'Secretly Liked' : 'Secret Like'}</span>`;
          } else {
            btnEl.className = `w-8 h-8 rounded-xl border border-rose-200 hover:border-rose-400 flex items-center justify-center text-sm transition-all ${data.liked ? 'bg-rose-100 text-rose-600 border-rose-300' : 'bg-rose-50/60 text-gray-400'}`;
          }
        }
      } else {
        this.showToast(data.error || "Unable to update secret like", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  async loadSecretLikesAndMutual() {
    if (!this.token) return;
    try {
      const res = await fetch("/api/secret-likes/mutual", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const mutual = data.mutual_matches || [];
      const sent = data.sent_secret_likes || [];

      const mutualCountEl = document.getElementById("dash-mutual-count");
      if (mutualCountEl) mutualCountEl.textContent = mutual.length;
      const sentCountEl = document.getElementById("dash-secret-likes-count");
      if (sentCountEl) sentCountEl.textContent = sent.length;

      const mutualList = document.getElementById("dash-mutual-matches-list");
      if (mutualList) {
        if (!mutual.length) {
          mutualList.innerHTML = `
            <div class="bg-white p-6 rounded-2xl border border-sandal-200 text-center text-xs text-gray-500">
              <span class="text-3xl block mb-2">💫</span>
              <p class="font-bold text-gray-700">No mutual matches yet</p>
              <p class="text-[11px] text-gray-400 mt-0.5">Secretly like more profiles in the search catalog. When someone likes you back, their profile will appear here!</p>
            </div>
          `;
        } else {
          mutualList.innerHTML = mutual.map(m => `
            <div class="bg-gradient-to-r from-rose-50 via-white to-gold-50 p-4 rounded-2xl border-2 border-rose-300 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
              <div class="flex items-center gap-3 w-full sm:w-auto">
                <img src="${m.photo_url || 'assets/circle-logo.png'}" class="w-14 h-14 rounded-full object-cover border-2 border-rose-400 shadow">
                <div>
                  <div class="flex items-center gap-2">
                    <h5 class="font-heading font-bold text-maroon-950 text-sm">${m.name} (${m.age} Yrs)</h5>
                    <span class="bg-rose-600 text-white font-bold text-[9px] px-2 py-0.5 rounded-full">Mutual ❤️</span>
                  </div>
                  <p class="text-gray-600 text-[11px] font-mono">${m.profile_id} • ${m.caste || ''} • 📍 ${m.district}</p>
                  <p class="text-[10px] text-rose-800 font-semibold mt-0.5">✨ Matched on: ${m.matched_at}</p>
                </div>
              </div>
              <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
                <button onclick="window.smApp.openProfileModal('${m.profile_id}')" class="px-3.5 py-2 bg-maroon-900 text-gold-300 font-bold rounded-xl text-xs hover:bg-maroon-800 shadow">View Full Biodata</button>
                <button onclick="window.smApp.openIceBreakerModal('${m.profile_id}', '${m.name.replace("'", "\\'")}', '${m.photo_url || ''}', '${m.district || ''}')" class="px-3 py-2 bg-amber-100 text-amber-900 font-bold rounded-xl text-xs border border-amber-300 hover:bg-amber-200">Break Ice 💬</button>
              </div>
            </div>
          `).join("");
        }
      }

      const sentList = document.getElementById("dash-sent-secret-likes-list");
      if (sentList) {
        if (!sent.length) {
          sentList.innerHTML = `<p class="col-span-full text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200 text-center">You haven't secretly liked any profiles yet.</p>`;
        } else {
          sentList.innerHTML = sent.map(s => `
            <div class="bg-white p-3.5 rounded-2xl border border-sandal-300 flex items-center justify-between gap-3 text-xs">
              <div class="flex items-center gap-2.5">
                <img src="${s.photo_url || 'assets/circle-logo.png'}" class="w-11 h-11 rounded-full object-cover">
                <div>
                  <h6 class="font-bold text-gray-900">${s.name} (${s.age})</h6>
                  <p class="text-[10px] text-gray-500 font-mono">${s.profile_id} • ${s.district}</p>
                  <span class="text-[10px] ${s.is_mutual ? 'text-emerald-700 font-bold' : 'text-amber-600'}">
                    ${s.is_mutual ? '✓ Mutual Match' : '⏳ Awaiting Reciprocal Like'}
                  </span>
                </div>
              </div>
              <button onclick="window.smApp.toggleSecretLike('${s.profile_id}', null); window.smApp.loadSecretLikesAndMutual();" class="text-xs text-gray-400 hover:text-rose-600" title="Unlike">
                ✕
              </button>
            </div>
          `).join("");
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  // --------------------------------------------------------------------------
  // Phase 1 Features: Ice Breakers Modal & Management
  // --------------------------------------------------------------------------
  openIceBreakerModal(targetProfileId, targetName, photoUrl, district) {
    if (!this.currentUser) {
      this.showToast("Please sign in to send an ice breaker.", "info");
      this.openLoginModal();
      return;
    }
    const modal = document.getElementById("icebreaker-modal");
    if (!modal) return;

    document.getElementById("ib-target-id").value = targetProfileId;
    document.getElementById("ib-target-name").textContent = targetName;
    document.getElementById("ib-target-meta").textContent = `${district ? district + ', ' : ''}Tamil Nadu • ${targetProfileId}`;
    if (photoUrl) document.getElementById("ib-target-photo").src = photoUrl;

    const customRadio = document.querySelector('input[name="ib_preset"][value="custom"]');
    const customContainer = document.getElementById("ib-custom-container");
    document.querySelectorAll('input[name="ib_preset"]').forEach(r => {
      r.onchange = () => {
        if (customContainer) {
          if (r.value === "custom" && r.checked) {
            customContainer.classList.remove("hidden");
          } else {
            customContainer.classList.add("hidden");
          }
        }
      };
    });

    modal.showModal();
  }

  async submitIceBreakerModal() {
    const targetId = document.getElementById("ib-target-id").value;
    const selectedPreset = document.querySelector('input[name="ib_preset"]:checked')?.value;
    let question = selectedPreset;

    if (selectedPreset === "custom") {
      question = document.getElementById("ib-custom-text")?.value.trim();
      if (!question) {
        this.showToast("Please write a question or choose a curated one.", "error");
        return;
      }
    }

    try {
      const res = await fetch("/api/icebreakers/send", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ receiver_id: targetId, question })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Ice breaker question sent to candidate! 💬", "success");
        document.getElementById("icebreaker-modal").close();
      } else {
        this.showToast(data.error || "Unable to send ice breaker", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  async loadIceBreakers() {
    if (!this.token) return;
    try {
      const res = await fetch("/api/icebreakers", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      const received = data.received || [];
      const sent = data.sent || [];
      const plan = data.plan || "Free";

      const limitText = document.getElementById("dash-icebreaker-limit-text");
      if (limitText) {
        limitText.textContent = `${plan}: ${data.remaining_questions} questions remaining (${data.sent_count}/${data.limit} used)`;
      }

      const recCount = document.getElementById("dash-received-icebreakers-count");
      if (recCount) recCount.textContent = received.length;
      const sentCount = document.getElementById("dash-sent-icebreakers-count");
      if (sentCount) sentCount.textContent = sent.length;

      const recList = document.getElementById("dash-received-icebreakers-list");
      if (recList) {
        if (!received.length) {
          recList.innerHTML = `<p class="text-xs text-gray-400 bg-white p-5 rounded-2xl border border-sandal-200 text-center">No ice breaker questions received yet.</p>`;
        } else {
          recList.innerHTML = received.map(ib => `
            <div class="bg-white p-5 rounded-2xl border border-sandal-300 shadow-2xs space-y-3 text-xs">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <img src="${ib.sender_photo || 'assets/circle-logo.png'}" class="w-10 h-10 rounded-full object-cover border border-gold-300">
                  <div>
                    <h5 class="font-bold text-gray-900">${ib.sender_name}</h5>
                    <p class="text-[11px] text-gray-500 font-mono">${ib.sender_id} • ${ib.sender_district}</p>
                  </div>
                </div>
                <span class="text-[10px] px-2.5 py-0.5 rounded-full font-bold ${ib.status === 'answered' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                  ${ib.status === 'answered' ? 'Answered ✓' : 'Awaiting Reply'}
                </span>
              </div>
              <div class="bg-sandal-50 p-3.5 rounded-xl border border-sandal-200">
                <p class="font-semibold text-maroon-950">Q: ${ib.question}</p>
              </div>
              ${ib.status === 'answered' ? `
                <div class="bg-emerald-50/50 p-3 rounded-xl border border-emerald-200 text-emerald-950">
                  <strong>Your Reply:</strong> ${ib.answer}
                  <span class="block text-[10px] text-gray-400 mt-1">Answered on ${ib.answered_at}</span>
                </div>
              ` : `
                <div class="space-y-2 pt-1">
                  <textarea id="reply-text-${ib.id}" rows="2" placeholder="Write your polite and honest answer..." class="w-full bg-white border border-sandal-300 rounded-xl p-2.5 text-xs focus:ring-maroon-800"></textarea>
                  <button onclick="window.smApp.replyIceBreaker(${ib.id})" class="px-4 py-1.5 bg-maroon-900 hover:bg-maroon-800 text-gold-300 font-bold rounded-xl text-xs shadow">
                    Submit Auspicious Reply ✍️
                  </button>
                </div>
              `}
            </div>
          `).join("");
        }
      }

      const sentList = document.getElementById("dash-sent-icebreakers-list");
      if (sentList) {
        if (!sent.length) {
          sentList.innerHTML = `<p class="text-xs text-gray-400 bg-white p-4 rounded-xl border border-sandal-200 text-center">You haven't asked any ice breaker questions yet.</p>`;
        } else {
          sentList.innerHTML = sent.map(ib => `
            <div class="bg-white p-4 rounded-2xl border border-sandal-300 text-xs space-y-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-gray-900">Sent to ${ib.receiver_name} (${ib.receiver_id})</span>
                <span class="text-[10px] text-gray-400">${ib.created_at}</span>
              </div>
              <p class="text-gray-700 bg-sandal-50 p-2.5 rounded-xl">Q: ${ib.question}</p>
              ${ib.answer ? `
                <div class="bg-emerald-50 p-3 rounded-xl border border-emerald-200 text-emerald-900">
                  <strong>Candidate's Answer:</strong> ${ib.answer}
                </div>
              ` : `
                <span class="text-[10px] text-amber-600 font-semibold">⏳ Candidate has not replied yet</span>
              `}
            </div>
          `).join("");
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  async replyIceBreaker(ibId) {
    const input = document.getElementById(`reply-text-${ibId}`);
    const answer = input?.value.trim();
    if (!answer) {
      this.showToast("Please enter your answer.", "error");
      return;
    }
    try {
      const res = await fetch("/api/icebreakers/reply", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ icebreaker_id: ibId, answer })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Reply submitted successfully!", "success");
        this.loadIceBreakers();
      } else {
        this.showToast(data.error || "Failed to submit reply", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  // --------------------------------------------------------------------------
  // Phase 1 Features: Kanchi Silk Trust Badge Application & Display
  // --------------------------------------------------------------------------
  loadTrustBadgeInfo() {
    const u = this.currentUser || {};
    const status = u.trust_badge_status || "unverified";
    const statusBox = document.getElementById("dash-trust-badge-status-box");
    const formBox = document.getElementById("dash-trust-badge-form-box");

    if (statusBox) {
      if (status === "verified") {
        statusBox.className = "p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-gold-500/20 to-amber-500/10 border-2 border-gold-400 space-y-2";
        statusBox.innerHTML = `
          <div class="flex items-center gap-3">
            <span class="text-3xl">🪔</span>
            <div>
              <h5 class="font-heading font-extrabold text-maroon-950 text-sm flex items-center gap-2">
                <span>Kanchi Silk Trust Verified</span>
                <span class="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">Active Seal</span>
              </h5>
              <p class="text-[11px] text-gray-700 mt-0.5">Your identity and matrimonial profile have been verified by Sarvamangala Matrimony administration.</p>
            </div>
          </div>
        `;
        if (formBox) formBox.classList.add("hidden");
      } else if (status === "pending") {
        statusBox.className = "p-5 rounded-2xl bg-amber-50 border-2 border-amber-300 space-y-2";
        statusBox.innerHTML = `
          <div class="flex items-center gap-3">
            <span class="text-3xl">⏳</span>
            <div>
              <h5 class="font-heading font-bold text-amber-950 text-sm">Application Under Review</h5>
              <p class="text-[11px] text-amber-800 mt-0.5">Your document reference is currently being authenticated by our Kanchipuram office. The badge will appear upon approval.</p>
            </div>
          </div>
        `;
        if (formBox) formBox.classList.add("hidden");
      } else {
        statusBox.className = "p-4 rounded-xl bg-gray-50 border border-gray-200 text-gray-600";
        statusBox.innerHTML = `
          <div class="flex items-center gap-2.5">
            <span class="text-xl">ℹ️</span>
            <div>
              <strong class="text-xs text-gray-800 block">Not Yet Verified</strong>
              <span class="text-[11px] text-gray-500">Apply below to receive the gold Kanchi Silk Trust seal and boost alliance inquiries by 4x.</span>
            </div>
          </div>
        `;
        if (formBox) formBox.classList.remove("hidden");
      }
    }
  }

  async applyTrustBadge() {
    if (!this.currentUser) return;
    const docType = document.getElementById("trust-doc-type").value;
    const docRef = document.getElementById("trust-doc-ref").value.trim();

    if (!docRef) {
      this.showToast("Please provide document identifier / reference.", "error");
      return;
    }

    try {
      const res = await fetch("/api/profile/apply-trust-badge", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ document_info: `${docType}: ${docRef}` })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Application submitted for admin verification! 🪔", "success");
        if (this.currentUser) this.currentUser.trust_badge_status = "pending";
        this.loadTrustBadgeInfo();
      } else {
        this.showToast(data.error || "Submission failed", "error");
      }
    } catch (e) {
      this.showToast("Network error", "error");
    }
  }

  // --------------------------------------------------------------------------
  // Phase 1 Features: Privacy Plus Settings
  // --------------------------------------------------------------------------
  async loadPrivacySettings() {
    if (!this.token) return;
    try {
      const res = await fetch("/api/settings/privacy", {
        headers: { "Authorization": `Bearer ${this.token}` }
      });
      const data = await res.json();
      if (data.privacy) {
        const form = document.getElementById("privacy-settings-form");
        if (!form) return;
        if (form.elements["photo_privacy"]) form.elements["photo_privacy"].value = data.privacy.photo_privacy || "everyone";
        if (form.elements["phone_privacy"]) form.elements["phone_privacy"].value = data.privacy.phone_privacy || "consent_only";
        if (form.elements["horoscope_privacy"]) form.elements["horoscope_privacy"].value = data.privacy.horoscope_privacy || "open";
      }
    } catch (e) {
      console.error(e);
    }
  }

  async savePrivacySettings(e) {
    e.preventDefault();
    const form = document.getElementById("privacy-settings-form");
    if (!form) return;

    const photo_privacy = form.elements["photo_privacy"]?.value || "everyone";
    const phone_privacy = form.elements["phone_privacy"]?.value || "consent_only";
    const horoscope_privacy = form.elements["horoscope_privacy"]?.value || "open";

    try {
      const res = await fetch("/api/settings/privacy", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.token}` },
        body: JSON.stringify({ photo_privacy, phone_privacy, horoscope_privacy })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast("Privacy Plus™ preferences updated securely! 🔒", "success");
      } else {
        this.showToast(data.error || "Failed to update settings", "error");
      }
    } catch (err) {
      this.showToast("Network error", "error");
    }
  }

}

// Initialize App
window.smApp = new SarvamangalaApp();
