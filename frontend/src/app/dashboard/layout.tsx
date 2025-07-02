import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    template: '%s | Finance Tracker',
    default: 'Dashboard | Finance Tracker',
  },
  description: "View and manage your investment portfolio dashboard",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>;
}