import React, { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Menu,
  X,
  Store,
  ShoppingBag,
  ClipboardList,
  BarChart4,
  Package,
  Users,
} from "lucide-react";
import { Button } from "../ui/button";
import { useSelector } from "react-redux";
import { selectUser } from "@/redux/features/user/userSlice";
// import { removeToken } from "@/imports/localStorage";

// Navigation items based on user role
const getNavigationItems = (role) => {
  // Default navigation for unauthenticated users
  const defaultNav = [{ name: "Home", href: "/home", icon: LayoutDashboard }];

  // Super Admin navigation
  const superAdminNav = [
    { name: "Dashboard", href: "/admin", icon: LayoutDashboard },
    { name: "Store Management", href: "/admin/stores", icon: Store },
    { name: "User Management", href: "/admin/users", icon: Users },
    { name: "Categories", href: "/admin/categories", icon: Package },
  ];

  // Store Admin navigation
  const storeAdminNav = [
    { name: "Dashboard", href: "/store", icon: LayoutDashboard },
    { name: "Products", href: "/store/products", icon: Package },
    { name: "Variants", href: "/store/variants", icon: Package },
    { name: "Orders", href: "/store/orders", icon: ShoppingBag },
    { name: "Inventory", href: "/store/inventory", icon: ClipboardList },
    { name: "Reports", href: "/store/reports", icon: BarChart4 },
  ];

  // Return navigation based on role
  switch (role) {
    case "SUPERADMIN":
      return superAdminNav;
    case "STORE_ADMIN":
      return storeAdminNav;
    default:
      return defaultNav;
  }
};

function NavigationBar() {
  const [isOpen, setIsOpen] = useState(false);
  const user = useSelector(selectUser);
  // Get navigation items based on user role
  const navigationItems = getNavigationItems(user?.role);

  // Close mobile menu when screen size becomes large
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Prevent scroll when mobile menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
  }, [isOpen]);

  return (
    <>
      {/* Mobile Menu Button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-3 left-4 z-50 lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </Button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Navigation Menu */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-72 border-r bg-card transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:fixed",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col gap-2">
          <div className="border-b">
            <div className="flex h-16 items-center gap-3 px-6 bg-gradient-to-r from-primary to-accent text-white shadow-md">
              <Store size={28} strokeWidth={2.5} />
              <div className="flex flex-col">
                <span className="text-2xl font-bold tracking-tight">
                  RepairKart
                </span>
                <span className="text-xs font-medium text-primary-foreground">
                  {user?.role === "SUPERADMIN"
                    ? "Admin Portal"
                    : user?.role === "STORE_ADMIN"
                    ? "Store Management"
                    : "Repair Shop Management"}
                </span>
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-1 p-4">
            <nav className="flex flex-1 flex-col gap-1">
              {/* User info section if logged in */}
              {user && (
                <div className="mb-6 px-3 py-2">
                  <div className="font-medium">{user.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {user.email}
                  </div>
                  <div className="text-xs font-semibold mt-1 text-primary">
                    {user.role === "SUPERADMIN"
                      ? "Super Admin"
                      : user.role === "STORE_ADMIN"
                      ? "Store Admin"
                      : "User"}
                  </div>
                </div>
              )}

              {/* Navigation links */}
              {navigationItems.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-primary hover:text-primary-foreground",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground"
                    )
                  }
                  end
                  onClick={() => setIsOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </div>
    </>
  );
}

export default NavigationBar;
