"use client";

import { useState } from "react";
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

export function LoginForm() {
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

    const response = await signIn("credentials", {
      email,
      password,
      redirect: false,
      callbackUrl,
    });

    setLoading(false);

    if (response?.error) {
      setError("Incorrect email or password. Use demo@example.com / demo123.");
      return;
    }

    router.push(response?.url || callbackUrl);
    router.refresh();
  };

  return (
    <Paper withBorder shadow="md" radius="md" p="xl" w="100%">
      <Stack>
        <div>
          <Title order={2}>Sign in to EvalMate</Title>
          <Text c="dimmed" size="sm">
            Use demo credentials to try the app.
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
              placeholder="demo@example.com"
              required
              value={email}
              onChange={(event) => setEmail(event.currentTarget.value)}
              disabled={loading}
              autoComplete="email"
              data-autofocus
            />

            <PasswordInput
              label="Password"
              placeholder="demo123"
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
