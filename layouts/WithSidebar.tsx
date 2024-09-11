import HeaderWithButton from "@/components/Headers/HeaderWithButton";
import { Sidebar } from "@/components/Sidebars/Sidebar";

export default function WithSidebar({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <Sidebar />
      <div className="relative h-screen w-full overflow-hidden flex flex-col">
        <HeaderWithButton />

        {children}
      </div>
    </div>
  );
}
