"use client";

import { Center, Loader } from "@mantine/core";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function ProtectedRoute({ children }) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return (
      <Center style={{ minHeight: "80vh" }}>
        <Loader color="orange" size="lg" />
      </Center>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  return children;
}
