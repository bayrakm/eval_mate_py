"use client";

import { Suspense } from "react";
import { Center, Container, Text } from "@mantine/core";
import Link from "next/link";
import { LoginForm } from "../../components/auth/LoginForm";

export default function LoginPage() {
  return (
    <Container size="xs" py="xl" style={{ minHeight: "100vh" }}>
      <Center style={{ minHeight: "80vh" }}>
        <div style={{ width: "100%" }}>
          <Suspense fallback={<Text ta="center">Loading form...</Text>}>
            <LoginForm />
          </Suspense>
          <Text size="xs" mt="sm" c="dimmed" ta="center">
            Demo hint: email{" "}
            <Text component="span" c="orange.7">
              demo@example.com
            </Text>{" "}
            / password{" "}
            <Text component="span" c="orange.7">
              demo123
            </Text>
            .
          </Text>
          <Text size="xs" mt="xs" ta="center">
            Don&apos;t have an account yet? You can later connect this to the
            backend through a registration endpoint.
          </Text>
          <Text size="xs" mt="xs" ta="center">
            <Link href="/">
              <Text component="span" c="orange.7" inherit>
                Back to homepage
              </Text>
            </Link>
          </Text>
        </div>
      </Center>
    </Container>
  );
}
