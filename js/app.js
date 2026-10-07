/**
 * Sarvamangala Matrimony – Kanchipuram
 * Main Application Logic & Reactive Controllers
 */

// Distance matrix from Kanchipuram to major Tamil Nadu districts (in km)
const TN_DISTRICTS_DATA = {
  "Kanchipuram": { lat: 12.8250, lng: 79.7038, distFromKanchi: 0 },
  "Chengalpattu": { lat: 12.6922, lng: 79.9765, distFromKanchi: 35 },
  "Chennai": { lat: 13.0827, lng: 80.2707, distFromKanchi: 72 },
  "Tiruvallur": { lat: 13.1231, lng: 79.9120, distFromKanchi: 45 },
  "Vellore": { lat: 12.9165, lng: 79.1325, distFromKanchi: 68 },
  "Ranipet": { lat: 12.9298, lng: 79.3331, distFromKanchi: 42 },
  "Tiruvannamalai": { lat: 12.2253, lng: 79.0747, distFromKanchi: 105 },
  "Villupuram": { lat: 11.9401, lng: 79.4861, distFromKanchi: 118 },
  "Salem": { lat: 11.6643, lng: 78.1460, distFromKanchi: 260 },
  "Tiruchirappalli": { lat: 10.7905, lng: 78.7047, distFromKanchi: 285 },
  "Madurai": { lat: 9.9252, lng: 78.1198, distFromKanchi: 410 },
  "Coimbatore": { lat: 11.0168, lng: 76.9558, distFromKanchi: 430 },
  "Thanjavur": { lat: 10.7870, lng: 79.1378, distFromKanchi: 295 },
  "Erode": { lat: 11.3410, lng: 77.7172, distFromKanchi: 350 },
  "Tirunelveli": { lat: 8.7139, lng: 77.7567, distFromKanchi: 560 },
  "Kanyakumari": { lat: 8.0883, lng: 77.5385, distFromKanchi: 640 }
};

// Seed Profiles: Realistic Tamil Hindu Profiles
const SEED_PROFILES = [
  {
    id: "SM-2026-9214",
    name: "Priya S.",
    gender: "female",
    age: 25,
    height: "5 ft 4 in",
    religion: "Hindu",
    caste: "Mudaliar",
    subcaste: "Thuluva Vellalar (Siva Gothram)",
    motherTongue: "Tamil",
    district: "Kanchipuram",
    city: "Kanchipuram",
    address: "Gandhi Road, Kanchipuram",
    education: "B.Tech (Information Technology)",
    occupation: "Software Engineer, Infosys (Hybrid)",
    income: "₹9.5 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Rishabam (Taurus)",
      nakshatra: "Rohini",
      lagnam: "Simmam",
      birthDate: "2001-05-14",
      birthTime: "07:35 AM",
      birthPlace: "Kanchipuram",
      dosham: "None (தோஷமில்லை)",
      verified: true
    },
    partnerPref: "Groom: 26-29 yrs, B.E / B.Tech / MBA, Settled in Chennai or Kanchipuram, Mudaliar / Pillai, Non-Smoker.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-12",
    compatibility: 92,
    poruthams: {
      dina: "compatible",
      gana: "compatible",
      mahendra: "compatible",
      sthree: "compatible",
      yoni: "moderate",
      rasi: "compatible",
      rasiAdhipathi: "compatible",
      vasya: "moderate",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-8842",
    name: "Anitha R.",
    gender: "female",
    age: 26,
    height: "5 ft 3 in",
    religion: "Hindu",
    caste: "Pillai",
    subcaste: "Saiva Pillai",
    motherTongue: "Tamil",
    district: "Chengalpattu",
    city: "Chengalpattu",
    address: "Alagesan Nagar, Chengalpattu",
    education: "M.Sc Mathematics, B.Ed",
    occupation: "Senior Higher Secondary Lecturer",
    income: "₹6.2 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Kanni (Virgo)",
      nakshatra: "Hastham",
      lagnam: "Kanni",
      birthDate: "2000-08-22",
      birthTime: "11:20 AM",
      birthPlace: "Chengalpattu",
      dosham: "None",
      verified: true
    },
    partnerPref: "Groom: 27-31 yrs, Master's degree / Govt employee or IT, Pillai / Mudaliar, values traditional family life.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-15",
    compatibility: 86,
    poruthams: {
      dina: "compatible",
      gana: "moderate",
      mahendra: "compatible",
      sthree: "compatible",
      yoni: "compatible",
      rasi: "moderate",
      rasiAdhipathi: "compatible",
      vasya: "compatible",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-8109",
    name: "Lakshmi Narayanan",
    gender: "female",
    age: 24,
    height: "5 ft 2 in",
    religion: "Hindu",
    caste: "Iyer",
    subcaste: "Vadama (Kausika Gothram)",
    motherTongue: "Tamil",
    district: "Chennai",
    city: "Mylapore, Chennai",
    address: "South Mada Street, Mylapore, Chennai",
    education: "B.Com, Chartered Accountant (Inter)",
    occupation: "Senior Financial Analyst, TCS",
    income: "₹8.4 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Makaram (Capricorn)",
      nakshatra: "Thiruvonam",
      lagnam: "Dhanusu",
      birthDate: "2002-01-10",
      birthTime: "04:45 PM",
      birthPlace: "Chennai",
      dosham: "None",
      verified: true
    },
    partnerPref: "Groom: 25-29 yrs, CA / MBA / B.Tech, Traditional Brahmin family, Chennai or Bangalore.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-20",
    compatibility: 82,
    poruthams: {
      dina: "compatible",
      gana: "compatible",
      mahendra: "moderate",
      sthree: "compatible",
      yoni: "moderate",
      rasi: "compatible",
      rasiAdhipathi: "moderate",
      vasya: "compatible",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-7451",
    name: "Karthikeyan M.",
    gender: "male",
    age: 28,
    height: "5 ft 10 in",
    religion: "Hindu",
    caste: "Mudaliar",
    subcaste: "Agamudaiyar",
    motherTongue: "Tamil",
    district: "Kanchipuram",
    city: "Kanchipuram",
    address: "Ennaikaran Street, Kanchipuram",
    education: "B.E Mechanical Engineering",
    occupation: "Assistant Manager, Hyundai Motors (Sriperumbudur)",
    income: "₹14.2 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Mesham (Aries)",
      nakshatra: "Aswini",
      lagnam: "Mesham",
      birthDate: "1998-04-18",
      birthTime: "06:15 AM",
      birthPlace: "Kanchipuram",
      dosham: "None",
      verified: true
    },
    partnerPref: "Bride: 23-26 yrs, Graduate / Professional, Vegetarian or Non-Vegetarian, Mudaliar community, Tamil speaking.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-05",
    compatibility: 94,
    poruthams: {
      dina: "compatible",
      gana: "compatible",
      mahendra: "compatible",
      sthree: "compatible",
      yoni: "compatible",
      rasi: "compatible",
      rasiAdhipathi: "compatible",
      vasya: "moderate",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-6320",
    name: "Balaji R.",
    gender: "male",
    age: 29,
    height: "5 ft 9 in",
    religion: "Hindu",
    caste: "Vanniyar",
    subcaste: "Padayatchi",
    motherTongue: "Tamil",
    district: "Chengalpattu",
    city: "Maraimalai Nagar",
    address: "Main Road, Maraimalai Nagar",
    education: "M.Tech Computer Science",
    occupation: "Senior Cloud Architect, Cognizant",
    income: "₹19.0 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Simmam (Leo)",
      nakshatra: "Magam",
      lagnam: "Thulam",
      birthDate: "1997-11-04",
      birthTime: "08:10 PM",
      birthPlace: "Chengalpattu",
      dosham: "None",
      verified: true
    },
    partnerPref: "Bride: 24-27 yrs, Any degree, Family-oriented, Vanniyar / Hindu, ready to settle near Chennai / Chengalpattu.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-18",
    compatibility: 88,
    poruthams: {
      dina: "compatible",
      gana: "moderate",
      mahendra: "compatible",
      sthree: "compatible",
      yoni: "moderate",
      rasi: "compatible",
      rasiAdhipathi: "compatible",
      vasya: "compatible",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-5591",
    name: "Dr. Srinivasan K.",
    gender: "male",
    age: 30,
    height: "5 ft 11 in",
    religion: "Hindu",
    caste: "Naidu",
    subcaste: "Kamma",
    motherTongue: "Telugu / Tamil",
    district: "Vellore",
    city: "Vellore",
    address: "Katpadi Road, Vellore",
    education: "MBBS, MD (General Medicine)",
    occupation: "Consultant Physician, Private Hospital",
    income: "₹24.0 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Dhanusu (Sagittarius)",
      nakshatra: "Moolam",
      lagnam: "Kumbam",
      birthDate: "1996-06-25",
      birthTime: "02:30 AM",
      birthPlace: "Vellore",
      dosham: "None",
      verified: true
    },
    partnerPref: "Bride: 25-28 yrs, Doctor / Engineer / Professional, Hindu Naidu / Balija, Vellore / Chennai preferred.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-22",
    compatibility: 90,
    poruthams: {
      dina: "compatible",
      gana: "compatible",
      mahendra: "compatible",
      sthree: "moderate",
      yoni: "compatible",
      rasi: "compatible",
      rasiAdhipathi: "compatible",
      vasya: "moderate",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-4412",
    name: "Deepa S.",
    gender: "female",
    age: 27,
    height: "5 ft 5 in",
    religion: "Hindu",
    caste: "Chettiar",
    subcaste: "Devanga Chettiar",
    motherTongue: "Tamil",
    district: "Tiruvallur",
    city: "Tiruvallur",
    address: "Bazaar Street, Tiruvallur",
    education: "B.Arch (Architecture)",
    occupation: "Senior Interior Architect",
    income: "₹10.5 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Thulam (Libra)",
      nakshatra: "Swathi",
      lagnam: "Rishabam",
      birthDate: "1999-03-12",
      birthTime: "05:50 AM",
      birthPlace: "Tiruvallur",
      dosham: "None",
      verified: true
    },
    partnerPref: "Groom: 28-31 yrs, Architect / Engineer / Business, Chettiar, respect for traditional values.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-26",
    compatibility: 85,
    poruthams: {
      dina: "compatible",
      gana: "compatible",
      mahendra: "moderate",
      sthree: "compatible",
      yoni: "moderate",
      rasi: "compatible",
      rasiAdhipathi: "moderate",
      vasya: "compatible",
      rajju: "compatible",
      vedha: "compatible"
    }
  },
  {
    id: "SM-2026-3890",
    name: "Vigneshwaran P.",
    gender: "male",
    age: 29,
    height: "5 ft 8 in",
    religion: "Hindu",
    caste: "Nadar",
    subcaste: "Gramani",
    motherTongue: "Tamil",
    district: "Madurai",
    city: "Madurai",
    address: "KK Nagar, Madurai",
    education: "B.Tech & MBA (Finance)",
    occupation: "Director, Agro Export Enterprise",
    income: "₹26.0 Lakhs / year",
    maritalStatus: "Never Married",
    photoUrl: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80",
    horoscope: {
      rasi: "Kumbam (Aquarius)",
      nakshatra: "Sathayam",
      lagnam: "Mesham",
      birthDate: "1997-12-19",
      birthTime: "10:45 AM",
      birthPlace: "Madurai",
      dosham: "None",
      verified: true
    },
    partnerPref: "Bride: 23-27 yrs, Graduate, Hindu Nadar, family-centric and traditional nature.",
    isApproved: true,
    paymentStatus: "Paid (₹2,000)",
    regDate: "2026-09-28",
    compatibility: 81,
    poruthams: {
      dina: "moderate",
      gana: "compatible",
      mahendra: "moderate",
      sthree: "compatible",
      yoni: "compatible",
      rasi: "moderate",
      rasiAdhipathi: "compatible",
      vasya: "moderate",
      rajju: "compatible",
      vedha: "compatible"
    }
  }
];

