"use client";

import { AppShell } from "@mantine/core";
import { Sidebar } from "./Sidebar";

export function AppLayout({ children, sidebarContent }) {
  // Hide navbar if sidebarContent is null
  const hasSidebar = sidebarContent !== null;

  return (
    <AppShell
      padding="md"
      navbar={
        hasSidebar
          ? {
              width: 300,
              breakpoint: "sm",
            }
          : undefined
      }
    >
      {hasSidebar && (
        <AppShell.Navbar p="md">
          {sidebarContent || <Sidebar />}
        </AppShell.Navbar>
      )}

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
