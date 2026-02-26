// import React, { useState } from "react";
// import { authAPI } from "../services/api";
// import { Mail, ArrowLeft, CheckCircle } from "lucide-react";

// const ForgotPassword = ({ onShowLogin }) => {
//   const [email, setEmail] = useState("");
//   const [error, setError] = useState("");
//   const [success, setSuccess] = useState(false);
//   const [loading, setLoading] = useState(false);

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError("");

//     if (!email) {
//       setError("Please enter your email address");
//       return;
//     }

//     setLoading(true);

//     try {
//       await authAPI.forgotPassword(email);
//       setSuccess(true);
//     } catch (err) {
//       setError(err.response?.data?.error || "Failed to send reset email");
//     } finally {
//       setLoading(false);
//     }
//   };

//   if (success) {
//     return (
//       <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
//         <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
//           <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
//             <CheckCircle className="w-10 h-10 text-green-600" />
//           </div>

//           <h1 className="text-2xl font-bold text-gray-900 mb-2">
//             Check Your Email
//           </h1>

//           <p className="text-gray-600 mb-6">
//             We've sent password reset instructions to <strong>{email}</strong>
//           </p>

//           <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
//             <p className="text-sm text-blue-700">
//               The reset link will expire in 1 hour for security reasons.
//             </p>
//           </div>

//           <button
//             onClick={onShowLogin}
//             className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
//           >
//             Back to Login
//           </button>

//           <p className="text-xs text-gray-500 mt-4">
//             Didn't receive the email? Check your spam folder or try again.
//           </p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
//       <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
//         <button
//           onClick={onShowLogin}
//           className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
//         >
//           <ArrowLeft className="w-4 h-4" />
//           Back to login
//         </button>

//         <div className="text-center mb-8">
//           <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
//             <Mail className="w-8 h-8 text-blue-600" />
//           </div>
//           <h1 className="text-2xl font-bold text-gray-900 mb-2">
//             Forgot Password?
//           </h1>
//           <p className="text-gray-600 text-sm">
//             Enter your email and we'll send you a reset link
//           </p>
//         </div>

//         {error && (
//           <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
//             {error}
//           </div>
//         )}

//         <form onSubmit={handleSubmit} className="space-y-6">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Email Address
//             </label>
//             <input
//               type="email"
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="your.email@example.com"
//               disabled={loading}
//             />
//           </div>

//           <button
//             type="submit"
//             disabled={loading}
//             className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
//           >
//             {loading ? "Sending..." : "Send Reset Link"}
//           </button>
//         </form>
//       </div>
//     </div>
//   );
// };

