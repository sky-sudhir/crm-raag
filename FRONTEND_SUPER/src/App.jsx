import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import NotFound from "./components/sections/NotFound";
import { ThemeProvider } from "./components/theme-provider";
import { ThemeToggle } from "./components/theme-toggle";
import { Toaster } from "sonner";
import "./styles/globals.css";
import { lazy, useEffect } from "react";
import HomePage from "./components/homePage/HomePage";
import { useSelector } from "react-redux";
import { selectUser } from "./redux/features/user/userSlice";

const AuthRoutes = lazy(() => import("./pages/AuthRoutes"));
const HomeRoutes = lazy(() => import("./pages/homeRoutes"));
const SuperAdminRoutes = lazy(() => import("./pages/SuperAdminRoutes"));
const StoreAdminRoutes = lazy(() => import("./pages/StoreAdminRoutes"));

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="repair-kart-theme">
      <Toaster position="top-right" expand={true} richColors />
      <div className="min-h-screen bg-background text-foreground">
        {/* <div className="fixed top-3.5 right-4 z-50">
          <ThemeToggle />
        </div> */}
        <BrowserRouter>
          <Routes>
            <Route path="" element={<HomePage />} />

            <Route path="auth/*" element={<AuthRoutes />} />
            <Route path="home/*" element={<HomeRoutes />} />
            <Route path="admin/*" element={<SuperAdminRoutes />} />
            <Route path="super/*" element={<StoreAdminRoutes />} />
            <Route path="404" element={<NotFound />} />
            <Route path="*" element={<Navigate replace to="/404" />} />
          </Routes>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

export default App;
