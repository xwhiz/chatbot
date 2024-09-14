"use client";
import WithSidebar from "@/layouts/WithSidebar";

import { CategoryScale } from "chart.js";
import { Line } from "react-chartjs-2";
import Chart from "chart.js/auto";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";

Chart.register(CategoryScale);

export default function Dashboard() {
  const router = useRouter();
  const [token, session] = useAuth();

  if (!session) return null;

  if (session.role !== "admin") {
    router.push("/");
  }

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Welcome to Admin Dashboard
        </h1>

        <h2 className="text-slate-900 text-center mt-6 mb-8 font-bold text-2xl md:text-left">
          Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Active Users</p>
            <h3 className="text-3xl font-semibold">1,000</h3>
          </article>
          <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Total Users</p>
            <h3 className="text-3xl font-semibold">10,000</h3>
          </article>
          <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Revenue</p>
            <h3 className="text-3xl font-semibold">$10,000</h3>
          </article>
        </div>

        <h2 className="text-slate-900 text-center mt-10 mb-8 font-bold text-2xl md:text-left">
          Chats timeline
        </h2>

        <div className="bg-white p-8 rounded shadow-lg">
          <Line
            data={{
              labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
              datasets: [
                {
                  label: "Chats",
                  data: [12, 19, 3, 5, 2, 3],
                  fill: false,
                  backgroundColor: "rgb(0, 9, 58)",
                  borderColor: "rgba(0, 9, 58, 0.2)",
                },
              ],
            }}
          />
        </div>

        <h2 className="text-slate-900 text-center mt-10 mb-8 font-bold text-2xl md:text-left">
          Users timeline
        </h2>

        <div className="bg-white p-8 rounded shadow-lg">
          <Line
            data={{
              labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
              datasets: [
                {
                  label: "Users",
                  data: [12, 19, 3, 14, 2, 3],
                  fill: false,
                  backgroundColor: "rgb(0, 9, 58)",
                  borderColor: "rgba(0, 9, 58, 0.2)",
                },
              ],
            }}
          />
        </div>
      </div>
    </WithSidebar>
  );
}
