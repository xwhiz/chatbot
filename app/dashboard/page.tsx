"use client";
import WithSidebar from "@/layouts/WithSidebar";

import { CategoryScale } from "chart.js";
import { Line } from "react-chartjs-2";
import Chart from "chart.js/auto";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";
import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";

Chart.register(CategoryScale);

interface IdAndDate {
  _id: string;
  created_at: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [token, session] = useAuth();

  const [users, setUsers] = useState<IdAndDate[]>([]);
  const [chats, setChats] = useState<IdAndDate[]>([]);

  useEffect(() => {
    if (!token) return;

    async function fetchUsers() {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/users/all-minimal",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setUsers(response.data.data);

        console.log(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    }

    async function fetchChats() {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/chats/all/minimal",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setChats(response.data.data);

        console.log(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    }

    fetchChats();
    fetchUsers();
  }, [token, session]);

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
          {/* <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Active Users</p>
            <h3 className="text-3xl font-semibold">1,000</h3>
          </article> */}
          <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Total Users</p>
            <h3 className="text-3xl font-semibold">
              {new Intl.NumberFormat().format(users.length)}
            </h3>
          </article>
          <article className="flex flex-col gap-2 justify-center items-center w-full bg-white p-8 rounded shadow-lg">
            <p>Total Chats</p>
            <h3 className="text-3xl font-semibold">$10,000</h3>
          </article>
        </div>

        <h2 className="text-slate-900 text-center mt-10 mb-8 font-bold text-2xl md:text-left">
          Chats timeline
        </h2>

        <div className="bg-white p-8 rounded shadow-lg">
          {/* Use the chats with created_at */}
          <Line
            data={{
              labels: chats
                .sort((a, b) => {
                  const dateA = new Date(a.created_at);
                  const dateB = new Date(b.created_at);
                  return dateA.getTime() - dateB.getTime();
                })
                .map((chat) => {
                  const date = new Date(chat.created_at);
                  // month with year
                  return date.toLocaleString("default", {
                    month: "short",
                    year: "numeric",
                  });
                })
                .filter((value, index, self) => self.indexOf(value) === index),
              datasets: [
                {
                  label: "Chats",
                  data: chats
                    .map((chat) => {
                      const date = new Date(chat.created_at);
                      // month with year
                      return date.toLocaleString("default", {
                        month: "short",
                        year: "numeric",
                      });
                    })
                    .reduce((acc: { [key: string]: number }, value) => {
                      acc[value] = (acc[value] || 0) + 1;
                      return acc;
                    }, {}),
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
          {/* Use the users with created_at */}
          <Line
            data={{
              labels: users
                .sort((a, b) => {
                  const dateA = new Date(a.created_at);
                  const dateB = new Date(b.created_at);
                  return dateA.getTime() - dateB.getTime();
                })
                .map((user) => {
                  const date = new Date(user.created_at);
                  // month with year
                  return date.toLocaleString("default", {
                    month: "short",
                    year: "numeric",
                  });
                })
                .filter((value, index, self) => self.indexOf(value) === index),
              datasets: [
                {
                  label: "Users",
                  data: users
                    .map((user) => {
                      const date = new Date(user.created_at);
                      // month with year
                      return date.toLocaleString("default", {
                        month: "short",
                        year: "numeric",
                      });
                    })
                    .reduce((acc: { [key: string]: number }, value) => {
                      acc[value] = (acc[value] || 0) + 1;
                      return acc;
                    }, {}),
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
