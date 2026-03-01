// import React, { useState, useEffect } from "react";
// import {
//   Activity,
//   AlertTriangle,
//   Camera,
//   Settings,
//   Info,
//   Clock,
//   Menu,
//   X,
//   Shield,
//   BarChart2,
//   Users,
//   Radio,
//   HeartPulse,
// } from "lucide-react";

// // Regular user tabs — unchanged from original
// const USER_TABS = [
//   { id: "dashboard", label: "Dashboard", icon: Activity },
//   { id: "logs", label: "Detection Logs", icon: AlertTriangle },
//   { id: "statistics", label: "Statistics", icon: Activity },
//   { id: "mlhistory", label: "ML History", icon: Clock },
//   { id: "camera", label: "Live Camera", icon: Camera },
//   { id: "settings", label: "Settings", icon: Settings },
//   { id: "device", label: "My Device", icon: Info },
// ];

// // Admin-only tabs — replaces the full nav for admin users
// const ADMIN_TABS = [
//   { id: "admin-health", label: "System Health", icon: HeartPulse },
//   { id: "admin-logs", label: "Detection Logs", icon: AlertTriangle },
//   { id: "admin-analytics", label: "ML Analytics", icon: BarChart2 },
//   { id: "admin-users", label: "Users & Devices", icon: Users },
//   { id: "admin-feed", label: "Live Feed", icon: Radio },
// ];

// const Navigation = ({ currentUser, activeTab, onTabChange }) => {
//   const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
//   const [isMobile, setIsMobile] = useState(false);

//   // Choose tab set based on role
//   const isAdmin = currentUser?.role === "admin";
//   const tabs = isAdmin ? ADMIN_TABS : USER_TABS;

//   useEffect(() => {
//     const checkMobile = () => {
//       setIsMobile(window.innerWidth < 768);
//       if (window.innerWidth >= 768) {
//         setIsMobileNavOpen(false);
//       }
//     };
//     checkMobile();
//     window.addEventListener("resize", checkMobile);
//     return () => window.removeEventListener("resize", checkMobile);
//   }, []);

//   const handleTabChange = (tabId) => {
//     onTabChange(tabId);
//     setIsMobileNavOpen(false);
//   };

//   const activeTabObj = tabs.find((t) => t.id === activeTab) || tabs[0];

//   return (
//     <>
//       <nav
//         className={`bg-white border-b border-gray-200 ${isAdmin ? "border-t-2 border-t-purple-500" : ""}`}
//       >
//         <div className="max-w-7xl mx-auto px-4">
//           {/* Admin mode badge */}
//           {isAdmin && (
//             <div className="flex items-center gap-2 py-1.5 border-b border-purple-100">
//               <Shield className="w-3.5 h-3.5 text-purple-600" />
//               <span className="text-xs font-semibold text-purple-700 tracking-wide uppercase">
//                 Admin Panel
//               </span>
//             </div>
//           )}

//           {/* Mobile: Burger + Active Tab */}
//           <div className="md:hidden flex items-center justify-between py-3">
//             <button
//               onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
//               className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
//             >
//               {isMobileNavOpen ? (
//                 <X className="w-5 h-5" />
//               ) : (
//                 <Menu className="w-5 h-5" />
//               )}
//               <span className="font-medium">Menu</span>
//             </button>

//             <div
//               className={`flex items-center gap-2 font-medium ${isAdmin ? "text-purple-600" : "text-blue-600"}`}
//             >
//               {React.createElement(activeTabObj.icon, { className: "w-4 h-4" })}
//               <span className="text-sm">{activeTabObj.label}</span>
//             </div>
//           </div>

//           {/* Desktop: Horizontal Tabs */}
//           <div className="hidden md:flex gap-1 overflow-x-auto">
//             {tabs.map((tab) => {
//               const Icon = tab.icon;
//               const isActive = activeTab === tab.id;
//               return (
//                 <button
//                   key={tab.id}
//                   onClick={() => onTabChange(tab.id)}
//                   className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all whitespace-nowrap ${
//                     isActive
//                       ? isAdmin
//                         ? "border-purple-600 text-purple-600"
//                         : "border-blue-600 text-blue-600"
//                       : "border-transparent text-gray-600 hover:text-gray-900"
//                   }`}
//                 >
//                   <Icon className="w-4 h-4" />
//                   {tab.label}
//                 </button>
//               );
//             })}
//           </div>
//         </div>
//       </nav>

