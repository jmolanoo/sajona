import React, { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Sprout,
  Package,
  TreePine,
  MapPin,
  Stethoscope,
  Scissors,
  FlaskConical,
  AlertOctagon,
  FileBarChart2,
  Settings,
  Users,
  ShieldCheck,
  Wifi,
  WifiOff,
  RefreshCw,
  Menu,
  X,
  LogOut,
  Download,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useSyncStatus } from "../db/useLocalData";
import { SyncCenterModal } from "./SyncCenterModal";

export type PageId =
  | "dashboard"
  | "propagacion"
  | "transplante_bolsa"
  | "planta_madre"
  | "transplante_campo"
  | "control_fases"
  | "cosecha"
  | "post_cosecha"
  | "bajas"
  | "reportes"
  | "parametros"
  | "usuarios"
  | "auditoria";

export interface NavItem {
  id: PageId;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  permission?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { id: "dashboard", label: "Inicio", shortLabel: "Inicio", icon: LayoutDashboard },
  { id: "propagacion", label: "Propagación", shortLabel: "Propag.", icon: Sprout },
  { id: "transplante_bolsa", label: "Transplante Bolsa", shortLabel: "Bolsa", icon: Package },
  { id: "planta_madre", label: "Planta Madre", shortLabel: "Madres", icon: TreePine },
  { id: "transplante_campo", label: "Transplante Campo", shortLabel: "Campo", icon: MapPin },
  { id: "control_fases", label: "Plan Control / Clínica", shortLabel: "Control", icon: Stethoscope },
  { id: "cosecha", label: "Cosecha", shortLabel: "Cosecha", icon: Scissors },
  { id: "post_cosecha", label: "Post Cosecha", shortLabel: "Secado", icon: FlaskConical },
  { id: "bajas", label: "Bajas y Descartes", shortLabel: "Bajas", icon: AlertOctagon },
  { id: "reportes", label: "Reportes", shortLabel: "Reportes", icon: FileBarChart2 },
  { id: "parametros", label: "Parámetros y Catálogos", shortLabel: "Parám.", icon: Settings },
  { id: "usuarios", label: "Usuarios y Roles", shortLabel: "Usuarios", icon: Users, permission: "users:read" },
  { id: "auditoria", label: "Auditoría", shortLabel: "Auditoría", icon: ShieldCheck, permission: "audit:read" },
];

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function AppShell({
  activePage,
  onNavigate,
  children,
}: {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  children: React.ReactNode;
}): React.ReactElement {
  const { user, isOfflineSession, logout, hasPermission } = useAuth();
  const syncStatus = useSyncStatus();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const handler = (e: Event): void => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const visibleNav = NAV_ITEMS.filter((item) => !item.permission || hasPermission(item.permission));
  const currentNav = visibleNav.find((n) => n.id === activePage) ?? visibleNav[0];
  const primaryMobileIds: PageId[] = ["dashboard", "propagacion", "transplante_campo", "cosecha"];

  const handleInstall = async (): Promise<void> => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    setInstallPrompt(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Cabecera institucional SAJONA */}
      <header className="sticky top-0 z-40 bg-red-800 text-white shadow-md no-print">
        <div className="flex items-center justify-between gap-2 px-3 py-2.5 sm:px-5">
          <div className="flex items-center gap-2.5 min-w-0">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              aria-label="Abrir menú de módulos"
              className="lg:hidden min-h-[40px] min-w-[40px] flex items-center justify-center rounded-lg hover:bg-red-900"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-wide text-base sm:text-lg">SAJONA</span>
                <span className="hidden sm:inline-block rounded bg-red-950/60 px-2 py-0.5 text-[11px] font-semibold">
                  TRL-6 PWA
                </span>
              </div>
              <div className="flex items-center gap-1 text-xs text-red-100 truncate">
                <span>Inicio</span>
                <ChevronRight className="h-3 w-3 shrink-0" />
                <span className="font-semibold truncate">{currentNav?.label}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {installPrompt && (
              <button
                type="button"
                onClick={() => void handleInstall()}
                className="hidden sm:inline-flex min-h-[36px] items-center gap-1.5 rounded-lg bg-white px-2.5 py-1 text-xs font-bold text-red-900 hover:bg-red-50"
              >
                <Download className="h-3.5 w-3.5" />
                Instalar App
              </button>
            )}

            <button
              type="button"
              onClick={() => setSyncModalOpen(true)}
              aria-label="Estado de conexión y sincronización"
              className={`inline-flex min-h-[38px] items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold transition border ${
                syncStatus.conflictCount > 0
                  ? "bg-amber-300 text-slate-950 border-amber-400"
                  : !syncStatus.isOnline
                    ? "bg-slate-900 text-amber-300 border-slate-700"
                    : syncStatus.pendingCount > 0
                      ? "bg-amber-100 text-amber-950 border-amber-300"
                      : "bg-emerald-700 text-white border-emerald-500"
              }`}
            >
              {syncStatus.isSyncing ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : syncStatus.isOnline ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              <span>
                {!syncStatus.isOnline
                  ? `Sin conexión${syncStatus.pendingCount > 0 ? ` (${syncStatus.pendingCount})` : ""}`
                  : syncStatus.conflictCount > 0
                    ? `Conflicto (${syncStatus.conflictCount})`
                    : syncStatus.pendingCount > 0
                      ? `Pendientes (${syncStatus.pendingCount})`
                      : "En línea"}
              </span>
            </button>

            <div className="hidden md:flex items-center gap-2 rounded-lg bg-red-900/70 px-2.5 py-1 text-xs">
              <span className="font-semibold">{user?.full_name}</span>
              <span className="rounded bg-white/15 px-1.5 py-0.5 text-[10px] font-bold">
                {user?.roles[0]}
              </span>
            </div>

            <button
              type="button"
              onClick={() => void logout()}
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
              className="min-h-[38px] min-w-[38px] flex items-center justify-center rounded-lg hover:bg-red-900"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>

        {(!syncStatus.isOnline || isOfflineSession) && (
          <div className="bg-slate-900 px-3 py-1.5 text-center text-xs font-medium text-amber-200 border-t border-slate-800">
            Modo Offline-First activo: los registros se guardan en IndexedDB y se sincronizarán al
            recuperar conectividad.
          </div>
        )}
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar Desktop (Mockups V2 Dark Charcoal) */}
        <aside className="hidden lg:flex lg:w-64 lg:flex-col bg-slate-800 text-slate-100 shrink-0 no-print">
          <div className="px-4 py-3 border-b border-slate-700 text-xs text-slate-300 flex items-center justify-between">
            <span>{new Date().toLocaleDateString("es-CO", { dateStyle: "medium" })}</span>
            <span className="font-semibold text-emerald-300">SAJONA ADE</span>
          </div>
          <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-1" aria-label="Módulos del sistema">
            {visibleNav.map((item) => {
              const Icon = item.icon;
              const active = item.id === activePage;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                    active
                      ? "bg-red-800 text-white shadow-sm"
                      : "text-slate-200 hover:bg-slate-700"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Drawer móvil completo */}
        {drawerOpen && (
          <div className="fixed inset-0 z-50 lg:hidden flex no-print" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-slate-900/60" onClick={() => setDrawerOpen(false)} />
            <div className="relative z-10 w-72 max-w-[85vw] bg-slate-800 text-white flex flex-col h-full shadow-2xl">
              <div className="flex items-center justify-between px-4 py-3.5 bg-red-800">
                <div>
                  <p className="font-bold text-base">SAJONA Móvil</p>
                  <p className="text-xs text-red-100">{user?.full_name}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setDrawerOpen(false)}
                  aria-label="Cerrar menú"
                  className="min-h-[40px] min-w-[40px] flex items-center justify-center rounded-lg hover:bg-red-900"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav className="flex-1 overflow-y-auto p-2 space-y-1">
                {visibleNav.map((item) => {
                  const Icon = item.icon;
                  const active = item.id === activePage;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        onNavigate(item.id);
                        setDrawerOpen(false);
                      }}
                      className={`w-full min-h-[44px] flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${
                        active ? "bg-red-800 text-white" : "text-slate-200 hover:bg-slate-700"
                      }`}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        )}

        {/* Contenido principal */}
        <main className="flex-1 min-w-0 p-3 sm:p-5 lg:p-6 pb-24 lg:pb-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>

      {/* Barra inferior Mobile-First */}
      <nav
        aria-label="Navegación rápida móvil"
        className="fixed bottom-0 inset-x-0 z-30 lg:hidden bg-white border-t border-slate-200 flex items-center justify-around px-1 py-1 no-print"
      >
        {primaryMobileIds.map((id) => {
          const item = visibleNav.find((n) => n.id === id);
          if (!item) return null;
          const Icon = item.icon;
          const active = activePage === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onNavigate(id)}
              className={`flex flex-col items-center justify-center min-h-[48px] px-2 py-1 rounded-lg text-[11px] font-semibold ${
                active ? "text-red-800" : "text-slate-600"
              }`}
            >
              <Icon className={`h-5 w-5 ${active ? "text-red-800" : "text-slate-500"}`} />
              <span>{item.shortLabel}</span>
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="flex flex-col items-center justify-center min-h-[48px] px-2 py-1 rounded-lg text-[11px] font-semibold text-slate-600"
        >
          <Menu className="h-5 w-5 text-slate-500" />
          <span>Módulos</span>
        </button>
      </nav>

      <SyncCenterModal open={syncModalOpen} onClose={() => setSyncModalOpen(false)} />
    </div>
  );
}
