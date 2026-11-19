import React, { useState } from "react";
import { Leaf, Lock, UserCheck, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";
import { apiFetch } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Field, inputCls } from "../components/UiPrimitives";

export function LoginPage(): React.ReactElement {
  const { login } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [resetMode, setResetMode] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(identifier, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible iniciar sesión.");
    } finally {
      setBusy(false);
    }
  };

  const handleRequestReset = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
    setResetMessage(null);
    setBusy(true);
    try {
      const res = await apiFetch<{ message: string; reset_token_preview?: string }>(
        "/api/v1/auth/password-reset/request",
        {
          method: "POST",
          body: JSON.stringify({ identifier }),
        }
      );
      setResetMessage(
        res.reset_token_preview
          ? `${res.message} Token temporal de verificación: ${res.reset_token_preview}`
          : res.message
      );
      if (res.reset_token_preview) {
        setResetToken(res.reset_token_preview);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error solicitando restablecimiento.");
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiFetch("/api/v1/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token: resetToken, new_password: newPassword }),
      });
      setResetMessage("Contraseña actualizada correctamente. Ya puedes iniciar sesión.");
      setResetMode(false);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Token inválido o expirado.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center px-4 py-8">
      <div className="mx-auto w-full max-w-md rounded-2xl bg-white shadow-2xl overflow-hidden border border-slate-200">
        <div className="bg-red-800 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-xl bg-white flex items-center justify-center shadow">
              <Leaf className="h-6 w-6 text-emerald-700" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-wide">SAJONA ADE</h1>
              <p className="text-xs text-red-100">Control de Siembra y Cosecha • PWA</p>
            </div>
          </div>
          <span className="rounded-lg bg-red-950/60 px-2.5 py-1 text-xs font-semibold">
            {new Date().toLocaleDateString("es-CO", { month: "short", year: "numeric" })}
          </span>
        </div>

        <div className="p-6 space-y-5">
          {error && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900"
            >
              <AlertCircle className="h-5 w-5 shrink-0 text-red-700" />
              <span>{error}</span>
            </div>
          )}

          {resetMessage && (
            <div
              role="status"
              className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-900 break-all"
            >
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-700" />
              <span>{resetMessage}</span>
            </div>
          )}

          {!resetMode ? (
            <form onSubmit={(e) => void handleLogin(e)} className="space-y-4">
              <Field label="Usuario o Correo" htmlFor="login-id" required>
                <div className="relative">
                  <UserCheck className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
                  <input
                    id="login-id"
                    type="text"
                    required
                    autoComplete="username"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="ej. jefe o admin@sajona.co"
                    className={`${inputCls} pl-9`}
                  />
                </div>
              </Field>

              <Field label="Contraseña" htmlFor="login-pwd" required>
                <div className="relative">
                  <Lock className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
                  <input
                    id="login-pwd"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className={`${inputCls} pl-9`}
                  />
                </div>
              </Field>

              <button
                type="submit"
                disabled={busy}
                className="w-full min-h-[46px] rounded-xl bg-emerald-700 px-4 py-2.5 text-base font-bold text-white shadow hover:bg-emerald-800 disabled:opacity-60 transition"
              >
                {busy ? "Verificando..." : "Ingresar"}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setResetMode(true);
                    setError(null);
                  }}
                  className="text-sm font-semibold text-red-800 hover:underline"
                >
                  ¿Olvidó la contraseña?
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => setResetMode(false)}
                className="inline-flex items-center gap-1 text-xs font-bold text-slate-700 hover:underline"
              >
                <ArrowLeft className="h-4 w-4" />
                Volver al inicio de sesión
              </button>
              <form onSubmit={(e) => void handleRequestReset(e)} className="space-y-3">
                <Field label="Usuario o correo registrado" htmlFor="rst-id" required>
                  <input
                    id="rst-id"
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className={inputCls}
                  />
                </Field>
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full min-h-[44px] rounded-xl bg-slate-800 px-4 py-2 text-sm font-bold text-white"
                >
                  Solicitar token de recuperación
                </button>
              </form>

              <form onSubmit={(e) => void handleConfirmReset(e)} className="space-y-3 pt-3 border-t">
                <Field label="Token de verificación" htmlFor="rst-tok" required>
                  <input
                    id="rst-tok"
                    type="text"
                    required
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    className={inputCls}
                  />
                </Field>
                <Field label="Nueva contraseña (mín. 8 caracteres)" htmlFor="rst-pwd" required>
                  <input
                    id="rst-pwd"
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={inputCls}
                  />
                </Field>
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full min-h-[44px] rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white"
                >
                  Restablecer contraseña
                </button>
              </form>
            </div>
          )}

          <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-xs text-slate-700 space-y-1">
            <p className="font-bold text-slate-900">Accesos de demostración (SAJONA TRL-6):</p>
            <p>
              <strong>Admin:</strong> admin / SajonaAdmin2026! • <strong>Jefe:</strong> jefe /
              SajonaJefe2026!
            </p>
            <p>
              <strong>Operario:</strong> operario / SajonaCampo2026! • <strong>Consulta:</strong>{" "}
              consulta / SajonaAudit2026!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