//       {/* Mobile: Slide-in Menu */}
//       {isMobile && (
//         <>
//           <div
//             className={`fixed inset-0 bg-black transition-opacity duration-300 z-40 ${
//               isMobileNavOpen
//                 ? "opacity-50 pointer-events-auto"
//                 : "opacity-0 pointer-events-none"
//             }`}
//             onClick={() => setIsMobileNavOpen(false)}
//           />

//           <div
//             className={`fixed top-0 left-0 h-full w-72 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 ${
//               isMobileNavOpen ? "translate-x-0" : "-translate-x-full"
//             }`}
//           >
//             <div className="p-6">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h2 className="text-lg font-bold text-gray-900">Menu</h2>
//                   {isAdmin && (
//                     <span className="inline-flex items-center gap-1 text-xs text-purple-600 font-semibold mt-0.5">
//                       <Shield className="w-3 h-3" /> Admin Panel
//                     </span>
//                   )}
//                 </div>
//                 <button
//                   onClick={() => setIsMobileNavOpen(false)}
//                   className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
//                 >
//                   <X className="w-5 h-5" />
//                 </button>
//               </div>

//               <div className="space-y-2">
//                 {tabs.map((tab) => {
//                   const Icon = tab.icon;
//                   const isActive = activeTab === tab.id;
//                   return (
//                     <button
//                       key={tab.id}
//                       onClick={() => handleTabChange(tab.id)}
//                       className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
//                         isActive
//                           ? isAdmin
//                             ? "bg-purple-600 text-white shadow-md"
//                             : "bg-blue-600 text-white shadow-md"
//                           : "text-gray-700 hover:bg-gray-100"
//                       }`}
//                     >
//                       <Icon className="w-5 h-5" />
//                       <span className="font-medium">{tab.label}</span>
//                     </button>
//                   );
//                 })}
//               </div>
//             </div>
//           </div>
//         </>
//       )}
//     </>
//   );
// };

// export default Navigation;
import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  Settings,
  Info,
  Clock,
  Shield,
  BarChart2,
  Users,
  Radio,
  HeartPulse,
  LogOut,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";

const USER_TABS = [
  { id: "dashboard", label: "Dashboard", icon: Activity },
  { id: "logs", label: "Detection Logs", icon: AlertTriangle },
  { id: "statistics", label: "Statistics", icon: Activity },
  { id: "mlhistory", label: "ML History", icon: Clock },
  { id: "camera", label: "Live Camera", icon: Camera },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "device", label: "My Device", icon: Info },
];

const ADMIN_TABS = [
  { id: "admin-health", label: "System Health", icon: HeartPulse },
  { id: "admin-logs", label: "Detection Logs", icon: AlertTriangle },
  { id: "admin-analytics", label: "ML Analytics", icon: BarChart2 },
  { id: "admin-users", label: "Users & Devices", icon: Users },
  { id: "admin-feed", label: "Live Feed", icon: Radio },
];

