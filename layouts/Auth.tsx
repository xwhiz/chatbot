import Navbar from "@/components/Navbars/AuthNavbar";
import FooterSmall from "@/components/Footers/FooterSmall";

export default function Auth({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar />
      <main>
        <section className="relative w-full h-full min-h-screen bg-slate-100">
          {children}
          <FooterSmall />
        </section>
      </main>
    </>
  );
}
