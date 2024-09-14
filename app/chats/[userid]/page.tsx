"use client";
import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import { useParams, usePathname, useRouter } from "next/navigation";

export default function Chats() {
  const [token, session] = useAuth();
  const router = useRouter();
  const params = useParams();
  const userid = params.userid;

  if (!session) return null;
  if (session.role !== "admin") router.push("/");

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Chats for {userid}
        </h1>

        <div className="bg-white p-8 rounded shadow-lg">Chats</div>
      </div>
    </WithSidebar>
  );
}
