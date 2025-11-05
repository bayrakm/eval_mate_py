"use client";

import { AppShell, Group } from "@mantine/core";
import { Sidebar } from "./Sidebar";

export function AppLayout({ children, sidebarContent }) {
  return (
    <AppShell
      padding="md"
      navbar={{
        width: 300,
        breakpoint: "sm",
      }}
    >
      <AppShell.Navbar p="md">{sidebarContent || <Sidebar />}</AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
