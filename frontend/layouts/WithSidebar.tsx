import HeaderWithButton from "@/components/Headers/HeaderWithButton";
import { Sidebar } from "@/components/Sidebars/Sidebar";

export default function WithSidebar({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex bg-[#ecf0f1]">
      <Sidebar />
      <div className="relative flex-1 h-screen w-full overflow-idden flex flex-col">
        <HeaderWithButton />

        {children}
      </div>
    </div>
  );
}
