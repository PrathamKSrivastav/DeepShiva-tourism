import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import { useState, useEffect } from "react";

function LoginButton({ onSuccess, darkMode }) {
  const { login } = useAuth();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 640); // sm breakpoint
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleSuccess = async (credentialResponse) => {
    console.log("🎫 Google credential received");
    const result = await login(credentialResponse.credential);

    if (result.success) {
      console.log("✅ Login complete:", result.user.email);

      // Check token with CORRECT key name
      setTimeout(() => {
        const token = localStorage.getItem("app_session_token");
        console.log(
          "🔍 Token check after login:",
          token ? "EXISTS ✅" : "MISSING ❌"
        );
        if (!token) {
          alert("Token save failed! Check browser settings.");
        } else {
          console.log("🎉 Token successfully saved and persisting!");
        }
      }, 500);

      if (onSuccess) {
        onSuccess(result.user);
      }
    } else {
      console.error("❌ Login result failed:", result.error);
      alert(`Login failed: ${result.error}`);
    }
  };

  const handleError = () => {
    console.error("❌ Google Login Failed");
    alert("Google Login failed. Please try again.");
  };

  return (
    <div className="flex items-center justify-center">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        useOneTap={false}
        theme={darkMode ? "filled_black" : "filled_blue"}
        size={isMobile ? "medium" : "large"}
        text={isMobile ? "signin" : "signin_with"}
        shape="rectangular"
        auto_select={false}
        width={isMobile ? "20" : undefined}
      />
    </div>
  );
}

export default LoginButton;
