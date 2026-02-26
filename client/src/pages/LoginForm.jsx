// import React, { useState } from "react";
// import { Camera, Eye, EyeOff, Mail, AlertCircle } from "lucide-react";
// import { login } from "../services/authService";
// import { authAPI } from "../services/api";

// const LoginForm = ({ onLogin, onShowRegister, onShowForgotPassword }) => {
//   const [formData, setFormData] = useState({
//     username: "",
//     password: "",
//     showPassword: false,
//   });
//   const [error, setError] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [needsVerification, setNeedsVerification] = useState(false);
//   const [userEmail, setUserEmail] = useState("");
//   const [resendingEmail, setResendingEmail] = useState(false);

//   const handleSubmit = async () => {
//     console.log("=== SUBMIT STARTED ===");

//     if (!formData.username || !formData.password) {
//       setError("Please enter both username and password");
//       return;
//     }

//     setLoading(true);
//     setError("");
//     setNeedsVerification(false);

//     try {
//       const result = await login(formData.username, formData.password);

//       if (result.error) {
//         // Check if it's an email verification error
//         if (result.error === "Email not verified") {
//           setNeedsVerification(true);
//           setUserEmail(result.email || "");
//           setError("Please verify your email before logging in");
//         } else {
//           setError(result.error);
//         }
//         setLoading(false);
//         return;
//       }

//       onLogin(result.user);
//     } catch (err) {
//       setError("An unexpected error occurred");
//       setLoading(false);
//     }
//   };

//   const handleResendVerification = async () => {
//     if (!userEmail) {
//       setError("Email address not found. Please try registering again.");
//       return;
//     }

//     setResendingEmail(true);
//     try {
//       await authAPI.resendVerification(userEmail);
//       setError("");
//       alert("Verification email sent! Please check your inbox.");
//     } catch (err) {
//       setError("Failed to resend verification email");
//     } finally {
//       setResendingEmail(false);
//     }
//   };

//   const handleKeyPress = (e) => {
//     if (e.key === "Enter") {
//       handleSubmit();
//     }
//   };

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
//       <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md fade-in">
//         <div className="text-center mb-8">
//           <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
//             <Camera className="w-8 h-8 text-blue-600" />
//           </div>
//           <h1 className="text-2xl font-bold text-gray-900 mb-2">
//             Assistive Device Dashboard
//           </h1>
//           <p className="text-gray-600 text-sm">
//             Wearable Computer Vision System
//           </p>
//         </div>

//         <div className="space-y-4">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Username
//             </label>
//             <input
//               type="text"
//               value={formData.username}
//               onChange={(e) =>
//                 setFormData({ ...formData, username: e.target.value })
//               }
//               onKeyPress={handleKeyPress}
//               className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="Enter username"
//               disabled={loading}
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Password
//             </label>
//             <div className="relative">
//               <input
//                 type={formData.showPassword ? "text" : "password"}
//                 value={formData.password}
//                 onChange={(e) =>
//                   setFormData({ ...formData, password: e.target.value })
//                 }
//                 onKeyPress={handleKeyPress}
//                 className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//                 placeholder="Enter password"
//                 disabled={loading}
//               />
//               <button
//                 type="button"
//                 onClick={() =>
//                   setFormData({
//                     ...formData,
//                     showPassword: !formData.showPassword,
//                   })
//                 }
//                 className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
//               >
//                 {formData.showPassword ? (
//                   <EyeOff className="w-5 h-5" />
//                 ) : (
//                   <Eye className="w-5 h-5" />
//                 )}
//               </button>
//             </div>
//           </div>

//           {error && (
//             <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-start gap-2">
//               <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
//               <div className="flex-1">
//                 <p>{error}</p>
//                 {needsVerification && userEmail && (
//                   <button
//                     onClick={handleResendVerification}
//                     disabled={resendingEmail}
//                     className="mt-2 text-blue-600 hover:text-blue-700 font-medium underline disabled:opacity-50"
//                   >
//                     {resendingEmail
//                       ? "Sending..."
//                       : "Resend verification email"}
//                   </button>
//                 )}
//               </div>
//             </div>
//           )}

//           <button
//             type="button"
//             onClick={handleSubmit}
//             disabled={loading}
//             className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             {loading ? "Signing in..." : "Sign In"}
//           </button>

//           <div className="text-center">
//             <button
//               type="button"
//               onClick={onShowForgotPassword}
//               className="text-sm text-blue-600 hover:text-blue-700"
//             >
//               Forgot password?
//             </button>
//           </div>
//         </div>

