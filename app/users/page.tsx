"use client";

import useAuth from "@/hooks/useAuth";
import WithSidebar from "@/layouts/WithSidebar";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import Paper from "@mui/material/Paper";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import { visuallyHidden } from "@mui/utils";
import CustomTable, { HeadCell } from "@/components/CustomTable";

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

    const fetchUsers = async () => {
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

    fetchUsers();
  }, [session, token]);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - users.length) : 0;

  if (!session) return null;
  if (session.role !== "admin") router.push("/");

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
                <Link
                  href={`/chats/${row._id}`}
                  className="text-blue-500 hover:underline"
                >
                  See Chats
                </Link>
                <button className="text-red-500 ml-2 hover:underline border-none bg-transparent">
                  Delete
                </button>
              </TableCell>
            </>
          )}
          totalRecords={users.length}
          handleChangePage={handleChangePage}
          handleChangeRowsPerPage={handleChangeRowsPerPage}
          emptyRows={emptyRows}
          page={page}
          rowsPerPage={rowsPerPage}
        />
      </div>
    </WithSidebar>
  );
}
