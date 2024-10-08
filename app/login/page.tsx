import Link from "next/link";
import Form from "./Form";
import MinFooter from "@/components/Footers/MinFooter";
import MinHeader from "@/components/Headers/MinHeader";

export default function Register() {
  return (
    <>
      <MinHeader />
      <main>
        <section className="relative w-full">
          <div className="container mx-auto my-4 p-4 h-full">
            <div className="flex content-center items-center justify-center h-full">
              <div className="w-full md:w-10/12 lg:w-6/12 bg-white rounded">
                <div className="relative flex flex-col min-w-0 break-words w-full shadow-lg rounded-lg border-0">
                  <div className="flex-uto px-4 lg:px-10 py-4 pt-0">
                    <h1 className="text-slate-900 text-center mb-8 mt-10 font-bold text-3xl">
                      Login
                    </h1>
                    <Form />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <MinFooter />
    </>
  );
}
