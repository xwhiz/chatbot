import { useCookies } from "next-client-cookies";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { decodeToken } from "@/utils/decodeToken";

export default function useAuth() {
  const cookies = useCookies();
  const [payload, setPayload] = useState<{
    role: string;
    email: string;
    name: string;
  } | null>(null);
  const token = cookies.get("token");
  const router = useRouter();

  useEffect(() => {
    decodeToken(token).then((payload: any) => {
      setPayload(payload);
    });
  }, [token]);

  if (!token) {
    router.push("/login");
  }

  return [token, payload];
}
