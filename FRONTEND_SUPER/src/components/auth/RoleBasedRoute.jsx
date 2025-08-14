import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { selectIsAuthenticated, selectUser } from '@/redux/features/user/userSlice';

/**
 * Component for role-based routing
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render
 * @param {Array<string>} props.allowedRoles - Array of roles allowed to access the route
 * @param {string} props.redirectTo - Path to redirect to if user doesn't have permission
 * @returns {React.ReactNode} - The rendered component
 */
function RoleBasedRoute({ children, allowedRoles, redirectTo = "/home" }) {
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  // If user doesn't have the required role, redirect to specified path
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to={redirectTo} replace />;
  }

  // If authenticated and has the required role, render the children
  return children;
}

export default RoleBasedRoute;
