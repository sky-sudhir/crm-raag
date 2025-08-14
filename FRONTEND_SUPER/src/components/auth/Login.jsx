import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import { Button } from "../ui/button";
import { Input, PasswordInput } from "../ui/input";
import { Label } from "../ui/label";
import { loginSchema } from "../../schemas/validation";
import { USERS_LOGIN } from "@/imports/api";
import useMutation from "@/hooks/useMutation";
import { useDispatch } from "react-redux";
import { setToken, setUser } from "@/redux/features/user/userSlice";

function Login() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { mutate, loading } = useMutation();
  // Focus email input on component mount
  useEffect(() => {
    const emailInput = document.querySelector("[data-email-input]");
    if (emailInput) {
      emailInput.focus();
    }
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data) => {
    console.log("Form submitted:", data);
    const response = await mutate({ url: USERS_LOGIN, method: "POST", data });
    if (response.success) {
      console.log(response.data);
      // Save user data and token to Redux store
      const userData = response?.data?.data?.user;
      dispatch(setUser({ ...userData, token: null }));
      dispatch(setToken({ token: response?.data?.data?.token }));

      // Redirect based on user role
      if (userData.role === "SUPERADMIN") {
        navigate("/super");
      } else if (
        userData.role === "ROLE_ADMIN" ||
        userData.role === "ROLE_USER"
      ) {
        navigate("/store");
      } else {
        // Default route for other roles
        navigate("/home");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card p-8 rounded-lg border shadow-sm">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold text-foreground">
            Welcome back RepairKart
          </h2>
          {/* <p className="mt-2 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link
              to="/auth/register"
              className="font-medium text-primary hover:text-primary/90"
            >
              Sign up
            </Link>
          </p> */}
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                className={errors.email ? "border-destructive" : ""}
                placeholder="you@example.com"
                data-email-input
              />
              {errors.email && (
                <p className="text-sm text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <PasswordInput
                id="password"
                autoComplete="current-password"
                {...register("password")}
                className={errors.password ? "border-destructive" : ""}
                placeholder="••••••"
              />
              {errors.password && (
                <p className="text-sm text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center"></div>
          </div>

          <Button loading={loading} type="submit" className="w-full">
            Sign in
          </Button>
        </form>
      </div>
    </div>
  );
}

export default Login;
