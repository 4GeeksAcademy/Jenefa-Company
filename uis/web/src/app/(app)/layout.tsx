import AppRouteGuard from "@/components/AppRouteGuard";
import { WebShell } from "@/components/WebShell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppRouteGuard>
      <WebShell>{children}</WebShell>
    </AppRouteGuard>
  );
}
