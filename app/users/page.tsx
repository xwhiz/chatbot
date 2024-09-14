"use client";
import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FaEdit, FaRegEdit, FaTrash } from "react-icons/fa";
import { FaPenToSquare } from "react-icons/fa6";

import { Table, Thead, Tbody, Tr, Td } from "react-super-responsive-table";
import "react-super-responsive-table/dist/SuperResponsiveTableStyle.css";
import { toast } from "react-toastify";

type User = {
  _id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
};

export default function Users() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>();
  const [token, session] = useAuth();

  useEffect(() => {
    if (!session) return;

    const fetchUsers = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/users",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const users = response.data.data;
        const sortedUsers = users.sort(
          (a: User, b: User) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setUsers(sortedUsers);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchUsers();
  }, [session, token]);

  if (!session) return null;
  if (session.role !== "admin") router.push("/");

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Users
        </h1>

        <div className="bg-white p-8 rounded shadow-lg">
          <Table className="w-full rounded overflow-hidden">
            <Thead>
              <Tr className="bg-slate-200">
                <Td className="p-2">Name</Td>
                <Td className="p-2">Email</Td>
                <Td className="p-2">Role</Td>
                <Td className="p-2">Actions</Td>
              </Tr>
            </Thead>
            <Tbody>
              {users?.map((user) => (
                <Tr key={user._id}>
                  <Td className="p-2">{user.name}</Td>
                  <Td className="p-2">{user.email}</Td>
                  <Td className="p-2">{user.role}</Td>
                  <Td className="p-2 flex gap-2">
                    <Link
                      href={`/chats/${user._id}`}
                      className="text-white bg-blue-600 px-4 py-2 rounded hover:bg-blue-500"
                    >
                      See Chats
                    </Link>

                    <button className="text-white bg-red-600 px-4 py-2 rounded hover:bg-red-500">
                      <FaTrash />
                    </button>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          {/* Pagination to be added */}
        </div>
      </div>
    </WithSidebar>
  );
}
