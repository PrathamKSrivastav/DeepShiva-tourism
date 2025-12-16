import React from "react";
import { useTheme } from "./context/ThemeContext";
import { Link, useOutletContext } from "react-router-dom";

const nationalHelplines = [
  {
    name: "All-India Emergency",
    number: "112",
    desc: "Unified response for Police, Fire, and Medical emergencies",
  },
  {
    name: "Ambulance",
    number: "108",
    desc: "Emergency medical services & patient transport",
  },
  {
    name: "Women Helpline",
    number: "1091 / 181",
    desc: "Women in distress, domestic abuse, and safety",
  },
  {
    name: "Tourism Helpline",
    number: "1363 / 1800-11-1363",
    desc: "24x7 multi-lingual tourist support",
  },
  {
    name: "Railway Helpline",
    number: "139",
    desc: "Train safety, security, and general enquiry",
  },
  {
    name: "Disaster Management",
    number: "1078",
    desc: "NDMA National Control Room",
  },
  {
    name: "Cyber Crime",
    number: "1930",
    desc: "National Cyber Crime Reporting Portal",
  },
];

const stateHelplines = [
  // --- NORTH INDIA ---
  {
    state: "Delhi (NCT)",
    police: "112",
    ambulance: "102 / 108",
    disaster: "1077",
    tourism: "1800-11-1363",
  },
  {
    state: "Haryana",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1363",
  },
  {
    state: "Himachal Pradesh",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "0177-2625924",
  },
  {
    state: "Jammu & Kashmir",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Ladakh",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Punjab",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "0172-2702955",
  },
  {
    state: "Rajasthan",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Uttar Pradesh",
    police: "112",
    ambulance: "108 / 102",
    disaster: "1070",
    tourism: "1800-180-2877",
  },
  {
    state: "Uttarakhand",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1364",
  },

  // --- WEST INDIA ---
  {
    state: "Goa",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1363",
  },
  {
    state: "Gujarat",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1800-203-1111",
  },
  {
    state: "Maharashtra",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1800-229-929",
  },
  {
    state: "Dadra & Nagar Haveli and Daman & Diu",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1363",
  },

  // --- SOUTH INDIA ---
  {
    state: "Andhra Pradesh",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070 / 1800-425-0101",
    tourism: "1363",
  },
  {
    state: "Karnataka",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1800-425-4646",
  },
  {
    state: "Kerala",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1800-425-4747",
  },
  {
    state: "Tamil Nadu",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070",
    tourism: "1800-425-31111",
  },
  {
    state: "Telangana",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070",
    tourism: "1800-425-46464",
  },
  {
    state: "Puducherry",
    police: "112",
    ambulance: "108",
    disaster: "1070 / 1077",
    tourism: "1363",
  },
  {
    state: "Lakshadweep",
    police: "112",
    ambulance: "102",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Andaman & Nicobar Islands",
    police: "112 / 100",
    ambulance: "102",
    disaster: "1070 / 1077",
    tourism: "03192-232694",
  },

  // --- EAST INDIA ---
  {
    state: "Bihar",
    police: "112",
    ambulance: "102 / 108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Jharkhand",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Odisha",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "West Bengal",
    police: "112 / 100",
    ambulance: "102",
    disaster: "1070",
    tourism: "1800-212-1655",
  },

  // --- CENTRAL INDIA ---
  {
    state: "Chhattisgarh",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1800-102-6415",
  },
  {
    state: "Madhya Pradesh",
    police: "112 / 100",
    ambulance: "108",
    disaster: "1070 / 1079",
    tourism: "1363",
  },

  // --- NORTH EAST INDIA ---
  {
    state: "Arunachal Pradesh",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Assam",
    police: "112",
    ambulance: "108 / 102",
    disaster: "1070 / 1079",
    tourism: "1363",
  },
  {
    state: "Manipur",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Meghalaya",
    police: "112",
    ambulance: "108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Mizoram",
    police: "112",
    ambulance: "108 / 102",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Nagaland",
    police: "112",
    ambulance: "102 / 108",
    disaster: "1070",
    tourism: "1363",
  },
  {
    state: "Sikkim",
    police: "112",
    ambulance: "102 / 108",
    disaster: "1070 / 1111",
    tourism: "1363",
  },
  {
    state: "Tripura",
    police: "112",
    ambulance: "102 / 108",
    disaster: "1070",
    tourism: "1363",
  },
];