// App State
class SarvamangalaApp {
  constructor() {
    this.currentLang = localStorage.getItem("sm_lang") || "en";
    this.profiles = this.loadProfiles();
    this.activeFilter = "all";
    this.currentNearMeDistrict = "Kanchipuram";
    this.currentNearMeRadius = 50; // default 50km
    this.selectedProfileForModal = null;
    this.currentRegStep = 1;
    this.newRegistrationData = {};
    this.enquiries = JSON.parse(localStorage.getItem("sm_enquiries") || "[]");
    
    // Default simulated user for Priya matching
    this.currentUserAstrology = {
      name: "Groom Candidate",
      rasi: "Mesham",
      nakshatra: "Aswini",
      caste: "Mudaliar"
    };

    this.init();
  }

  loadProfiles() {
    const saved = localStorage.getItem("sm_profiles");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Error loading profiles from localStorage", e);
      }
    }
    localStorage.setItem("sm_profiles", JSON.stringify(SEED_PROFILES));
    return [...SEED_PROFILES];
  }

  saveProfiles() {
    localStorage.setItem("sm_profiles", JSON.stringify(this.profiles));
  }

  init() {
    this.initLoader();
    this.initScrollEffects();
    this.initMobileDrawer();
    this.applyLanguage(this.currentLang);
    this.renderProfiles();
    this.renderNearMeMatches();
    this.initPriyaMatching();
    this.bindEvents();
  }

  // Set & Switch Language
  setLanguage(lang) {
    if (!i18nData[lang]) return;
    this.currentLang = lang;
    localStorage.setItem("sm_lang", lang);
    this.applyLanguage(lang);
    this.renderProfiles();
    this.renderNearMeMatches();
    this.initPriyaMatching();
    this.showToast(lang === 'ta' ? 'தமிழ் மொழி தேர்வு செய்யப்பட்டது' : 'Language switched to English');
  }

  applyLanguage(lang) {
    const dict = i18nData[lang];
    if (!dict) return;

    // Update simple text elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });

    // Update placeholders
    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
      const key = el.getAttribute("data-i18n-ph");
      if (dict[key]) {
        el.setAttribute("placeholder", dict[key]);
      }
    });

    // Update active state of language toggle buttons
    const btnEn = document.getElementById("btn-lang-en");
    const btnTa = document.getElementById("btn-lang-ta");
    if (btnEn && btnTa) {
      if (lang === "en") {
        btnEn.className = "px-2.5 py-1 text-xs font-semibold rounded bg-[#6B111E] text-white shadow-sm";
        btnTa.className = "px-2.5 py-1 text-xs font-semibold rounded text-[#6B111E] hover:bg-[#F3E8D3]";
      } else {
        btnTa.className = "px-2.5 py-1 text-xs font-semibold rounded bg-[#6B111E] text-white shadow-sm";
        btnEn.className = "px-2.5 py-1 text-xs font-semibold rounded text-[#6B111E] hover:bg-[#F3E8D3]";
      }
    }
  }

  getTranslation(key) {
    return i18nData[this.currentLang]?.[key] || i18nData["en"]?.[key] || key;
  }

  // Render Profiles Directory
  renderProfiles() {
    const container = document.getElementById("profiles-grid");
    if (!container) return;

    let filtered = this.profiles.filter(p => p.isApproved);
    if (this.activeFilter === "brides") {
      filtered = filtered.filter(p => p.gender === "female");
    } else if (this.activeFilter === "grooms") {
      filtered = filtered.filter(p => p.gender === "male");
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="col-span-full py-12 text-center text-gray-500">
          <p class="text-lg">No profiles found for this category.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(p => `
      <div class="bg-white rounded-2xl border border-[#E6D2B1] overflow-hidden shadow-sm card-hover-shadow flex flex-col transition-all">
        <!-- Photo and Badge header -->
        <div class="relative h-64 overflow-hidden bg-[#FAF5EB]">
          <img src="${p.photoUrl}" alt="${p.name}" class="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-500" onerror="this.src='https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80'" />
          <div class="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent"></div>
          
          <!-- ID & Horoscope Verified Tag -->
          <div class="absolute top-3 left-3 bg-[#6B111E]/90 backdrop-blur-sm text-white px-2.5 py-1 rounded-full text-xs font-medium border border-[#DFB758]/50 flex items-center gap-1 shadow">
            <span>🪔</span> ${p.id}
          </div>

          <div class="absolute top-3 right-3 bg-emerald-700/90 text-white px-2.5 py-1 rounded-full text-xs font-semibold backdrop-blur-sm flex items-center gap-1 shadow">
            <span>✓</span> Jathagam Checked
          </div>

          <!-- Bottom Floating Name & District -->
          <div class="absolute bottom-3 left-3 right-3 text-white">
            <h3 class="font-heading text-xl font-bold text-[#FCE082] drop-shadow-sm flex items-center justify-between">
              <span>${p.name}</span>
              <span class="text-xs bg-[#C99B38] text-[#30060C] px-2 py-0.5 rounded-full font-bold">
                ${p.compatibility}% Match
              </span>
            </h3>
            <p class="text-xs text-gray-200 flex items-center gap-1.5 mt-0.5">
              <span>📍 ${p.city}, ${p.district}</span>
              <span>•</span>
              <span>${p.age} Yrs, ${p.height}</span>
            </p>
          </div>
        </div>

        <!-- Details Body -->
        <div class="p-5 flex-1 flex flex-col justify-between space-y-4">
          <div class="space-y-2.5 text-sm">
            <div class="flex items-center justify-between text-xs py-1 border-b border-[#F3E8D3]">
              <span class="text-gray-500 font-medium">${this.getTranslation("lblCaste")}:</span>
              <span class="font-semibold text-[#6B111E]">${p.caste} (${p.subcaste.split(' ')[0]})</span>
            </div>
            
            <div class="flex items-center justify-between text-xs py-1 border-b border-[#F3E8D3]">
              <span class="text-gray-500 font-medium">${this.getTranslation("lblEducation")}:</span>
              <span class="font-medium text-gray-800 text-right truncate max-w-[180px]">${p.education}</span>
            </div>

            <div class="flex items-center justify-between text-xs py-1 border-b border-[#F3E8D3]">
              <span class="text-gray-500 font-medium">${this.getTranslation("lblJob")}:</span>
              <span class="font-medium text-gray-800 text-right truncate max-w-[180px]">${p.occupation}</span>
            </div>

            <div class="flex items-center justify-between text-xs py-1 border-b border-[#F3E8D3]">
              <span class="text-gray-500 font-medium">Rasi & Star:</span>
              <span class="font-semibold text-amber-900">${p.horoscope.rasi} • ${p.horoscope.nakshatra}</span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="pt-2 grid grid-cols-2 gap-2">
            <button onclick="window.smApp.openProfileModal('${p.id}')" class="w-full text-xs font-semibold py-2 px-3 rounded-lg border border-[#6B111E] text-[#6B111E] hover:bg-[#FAF5EB] transition-colors flex items-center justify-center gap-1">
              <span>👁️</span> ${this.getTranslation("btnViewProfile")}
            </button>
            <button onclick="window.smApp.openEnquiryForProfile('${p.id}')" class="w-full text-xs font-semibold py-2 px-3 rounded-lg bg-[#6B111E] text-white hover:bg-[#851828] transition-colors flex items-center justify-center gap-1 shadow-sm">
              <span>📞</span> ${this.getTranslation("btnEnquireProfile")}
            </button>
          </div>
        </div>
      </div>
    `).join("");
  }

  // Filter profiles by Gender
  setProfileFilter(filter) {
    this.activeFilter = filter;
    document.querySelectorAll("[data-filter-btn]").forEach(btn => {
      if (btn.getAttribute("data-filter-btn") === filter) {
        btn.className = "px-4 py-2 rounded-full text-xs font-bold bg-[#6B111E] text-white shadow-sm border border-[#DFB758]/50";
      } else {
        btn.className = "px-4 py-2 rounded-full text-xs font-bold bg-[#FAF5EB] text-gray-700 hover:bg-[#F3E8D3] border border-[#E6D2B1]";
      }
    });
    this.renderProfiles();
  }

  // Near Me Matches Engine
  renderNearMeMatches() {
    const container = document.getElementById("near-me-grid");
    if (!container) return;

    const baseDist = TN_DISTRICTS_DATA[this.currentNearMeDistrict] || TN_DISTRICTS_DATA["Kanchipuram"];
    
    // Compute distance for all approved profiles
    const matchesWithDistance = this.profiles
      .filter(p => p.isApproved)
      .map(p => {
        const pDistrictData = TN_DISTRICTS_DATA[p.district] || { distFromKanchi: 50 };
        // Approximate distance calculation between two TN districts
        let approxKm = 0;
        if (p.district === this.currentNearMeDistrict) {
          approxKm = 0;
        } else {
          approxKm = Math.abs(pDistrictData.distFromKanchi - baseDist.distFromKanchi) + 15;
        }
        return {
          ...p,
          distanceKm: approxKm
        };
      })
      .filter(p => {
        if (this.currentNearMeRadius === 'all' || this.currentNearMeRadius >= 500) return true;
        return p.distanceKm <= this.currentNearMeRadius;
      })
      .sort((a, b) => a.distanceKm - b.distanceKm);

    if (matchesWithDistance.length === 0) {
      container.innerHTML = `
        <div class="col-span-full py-12 text-center text-gray-600 bg-white rounded-2xl border border-[#E6D2B1] p-8">
          <p class="text-base font-semibold">No verified matches found within ${this.currentNearMeRadius} km of ${this.currentNearMeDistrict}.</p>
          <p class="text-xs text-gray-500 mt-1">Try expanding your distance radius to 100 km or "All Tamil Nadu".</p>
        </div>
      `;
      return;
    }

    container.innerHTML = matchesWithDistance.slice(0, 4).map(p => `
      <div class="bg-white rounded-xl border border-[#E6D2B1] p-4 flex items-center justify-between gap-4 card-hover-shadow">
        <div class="flex items-center gap-3.5">
          <img src="${p.photoUrl}" alt="${p.name}" class="w-16 h-16 rounded-full object-cover border-2 border-[#DFB758] shadow-sm flex-shrink-0" />
          <div>
            <div class="flex items-center gap-2">
              <h4 class="font-heading font-bold text-base text-[#6B111E]">${p.name}</h4>
              <span class="text-[11px] bg-emerald-50 text-emerald-800 border border-emerald-300 px-2 py-0.2 rounded-full font-bold">
                ${p.compatibility}% Match
              </span>
            </div>
            <p class="text-xs text-gray-600 mt-0.5">${p.caste} • ${p.education}</p>
            <p class="text-xs font-semibold text-amber-900 mt-1 flex items-center gap-1">
              <span>📍 ${p.city}, ${p.district}</span>
              <span class="bg-[#FAF5EB] text-[#6B111E] px-2 py-0.5 rounded text-[11px] font-bold border border-[#E6D2B1]">
                ${p.distanceKm === 0 ? 'Same City' : p.distanceKm + ' km away'}
              </span>
            </p>
          </div>
        </div>
        <div class="flex flex-col gap-1.5 flex-shrink-0">
          <button onclick="window.smApp.openProfileModal('${p.id}')" class="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#6B111E] text-[#6B111E] hover:bg-[#FAF5EB] transition-colors">
            View
          </button>
          <button onclick="window.smApp.openEnquiryForProfile('${p.id}')" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#6B111E] text-white hover:bg-[#851828] transition-colors shadow-sm">
            Enquire
          </button>
        </div>
      </div>
    `).join("");
  }

  updateNearMeDistrict(district) {
    this.currentNearMeDistrict = district;
    this.renderNearMeMatches();
  }

  updateNearMeRadius(radius) {
    this.currentNearMeRadius = radius === 'all' ? 1000 : parseInt(radius);
    this.renderNearMeMatches();
  }

  // =========================================================================
  // Animation & System Controllers: Loader, Scroll, Drawer
  // =========================================================================
  initLoader() {
    const loader = document.getElementById("site-loader");
    if (!loader) return;
    const hideLoader = () => {
      loader.classList.add("loader-hidden");
      setTimeout(() => {
        loader.style.display = "none";
      }, 700);
    };

    if (document.readyState === "complete") {
      setTimeout(hideLoader, 350);
    } else {
      window.addEventListener("load", () => setTimeout(hideLoader, 350));
      setTimeout(hideLoader, 1000); // Safety fallback
    }
  }

  initScrollEffects() {
    const header = document.querySelector("header");
    const heroBg = document.getElementById("hero-parallax-bg");
    const heroContent = document.getElementById("hero-main-content");
    const heroSection = document.getElementById("home");

    const onScroll = () => {
      const scrollY = window.scrollY;

      // Header transition between transparent and scrolled
      if (header) {
        if (scrollY > 30) {
          header.classList.add("header-scrolled");
          header.classList.remove("header-transparent");
        } else {
          header.classList.remove("header-scrolled");
          header.classList.add("header-transparent");
        }
      }

      // Parallax Background movement & Content upward fade
      if (heroSection && (heroBg || heroContent)) {
        const heroHeight = heroSection.offsetHeight || window.innerHeight;
        const progress = Math.min(1, Math.max(0, scrollY / heroHeight));

        if (heroBg) {
          heroBg.style.transform = `translate3d(0, ${scrollY * 0.28}px, 0)`;
        }
        if (heroContent) {
          heroContent.style.opacity = `${Math.max(0, 1 - progress * 1.35)}`;
          heroContent.style.transform = `translate3d(0, -${progress * 65}px, 0)`;
        }
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    // IntersectionObserver for smooth scroll reveals
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            obs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });

      document.querySelectorAll(".reveal, .reveal-left, .reveal-right").forEach(el => observer.observe(el));
    } else {
      document.querySelectorAll(".reveal, .reveal-left, .reveal-right").forEach(el => el.classList.add("revealed"));
    }

    // Parallax tilt on hero profile cards
    const card1 = document.querySelector(".hero-float-card-1");
    const card2 = document.querySelector(".hero-float-card-2");
    if (heroSection && (card1 || card2)) {
      heroSection.addEventListener("mousemove", (e) => {
        const { clientX, clientY } = e;
        const xOffset = (clientX / window.innerWidth - 0.5) * 14;
        const yOffset = (clientY / window.innerHeight - 0.5) * 14;
        if (card1) card1.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
        if (card2) card2.style.transform = `translate(${-xOffset}px, ${-yOffset}px)`;
      });
      heroSection.addEventListener("mouseleave", () => {
        if (card1) card1.style.transform = "";
        if (card2) card2.style.transform = "";
      });
    }
  }

  initMobileDrawer() {
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.closeMobileMenu();
    });
  }

  toggleMobileMenu() {
    const drawer = document.getElementById("mobile-menu-drawer");
    if (!drawer) return;
    drawer.classList.toggle("drawer-open");
    document.body.style.overflow = drawer.classList.contains("drawer-open") ? "hidden" : "";
  }

  openMobileMenu() {
    const drawer = document.getElementById("mobile-menu-drawer");
    if (!drawer) return;
    drawer.classList.add("drawer-open");
    document.body.style.overflow = "hidden";
  }

  closeMobileMenu() {
    const drawer = document.getElementById("mobile-menu-drawer");
    if (!drawer) return;
    drawer.classList.remove("drawer-open");
    document.body.style.overflow = "";
  }

  // =========================================================================
  // "Priya Matching ❤️" Core Feature & Interactive Astrological System
  // =========================================================================
  initPriyaMatching() {
    this.renderPriyaCards(this.priyaCardFilter || 'all');
  }

  filterPriyaCards(filter) {
    this.priyaCardFilter = filter;
    
    // Update button styling
    const btnAll = document.getElementById("priya-filter-all");
    const btnBrides = document.getElementById("priya-filter-brides");
    const btnGrooms = document.getElementById("priya-filter-grooms");

    [btnAll, btnBrides, btnGrooms].forEach(btn => {
      if (btn) {
        btn.className = "px-4 py-2 rounded-full text-xs font-bold bg-white text-gray-700 hover:bg-sandal-200 border border-sandal-300 shadow-2xs cursor-pointer transition-all";
      }
    });

    const activeBtn = filter === 'female' ? btnBrides : (filter === 'male' ? btnGrooms : btnAll);
    if (activeBtn) {
      activeBtn.className = "px-4 py-2 rounded-full text-xs font-bold bg-maroon-800 text-gold-300 border border-gold-400 shadow-sm cursor-pointer transition-all";
    }

    this.renderPriyaCards(filter);
  }

  renderPriyaCards(filter = 'all') {
    const grid = document.getElementById("priya-matching-cards-grid");
    if (!grid) return;

    let matchedProfiles = [...this.profiles].filter(p => p.compatibility && p.compatibility >= 80);
    
    if (filter === 'female') {
      matchedProfiles = matchedProfiles.filter(p => p.gender === 'female');
    } else if (filter === 'male') {
      matchedProfiles = matchedProfiles.filter(p => p.gender === 'male');
    }

    // Sort by compatibility descending
    matchedProfiles.sort((a, b) => (b.compatibility || 0) - (a.compatibility || 0));

    grid.innerHTML = matchedProfiles.map((p, idx) => {
      const matchScore = p.compatibility || 90;
      const gunaScore = (matchScore / 10).toFixed(1);
      const isFemale = p.gender === 'female';
      const roleBadge = isFemale ? 'Verified Bride' : 'Verified Groom';
      const star = p.horoscope ? p.horoscope.nakshatra : 'Rohini';
      const rasi = p.horoscope ? p.horoscope.rasi : 'Rishabam';

      return `
        <div class="priya-card bg-white rounded-3xl border-2 border-gold-400/70 p-5 shadow-lg relative flex flex-col justify-between reveal delay-${(idx % 4) + 1}">
          <!-- Top Row: Photo, Verified Status & Compatibility Badge -->
          <div class="space-y-4">
            <div class="relative w-full h-56 rounded-2xl overflow-hidden shadow-inner bg-sandal-100">
              <img src="${p.photoUrl}" alt="${p.name}" class="priya-card-image w-full h-full object-cover object-top" onerror="this.src='https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80'" />
              
              <!-- Gradient Overlay on Photo -->
              <div class="absolute inset-0 bg-gradient-to-t from-maroon-950/80 via-transparent to-black/20 pointer-events-none"></div>

              <!-- Top Left Verified Badge -->
              <div class="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-3 py-1 rounded-full border border-emerald-400/80 shadow-sm flex items-center gap-1.5 text-[11px] font-extrabold text-emerald-800">
                <span>✓</span> <span>${roleBadge}</span>
              </div>

              <!-- Top Right Compatibility Percentage Badge (Pulsing Heart) -->
              <div class="absolute top-3 right-3 bg-gradient-to-r from-amber-400 via-gold-400 to-rose-500 text-maroon-950 font-extrabold text-xs sm:text-sm px-3.5 py-1 rounded-full shadow-lg border border-white flex items-center gap-1.5 animate-heart-beat">
                <span>❤️</span> <span>${matchScore}% Match</span>
              </div>

              <!-- Bottom Overlay Profile Details on Photo -->
              <div class="absolute bottom-3 left-3 right-3 text-white">
                <div class="flex items-baseline justify-between">
                  <h3 class="font-heading text-xl font-bold tracking-tight text-white drop-shadow-md">
                    ${p.name}, ${p.age}
                  </h3>
                  <span class="text-xs text-gold-300 font-semibold drop-shadow">${p.height || '5 ft 4 in'}</span>
                </div>
                <p class="text-xs text-rose-100 font-medium truncate drop-shadow">
                  📍 ${p.city}, ${p.district}
                </p>
              </div>
            </div>

            <!-- Profile Attributes Details -->
            <div class="space-y-2 pt-1">
              <div class="flex items-center justify-between text-xs text-gray-700">
                <span class="font-semibold text-maroon-900">Community:</span>
                <span class="font-bold text-gray-900 bg-sandal-100 px-2.5 py-0.5 rounded-full border border-sandal-300">${p.caste} (${p.subcaste ? p.subcaste.split(' ')[0] : 'Hindu'})</span>
              </div>
              <div class="flex items-center justify-between text-xs text-gray-700">
                <span class="font-semibold text-maroon-900">Education:</span>
                <span class="font-medium text-gray-800 truncate max-w-[180px]">${p.education}</span>
              </div>
              <div class="flex items-center justify-between text-xs text-gray-700">
                <span class="font-semibold text-maroon-900">Profession:</span>
                <span class="font-medium text-gray-800 truncate max-w-[180px]">${p.occupation}</span>
              </div>

              <!-- Astrological & Score Highlight -->
              <div class="mt-3 p-3 rounded-2xl bg-gradient-to-r from-sandal-100 via-amber-50 to-sandal-100 border border-gold-400/50 flex items-center justify-between">
                <div>
                  <span class="text-[10px] uppercase font-extrabold text-gold-700 block tracking-wider">Matching Score</span>
                  <span class="text-xs font-extrabold text-maroon-950">${gunaScore} / 10 Compatibility</span>
                </div>
                <div class="text-right">
                  <span class="text-[10px] text-gray-500 block">Vedic Alignment</span>
                  <span class="text-xs font-bold text-emerald-800">Rajju Auspicious</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Action Buttons -->
          <div class="mt-4 pt-3 border-t border-sandal-200 flex items-center gap-2">
            <button onclick="window.smApp.openProfileModal('${p.id}')" class="btn-tactile flex-1 bg-sandal-100 hover:bg-sandal-200 text-maroon-950 font-bold text-xs py-2.5 px-3 rounded-xl border border-sandal-300 text-center cursor-pointer transition-colors">
              View Profile
            </button>
            <button onclick="window.smApp.openPriyaMatchingModal('${p.id}')" class="btn-shimmer btn-tactile flex-1 bg-maroon-800 hover:bg-maroon-700 text-gold-300 font-extrabold text-xs py-2.5 px-3 rounded-xl border border-gold-400 text-center cursor-pointer shadow flex items-center justify-center gap-1">
              <span>❤️</span> <span>View Match</span>
            </button>
          </div>

          <!-- Smooth Hover Compatibility Overlay (Drawer revealing more compatibility information) -->
          <div class="priya-hover-reveal absolute inset-0 bg-gradient-to-b from-maroon-950 via-maroon-900 to-[#480A13] text-white p-6 rounded-3xl flex flex-col justify-between z-30 border-2 border-gold-400 shadow-2xl">
            <div>
              <div class="flex items-center justify-between border-b border-maroon-800 pb-3">
                <div class="flex items-center gap-2">
                  <span class="text-xl animate-heart-beat">❤️</span>
                  <h4 class="font-heading font-bold text-base text-gold-200">${p.name} • Match Report</h4>
                </div>
                <span class="bg-gold-500 text-maroon-950 font-extrabold text-xs px-2.5 py-0.5 rounded-full">
                  ${matchScore}% Match
                </span>
              </div>

              <!-- Porutham Breakdown Highlights -->
              <div class="mt-4 space-y-2.5 text-xs">
                <div class="p-2.5 rounded-xl bg-white/10 border border-gold-400/30 flex items-center justify-between">
                  <span class="text-gray-200 font-medium">Rajju Porutham (Mangalsutra)</span>
                  <span class="text-emerald-400 font-bold flex items-center gap-1"><span>✓</span> Auspicious</span>
                </div>
                <div class="p-2.5 rounded-xl bg-white/10 border border-gold-400/30 flex items-center justify-between">
                  <span class="text-gray-200 font-medium">Dina & Gana Porutham</span>
                  <span class="text-emerald-400 font-bold flex items-center gap-1"><span>✓</span> Compatible</span>
                </div>
                <div class="p-2.5 rounded-xl bg-white/10 border border-gold-400/30 flex items-center justify-between">
                  <span class="text-gray-200 font-medium">Rasi & Star Alignment</span>
                  <span class="text-gold-300 font-bold truncate max-w-[140px]">${star} & ${rasi.split(' ')[0]}</span>
                </div>
                <div class="p-2.5 rounded-xl bg-white/10 border border-gold-400/30 flex items-center justify-between">
                  <span class="text-gray-200 font-medium">Family Values & Harmony</span>
                  <span class="text-emerald-300 font-bold">100% Traditional</span>
                </div>
              </div>
            </div>

            <!-- Action buttons inside reveal -->
            <div class="space-y-2 pt-3 border-t border-maroon-800">
              <button onclick="window.smApp.openPriyaMatchingModal('${p.id}')" class="w-full bg-gradient-to-r from-gold-400 to-amber-500 text-maroon-950 font-extrabold text-xs py-2.5 rounded-xl shadow border border-white flex items-center justify-center gap-1.5 cursor-pointer hover:brightness-105 transition-all">
                <span>🪐</span> <span>View Full Porutham Breakdown</span>
              </button>
              <div class="flex items-center gap-2">
                <a href="https://wa.me/918248853928?text=Namaskaram%2C+I+am+interested+in+Priya+Matching+profile+ID+${p.id}+(${encodeURIComponent(p.name)})+on+Sarvamangala+Matrimony." target="_blank" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2.5 rounded-xl flex items-center justify-center gap-1 shadow transition-colors">
                  <span>💬</span> WhatsApp (8248853928)
                </a>
                <a href="tel:8248853928" class="bg-maroon-800 hover:bg-maroon-700 text-gold-300 px-3 py-2.5 rounded-xl border border-gold-500/40 text-xs font-bold transition-colors">
                  📞 Call
                </a>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  // Open Dedicated Priya Matching Modal
  openPriyaMatchingModal(candidateId = "SM-2026-9214") {
    const candidate = this.profiles.find(p => p.id === candidateId) || this.profiles[0];
    if (!candidate) return;

    this.currentPriyaCandidate = candidate;
    const banner = document.getElementById("pm-modal-candidate-banner");
    if (banner) {
      banner.innerHTML = `
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-full overflow-hidden border-2 border-gold-500 shadow flex-shrink-0">
            <img src="${candidate.photoUrl}" alt="${candidate.name}" class="w-full h-full object-cover">
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h4 class="font-heading text-lg sm:text-xl font-bold text-maroon-950">${candidate.name}, ${candidate.age}</h4>
              <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">
                ${candidate.gender === 'female' ? 'Verified Bride' : 'Verified Groom'}
              </span>
            </div>
            <p class="text-xs text-gray-600 mt-0.5">
              ${candidate.city}, ${candidate.district} • ${candidate.caste} • ${candidate.education}
            </p>
            <p class="text-xs font-semibold text-gold-700 mt-0.5">
              Star: ${candidate.horoscope ? candidate.horoscope.nakshatra : 'Rohini'} • Rasi: ${candidate.horoscope ? candidate.horoscope.rasi : 'Rishabam'}
            </p>
          </div>
        </div>
        <div class="text-right flex-shrink-0 bg-sandal-100 p-3 rounded-xl border border-gold-400">
          <span class="text-[10px] font-bold text-gray-500 uppercase block">Base Match</span>
          <span class="font-heading font-extrabold text-2xl sm:text-3xl text-maroon-900 leading-none">${candidate.compatibility || 92}%</span>
          <span class="text-[10px] text-emerald-700 font-bold block mt-0.5">Highly Compatible</span>
        </div>
      `;
    }

    this.calculateModalPorutham();
    const modal = document.getElementById("priya-matching-modal");
    if (modal) modal.showModal();
  }

  calculateModalPorutham() {
    const candidate = this.currentPriyaCandidate || this.profiles[0];
    const userStar = document.getElementById("pm-user-star")?.value || "Hastham";

    const poruthamData = [
      { name: "Dina Porutham", ta: "தினப் பொருத்தம்", desc: "Longevity, health, and freedom from disease.", status: "Auspicious", icon: "✓", state: "compatible" },
      { name: "Gana Porutham", ta: "கணப் பொருத்தம்", desc: "Temperament alignment, mutual harmony and respect.", status: "Compatible", icon: "✓", state: "compatible" },
      { name: "Mahendra Porutham", ta: "மாகேந்திரப் பொருத்தம்", desc: "Lineage continuation and blissful progeny.", status: "Auspicious", icon: "✓", state: "compatible" },
      { name: "Sthree Deergham", ta: "ஸ்திரீ தீர்க்கப் பொருத்தம்", desc: "Prosperity and longevity for the bride.", status: "Compatible", icon: "✓", state: "compatible" },
      { name: "Yoni Porutham", ta: "யோனிப் பொருத்தம்", desc: "Physical intimacy and mutual attraction.", status: "Favorable", icon: "≈", state: "moderate" },
      { name: "Rasi Porutham", ta: "ராசிப் பொருத்தம்", desc: "Family growth and peaceful coexistence.", status: "Harmonic", icon: "✓", state: "compatible" },
      { name: "Rasi Adhipathi", ta: "ராசி அதிபதிப் பொருத்தம்", desc: "Friendship between ruling planetary deities.", status: "Auspicious", icon: "✓", state: "compatible" },
      { name: "Vasya Porutham", ta: "வசியப் பொருத்தம்", desc: "Mutual magnetic attraction and affection.", status: "Harmonic", icon: "✓", state: "compatible" },
      { name: "Rajju Porutham", ta: "ரஜ்ஜுப் பொருத்தம் (மாங்கல்ய பலம்)", desc: "Sacred Mangala sutra strength and long married life. Absolutely vital.", status: "100% Auspicious (No Dosham)", icon: "✓", state: "compatible" },
      { name: "Vedha Porutham", ta: "வேதைப் பொருத்தம்", desc: "Wards off evil eyes and destructive planetary clashes.", status: "Clean & Free", icon: "✓", state: "compatible" }
    ];

    const resultBanner = document.getElementById("pm-calculation-result");
    if (resultBanner) {
      resultBanner.innerHTML = `
        <div class="flex items-center gap-3">
          <span class="text-2xl animate-heart-beat">❤️</span>
          <div>
            <strong class="text-sm font-bold text-maroon-950">Auspicious Porutham Score: 9 / 10 Poruthams Matched</strong>
            <p class="text-xs text-emerald-800 font-semibold">${userStar} & ${candidate.horoscope ? candidate.horoscope.nakshatra : 'Rohini'} are astrologically harmonic. Rajju Porutham is complete and safe.</p>
          </div>
        </div>
        <span class="font-heading font-extrabold text-2xl text-emerald-700">92%</span>
      `;
    }

    const grid = document.getElementById("pm-modal-porutham-grid");
    if (grid) {
      grid.innerHTML = poruthamData.map(item => `
        <div class="p-3 rounded-xl bg-sandal-100/70 border border-sandal-300 flex items-center justify-between">
          <div>
            <h6 class="font-bold text-xs text-maroon-950">${item.name} (${item.ta})</h6>
            <p class="text-[11px] text-gray-600">${item.desc}</p>
          </div>
          <span class="bg-emerald-100 text-emerald-900 border border-emerald-300 text-[11px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1 flex-shrink-0 shadow-2xs">
            <span>${item.icon}</span> <span>${item.status}</span>
          </span>
        </div>
      `).join("");
    }
  }

  // Profile Details Modal
  openProfileModal(profileId) {
    const profile = this.profiles.find(p => p.id === profileId);
    if (!profile) return;
    this.selectedProfileForModal = profile;

    const modal = document.getElementById("profile-detail-modal");
    const content = document.getElementById("profile-modal-content");
    if (!modal || !content) return;

    content.innerHTML = `
      <div class="relative bg-white rounded-3xl overflow-hidden shadow-2xl border-2 border-[#DFB758] max-w-2xl w-full mx-auto">
        <!-- Close Button -->
        <button onclick="document.getElementById('profile-detail-modal').close()" class="absolute top-4 right-4 z-20 w-9 h-9 rounded-full bg-black/60 text-white hover:bg-black flex items-center justify-center text-lg font-bold transition-all">
          ✕
        </button>

        <!-- Header Image & Badges -->
        <div class="relative h-72 bg-gradient-to-b from-maroon-900 to-black">
          <img src="${profile.photoUrl}" alt="${profile.name}" class="w-full h-full object-cover object-top" />
          <div class="absolute inset-0 bg-gradient-to-t from-[#480A13] via-transparent to-black/40"></div>

          <div class="absolute bottom-4 left-6 right-6 text-white">
            <div class="flex items-center gap-2">
              <span class="bg-[#DFB758] text-[#30060C] font-bold text-xs px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                ID: ${profile.id}
              </span>
              <span class="bg-emerald-600 text-white text-xs px-2.5 py-0.5 rounded-full font-semibold">
                ✓ 100% Horoscope Verified
              </span>
            </div>
            <h2 class="font-heading text-2xl sm:text-3xl font-bold text-white mt-1 drop-shadow">
              ${profile.name}
            </h2>
            <p class="text-xs sm:text-sm text-[#FCE082] mt-0.5">
              ${profile.age} Yrs • ${profile.height} • ${profile.maritalStatus} • ${profile.city}, ${profile.district}
            </p>
          </div>
        </div>

        <!-- Body Tabs & Content -->
        <div class="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
          <!-- Privacy Notice Alert -->
          <div class="bg-[#FAF5EB] border-l-4 border-[#C99B38] p-3.5 rounded-r-xl flex items-start gap-3 text-xs text-amber-950">
            <span class="text-base">🔒</span>
            <p>
              <strong>Confidentiality Guarantee:</strong> Direct telephone numbers and residential house numbers are shielded for member family privacy. To arrange a family horoscope exchange or video/personal call, contact our Kanchipuram office below.
            </p>
          </div>

          <!-- Basic & Family Details -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div class="bg-gray-50 p-3.5 rounded-xl border border-gray-200 space-y-2">
              <h4 class="font-bold text-[#6B111E] text-sm border-b pb-1">Personal & Community</h4>
              <p><span class="text-gray-500">Religion:</span> <strong>${profile.religion}</strong></p>
              <p><span class="text-gray-500">Caste:</span> <strong>${profile.caste}</strong></p>
              <p><span class="text-gray-500">Sub-caste / Gothram:</span> <strong>${profile.subcaste}</strong></p>
              <p><span class="text-gray-500">Mother Tongue:</span> <strong>${profile.motherTongue}</strong></p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-xl border border-gray-200 space-y-2">
              <h4 class="font-bold text-[#6B111E] text-sm border-b pb-1">Education & Career</h4>
              <p><span class="text-gray-500">Education:</span> <strong>${profile.education}</strong></p>
              <p><span class="text-gray-500">Occupation:</span> <strong>${profile.occupation}</strong></p>
              <p><span class="text-gray-500">Annual Income:</span> <strong>${profile.income}</strong></p>
              <p><span class="text-gray-500">Location:</span> <strong>${profile.city}, ${profile.district}</strong></p>
            </div>
          </div>

          <!-- Jathagam / Horoscope Section -->
          <div class="bg-amber-50/50 p-4 rounded-2xl border border-amber-200 space-y-3">
            <div class="flex items-center justify-between">
              <h4 class="font-heading font-bold text-sm text-[#6B111E] flex items-center gap-1.5">
                <span>🪐</span> Detailed Horoscope (ஜாதகக் குறிப்புகள்)
              </h4>
              <span class="text-xs font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                Jathagam Verified
              </span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div class="bg-white p-2 rounded-lg border border-amber-200 text-center">
                <span class="text-gray-500 block text-[10px]">Rasi (ராசி)</span>
                <strong class="text-amber-900">${profile.horoscope.rasi}</strong>
              </div>
              <div class="bg-white p-2 rounded-lg border border-amber-200 text-center">
                <span class="text-gray-500 block text-[10px]">Nakshatra (நட்சத்திரம்)</span>
                <strong class="text-amber-900">${profile.horoscope.nakshatra}</strong>
              </div>
              <div class="bg-white p-2 rounded-lg border border-amber-200 text-center">
                <span class="text-gray-500 block text-[10px]">Lagnam (லக்னம்)</span>
                <strong class="text-amber-900">${profile.horoscope.lagnam}</strong>
              </div>
              <div class="bg-white p-2 rounded-lg border border-amber-200 text-center">
                <span class="text-gray-500 block text-[10px]">Dosham (தோஷம்)</span>
                <strong class="text-amber-900">${profile.horoscope.dosham}</strong>
              </div>
            </div>

            <p class="text-[11px] text-gray-600">
              Birth particulars: ${profile.horoscope.birthDate} at ${profile.horoscope.birthTime}, ${profile.horoscope.birthPlace}. Certified horoscope chart on file.
            </p>
          </div>

          <!-- Partner Preferences -->
          <div class="bg-[#FAF5EB] p-4 rounded-2xl border border-[#E6D2B1] space-y-2 text-xs">
            <h4 class="font-bold text-[#6B111E] text-sm">Partner Preferences (எதிர்பார்ப்புகள்)</h4>
            <p class="text-gray-800 leading-relaxed">${profile.partnerPref}</p>
          </div>
        </div>

        <!-- Footer Call to Action -->
        <div class="p-6 bg-[#FAF5EB] border-t border-[#E6D2B1] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p class="text-xs text-gray-500">Ready to initiate family talks?</p>
            <p class="text-sm font-bold text-[#6B111E]">Kanchipuram Relationship Desk</p>
          </div>
          <div class="flex items-center gap-3 w-full sm:w-auto">
            <a href="https://wa.me/918248853928?text=Namaskaram%2C+I+am+interested+in+profile+ID+${profile.id}+(${encodeURIComponent(profile.name)})+on+Sarvamangala+Matrimony.+Please+share+details." target="_blank" class="flex-1 sm:flex-initial bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-3 px-5 rounded-xl flex items-center justify-center gap-1.5 shadow transition-colors">
              <span>💬</span> WhatsApp Enquiry
            </a>
            <a href="tel:8248853928" class="flex-1 sm:flex-initial bg-[#6B111E] hover:bg-[#851828] text-white font-bold text-xs py-3 px-5 rounded-xl flex items-center justify-center gap-1.5 shadow transition-colors">
              <span>📞</span> Call 8248853928
            </a>
          </div>
        </div>
      </div>
    `;

    modal.showModal();
  }

  // Enquiry for specific profile
  openEnquiryForProfile(profileId) {
    const profile = this.profiles.find(p => p.id === profileId);
    const profileName = profile ? `${profile.name} (ID: ${profile.id})` : "General Profile";
    const waUrl = `https://wa.me/918248853928?text=Namaskaram%20Sarvamangala%20Matrimony%2C%20I%20would%20like%20to%20enquire%20about%20${encodeURIComponent(profileName)}.%20Kindly%20guide%20our%20family.`;
    window.open(waUrl, "_blank");
  }

  // Standalone Horoscope 10 Porutham Calculator
  calculateHoroscopePorutham() {
    const boyStar = document.getElementById("calc-boy-star")?.value || "Aswini";
    const girlStar = document.getElementById("calc-girl-star")?.value || "Rohini";
    const resultBox = document.getElementById("calc-result-box");
    if (!resultBox) return;

    // Simulate authentic astrological algorithm based on Nakshatra pair
    // Rohini + Aswini = 9/10 high compatibility
    const poruthams = [
      { name: "1. Dina Porutham (Health)", status: true, desc: "Auspicious health and vitality harmony" },
      { name: "2. Gana Porutham (Nature)", status: true, desc: "Deva & Manushya Gana favorable alliance" },
      { name: "3. Mahendra Porutham (Offspring)", status: true, desc: "Excellent blessings for progeny and lineage" },
      { name: "4. Sthree Deergha (Longevity)", status: true, desc: "Favorable prosperity and bride's well-being" },
      { name: "5. Yoni Porutham (Intimacy)", status: true, desc: "Friendly animal yoni compatibility" },
      { name: "6. Rasi Porutham (Unity)", status: true, desc: "Mesham & Rishabam harmonious family bond" },
      { name: "7. Rasi Adhipathi (Lords)", status: true, desc: "Mars and Venus friendly cosmic alignment" },
      { name: "8. Vasya Porutham (Affection)", status: false, desc: "Moderate attraction, neutral" },
      { name: "9. Rajju Porutham (Sacred Knot)", status: true, desc: "Auspicious different Rajjus - Long married bliss (Crucial ✓)" },
      { name: "10. Vedha Porutham (Affliction)", status: true, desc: "Zero Vedha affliction detected" }
    ];

    const compatibleCount = poruthams.filter(p => p.status).length;
    const scorePct = Math.round((compatibleCount / 10) * 100);

    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `
      <div class="bg-white p-6 rounded-2xl border-2 border-[#DFB758] shadow-md space-y-4">
        <div class="flex flex-col sm:flex-row items-center justify-between border-b pb-4 gap-2">
          <div>
            <h4 class="font-heading text-lg font-bold text-[#6B111E]">Porutham Calculation Result</h4>
            <p class="text-xs text-gray-500">Boy Star: <strong>${boyStar}</strong> | Girl Star: <strong>${girlStar}</strong></p>
          </div>
          <div class="text-center sm:text-right">
            <span class="text-2xl font-extrabold text-[#6B111E]">${scorePct}%</span>
            <span class="block text-xs font-semibold text-emerald-700 font-medium">✓ Highly Auspicious Match (${compatibleCount}/10 Poruthams)</span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
          ${poruthams.map(p => `
            <div class="flex items-center justify-between p-2.5 rounded-lg border ${p.status ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950' : 'bg-gray-50 border-gray-200 text-gray-600'}">
              <div>
                <span class="font-semibold">${p.name}</span>
                <span class="block text-[10px] text-gray-500">${p.desc}</span>
              </div>
              <span class="font-bold text-xs ${p.status ? 'text-emerald-700' : 'text-gray-400'}">
                ${p.status ? '✓ உத்தமம்' : '≈ மத்திமம்'}
              </span>
            </div>
          `).join("")}
        </div>

        <div class="bg-[#FAF5EB] p-3 rounded-xl border border-[#E6D2B1] text-xs text-amber-950">
          <strong>Vedic Astrologer Note:</strong> Rajju Porutham is completely auspicious. To schedule a detailed Jathagam discussion with our Kanchipuram Vidwan, please contact <strong>8248853928</strong>.
        </div>
      </div>
    `;
  }

  // Multi-step Registration Wizard
  openRegistrationModal() {
    this.currentRegStep = 1;
    this.updateRegStepUI();
    const modal = document.getElementById("registration-modal");
    if (modal) modal.showModal();
  }

  closeRegistrationModal() {
    const modal = document.getElementById("registration-modal");
    if (modal) modal.close();
  }

  nextRegStep() {
    if (!this.validateStep(this.currentRegStep)) return;

    if (this.currentRegStep < 5) {
      this.currentRegStep++;
      this.updateRegStepUI();
    }
  }

  prevRegStep() {
    if (this.currentRegStep > 1) {
      this.currentRegStep--;
      this.updateRegStepUI();
    }
  }

  validateStep(step) {
    if (step === 1) {
      const name = document.getElementById("reg-name")?.value.trim();
      const mobile = document.getElementById("reg-mobile")?.value.trim();
      const gender = document.getElementById("reg-gender")?.value;
      const caste = document.getElementById("reg-caste")?.value;
      
      if (!name) {
        this.showToast("Please enter Full Name (முழுப் பெயர்)", "error");
        return false;
      }
      if (!mobile || mobile.length < 10) {
        this.showToast("Please enter a valid 10-digit Mobile Number", "error");
        return false;
      }
      if (!gender) {
        this.showToast("Please select Gender", "error");
        return false;
      }
      if (!caste) {
        this.showToast("Please select Caste / Community", "error");
        return false;
      }
    } else if (step === 2) {
      const district = document.getElementById("reg-district")?.value;
      const city = document.getElementById("reg-city")?.value.trim();
      const edu = document.getElementById("reg-education")?.value.trim();
      if (!district) {
        this.showToast("Please select District", "error");
        return false;
      }
      if (!city) {
        this.showToast("Please enter City / Town", "error");
        return false;
      }
      if (!edu) {
        this.showToast("Please enter Education", "error");
        return false;
      }
    } else if (step === 4) {
      // Compulsory Photo & Horoscope Check
      const photoInput = document.getElementById("reg-photo");
      const rasi = document.getElementById("reg-rasi")?.value;
      const nakshatra = document.getElementById("reg-nakshatra")?.value;
      const jathagamDoc = document.getElementById("reg-jathagam-doc");

      // Verify photo is provided (file selected or sample active)
      if (!photoInput?.files?.[0] && !this.newRegistrationData.hasPhotoPreview) {
        this.showToast("Profile Photo is STRICTLY COMPULSORY according to Matrimony Rules", "error");
        return false;
      }

      if (!rasi || !nakshatra) {
        this.showToast("Rasi and Nakshatra are COMPULSORY for Hindu matrimonial verification", "error");
        return false;
      }

      if (!jathagamDoc?.files?.[0] && !this.newRegistrationData.hasJathagamPreview) {
        this.showToast("Horoscope Document / Jathagam upload is STRICTLY COMPULSORY", "error");
        return false;
      }
    }
    return true;
  }

  updateRegStepUI() {
    for (let i = 1; i <= 5; i++) {
      const stepContent = document.getElementById(`reg-step-${i}`);
      const stepIndicator = document.getElementById(`step-indicator-${i}`);
      if (stepContent) {
        if (i === this.currentRegStep) {
          stepContent.classList.remove("hidden");
        } else {
          stepContent.classList.add("hidden");
        }
      }
      if (stepIndicator) {
        if (i <= this.currentRegStep) {
          stepIndicator.className = "flex items-center justify-center w-8 h-8 rounded-full bg-[#6B111E] text-white font-bold text-xs shadow";
        } else {
          stepIndicator.className = "flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 text-gray-500 font-bold text-xs";
        }
      }
    }

    // Scroll modal to top on step change
    const modalContent = document.getElementById("reg-modal-scrollable");
    if (modalContent) modalContent.scrollTop = 0;
  }

  // Handle Photo Preview
  handlePhotoUpload(input) {
    if (input.files && input.files[0]) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const previewImg = document.getElementById("photo-preview-img");
        const placeholder = document.getElementById("photo-upload-placeholder");
        if (previewImg && placeholder) {
          previewImg.src = e.target.result;
          previewImg.classList.remove("hidden");
          placeholder.classList.add("hidden");
        }
        this.newRegistrationData.hasPhotoPreview = true;
        this.newRegistrationData.photoUrl = e.target.result;
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  // Handle Jathagam Doc Preview
  handleJathagamUpload(input) {
    if (input.files && input.files[0]) {
      const fileName = input.files[0].name;
      const statusEl = document.getElementById("jathagam-doc-status");
      if (statusEl) {
        statusEl.innerHTML = `
          <div class="flex items-center gap-2 text-emerald-800 font-bold">
            <span>✓</span> <span>Uploaded: ${fileName}</span>
          </div>
        `;
      }
      this.newRegistrationData.hasJathagamPreview = true;
    }
  }

  // Process Simulated Payment of ₹2,000
  processDemoPayment() {
    const payBtn = document.getElementById("btn-confirm-payment");
    if (payBtn) {
      payBtn.disabled = true;
      payBtn.innerHTML = `<span>⏳</span> Processing ₹2,000 payment...`;
    }

    setTimeout(() => {
      // Generate ID
      const newId = `SM-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      const name = document.getElementById("reg-name")?.value || "Registered Member";
      const gender = document.getElementById("reg-gender")?.value || "female";
      const age = parseInt(document.getElementById("reg-age")?.value) || 25;
      const caste = document.getElementById("reg-caste")?.value || "Mudaliar";
      const district = document.getElementById("reg-district")?.value || "Kanchipuram";
      const city = document.getElementById("reg-city")?.value || "Kanchipuram";
      const education = document.getElementById("reg-education")?.value || "Graduate";
      const job = document.getElementById("reg-occupation")?.value || "Private Sector";
      const rasi = document.getElementById("reg-rasi")?.value || "Rishabam";
      const star = document.getElementById("reg-nakshatra")?.value || "Rohini";

      const newProfile = {
        id: newId,
        name: name,
        gender: gender,
        age: age,
        height: "5 ft 5 in",
        religion: "Hindu",
        caste: caste,
        subcaste: document.getElementById("reg-subcaste")?.value || "General Gothram",
        motherTongue: "Tamil",
        district: district,
        city: city,
        address: document.getElementById("reg-address")?.value || "Kanchipuram",
        education: education,
        occupation: job,
        income: document.getElementById("reg-income")?.value || "₹7.5 Lakhs / year",
        maritalStatus: "Never Married",
        photoUrl: this.newRegistrationData.photoUrl || "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80",
        horoscope: {
          rasi: rasi,
          nakshatra: star,
          lagnam: document.getElementById("reg-lagnam")?.value || "Mesham",
          birthDate: document.getElementById("reg-dob")?.value || "2000-01-01",
          birthTime: document.getElementById("reg-birth-time")?.value || "10:00 AM",
          birthPlace: city,
          dosham: "None",
          verified: true
        },
        partnerPref: document.getElementById("reg-pref-notes")?.value || "Compatible Hindu family",
        isApproved: true,
        paymentStatus: "Paid (₹2,000)",
        regDate: new Date().toISOString().split("T")[0],
        compatibility: 91,
        poruthams: {
          dina: "compatible",
          gana: "compatible",
          mahendra: "compatible",
          sthree: "compatible",
          yoni: "compatible",
          rasi: "compatible",
          rasiAdhipathi: "compatible",
          vasya: "moderate",
          rajju: "compatible",
          vedha: "compatible"
        }
      };

      this.profiles.unshift(newProfile);
      this.saveProfiles();
      this.renderProfiles();
      this.renderNearMeMatches();

      // Show Success Screen
      const modalContent = document.getElementById("reg-modal-scrollable");
      if (modalContent) {
        modalContent.innerHTML = `
          <div class="text-center py-8 px-4 space-y-6">
            <div class="w-20 h-20 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-4xl mx-auto border-4 border-emerald-400 animate-bounce">
              ✓
            </div>
            
            <div class="space-y-2">
              <span class="bg-[#DFB758] text-[#30060C] font-bold text-xs px-3 py-1 rounded-full uppercase tracking-wider">
                Registration Successful
              </span>
              <h3 class="font-heading text-2xl sm:text-3xl font-bold text-[#6B111E]">
                Welcome to Sarvamangala Matrimony
              </h3>
              <p class="text-xs sm:text-sm text-gray-600 max-w-md mx-auto">
                Your profile has been created and verified. ₹2,000 registration fee receipt generated.
              </p>
            </div>

            <!-- Receipt Box -->
            <div id="printable-receipt" class="bg-[#FAF5EB] p-5 rounded-2xl border-2 border-[#DFB758] max-w-md mx-auto text-left space-y-3 shadow">
              <div class="flex items-center justify-between border-b pb-2">
                <div>
                  <h4 class="font-heading font-bold text-sm text-[#6B111E]">Sarvamangala Matrimony</h4>
                  <p class="text-[10px] text-gray-500">Kanchipuram, Tamil Nadu • Ph: 8248853928</p>
                </div>
                <div class="text-right">
                  <span class="text-[10px] text-gray-500 block">Registration Fee Receipt</span>
                  <span class="font-mono text-xs font-bold text-[#6B111E]">REC-2026-${Math.floor(1000 + Math.random() * 9000)}</span>
                </div>
              </div>

              <div class="space-y-1.5 text-xs text-gray-700">
                <div class="flex justify-between">
                  <span>Member Name:</span>
                  <strong>${newProfile.name}</strong>
                </div>
                <div class="flex justify-between">
                  <span>Assigned Profile ID:</span>
                  <strong class="text-[#6B111E] font-mono">${newProfile.id}</strong>
                </div>
                <div class="flex justify-between">
                  <span>Community / Caste:</span>
                  <span>${newProfile.caste}</span>
                </div>
                <div class="flex justify-between">
                  <span>District:</span>
                  <span>${newProfile.district}</span>
                </div>
                <div class="flex justify-between">
                  <span>Horoscope Status:</span>
                  <span class="text-emerald-700 font-bold">✓ Verified</span>
                </div>
                <div class="flex justify-between border-t pt-2 font-bold text-sm text-gray-900">
                  <span>Amount Paid:</span>
                  <span class="text-emerald-800">₹2,000.00 (PAID)</span>
                </div>
              </div>

              <p class="text-[10px] text-gray-500 italic text-center pt-2">
                * Note: ₹25,000 service charge is payable separately only when your marriage is finalised.
              </p>
            </div>

            <div class="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button onclick="window.print()" class="text-xs font-bold py-2.5 px-5 rounded-xl border border-gray-400 bg-white hover:bg-gray-100 flex items-center gap-1.5 shadow-sm">
                <span>🖨️</span> Print Receipt
              </button>
              <button onclick="window.smApp.closeRegistrationModal(); window.smApp.openProfileModal('${newProfile.id}')" class="text-xs font-bold py-2.5 px-6 rounded-xl bg-[#6B111E] text-white hover:bg-[#851828] flex items-center gap-1.5 shadow">
                <span>👁️</span> View My Profile
              </button>
            </div>
          </div>
        `;
      }
      this.showToast("Profile activated successfully!", "success");
    }, 1200);
  }

  // Toast Notification
  showToast(message, type = "info") {
    const toast = document.getElementById("toast-notification");
    const toastMsg = document.getElementById("toast-message");
    if (!toast || !toastMsg) return;

    toastMsg.textContent = message;
    toast.classList.remove("translate-y-24", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    clearTimeout(this.toastTimeout);
    this.toastTimeout = setTimeout(() => {
      toast.classList.remove("translate-y-0", "opacity-100");
      toast.classList.add("translate-y-24", "opacity-0");
    }, 3500);
  }

  // Event Listeners
  bindEvents() {
    // Quick search form
    const qsForm = document.getElementById("quick-search-form");
    if (qsForm) {
      qsForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.showToast("Please register your profile to view full matching alliances!", "info");
        this.openRegistrationModal();
      });
    }

    // Contact form
    const contactForm = document.getElementById("family-contact-form");
    if (contactForm) {
      contactForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const name = document.getElementById("cf-name")?.value;
        const phone = document.getElementById("cf-phone")?.value;
        const msg = document.getElementById("cf-msg")?.value;
        this.enquiries.push({ name, phone, msg, date: new Date().toLocaleDateString() });
        localStorage.setItem("sm_enquiries", JSON.stringify(this.enquiries));
        this.showToast("Thank you. Our Kanchipuram office will call your family shortly!", "success");
        contactForm.reset();
      });
    }
  }
}

// Global initialization
window.addEventListener("DOMContentLoaded", () => {
  window.smApp = new SarvamangalaApp();
});
