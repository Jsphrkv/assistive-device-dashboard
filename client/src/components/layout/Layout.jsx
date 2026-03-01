// import React from "react";
// import Header from "./Header";
// import Navigation from "./Navigation";

// const Layout = ({
//   currentUser,
//   activeTab,
//   onTabChange,
//   onLogout,
//   children,
// }) => {
//   return (
//     <div className="min-h-screen bg-gray-50">
//       <Header currentUser={currentUser} onLogout={onLogout} />
//       {/* FIX: Pass currentUser so Navigation can render role-appropriate tabs */}
//       <Navigation
//         currentUser={currentUser}
//         activeTab={activeTab}
//         onTabChange={onTabChange}
//       />
//       <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
//     </div>
//   );
// };

// export default Layout;
import React, { useState, useEffect } from "react";
import Navigation from "./Navigation";
import Header from "./Header";

const DARK_CSS = `
  [data-theme="dark"] .bg-white {
    background-color: #1e1e2a !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 20px rgba(0,0,0,0.45), 0 1px 3px rgba(0,0,0,0.3) !important;
  }
  [data-theme="dark"] .bg-gray-50  { background-color: #191924 !important; }
  [data-theme="dark"] .bg-gray-100 { background-color: #252535 !important; }
  [data-theme="dark"] .bg-gray-200 { background-color: #2e2e40 !important; }
  [data-theme="dark"] .bg-gray-900 { background-color: #0c0c14 !important; }

  [data-theme="dark"] .shadow {
    box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 20px rgba(0,0,0,0.45), 0 1px 3px rgba(0,0,0,0.3) !important;
  }
  [data-theme="dark"] .shadow-lg {
    box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 12px 36px rgba(0,0,0,0.55), 0 4px 8px rgba(0,0,0,0.35) !important;
  }
  [data-theme="dark"] .shadow-xl,
  [data-theme="dark"] .shadow-2xl {
    box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 24px 56px rgba(0,0,0,0.65), 0 8px 16px rgba(0,0,0,0.45) !important;
  }

  [data-theme="dark"] .text-gray-900 { color: #eeeef2 !important; }
  [data-theme="dark"] .text-gray-800 { color: #d8d8e4 !important; }
  [data-theme="dark"] .text-gray-700 { color: #bdbdce !important; }
  [data-theme="dark"] .text-gray-600 { color: #9898ac !important; }
  [data-theme="dark"] .text-gray-500 { color: #78788c !important; }
  [data-theme="dark"] .text-gray-400 { color: #58586c !important; }
  [data-theme="dark"] .text-gray-300 { color: #42425a !important; }

  [data-theme="dark"] .border-gray-100 { border-color: #252535 !important; }
  [data-theme="dark"] .border-gray-200 { border-color: #2e2e40 !important; }
  [data-theme="dark"] .border-gray-300 { border-color: #3a3a50 !important; }
  [data-theme="dark"] .divide-gray-200 > * + * { border-color: #2a2a38 !important; }

  [data-theme="dark"] .hover\\:bg-gray-50:hover  { background-color: #22223a !important; }
  [data-theme="dark"] .hover\\:bg-gray-100:hover { background-color: #282840 !important; }
  [data-theme="dark"] .hover\\:bg-gray-200:hover { background-color: #30304a !important; }

  [data-theme="dark"] input[type="text"],
  [data-theme="dark"] input[type="password"],
  [data-theme="dark"] input[type="email"],
  [data-theme="dark"] input[type="number"],
  [data-theme="dark"] select,
  [data-theme="dark"] textarea {
    background-color: #16162a !important;
    color: #dddde8 !important;
    border-color: #3a3a50 !important;
  }
  [data-theme="dark"] input[type="text"]:focus,
  [data-theme="dark"] input[type="password"]:focus,
  [data-theme="dark"] input[type="email"]:focus,
  [data-theme="dark"] select:focus,
  [data-theme="dark"] textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
    outline: none !important;
  }
  [data-theme="dark"] input::placeholder,
  [data-theme="dark"] textarea::placeholder { color: #52526a !important; }

  [data-theme="dark"] thead,
  [data-theme="dark"] .bg-gray-50.sticky { background-color: #191924 !important; }

  [data-theme="dark"] .bg-blue-50   { background: linear-gradient(135deg,#131a2e,#162036) !important; border-color: #22346a !important; }
  [data-theme="dark"] .bg-red-50    { background: linear-gradient(135deg,#220d0d,#2c1010) !important; border-color: #5a1c1c !important; }
  [data-theme="dark"] .bg-green-50  { background: linear-gradient(135deg,#0d1f12,#102618) !important; border-color: #1e4428 !important; }
  [data-theme="dark"] .bg-yellow-50 { background: linear-gradient(135deg,#201900,#281f00) !important; border-color: #4a3c00 !important; }
  [data-theme="dark"] .bg-orange-50 { background: linear-gradient(135deg,#201200,#281700) !important; border-color: #553000 !important; }
  [data-theme="dark"] .bg-purple-50 { background: linear-gradient(135deg,#18102e,#1e1438) !important; border-color: #42207a !important; }
  [data-theme="dark"] .bg-amber-50  { background: linear-gradient(135deg,#1e1600,#261c00) !important; border-color: #4a3800 !important; }

  [data-theme="dark"] .border-blue-200   { border-color: #22346a !important; }
  [data-theme="dark"] .border-red-200    { border-color: #5a1c1c !important; }
  [data-theme="dark"] .border-green-200  { border-color: #1e4428 !important; }
  [data-theme="dark"] .border-yellow-200 { border-color: #4a3c00 !important; }
  [data-theme="dark"] .border-orange-200 { border-color: #553000 !important; }
  [data-theme="dark"] .border-purple-200 { border-color: #42207a !important; }
  [data-theme="dark"] .border-amber-200  { border-color: #4a3800 !important; }

  [data-theme="dark"] .bg-blue-100   { background-color: #1c2e55 !important; }
  [data-theme="dark"] .bg-red-100    { background-color: #441818 !important; }
  [data-theme="dark"] .bg-green-100  { background-color: #1a3825 !important; }
  [data-theme="dark"] .bg-yellow-100 { background-color: #3e3400 !important; }
  [data-theme="dark"] .bg-orange-100 { background-color: #442500 !important; }
  [data-theme="dark"] .bg-purple-100 { background-color: #2e1c58 !important; }
  [data-theme="dark"] .bg-amber-100  { background-color: #3c2c00 !important; }

  [data-theme="dark"] .text-blue-800   { color: #93c5fd !important; }
  [data-theme="dark"] .text-blue-700   { color: #60a5fa !important; }
  [data-theme="dark"] .text-blue-600   { color: #3b82f6 !important; }
  [data-theme="dark"] .text-red-800    { color: #fca5a5 !important; }
  [data-theme="dark"] .text-red-700    { color: #f87171 !important; }
  [data-theme="dark"] .text-red-600    { color: #f87171 !important; }
  [data-theme="dark"] .text-red-500    { color: #ef4444 !important; }
  [data-theme="dark"] .text-green-800  { color: #86efac !important; }
  [data-theme="dark"] .text-green-700  { color: #4ade80 !important; }
  [data-theme="dark"] .text-green-600  { color: #22c55e !important; }
  [data-theme="dark"] .text-yellow-800 { color: #fde68a !important; }
  [data-theme="dark"] .text-yellow-700 { color: #fbbf24 !important; }
  [data-theme="dark"] .text-yellow-600 { color: #f59e0b !important; }
  [data-theme="dark"] .text-orange-800 { color: #fdba74 !important; }
  [data-theme="dark"] .text-orange-700 { color: #fb923c !important; }
  [data-theme="dark"] .text-orange-600 { color: #f97316 !important; }
  [data-theme="dark"] .text-orange-500 { color: #f97316 !important; }
  [data-theme="dark"] .text-purple-800 { color: #d8b4fe !important; }
  [data-theme="dark"] .text-purple-700 { color: #c084fc !important; }
  [data-theme="dark"] .text-purple-600 { color: #a855f7 !important; }
  [data-theme="dark"] .text-amber-800  { color: #fde68a !important; }
  [data-theme="dark"] .text-amber-700  { color: #fcd34d !important; }
  [data-theme="dark"] .text-amber-600  { color: #f59e0b !important; }

  [data-theme="dark"] .bg-gray-200.rounded-full,
  [data-theme="dark"] .bg-gray-200.rounded-full.h-2 { background-color: #2e2e40 !important; }

  [data-theme="dark"] .recharts-text,
  [data-theme="dark"] .recharts-cartesian-axis-tick-value { fill: #78788c !important; }
  [data-theme="dark"] .recharts-cartesian-grid line { stroke: #2e2e40 !important; }
  [data-theme="dark"] .recharts-tooltip-wrapper .recharts-default-tooltip {
    background-color: #22223a !important;
    border-color: #3a3a50 !important;
    color: #dddde8 !important;
  }
  [data-theme="dark"] .recharts-legend-item-text { color: #9898ac !important; }

  [data-theme="dark"] .bg-white.rounded-lg.shadow-xl,
  [data-theme="dark"] .bg-white.rounded-lg.shadow-2xl,
  [data-theme="dark"] .bg-white.rounded-xl.shadow-2xl {
    background-color: #1e1e2a !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
  }

  [data-theme="dark"] ::-webkit-scrollbar              { width: 5px; height: 5px; }
  [data-theme="dark"] ::-webkit-scrollbar-track        { background: transparent; }
  [data-theme="dark"] ::-webkit-scrollbar-thumb        { background: #3a3a52; border-radius: 4px; }
  [data-theme="dark"] ::-webkit-scrollbar-thumb:hover  { background: #5a5a78; }

  [data-theme="dark"] button.border,
  [data-theme="dark"] button.border-gray-300 {
    border-color: #4a4a62 !important;
    color: #bdbdce !important;
    background-color: transparent !important;
  }
  [data-theme="dark"] button.border:hover,
  [data-theme="dark"] button.border-gray-300:hover {
    background-color: #252538 !important;
    border-color: #5a5a78 !important;
    color: #eeeef2 !important;
  }
  [data-theme="dark"] button.border:disabled,
  [data-theme="dark"] button.border-gray-300:disabled {
    border-color: #36364a !important;
    color: #58586c !important;
    opacity: 0.6 !important;
  }
  [data-theme="dark"] button.bg-blue-600,
  [data-theme="dark"] button.bg-red-600,
  [data-theme="dark"] button.bg-yellow-600,
  [data-theme="dark"] button.bg-purple-600,
  [data-theme="dark"] button.bg-green-600 { color: #ffffff !important; border: none !important; }

  [data-theme="dark"] .opacity-50 { opacity: 0.45 !important; }
  [data-theme="dark"] .bg-green-500 { background-color: #22c55e !important; }
  [data-theme="dark"] .bg-red-500   { background-color: #ef4444 !important; }
  [data-theme="dark"] .bg-red-500.text-white,
  [data-theme="dark"] .bg-yellow-500.text-white,
  [data-theme="dark"] .bg-blue-500.text-white,
  [data-theme="dark"] .bg-green-500.text-white { border: none !important; }
`;

