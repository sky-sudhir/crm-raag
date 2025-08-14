import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import { Button } from "../ui/button";
import { Input, PasswordInput } from "../ui/input";
import { Label } from "../ui/label";
import { registerSchema } from "../../schemas/validation";
import useMutation from "@/hooks/useMutation";
import { USERS_REGISTER_REQUEST_OTP, USERS_SIGNUP } from "@/imports/api";

function Signup() {
  const navigate = useNavigate();

  const { mutate ,loading} = useMutation();
  // Focus first input on component mount
  useEffect(() => {
    const firstInput = document.querySelector("[data-first-name-input]");
    if (firstInput) {
      firstInput.focus();
    }
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      mobileNumber: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (data) => {
    const tempData={
      ...data,
    }
    delete tempData.confirmPassword
    const response = await mutate({url:USERS_SIGNUP,method:"POST",data:tempData})
    // if(response.success){
    //   navigate("/auth/verify", { state: { ...tempData } });
    // }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card p-8 rounded-lg border shadow-sm">
          <h2 className="mt-6 text-center text-3xl font-bold text-foreground">
            Create your account
          </h2>
        <div>
          <p className="mt-2 text-center text-sm text-muted-foreground">
           Continue to TaskPal?{" "}
            <Link
              to="/auth/login"
              className="font-medium text-primary hover:text-primary/90"
            >
              Sign in
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  autoComplete="given-name"
                  {...register("name")}
                  data-first-name-input
                  className={errors.name ? "border-destructive" : ""}
                  placeholder="John"
                />
                {errors.name && (
                  <p className="text-sm text-destructive">
                    {errors.name.message}
                  </p>
                )}
              </div>

            

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="mobileNumber">Mobile Number</Label>
                <Input
                  id="mobileNumber"
                  type="tel"
                  autoComplete="tel"
                  {...register("mobileNumber")}
                  className={errors.mobileNumber ? "border-destructive" : ""}
                  placeholder="+91 9845367890"
                />
                {errors.mobileNumber && (
                  <p className="text-sm text-destructive">
                    {errors.mobileNumber.message}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                className={errors.email ? "border-destructive" : ""}
                placeholder="you@example.com"
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
                autoComplete="new-password"
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

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <PasswordInput
                id="confirmPassword"
                autoComplete="new-password"
                {...register("confirmPassword")}
                className={errors.confirmPassword ? "border-destructive" : ""}
                placeholder="••••••"
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>
          </div>

          <Button loading={loading} type="submit" className="w-full">
            Create account
          </Button>
        </form>
      </div>
    </div>
  );
}

export default Signup;
