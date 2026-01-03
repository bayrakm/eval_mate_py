"use client";

import { AppShell, Group, Button } from "@mantine/core";
import { IconLogout } from "@tabler/icons-react";
import { signOut, useSession } from "next-auth/react";
import { Sidebar } from "./Sidebar";

export function AppLayout({ children, sidebarContent }) {
  const hasSidebar = sidebarContent !== null;
  const { data: session } = useSession();

  const handleLogout = async () => {
    await signOut({ redirect: true, callbackUrl: "/login" });
  };

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
      header={{ height: 60 }}
    >
      <AppShell.Header p="md">
        <Group justify="space-between" h="100%">
          <div style={{ fontSize: "18px", fontWeight: "bold" }}>EvalMate</div>
          <Group gap="xs">
            {session?.user?.name && (
              <span style={{ fontSize: "14px", color: "#666" }}>
                Welcome, {session.user.name}
              </span>
            )}
            <Button
              size="xs"
              variant="default"
              rightSection={<IconLogout size={14} />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      {hasSidebar && (
        <AppShell.Navbar p="md">
          {sidebarContent || <Sidebar />}
        </AppShell.Navbar>
      )}

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
