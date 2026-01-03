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
import { IconAlertCircle, IconCheck } from "@tabler/icons-react";
import { useRouter } from "next/navigation";

function RegisterFormContent() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (!name || !email || !password || !passwordConfirm) {
      setError("All fields are required");
      setLoading(false);
      return;
    }

    if (password !== passwordConfirm) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Registration failed");
        return;
      }

      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err) {
      setError("An error occurred during registration");
      console.error("Register error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper withBorder shadow="md" radius="md" p="xl" w="100%">
      <Stack>
        <div>
          <Title order={2}>Create EvalMate Account</Title>
          <Text c="dimmed" size="sm">
            Sign up to start using our platform.
          </Text>
        </div>

        {error && (
          <Alert
            color="red"
            title="Registration failed"
            icon={<IconAlertCircle size={16} />}
          >
            {error}
          </Alert>
        )}

        {success && (
          <Alert
            color="green"
            title="Success"
            icon={<IconCheck size={16} />}
          >
            {success}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Full Name"
              placeholder="John Doe"
              required
              value={name}
              onChange={(event) => setName(event.currentTarget.value)}
              disabled={loading}
              data-autofocus
            />

            <TextInput
              label="Email"
              placeholder="john@example.com"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.currentTarget.value)}
              disabled={loading}
              autoComplete="email"
            />

            <PasswordInput
              label="Password"
              placeholder="At least 6 characters"
              required
              value={password}
              onChange={(event) => setPassword(event.currentTarget.value)}
              disabled={loading}
            />

            <PasswordInput
              label="Confirm Password"
              placeholder="Re-enter your password"
              required
              value={passwordConfirm}
              onChange={(event) => setPasswordConfirm(event.currentTarget.value)}
              disabled={loading}
            />

            <Button type="submit" loading={loading} fullWidth>
              Sign Up
            </Button>
          </Stack>
        </form>

        <Text size="xs" ta="center">
          Already have an account?{" "}
          <Text
            component="a"
            href="/login"
            c="orange.7"
            inherit
            style={{ cursor: "pointer" }}
          >
            Sign in here
          </Text>
        </Text>
      </Stack>
    </Paper>
  );
}

export function RegisterForm() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <RegisterFormContent />
    </Suspense>
  );
}
