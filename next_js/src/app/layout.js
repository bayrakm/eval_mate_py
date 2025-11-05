"use client";

import { MantineProvider, createTheme } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "./globals.css";

// Orange theme configuration
const theme = createTheme({
  primaryColor: "orange",
  colors: {
    orange: [
      "#fff4e6",
      "#ffe8cc",
      "#ffd8a8",
      "#ffc078",
      "#ffa94d",
      "#ff922b",
      "#fd7e14",
      "#f76707",
      "#e8590c",
      "#d9480f",
    ],
  },
  defaultRadius: "md",
  fontFamily: "Inter, system-ui, sans-serif",
  headings: {
    fontFamily: "Inter, system-ui, sans-serif",
  },
});

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body>
        <MantineProvider theme={theme}>
          <Notifications position="top-right" />
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
