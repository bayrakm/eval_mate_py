"use client";

import { Center, Container, Text } from "@mantine/core";
import Link from "next/link";
import { RegisterForm } from "../../components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <Container size="xs" py="xl" style={{ minHeight: "100vh" }}>
      <Center style={{ minHeight: "80vh" }}>
        <div style={{ width: "100%" }}>
          <RegisterForm />
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
