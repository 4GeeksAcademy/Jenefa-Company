"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

const TOKEN_KEY = "hc_auth_token";

function subscribe(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function getSnapshot() {
  return window.localStorage.getItem(TOKEN_KEY);
}

function getServerSnapshot() {
  return null;
}

export default function AppRouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const token = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  if (!token) {
    return (
      <div className="loading-state flex min-h-full flex-1 items-center justify-center bg-background px-6 text-sm text-muted">
        Verifying session token safety layer...
      </div>
    );
  }

  return <>{children}</>;
}
