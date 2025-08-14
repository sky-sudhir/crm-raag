# Frontend AI Agent Instructions

## 1. Folder Structure

- `src/`
  - `components/`
    - `ui/` – All reusable UI components (e.g., `tabs.jsx`, `button.jsx`, `input.jsx`, etc.).
    - Other feature or layout components.
  - `hooks/`
    - `useQuery.js` – For GET API requests.
    - `useMutation.js` – For POST, PUT, PATCH, DELETE API requests.
  - `functions/` – Utility functions for API and logic (e.g., `apiHandler.js`).
  - `imports/` – Centralized API endpoints, base URLs, and localStorage helpers.
  - `redux/` – Redux Toolkit store and slices.
  - `schemas/` – Yup validation schemas for forms.
  - `styles/` – Global and component CSS (e.g., `globals.css`).
  - `lib/` – Utility helpers for cn(e.g., `utils.js`).
  - `pages/` – Route-level components (e.g., `AuthRoutes.jsx`, `homeRoutes.jsx`).

## 2. How to Use Hooks and Patterns

### Data Fetching and Mutations

- Use `useQuery` for all GET requests:
  ```js
  import useQuery from "@/hooks/useQuery";
  const { data, loading, error } = useQuery("/api/users");
  ```
- Use `useMutation` for POST, PUT, PATCH, DELETE:
  ```js
  import useMutation from "@/hooks/useMutation";
  const { mutate, loading, error } = useMutation("/api/users", {
    method: "POST",
  });
  mutate({ name: "John" });
  ```

### UI Components

- All reusable UI primitives (Tabs, Button, Input, etc.) are in `components/ui/`.
- Example usage:
  ```jsx
  import {
    Tabs,
    TabsList,
    TabsTrigger,
    TabsContent,
  } from "@/components/ui/tabs";
  ```

### API Calls

- Use `apiHandler` for custom API logic if needed.
- Always prefer `useQuery` and `useMutation` for data operations.

### Redux Store

- Store is configured in `redux/store.js`.
- Slices are combined using `combineSlices`.
- State is persisted to localStorage using the key from `imports/localStorage.js`.

### Toast Notifications

- Use `showToast` from `utils/toast.js` for user feedback.

### Form Validation

- Use Yup schemas from `schemas/` for form validation.
- Integrate with React Hook Form using `yupResolver`.

### Route Protection

- Use `ProtectedRoute` and `RoleBasedRoute` for authentication and authorization.

## 3. Example: Using useQuery and useMutation

```js
// GET example
import useQuery from "@/hooks/useQuery";
const { data, loading } = useQuery("/api/users");

// POST example
import useMutation from "@/hooks/useMutation";
const { mutate } = useMutation("/api/users", { method: "POST" });
mutate({ name: "Jane" });
```

## 4. Best Practices

- Use `useQuery` for all GET requests, `useMutation` for all others.
- Use UI components from `components/ui/` for consistency.
- Keep business logic in hooks/functions, not in components.
- Organize new features by domain (e.g., `components/featureName/`).
- Use centralized API endpoint constants from `imports/api.js`.
