import React, { useEffect, useState } from "react";
import { UserPlus } from "lucide-react";
import { apiFetch } from "../api/client";
import { Field, ModalDrawer, ToastBanner, inputCls } from "../components/UiPrimitives";
import type { RoleCode } from "../domain/types";

interface AdminUserRow {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: RoleCode[];
  activo: boolean;
}

export function UsuariosAdminPage(): React.ReactElement {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nombres, setNombres] = useState("");
  const [apellidos, setApellidos] = useState("");
  const [doc, setDoc] = useState("");
  const [telefono, setTelefono] = useState("");
  const [role, setRole] = useState<RoleCode>("OPERARIO");

  const loadUsers = async (): Promise<void> => {
    try {
      const data = await apiFetch<AdminUserRow[]>("/api/v1/admin/users");
      setUsers(data);
    } catch (err) {
      setToast({
        type: "warning",
        text: err instanceof Error ? err.message : "La gestión de usuarios requiere conexión al servidor.",
      });
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const handleCreate = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/admin/users", {
        method: "POST",
        body: JSON.stringify({
          username,
          email,
          password,
          nombres,
          apellidos,
          numero_identificacion: doc,
          telefono,
          roles: [role],
        }),
      });
      setModalOpen(false);
      setToast({ type: "success", text: "Usuario y funcionario creados." });
      await loadUsers();
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error creando usuario." });
    }
  };

  const toggleStatus = async (u: AdminUserRow): Promise<void> => {
    try {
      await apiFetch(`/api/v1/admin/users/${u.id}`, {
        method: "PATCH",
        body: JSON.stringify({ activo: !u.activo }),
      });
      await loadUsers();
    } catch (err) {
      setToast({ type: "error", text: err instanceof Error ? err.message : "Error actualizando." });
    }
  };

  return (
    <div className="space-y-4">
      <ToastBanner toast={toast} onDismiss={() => setToast(null)} />
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">Usuarios, Funcionarios y Roles</h1>
          <p className="text-xs sm:text-sm text-slate-600">Control de acceso RBAC (requiere conectividad en línea).</p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="min-h-[44px] inline-flex items-center gap-1.5 rounded-xl bg-emerald-700 px-4 text-sm font-bold text-white"
        >
          <UserPlus className="h-4 w-4" />
          Nuevo Usuario
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {users.map((u) => (
          <div key={u.id} className="rounded-xl border border-slate-200 bg-white p-4 flex items-center justify-between gap-3">
            <div>
              <p className="font-bold text-slate-900">{u.full_name}</p>
              <p className="text-xs text-slate-600">
                @{u.username} • {u.email}
              </p>
              <span className="inline-block mt-1 rounded bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-800">
                {u.roles.join(", ")}
              </span>
            </div>
            <button
              type="button"
              onClick={() => void toggleStatus(u)}
              className={`min-h-[38px] rounded-lg px-3 text-xs font-bold ${
                u.activo ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-red-50 text-red-800 border border-red-200"
              }`}
            >
              {u.activo ? "Activo" : "Inactivo"}
            </button>
          </div>
        ))}
      </div>

      <ModalDrawer open={modalOpen} onClose={() => setModalOpen(false)} title="Nuevo Funcionario y Usuario">
        <form onSubmit={(e) => void handleCreate(e)} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Nombres" htmlFor="u-nom" required><input id="u-nom" required value={nombres} onChange={(e) => setNombres(e.target.value)} className={inputCls} /></Field>
            <Field label="Apellidos" htmlFor="u-ape" required><input id="u-ape" required value={apellidos} onChange={(e) => setApellidos(e.target.value)} className={inputCls} /></Field>
            <Field label="Cédula / ID" htmlFor="u-doc" required><input id="u-doc" required value={doc} onChange={(e) => setDoc(e.target.value)} className={inputCls} /></Field>
            <Field label="Teléfono" htmlFor="u-tel" required><input id="u-tel" required value={telefono} onChange={(e) => setTelefono(e.target.value)} className={inputCls} /></Field>
            <Field label="Username" htmlFor="u-usr" required><input id="u-usr" required value={username} onChange={(e) => setUsername(e.target.value)} className={inputCls} /></Field>
            <Field label="Correo" htmlFor="u-mail" required><input id="u-mail" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} /></Field>
            <Field label="Contraseña" htmlFor="u-pwd" required><input id="u-pwd" type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} className={inputCls} /></Field>
            <Field label="Rol" htmlFor="u-rol" required>
              <select id="u-rol" value={role} onChange={(e) => setRole(e.target.value as RoleCode)} className={inputCls}>
                <option value="OPERARIO">Operario</option>
                <option value="JEFE_PROYECTO">Jefe de Proyecto</option>
                <option value="CONSULTA">Consulta</option>
                <option value="ADMIN">Administrador</option>
              </select>
            </Field>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="min-h-[44px] rounded-xl border px-4 text-sm font-semibold">Cancelar</button>
            <button type="submit" className="min-h-[44px] rounded-xl bg-emerald-700 px-5 text-sm font-bold text-white">Crear Usuario</button>
          </div>
        </form>
      </ModalDrawer>
    </div>
  );
}

interface AuditEntry {
  id: string;
  correlation_id: string;
  username: string;
  entidad: string;
  entidad_id: string;
  operacion: string;
  resultado: string;
  fuente: string;
  created_at: string;
}

export function AuditoriaPage(): React.ReactElement {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const res = await apiFetch<AuditEntry[]>("/api/v1/admin/audit-logs?limit=100");
        setLogs(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "La bitácora requiere conexión al servidor.");
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">Bitácora de Auditoría Inmutable</h1>
        <p className="text-xs sm:text-sm text-slate-600">
          Registro trazable de escrituras, sincronizaciones offline y cambios de seguridad con correlation_id.
        </p>
      </div>
      {error ? (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-100">
              <tr>
                <th className="px-3 py-2.5 text-left font-bold">Fecha</th>
                <th className="px-3 py-2.5 text-left font-bold">Usuario</th>
                <th className="px-3 py-2.5 text-left font-bold">Entidad</th>
                <th className="px-3 py-2.5 text-left font-bold">Operación</th>
                <th className="px-3 py-2.5 text-left font-bold">Fuente</th>
                <th className="px-3 py-2.5 text-left font-bold">Resultado</th>
                <th className="px-3 py-2.5 text-left font-bold">Correlation ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.map((l) => (
                <tr key={l.id}>
                  <td className="px-3 py-2 whitespace-nowrap">{new Date(l.created_at).toLocaleString("es-CO")}</td>
                  <td className="px-3 py-2 font-semibold">{l.username}</td>
                  <td className="px-3 py-2">{l.entidad}</td>
                  <td className="px-3 py-2 font-bold">{l.operacion}</td>
                  <td className="px-3 py-2">{l.fuente}</td>
                  <td className="px-3 py-2">{l.resultado}</td>
                  <td className="px-3 py-2 font-mono text-[11px]">{l.correlation_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
