import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { decodeToken } from "@/utils/decodeToken";

export default function useAuth(): [
  string | null,
  { role: string; email: string; name: string } | null
] {
  const router = useRouter();
  const [payload, setPayload] = useState<{
    role: string;
    email: string;
    name: string;
  } | null>(null);

  // check if the window is defined
  if (typeof window === "undefined") return [null, null];

  const token = window.localStorage.getItem("token");

  useEffect(() => {
    decodeToken(token as any).then((payload: any) => {
      setPayload(payload);
    });
  }, [token]);

  if (!token) {
    router.replace("/login");
  }

  return [token, payload];
}