// export default ForgotPassword;
import React, { useState } from "react";
import { Camera, Moon, Sun, Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { authAPI } from "../services/api";
import imgbgbg1 from "../styles/imgbgbg1.jpg";
import imgbgbg3 from "../styles/imgbgbg3.jpg";

const AUTH_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  @keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
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

const ForgotPassword = ({ onShowLogin }) => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(
    () => localStorage.getItem("theme") === "dark",
  );

  const toggleDark = () => {
    const n = !dark;
    setDark(n);
    localStorage.setItem("theme", n ? "dark" : "light");
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email) {
      setError("Please enter your email address");
      return;
    }
    setLoading(true);
    try {
      await authAPI.forgotPassword(email);
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  const bg = dark ? imgbgbg3 : imgbgbg1;

  const renderContent = (mobile = false) => {
    const tc = mobile ? "#ffffff" : dark ? "#f9fafb" : "#111827";
    const sc = mobile ? "rgba(255,255,255,0.75)" : dark ? "#aaaaaa" : "#6b7280";
    const lc = mobile ? "rgba(255,255,255,0.9)" : dark ? "#e0e0e0" : "#374151";
    const ic = mobile ? "rgba(0,0,0,0.55)" : dark ? "#2a2a2a" : "#ffffff";
    const ib = mobile ? "rgba(255,255,255,0.22)" : dark ? "#555555" : "#c4c4cc";
    const acc = mobile ? "#c084fc" : "#7c3aed";

    if (success)
      return (
        <div
          className="auth-fadein"
          style={{
            width: "100%",
            maxWidth: mobile ? 420 : 460,
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: mobile
                ? "rgba(16,185,129,.2)"
                : dark
                  ? "rgba(16,185,129,.15)"
                  : "#dcfce7",
              border: `1px solid ${mobile ? "rgba(16,185,129,.4)" : dark ? "rgba(16,185,129,.3)" : "#bbf7d0"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1.25rem",
            }}
          >
            <CheckCircle size={26} color="#22c55e" />
          </div>
          <h1
            style={{
              fontWeight: 700,
              fontSize: "1.5rem",
              color: tc,
              marginBottom: ".35rem",
            }}
          >
            Check Your Email
          </h1>
          <p style={{ color: sc, fontSize: ".875rem", marginBottom: "1rem" }}>
            Reset instructions sent to{" "}
            <span style={{ color: acc, fontWeight: 500 }}>{email}</span>
          </p>
          <div
            style={{
              padding: ".7rem 1rem",
              borderRadius: ".45rem",
              background: mobile
                ? "rgba(124,58,237,.18)"
                : dark
                  ? "rgba(124,58,237,.12)"
                  : "#f5f3ff",
              border: `1px solid ${mobile ? "rgba(168,85,247,.35)" : dark ? "rgba(124,58,237,.25)" : "#ddd6fe"}`,
              marginBottom: "1.5rem",
            }}
          >
            <p
              style={{
                color: mobile ? "#d8b4fe" : dark ? "#9d7fe8" : "#7c3aed",
                fontSize: ".8rem",
                margin: 0,
              }}
            >
              The reset link expires in 1 hour.
            </p>
          </div>
          <button
            onClick={onShowLogin}
            className="auth-btn"
            style={{
              width: "100%",
              background: "linear-gradient(135deg,#7c3aed,#a855f7)",
              border: "none",
              borderRadius: ".45rem",
              padding: ".72rem",
              color: "#fff",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Back to Login
          </button>
          <p
            style={{
              color: mobile ? "rgba(255,255,255,0.4)" : sc,
              fontSize: ".72rem",
              marginTop: "1rem",
            }}
          >
            Didn't receive it? Check your spam folder.
          </p>
        </div>
      );

    return (
      <div
        className="auth-fadein"
        style={{ width: "100%", maxWidth: mobile ? 420 : 460 }}
      >
        <button
          onClick={onShowLogin}
          style={{
            display: "flex",
            alignItems: "center",
            gap: ".4rem",
            color: sc,
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: ".82rem",
            marginBottom: "1.75rem",
            padding: 0,
          }}
        >
          <ArrowLeft size={14} /> Back to login
        </button>
        <h1
          style={{
            fontWeight: 700,
            fontSize: "1.6rem",
            color: tc,
            margin: "0 0 .3rem",
          }}
        >
          Forgot Password?
        </h1>
        <p style={{ color: sc, fontSize: ".875rem", margin: "0 0 1.75rem" }}>
          Enter your email and we'll send a reset link
        </p>

        {error && (
          <div
            style={{
              marginBottom: "1rem",
              padding: ".7rem .9rem",
              borderRadius: ".5rem",
              background: mobile
                ? "rgba(239,68,68,.18)"
                : dark
                  ? "rgba(239,68,68,.1)"
                  : "#fef2f2",
              border: `1px solid ${mobile ? "rgba(239,68,68,.35)" : dark ? "rgba(239,68,68,.2)" : "#fecaca"}`,
            }}
          >
            <p
              style={{
                color: mobile ? "#ffaaaa" : dark ? "#fca5a5" : "#dc2626",
                fontSize: ".8rem",
                margin: 0,
              }}
            >
              {error}
            </p>
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
        >
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
              Email Address <span style={{ color: "#f87171" }}>*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              disabled={loading}
              className="auth-input"
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
          <button
            type="submit"
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
            }}
          >
            {loading ? "Sending…" : "Send Reset Link"}
          </button>
        </form>
      </div>
    );
  };

  const TopBar = ({ mobile = false }) => (
    <div
      style={{
        position: mobile ? "relative" : "static",
        zIndex: mobile ? 2 : "auto",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: mobile ? "1rem 1.25rem" : "1.25rem 2.5rem",
        borderBottom: mobile
          ? "none"
          : `1px solid ${dark ? "#1c1c1c" : "#f3f4f6"}`,
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
          style={{
            fontWeight: 700,
            fontSize: ".95rem",
            color: mobile ? "#fff" : dark ? "#f9fafb" : "#111827",
          }}
        >
          Assistive Device
        </span>
      </div>
      <button
        onClick={toggleDark}
        style={{
          width: mobile ? 34 : 36,
          height: mobile ? 34 : 36,
          borderRadius: "50%",
          border: mobile
            ? "1px solid rgba(255,255,255,0.3)"
            : `1px solid ${dark ? "#333" : "#e5e7eb"}`,
          background: mobile ? "rgba(0,0,0,0.3)" : dark ? "#1e1e1e" : "#f9fafb",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
        }}
      >
        {dark ? (
          <Sun size={mobile ? 15 : 16} color="#fbbf24" />
        ) : (
          <Moon size={mobile ? 15 : 16} color={mobile ? "#fff" : "#6b7280"} />
        )}
      </button>
    </div>
  );

  return (
    <>
      <style>{AUTH_CSS}</style>

      {/* MOBILE */}
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
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.48)",
            zIndex: 1,
          }}
        />
        <TopBar mobile />
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
          {renderContent(true)}
        </div>
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

      {/* DESKTOP */}
      <div
        className="auth-desktop"
        style={{
          display: "none",
          minHeight: "100vh",
          fontFamily: "'Inter',sans-serif",
        }}
      >
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
          <TopBar />
          {/* form area — no card */}
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "2rem 2.5rem",
            }}
          >
            {renderContent(false)}
          </div>
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

export default ForgotPassword;