//         <div className="mt-6 text-center">
//           <p className="text-sm text-gray-600">
//             Don't have an account?{" "}
//             <button
//               type="button"
//               onClick={onShowRegister}
//               className="text-blue-600 hover:text-blue-700 font-medium"
//             >
//               Sign up here
//             </button>
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default LoginForm;
import React, { useState } from "react";
import { Camera, Eye, EyeOff, AlertCircle, Moon, Sun } from "lucide-react";
import { login } from "../services/authService";
import { authAPI } from "../services/api";
import imgbgbg1 from "../styles/imgbgbg1.jpg";
import imgbgbg3 from "../styles/imgbgbg3.jpg";

const AUTH_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  @keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
  @keyframes spin   { to{transform:rotate(360deg)} }
  .auth-fadein { animation: fadeUp .4s ease-out both; }
  .auth-input  { transition: border-color .15s, box-shadow .15s; }
  .auth-input:focus { outline: none; }
  .auth-btn { transition: all .15s ease; font-family:'Inter',sans-serif; }
  .auth-btn:hover:not(:disabled) { opacity:.88; transform:translateY(-1px); }
  .auth-btn:active:not(:disabled) { transform:translateY(0); }

  @media (max-width: 767px) {
    .auth-desktop { display: none !important; }
    .auth-mobile  { display: flex !important; }
  }
  @media (min-width: 768px) {
    .auth-mobile  { display: none !important; }
    .auth-desktop { display: flex !important; }
  }
