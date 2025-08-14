// Auth endpoints
export const USERS_REGISTER_REQUEST_OTP = "api/auth/register/request-otp";
export const USERS_REGISTER = "api/auth/register";
export const AUTH_VERIFY = "api/auth/verify";
export const USERS_LOGIN = "api/auth/login";
export const USERS_SIGNUP = "api/auth/signup";
export const USER_FORGOT_PASSWORD_REQUEST_OTP = "api/users/forgot-password/request-otp";
export const USER_FORGOT_PASSWORD_RESET = "api/auth/forgot-password/reset";
export const API_USER_ME = "api/users/me";
export const USERS_PROFILE = "api/users/profile";

// User management endpoints
export const API_USERS_LIST = "api/users";
export const API_USER_DETAILS = "api/users/";
export const API_USER_UPDATE = "api/users/";
export const API_USER_DELETE = "api/users/";
export const API_USER_STATUS = "api/users/{id}/status";

// Store management endpoints
export const STORES_LIST = "api/stores";
export const STORE_CREATE = "api/stores";
export const STORE_DETAILS = "api/stores/";
export const STORE_UPDATE = "api/stores/";
export const STORE_DELETE = "api/stores/";
export const STORE_ASSIGN_ADMIN = "api/stores/{id}/admin";

// Product management endpoints
export const PRODUCTS_LIST = "api/products";
export const PRODUCT_CREATE = "api/products";
export const PRODUCT_DETAILS = "api/products/";
export const PRODUCT_UPDATE = "api/products/";
export const PRODUCT_DELETE = "api/products/";
export const PRODUCTS_BY_STORE = "api/products/store/";

// Product variant endpoints
export const PRODUCT_VARIANTS = "api/products/{productId}/variants";
export const VARIANT_DETAILS = "api/products/variants/";
export const VARIANT_UPDATE = "api/products/variants/";
export const VARIANT_DELETE = "api/products/variants/";
export const VARIANT_STOCK_UPDATE = "api/products/variants/{variantId}/stock";
export const LOW_STOCK_ITEMS = "api/products/store/low-stock";
export const STORE_VARIANTS = "api/products/store/variants";

// Order management endpoints
export const ORDERS_LIST = "api/orders";
export const ORDER_CREATE = "api/orders";
export const ORDER_DETAILS = "api/orders/";
export const ORDERS_BY_STORE = "api/orders/store";
export const ORDER_STATUS_UPDATE = "api/orders/{id}/status";
export const ORDER_CANCEL = "api/orders/{id}/cancel";
export const SALES_REPORT = "api/orders/reports/sales";

// File upload
export const FILES_UPLOAD = "api/files/upload";

// Legacy endpoints (can be removed if not needed)
export const CASE_STUDY = "case-studies";
export const CASE_STUDIES_ME = "case-studies";
export const PUBLIC_PORTFOLIO = "public";
export const OAUTH_GOOGLE_AUTHORIZE = "oauth2/google/authorize";