export default function Emergency() {
  const { darkMode } = useTheme();
  const handleDownload = () => {
    window.print();
  };

  return (
    <div
      className={`min-h-screen ${
        darkMode
          ? "bg-dark-bg text-slate-100"
          : "bg-gradient-to-br from-blue-50 to-indigo-100 text-gray-900"
      }`}
    >
      {/* Header */}
      <header
        className={`border-b ${
          darkMode
            ? "bg-dark-surface border-dark-border"
            : "bg-white border-gray-200"
        }`}
      >
        <div className="max-w-6xl mx-auto px-4 py-6 lg:py-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p
                className={`text-sm uppercase tracking-[0.2em] ${
                  darkMode ? "text-indigo-200" : "text-indigo-600"
                }`}
              >
                Emergency Resources
              </p>
              <h1
                className={`text-3xl lg:text-4xl font-semibold mt-2 ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}
              >
                Helplines & Quick Contacts
              </h1>
              <p
                className={`mt-2 text-sm lg:text-base ${
                  darkMode ? "text-indigo-100/90" : "text-indigo-600"
                }`}
              >
                Keep these numbers handy while traveling. Call 112 for any
                life-threatening emergency.
              </p>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <button
                onClick={handleDownload}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium shadow-md shadow-emerald-500/30 transition"
                title="Download contacts as PDF"
              >
                📥 PDF
              </button>
              <Link
                to="/"
                className={`px-4 py-2 rounded-lg border transition ${
                  darkMode
                    ? "border-dark-border text-slate-100 hover:bg-dark-elev"
                    : "border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                ← Back
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-10 lg:py-14">
        <section className="grid lg:grid-cols-3 gap-6">
          {/* National Helplines */}
          <div
            className={`lg:col-span-1 rounded-2xl p-6 border shadow-xl ${
              darkMode
                ? "bg-dark-surface/50 border-dark-border"
                : "bg-white/40 border-white/40"
            }`}
          >
            <h2
              className={`text-xl font-semibold mb-4 ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              National Helplines
            </h2>
            <div className="space-y-4">
              {nationalHelplines.map((item) => (
                <div
                  key={item.name}
                  className={`p-4 rounded-xl border ${
                    darkMode
                      ? "bg-dark-elev/40 border-dark-border"
                      : "bg-white/50 border-white/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-sm font-medium ${
                        darkMode ? "text-slate-100" : "text-gray-700"
                      }`}
                    >
                      {item.name}
                    </span>
                    <span className="text-lg font-semibold text-emerald-500">
                      {item.number}
                    </span>
                  </div>
                  <p
                    className={`text-xs mt-2 leading-relaxed ${
                      darkMode ? "text-slate-300" : "text-gray-600"
                    }`}
                  >
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* State-wise Helplines */}
          <div
            className={`lg:col-span-2 rounded-2xl p-6 border shadow-xl ${
              darkMode
                ? "bg-dark-surface/50 border-dark-border"
                : "bg-white/40 border-white/40"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h2
                className={`text-xl font-semibold ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}
              >
                State-wise Quick Dial
              </h2>
              <span
                className={`text-xs ${
                  darkMode ? "text-slate-400" : "text-gray-600"
                }`}
              >
                Police · Ambulance · Disaster · Tourism
              </span>
            </div>
            <div
              className={`overflow-hidden rounded-xl border ${
                darkMode
                  ? "bg-dark-elev/40 border-dark-border"
                  : "bg-white/50 border-white/60"
              }`}
            >
              <div
                className={`grid grid-cols-5 text-xs uppercase tracking-wide font-semibold py-2 px-3 border-b ${
                  darkMode
                    ? "bg-dark-elev border-dark-border text-slate-400"
                    : "bg-gray-100 border-white/60 text-gray-600"
                }`}
              >
                <span>State</span>
                <span>Police</span>
                <span>Ambulance</span>
                <span>Disaster</span>
                <span>Tourism</span>
              </div>
              <div
                className={`divide-y ${
                  darkMode ? "divide-dark-border" : "divide-white/60"
                }`}
              >
                {stateHelplines.map((row) => (
                  <div
                    key={row.state}
                    className={`grid grid-cols-5 text-sm px-3 py-3 transition ${
                      darkMode
                        ? "text-slate-100 hover:bg-dark-elev/30"
                        : "text-gray-800 hover:bg-white/60"
                    }`}
                  >
                    <span className="font-medium">{row.state}</span>
                    <span>{row.police}</span>
                    <span>{row.ambulance}</span>
                    <span>{row.disaster}</span>
                    <span>{row.tourism}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tips */}
            <div className="mt-6 grid md:grid-cols-2 gap-4">
              <div
                className={`p-4 rounded-xl border ${
                  darkMode
                    ? "bg-emerald-900/20 border-emerald-800/30"
                    : "bg-emerald-50/60 border-emerald-200/40"
                }`}
              >
                <p
                  className={`text-sm font-semibold ${
                    darkMode ? "text-emerald-300" : "text-emerald-700"
                  }`}
                >
                  Travel Tip
                </p>
                <p
                  className={`text-xs mt-2 leading-relaxed ${
                    darkMode ? "text-slate-300" : "text-gray-700"
                  }`}
                >
                  Save key numbers to your phone and keep a small card in your
                  wallet with your blood group and an emergency contact.
                </p>
              </div>
              <div
                className={`p-4 rounded-xl border ${
                  darkMode
                    ? "bg-indigo-900/20 border-indigo-800/30"
                    : "bg-indigo-50/60 border-indigo-200/40"
                }`}
              >
                <p
                  className={`text-sm font-semibold ${
                    darkMode ? "text-indigo-300" : "text-indigo-700"
                  }`}
                >
                  Safety Note
                </p>
                <p
                  className={`text-xs mt-2 leading-relaxed ${
                    darkMode ? "text-slate-300" : "text-gray-700"
                  }`}
                >
                  In the hills, network can be patchy. Share your itinerary with
                  a trusted person and download offline maps.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