`;

const LoginForm = ({ onLogin, onShowRegister, onShowForgotPassword }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [needsVerif, setNeedsVerif] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [resending, setResending] = useState(false);
  const [dark, setDark] = useState(
    () => localStorage.getItem("theme") === "dark",
  );

  const toggleDark = () => {
    const n = !dark;
    setDark(n);
    localStorage.setItem("theme", n ? "dark" : "light");
  };

  const handleSubmit = async () => {
    if (!username || !password) {
      setError("Please enter both username and password");
      return;
    }
    setLoading(true);
    setError("");
    setNeedsVerif(false);
    try {
      const r = await login(username, password);
      if (r.error) {
        if (r.error === "Email not verified") {
          setNeedsVerif(true);
          setUserEmail(r.email || "");
          setError("Please verify your email before logging in");
        } else setError(r.error);
        setLoading(false);
        return;
      }
      onLogin(r.user);
    } catch {
      setError("An unexpected error occurred");
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!userEmail) {
      setError("Email not found. Try registering again.");
      return;
    }
    setResending(true);
    try {
      await authAPI.resendVerification(userEmail);
      setError("");
      alert("Verification email sent!");
    } catch {
      setError("Failed to resend verification email");
    } finally {
      setResending(false);
    }
  };

  const bg = dark ? imgbgbg3 : imgbgbg1;

  // ── Shared form JSX (rendered in both mobile + desktop) ──────────────────
  const renderForm = (mobile = false) => {
    // mobile: white text on blurred bg, no card bg
    // desktop: styled per dark/light theme inside card
    const tc = mobile ? "#ffffff" : dark ? "#f9fafb" : "#111827";
    const sc = mobile ? "rgba(255,255,255,0.75)" : dark ? "#aaaaaa" : "#6b7280";
    const lc = mobile ? "rgba(255,255,255,0.9)" : dark ? "#e0e0e0" : "#374151";
    const ic = mobile ? "rgba(0,0,0,0.55)" : dark ? "#2a2a2a" : "#ffffff";
    const ib = mobile ? "rgba(255,255,255,0.22)" : dark ? "#555555" : "#c4c4cc";
    const acc = mobile ? "#c084fc" : "#7c3aed";

    return (
      <div
        className="auth-fadein"
        style={{ width: "100%", maxWidth: mobile ? 420 : 420 }}
      >
        <h1
          style={{
            fontWeight: 700,
            fontSize: "1.6rem",
            color: tc,
            margin: "0 0 .3rem",
          }}
        >
          Sign in
        </h1>
        <p style={{ color: sc, fontSize: ".875rem", margin: "0 0 1.75rem" }}>
          Welcome back to your dashboard
        </p>

        {error && (
          <div
            style={{
              marginBottom: "1.25rem",
              padding: ".7rem .9rem",
              borderRadius: ".5rem",
              background: mobile
                ? "rgba(239,68,68,.18)"
                : dark
                  ? "rgba(239,68,68,.1)"
                  : "#fef2f2",
              border: `1px solid ${mobile ? "rgba(239,68,68,.35)" : dark ? "rgba(239,68,68,.2)" : "#fecaca"}`,
              display: "flex",
              alignItems: "flex-start",
              gap: ".5rem",
            }}
          >
            <AlertCircle
              size={15}
              color="#f87171"
              style={{ flexShrink: 0, marginTop: 2 }}
            />
            <div>
              <p
                style={{
                  color: mobile ? "#ffaaaa" : dark ? "#fca5a5" : "#dc2626",
                  fontSize: ".8rem",
                  margin: 0,
                }}
              >
                {error}
              </p>
              {needsVerif && userEmail && (
                <button
                  onClick={handleResend}
                  disabled={resending}
                  style={{
                    color: acc,
                    fontSize: ".76rem",
                    textDecoration: "underline",
                    marginTop: 4,
                    padding: 0,
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  {resending ? "Sending…" : "Resend verification email"}
                </button>
              )}
            </div>
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label
              style={{
                display: "block",
                fontSize: ".82rem",
                fontWeight: 500,
                color: lc,
                marginBottom: ".4rem",
              }}
            >
              Username <span style={{ color: "#f87171" }}>*</span>
            </label>
            <input
              type="text"
              value={username}
              disabled={loading}
              className="auth-input"
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSubmit()}
              style={{
                width: "100%",
                padding: ".65rem .85rem",
                borderRadius: ".45rem",
                border: `1px solid ${ib}`,
                background: ic,
                color: tc,
                fontSize: ".875rem",
                boxSizing: "border-box",
              }}
              onFocus={(e) =>
                (e.target.style.boxShadow = "0 0 0 3px rgba(168,85,247,.4)")
              }
              onBlur={(e) => (e.target.style.boxShadow = "none")}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: ".82rem",
                fontWeight: 500,
                color: lc,
                marginBottom: ".4rem",
              }}
            >
              Password <span style={{ color: "#f87171" }}>*</span>
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={showPw ? "text" : "password"}
                value={password}
                disabled={loading}
                className="auth-input"
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSubmit()}
                style={{
                  width: "100%",
                  padding: ".65rem 2.6rem .65rem .85rem",
                  borderRadius: ".45rem",
                  border: `1px solid ${ib}`,
                  background: ic,
                  color: tc,
                  fontSize: ".875rem",
                  boxSizing: "border-box",
                }}
                onFocus={(e) =>
                  (e.target.style.boxShadow = "0 0 0 3px rgba(168,85,247,.4)")
                }
                onBlur={(e) => (e.target.style.boxShadow = "none")}
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPw(!showPw)}
                style={{
                  position: "absolute",
                  right: ".75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: sc,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            <div style={{ textAlign: "right", marginTop: ".4rem" }}>
              <button
                type="button"
                onClick={onShowForgotPassword}
                style={{
                  color: acc,
                  fontSize: ".78rem",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Forgot password?
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="auth-btn"
            style={{
              background: "linear-gradient(135deg,#7c3aed,#a855f7)",
              border: "none",
              borderRadius: ".45rem",
              padding: ".72rem",
              color: "#fff",
              fontWeight: 600,
              fontSize: ".9rem",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.65 : 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: ".45rem",
            }}
          >
            {loading ? (
              <>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    border: "2px solid rgba(255,255,255,.3)",
                    borderTopColor: "#fff",
                    borderRadius: "50%",
                    animation: "spin .7s linear infinite",
                  }}
                />
                Signing in…
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </div>

        <p
          style={{
            color: sc,
            fontSize: ".82rem",
            textAlign: "center",
            marginTop: "1.5rem",
          }}
        >
          Don't have an account?{" "}
          <button
            type="button"
            onClick={onShowRegister}
            style={{
              color: acc,
              fontWeight: 600,
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            Sign up here
          </button>
        </p>
      </div>
    );
  };

  return (
    <>
      <style>{AUTH_CSS}</style>

      {/* ════════════════════════════════════
          MOBILE — full-screen bg, form floats
          ════════════════════════════════════ */}
      <div
        className="auth-mobile"
        style={{
          display: "none",
          flexDirection: "column",
          minHeight: "100vh",
          position: "relative",
          fontFamily: "'Inter',sans-serif",
          overflow: "hidden",
        }}
      >
        {/* bg image */}
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundImage: `url(${bg})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            zIndex: 0,
          }}
        />
        {/* dim */}
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.48)",
            zIndex: 1,
          }}
        />

        {/* top bar */}
        <div
          style={{
            position: "relative",
            zIndex: 2,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 1.25rem",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: ".5rem" }}>
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 7,
                background: "linear-gradient(135deg,#7c3aed,#a855f7)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Camera size={14} color="#fff" />
            </div>
            <span
              style={{ fontWeight: 700, fontSize: ".95rem", color: "#fff" }}
            >
              Assistive Device
            </span>
          </div>
          <button
            onClick={toggleDark}
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              border: "1px solid rgba(255,255,255,0.3)",
              background: "rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            {dark ? (
              <Sun size={15} color="#fbbf24" />
            ) : (
              <Moon size={15} color="#fff" />
            )}
          </button>
        </div>

        {/* centered form — no card, just floating on bg */}
        <div
          style={{
            position: "relative",
            zIndex: 2,
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem 1.5rem",
          }}
        >
          {renderForm(true)}
        </div>

        {/* footer */}
        <div
          style={{
            position: "relative",
            zIndex: 2,
            textAlign: "center",
            padding: ".75rem 1rem 1.5rem",
            flexShrink: 0,
          }}
        >
          <p
            style={{
              fontSize: ".72rem",
              color: "rgba(255,255,255,0.3)",
              margin: 0,
            }}
          >
            Assistive Device Dashboard · Wearable Computer Vision System
          </p>
        </div>
      </div>

      {/* ════════════════════════════════════
          DESKTOP — 50:50 split
          ════════════════════════════════════ */}
      <div
        className="auth-desktop"
        style={{
          display: "none",
          minHeight: "100vh",
          fontFamily: "'Inter',sans-serif",
        }}
      >
        {/* left panel */}
        <div
          style={{
            width: "50%",
            minWidth: 360,
            flexShrink: 0,
            background: dark ? "#181818" : "#ffffff",
            display: "flex",
            flexDirection: "column",
            borderRight: `1px solid ${dark ? "#242424" : "#e5e7eb"}`,
          }}
        >
          {/* top bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "1.25rem 2.5rem",
              borderBottom: `1px solid ${dark ? "#1c1c1c" : "#f3f4f6"}`,
            }}
          >
            <div
              style={{ display: "flex", alignItems: "center", gap: ".5rem" }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  background: "linear-gradient(135deg,#7c3aed,#a855f7)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Camera size={14} color="#fff" />
              </div>
              <span
                style={{
                  fontWeight: 700,
                  fontSize: ".95rem",
                  color: dark ? "#f9fafb" : "#111827",
                }}
              >
                Assistive Device
              </span>
            </div>
            <button
              onClick={toggleDark}
              style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                border: `1px solid ${dark ? "#333" : "#e5e7eb"}`,
                background: dark ? "#1e1e1e" : "#f9fafb",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
              }}
            >
              {dark ? (
                <Sun size={16} color="#fbbf24" />
              ) : (
                <Moon size={16} color="#6b7280" />
              )}
            </button>
          </div>

          {/* form inside card */}
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "2rem 2.5rem",
            }}
          >
            <div
              className="auth-fadein"
              style={{
                width: "100%",
                maxWidth: 420,
                background: dark ? "#2c2c2c" : "#f0f0f2",
                border: `1px solid ${dark ? "#444" : "#dcdce0"}`,
                borderRadius: 12,
                padding: "2rem",
                boxSizing: "border-box",
                boxShadow: dark
                  ? "0 8px 32px rgba(0,0,0,.6)"
                  : "0 4px 20px rgba(0,0,0,.07)",
              }}
            >
              {renderForm(false)}
            </div>
          </div>

          {/* footer */}
          <div
            style={{
              padding: "1rem 2.5rem",
              borderTop: `1px solid ${dark ? "#1c1c1c" : "#f3f4f6"}`,
              textAlign: "center",
            }}
          >
            <p
              style={{
                fontSize: ".72rem",
                color: dark ? "#555" : "#9ca3af",
                margin: 0,
              }}
            >
              Assistive Device Dashboard · Wearable Computer Vision System
            </p>
          </div>
        </div>

        {/* right image */}
        <div
          style={{
            flex: 1,
            position: "relative",
            overflow: "hidden",
            background: "#0a0a0a",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `url(${bg})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />
        </div>
      </div>
    </>
  );
};

export default LoginForm;
