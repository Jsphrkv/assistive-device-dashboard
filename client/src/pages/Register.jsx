// import React, { useState } from "react";
// import { authAPI } from "../services/api";
// import { CheckCircle, Mail } from "lucide-react";

// const Register = ({ onShowLogin }) => {
//   const [formData, setFormData] = useState({
//     username: "",
//     email: "",
//     password: "",
//     confirmPassword: "",
//   });
//   const [error, setError] = useState("");
//   const [success, setSuccess] = useState(false);
//   const [registeredEmail, setRegisteredEmail] = useState("");
//   const [loading, setLoading] = useState(false);

//   const handleChange = (e) => {
//     setFormData({
//       ...formData,
//       [e.target.name]: e.target.value,
//     });
//     setError("");
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError("");

//     // Validation
//     if (!formData.username || !formData.email || !formData.password) {
//       setError("All fields are required");
//       return;
//     }

//     if (formData.password !== formData.confirmPassword) {
//       setError("Passwords do not match");
//       return;
//     }

//     if (formData.password.length < 8) {
//       setError("Password must be at least 8 characters");
//       return;
//     }

//     setLoading(true);

//     try {
//       const response = await authAPI.register(
//         formData.username,
//         formData.email,
//         formData.password,
//       );

//       setSuccess(true);
//       setRegisteredEmail(formData.email);
//     } catch (err) {
//       setError(err.response?.data?.error || "Registration failed");
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Success screen
//   if (success) {
//     return (
//       <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-4">
//         <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
//           <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
//             <CheckCircle className="w-10 h-10 text-green-600" />
//           </div>

//           <h1 className="text-2xl font-bold text-gray-900 mb-2">
//             Check Your Email!
//           </h1>

//           <p className="text-gray-600 mb-6">
//             We've sent a verification link to:
//           </p>

//           <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
//             <div className="flex items-center justify-center gap-2 text-blue-700">
//               <Mail className="w-5 h-5" />
//               <span className="font-medium">{registeredEmail}</span>
//             </div>
//           </div>

//           <p className="text-sm text-gray-600 mb-6">
//             Click the link in the email to verify your account and start using
//             the dashboard.
//           </p>

//           <button
//             onClick={onShowLogin}
//             className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
//           >
//             Back to Login
//           </button>

//           <p className="text-xs text-gray-500 mt-4">
//             Didn't receive the email? Check your spam folder.
//           </p>
//         </div>
//       </div>
//     );
//   }

//   // Registration form
//   return (
//     <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
//       <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
//         <div className="text-center mb-8">
//           <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
//           <p className="text-gray-600 mt-2">
//             Sign up for Assistive Device Dashboard
//           </p>
//         </div>

//         {error && (
//           <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
//             {error}
//           </div>
//         )}

//         <form onSubmit={handleSubmit} className="space-y-4">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Username
//             </label>
//             <input
//               type="text"
//               name="username"
//               value={formData.username}
//               onChange={handleChange}
//               className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="Enter username"
//               disabled={loading}
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Email
//             </label>
//             <input
//               type="email"
//               name="email"
//               value={formData.email}
//               onChange={handleChange}
//               className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="Enter email"
//               disabled={loading}
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Password
//             </label>
//             <input
//               type="password"
//               name="password"
//               value={formData.password}
//               onChange={handleChange}
//               className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="Enter password (min 8 characters)"
//               disabled={loading}
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-1">
//               Confirm Password
//             </label>
//             <input
//               type="password"
//               name="confirmPassword"
//               value={formData.confirmPassword}
//               onChange={handleChange}
//               className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//               placeholder="Confirm password"
//               disabled={loading}
//             />
//           </div>

//           <button
//             type="submit"
//             disabled={loading}
//             className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
//           >
//             {loading ? "Creating Account..." : "Sign Up"}
//           </button>
//         </form>

//         <div className="mt-6 text-center">
//           <p className="text-sm text-gray-600">
//             Already have an account?{" "}
//             <button
//               onClick={onShowLogin}
//               className="text-blue-600 hover:text-blue-700 font-medium"
//             >
//               Login here
//             </button>
//           </p>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Register;
import React, { useState } from "react";
import { Camera, Moon, Sun, CheckCircle, Mail } from "lucide-react";
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

const Register = ({ onShowLogin }) => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(
    () => localStorage.getItem("theme") === "dark",
  );

  const toggleDark = () => {
    const n = !dark;
    setDark(n);
    localStorage.setItem("theme", n ? "dark" : "light");
  };
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!formData.username || !formData.email || !formData.password) {
      setError("All fields are required");
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await authAPI.register(
        formData.username,
        formData.email,
        formData.password,
      );
      setSuccess(true);
      setRegisteredEmail(formData.email);
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed");
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
          style={{ width: "100%", maxWidth: 420, textAlign: "center" }}
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
            Check Your Email!
          </h1>
          <p
            style={{ color: sc, fontSize: ".875rem", marginBottom: "1.25rem" }}
          >
            We've sent a verification link to:
          </p>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: ".45rem",
              padding: ".7rem 1rem",
              borderRadius: ".45rem",
              background: mobile
                ? "rgba(124,58,237,.18)"
                : dark
                  ? "rgba(124,58,237,.12)"
                  : "#f5f3ff",
              border: `1px solid ${mobile ? "rgba(168,85,247,.35)" : dark ? "rgba(124,58,237,.25)" : "#ddd6fe"}`,
              marginBottom: "1.25rem",
            }}
          >
            <Mail size={14} color={acc} />
            <span style={{ color: acc, fontWeight: 500, fontSize: ".875rem" }}>
              {registeredEmail}
            </span>
          </div>
          <p style={{ color: sc, fontSize: ".8rem", marginBottom: "1.5rem" }}>
            Click the link to verify your account.
          </p>
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
        </div>
      );

    return (
      <div className="auth-fadein" style={{ width: "100%", maxWidth: 420 }}>
        <h1
          style={{
            fontWeight: 700,
            fontSize: "1.6rem",
            color: tc,
            margin: "0 0 .3rem",
          }}
        >
          Create Account
        </h1>
        <p style={{ color: sc, fontSize: ".875rem", margin: "0 0 1.5rem" }}>
          Sign up for the assistive device platform
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
          style={{ display: "flex", flexDirection: "column", gap: ".85rem" }}
        >
          {[
            { label: "Username", name: "username", type: "text" },
            { label: "Email", name: "email", type: "email" },
            { label: "Password", name: "password", type: "password" },
            {
              label: "Confirm Password",
              name: "confirmPassword",
              type: "password",
            },
          ].map(({ label, name, type }) => (
            <div key={name}>
              <label
                style={{
                  display: "block",
                  fontSize: ".82rem",
                  fontWeight: 500,
                  color: lc,
                  marginBottom: ".35rem",
                }}
              >
                {label} <span style={{ color: "#f87171" }}>*</span>
              </label>
              <input
                type={type}
                name={name}
                value={formData[name]}
                onChange={handleChange}
                disabled={loading}
                className="auth-input"
                style={{
                  width: "100%",
                  padding: ".6rem .85rem",
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
          ))}
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
              marginTop: ".1rem",
            }}
          >
            {loading ? "Creating Account…" : "Sign Up"}
          </button>
        </form>

        <p
          style={{
            color: sc,
            fontSize: ".82rem",
            textAlign: "center",
            marginTop: "1.25rem",
          }}
        >
          Already have an account?{" "}
          <button
            onClick={onShowLogin}
            style={{
              color: acc,
              fontWeight: 600,
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            Login here
          </button>
        </p>
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
              {renderContent(false)}
            </div>
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

export default Register;
