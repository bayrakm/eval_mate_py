"use client";

import { useState, Suspense } from "react";
import {
  Alert,
  Button,
  PasswordInput,
  Paper,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { IconAlertCircle } from "@tabler/icons-react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    if (!email || !password) {
      setError("Email and password are required");
      setLoading(false);
      return;
    }

    try {
      const response = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl,
      });

      if (response?.error) {
        setError("Incorrect email or password.");
        return;
      }

      if (response?.ok) {
        router.push(response?.url || callbackUrl);
        router.refresh();
      }
    } catch (err) {
      setError("An error occurred during login");
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper withBorder shadow="md" radius="md" p="xl" w="100%">
      <Stack>
        <div>
          <Title order={2}>Sign in to EvalMate</Title>
          <Text c="dimmed" size="sm">
            Enter your email and password.
          </Text>
        </div>

        {error && (
          <Alert
            color="red"
            title="Sign-in failed"
            icon={<IconAlertCircle size={16} />}
          >
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Email"
              placeholder="email@example.com"
              required
              value={email}
              onChange={(event) => setEmail(event.currentTarget.value)}
              disabled={loading}
              autoComplete="email"
              data-autofocus
            />

            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              required
              value={password}
              onChange={(event) => setPassword(event.currentTarget.value)}
              disabled={loading}
              autoComplete="current-password"
            />

            <Button type="submit" loading={loading} fullWidth>
              Sign In
            </Button>
          </Stack>
        </form>
      </Stack>
    </Paper>
  );
}

export function LoginForm() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginFormContent />
    </Suspense>
  );
}
