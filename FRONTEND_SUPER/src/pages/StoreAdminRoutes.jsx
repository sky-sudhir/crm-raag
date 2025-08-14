import React, { lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Suspense } from "../components/ui/suspense";
import Topbar from "../components/home/Topbar";
import NavigationBar from "../components/home/NavigationBar";
import RoleBasedRoute from "../components/auth/RoleBasedRoute";

// Lazy load components for better performance
const Dashboard = lazy(() => import("../components/home/dashboard/dashboard"));

function StoreAdminRoutes() {
  return (
    <RoleBasedRoute
      allowedRoles={["ROLE_ADMIN", "ROLE_USER"]}
      redirectTo="/home"
    >
      <Suspense>
        <div className="min-h-screen bg-background">
          <NavigationBar />
          <div className="lg:pl-72">
            <Topbar />
            <main className="container mx-auto py-6 px-4 lg:px-6">
              <Routes>
                <Route path="" element={<Dashboard />} />

                <Route path="*" element={<Navigate replace to="/404" />} />
              </Routes>
            </main>
          </div>
        </div>
      </Suspense>
    </RoleBasedRoute>
  );
}

export default StoreAdminRoutes;
