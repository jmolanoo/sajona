import React, { useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { AppShell, type PageId } from "./components/AppShell";
import { AuditoriaPage, UsuariosAdminPage } from "./pages/AdminPages";
import { BajasPage } from "./pages/BajasPage";
import { ControlFasesPage } from "./pages/ControlFasesPage";
import { CosechaPage } from "./pages/CosechaPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ParametrosPage } from "./pages/ParametrosPage";
import { PlantaMadrePage } from "./pages/PlantaMadrePage";
import { PostCosechaPage } from "./pages/PostCosechaPage";
import { PropagacionPage } from "./pages/PropagacionPage";
import { ReportesPage } from "./pages/ReportesPage";
import { TransplantePage } from "./pages/TransplantePage";

function MainRouter(): React.ReactElement {
  const { user, loading } = useAuth();
  const [page, setPage] = useState<PageId>("dashboard");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-700 font-semibold">
        Cargando SAJONA PWA...
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const renderPage = (): React.ReactElement => {
    switch (page) {
      case "dashboard":
        return <DashboardPage onNavigate={setPage} />;
      case "propagacion":
        return <PropagacionPage />;
      case "transplante_bolsa":
        return <TransplantePage etapa="BOLSA" />;
      case "planta_madre":
        return <PlantaMadrePage />;
      case "transplante_campo":
        return <TransplantePage etapa="CAMPO" />;
      case "control_fases":
        return <ControlFasesPage />;
      case "cosecha":
        return <CosechaPage />;
      case "post_cosecha":
        return <PostCosechaPage />;
      case "bajas":
        return <BajasPage />;
      case "reportes":
        return <ReportesPage />;
      case "parametros":
        return <ParametrosPage />;
      case "usuarios":
        return <UsuariosAdminPage />;
      case "auditoria":
        return <AuditoriaPage />;
    }
  };

  return (
    <AppShell activePage={page} onNavigate={setPage}>
      {renderPage()}
    </AppShell>
  );
}

export default function App(): React.ReactElement {
  return (
    <AuthProvider>
      <MainRouter />
    </AuthProvider>
  );
}
