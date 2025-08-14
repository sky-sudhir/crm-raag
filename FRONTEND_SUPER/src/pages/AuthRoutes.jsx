import React, { lazy, useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { Suspense } from "../components/ui/suspense";
import Signup from "@/components/auth/signup";
import OtpVerification from "@/components/auth/OtpVerification";
import ForgotPassword from "@/components/auth/ForgotPassword";
import ResetPassword from "@/components/auth/ResetPassword";
import VerifyPage from "@/components/auth/VerifyPage";
import { useSelector } from "react-redux";
import { selectIsAuthenticated, selectUser } from "@/redux/features/user/userSlice";

const Login = lazy(() => import("../components/auth/Login"));

function AuthRoutes() {

  const navigate = useNavigate();
  const isAuthenticated= useSelector(selectIsAuthenticated);


  useEffect(() => {
    if (isAuthenticated) {
      navigate("/home");
    }
  }, [isAuthenticated]);
  return (
    <Suspense>
      <Routes>
        <Route path="" element={<Navigate replace to="login" />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Signup />} />
        <Route path="verify" element={<OtpVerification />} />
        <Route path="verify-email" element={<VerifyPage />} />

        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="reset-password" element={<ResetPassword />} />
        <Route path="*" element={<Navigate replace to="/404" />} />
      </Routes>
    </Suspense>
  );
}

export default AuthRoutes;