const S = {
  light: {
    bg: "#ffffff",
    border: "#e5e7eb",
    activeText: "#7c3aed",
    activeBg: "#f3effe",
    hoverBg: "#f9f7ff",
    text: "#374151",
    muted: "#9ca3af",
    logoutHover: "#fef2f2",
    logoutText: "#ef4444",
    divider: "#f0f0f0",
    badgeBg: "#f5f3ff",
    badgeText: "#7c3aed",
    userCardBg: "#f9fafb",
    collapseBtn: "#f3f4f6",
    collapseBorder: "#e5e7eb",
    collapseIcon: "#6b7280",
    menuLabel: "#9ca3af",
    overlay: "rgba(0,0,0,0.35)",
    modalBg: "#ffffff",
    modalBorder: "#e5e7eb",
    modalShadow: "0 20px 60px rgba(0,0,0,0.18), 0 4px 16px rgba(0,0,0,0.1)",
    modalTitle: "#111827",
    modalBody: "#6b7280",
    cancelBg: "#f3f4f6",
    cancelBorder: "#e5e7eb",
    cancelText: "#374151",
    cancelHover: "#e5e7eb",
    confirmBg: "#ef4444",
    confirmHover: "#dc2626",
    confirmText: "#ffffff",
    backdropBg: "rgba(0,0,0,0.4)",
  },
  dark: {
    bg: "#1a1a26",
    border: "#2a2a3a",
    activeText: "#c084fc",
    activeBg: "#2a1a45",
    hoverBg: "#222232",
    text: "#bdbdce",
    muted: "#58586c",
    logoutHover: "#2a1520",
    logoutText: "#f87171",
    divider: "#242434",
    badgeBg: "#2a1a45",
    badgeText: "#c084fc",
    userCardBg: "#13131a",
    collapseBtn: "#252535",
    collapseBorder: "#3a3a50",
    collapseIcon: "#78788c",
    menuLabel: "#58586c",
    overlay: "rgba(0,0,0,0.6)",
    modalBg: "#1e1e2e",
    modalBorder: "#3a3a50",
    modalShadow: "0 20px 60px rgba(0,0,0,0.55), 0 4px 16px rgba(0,0,0,0.4)",
    modalTitle: "#eeeef2",
    modalBody: "#78788c",
    cancelBg: "#252535",
    cancelBorder: "#3a3a50",
    cancelText: "#bdbdce",
    cancelHover: "#2e2e42",
    confirmBg: "#ef4444",
    confirmHover: "#dc2626",
    confirmText: "#ffffff",
    backdropBg: "rgba(0,0,0,0.65)",
  },
};

const btnBase = {
  width: 28,
  height: 28,
  borderRadius: 6,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
  flexShrink: 0,
};

