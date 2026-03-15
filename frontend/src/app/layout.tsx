import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "TODO App",
  description: "Personal TODO management application",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body
        style={{
          margin: 0,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          backgroundColor: "#f5f5f5",
          color: "#333",
          minHeight: "100vh",
        }}
      >
        {children}
      </body>
    </html>
  );
}
