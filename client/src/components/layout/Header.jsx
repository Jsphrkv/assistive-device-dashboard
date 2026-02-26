import React from "react";
import { Camera, Moon, Sun, Menu } from "lucide-react";

const Header = ({ theme, onToggleDark, isMobile, onOpenMobileMenu }) => {
  const { dark, headerBg, headerBorder, headerText, headerSub } = theme;

  return (
    <header
      style={{
        background: headerBg,
        borderBottom: `1px solid ${headerBorder}`,
        height: 64,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1.5rem",
        width: "100%",
        boxSizing: "border-box",
        transition: "background .2s, border-color .2s",
      }}
    >
      {/* Left: burger (mobile only) + logo icon + title */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        {isMobile && (
          <button
            onClick={onOpenMobileMenu}
            aria-label="Open menu"
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: "linear-gradient(135deg,#7c3aed,#a855f7)",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              boxShadow: "0 2px 8px rgba(124,58,237,0.35)",
            }}
          >
            <Menu size={18} color="#fff" />
          </button>
        )}

        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            flexShrink: 0,
            background: "linear-gradient(135deg,#7c3aed,#a855f7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Camera size={16} color="#fff" />
        </div>

        <div>
          <h1
            style={{
              fontWeight: 700,
              fontSize: "1rem",
              color: headerText,
              margin: 0,
              lineHeight: 1.25,
              whiteSpace: "nowrap",
            }}
          >
            Assistive Device Dashboard
          </h1>
          {!isMobile && (
            <p style={{ fontSize: "0.7rem", color: headerSub, margin: 0 }}>
              Wearable Computer Vision System
            </p>
          )}
        </div>
      </div>

      {/* Right: dark mode toggle */}
      <button
        onClick={onToggleDark}
        title={dark ? "Switch to light mode" : "Switch to dark mode"}
        style={{
          width: 38,
          height: 38,
          borderRadius: "50%",
          border: `1px solid ${dark ? "#3a3a3a" : "#e5e7eb"}`,
          background: dark ? "#2a2a2a" : "#f9fafb",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "background .2s, border-color .2s",
          flexShrink: 0,
        }}
      >
        {dark ? (
          <Sun size={16} color="#fbbf24" />
        ) : (
          <Moon size={16} color="#6b7280" />
        )}
      </button>
    </header>
  );
};

export default Header;