const STYLE_ID = "app-dark-mode-overrides";

function injectDarkCSS(dark) {
  let el = document.getElementById(STYLE_ID);
  if (!el) {
    el = document.createElement("style");
    el.id = STYLE_ID;
    document.head.appendChild(el);
  }
  el.textContent = dark ? DARK_CSS : "";
}

const MOBILE_BREAKPOINT = 768;

const Layout = ({
  currentUser,
  activeTab,
  onTabChange,
  onLogout,
  children,
}) => {
  const [dark, setDark] = useState(
    () => localStorage.getItem("theme") === "dark",
  );
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(
    () => window.innerWidth < MOBILE_BREAKPOINT,
  );

  useEffect(() => {
    const onResize = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
      if (!mobile) setCollapsed(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    injectDarkCSS(dark);
  }, [dark]);

  useEffect(() => {
    injectDarkCSS(dark);
    return () => {
      const el = document.getElementById(STYLE_ID);
      if (el) el.textContent = "";
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  // CHANGED: 310→260 expanded, 80→52 collapsed (matches Claude sidebar proportions)
  const sidebarWidth = isMobile ? 0 : collapsed ? 52 : 260;

  const theme = {
    dark,
    pageBg: dark ? "#13131a" : "#f3f4f6",
    headerBg: dark ? "#1a1a26" : "#ffffff",
    headerBorder: dark ? "#2a2a3a" : "#e5e7eb",
    headerText: dark ? "#eeeef2" : "#111827",
    headerSub: dark ? "#78788c" : "#6b7280",
    cardBg: dark ? "#1e1e2a" : "#ffffff",
    cardBorder: dark ? "#2e2e42" : "#e5e7eb",
    textPrimary: dark ? "#eeeef2" : "#111827",
    textMuted: dark ? "#78788c" : "#6b7280",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: theme.pageBg,
        fontFamily: "'Inter', sans-serif",
        transition: "background .2s",
      }}
    >
      {/* Fixed header — full width */}
      <div style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50 }}>
        <Header
          theme={theme}
          onToggleDark={toggleDark}
          isMobile={isMobile}
          onOpenMobileMenu={() => {
            if (typeof window.__openMobileNav === "function")
              window.__openMobileNav();
          }}
        />
      </div>

      {/* Body — CHANGED: paddingTop 72→56 to match new header height */}
      <div style={{ display: "flex", paddingTop: 56 }}>
        <Navigation
          currentUser={currentUser}
          activeTab={activeTab}
          onTabChange={onTabChange}
          onLogout={onLogout}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(!collapsed)}
          theme={theme}
          sidebarWidth={sidebarWidth}
          isMobile={isMobile}
        />

        {/* Main content */}
        <div
          style={{
            flex: 1,
            marginLeft: sidebarWidth,
            transition: "margin-left .3s",
            padding: isMobile ? "1rem" : "1.75rem 2rem",
            minWidth: 0,
            minHeight: "calc(100vh - 56px)",
            boxSizing: "border-box",
            width: "100%",
          }}
        >
          <div
            data-theme={dark ? "dark" : "light"}
            style={{ maxWidth: 1200, margin: "0 auto" }}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Layout;
