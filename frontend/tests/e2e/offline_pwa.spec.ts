import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("SAJONA PWA Mobile-First & Offline-First E2E", () => {
  test("escenarios completos online, offline, reapertura sin red, sync, conflictos, móvil y accesibilidad", async ({
    browser,
    request,
    baseURL,
  }) => {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      serviceWorkers: "allow",
    });
    const page = await context.newPage();

    // 1. Primer acceso con conexión + Auditoría de accesibilidad en Login
    await page.goto(baseURL!);
    await expect(page.getByRole("heading", { name: "SAJONA ADE" })).toBeVisible();

    const axeLogin = await new AxeBuilder({ page }).analyze();
    expect(axeLogin.violations.filter((v) => v.impact === "critical")).toEqual([]);

    await page.getByLabel(/Usuario o Correo/i).fill("jefe");
    await page.getByLabel(/Contraseña/i).fill("SajonaJefe2026!");
    await page.getByRole("button", { name: "Ingresar" }).click();

    await expect(page.getByRole("heading", { name: "Panel Operativo SAJONA" })).toBeVisible();
    await expect(page.getByText("LOT-2026-030")).toBeVisible({ timeout: 15000 });

    // Verificar Service Worker y Manifest PWA
    const pwaInfo = await page.evaluate(async () => {
      const reg = await navigator.serviceWorker.ready;
      const manResp = await fetch("/manifest.webmanifest");
      const man = await manResp.json();
      return { swActive: Boolean(reg.active), shortName: man.short_name };
    });
    expect(pwaInfo.swActive).toBe(true);
    expect(pwaInfo.shortName).toBe("SAJONA");

    const axeDash = await new AxeBuilder({ page }).analyze();
    expect(axeDash.violations.filter((v) => v.impact === "critical")).toEqual([]);

    // 2. Desconectar red -> navegar a Propagación y crear lote OFFLINE
    await context.setOffline(true);
    await expect(page.getByText(/Sin conexión/i).first()).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /Propag\./i }).click();
    await expect(page.getByRole("heading", { name: "Propagación" })).toBeVisible();

    await page.getByRole("button", { name: "Nuevo" }).click();
    const offlineCode = `LOT-E2E-${Date.now().toString().slice(-5)}`;
    await page.getByLabel(/Id Lote/i).fill(offlineCode);
    await page.getByLabel(/Cantidad de Siembra/i).fill("45");
    await page.getByRole("button", { name: "Guardar" }).click();

    await expect(page.getByText(offlineCode).first()).toBeVisible();
    await expect(page.getByText(/Pendiente/i).first()).toBeVisible();

    // 3. Cierre y reapertura de la pestaña SIN CONEXIÓN (Service Worker + IndexedDB)
    await page.close();
    const reopenedPage = await context.newPage();
    await reopenedPage.goto(baseURL!);
    await expect(reopenedPage.getByRole("heading", { name: "Panel Operativo SAJONA" })).toBeVisible({
      timeout: 15000,
    });
    await expect(reopenedPage.getByText(offlineCode).first()).toBeVisible();
    await expect(reopenedPage.getByText(/Sin conexión/i).first()).toBeVisible();

    // 4. Recuperar conectividad -> Auto-Sync + verificar en servidor
    await context.setOffline(false);
    await expect(reopenedPage.getByRole("button", { name: /Estado de conexión/i })).toContainText(
      /En línea/i,
      { timeout: 15000 }
    );

    await reopenedPage.getByRole("button", { name: /Estado de conexión/i }).click();
    await expect(
      reopenedPage.getByText("Todo está sincronizado con el servidor")
    ).toBeVisible({ timeout: 15000 });
    await reopenedPage.getByRole("button", { name: "Cerrar modal" }).click();

    // 5. Simular conflicto concurrente real (modificación concurrente en servidor mientras otro edita offline)
    await reopenedPage.getByRole("button", { name: /Propag\./i }).click();
    await expect(reopenedPage.getByText(offlineCode).first()).toBeVisible();

    // Simular otro dispositivo (Dispositivo B) modificando el mismo lote en backend
    const loginB = await request.post(`${baseURL}/api/v1/auth/login`, {
      data: { identifier: "admin", password: "SajonaAdmin2026!" },
    });
    const { access_token: adminToken } = (await loginB.json()) as { access_token: string };
    const listB = await request.get(`${baseURL}/api/v1/entities/propagacion`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    const lotesB = (await listB.json()) as Array<{ id: string; codigo_lote: string }>;
    const targetB = lotesB.find((l) => l.codigo_lote === offlineCode)!;
    expect(targetB).toBeTruthy();
    const putB = await request.put(`${baseURL}/api/v1/entities/propagacion/${targetB.id}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { ...targetB, cantidad_material: 60, observaciones: "Editado por Dispositivo B" },
    });
    expect(putB.status()).toBe(200);

    // Ahora el usuario móvil está offline con versión local v1 y edita el mismo lote -> al reconectar genera conflicto!
    await context.setOffline(true);
    await reopenedPage.getByRole("button", { name: "Editar" }).first().click();
    await reopenedPage.getByLabel(/Cantidad de Siembra/i).fill("42");
    await reopenedPage.getByRole("button", { name: "Guardar" }).click();

    await context.setOffline(false);
    await expect(reopenedPage.getByRole("button", { name: /Estado de conexión/i })).toContainText(
      /Conflicto/i,
      { timeout: 15000 }
    );

    // Abrir Centro de Sincronización y resolver conflicto conservando cambios locales
    await reopenedPage.getByRole("button", { name: /Estado de conexión/i }).click();
    await expect(reopenedPage.getByText("Tu cambio local")).toBeVisible();
    await expect(reopenedPage.getByText(/Versión actual del servidor/i)).toBeVisible();
    await reopenedPage.getByRole("button", { name: "Conservar mis cambios" }).click();
    await expect(
      reopenedPage.getByText("Todo está sincronizado con el servidor")
    ).toBeVisible({ timeout: 15000 });
    await reopenedPage.getByRole("button", { name: "Cerrar modal" }).click();

    // 6. Verificar vista Escritorio (1280x800) + Reportes
    await reopenedPage.setViewportSize({ width: 1280, height: 800 });
    await reopenedPage.getByRole("button", { name: "Reportes" }).first().click();
    await expect(reopenedPage.getByRole("heading", { name: "Reportes y Trazabilidad" })).toBeVisible();
    await expect(reopenedPage.getByText(offlineCode).first()).toBeVisible();

    await context.close();
  });
});
