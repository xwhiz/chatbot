import HeaderWithButton from "@/components/Headers/HeaderWithButton";
import { Sidebar } from "@/components/Sidebars/Sidebar";

export default function WithSidebar({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="block md:grid md:grid-cols-12">
      <div className="md:col-span-3">
        <Sidebar />
      </div>
      <div className="md:col-span-9 relative h-screen overflow-hidden flex flex-col">
        <HeaderWithButton />

        {children}
      </div>
    </div>
  );
}
