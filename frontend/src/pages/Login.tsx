/**
 * Login Page for OSINT Platform
 * Handles user authentication with login and registration forms
 */

import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

interface LoginFormData {
  email: string;
  password: string;
}

interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
  company?: string;
}

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const { login, register, isAuthenticated, isLoading } = useAuth();

  const {
    register: registerField,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<LoginFormData & RegisterFormData>();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const onSubmit = async (data: LoginFormData & RegisterFormData) => {
    try {
      if (isLogin) {
        await login(data.email, data.password);
      } else {
        if (data.password !== data.confirmPassword) {
          toast.error('Passwords do not match');
          return;
        }
        await register(data.email, data.password, data.fullName, data.company);
      }
    } catch (error) {
      // Error handling is done in the auth context
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    reset();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">O</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={toggleMode}
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            {/* Full Name (Register only) */}
            {!isLogin && (
              <div>
                <label htmlFor="fullName" className="label">
                  Full Name
                </label>
                <input
                  {...registerField('fullName', {
                    required: !isLogin ? 'Full name is required' : false,
                    minLength: {
                      value: 2,
                      message: 'Full name must be at least 2 characters',
                    },
                  })}
                  type="text"
                  className={`input-field ${errors.fullName ? 'input-error' : ''}`}
                  placeholder="Enter your full name"
                />
                {errors.fullName && (
                  <p className="error-text">{errors.fullName.message}</p>
                )}
              </div>
            )}

            {/* Email */}
            <div>
              <label htmlFor="email" className="label">
                Email Address
              </label>
              <input
                {...registerField('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address',
                  },
                })}
                type="email"
                autoComplete="email"
                className={`input-field ${errors.email ? 'input-error' : ''}`}
                placeholder="Enter your email"
              />
              {errors.email && <p className="error-text">{errors.email.message}</p>}
            </div>

            {/* Company (Register only) */}
            {!isLogin && (
              <div>
                <label htmlFor="company" className="label">
                  Company (Optional)
                </label>
                <input
                  {...registerField('company')}
                  type="text"
                  className="input-field"
                  placeholder="Enter your company name"
                />
              </div>
            )}

            {/* Password */}
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative">
                <input
                  {...registerField('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 8,
                      message: 'Password must be at least 8 characters',
                    },
                  })}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  className={`input-field pr-10 ${errors.password ? 'input-error' : ''}`}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="error-text">{errors.password.message}</p>
              )}
            </div>

            {/* Confirm Password (Register only) */}
            {!isLogin && (
              <div>
                <label htmlFor="confirmPassword" className="label">
                  Confirm Password
                </label>
                <input
                  {...registerField('confirmPassword', {
                    required: !isLogin ? 'Please confirm your password' : false,
                    validate: (value) =>
                      value === watch('password') || 'Passwords do not match',
                  })}
                  type="password"
                  autoComplete="new-password"
                  className={`input-field ${
                    errors.confirmPassword ? 'input-error' : ''
                  }`}
                  placeholder="Confirm your password"
                />
                {errors.confirmPassword && (
                  <p className="error-text">{errors.confirmPassword.message}</p>
                )}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {isLogin ? 'Signing in...' : 'Creating account...'}
                </div>
              ) : (
                <span>{isLogin ? 'Sign in' : 'Create account'}</span>
              )}
            </button>
          </div>

          {/* Login options */}
          {isLogin && (
            <div className="flex items-center justify-between">
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  Forgot your password?
                </a>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          By {isLogin ? 'signing in' : 'creating an account'}, you agree to our{' '}
          <a href="#" className="text-blue-600 hover:text-blue-500">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className="text-blue-600 hover:text-blue-500">
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  );
};

export default Login;
