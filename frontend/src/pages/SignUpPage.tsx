import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { useAuth } from "../context/useAuth";
import type { SignupPayload } from "../types/auth";

function SignUpPage() {
  const { signup, loginError, isAuthenticated, status } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  const error = loginError ?? fieldError;

  useEffect(() => {
    if (isAuthenticated) {
      window.location.hash = "#/discover";
    }
  }, [isAuthenticated]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!username.trim()) {
      setFieldError("Choose a HarmonIQ username.");
      return;
    }
    if (!email.trim()) {
      setFieldError("Enter your email address.");
      return;
    }
    if (!password) {
      setFieldError("Create a password.");
      return;
    }
    if (password !== passwordConfirm) {
      setFieldError("Passwords do not match.");
      return;
    }

    setFieldError(null);
    setIsSubmitting(true);
    const payload: SignupPayload = {
      username: username.trim(),
      email: email.trim(),
      password,
      password_confirm: passwordConfirm,
    };

    try {
      await signup(payload);
    } catch {
      // The failure message is surfaced through the auth context.
    } finally {
      setIsSubmitting(false);
    }
  };

  const busy = isSubmitting || status === "loading";

  return (
    <div className="auth-page">
      <header className="auth-page__header">
        <a href="/" className="auth-page__brand">
          HarmonIQ
        </a>
      </header>

      <main className="auth-page__main">
        <div className="auth-card">
          <p className="eyebrow">Your account</p>
          <h1 className="auth-card__title">Create your HarmonIQ account</h1>
          <p className="auth-card__copy">
            Choose a HarmonIQ username. Your Spotify identity stays separate —
            connect it whenever you like.
          </p>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-form__field">
              <label className="auth-form__label" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                className="input"
                type="text"
                name="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                autoCapitalize="none"
                required
                disabled={busy}
                aria-describedby={error ? "auth-form-error" : undefined}
              />
            </div>

            <div className="auth-form__field">
              <label className="auth-form__label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                className="input"
                type="email"
                name="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
                disabled={busy}
                aria-describedby={error ? "auth-form-error" : undefined}
              />
            </div>

            <div className="auth-form__field">
              <label className="auth-form__label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                className="input"
                type="password"
                name="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
                disabled={busy}
                aria-describedby={error ? "auth-form-error" : undefined}
              />
            </div>

            <div className="auth-form__field">
              <label className="auth-form__label" htmlFor="password-confirm">
                Confirm password
              </label>
              <input
                id="password-confirm"
                className="input"
                type="password"
                name="password-confirm"
                value={passwordConfirm}
                onChange={(event) => setPasswordConfirm(event.target.value)}
                autoComplete="new-password"
                required
                disabled={busy}
                aria-describedby={error ? "auth-form-error" : undefined}
              />
            </div>

            {error ? (
              <p
                id="auth-form-error"
                className="auth-form__error"
                role="alert"
              >
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              className="button button--primary auth-form__submit"
              disabled={busy}
            >
              {busy ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="auth-card__alt">
            Already have an account?{" "}
            <a href="#/login" className="auth-card__alt-link">
              Sign in
            </a>
          </p>

          <a href="/" className="auth-card__back">
            &larr; Back to home
          </a>
        </div>
      </main>
    </div>
  );
}

export default SignUpPage;