import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./global.css";
import "react-toastify/dist/ReactToastify.css";
import { ToastContainer } from "react-toastify";
import { CookiesProvider } from "next-client-cookies/server";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v14-appRouter";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Chatbot",
  description: "A personalized chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className + " overflow-x-hidden"}>
        <AppRouterCacheProvider>
          <CookiesProvider>
            {children}
            <ToastContainer stacked />
          </CookiesProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
