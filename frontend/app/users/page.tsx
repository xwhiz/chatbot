"use client";

import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import TableCell from "@mui/material/TableCell";
import CustomTable, { HeadCell } from "@/components/CustomTable";
import Swal from "sweetalert2";
import { Trash2Icon } from "lucide-react";

type User = {
  _id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
};

const headCells: readonly HeadCell[] = [
  {
    id: "name",
    numeric: false,
    label: "Name",
  },
  {
    id: "email",
    numeric: true,
    label: "Email",
  },
  {
    id: "role",
    numeric: true,
    label: "Role",
  },
  {
    id: "created_at",
    numeric: true,
    label: "Created At",
  },
  {
    id: "_id",
    numeric: true,
    label: "Actions",
  },
];

export default function Users() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [token, session] = useAuth();
  const [totalRecords, setTotalRecords] = useState(0);
  const [isPromptPosting, setIsPromptPosting] = useState(false);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  useEffect(() => {
    if (!session) return;

    const fetchTotalRecords = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/users/count",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setTotalRecords(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    };

    fetchTotalRecords();
  }, [session, token]);

  useEffect(() => {
    if (!session) return;

    const fetchRecords = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL +
            `/users?page=${page}&limit=${rowsPerPage}`,
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

    fetchRecords();
  }, [page, rowsPerPage, session, token]);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (!session) return null;
  if (session.role !== "admin") router.push("/");

  const handleDelete = async (id: string) => {
    const result = await Swal.fire({
      title: "Are you sure?",
      text: "You are deleting the user and their chats, you won't be able to revert this!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "No, cancel!",
    });

    if (!result.isConfirmed) return;

    try {
      await axios.delete(process.env.NEXT_PUBLIC_API_URL + `/users/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setTotalRecords(totalRecords - 1);

      const response = await axios.get(
        process.env.NEXT_PUBLIC_API_URL +
          `/users?page=${page}&limit=${rowsPerPage}`,
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

      toast.success("User deleted successfully");
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    }
  };

  const handleChangePrompt = async (userId: string) => {
    const { value: prompt } = await Swal.fire({
      title: "Enter custom prompt for user",
      html: `<textarea id="swal-input1" class="w-full max-w-xs h-40 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter your prompt"></textarea>`,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: "Update",
      preConfirm: () => {
        const prompt = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;

        if (!prompt) {
          Swal.showValidationMessage("Please provide the prompt text");
          return false;
        }
        return prompt;
      },
    });

    if (!prompt) return;

    setIsPromptPosting(true);

    try {
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/users/prompt/${userId}`,
        {
          prompt: prompt.trim(),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setIsPromptPosting(false);
      toast.success("Prompt updated successfully");
    } catch (error: any) {
      const data = error.response;
      if (data) {
        console.log(data.message);
        toast.error(data.message);
      }
    } finally {
      setIsPromptPosting(false);
    }
  };

  return (
    <WithSidebar>
      <div className="container mx-auto p-4 h-full overflow-auto scrollbar">
        <h1 className="text-slate-900 text-center mt-6 mb-8 font-bold text-3xl md:text-left">
          Users
        </h1>

        <CustomTable
          data={users}
          headCells={headCells}
          tableRow={(row: User, index: number) => (
            <>
              <TableCell>{row.name}</TableCell>
              <TableCell align="right">{row.email}</TableCell>
              <TableCell align="right">{row.role}</TableCell>
              <TableCell align="right">
                {new Date(row.created_at).toLocaleString()}
              </TableCell>
              <TableCell align="right">
                {row.role !== "admin" && (
                  <div className="flex justify-end items-center flex-wrap">
                    <button
                      className="text-blue-500 hover:underline bg-none mr-2"
                      onClick={() => handleChangePrompt(row._id)}
                    >
                      Change Prompt
                    </button>
                    <Link
                      href={{
                        pathname: `/users/change-access/${row._id}`,
                        query: { name: row.name },
                      }}
                      className="text-orange-500 mr-2 hover:underline border-none bg-transparent"
                    >
                      Change Access
                    </Link>
                    <Link
                      href={`/chats/${row._id}`}
                      className="text-blue-500 hover:underline"
                    >
                      See Chats
                    </Link>
                    <button
                      className="text-red-500 ml-2 hover:underline border-none bg-transparent"
                      onClick={() => handleDelete(row._id)}
                    >
                      <Trash2Icon />
                    </button>
                  </div>
                )}
              </TableCell>
            </>
          )}
          totalRecords={totalRecords}
          handleChangePage={handleChangePage}
          handleChangeRowsPerPage={handleChangeRowsPerPage}
          page={page}
          rowsPerPage={rowsPerPage}
        />
      </div>
    </WithSidebar>
  );
}