// ── Logout Confirmation Modal ────────────────────────────────────────────────
const LogoutModal = ({ s, onCancel, onConfirm }) => {
  const [cancelHover, setCancelHover] = useState(false);
  const [confirmHover, setConfirmHover] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onCancel]);

  return (
    <div
      onClick={onCancel}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        background: s.backdropBg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        animation: "fadeIn .15s ease-out",
      }}
    >
      <style>{`@keyframes fadeIn{from{opacity:0}to{opacity:1}} @keyframes popIn{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:scale(1)}}`}</style>

      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: s.modalBg,
          border: `1px solid ${s.modalBorder}`,
          borderRadius: 14,
          boxShadow: s.modalShadow,
          padding: "1.75rem 2rem",
          width: "100%",
          maxWidth: 360,
          margin: "0 1rem",
          animation: "popIn .18s ease-out",
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background: "rgba(239,68,68,.12)",
            border: "1px solid rgba(239,68,68,.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "1.1rem",
          }}
        >
          <LogOut size={22} color="#ef4444" />
        </div>

        <h3
          style={{
            fontWeight: 700,
            fontSize: "1.05rem",
            color: s.modalTitle,
            margin: "0 0 .45rem",
            fontFamily: "inherit",
          }}
        >
          Sign out?
        </h3>
        <p
          style={{
            fontSize: ".875rem",
            color: s.modalBody,
            margin: "0 0 1.5rem",
            lineHeight: 1.55,
            fontFamily: "inherit",
          }}
        >
          You'll be returned to the login screen. Any unsaved changes will be
          lost.
        </p>

        <div style={{ display: "flex", gap: ".65rem" }}>
          <button
            onClick={onCancel}
            onMouseEnter={() => setCancelHover(true)}
            onMouseLeave={() => setCancelHover(false)}
            style={{
              flex: 1,
              padding: ".65rem",
              borderRadius: 8,
              border: `1px solid ${s.cancelBorder}`,
              background: cancelHover ? s.cancelHover : s.cancelBg,
              color: s.cancelText,
              fontWeight: 500,
              fontSize: ".875rem",
              cursor: "pointer",
              transition: "background .15s",
              fontFamily: "inherit",
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            onMouseEnter={() => setConfirmHover(true)}
            onMouseLeave={() => setConfirmHover(false)}
            style={{
              flex: 1,
              padding: ".65rem",
              borderRadius: 8,
              border: "none",
              background: confirmHover ? s.confirmHover : s.confirmBg,
              color: s.confirmText,
              fontWeight: 600,
              fontSize: ".875rem",
              cursor: "pointer",
              transition: "background .15s",
              fontFamily: "inherit",
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

// ── Sidebar Panel ────────────────────────────────────────────────────────────
const SidebarPanel = ({
  s,
  theme,
  tabs,
  isAdmin,
  activeTab,
  onTabChange,
  onLogoutClick,
  currentUser,
  collapsed,
  onToggleCollapse,
  isMobilePanel,
  onClose,
  width,
}) => (
  <div
    style={{
      width,
      height: "calc(100vh - 56px)",
      background: s.bg,
      borderRight: `1px solid ${s.border}`,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      transition: "width .3s",
    }}
  >
    {/* Top bar */}
    <div
      style={{
        height: 52,
        display: "flex",
        alignItems: "center",
        justifyContent:
          collapsed && !isMobilePanel ? "center" : "space-between",
        padding: "0 0.75rem",
        borderBottom: `1px solid ${s.divider}`,
        flexShrink: 0,
      }}
    >
      {(!collapsed || isMobilePanel) && (
        <span
          style={{
            fontSize: "0.8rem",
            fontWeight: 700,
            letterSpacing: "0.12em",
            color: s.menuLabel,
            textTransform: "uppercase",
            userSelect: "none",
            paddingLeft: "0.75rem",
          }}
        >
          Menu
        </span>
      )}
      {isMobilePanel ? (
        <button
          onClick={onClose}
          style={{
            ...btnBase,
            background: s.collapseBtn,
            border: `1px solid ${s.collapseBorder}`,
          }}
        >
          <X size={15} color={s.collapseIcon} />
        </button>
      ) : (
        <button
          onClick={onToggleCollapse}
          title={collapsed ? "Expand" : "Collapse"}
          style={{
            ...btnBase,
            background: s.collapseBtn,
            border: `1px solid ${s.collapseBorder}`,
            marginLeft: collapsed ? 0 : "auto",
          }}
        >
          {collapsed ? (
            <ChevronRight size={15} color={s.collapseIcon} />
          ) : (
            <ChevronLeft size={15} color={s.collapseIcon} />
          )}
        </button>
      )}
    </div>

    {/* Admin badge */}
    {isAdmin && (!collapsed || isMobilePanel) && (
      <div
        style={{
          margin: "0.6rem 0.75rem 0",
          padding: "0.35rem 0.7rem",
          borderRadius: 6,
          background: s.badgeBg,
          display: "flex",
          alignItems: "center",
          gap: "0.4rem",
          flexShrink: 0,
        }}
      >
        <Shield size={12} color={s.badgeText} />
        <span
          style={{
            fontSize: ".7rem",
            fontWeight: 700,
            letterSpacing: "0.08em",
            color: s.badgeText,
            textTransform: "uppercase",
          }}
        >
          Admin Panel
        </span>
      </div>
    )}

    {/* Nav items */}
    <nav style={{ flex: 1, overflowY: "auto", padding: "0.6rem 0.6rem 0" }}>
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => {
              onTabChange(tab.id);
              if (isMobilePanel) onClose();
            }}
            title={collapsed && !isMobilePanel ? tab.label : ""}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding:
                collapsed && !isMobilePanel ? "0.7rem 0" : "0.65rem 0.9rem",
              borderRadius: 9,
              marginBottom: 3,
              border: "none",
              background: isActive ? s.activeBg : "transparent",
              color: isActive ? s.activeText : s.text,
              fontWeight: isActive ? 600 : 400,
              fontSize: "1rem",
              cursor: "pointer",
              justifyContent:
                collapsed && !isMobilePanel ? "center" : "flex-start",
              transition: "background .15s, color .15s",
              outline: "none",
              fontFamily: "inherit",
            }}
            onMouseEnter={(e) => {
              if (!isActive) e.currentTarget.style.background = s.hoverBg;
            }}
            onMouseLeave={(e) => {
              if (!isActive) e.currentTarget.style.background = "transparent";
            }}
          >
            <Icon size={20} style={{ flexShrink: 0 }} />
            {(!collapsed || isMobilePanel) && (
              <span
                style={{
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {tab.label}
              </span>
            )}
          </button>
        );
      })}
    </nav>

    {/* Bottom: user card + logout */}
    <div
      style={{
        borderTop: `1px solid ${s.divider}`,
        padding: "0.75rem 0.6rem",
        flexShrink: 0,
      }}
    >
      {!collapsed || isMobilePanel ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            padding: "0.55rem 0.7rem",
            borderRadius: 9,
            background: s.userCardBg,
            border: `1px solid ${s.divider}`,
            marginBottom: "0.5rem",
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              flexShrink: 0,
              background: "linear-gradient(135deg,#7c3aed,#a855f7)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span
              style={{ fontSize: ".82rem", fontWeight: 700, color: "#fff" }}
            >
              {currentUser?.username?.[0]?.toUpperCase() || "U"}
            </span>
          </div>
          <div style={{ overflow: "hidden", flex: 1 }}>
            <div
              style={{
                fontWeight: 600,
                fontSize: ".875rem",
                color: theme.textPrimary,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {currentUser?.username || "User"}
            </div>
            <div
              style={{
                fontSize: ".72rem",
                color: s.muted,
                textTransform: "capitalize",
              }}
            >
              {currentUser?.role || "user"}
            </div>
          </div>
        </div>
      ) : (
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            margin: "0 auto 0.5rem",
            background: "linear-gradient(135deg,#7c3aed,#a855f7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span style={{ fontSize: ".82rem", fontWeight: 700, color: "#fff" }}>
            {currentUser?.username?.[0]?.toUpperCase() || "U"}
          </span>
        </div>
      )}

      {/* Logout button */}
      <button
        onClick={onLogoutClick}
        title="Logout"
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: "0.65rem",
          padding: collapsed && !isMobilePanel ? "0.65rem 0" : "0.6rem 0.9rem",
          borderRadius: 9,
          border: "none",
          background: "transparent",
          color: s.logoutText,
          fontWeight: 500,
          fontSize: "0.9375rem",
          cursor: "pointer",
          justifyContent: collapsed && !isMobilePanel ? "center" : "flex-start",
          transition: "background .15s",
          fontFamily: "inherit",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = s.logoutHover)}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <LogOut size={19} style={{ flexShrink: 0 }} />
        {(!collapsed || isMobilePanel) && <span>Logout</span>}
      </button>
    </div>
  </div>
);

