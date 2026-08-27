"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthToken } from "@/lib/authStorage";

export function useRequireAuth() {
  const router = useRouter();
  const [token] = useState<string | null>(() => getAuthToken());
  const isAuthorized = Boolean(token);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [router, token]);

  return { isAuthorized };
}
