import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "EvalMate - Student Assignment Feedback",
  description: "AI-powered student assignment evaluation with rubric-based grading",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full font-sans antialiased">
        {children}
      </body>
    </html>
  );
}