// ── Navigation (root) ────────────────────────────────────────────────────────
const Navigation = ({
  currentUser,
  activeTab,
  onTabChange,
  onLogout,
  collapsed,
  onToggleCollapse,
  theme,
  sidebarWidth,
  isMobile,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (!isMobile) setMobileOpen(false);
  }, [isMobile]);

  useEffect(() => {
    window.__openMobileNav = () => setMobileOpen(true);
    return () => {
      delete window.__openMobileNav;
    };
  }, []);

  const isAdmin = currentUser?.role === "admin";
  const tabs = isAdmin ? ADMIN_TABS : USER_TABS;
  const s = theme.dark ? S.dark : S.light;

  const handleLogoutClick = () => setShowConfirm(true);
  const handleConfirm = () => {
    setShowConfirm(false);
    onLogout();
  };
  const handleCancel = () => setShowConfirm(false);

  const sharedProps = {
    s,
    theme,
    tabs,
    isAdmin,
    activeTab,
    onTabChange,
    onLogoutClick: handleLogoutClick,
    currentUser,
    collapsed,
    onToggleCollapse,
  };

  return (
    <>
      {showConfirm && (
        <LogoutModal s={s} onCancel={handleCancel} onConfirm={handleConfirm} />
      )}

      {isMobile ? (
        <>
          <div
            onClick={() => setMobileOpen(false)}
            style={{
              position: "fixed",
              inset: 0,
              background: s.overlay,
              zIndex: 45,
              opacity: mobileOpen ? 1 : 0,
              pointerEvents: mobileOpen ? "auto" : "none",
              transition: "opacity .28s ease",
            }}
          />
          <div
            style={{
              position: "fixed",
              left: 0,
              top: 56,
              zIndex: 50,
              transform: mobileOpen ? "translateX(0)" : "translateX(-100%)",
              transition: "transform .28s ease",
            }}
          >
            <SidebarPanel
              {...sharedProps}
              isMobilePanel
              onClose={() => setMobileOpen(false)}
              width={260}
            />
          </div>
        </>
      ) : (
        <div style={{ position: "fixed", left: 0, top: 56, zIndex: 40 }}>
          <SidebarPanel
            {...sharedProps}
            isMobilePanel={false}
            onClose={null}
            width={sidebarWidth}
          />
        </div>
      )}
    </>
  );
};

export default Navigation;
