import "./globals.css";
import type { Metadata } from "next";
import AuthProvider from "@/lib/auth-provider";

export const metadata: Metadata = {
  title: "Auth Project",
  description: "Next.js + FastAPI Auth System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-100 text-gray-900">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
